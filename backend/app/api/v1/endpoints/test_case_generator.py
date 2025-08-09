"""
统一测试用例生成API
整合所有输入方式和智能体，提供简洁统一的接口
"""
import asyncio
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from autogen_core import MessageContext, ClosureContext
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from loguru import logger

from app.core.messages import StreamMessage
from app.core.messages.test_case import (
    DocumentParseRequest, ImageAnalysisRequest, ApiSpecParseRequest,
    DatabaseSchemaParseRequest, VideoAnalysisRequest, DirectRequirementRequest
)
from app.core.agents.collector import StreamResponseCollector
from app.core.types import AgentPlatform, FILE_TYPE_TO_AGENT_MAPPING, AgentTypes
from app.services.test_case.orchestrator_service import get_test_case_orchestrator
from app.utils.session_db_utils import (
    create_processing_session, update_session_status, update_session_progress,
    determine_session_type, extract_session_config, extract_session_input_data
)
from app.utils.agent_message_log_utils import (
    save_agent_message_log, update_session_logs_summary
)
from app.core.enums import SessionStatus

# 全局会话存储
active_sessions: Dict[str, Dict[str, Any]] = {}
message_queues: Dict[str, asyncio.Queue] = {}

# 会话超时（秒）
SESSION_TIMEOUT = 3600  # 1小时

logger = logger.bind(module="test_case_generator")
router = APIRouter()


# 智能体名称映射
AGENT_DISPLAY_NAMES = {
    "document_parser": "文档解析智能体",
    "image_analyzer": "图片分析智能体",
    "api_spec_parser": "API规范解析智能体",
    "database_schema_parser": "数据库Schema解析智能体",
    "video_analyzer": "视频分析智能体",
    "test_case_generator": "测试用例生成智能体",
    "mind_map_generator": "思维导图生成智能体",
    "excel_exporter": "Excel导出智能体",
    "test_case_saver": "测试用例保存智能体",
    "requirement_saver": "需求保存智能体",
    "系统": "系统",
    "unknown": "未知智能体"
}


def _get_agent_display_name(agent_type: str) -> str:
    """获取智能体显示名称"""
    return AGENT_DISPLAY_NAMES.get(agent_type, agent_type)


def _determine_processing_stage(message: StreamMessage) -> str:
    """根据消息内容确定处理阶段"""
    content = message.content.lower()

    if any(keyword in content for keyword in ['开始', '启动', '初始化']):
        return "initialization"
    elif any(keyword in content for keyword in ['解析', '分析', '处理']):
        return "processing"
    elif any(keyword in content for keyword in ['生成', '创建', '构建']):
        return "generation"
    elif any(keyword in content for keyword in ['保存', '存储', '写入']):
        return "saving"
    elif any(keyword in content for keyword in ['完成', '结束', '成功']):
        return "completion"
    elif any(keyword in content for keyword in ['失败', '错误', '异常']):
        return "error"
    else:
        return "processing"


async def _save_message_to_database(session_id: str, message: StreamMessage) -> None:
    """保存消息到数据库的辅助函数"""
    try:
        # 确定智能体信息
        agent_type = message.source if message.source else "unknown"
        agent_name = _get_agent_display_name(agent_type)

        # 确定处理阶段
        processing_stage = _determine_processing_stage(message)

        # 只保存重要的消息类型到数据库
        important_message_types = ['progress', 'success', 'error', 'completion', 'warning']
        important_keywords = ['完成', '失败', '错误', '成功', '开始', '生成', '解析', '保存', '导出']

        should_save = (
            message.type in important_message_types or
            message.is_final or
            message.result or
            message.error or
            any(keyword in message.content for keyword in important_keywords)
        )

        if should_save:
            # 保存到数据库
            save_success = await save_agent_message_log(
                session_id=session_id,
                message=message,
                agent_type=agent_type,
                agent_name=agent_name,
                processing_stage=processing_stage
            )

            if save_success:
                logger.debug(f"智能体消息已保存到数据库: {session_id} - {agent_type}")
            else:
                logger.warning(f"智能体消息保存失败: {session_id} - {agent_type}")

        # 如果是最终消息，更新会话日志摘要
        if message.is_final or message.type == 'completion':
            await update_session_logs_summary(session_id)
            logger.debug(f"会话日志摘要已更新: {session_id}")

    except Exception as e:
        logger.error(f"保存智能体消息到数据库失败: {session_id} - {str(e)}", exc_info=True)


