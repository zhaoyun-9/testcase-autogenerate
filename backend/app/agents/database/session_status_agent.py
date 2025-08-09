"""
会话状态更新智能体 - 优化版本
专门负责更新会话状态，确保状态更新的时机正确
遵循单一职责原则，专注于会话状态管理
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages import StreamMessage
from app.core.enums import SessionStatus
from app.utils.session_db_utils import update_session_status, update_session_progress


class SessionStatusUpdateRequest(BaseModel):
    """会话状态更新请求"""
    session_id: str = Field(..., description="会话ID")
    new_status: SessionStatus = Field(..., description="新状态")
    progress: Optional[float] = Field(None, description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误信息")
    processing_time: Optional[float] = Field(None, description="处理时间")
    generated_count: Optional[int] = Field(None, description="生成数量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class SessionStatusUpdateResponse(BaseModel):
    """会话状态更新响应"""
    session_id: str = Field(..., description="会话ID")
    success: bool = Field(..., description="是否成功")
    old_status: Optional[str] = Field(None, description="原状态")
    new_status: str = Field(..., description="新状态")
    processing_time: float = Field(0.0, description="处理时间")
    error_message: Optional[str] = Field(None, description="错误信息")


@type_subscription(topic_type=TopicTypes.SESSION_STATUS.value)
class SessionStatusAgent(BaseAgent):
    """
    会话状态更新智能体 - 优化版本

    职责:
    1. 接收会话状态更新请求
    2. 数据验证和状态转换
    3. 数据库状态更新操作
    4. 状态更新结果反馈
    5. 性能监控和错误处理

    设计原则:
    - 单一职责：专注于会话状态管理
    - 事务安全：确保状态更新的一致性
    - 错误恢复：完善的错误处理和重试机制
    - 性能监控：详细的操作指标统计
    """

    def __init__(self, **kwargs):
        """初始化会话状态更新智能体"""
        super().__init__(
            agent_id=AgentTypes.SESSION_STATUS.value,
            agent_name=AGENT_NAMES.get(AgentTypes.SESSION_STATUS.value, "会话状态更新智能体"),
            **kwargs
        )

        # 初始化性能指标
        self.status_metrics = {
            "total_requests": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "status_transitions": {},
            "average_processing_time": 0.0,
            "error_types": {}
        }

        # 状态更新配置
        self.update_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "enable_validation": True,
            "enable_metrics": True
        }

        logger.info(f"会话状态更新智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_session_status_update_request(
        self,
        message: SessionStatusUpdateRequest,
        ctx: MessageContext
    ) -> SessionStatusUpdateResponse:
        """
        处理会话状态更新请求 - 优化版本

        流程:
        1. 数据验证
        2. 状态更新处理
        3. 进度更新（如果需要）
        4. 错误处理和重试
        5. 结果反馈
        """
        start_time = datetime.now()
        self.status_metrics["total_requests"] += 1

        try:
            logger.info(f"开始处理会话状态更新请求: {message.session_id}")

            await self.send_response(
                f"🔄 开始更新会话状态: {message.session_id} -> {message.new_status.value}",
                region="process"
            )

            # 数据验证
            if not await self._validate_status_update_request(message):
                return await self._handle_validation_error(message, start_time)

            # 状态更新处理
            update_result = await self._update_session_status_with_retry(message)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            update_result.processing_time = processing_time

            # 更新指标
            if update_result.success:
                self.status_metrics["successful_updates"] += 1
                self._track_status_transition(update_result.old_status, update_result.new_status)
            else:
                self.status_metrics["failed_updates"] += 1
                self._track_error_type(update_result.error_message)

            self._update_average_processing_time(start_time)

            # 发送响应
            await self._send_status_update_response(update_result)

            # 发布更新结果到流式输出
            await self.publish_message(
                update_result,
                topic_id=TopicId(type=TopicTypes.STREAM_OUTPUT.value, source=self.id.key)
            )

            return update_result

        except Exception as e:
            return await self._handle_status_update_error(message, e, start_time)

    async def _validate_status_update_request(self, message: SessionStatusUpdateRequest) -> bool:
        """验证状态更新请求"""
        if not message.session_id or not message.session_id.strip():
            logger.warning("会话ID为空")
            return False

        if not isinstance(message.new_status, SessionStatus):
            logger.warning(f"无效的状态类型: {type(message.new_status)}")
            return False

        if message.progress is not None and (message.progress < 0 or message.progress > 100):
            logger.warning(f"无效的进度值: {message.progress}")
            return False

        return True

    async def _handle_validation_error(
        self,
        message: SessionStatusUpdateRequest,
        start_time: datetime
    ) -> SessionStatusUpdateResponse:
        """处理验证错误"""
        error_response = SessionStatusUpdateResponse(
            session_id=message.session_id,
            success=False,
            new_status=message.new_status.value,
            processing_time=(datetime.now() - start_time).total_seconds(),
            error_message="数据验证失败"
        )

        await self.send_response(
            "❌ 会话状态更新请求验证失败",
            is_final=True
        )

        return error_response

    async def _update_session_status_with_retry(
        self,
        message: SessionStatusUpdateRequest
    ) -> SessionStatusUpdateResponse:
        """带重试的状态更新"""
        last_error = None

        for attempt in range(self.update_config["max_retries"]):
            try:
                if attempt > 0:
                    await self.send_response(f"🔄 第 {attempt + 1} 次重试状态更新...")
                    import asyncio
                    await asyncio.sleep(self.update_config["retry_delay"])

                return await self._update_session_status_to_database(message)

            except Exception as e:
                last_error = e
                logger.warning(f"状态更新尝试 {attempt + 1} 失败: {str(e)}")

        # 所有重试都失败
        return SessionStatusUpdateResponse(
            session_id=message.session_id,
            success=False,
            new_status=message.new_status.value,
            error_message=f"重试 {self.update_config['max_retries']} 次后仍然失败: {str(last_error)}"
        )

    async def _update_session_status_to_database(
        self,
        message: SessionStatusUpdateRequest
    ) -> SessionStatusUpdateResponse:
        """更新会话状态到数据库"""
        try:
            # 获取当前状态（用于记录状态转换）
            old_status = await self._get_current_session_status(message.session_id)

            # 更新数据库中的会话状态
            success = await update_session_status(
                session_id=message.session_id,
                status=message.new_status,
                error_message=message.error_message,
                processing_time=message.processing_time,
                generated_count=message.generated_count
            )

            if not success:
                return SessionStatusUpdateResponse(
                    session_id=message.session_id,
                    success=False,
                    new_status=message.new_status.value,
                    error_message="数据库状态更新失败"
                )

            # 如果有进度信息，也更新进度
            if message.progress is not None:
                progress_success = await update_session_progress(
                    message.session_id,
                    message.progress
                )
                if not progress_success:
                    logger.warning(f"进度更新失败: {message.session_id}")

            # 构建成功响应
            response = SessionStatusUpdateResponse(
                session_id=message.session_id,
                success=True,
                old_status=old_status,
                new_status=message.new_status.value
            )

            logger.info(f"会话状态更新成功: {message.session_id} {old_status} -> {message.new_status.value}")
            return response

        except Exception as e:
            logger.error(f"更新会话状态到数据库异常: {str(e)}")
            return SessionStatusUpdateResponse(
                session_id=message.session_id,
                success=False,
                new_status=message.new_status.value,
                error_message=str(e)
            )

    async def _get_current_session_status(self, session_id: str) -> Optional[str]:
        """获取当前会话状态"""
        try:
            from app.utils.session_db_utils import get_processing_session
            session_data = await get_processing_session(session_id)
            return session_data.get("status") if session_data else None
        except Exception as e:
            logger.warning(f"获取当前会话状态失败: {str(e)}")
            return None

    async def _send_status_update_response(self, response: SessionStatusUpdateResponse):
        """发送状态更新响应"""
        if response.success:
            status_change = f"{response.old_status} -> {response.new_status}" if response.old_status else response.new_status
            await self.send_response(
                f"✅ 会话状态更新完成: {status_change}",
                is_final=True,
                result=response.model_dump()
            )
        else:
            await self.send_response(
                f"❌ 会话状态更新失败: {response.error_message}",
                is_final=True,
                result=response.model_dump()
            )

    async def _handle_status_update_error(
        self,
        message: SessionStatusUpdateRequest,
        error: Exception,
        start_time: datetime
    ) -> SessionStatusUpdateResponse:
        """处理状态更新错误"""
        logger.error(f"会话状态更新失败: {str(error)}")
        self.status_metrics["failed_updates"] += 1
        self._track_error_type(str(error))

        error_response = SessionStatusUpdateResponse(
            session_id=message.session_id,
            success=False,
            new_status=message.new_status.value,
            processing_time=(datetime.now() - start_time).total_seconds(),
            error_message=str(error)
        )

        await self.send_response(
            f"❌ 会话状态更新异常: {str(error)}",
            is_final=True
        )

        await self.publish_message(
            error_response,
            topic_id=TopicId(type=TopicTypes.STREAM_OUTPUT.value, source=self.id.key)
        )

        return error_response

    def _track_status_transition(self, old_status: Optional[str], new_status: str):
        """跟踪状态转换"""
        if old_status:
            transition_key = f"{old_status}->{new_status}"
            self.status_metrics["status_transitions"][transition_key] = (
                self.status_metrics["status_transitions"].get(transition_key, 0) + 1
            )

    def _track_error_type(self, error_message: Optional[str]):
        """跟踪错误类型"""
        if error_message:
            # 简化错误类型分类
            if "验证" in error_message:
                error_type = "validation_error"
            elif "数据库" in error_message:
                error_type = "database_error"
            elif "重试" in error_message:
                error_type = "retry_exhausted"
            else:
                error_type = "unknown_error"

            self.status_metrics["error_types"][error_type] = (
                self.status_metrics["error_types"].get(error_type, 0) + 1
            )

    def _update_average_processing_time(self, start_time: datetime):
        """更新平均处理时间"""
        processing_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.status_metrics["average_processing_time"]
        total_requests = self.status_metrics["total_requests"]

        # 计算新的平均值
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.status_metrics["average_processing_time"] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        total_requests = max(self.status_metrics["total_requests"], 1)
        successful_updates = self.status_metrics["successful_updates"]

        return {
            **self.status_metrics,
            "success_rate": (successful_updates / total_requests) * 100,
            "most_common_transitions": self._get_top_transitions(),
            "most_common_errors": self._get_top_errors(),
            "agent_name": self.agent_name,
            "agent_id": self.id.key
        }

    def _get_top_transitions(self, limit: int = 5) -> Dict[str, int]:
        """获取最常见的状态转换"""
        transitions = self.status_metrics["status_transitions"]
        return dict(sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:limit])

    def _get_top_errors(self, limit: int = 5) -> Dict[str, int]:
        """获取最常见的错误类型"""
        errors = self.status_metrics["error_types"]
        return dict(sorted(errors.items(), key=lambda x: x[1], reverse=True)[:limit])

    def reset_metrics(self):
        """重置性能指标"""
        self.status_metrics = {
            "total_requests": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "status_transitions": {},
            "average_processing_time": 0.0,
            "error_types": {}
        }
        logger.info(f"已重置 {self.agent_name} 的性能指标")

    def update_config(self, config_updates: Dict[str, Any]):
        """更新配置"""
        for key, value in config_updates.items():
            if key in self.update_config:
                old_value = self.update_config[key]
                self.update_config[key] = value
                logger.info(f"更新配置 {key}: {old_value} → {value}")
            else:
                logger.warning(f"未知的配置项: {key}")

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.update_config.copy()

    async def batch_update_session_status(
        self,
        updates: List[SessionStatusUpdateRequest]
    ) -> List[SessionStatusUpdateResponse]:
        """批量更新会话状态"""
        results = []

        await self.send_response(f"🔄 开始批量更新 {len(updates)} 个会话状态...")

        for i, update_request in enumerate(updates):
            try:
                await self.send_response(f"📝 处理第 {i+1}/{len(updates)} 个状态更新...")

                # 创建模拟的消息上下文
                from autogen_core import MessageContext
                mock_ctx = MessageContext(sender=self.id, topic_id=TopicId(type="mock", source="batch"))

                result = await self.handle_session_status_update_request(update_request, mock_ctx)
                results.append(result)

            except Exception as e:
                logger.error(f"批量更新第 {i+1} 个会话状态失败: {str(e)}")
                error_result = SessionStatusUpdateResponse(
                    session_id=update_request.session_id,
                    success=False,
                    new_status=update_request.new_status.value,
                    error_message=str(e)
                )
                results.append(error_result)

        successful_count = sum(1 for r in results if r.success)
        await self.send_response(
            f"✅ 批量状态更新完成: 成功 {successful_count}/{len(updates)} 个",
            is_final=True
        )

        return results


class SessionStatusManager:
    """会话状态管理器 - 优化版本，提供便捷的状态更新方法"""

    def __init__(self, runtime=None):
        self.runtime = runtime
        self.logger = logger.bind(component="session_status_manager")

    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None,
        generated_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送会话状态更新请求 - 优化版本

        Args:
            session_id: 会话ID
            status: 新状态
            progress: 进度百分比
            error_message: 错误信息（如果有）
            processing_time: 处理时间（秒）
            generated_count: 生成的测试用例数量
            metadata: 额外元数据

        Returns:
            bool: 是否成功发送更新请求
        """
        try:
            if not self.runtime:
                self.logger.warning("运行时未初始化，直接调用数据库更新")
                return await update_session_status(
                    session_id=session_id,
                    status=status,
                    error_message=error_message,
                    processing_time=processing_time,
                    generated_count=generated_count
                )

            # 创建状态更新请求
            update_request = SessionStatusUpdateRequest(
                session_id=session_id,
                new_status=status,
                progress=progress,
                error_message=error_message,
                processing_time=processing_time,
                generated_count=generated_count,
                metadata=metadata
            )

            # 发送消息给会话状态智能体
            await self.runtime.send_message(
                update_request,
                recipient=AgentTypes.SESSION_STATUS.value
            )

            self.logger.info(f"会话状态更新请求已发送: {session_id} -> {status.value}")
            return True

        except Exception as e:
            self.logger.error(f"发送会话状态更新请求失败: {str(e)}", exc_info=True)
            return False

    async def mark_session_completed(
        self,
        session_id: str,
        processing_time: Optional[float] = None,
        generated_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """标记会话为已完成 - 优化版本"""
        return await self.update_session_status(
            session_id=session_id,
            status=SessionStatus.COMPLETED,
            progress=100.0,
            processing_time=processing_time,
            generated_count=generated_count,
            metadata=metadata
        )

    async def mark_session_failed(
        self,
        session_id: str,
        error_message: str,
        processing_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """标记会话为失败 - 优化版本"""
        return await self.update_session_status(
            session_id=session_id,
            status=SessionStatus.FAILED,
            error_message=error_message,
            processing_time=processing_time,
            metadata=metadata
        )

    async def mark_session_processing(
        self,
        session_id: str,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """标记会话为处理中 - 优化版本"""
        return await self.update_session_status(
            session_id=session_id,
            status=SessionStatus.PROCESSING,
            progress=progress,
            metadata=metadata
        )

    async def batch_update_sessions(
        self,
        session_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量更新会话状态"""
        try:
            if not self.runtime:
                self.logger.warning("运行时未初始化，无法进行批量更新")
                return {"success": False, "error": "运行时未初始化"}

            # 转换为请求对象
            update_requests = []
            for update_data in session_updates:
                request = SessionStatusUpdateRequest(
                    session_id=update_data["session_id"],
                    new_status=SessionStatus(update_data["status"]),
                    progress=update_data.get("progress"),
                    error_message=update_data.get("error_message"),
                    processing_time=update_data.get("processing_time"),
                    generated_count=update_data.get("generated_count"),
                    metadata=update_data.get("metadata")
                )
                update_requests.append(request)

            # 发送批量更新请求
            # 注意：这里需要智能体支持批量处理，或者逐个发送
            results = []
            for request in update_requests:
                success = await self.update_session_status(
                    session_id=request.session_id,
                    status=request.new_status,
                    progress=request.progress,
                    error_message=request.error_message,
                    processing_time=request.processing_time,
                    generated_count=request.generated_count,
                    metadata=request.metadata
                )
                results.append({"session_id": request.session_id, "success": success})

            successful_count = sum(1 for r in results if r["success"])

            return {
                "success": True,
                "total_count": len(session_updates),
                "successful_count": successful_count,
                "failed_count": len(session_updates) - successful_count,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"批量更新会话状态失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "total_count": len(session_updates),
                "successful_count": 0,
                "failed_count": len(session_updates)
            }
