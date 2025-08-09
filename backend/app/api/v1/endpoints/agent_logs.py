"""
智能体消息日志查询API
提供智能体处理日志的查询和展示功能
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from app.utils.agent_message_log_utils import get_agent_message_logs
from app.utils.session_db_utils import get_processing_session

logger = logger.bind(module="agent_logs")
router = APIRouter()


class AgentLogResponse(BaseModel):
    """智能体日志响应"""
    id: str
    session_id: str
    message_id: str
    agent_type: str
    agent_name: str
    message_type: str
    content: str
    region: str
    source: Optional[str]
    is_final: bool
    result_data: Optional[Dict[str, Any]]
    error_info: Optional[Dict[str, Any]]
    metrics_data: Optional[Dict[str, Any]]
    processing_stage: Optional[str]
    timestamp: str
    created_at: str


class AgentLogListResponse(BaseModel):
    """智能体日志列表响应"""
    items: List[AgentLogResponse]
    total: int
    session_id: str
    session_info: Optional[Dict[str, Any]] = None


class AgentLogSummaryResponse(BaseModel):
    """智能体日志摘要响应"""
    session_id: str
    total_messages: int
    message_types: Dict[str, int]
    agents: Dict[str, Dict[str, Any]]
    processing_stages: List[str]
    errors: List[Dict[str, Any]]
    key_events: List[Dict[str, Any]]
    key_metrics: Optional[Dict[str, Any]]
    processing_stages_detail: Optional[List[Dict[str, Any]]]


@router.get("/session/{session_id}/logs", response_model=AgentLogListResponse)
async def get_session_agent_logs(
    session_id: str,
    agent_type: Optional[str] = Query(None, description="智能体类型过滤"),
    message_type: Optional[str] = Query(None, description="消息类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取会话的智能体日志"""
    try:
        # 获取日志数据
        logs = await get_agent_message_logs(
            session_id=session_id,
            agent_type=agent_type,
            message_type=message_type,
            limit=limit
        )
        
        # 获取会话信息
        session_info = await get_processing_session(session_id)
        
        # 转换为响应格式
        log_items = []
        for log in logs:
            log_items.append(AgentLogResponse(
                id=log["id"],
                session_id=log["session_id"],
                message_id=log["message_id"],
                agent_type=log["agent_type"],
                agent_name=log["agent_name"],
                message_type=log["message_type"],
                content=log["content"],
                region=log["region"],
                source=log["source"],
                is_final=log["is_final"],
                result_data=log["result_data"],
                error_info=log["error_info"],
                metrics_data=log["metrics_data"],
                processing_stage=log["processing_stage"],
                timestamp=log["timestamp"],
                created_at=log["created_at"]
            ))
        
        return AgentLogListResponse(
            items=log_items,
            total=len(log_items),
            session_id=session_id,
            session_info=session_info
        )
        
    except Exception as e:
        logger.error(f"获取会话智能体日志失败: {session_id} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")


