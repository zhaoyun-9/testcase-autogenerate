"""
会话数据库操作工具函数
用于ProcessingSession的数据库操作
"""
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import ProcessingSession
from app.core.enums import SessionType, SessionStatus


async def create_processing_session(
    session_id: str,
    session_type: SessionType,
    project_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    config_data: Optional[Dict[str, Any]] = None,
    agent_type: Optional[str] = None
) -> bool:
    """创建处理会话记录"""
    try:
        from sqlalchemy import text
        import json

        async with db_manager.get_session() as db_session:
            await db_session.execute(text("""
                INSERT INTO processing_sessions (
                    id, session_type, status, progress, project_id,
                    input_data, config_data, agent_type, started_at
                ) VALUES (
                    :id, :session_type, :status, :progress, :project_id,
                    :input_data, :config_data, :agent_type, NOW()
                )
            """), {
                "id": session_id,
                "session_type": session_type.value,
                "status": SessionStatus.CREATED.value,
                "progress": 0.00,
                "project_id": project_id,
                "input_data": json.dumps(input_data or {}),
                "config_data": json.dumps(config_data or {}),
                "agent_type": agent_type
            })

            await db_session.commit()

            logger.info(f"创建处理会话记录成功: {session_id}")
            return True

    except Exception as e:
        logger.error(f"创建处理会话记录失败: {session_id}, 错误: {str(e)}")
        return False


async def update_session_status(
    session_id: str,
    status: SessionStatus,
    error_message: Optional[str] = None,
    output_data: Optional[Dict[str, Any]] = None,
    processing_time: Optional[float] = None,
    generated_count: Optional[int] = None
) -> bool:
    """更新会话状态"""
    try:
        from sqlalchemy import text
        import json

        # 确保 status 是正确的枚举类型
        if not isinstance(status, SessionStatus):
            logger.error(f"status 参数类型错误: {type(status)}, 期望: {SessionStatus}")
            # 尝试转换
            if isinstance(status, str):
                try:
                    status = SessionStatus(status)
                    logger.info(f"成功将字符串转换为枚举: {status}")
                except ValueError as ve:
                    logger.error(f"无法将字符串 '{status}' 转换为 SessionStatus 枚举: {ve}")
                    return False
            else:
                return False

        async with db_manager.get_session() as db_session:
            # 构建更新SQL
            update_fields = ["status = :status", "updated_at = NOW()"]
            params = {
                "id": session_id,
                "status": status.value
            }

            if error_message:
                update_fields.append("error_message = :error_message")
                params["error_message"] = error_message

            if output_data:
                update_fields.append("output_data = :output_data")
                params["output_data"] = json.dumps(output_data)

            if processing_time is not None:
                update_fields.append("processing_time = :processing_time")
                params["processing_time"] = processing_time

            if generated_count is not None:
                update_fields.append("generated_count = :generated_count")
                params["generated_count"] = generated_count

            # 设置完成时间
            if status == SessionStatus.COMPLETED:
                update_fields.append("completed_at = NOW()")
            elif status == SessionStatus.PROCESSING:
                # 只在started_at为空时设置
                update_fields.append("started_at = COALESCE(started_at, NOW())")

            sql = f"""
                UPDATE processing_sessions
                SET {', '.join(update_fields)}
                WHERE id = :id
            """

            result = await db_session.execute(text(sql), params)

            if result.rowcount == 0:
                logger.error(f"会话不存在: {session_id}")
                return False

            await db_session.commit()

            logger.info(f"更新会话状态成功: {session_id} -> {status.value}")
            return True

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__

        logger.error(f"更新会话状态失败: {session_id}")
        logger.error(f"  错误类型: {error_type}")
        logger.error(f"  错误信息: {error_msg}")
        logger.error(f"  状态值: {status} (类型: {type(status)})")
        logger.error(f"  状态.value: {status.value if hasattr(status, 'value') else 'N/A'}")
        logger.error(f"  完整异常信息:", exc_info=True)

        return False