class GenerateRequest(BaseModel):
    """测试用例生成请求"""
    requirement_text: Optional[str] = Field(None, description="直接输入的需求文本")
    analysis_target: str = Field("生成测试用例", description="分析目标")
    generate_mind_map: bool = Field(True, description="是否生成思维导图")
    export_excel: bool = Field(False, description="是否导出Excel")
    max_test_cases: Optional[int] = Field(None, description="最大测试用例数量")
    tags: List[str] = Field(default_factory=list, description="标签")


class GenerateResponse(BaseModel):
    """测试用例生成响应"""
    session_id: str = Field(..., description="会话ID", alias="sessionId")
    upload_url: Optional[str] = Field(None, description="文件上传URL（如需要）", alias="uploadUrl")
    stream_url: str = Field(..., description="流式进度URL", alias="streamUrl")
    status: str = Field(..., description="状态")
    input_type: str = Field(..., description="输入类型：file/text", alias="inputType")
    created_at: str = Field(..., description="创建时间", alias="createdAt")

    class Config:
        populate_by_name = True


class SessionStatusResponse(BaseModel):
    """会话状态响应"""
    session_id: str = Field(..., alias="sessionId")
    status: str  # created, processing, completed, failed
    input_type: str = Field(..., alias="inputType")  # file, text
    file_info: Optional[Dict[str, Any]] = Field(None, alias="fileInfo")
    progress: float = 0.0
    current_stage: str = Field("", alias="currentStage")
    selected_agent: Optional[str] = Field(None, alias="selectedAgent")
    test_cases_count: int = Field(0, alias="testCasesCount")
    created_at: str = Field(..., alias="createdAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    error: Optional[str] = None

    class Config:
        populate_by_name = True


async def cleanup_session(session_id: str, delay: int = SESSION_TIMEOUT):
    """清理过期会话"""
    await asyncio.sleep(delay)
    if session_id in active_sessions:
        logger.info(f"清理过期会话: {session_id}")
        # 删除上传的文件
        session_info = active_sessions[session_id]
        if session_info.get("file_path") and os.path.exists(session_info["file_path"]):
            try:
                os.remove(session_info["file_path"])
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")
        
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "test-case-generator",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    }