@router.get("/session/{session_id}/summary", response_model=AgentLogSummaryResponse)
async def get_session_logs_summary(session_id: str):
    """获取会话日志摘要"""
    try:
        # 获取所有日志
        logs = await get_agent_message_logs(session_id=session_id, limit=1000)
        
        if not logs:
            raise HTTPException(status_code=404, detail="未找到会话日志")
        
        # 生成摘要统计
        summary = {
            "total_messages": len(logs),
            "message_types": {},
            "agents": {},
            "processing_stages": [],
            "errors": [],
            "key_events": []
        }
        
        for log in logs:
            # 统计消息类型
            msg_type = log["message_type"]
            summary["message_types"][msg_type] = summary["message_types"].get(msg_type, 0) + 1
            
            # 统计智能体
            agent_type = log["agent_type"]
            if agent_type not in summary["agents"]:
                summary["agents"][agent_type] = {
                    "count": 0, 
                    "name": log["agent_name"],
                    "first_message": log["timestamp"],
                    "last_message": log["timestamp"]
                }
            summary["agents"][agent_type]["count"] += 1
            summary["agents"][agent_type]["last_message"] = log["timestamp"]
            
            # 收集处理阶段
            if log["processing_stage"] and log["processing_stage"] not in summary["processing_stages"]:
                summary["processing_stages"].append(log["processing_stage"])
            
            # 收集错误信息
            if msg_type == 'error':
                summary["errors"].append({
                    "agent": agent_type,
                    "content": log["content"],
                    "timestamp": log["timestamp"]
                })
            
            # 收集关键事件
            if msg_type in ['success', 'completion'] or log["is_final"]:
                summary["key_events"].append({
                    "agent": agent_type,
                    "content": log["content"],
                    "timestamp": log["timestamp"],
                    "result_data": log["result_data"]
                })
        
        # 获取会话的关键指标和处理阶段详情
        session_info = await get_processing_session(session_id)
        key_metrics = None
        processing_stages_detail = None
        
        if session_info:
            import json
            if session_info.get("key_metrics"):
                try:
                    key_metrics = json.loads(session_info["key_metrics"]) if isinstance(session_info["key_metrics"], str) else session_info["key_metrics"]
                except:
                    pass
            
            if session_info.get("processing_stages"):
                try:
                    processing_stages_detail = json.loads(session_info["processing_stages"]) if isinstance(session_info["processing_stages"], str) else session_info["processing_stages"]
                except:
                    pass
        
        return AgentLogSummaryResponse(
            session_id=session_id,
            total_messages=summary["total_messages"],
            message_types=summary["message_types"],
            agents=summary["agents"],
            processing_stages=summary["processing_stages"],
            errors=summary["errors"],
            key_events=summary["key_events"],
            key_metrics=key_metrics,
            processing_stages_detail=processing_stages_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话日志摘要失败: {session_id} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取摘要失败: {str(e)}")


@router.get("/agents/performance")
async def get_agents_performance():
    """获取智能体性能统计"""
    try:
        from sqlalchemy import text
        from app.database.connection import db_manager
        
        async with db_manager.get_session() as db_session:
            result = await db_session.execute(text("""
                SELECT 
                    agent_type,
                    agent_name,
                    COUNT(DISTINCT session_id) as sessions_handled,
                    COUNT(id) as total_messages,
                    AVG(CASE WHEN message_type = 'error' THEN 1 ELSE 0 END) * 100 as error_rate,
                    AVG(CASE WHEN message_type = 'success' THEN 1 ELSE 0 END) * 100 as success_rate,
                    COUNT(DISTINCT processing_stage) as stages_count,
                    MIN(timestamp) as first_activity,
                    MAX(timestamp) as last_activity
                FROM agent_message_logs
                GROUP BY agent_type, agent_name
                ORDER BY sessions_handled DESC
            """))
            
            performance_data = []
            for row in result.fetchall():
                performance_data.append({
                    "agent_type": row[0],
                    "agent_name": row[1],
                    "sessions_handled": row[2],
                    "total_messages": row[3],
                    "error_rate": float(row[4]) if row[4] else 0.0,
                    "success_rate": float(row[5]) if row[5] else 0.0,
                    "stages_count": row[6],
                    "first_activity": row[7].isoformat() if row[7] else None,
                    "last_activity": row[8].isoformat() if row[8] else None
                })
            
            return {
                "agents": performance_data,
                "total_agents": len(performance_data),
                "generated_at": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"获取智能体性能统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")


@router.delete("/session/{session_id}/logs")
async def delete_session_logs(session_id: str):
    """删除会话的所有日志"""
    try:
        from sqlalchemy import text
        from app.database.connection import db_manager
        
        async with db_manager.get_session() as db_session:
            result = await db_session.execute(text("""
                DELETE FROM agent_message_logs WHERE session_id = :session_id
            """), {"session_id": session_id})
            
            deleted_count = result.rowcount
            await db_session.commit()
            
            logger.info(f"删除会话日志: {session_id}, 删除数量: {deleted_count}")
            
            return {
                "status": "success",
                "message": f"已删除 {deleted_count} 条日志",
                "session_id": session_id,
                "deleted_count": deleted_count
            }
        
    except Exception as e:
        logger.error(f"删除会话日志失败: {session_id} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除日志失败: {str(e)}")