async def update_session_progress(session_id: str, progress: float) -> bool:
    """更新会话进度"""
    try:
        from sqlalchemy import text

        async with db_manager.get_session() as db_session:
            # 限制进度范围
            progress = min(max(progress, 0.0), 100.0)

            result = await db_session.execute(text("""
                UPDATE processing_sessions
                SET progress = :progress, updated_at = NOW()
                WHERE id = :id
            """), {
                "id": session_id,
                "progress": progress
            })

            if result.rowcount == 0:
                logger.error(f"会话不存在: {session_id}")
                return False

            await db_session.commit()

            logger.debug(f"更新会话进度成功: {session_id} -> {progress}%")
            return True

    except Exception as e:
        logger.error(f"更新会话进度失败: {session_id}, 错误: {str(e)}")
        return False


async def get_processing_session(session_id: str) -> Optional[Dict[str, Any]]:
    """获取处理会话记录"""
    try:
        from sqlalchemy import text

        async with db_manager.get_session() as db_session:
            result = await db_session.execute(text("""
                SELECT id, session_type, status, progress, project_id,
                       input_data, output_data, config_data, agent_type,
                       processing_time, error_message, generated_count,
                       started_at, completed_at, created_at, updated_at
                FROM processing_sessions
                WHERE id = :id
            """), {"id": session_id})

            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "session_type": row[1],
                    "status": row[2],
                    "progress": float(row[3]) if row[3] else 0.0,
                    "project_id": row[4],
                    "input_data": row[5],
                    "output_data": row[6],
                    "config_data": row[7],
                    "agent_type": row[8],
                    "processing_time": row[9],
                    "error_message": row[10],
                    "generated_count": row[11] or 0,
                    "started_at": row[12],
                    "completed_at": row[13],
                    "created_at": row[14],
                    "updated_at": row[15]
                }

            return None

    except Exception as e:
        logger.error(f"获取处理会话记录失败: {session_id}, 错误: {str(e)}")
        return None


def determine_session_type(input_type: str, analysis_target: str = "") -> SessionType:
    """根据输入类型确定会话类型"""
    if input_type == "text":
        return SessionType.MANUAL_INPUT
    elif input_type == "file":
        # 根据分析目标确定具体类型
        if "图片" in analysis_target or "image" in analysis_target.lower():
            return SessionType.IMAGE_ANALYSIS
        elif "文档" in analysis_target or "document" in analysis_target.lower():
            return SessionType.DOCUMENT_PARSE
        elif "API" in analysis_target or "api" in analysis_target.lower():
            return SessionType.API_SPEC_PARSE
        elif "数据库" in analysis_target or "database" in analysis_target.lower():
            return SessionType.DATABASE_SCHEMA_PARSE
        elif "视频" in analysis_target or "video" in analysis_target.lower():
            return SessionType.VIDEO_ANALYSIS
        else:
            return SessionType.DOCUMENT_PARSE  # 默认为文档解析
    else:
        return SessionType.MANUAL_INPUT


def extract_session_config(session_info: Dict[str, Any]) -> Dict[str, Any]:
    """从会话信息中提取配置数据"""
    config = {}
    
    # 提取配置相关字段
    config_fields = [
        "analysis_target", "generate_mind_map", "export_excel", 
        "max_test_cases", "tags", "input_type"
    ]
    
    for field in config_fields:
        if field in session_info:
            config[field] = session_info[field]
    
    return config


def extract_session_input_data(session_info: Dict[str, Any]) -> Dict[str, Any]:
    """从会话信息中提取输入数据"""
    input_data = {}
    
    # 提取输入相关字段
    input_fields = [
        "file_path", "file_name", "file_size", "file_type",
        "text_content", "requirements", "description"
    ]
    
    for field in input_fields:
        if field in session_info:
            input_data[field] = session_info[field]
    
    return input_data
