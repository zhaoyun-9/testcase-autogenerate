"""
需求存储智能体
专门负责将解析出来的需求数据保存到数据库
"""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.database.connection import db_manager
from app.database.repositories.requirement_repository import RequirementRepository
from app.database.models.requirement import (
    RequirementCreateRequest, RequirementResponse,
    RequirementType, RequirementPriority, RequirementStatus
)


class RequirementSaveRequest(BaseModel):
    """需求保存请求"""
    session_id: str = Field(..., description="会话ID")
    document_id: Optional[str] = Field(None, description="文档ID")
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    requirements: List[Dict[str, Any]] = Field(..., description="需求数据列表")
    project_id: Optional[str] = Field(None, description="项目ID")
    ai_model_info: Optional[Dict[str, Any]] = Field(None, description="AI模型信息")


class RequirementSaveResponse(BaseModel):
    """需求保存响应"""
    session_id: str = Field(..., description="会话ID")
    success: bool = Field(..., description="是否成功")
    saved_count: int = Field(0, description="保存成功的数量")
    failed_count: int = Field(0, description="保存失败的数量")
    saved_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="保存成功的需求")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    processing_time: float = Field(0.0, description="处理时间")


@type_subscription(topic_type=TopicTypes.REQUIREMENT_SAVER.value)
class RequirementSaverAgent(BaseAgent):
    """
    需求存储智能体
    
    职责：
    1. 接收需求保存请求
    2. 数据验证和转换
    3. 批量保存需求到数据库
    4. 事务管理和错误处理
    5. 保存结果反馈
    """

    def __init__(self, **kwargs):
        """初始化需求存储智能体"""
        super().__init__(
            agent_id=AgentTypes.REQUIREMENT_SAVER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.REQUIREMENT_SAVER.value, "需求存储智能体"),
            **kwargs
        )

        # 初始化仓储
        self.requirement_repository = RequirementRepository()

        # 初始化性能指标
        self.save_metrics = {
            "total_requests": 0,
            "successful_saves": 0,
            "failed_saves": 0,
            "total_requirements_saved": 0,
            "average_processing_time": 0.0
        }

        logger.info(f"需求存储智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_requirement_save_request(
        self, 
        message: RequirementSaveRequest, 
        ctx: MessageContext
    ) -> RequirementSaveResponse:
        """处理需求保存请求"""
        start_time = datetime.now()
        self.save_metrics["total_requests"] += 1

        try:
            logger.info(f"开始处理需求保存请求: {message.session_id}")

            await self.send_response(
                f"💾 开始保存 {len(message.requirements)} 个需求到数据库...",
                region="process"
            )

            # 数据验证
            if not await self._validate_save_request(message):
                return await self._handle_validation_error(message, start_time)

            # 批量保存处理
            save_result = await self._save_requirements_with_retry(message)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            save_result.processing_time = processing_time

            # 更新指标
            if save_result.success:
                self.save_metrics["successful_saves"] += 1
                self.save_metrics["total_requirements_saved"] += save_result.saved_count
            else:
                self.save_metrics["failed_saves"] += 1

            self._update_average_processing_time(start_time)

            # 发送响应
            await self._send_save_response(save_result)

            # 发布保存结果到流式输出
            await self.publish_message(
                save_result,
                topic_id=TopicId(type=TopicTypes.STREAM_OUTPUT.value, source=self.id.key)
            )

            return save_result

        except Exception as e:
            return await self._handle_save_error(message, e, start_time)

    async def _validate_save_request(self, message: RequirementSaveRequest) -> bool:
        """验证保存请求"""
        if not message.requirements:
            logger.warning(f"保存请求中没有需求数据: {message.session_id}")
            return False

        if len(message.requirements) > 500:  # 限制批量大小
            logger.warning(f"批量保存数量过大: {len(message.requirements)}")
            return False

        return True

    async def _save_requirements_with_retry(
        self, 
        message: RequirementSaveRequest,
        max_retries: int = 3
    ) -> RequirementSaveResponse:
        """带重试的需求保存"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self._save_requirements(message)
            except Exception as e:
                last_error = e
                logger.warning(f"需求保存尝试 {attempt + 1} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    await self.send_response(f"⚠️ 保存失败，正在重试 ({attempt + 2}/{max_retries})...")
                    # 简单的延迟重试
                    import asyncio
                    await asyncio.sleep(1.0 * (attempt + 1))
        
        # 所有重试都失败
        return RequirementSaveResponse(
            session_id=message.session_id,
            success=False,
            errors=[f"保存失败，已重试 {max_retries} 次: {str(last_error)}"]
        )

    async def _save_requirements(self, message: RequirementSaveRequest) -> RequirementSaveResponse:
        """保存需求到数据库"""
        saved_requirements = []
        errors = []
        
        try:
            async with db_manager.get_session() as session:
                # 转换需求数据
                requirement_requests = []
                for i, req_data in enumerate(message.requirements):
                    try:
                        create_request = await self._convert_to_create_request(req_data, message)
                        requirement_requests.append(create_request)
                    except Exception as e:
                        error_msg = f"需求 {i+1} 数据转换失败: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)

                if not requirement_requests:
                    return RequirementSaveResponse(
                        session_id=message.session_id,
                        success=False,
                        errors=["没有有效的需求数据可以保存"]
                    )

                # 批量保存需求
                await self.send_response(f"💾 正在批量保存 {len(requirement_requests)} 个需求...")
                
                saved_reqs = await self.requirement_repository.batch_create_requirements(
                    session,
                    requirement_requests
                )

                # 记录成功保存的需求
                for req in saved_reqs:
                    saved_requirements.append({
                        "id": req.id,
                        "requirement_id": req.requirement_id,
                        "title": req.title,
                        "requirement_type": req.requirement_type,
                        "priority": req.priority,
                        "status": req.status
                    })

                success_count = len(saved_requirements)
                failed_count = len(errors)

                await self.send_response(
                    f"✅ 需求保存完成: 成功 {success_count} 个，失败 {failed_count} 个"
                )

                return RequirementSaveResponse(
                    session_id=message.session_id,
                    success=True,
                    saved_count=success_count,
                    failed_count=failed_count,
                    saved_requirements=saved_requirements,
                    errors=errors
                )

        except Exception as e:
            logger.error(f"批量保存需求失败: {str(e)}")
            return RequirementSaveResponse(
                session_id=message.session_id,
                success=False,
                errors=[f"数据库操作失败: {str(e)}"]
            )

    async def _convert_to_create_request(
        self, 
        req_data: Dict[str, Any], 
        message: RequirementSaveRequest
    ) -> RequirementCreateRequest:
        """转换为需求创建请求"""
        # 映射需求类型
        req_type_mapping = {
            "functional": RequirementType.FUNCTIONAL,
            "non-functional": RequirementType.NON_FUNCTIONAL,
            "business": RequirementType.BUSINESS,
            "technical": RequirementType.TECHNICAL,
            "interface": RequirementType.INTERFACE,
            "performance": RequirementType.PERFORMANCE,
            "security": RequirementType.SECURITY,
            "usability": RequirementType.USABILITY
        }

        # 映射优先级
        priority_mapping = {
            "high": RequirementPriority.HIGH,
            "medium": RequirementPriority.MEDIUM,
            "low": RequirementPriority.LOW
        }

        # 获取需求类型
        req_type_str = req_data.get("type", "functional").lower()
        requirement_type = req_type_mapping.get(req_type_str, RequirementType.FUNCTIONAL)

        # 获取优先级
        priority_str = req_data.get("priority", "medium").lower()
        priority = priority_mapping.get(priority_str, RequirementPriority.MEDIUM)

        # 生成需求ID（如果没有提供）
        requirement_id = req_data.get("id") or f"REQ-{uuid.uuid4().hex[:8].upper()}"

        return RequirementCreateRequest(
            requirement_id=requirement_id,
            title=req_data.get("title", "未命名需求"),
            description=req_data.get("description", ""),
            requirement_type=requirement_type,
            priority=priority,
            status=RequirementStatus.DRAFT,
            project_id=message.project_id,
            document_id=message.document_id,
            session_id=message.session_id,
            source_file_path=message.file_path,
            source_section=req_data.get("section"),
            ai_generated=True,
            ai_confidence=req_data.get("confidence", 0.8),
            ai_model_info=message.ai_model_info or {
                "model": "deepseek-chat",
                "generation_time": datetime.now().isoformat(),
                "agent_version": "1.0",
                "session_id": message.session_id
            },
            extra_metadata={
                "source_file": message.file_name,
                "original_data": req_data
            }
        )

    async def _handle_validation_error(
        self, 
        message: RequirementSaveRequest, 
        start_time: datetime
    ) -> RequirementSaveResponse:
        """处理验证错误"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        error_response = RequirementSaveResponse(
            session_id=message.session_id,
            success=False,
            errors=["请求数据验证失败"],
            processing_time=processing_time
        )
        
        await self._send_save_response(error_response)
        return error_response

    async def _handle_save_error(
        self, 
        message: RequirementSaveRequest, 
        error: Exception, 
        start_time: datetime
    ) -> RequirementSaveResponse:
        """处理保存错误"""
        processing_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"需求保存失败: {str(error)}"
        
        logger.error(error_msg)
        self.save_metrics["failed_saves"] += 1
        
        error_response = RequirementSaveResponse(
            session_id=message.session_id,
            success=False,
            errors=[error_msg],
            processing_time=processing_time
        )
        
        await self._send_save_response(error_response)
        return error_response

    async def _send_save_response(self, response: RequirementSaveResponse):
        """发送保存响应"""
        if response.success:
            await self.send_response(
                f"✅ 需求保存成功: {response.saved_count} 个需求已保存到数据库",
                region="result"
            )
        else:
            await self.send_response(
                f"❌ 需求保存失败: {'; '.join(response.errors)}",
                region="error"
            )

    def _update_average_processing_time(self, start_time: datetime):
        """更新平均处理时间"""
        processing_time = (datetime.now() - start_time).total_seconds()
        total_requests = self.save_metrics["total_requests"]
        
        if total_requests == 1:
            self.save_metrics["average_processing_time"] = processing_time
        else:
            current_avg = self.save_metrics["average_processing_time"]
            self.save_metrics["average_processing_time"] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )

    async def get_save_metrics(self) -> Dict[str, Any]:
        """获取保存指标"""
        return {
            **self.save_metrics,
            "agent_name": self.agent_name,
            "agent_id": self.agent_id
        }
