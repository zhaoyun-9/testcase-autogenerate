"""
智能体工厂
统一创建和管理所有智能体实例，提供 AssistantAgent 和自定义智能体的创建接口
参考 examples/agents/factory.py 的优秀设计模式进行优化
"""
from typing import Dict, Any, Optional, Type, Callable, List, Union
from abc import ABC, abstractmethod

from autogen_core import SingleThreadedAgentRuntime, TypeSubscription, ClosureAgent
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from loguru import logger

from app.core.config import settings
from app.core.types import AgentTypes, AGENT_NAMES, TopicTypes, AgentPlatform
from app.core.agents.base import BaseAgent


class AgentFactory:
    """智能体工厂类，统一管理智能体的创建和注册"""

    def __init__(self):
        """初始化智能体工厂"""
        self._registered_agents: Dict[str, Dict[str, Any]] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._assistant_agent_configs: Dict[str, Dict[str, Any]] = {}
        self._agents: Dict[str, Dict[str, Any]] = {}  # 添加缺失的_agents属性

        # 注册所有可用的智能体类
        self._register_agent_classes()

        logger.info("智能体工厂初始化完成")
    
    def _register_agent_classes(self) -> None:
        """注册所有智能体类"""
        try:
            # 测试用例平台智能体
            from app.agents.test_case.document_parser_agent import DocumentParserAgent
            from app.agents.test_case.image_analyzer_agent import ImageAnalyzerAgent
            from app.agents.test_case.api_spec_parser_agent import ApiSpecParserAgent
            from app.agents.test_case.database_schema_parser_agent import DatabaseSchemaParserAgent
            from app.agents.test_case.video_analyzer_agent import VideoAnalyzerAgent
            from app.agents.test_case.requirement_analysis_agent import RequirementAnalysisAgent
            from app.agents.test_case.test_point_extraction_agent import TestPointExtractionAgent
            from app.agents.test_case.test_case_generator_agent import TestCaseGeneratorAgent
            from app.agents.test_case.rag_retrieval_agent import RagRetrievalAgent
            from app.agents.test_case.mind_map_generator_agent import MindMapGeneratorAgent
            from app.agents.test_case.excel_exporter_agent import ExcelExporterAgent
            from app.agents.database.test_case_saver_agent import TestCaseSaverAgent
            from app.agents.database.requirement_saver_agent import RequirementSaverAgent
            from app.agents.database.session_status_agent import SessionStatusAgent
            # 注册测试用例平台智能体类
            self._agent_classes.update({
                AgentTypes.DOCUMENT_PARSER.value: DocumentParserAgent,
                AgentTypes.IMAGE_ANALYZER.value: ImageAnalyzerAgent,
                AgentTypes.API_SPEC_PARSER.value: ApiSpecParserAgent,
                AgentTypes.DATABASE_SCHEMA_PARSER.value: DatabaseSchemaParserAgent,
                AgentTypes.VIDEO_ANALYZER.value: VideoAnalyzerAgent,
                AgentTypes.REQUIREMENT_ANALYZER.value: RequirementAnalysisAgent,
                AgentTypes.TEST_POINT_EXTRACTOR.value: TestPointExtractionAgent,
                AgentTypes.TEST_CASE_GENERATOR.value: TestCaseGeneratorAgent,
                AgentTypes.RAG_RETRIEVAL.value: RagRetrievalAgent,
                AgentTypes.MIND_MAP_GENERATOR.value: MindMapGeneratorAgent,
                AgentTypes.EXCEL_EXPORTER.value: ExcelExporterAgent,
                AgentTypes.TEST_CASE_SAVER.value: TestCaseSaverAgent,
                AgentTypes.REQUIREMENT_SAVER.value: RequirementSaverAgent,
                AgentTypes.SESSION_STATUS.value: SessionStatusAgent
            })

            # 调试信息
            logger.info(f"已注册 {len(self._agent_classes)} 个智能体类")
            logger.debug(f"注册的智能体类型: {list(self._agent_classes.keys())}")

        except ImportError as e:
            logger.error(f"智能体类导入失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"注册智能体类时发生错误: {str(e)}")
            raise
    
    def create_assistant_agent(self,
                               name: str,
                               system_message: str,
                               model_client_type: str = "deepseek",
                               model_client_stream: bool = True,
                               **kwargs) -> AssistantAgent:
        """创建 AssistantAgent 实例

        Args:
            name: 智能体名称
            system_message: 系统提示词
            model_client_type: 模型客户端类型 ("deepseek", "qwenvl", 或 "uitars")
            model_client_stream: 是否使用流式响应
            **kwargs: 其他参数

        Returns:
            AssistantAgent: 创建的智能体实例
        """
        try:
            # 选择模型客户端
            if model_client_type == "uitars":
                try:
                    from app.core.llms import get_uitars_model_client
                    model_client = get_uitars_model_client()
                except ImportError:
                    logger.warning("UI-TARS模型客户端不可用，回退到DeepSeek")
                    from app.core.llms import get_deepseek_model_client
                    model_client = get_deepseek_model_client()
            elif model_client_type == "qwenvl":
                from app.core.llms import get_qwenvl_model_client
                model_client = get_qwenvl_model_client()
            else:
                from app.core.llms import get_deepseek_model_client
                model_client = get_deepseek_model_client()

            # 创建 AssistantAgent
            agent = AssistantAgent(
                name=name,
                model_client=model_client,
                system_message=system_message,
                model_client_stream=model_client_stream,
                **kwargs
            )

            logger.info(f"创建 AssistantAgent: {name} (模型: {model_client_type})")
            return agent

        except Exception as e:
            logger.error(f"创建 AssistantAgent 失败: {str(e)}")
            raise
    
    def create_agent(self,
                    agent_type: str,
                    **kwargs) -> BaseAgent:
        """创建自定义智能体实例

        Args:
            agent_type: 智能体类型 (AgentTypes 枚举值)
            **kwargs: 智能体初始化参数

        Returns:
            BaseAgent: 创建的智能体实例
        """
        try:
            if agent_type not in self._agent_classes:
                raise ValueError(f"未知的智能体类型: {agent_type}")

            agent_class = self._agent_classes[agent_type]

            # 根据智能体类型选择合适的模型客户端
            if not kwargs.get('model_client_instance'):
                if agent_type in [AgentTypes.IMAGE_ANALYZER.value]:
                    # 图片分析相关智能体使用UI-TARS或QwenVL
                    try:
                        from app.core.llms import get_uitars_model_client
                        kwargs['model_client_instance'] = get_uitars_model_client()
                    except ImportError:
                        from app.core.llms import get_qwenvl_model_client
                        kwargs['model_client_instance'] = get_qwenvl_model_client()
                elif agent_type in [AgentTypes.VIDEO_ANALYZER.value]:
                    # 视频分析使用QwenVL
                    from app.core.llms import get_qwenvl_model_client
                    kwargs['model_client_instance'] = get_qwenvl_model_client()
                else:
                    # 其他智能体默认使用DeepSeek
                    from app.core.llms import get_deepseek_model_client
                    kwargs['model_client_instance'] = get_deepseek_model_client()

            # 创建智能体实例
            agent = agent_class(**kwargs)

            logger.info(f"创建智能体: {AGENT_NAMES.get(agent_type, agent_type)}")
            return agent

        except Exception as e:
            logger.error(f"创建智能体失败 ({agent_type}): {str(e)}")
            raise

    def register_agent(self,
                      agent_type: str,
                      agent_class: Type[BaseAgent],
                      agent_name: Optional[str] = None,
                      topic_type: Optional[str] = None,
                      platform: AgentPlatform = AgentPlatform.TEST_CASE) -> None:
        """注册智能体类型

        Args:
            agent_type: 智能体类型标识符
            agent_class: 智能体类
            agent_name: 智能体显示名称
            topic_type: 对应的主题类型
            platform: 智能体平台
        """
        self._agent_classes[agent_type] = agent_class

        # 注册到全局映射中
        if agent_name:
            AGENT_NAMES[agent_type] = agent_name

        # 存储注册信息
        self._registered_agents[agent_type] = {
            "class": agent_class,
            "name": agent_name or agent_type,
            "topic_type": topic_type,
            "platform": platform.value
        }

        logger.info(f"注册智能体: {agent_name or agent_type} ({agent_type})")

    def create_user_proxy_agent(self,
                               name: str = "user_proxy",
                               input_func: Optional[Callable] = None,
                               **kwargs) -> UserProxyAgent:
        """创建用户代理智能体

        Args:
            name: 智能体名称
            input_func: 用户输入函数
            **kwargs: 其他参数

        Returns:
            UserProxyAgent: 用户代理智能体实例
        """
        try:
            from autogen_agentchat.agents import UserProxyAgent

            agent = UserProxyAgent(
                name=name,
                input_func=input_func,
                **kwargs
            )

            logger.info(f"创建用户代理智能体: {name}")
            return agent

        except Exception as e:
            logger.error(f"创建用户代理智能体失败: {str(e)}")
            raise

    def get_available_agents(self, platform: Optional[AgentPlatform] = None) -> Dict[str, Dict[str, Any]]:
        """获取可用的智能体列表

        Args:
            platform: 可选的平台过滤器

        Returns:
            Dict[str, Dict[str, Any]]: 智能体信息字典
        """
        if platform is None:
            return self._registered_agents.copy()

        return {
            agent_type: info
            for agent_type, info in self._registered_agents.items()
            if info.get("platform") == platform.value
        }

    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """获取特定智能体的信息

        Args:
            agent_type: 智能体类型

        Returns:
            Optional[Dict[str, Any]]: 智能体信息，如果不存在则返回None
        """
        return self._registered_agents.get(agent_type)

    def is_agent_available(self, agent_type: str) -> bool:
        """检查智能体是否可用

        Args:
            agent_type: 智能体类型

        Returns:
            bool: 智能体是否可用
        """
        return agent_type in self._agent_classes

    def get_available_agent_types(self, platform: Optional[AgentPlatform] = None) -> List[str]:
        """获取所有可用的智能体类型

        Args:
            platform: 可选的平台过滤器

        Returns:
            List[str]: 智能体类型列表
        """
        if platform is None:
            return list(self._agent_classes.keys())

        return [
            agent_type for agent_type, info in self._registered_agents.items()
            if info.get("platform") == platform.value
        ]

    def get_agent_name(self, agent_type: str) -> str:
        """获取智能体显示名称"""
        return AGENT_NAMES.get(agent_type, agent_type)

    def is_agent_type_valid(self, agent_type: str) -> bool:
        """检查智能体类型是否有效"""
        return agent_type in self._agent_classes

    def create_agents_for_platform(self,
                                  platform: AgentPlatform,
                                  **common_kwargs) -> Dict[str, BaseAgent]:
        """为特定平台创建所有智能体

        Args:
            platform: 目标平台
            **common_kwargs: 所有智能体的通用参数

        Returns:
            Dict[str, BaseAgent]: 智能体类型到实例的映射
        """
        agents = {}
        platform_agents = self.get_available_agents(platform)

        for agent_type in platform_agents:
            try:
                agent = self.create_agent(agent_type, **common_kwargs)
                agents[agent_type] = agent
                logger.info(f"为平台 {platform.value} 创建智能体: {agent_type}")
            except Exception as e:
                logger.error(f"为平台 {platform.value} 创建智能体 {agent_type} 失败: {str(e)}")

        return agents

    def get_factory_stats(self) -> Dict[str, Any]:
        """获取工厂统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        platform_counts = {}
        for info in self._registered_agents.values():
            platform = info.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        return {
            "total_registered_agents": len(self._registered_agents),
            "total_agent_classes": len(self._agent_classes),
            "platform_distribution": platform_counts,
            "available_platforms": list(set(info.get("platform") for info in self._registered_agents.values()))
        }

    async def register_agent_to_runtime(self,
                                      runtime: SingleThreadedAgentRuntime,
                                      agent_type: str,
                                      topic_type: str,
                                      **kwargs):
        """注册智能体到运行时
        
        Args:
            runtime: 智能体运行时
            agent_type: 智能体类型
            topic_type: 主题类型
            **kwargs: 智能体初始化参数
        """
        try:
            if agent_type not in self._agent_classes:
                raise ValueError(f"未知的智能体类型: {agent_type}")

            agent_class = self._agent_classes[agent_type]
            
            # 注册智能体
            await agent_class.register(
                runtime,
                topic_type,
                lambda: self.create_agent(agent_type, **kwargs)
            )
            
            # 记录注册信息
            self._agents[agent_type] = {
                "agent_type": agent_type,
                "topic_type": topic_type,
                "agent_name": AGENT_NAMES.get(agent_type, agent_type),
                "kwargs": kwargs
            }
            
            logger.info(f"智能体注册成功: {AGENT_NAMES.get(agent_type, agent_type)}")
            
        except Exception as e:
            logger.error(f"注册智能体失败: {agent_type}, 错误: {str(e)}")
            raise

    async def register_stream_collector(self,
                                      runtime: SingleThreadedAgentRuntime,
                                      collector) -> None:
        """注册流式响应收集器

        Args:
            runtime: 智能体运行时
            collector: 响应收集器实例
        """
        try:
            # 检查回调函数是否存在
            if collector.callback is None:
                logger.warning("流式响应收集器回调函数为空，跳过注册")
                return

            await ClosureAgent.register_closure(
                runtime,
                "stream_collector_agent",
                collector.callback,
                subscriptions=lambda: [
                    TypeSubscription(
                        topic_type=TopicTypes.STREAM_OUTPUT.value,
                        agent_type="stream_collector_agent"
                    )
                ],
            )

            logger.info("流式响应收集器注册成功")

        except Exception as e:
            logger.error(f"注册流式响应收集器失败: {str(e)}")
            raise

    async def initialize(self):
        """初始化智能体工厂"""
        try:
            logger.info("智能体工厂初始化中...")
            # 这里可以添加初始化逻辑
            logger.info("智能体工厂初始化完成")
        except Exception as e:
            logger.error(f"智能体工厂初始化失败: {str(e)}")
            raise
    
    async def cleanup(self):
        """清理智能体工厂资源"""
        try:
            logger.info("清理智能体工厂资源...")
            self._agents.clear()
            logger.info("智能体工厂资源清理完成")
        except Exception as e:
            logger.error(f"清理智能体工厂资源失败: {str(e)}")
    
    def get_factory_info(self) -> Dict[str, Any]:
        """获取工厂信息"""
        return {
            "supported_agents": list(self._agent_classes.keys()),
            "agent_names": AGENT_NAMES,
            "registered_agents": len(self._agents),
            "available_agent_classes": len(self._agent_classes)
        }
    



# 全局智能体工厂实例
agent_factory = AgentFactory()
