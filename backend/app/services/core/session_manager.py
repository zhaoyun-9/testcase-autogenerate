"""
会话管理服务
负责处理会话的创建、状态管理、清理等功能
"""
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from loguru import logger
from pydantic import BaseModel
from app.core.enums import SessionStatus


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    status: SessionStatus
    input_type: str
    created_at: datetime
    updated_at: datetime
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ProcessingResult(BaseModel):
    """处理结果"""
    session_id: str
    status: str
    progress: float = 0.0
    
    # 统计信息
    total_files_processed: int = 0
    total_test_cases_generated: int = 0
    processing_time: float = 0.0
    
    # 结果数据
    generated_test_cases: List[str] = []
    mind_map_id: Optional[str] = None
    export_file_path: Optional[str] = None
    
    # 错误和警告
    errors: List[str] = []
    warnings: List[str] = []
    
    # 时间戳
    started_at: datetime
    completed_at: Optional[datetime] = None


class SessionManager:
    """会话管理器"""
    
    def __init__(self, cleanup_interval: int = 3600):
        self.sessions: Dict[str, SessionInfo] = {}
        self.processing_results: Dict[str, ProcessingResult] = {}
        self.cleanup_interval = cleanup_interval
        self.max_session_age = timedelta(hours=24)
        self._cleanup_task_started = False

    async def start_cleanup_task(self):
        """启动清理任务"""
        if not self._cleanup_task_started:
            asyncio.create_task(self._cleanup_task())
            self._cleanup_task_started = True

    def create_session(self, session_id: Optional[str] = None,
                      input_type: str = "file_upload",
                      config: Optional[Dict[str, Any]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新会话"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id in self.sessions:
            logger.warning(f"会话已存在，将覆盖: {session_id}")
        
        session_info = SessionInfo(
            session_id=session_id,
            status=SessionStatus.CREATED,
            input_type=input_type,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            config=config or {},
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session_info
        logger.info(f"创建会话: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: SessionStatus,
                             error_message: Optional[str] = None,
                             result: Optional[Dict[str, Any]] = None):
        """更新会话状态"""
        if session_id not in self.sessions:
            logger.error(f"会话不存在: {session_id}")
            return
        
        session = self.sessions[session_id]
        session.status = status
        session.updated_at = datetime.now()
        
        if error_message:
            session.error_message = error_message
        
        if result:
            session.result = result
        
        logger.info(f"更新会话状态: {session_id} -> {status.value}")
    
    def update_session_progress(self, session_id: str, progress: float):
        """更新会话进度"""
        if session_id not in self.sessions:
            logger.error(f"会话不存在: {session_id}")
            return
        
        session = self.sessions[session_id]
        session.progress = min(max(progress, 0.0), 100.0)
        session.updated_at = datetime.now()
    
    def set_processing_result(self, session_id: str, result: ProcessingResult):
        """设置处理结果"""
        self.processing_results[session_id] = result
        logger.info(f"设置处理结果: {session_id}")
    
    def get_processing_result(self, session_id: str) -> Optional[ProcessingResult]:
        """获取处理结果"""
        return self.processing_results.get(session_id)
    
    def list_sessions(self, status: Optional[SessionStatus] = None,
                     input_type: Optional[str] = None,
                     limit: int = 100) -> List[SessionInfo]:
        """列出会话"""
        sessions = list(self.sessions.values())
        
        # 过滤
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        if input_type:
            sessions = [s for s in sessions if s.input_type == input_type]
        
        # 排序（最新的在前）
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        
        return sessions[:limit]
    
    def cleanup_session(self, session_id: str):
        """清理单个会话"""
        try:
            # 清理会话信息
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            # 清理处理结果
            if session_id in self.processing_results:
                del self.processing_results[session_id]
            
            # 清理文件（通过文件处理器）
            from app.services.core.file_processor import file_processor
            file_processor.cleanup_session_files(session_id)
            
            logger.info(f"清理会话: {session_id}")
            
        except Exception as e:
            logger.error(f"清理会话失败: {session_id} - {e}")
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session.created_at > self.max_session_age:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.cleanup_session(session_id)
        
        if expired_sessions:
            logger.info(f"清理过期会话: {len(expired_sessions)} 个")
    
    async def _cleanup_task(self):
        """定期清理任务"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"清理任务失败: {e}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        total_sessions = len(self.sessions)
        status_counts = {}
        
        for session in self.sessions.values():
            status = session.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_sessions': total_sessions,
            'status_distribution': status_counts,
            'active_sessions': len([s for s in self.sessions.values() 
                                  if s.status in [SessionStatus.CREATED, SessionStatus.PROCESSING]]),
            'completed_sessions': status_counts.get('completed', 0),
            'failed_sessions': status_counts.get('failed', 0)
        }
    
    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """导出会话数据"""
        session = self.get_session(session_id)
        result = self.get_processing_result(session_id)
        
        if not session:
            return None
        
        return {
            'session_info': {
                'session_id': session.session_id,
                'status': session.status.value,
                'input_type': session.input_type,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'config': session.config,
                'metadata': session.metadata,
                'progress': session.progress,
                'error_message': session.error_message
            },
            'processing_result': result.dict() if result else None
        }
    
    def import_session_data(self, data: Dict[str, Any]) -> str:
        """导入会话数据"""
        session_data = data.get('session_info', {})
        result_data = data.get('processing_result')
        
        session_id = session_data.get('session_id')
        if not session_id:
            raise ValueError("会话ID不能为空")
        
        # 重建会话信息
        session_info = SessionInfo(
            session_id=session_id,
            status=SessionStatus(session_data.get('status', 'created')),
            input_type=session_data.get('input_type', 'file_upload'),
            created_at=datetime.fromisoformat(session_data.get('created_at')),
            updated_at=datetime.fromisoformat(session_data.get('updated_at')),
            config=session_data.get('config', {}),
            metadata=session_data.get('metadata', {}),
            progress=session_data.get('progress', 0.0),
            error_message=session_data.get('error_message')
        )
        
        self.sessions[session_id] = session_info
        
        # 重建处理结果
        if result_data:
            result = ProcessingResult(**result_data)
            self.processing_results[session_id] = result
        
        logger.info(f"导入会话数据: {session_id}")
        return session_id


# 全局实例
session_manager = SessionManager()