@router.post("/generate", response_model=GenerateResponse)
async def create_generation_session(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    创建测试用例生成会话
    支持直接文本输入或文件上传两种方式
    """
    try:
        session_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # 判断输入类型
        if request.requirement_text:
            # 直接文本输入
            input_type = "text"
            upload_url = None

            # 立即开始处理文本需求
            session_info = {
                "session_id": session_id,
                "status": "processing",
                "input_type": input_type,
                "requirement_text": request.requirement_text,
                "analysis_target": request.analysis_target,
                "generate_mind_map": request.generate_mind_map,
                "export_excel": request.export_excel,
                "max_test_cases": request.max_test_cases,
                "tags": request.tags,
                "created_at": current_time.isoformat(),
                "progress": 0.0,
                "current_stage": "开始处理文本需求"
            }

            active_sessions[session_id] = session_info
            message_queues[session_id] = asyncio.Queue()

            # 保存会话到数据库
            session_type = determine_session_type(input_type, request.analysis_target)
            config_data = extract_session_config(session_info)
            input_data = extract_session_input_data(session_info)

            await create_processing_session(
                session_id=session_id,
                session_type=session_type,
                config_data=config_data,
                input_data=input_data,
                agent_type="test_case_generator"
            )

            # 更新状态为处理中
            await update_session_status(session_id, SessionStatus.PROCESSING)

            # 启动文本处理任务
            background_tasks.add_task(process_text_requirement, session_id)
            
        else:
            # 文件上传模式
            input_type = "file"
            upload_url = f"/api/v1/generate/upload/{session_id}"

            session_info = {
                "session_id": session_id,
                "status": "created",
                "input_type": input_type,
                "analysis_target": request.analysis_target,
                "generate_mind_map": request.generate_mind_map,
                "export_excel": request.export_excel,
                "max_test_cases": request.max_test_cases,
                "tags": request.tags,
                "created_at": current_time.isoformat(),
                "progress": 0.0,
                "current_stage": "等待文件上传"
            }

            active_sessions[session_id] = session_info
            message_queues[session_id] = asyncio.Queue()

            # 保存会话到数据库
            session_type = determine_session_type(input_type, request.analysis_target)
            config_data = extract_session_config(session_info)
            input_data = extract_session_input_data(session_info)

            await create_processing_session(
                session_id=session_id,
                session_type=session_type,
                config_data=config_data,
                input_data=input_data,
                agent_type="test_case_generator"
            )
        
        # 添加会话清理任务
        background_tasks.add_task(cleanup_session, session_id)
        
        logger.info(f"创建测试用例生成会话: {session_id}, 类型: {input_type}")

        return GenerateResponse(
            session_id=session_id,
            upload_url=upload_url,
            stream_url=f"/api/v1/generate/stream/{session_id}",
            status=session_info["status"],
            input_type=input_type,
            created_at=current_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"创建生成会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.post("/upload/{session_id}")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    上传文件并自动选择智能体进行处理
    支持文档、图片、视频、API规范、数据库Schema等多种文件类型
    """
    try:
        # 检查会话是否存在
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        session_info = active_sessions[session_id]
        
        if session_info["input_type"] != "file":
            raise HTTPException(status_code=400, detail="该会话不支持文件上传")
        
        # 获取文件扩展名并选择智能体
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in FILE_TYPE_TO_AGENT_MAPPING:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        selected_agent = FILE_TYPE_TO_AGENT_MAPPING[file_extension]
        
        # 检查文件大小
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # 根据文件类型设置大小限制
        max_size_mb = 500 if selected_agent == AgentTypes.VIDEO_ANALYZER.value else 50
        if file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大: {file_size_mb:.1f}MB，最大支持{max_size_mb}MB"
            )
        
        # 创建上传目录
        upload_dir = Path("uploads") / selected_agent.replace("_", "s")  # video_analyzer -> videos
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{session_id[:8]}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # 更新会话信息
        session_info.update({
            "status": "processing",
            "file_name": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "file_size_mb": f"{file_size_mb:.1f}MB",
            "description": description,
            "selected_agent": selected_agent,
            "progress": 10.0,
            "current_stage": f"文件上传完成，使用{selected_agent}智能体分析"
        })

        # 更新数据库状态
        try:
            logger.debug(f"开始更新数据库状态: {session_id}")

            status_success = await update_session_status(
                session_id,
                SessionStatus.PROCESSING,
                output_data={"file_upload_completed": True, "selected_agent": selected_agent}
            )

            if not status_success:
                logger.error(f"数据库状态更新失败: {session_id}")
                raise Exception("数据库状态更新失败")

            progress_success = await update_session_progress(session_id, 10.0)

            if not progress_success:
                logger.error(f"数据库进度更新失败: {session_id}")
                raise Exception("数据库进度更新失败")

            logger.debug(f"数据库状态更新成功: {session_id}")

        except Exception as db_error:
            logger.error(f"数据库操作异常: {session_id} - {str(db_error)}", exc_info=True)
            # 不要重新抛出异常，继续处理其他逻辑
            # 但要记录错误状态
            session_info["db_error"] = str(db_error)

        logger.info(f"文件上传成功: {session_id}, 文件: {file.filename}, 智能体: {selected_agent}")

        # 启动文件处理任务
        if background_tasks:
            background_tasks.add_task(process_file, session_id)
        else:
            asyncio.create_task(process_file(session_id))
        
        return {
            "status": "success",
            "message": "文件上传成功，开始分析",
            "file_name": file.filename,
            "file_size_mb": f"{file_size_mb:.1f}MB",
            "selected_agent": selected_agent,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 详细的错误日志记录
        error_msg = str(e)
        error_type = type(e).__name__

        logger.error(f"文件上传失败: {session_id}")
        logger.error(f"  错误类型: {error_type}")
        logger.error(f"  错误信息: {error_msg}")
        logger.error(f"  错误参数: {e.args}")
        logger.error(f"  完整异常信息:", exc_info=True)

        # 检查是否是特定的枚举相关错误
        if error_msg == "PROCESSING" or "PROCESSING" in error_msg:
            logger.error(f"检测到可能的枚举错误: {error_msg}")
            detailed_error = f"枚举处理错误: {error_msg} (类型: {error_type})"
        else:
            detailed_error = f"文件上传失败: {error_msg}"

        raise HTTPException(status_code=500, detail=detailed_error)


async def process_text_requirement(session_id: str):
    """处理文本需求"""
    try:
        session_info = active_sessions.get(session_id)
        if not session_info:
            logger.error(f"会话信息不存在: {session_id}")
            return

        logger.info(f"开始处理文本需求: {session_id}")

        # 发送初始消息
        initial_message = StreamMessage(
            message_id=f"init-{uuid.uuid4()}",
            type="message",
            source="系统",
            content="🚀 开始处理文本需求...",
            region="process",
            platform="test_case",
            is_final=False
        )

        if session_id in message_queues:
            await message_queues[session_id].put(initial_message)

        # 创建消息回调
        async def message_callback(ctx: ClosureContext, message: StreamMessage, message_ctx: MessageContext)-> None:
            # 忽略未使用的参数
            _ = ctx, message_ctx

            logger.info(f"收到流式消息: {message.type} - {message.content[:100] if message.content else 'No content'}")

            # 将消息放入队列供前端流式显示
            if session_id in message_queues:
                await message_queues[session_id].put(message)
                logger.info(f"消息已放入队列: {session_id}")
            else:
                logger.warning(f"会话队列不存在: {session_id}")

            # 保存关键消息到数据库
            await _save_message_to_database(session_id, message)

        # 创建响应收集器
        collector = StreamResponseCollector(platform=AgentPlatform.TEST_CASE)
        collector.set_callback(message_callback)

        # 获取编排器
        orchestrator = get_test_case_orchestrator(collector=collector)

        # 创建直接需求请求
        requirement_request = DirectRequirementRequest(
            session_id=session_id,
            requirement_text=session_info["requirement_text"],
            analysis_target=session_info["analysis_target"]
        )

        logger.info(f"创建需求请求成功: {session_id}")

        # 发送进度消息
        progress_message = StreamMessage(
            message_id=f"progress-{uuid.uuid4()}",
            type="progress",
            source="系统",
            content="📝 正在分析需求文本...",
            region="process",
            platform="test_case",
            is_final=False,
            result={"progress": 20}
        )

        if session_id in message_queues:
            await message_queues[session_id].put(progress_message)

        # 更新数据库进度
        await update_session_progress(session_id, 20.0)

        # 处理需求
        logger.info(f"开始调用编排器处理需求: {session_id}")
        await orchestrator.process_direct_requirement(requirement_request)
        logger.info(f"编排器处理完成: {session_id}")

        # 发送处理完成消息
        processing_message = StreamMessage(
            message_id=f"processing-{uuid.uuid4()}",
            type="progress",
            source="系统",
            content="🔄 需求处理完成，正在生成测试用例...",
            region="process",
            platform="test_case",
            is_final=False,
            result={"progress": 80}
        )

        if session_id in message_queues:
            await message_queues[session_id].put(processing_message)

        # 更新数据库进度
        await update_session_progress(session_id, 80.0)

        # 注意：不在这里直接更新数据库状态为完成
        # 状态更新将由编排器在 _cleanup_runtime 方法中通过会话状态智能体处理

        # 处理完成后，从内存中移除会话，让后续查询从数据库获取
        logger.info(f"文本处理完成，从内存中移除会话: {session_id}")
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)

        # 发送完成消息
        completion_message = StreamMessage(
            message_id=f"completion-{uuid.uuid4()}",
            type="completion",
            source="系统",
            content="✅ 文本需求处理完成",
            region="process",
            platform="test_case",
            is_final=True
        )

        if session_id in message_queues:
            await message_queues[session_id].put(completion_message)

        logger.info(f"文本需求处理完成: {session_id}")

    except Exception as e:
        logger.error(f"文本需求处理失败: {session_id} - {e}", exc_info=True)

        # 更新数据库状态为失败
        await update_session_status(session_id, SessionStatus.FAILED, error_message=str(e))

        # 处理失败后，从内存中移除会话
        logger.info(f"文本处理失败，从内存中移除会话: {session_id}")
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)

        # 发送错误消息
        error_message = StreamMessage(
            message_id=f"error-{uuid.uuid4()}",
            type="error",
            source="系统",
            content=f"❌ 文本需求处理失败: {str(e)}",
            region="process",
            platform="test_case",
            is_final=True,
            error=str(e)
        )

        if session_id in message_queues:
            await message_queues[session_id].put(error_message)


