"""
测试用例智能体编排服务 - 统一版本
协调测试用例相关智能体的执行流程，集成智能体管理器功能
提供完整的业务流程编排、性能监控和配置管理
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from autogen_core import SingleThreadedAgentRuntime, TopicId, TypeSubscription

# 导入智能体工厂和管理器
from app.agents.factory import agent_factory
from app.core.types import TopicTypes, AgentTypes
from app.core.agents.collector import StreamResponseCollector
from app.agents.database.session_status_agent import SessionStatusAgent, SessionStatusManager
# 导入消息类型
from app.core.messages.test_case import (
    DocumentParseRequest, ImageAnalysisRequest, ApiSpecParseRequest,
    DatabaseSchemaParseRequest, VideoAnalysisRequest,
    MindMapGenerationRequest, ExcelExportRequest, BatchProcessRequest,
    DirectRequirementRequest, RequirementAnalysisRequest
)


class TestCaseAgentOrchestrator:
    """
    测试用例智能体编排器 - 统一版本

    集成了智能体管理器的功能，提供：
    1. 智能体生命周期管理
    2. 性能监控和健康检查
    3. 配置管理
    4. 工作流编排
    5. 错误恢复和重试

    负责协调各种测试用例相关智能体的工作流程：
    - 文档解析智能体
    - 图片分析智能体
    - API规范解析智能体
    - 数据库Schema解析智能体
    - 录屏分析智能体
    - 测试用例生成智能体
    - 思维导图生成智能体
    - Excel导出智能体
    """

    def __init__(self, collector: Optional[StreamResponseCollector] = None):
        """
        初始化测试用例智能体编排器

        Args:
            collector: 可选的StreamResponseCollector用于捕获智能体响应
        """
        self.response_collector = collector
        self.runtime: Optional[SingleThreadedAgentRuntime] = None
        self.agent_factory = agent_factory
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # 编排器性能指标
        self.orchestrator_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "active_sessions": 0
        }
        logger.info("测试用例智能体编排器初始化完成")

    async def initialize(self, **agent_kwargs) -> None:
        """
        初始化编排器和智能体管理器

        Args:
            **agent_kwargs: 智能体初始化参数
        """
        try:
            logger.info("🚀 初始化测试用例智能体编排器...")

            if self.runtime is None:
                # 创建运行时
                self.runtime = SingleThreadedAgentRuntime()
                await self._register_test_case_agents()
                # 设置响应收集器
                if self.response_collector:
                    await self.agent_factory.register_stream_collector(
                        runtime=self.runtime,
                        collector=self.response_collector
                    )

                # 启动运行时
                self.runtime.start()

                logger.info("✅ 测试用例智能体编排器初始化完成")

        except Exception as e:
            logger.error(f"❌ 测试用例智能体编排器初始化失败: {str(e)}")
            raise

    async def _initialize_runtime(self, session_id: str) -> None:
        """
        初始化智能体运行时环境（兼容性方法）

        Args:
            session_id: 会话标识符
        """
        try:
            # 如果还没有初始化，则进行初始化
            if self.runtime is None:
                await self.initialize()

            # 记录会话
            self.active_sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }

            logger.info(f"会话已记录: {session_id}")

        except Exception as e:
            logger.error(f"初始化智能体运行时失败: {session_id}, 错误: {str(e)}")
            raise
    async def _cleanup_runtime(self, session_id: Optional[str] = None) -> None:
        """
        清理运行时资源

        清理流程:
        1. 向会话状态更新智能体发送已完成的消息（如果提供了session_id）
        2. 停止运行时当空闲时 (等待所有智能体完成当前任务)
        3. 关闭运行时并释放资源
        4. 清除智能体工厂注册记录
        5. 重置响应收集器为None
        6. 设置运行时为None

        这确保智能体工作流完成后的适当资源清理。

        Args:
            session_id: 可选的会话ID，如果提供则会标记该会话为已完成
        """
        try:
            if self.runtime:
                await self.runtime.stop_when_idle()
                await self.runtime.close()
                self.runtime = None

            # 如果提供了会话ID，向会话状态更新智能体发送已完成的消息
            if session_id:
                logger.info(f"标记会话为已完成: {session_id}")
                # 初始化会话状态管理器
                session_status_manager = SessionStatusManager()

                await session_status_manager.mark_session_completed(
                    session_id=session_id,
                    processing_time=None,  # 可以在这里计算实际处理时间
                    generated_count=None  # 可以在这里获取生成的测试用例数量
                )

            logger.debug("运行时清理成功完成")

        except Exception as e:
            logger.error(f"运行时清理失败: {str(e)}")
    async def _register_test_case_agents(self) -> None:
        """注册所有测试用例相关智能体"""
        try:
            # 注册文档解析智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.DOCUMENT_PARSER.value,
                TopicTypes.DOCUMENT_PARSER.value,
            )

            # 注册图片分析智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.IMAGE_ANALYZER.value,
                TopicTypes.IMAGE_ANALYZER.value,
            )

            # 注册API规范解析智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.API_SPEC_PARSER.value,
                TopicTypes.API_SPEC_PARSER.value,
            )

            # 注册数据库Schema解析智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.DATABASE_SCHEMA_PARSER.value,
                TopicTypes.DATABASE_SCHEMA_PARSER.value,
            )

            # 注册录屏分析智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.VIDEO_ANALYZER.value,
                TopicTypes.VIDEO_ANALYZER.value,
            )

            # 注册需求解析智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.REQUIREMENT_ANALYZER.value,
                TopicTypes.REQUIREMENT_ANALYZER.value,
            )

            # 注册测试点提取智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.TEST_POINT_EXTRACTOR.value,
                TopicTypes.TEST_POINT_EXTRACTOR.value,
            )

            # 注册测试用例生成智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.TEST_CASE_GENERATOR.value,
                TopicTypes.TEST_CASE_GENERATOR.value,
            )

            # 注册RAG知识库检索智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.RAG_RETRIEVAL.value,
                TopicTypes.RAG_RETRIEVAL.value,
            )

            # 注册思维导图生成智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.MIND_MAP_GENERATOR.value,
                TopicTypes.MIND_MAP_GENERATOR.value,
            )

            # 注册Excel导出智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.EXCEL_EXPORTER.value,
                TopicTypes.EXCEL_EXPORTER.value,
            )

            # 注册数据保存智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.TEST_CASE_SAVER.value,
                TopicTypes.TEST_CASE_SAVER.value,
            )

            # 注册需求保存智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.REQUIREMENT_SAVER.value,
                TopicTypes.REQUIREMENT_SAVER.value,
            )

            # 注册会话状态智能体
            await self.agent_factory.register_agent_to_runtime(
                self.runtime,
                AgentTypes.SESSION_STATUS.value,
                TopicTypes.SESSION_STATUS.value,
            )

            logger.info("所有测试用例智能体注册完成")

        except Exception as e:
            logger.error(f"注册智能体失败: {str(e)}")
            raise

    # ==================== 工作流管理方法 ====================

    async def _start_workflow(self, workflow_type: str, session_id: str) -> str:
        """开始工作流"""
        workflow_id = f"{workflow_type}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.active_sessions[workflow_id] = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "session_id": session_id,
            "status": "running",
            "started_at": datetime.now(),
            "completed_at": None,
            "success": None,
            "error": None
        }

        self.orchestrator_metrics["total_workflows"] += 1
        return workflow_id

    async def _complete_workflow(self, workflow_id: str, success: bool, error: str = None):
        """完成工作流"""
        if workflow_id in self.active_sessions:
            self.active_sessions[workflow_id].update({
                "status": "completed" if success else "failed",
                "completed_at": datetime.now(),
                "success": success,
                "error": error
            })

            if success:
                self.orchestrator_metrics["successful_workflows"] += 1
            else:
                self.orchestrator_metrics["failed_workflows"] += 1

    # ==================== 工作流方法 ====================

    async def parse_document(self, request: DocumentParseRequest) -> str:
        """
        解析文档并生成测试用例

        智能体消息流:
        1. 发送 DocumentParseRequest → DOCUMENT_PARSER 智能体
        2. DocumentParserAgent 解析文档内容
        3. DocumentParserAgent 发送 TestCaseGenerationRequest → TEST_CASE_GENERATOR 智能体
        4. TestCaseGeneratorAgent 生成并保存测试用例
        5. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        6. MindMapGeneratorAgent 生成思维导图

        Args:
            request: 文档解析请求

        Returns:
            str: 工作流ID
        """
        workflow_id = await self._start_workflow("document_parse", request.session_id)

        try:
            logger.info(f"开始文档解析工作流: {request.session_id}")

            # 初始化运行时
            await self._initialize_runtime(request.session_id)

            # 发送到文档解析智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.DOCUMENT_PARSER.value, source="orchestrator")
            )

            await self._complete_workflow(workflow_id, True)
            logger.info(f"文档解析工作流启动完成: {request.session_id}")
            return workflow_id

        except Exception as e:
            await self._complete_workflow(workflow_id, False, str(e))
            logger.error(f"文档解析工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def analyze_image(self, request: ImageAnalysisRequest) -> None:
        """
        分析图片并生成测试用例
        
        智能体消息流:
        1. 发送 ImageAnalysisRequest → IMAGE_ANALYZER 智能体
        2. ImageAnalyzerAgent 分析图片内容
        3. ImageAnalyzerAgent 发送 TestCaseGenerationRequest → TEST_CASE_GENERATOR 智能体
        4. TestCaseGeneratorAgent 生成并保存测试用例
        5. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        6. MindMapGeneratorAgent 生成思维导图
        
        Args:
            request: 图片分析请求
        """
        try:
            logger.info(f"开始图片分析工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 发送到图片分析智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.IMAGE_ANALYZER.value, source="user")
            )
            
            logger.info(f"图片分析工作流启动完成: {request.session_id}")
            
        except Exception as e:
            logger.error(f"图片分析工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def parse_api_spec(self, request: ApiSpecParseRequest) -> None:
        """
        解析API规范并生成测试用例
        
        智能体消息流:
        1. 发送 ApiSpecParseRequest → API_SPEC_PARSER 智能体
        2. ApiSpecParserAgent 解析API规范
        3. ApiSpecParserAgent 发送 TestCaseGenerationRequest → TEST_CASE_GENERATOR 智能体
        4. TestCaseGeneratorAgent 生成并保存测试用例
        5. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        6. MindMapGeneratorAgent 生成思维导图
        
        Args:
            request: API规范解析请求
        """
        try:
            logger.info(f"开始API规范解析工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 发送到API规范解析智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.API_SPEC_PARSER.value, source="user")
            )
            
            logger.info(f"API规范解析工作流启动完成: {request.session_id}")
            
        except Exception as e:
            logger.error(f"API规范解析工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def parse_database_schema(self, request: DatabaseSchemaParseRequest) -> None:
        """
        解析数据库Schema并生成测试用例
        
        智能体消息流:
        1. 发送 DatabaseSchemaParseRequest → DATABASE_SCHEMA_PARSER 智能体
        2. DatabaseSchemaParserAgent 解析数据库Schema
        3. DatabaseSchemaParserAgent 发送 TestCaseGenerationRequest → TEST_CASE_GENERATOR 智能体
        4. TestCaseGeneratorAgent 生成并保存测试用例
        5. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        6. MindMapGeneratorAgent 生成思维导图
        
        Args:
            request: 数据库Schema解析请求
        """
        try:
            logger.info(f"开始数据库Schema解析工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 发送到数据库Schema解析智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.DATABASE_SCHEMA_PARSER.value, source="user")
            )
            
            logger.info(f"数据库Schema解析工作流启动完成: {request.session_id}")
            
        except Exception as e:
            logger.error(f"数据库Schema解析工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def analyze_video(self, request: VideoAnalysisRequest) -> None:
        """
        分析录屏视频并生成测试用例
        
        智能体消息流:
        1. 发送 VideoAnalysisRequest → VIDEO_ANALYZER 智能体
        2. VideoAnalyzerAgent 分析录屏视频
        3. VideoAnalyzerAgent 发送 TestCaseGenerationRequest → TEST_CASE_GENERATOR 智能体
        4. TestCaseGeneratorAgent 生成并保存测试用例
        5. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        6. MindMapGeneratorAgent 生成思维导图
        
        Args:
            request: 录屏分析请求
        """
        try:
            logger.info(f"开始录屏分析工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 发送到录屏分析智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.VIDEO_ANALYZER.value, source="user")
            )
            
            logger.info(f"录屏分析工作流启动完成: {request.session_id}")

        except Exception as e:
            logger.error(f"录屏分析工作流失败: {request.session_id}, 错误: {str(e)}")
            raise

    async def analyze_requirement(self, request: RequirementAnalysisRequest) -> None:
        """
        分析需求内容并生成测试用例

        智能体消息流:
        1. 发送 RequirementAnalysisRequest → REQUIREMENT_ANALYZER 智能体
        2. RequirementAnalysisAgent 进行企业级需求解析
        3. RequirementAnalysisAgent 发送 TestCaseGenerationRequest → TEST_CASE_GENERATOR 智能体
        4. TestCaseGeneratorAgent 生成并保存测试用例
        5. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        6. MindMapGeneratorAgent 生成思维导图

        Args:
            request: 需求解析请求
        """
        try:
            logger.info(f"开始需求解析工作流: {request.session_id}")

            # 初始化运行时
            await self._initialize_runtime(request.session_id)

            # 发送到需求解析智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.REQUIREMENT_ANALYZER.value, source="user")
            )

            logger.info(f"需求解析工作流启动完成: {request.session_id}")

        except Exception as e:
            logger.error(f"需求解析工作流启动失败: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def process_direct_requirement(self, request) -> None:
        """
        处理直接需求输入

        智能体消息流:
        1. 直接创建 TestCaseGenerationRequest
        2. 发送到 TEST_CASE_GENERATOR 智能体
        3. TestCaseGeneratorAgent 生成并保存测试用例
        4. TestCaseGeneratorAgent 发送 MindMapGenerationRequest → MIND_MAP_GENERATOR 智能体
        5. MindMapGeneratorAgent 生成思维导图

        Args:
            request: 直接需求请求
        """
        try:
            logger.info(f"开始直接需求处理工作流: {request.session_id}")

            # 初始化运行时
            await self._initialize_runtime(request.session_id)

            # 发送到需求分析智能体，使用新的测试点提取流程
            requirement_analysis_request = RequirementAnalysisRequest(
                session_id=request.session_id,
                requirement_content=request.requirement_text,
                source_type="direct_requirement",
                source_data={
                    "requirement_text": request.requirement_text,
                    "requirement_title": getattr(request, 'requirement_title', None),
                    "analysis_target": getattr(request, 'analysis_target', '生成测试用例'),
                    "input_method": "direct"
                },
                analysis_config={
                    "enable_detailed_analysis": True,
                    "extract_business_rules": True,
                    "identify_stakeholders": True,
                    "analyze_dependencies": True
                }
            )

            # 发送到需求分析智能体
            await self.runtime.publish_message(
                requirement_analysis_request,
                topic_id=TopicId(type=TopicTypes.REQUIREMENT_ANALYZER.value, source="user")
            )

            logger.info(f"直接需求处理工作流启动完成: {request.session_id}")

        except Exception as e:
            logger.error(f"直接需求处理工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def generate_mind_map(self, request: MindMapGenerationRequest) -> None:
        """
        生成测试用例思维导图
        
        Args:
            request: 思维导图生成请求
        """
        try:
            logger.info(f"开始思维导图生成工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 发送到思维导图生成智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.MIND_MAP_GENERATOR.value, source="user")
            )
            
            logger.info(f"思维导图生成工作流启动完成: {request.session_id}")
            
        except Exception as e:
            logger.error(f"思维导图生成工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def export_to_excel(self, request: ExcelExportRequest) -> None:
        """
        导出测试用例到Excel
        
        Args:
            request: Excel导出请求
        """
        try:
            logger.info(f"开始Excel导出工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 发送到Excel导出智能体
            await self.runtime.publish_message(
                request,
                topic_id=TopicId(type=TopicTypes.EXCEL_EXPORTER.value, source="user")
            )
            
            logger.info(f"Excel导出工作流启动完成: {request.session_id}")
            
        except Exception as e:
            logger.error(f"Excel导出工作流失败: {request.session_id}, 错误: {str(e)}")
            raise
        finally:
            await self._cleanup_runtime(request.session_id)

    async def batch_process(self, request: BatchProcessRequest) -> None:
        """
        批量处理多个文件
        
        Args:
            request: 批量处理请求
        """
        try:
            logger.info(f"开始批量处理工作流: {request.session_id}")
            
            # 初始化运行时
            await self._initialize_runtime(request.session_id)
            
            # 根据处理类型分发到不同的智能体
            for input_file in request.input_files:
                file_type = input_file.get("type")
                
                if file_type == "document":
                    # 创建文档解析请求
                    doc_request = DocumentParseRequest(
                        session_id=f"{request.session_id}_{input_file['id']}",
                        file_name=input_file["name"],
                        file_path=input_file["path"],
                        document_type=input_file.get("document_type"),
                        analysis_target=request.process_config.get("analysis_target")
                    )
                    await self.parse_document(doc_request)
                    
                elif file_type == "image":
                    # 创建图片分析请求
                    img_request = ImageAnalysisRequest(
                        session_id=f"{request.session_id}_{input_file['id']}",
                        image_name=input_file["name"],
                        image_path=input_file["path"],
                        image_type=input_file.get("image_type"),
                        analysis_target=request.process_config.get("analysis_target")
                    )
                    await self.analyze_image(img_request)
                    
                elif file_type == "api_spec":
                    # 创建API规范解析请求
                    api_request = ApiSpecParseRequest(
                        session_id=f"{request.session_id}_{input_file['id']}",
                        file_name=input_file["name"],
                        file_path=input_file["path"],
                        spec_type=input_file.get("spec_type"),
                        analysis_target=request.process_config.get("analysis_target")
                    )
                    await self.parse_api_spec(api_request)
            
            logger.info(f"批量处理工作流启动完成: {request.session_id}")
            
        except Exception as e:
            logger.error(f"批量处理工作流失败: {request.session_id}, 错误: {str(e)}")
            raise

    def get_agent_factory_info(self) -> Dict[str, Any]:
        """
        获取智能体工厂信息
        
        Returns:
            智能体工厂的详细信息
        """
        return self.agent_factory.get_factory_info()

    def get_available_agents(self) -> List[str]:
        """
        获取可用的智能体列表
        
        Returns:
            可用智能体类型列表
        """
        return self.agent_factory.get_available_agents()

    async def cleanup_session(self, session_id: str) -> None:
        """
        清理会话资源

        Args:
            session_id: 会话标识符
        """
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"会话资源清理完成: {session_id}")
        except Exception as e:
            logger.error(f"清理会话资源失败: {session_id}, 错误: {str(e)}")

    # ==================== 系统管理方法 ====================

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy",
                "orchestrator_metrics": self.orchestrator_metrics.copy(),
                "active_sessions": list(self.active_sessions.keys())
            }

            # 更新活跃会话数
            status["orchestrator_metrics"]["active_sessions"] = len(self.active_sessions)

            if self.use_agent_manager and self.agent_manager:
                # 获取智能体性能指标
                agent_metrics = await self.agent_manager.get_performance_metrics()
                health_status = await self.agent_manager.health_check()

                status.update({
                    "agent_metrics": agent_metrics,
                    "health_status": health_status,
                    "system_status": "healthy" if health_status["overall_status"] == "healthy" else "degraded"
                })
            else:
                # 传统模式的状态信息
                status.update({
                    "agent_metrics": {"mode": "traditional", "factory_info": self.get_agent_factory_info()},
                    "health_status": {"overall_status": "healthy", "mode": "traditional"}
                })

            return status

        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "error",
                "error": str(e)
            }

    async def update_agent_config(self, agent_type: str, config_updates: Dict[str, Any]):
        """更新智能体配置"""
        if not self.use_agent_manager or not self.agent_manager:
            raise RuntimeError("智能体管理器模式未启用或未初始化")

        await self.agent_manager.update_agent_config(agent_type, config_updates)
        logger.info(f"已更新智能体配置: {agent_type}")

    async def get_agent_list(self) -> List[Dict[str, Any]]:
        """获取智能体列表"""
        if self.use_agent_manager and self.agent_manager:
            return self.agent_manager.get_agent_list()
        else:
            # 传统模式返回可用智能体列表
            available_agents = self.get_available_agents()
            return [
                {
                    "agent_type": agent_type,
                    "status": "active",
                    "mode": "traditional"
                }
                for agent_type in available_agents
            ]

    async def process_direct_requirement(self, request: DirectRequirementRequest) -> str:
        """直接需求处理工作流"""
        workflow_id = await self._start_workflow("direct_requirement", request.session_id)

        try:
            logger.info(f"开始直接需求处理工作流: {request.session_id}")

            # 初始化运行时
            await self._initialize_runtime(request.session_id)

            # 发送到需求分析智能体，使用新的测试点提取流程
            requirement_analysis_request = RequirementAnalysisRequest(
                session_id=request.session_id,
                requirement_content=request.requirement_text,
                source_type="direct_requirement",
                source_data={
                    "requirement_text": request.requirement_text,
                    "requirement_title": getattr(request, 'requirement_title', None),
                    "analysis_target": getattr(request, 'analysis_target', '生成测试用例'),
                    "input_method": "direct_workflow"
                },
                analysis_config={
                    "enable_detailed_analysis": True,
                    "extract_business_rules": True,
                    "identify_stakeholders": True,
                    "analyze_dependencies": True,
                    "auto_save": True,
                    "generate_mind_map": True
                }
            )

            await self.runtime.publish_message(
                requirement_analysis_request,
                topic_id=TopicId(type=TopicTypes.REQUIREMENT_ANALYZER.value, source="orchestrator")
            )

            await self._complete_workflow(workflow_id, True)
            logger.info(f"直接需求处理工作流启动完成: {request.session_id}")
            return workflow_id

        except Exception as e:
            await self._complete_workflow(workflow_id, False, str(e))
            logger.error(f"直接需求处理工作流失败: {request.session_id}, 错误: {str(e)}")
            raise

    def get_agent_factory_info(self) -> Dict[str, Any]:
        """获取智能体工厂信息（传统模式）"""
        available_types = self.agent_factory.get_available_agent_types()
        return {
            "available_agent_types": available_types,
            "registered_agents": len(self.agent_factory._registered_agents),
            "agent_classes": len(self.agent_factory._agent_classes),
            "total_available": len(available_types),
            "agent_categories": {
                "core": len([t for t in available_types if t in ["test_case_generator", "mind_map_generator", "test_case_saver"]]),
                "parser": len([t for t in available_types if t in ["document_parser", "image_analyzer", "api_spec_parser", "database_schema_parser", "video_analyzer"]]),
                "exporter": len([t for t in available_types if t == "excel_exporter"]),
                "web": len([t for t in available_types if any(prefix in t for prefix in ["page_", "yaml_", "playwright_"])])
            }
        }

    def get_available_agents(self) -> List[str]:
        """获取可用的智能体类型列表"""
        return self.agent_factory.get_available_agent_types()

    async def stop(self) -> None:
        """停止编排器"""
        try:
            logger.info("🛑 停止测试用例智能体编排器...")

            if self.use_agent_manager and self.agent_manager:
                await self.agent_manager.shutdown()

            if self.runtime:
                await self.runtime.stop()
                self.runtime = None

            self.active_sessions.clear()
            logger.info("✅ 测试用例智能体编排器已停止")

        except Exception as e:
            logger.error(f"❌ 停止编排器失败: {str(e)}")


# ==================== 全局实例管理 ====================

def get_test_case_orchestrator(collector: Optional[StreamResponseCollector] = None) -> TestCaseAgentOrchestrator:
    """
    获取测试用例智能体编排器实例
    
    工厂函数，创建新的TestCaseAgentOrchestrator实例。
    每次调用都创建新实例，确保每个工作流的状态干净。
    
    Args:
        collector: 可选的StreamResponseCollector用于捕获智能体响应
    
    Returns:
        TestCaseAgentOrchestrator: 准备好进行智能体工作流的新编排器实例
    
    注意: 此函数不会触发任何智能体消息流。
    """
    return TestCaseAgentOrchestrator(collector)
