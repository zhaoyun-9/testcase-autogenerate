"""
智能体基类
定义所有智能体的通用接口和功能，基于AutoGen Core
参考 examples/base.py 的优秀设计模式进行优化
"""
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from datetime import datetime

from autogen_core import RoutedAgent, MessageContext, TopicId, ClosureContext
from loguru import logger

from app.core.messages import StreamMessage
from app.core.agents.collector import StreamResponseCollector
from app.core.types import AgentPlatform, MessageRegion, TopicTypes


class BaseAgent(RoutedAgent, ABC):
    """统一智能体基类，提供所有智能体的共享功能"""

    def __init__(self, agent_id: str, agent_name: str, platform: AgentPlatform = AgentPlatform.TEST_CASE,
                 model_client_instance=None, **kwargs):
        """初始化基础智能体

        Args:
            agent_id: 智能体ID
            agent_name: 智能体名称（用于显示）
            platform: 智能体平台类型
            model_client_instance: 模型客户端实例
            **kwargs: 其他初始化参数
        """
        super().__init__(agent_id)
        self.agent_name = agent_name
        self.platform = platform
        self.model_client = model_client_instance
        self.agent_metadata = kwargs
        self.performance_metrics = {}
        self.created_at = datetime.now()

        # 智能体状态
        self.is_active = True
        self.message_count = 0
        self.error_count = 0

        logger.info(f"初始化 {agent_name} 智能体 (ID: {agent_id})")

    async def _send_message(self, content: str, message_type: str = "message",
                          is_final: bool = False, result: Optional[Dict[str, Any]] = None,
                          region: Union[str, MessageRegion] = MessageRegion.PROCESS, source=None) -> None:
        """发送消息到流输出主题

        Args:
            content: 消息内容
            message_type: 消息类型
            is_final: 是否是最终消息
            result: 可选的结果数据
            region: 消息区域
            source: 消息来源
        """
        # 处理region参数
        if isinstance(region, MessageRegion):
            region_str = region.value
        else:
            region_str = region

        message = StreamMessage(
            type=message_type,
            source=source if source else self.agent_name,
            content=content,
            region=region_str,
            is_final=is_final,
            result=result,
            message_id=f"{self.id.key}-{uuid.uuid4()}",
            platform=self.platform.value
        )

        try:
            await self.publish_message(
                message,
                topic_id=TopicId(type=TopicTypes.STREAM_OUTPUT.value, source=self.id.key)
            )
        except Exception as e:
            logger.warning(f"无法发送消息，没有可用的发布机制: {str(e)}")

        self.message_count += 1
        logger.debug(f"[{self.agent_name}] 发送{message_type}: {content[:50]}...")

    async def send_stream_message(self, content: str, message_type: str = "message",
                                 is_final: bool = False, result: Optional[Dict[str, Any]] = None,
                                 region: Union[str, MessageRegion] = MessageRegion.PROCESS) -> None:
        """发送流式消息（简化版本，与examples保持一致）

        Args:
            content: 消息内容
            message_type: 消息类型
            is_final: 是否是最终消息
            result: 可选的结果数据
            region: 消息区域
        """
        await self._send_message(content, message_type, is_final, result, region)

    async def log_and_send(self, content: str, level: str = "info",
                          message_type: str = "message", region: MessageRegion = MessageRegion.PROCESS) -> None:
        """记录日志并发送消息

        Args:
            content: 消息内容
            level: 日志级别 (debug, info, warning, error)
            message_type: 消息类型
            region: 消息区域
        """
        # 记录日志
        log_func = getattr(logger, level, logger.info)
        log_func(f"[{self.agent_name}] {content}")

        # 发送消息
        await self._send_message(content, message_type, False, None, region)

    def create_context_variables(self, **kwargs) -> Dict[str, Any]:
        """创建上下文变量

        Args:
            **kwargs: 额外的上下文变量

        Returns:
            Dict[str, Any]: 上下文变量字典
        """
        return {
            "agent_id": self.id.key,
            "agent_name": self.agent_name,
            "platform": self.platform.value,
            "timestamp": time.time(),
            **kwargs
        }
    
    async def send_response(self, content: str, is_final: bool = False,
                          result: Optional[Dict[str, Any]] = None,
                          region: Union[str, MessageRegion] = MessageRegion.PROCESS, source: str = None) -> None:
        """发送响应消息（兼容性方法）"""
        await self._send_message(content, "message", is_final, result, region, source)

    async def send_progress(self, content: str, progress_percent: Optional[float] = None) -> None:
        """发送进度消息

        Args:
            content: 进度描述
            progress_percent: 进度百分比（0-100）
        """
        result = {"progress": progress_percent} if progress_percent is not None else None
        await self._send_message(content, "progress", False, result, MessageRegion.PROCESS)

    async def send_success(self, content: str, result: Optional[Dict[str, Any]] = None) -> None:
        """发送成功消息"""
        await self._send_message(f"✅ {content}", "success", False, result, MessageRegion.SUCCESS)

    async def send_warning(self, content: str) -> None:
        """发送警告消息"""
        logger.warning(f"[{self.agent_name}] 警告: {content}")
        await self._send_message(f"⚠️ {content}", "warning", False, None, MessageRegion.WARNING)

    async def send_error(self, error_message: str, is_final: bool = True) -> None:
        """发送错误消息

        Args:
            error_message: 错误消息内容
            is_final: 是否是最终消息
        """
        logger.error(f"[{self.agent_name}] 错误: {error_message}")
        await self._send_message(f"❌ {error_message}", "error", is_final, None, MessageRegion.ERROR)
        self.error_count += 1

    async def send_info(self, content: str) -> None:
        """发送信息消息"""
        await self._send_message(f"ℹ️ {content}", "info", False, None, MessageRegion.INFO)

    async def handle_exception(self, func_name: str, exception: Exception,
                             send_error_message: bool = True) -> None:
        """处理异常并可选发送错误消息

        Args:
            func_name: 发生异常的函数名
            exception: 异常对象
            send_error_message: 是否发送错误消息到流
        """
        error_msg = f"在{func_name}中发生错误: {str(exception)}"
        logger.error(f"[{self.agent_name}] {error_msg}")

        if send_error_message:
            await self.send_error(error_msg)

    def start_performance_monitoring(self, operation_name: str = "operation") -> str:
        """开始性能监控

        Args:
            operation_name: 操作名称

        Returns:
            str: 监控ID
        """
        monitor_id = f"{operation_name}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        self.performance_metrics[monitor_id] = {
            "operation": operation_name,
            "start_time": start_time,
            "agent": self.agent_name
        }

        logger.debug(f"[{self.agent_name}] 开始性能监控: {operation_name} (ID: {monitor_id})")
        return monitor_id

    def end_performance_monitoring(self, monitor_id: str,
                                 log_result: bool = True) -> Optional[Dict[str, Any]]:
        """结束性能监控

        Args:
            monitor_id: 监控ID
            log_result: 是否记录结果到日志

        Returns:
            Dict[str, Any]: 性能指标数据
        """
        if monitor_id not in self.performance_metrics:
            logger.warning(f"[{self.agent_name}] 未找到监控ID: {monitor_id}")
            return None

        metric = self.performance_metrics[monitor_id]
        end_time = time.time()
        duration = end_time - metric["start_time"]

        result = {
            **metric,
            "end_time": end_time,
            "duration": duration,
            "duration_formatted": f"{duration:.2f}秒"
        }

        if log_result:
            logger.info(f"[{self.agent_name}] {metric['operation']} 耗时: {duration:.2f}秒")

        # 清理已完成的监控
        del self.performance_metrics[monitor_id]

        return result

    async def cleanup(self):
        """清理智能体资源"""
        try:
            self.is_active = False
            # 清理性能监控数据
            self.performance_metrics.clear()
            logger.info(f"智能体资源清理完成: {self.agent_name}")
        except Exception as e:
            logger.error(f"清理智能体资源失败: {str(e)}")