async def process_file(session_id: str):
    """处理上传的文件"""
    try:
        session_info = active_sessions.get(session_id)
        if not session_info:
            return

        # 更新状态为处理中
        session_info["status"] = "processing"
        session_info["current_stage"] = "开始处理文件"
        await update_session_status(session_id, SessionStatus.PROCESSING)

        # 添加一个短暂延迟，确保用户能看到处理状态
        logger.info(f"文件处理开始，会话 {session_id} 状态已更新为 processing")
        await asyncio.sleep(2)  # 2秒延迟，让用户能看到处理状态

        selected_agent = session_info["selected_agent"]

        # 创建消息回调
        async def message_callback(ctx: ClosureContext, message: StreamMessage, message_ctx: MessageContext)-> None:
            # 忽略未使用的参数
            _ = ctx, message_ctx

            logger.info(f"收到流式消息: {message.type} - {message.content[:100] if message.content else 'No content'}")

            # 将消息放入队列供前端流式显示
            if session_id in message_queues:
                await message_queues[session_id].put(message)
                logger.info(f"消息已放入队列: {session_id}")
            else:
                logger.warning(f"会话队列不存在: {session_id}")

            # 保存关键消息到数据库
            await _save_message_to_database(session_id, message)

        # 创建响应收集器
        collector = StreamResponseCollector(platform=AgentPlatform.TEST_CASE)
        collector.set_callback(message_callback)

        # 获取编排器
        orchestrator = get_test_case_orchestrator(collector=collector)

        # 根据智能体类型创建相应的请求
        if selected_agent == AgentTypes.DOCUMENT_PARSER.value:
            # 根据文件扩展名推断文档类型
            file_extension = Path(session_info["file_path"]).suffix.lower()
            document_type_mapping = {
                ".pdf": "pdf",
                ".docx": "word",
                ".doc": "word",
                ".txt": "text",
                ".md": "markdown"
            }
            document_type = document_type_mapping.get(file_extension, "unknown")

            request = DocumentParseRequest(
                session_id=session_id,
                file_name=session_info["file_name"],
                file_path=session_info["file_path"],
                document_type=document_type,
                analysis_target=session_info["analysis_target"]
            )
            await orchestrator.parse_document(request)

        elif selected_agent == AgentTypes.IMAGE_ANALYZER.value:
            # 根据文件扩展名推断图片类型
            file_extension = Path(session_info["file_path"]).suffix.lower()
            image_type_mapping = {
                ".jpg": "jpeg",
                ".jpeg": "jpeg",
                ".png": "png",
                ".gif": "gif",
                ".bmp": "bmp",
                ".webp": "webp"
            }
            image_type = image_type_mapping.get(file_extension, "unknown")

            request = ImageAnalysisRequest(
                session_id=session_id,
                image_name=session_info["file_name"],
                image_path=session_info["file_path"],
                image_type=image_type,
                description=session_info.get("description"),
                analysis_target=session_info["analysis_target"]
            )
            await orchestrator.analyze_image(request)

        elif selected_agent == AgentTypes.VIDEO_ANALYZER.value:
            # 根据文件名和描述推断视频类型
            video_name = session_info["file_name"].lower()
            description = (session_info.get("description") or "").lower()

            if any(keyword in video_name or keyword in description
                   for keyword in ['screen', 'recording', '录屏', '屏幕']):
                video_type = 'screen_recording'
            elif any(keyword in video_name or keyword in description
                     for keyword in ['demo', '演示', '示例']):
                video_type = 'demo_video'
            else:
                video_type = 'screen_recording'  # 默认类型

            request = VideoAnalysisRequest(
                session_id=session_id,
                video_name=session_info["file_name"],
                video_path=session_info["file_path"],
                video_type=video_type,
                description=session_info.get("description"),
                analysis_target=session_info["analysis_target"]
            )
            await orchestrator.analyze_video(request)

        elif selected_agent == AgentTypes.API_SPEC_PARSER.value:
            # 根据文件扩展名推断规范类型
            file_extension = Path(session_info["file_path"]).suffix.lower()
            spec_type = "openapi" if file_extension in [".json", ".yaml", ".yml"] else "unknown"

            request = ApiSpecParseRequest(
                session_id=session_id,
                file_name=session_info["file_name"],
                file_path=session_info["file_path"],
                spec_type=spec_type,
                analysis_target=session_info["analysis_target"]
            )
            await orchestrator.parse_api_spec(request)

        elif selected_agent == AgentTypes.DATABASE_SCHEMA_PARSER.value:
            # 根据文件扩展名推断数据库类型
            file_extension = Path(session_info["file_path"]).suffix.lower()
            database_type = "mysql" if file_extension == ".sql" else "unknown"

            request = DatabaseSchemaParseRequest(
                session_id=session_id,
                file_name=session_info["file_name"],
                file_path=session_info["file_path"],
                database_type=database_type,
                analysis_target=session_info["analysis_target"]
            )
            await orchestrator.parse_database_schema(request)

        # 注意：不在这里直接更新数据库状态为完成
        # 状态更新将由编排器在 _cleanup_runtime 方法中通过会话状态智能体处理

        # 处理完成后，从内存中移除会话，让后续查询从数据库获取
        logger.info(f"文件处理完成，从内存中移除会话: {session_id}")
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)

        # 发送完成消息
        completion_message = StreamMessage(
            message_id=f"completion-{uuid.uuid4()}",
            type="completion",
            source="系统",
            content="✅ 文件处理任务已启动",
            region="process",
            platform="test_case",
            is_final=False
        )

        if session_id in message_queues:
            await message_queues[session_id].put(completion_message)

        logger.info(f"文件处理任务已启动: {session_id}")

    except Exception as e:
        logger.error(f"文件处理失败: {session_id} - {e}")

        # 更新数据库状态为失败
        await update_session_status(session_id, SessionStatus.FAILED, error_message=str(e))

        # 处理失败后，从内存中移除会话
        logger.info(f"文件处理失败，从内存中移除会话: {session_id}")
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)

        # 发送错误消息
        error_message = StreamMessage(
            message_id=f"error-{uuid.uuid4()}",
            type="error",
            source="系统",
            content=f"❌ 文件处理失败: {str(e)}",
            region="process",
            platform="test_case",
            is_final=True,
            error=str(e)
        )

        if session_id in message_queues:
            await message_queues[session_id].put(error_message)


