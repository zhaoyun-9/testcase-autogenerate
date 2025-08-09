"""
智能体消息日志数据库操作工具函数
用于存储和查询智能体的关键输出信息
"""
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from app.database.connection import db_manager
from app.core.messages import StreamMessage


async def save_agent_message_log(
    session_id: str,
    message: StreamMessage,
    agent_type: str,
    agent_name: str,
    processing_stage: Optional[str] = None
) -> bool:
    """保存智能体消息日志到数据库"""
    try:
        from sqlalchemy import text

        # 确定消息类型
        message_type = _determine_message_type(message)
        
        # 提取结果数据
        result_data = message.result if message.result else None
        
        # 提取错误信息
        error_info = None
        if message.error:
            error_info = {"error": message.error}
        
        # 提取指标数据
        metrics_data = None
        if message_type == 'metrics' and result_data:
            metrics_data = result_data

        async with db_manager.get_session() as db_session:
            await db_session.execute(text("""
                INSERT INTO agent_message_logs (
                    id, session_id, message_id, agent_type, agent_name,
                    message_type, content, region, source, is_final,
                    result_data, error_info, metrics_data, processing_stage,
                    timestamp, created_at
                ) VALUES (
                    :id, :session_id, :message_id, :agent_type, :agent_name,
                    :message_type, :content, :region, :source, :is_final,
                    :result_data, :error_info, :metrics_data, :processing_stage,
                    :timestamp, NOW()
                )
            """), {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "message_id": message.message_id,
                "agent_type": agent_type,
                "agent_name": agent_name,
                "message_type": message_type,
                "content": message.content,
                "region": message.region,
                "source": message.source,
                "is_final": message.is_final,
                "result_data": json.dumps(result_data) if result_data else None,
                "error_info": json.dumps(error_info) if error_info else None,
                "metrics_data": json.dumps(metrics_data) if metrics_data else None,
                "processing_stage": processing_stage,
                "timestamp": datetime.fromisoformat(message.timestamp.replace('Z', '+00:00')) if message.timestamp else datetime.now()
            })

            await db_session.commit()
            
            logger.debug(f"保存智能体消息日志成功: {session_id} - {agent_type} - {message_type}")
            return True

    except Exception as e:
        logger.error(f"保存智能体消息日志失败: {session_id} - {str(e)}")
        return False


async def get_agent_message_logs(
    session_id: str,
    agent_type: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """获取智能体消息日志"""
    try:
        from sqlalchemy import text

        # 构建查询条件
        where_conditions = ["session_id = :session_id"]
        params = {"session_id": session_id}

        if agent_type is not None:
            where_conditions.append("agent_type = :agent_type")
            params["agent_type"] = agent_type

        if message_type is not None:
            where_conditions.append("message_type = :message_type")
            params["message_type"] = message_type

        where_clause = " AND ".join(where_conditions)

        async with db_manager.get_session() as db_session:
            result = await db_session.execute(text(f"""
                SELECT id, session_id, message_id, agent_type, agent_name,
                       message_type, content, region, source, is_final,
                       result_data, error_info, metrics_data, processing_stage,
                       timestamp, created_at
                FROM agent_message_logs
                WHERE {where_clause}
                ORDER BY timestamp ASC
                LIMIT :limit
            """), {**params, "limit": limit})

            logs = []
            for row in result.fetchall():
                log_data = {
                    "id": row[0],
                    "session_id": row[1],
                    "message_id": row[2],
                    "agent_type": row[3],
                    "agent_name": row[4],
                    "message_type": row[5],
                    "content": row[6],
                    "region": row[7],
                    "source": row[8],
                    "is_final": row[9],
                    "result_data": json.loads(row[10]) if row[10] else None,
                    "error_info": json.loads(row[11]) if row[11] else None,
                    "metrics_data": json.loads(row[12]) if row[12] else None,
                    "processing_stage": row[13],
                    "timestamp": row[14].isoformat() if row[14] else None,
                    "created_at": row[15].isoformat() if row[15] else None
                }
                logs.append(log_data)

            return logs

    except Exception as e:
        logger.error(f"获取智能体消息日志失败: {session_id} - {str(e)}")
        return []


async def update_session_logs_summary(session_id: str) -> bool:
    """更新会话的日志摘要信息"""
    try:
        from sqlalchemy import text

        # 获取会话的所有日志
        logs = await get_agent_message_logs(session_id)
        
        if not logs:
            return True

        # 生成摘要信息
        summary = _generate_logs_summary(logs)
        metrics = _extract_key_metrics(logs)
        stages = _extract_processing_stages(logs)

        async with db_manager.get_session() as db_session:
            await db_session.execute(text("""
                UPDATE processing_sessions
                SET agent_logs_summary = :summary,
                    key_metrics = :metrics,
                    processing_stages = :stages,
                    updated_at = NOW()
                WHERE id = :session_id
            """), {
                "session_id": session_id,
                "summary": json.dumps(summary),
                "metrics": json.dumps(metrics),
                "stages": json.dumps(stages)
            })

            await db_session.commit()
            
            logger.debug(f"更新会话日志摘要成功: {session_id}")
            return True

    except Exception as e:
        logger.error(f"更新会话日志摘要失败: {session_id} - {str(e)}")
        return False


def _determine_message_type(message: StreamMessage) -> str:
    """根据消息内容确定消息类型"""
    content = message.content.lower()
    
    if message.error:
        return 'error'
    elif message.type == 'completion' or message.is_final:
        return 'completion'
    elif '进度' in content or '正在' in content or '%' in content:
        return 'progress'
    elif '成功' in content or '完成' in content or '✅' in content:
        return 'success'
    elif '警告' in content or '注意' in content or '⚠️' in content:
        return 'warning'
    elif '失败' in content or '错误' in content or '❌' in content:
        return 'error'
    elif message.result and any(key in str(message.result) for key in ['time', 'count', 'size', 'duration']):
        return 'metrics'
    else:
        return 'info'


def _generate_logs_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成日志摘要"""
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
            summary["agents"][agent_type] = {"count": 0, "name": log["agent_name"]}
        summary["agents"][agent_type]["count"] += 1
        
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
                "timestamp": log["timestamp"]
            })
    
    return summary


def _extract_key_metrics(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """提取关键指标"""
    metrics = {
        "processing_time": 0.0,
        "success_rate": 0.0,
        "error_count": 0,
        "completion_count": 0
    }
    
    total_messages = len(logs)
    if total_messages == 0:
        return metrics
    
    for log in logs:
        if log["message_type"] == 'error':
            metrics["error_count"] += 1
        elif log["message_type"] == 'completion':
            metrics["completion_count"] += 1
        
        # 提取处理时间信息
        if log["metrics_data"] and "processing_time" in log["metrics_data"]:
            metrics["processing_time"] += log["metrics_data"]["processing_time"]
    
    # 计算成功率
    if total_messages > 0:
        metrics["success_rate"] = (total_messages - metrics["error_count"]) / total_messages * 100
    
    return metrics


def _extract_processing_stages(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取处理阶段信息"""
    stages = []
    current_stage = None
    
    for log in logs:
        if log["processing_stage"]:
            if current_stage != log["processing_stage"]:
                current_stage = log["processing_stage"]
                stages.append({
                    "stage": current_stage,
                    "agent": log["agent_type"],
                    "started_at": log["timestamp"],
                    "messages": []
                })
        
        if stages:
            stages[-1]["messages"].append({
                "type": log["message_type"],
                "content": log["content"],
                "timestamp": log["timestamp"]
            })
    
    return stages