@router.get("/stream/{session_id}")
async def stream_progress(session_id: str, request: Request):
    """
    流式获取处理进度
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        if session_id not in message_queues:
            message_queues[session_id] = asyncio.Queue()

        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        logger.info(f"客户端断开连接: {session_id}")
                        break

                    try:
                        message = await asyncio.wait_for(
                            message_queues[session_id].get(),
                            timeout=30.0
                        )

                        # 正确的SSE格式
                        yield f"event: {message.type}\ndata: {message.model_dump_json()}\n\n"

                        if message.is_final:
                            break

                    except asyncio.TimeoutError:
                        # 发送心跳
                        heartbeat_data = f'{{"type": "heartbeat", "timestamp": "{datetime.now().isoformat()}"}}'
                        yield f"event: heartbeat\ndata: {heartbeat_data}\n\n"

            except Exception as e:
                logger.error(f"流式响应生成失败: {session_id} - {e}")
                error_data = f'{{"type": "error", "error": "{str(e)}", "timestamp": "{datetime.now().isoformat()}"}}'
                yield f"event: error\ndata: {error_data}\n\n"

        response = EventSourceResponse(event_generator(), media_type="text/event-stream")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        response.headers["X-Accel-Buffering"] = "no"  # 禁用Nginx缓冲
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建流式响应失败: {session_id} - {e}")
        raise HTTPException(status_code=500, detail=f"创建流式响应失败: {str(e)}")


@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """获取会话状态"""
    try:
        # 首先尝试从内存中获取
        if session_id in active_sessions:
            session_info = active_sessions[session_id]
            return SessionStatusResponse(
                session_id=session_id,
                status=session_info["status"],
                input_type=session_info["input_type"],
                file_info={
                    "name": session_info.get("file_name"),
                    "size_mb": session_info.get("file_size_mb"),
                    "description": session_info.get("description")
                } if session_info["input_type"] == "file" else None,
                progress=session_info.get("progress", 0.0),
                current_stage=session_info.get("current_stage", ""),
                selected_agent=session_info.get("selected_agent"),
                test_cases_count=session_info.get("test_cases_count", 0),
                created_at=session_info["created_at"],
                completed_at=session_info.get("completed_at"),
                error=session_info.get("error")
            )

        # 如果内存中没有，尝试从数据库获取
        from app.database.connection import db_manager

        async with db_manager.get_session() as db:
            # 查询processing_sessions表
            from sqlalchemy import text
            query = text("""
                SELECT id, session_type, status, progress, agent_type,
                       processing_time, error_message, generated_count,
                       started_at, completed_at, created_at, updated_at
                FROM processing_sessions
                WHERE id = :session_id
            """)

            result = await db.execute(query, {"session_id": session_id})
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="会话不存在")

            # 转换数据库结果为响应格式
            return SessionStatusResponse(
                session_id=row.id,
                status=row.status,
                input_type="file" if row.session_type in ["document_parse", "image_analysis", "video_analysis"] else "text",
                file_info=None,  # 数据库中没有存储文件信息
                progress=float(row.progress or 0.0),
                current_stage=row.status,
                selected_agent=row.agent_type,
                test_cases_count=row.generated_count or 0,
                created_at=row.created_at,
                completed_at=row.completed_at,
                error=row.error_message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话状态失败: {session_id} - {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/sessions")
async def list_sessions():
    """列出所有会话"""
    try:
        sessions = []

        # 首先添加内存中的活跃会话
        logger.info(f"内存中的活跃会话数量: {len(active_sessions)}")
        for session_id, session_info in active_sessions.items():
            logger.info(f"内存会话 {session_id}: status={session_info['status']}, progress={session_info.get('progress', 0.0)}")
            sessions.append({
                "sessionId": session_id,
                "status": session_info["status"],
                "inputType": session_info["input_type"],
                "fileName": session_info.get("file_name"),
                "selectedAgent": session_info.get("selected_agent"),
                "progress": session_info.get("progress", 0.0),
                "createdAt": session_info["created_at"],
                "completedAt": session_info.get("completed_at")
            })

        # 然后从数据库获取历史会话（最近24小时）
        from app.database.connection import db_manager

        async with db_manager.get_session() as db:
            from sqlalchemy import text

            # 构建排除活跃会话的查询
            if active_sessions:
                placeholders = ','.join([f':session_{i}' for i in range(len(active_sessions))])
                query = text(f"""
                    SELECT id, session_type, status, progress, agent_type,
                           processing_time, error_message, generated_count,
                           started_at, completed_at, created_at, updated_at
                    FROM processing_sessions
                    WHERE id NOT IN ({placeholders})
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                params = {f'session_{i}': session_id for i, session_id in enumerate(active_sessions.keys())}
            else:
                query = text("""
                    SELECT id, session_type, status, progress, agent_type,
                           processing_time, error_message, generated_count,
                           started_at, completed_at, created_at, updated_at
                    FROM processing_sessions
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                params = {}

            result = await db.execute(query, params)
            rows = result.fetchall()

            logger.info(f"从数据库查询到 {len(rows)} 个历史会话")
            for row in rows:
                logger.info(f"数据库会话 {row.id}: status={row.status}, progress={row.progress}")
                sessions.append({
                    "sessionId": row.id,
                    "status": row.status,
                    "inputType": "file" if row.session_type in ["document_parse", "image_analysis", "video_analysis"] else "text",
                    "fileName": None,
                    "selectedAgent": row.agent_type,
                    "progress": float(row.progress or 0.0),
                    "createdAt": row.created_at,
                    "completedAt": row.completed_at
                })

        return {
            "sessions": sessions,
            "total": len(sessions)
        }

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/cancel/{session_id}")
async def cancel_generation(session_id: str):
    """取消生成任务"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        session_info = active_sessions[session_id]

        # 更新会话状态
        session_info["status"] = "cancelled"
        session_info["completed_at"] = datetime.now().isoformat()

        # 发送取消消息
        cancel_message = StreamMessage(
            message_id=f"cancel-{uuid.uuid4()}",
            type="cancelled",
            source="系统",
            content="⏹️ 生成任务已取消",
            region="process",
            platform="test_case",
            is_final=True
        )

        if session_id in message_queues:
            await message_queues[session_id].put(cancel_message)

        logger.info(f"取消生成任务: {session_id}")

        return {
            "status": "success",
            "message": "生成任务已取消",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消生成任务失败: {session_id} - {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        session_info = active_sessions[session_id]

        # 删除上传的文件
        if session_info.get("file_path") and os.path.exists(session_info["file_path"]):
            try:
                os.remove(session_info["file_path"])
                logger.info(f"删除文件: {session_info['file_path']}")
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")

        # 清理会话数据
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)

        logger.info(f"删除会话: {session_id}")

        return {
            "status": "success",
            "message": "会话已删除",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {session_id} - {e}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")
