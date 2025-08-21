"""
RAG知识库检索智能体
专门负责从知识库中检索相关信息，为测试用例生成提供上下文支持
基于AutoGen Core架构实现，参考requirement_analysis_agent.py的优秀设计模式
集成examples/test_retrieval.py中的RAG检索逻辑
"""
import uuid
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import RagRetrievalRequest, RagRetrievalResponse


class RagRetrievalResult(BaseModel):
    """RAG检索结果"""
    retrieval_id: str = Field(..., description="检索ID")
    query: str = Field(..., description="检索查询")
    search_results: List[Dict[str, Any]] = Field(default_factory=list, description="检索结果")
    rag_completion: Optional[str] = Field(None, description="RAG生成的完整回答")
    context_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="上下文片段")
    relevance_scores: List[float] = Field(default_factory=list, description="相关性评分")
    total_results: int = Field(0, description="总结果数量")
    confidence_score: float = Field(0.0, description="置信度评分")
    knowledge_sources: List[str] = Field(default_factory=list, description="知识来源列表")


@type_subscription(topic_type=TopicTypes.RAG_RETRIEVAL.value)
class RagRetrievalAgent(BaseAgent):
    """RAG知识库检索智能体，专门负责知识库检索和上下文提供"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化RAG知识库检索智能体"""
        super().__init__(
            agent_id=AgentTypes.RAG_RETRIEVAL.value,
            agent_name=AGENT_NAMES.get(AgentTypes.RAG_RETRIEVAL.value, "RAG知识库检索智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )
        
        # RAG检索配置
        self.retrieval_config = {
            # 'base_url': "http://155.138.220.75:7272",
            'base_url': "http://123.57.32.249:7272",
            'superuser_email': "1058069461@qq.com",
            'superuser_password': "1058069461",
            'default_search_mode': "basic",
            'default_max_results': 1,
            'default_confidence_threshold': 0.7,
            'enable_semantic_search': True,
            'enable_fulltext_search': True,
            'enable_rag_generation': True
        }
        
        # 初始化R2R客户端
        self.r2r_client = None
        self._initialize_r2r_client()
        
        logger.info(f"RAG知识库检索智能体初始化完成: {self.agent_name}")

    def _initialize_r2r_client(self):
        """初始化R2R客户端"""
        try:
            from r2r import R2RClient
            self.r2r_client = R2RClient(self.retrieval_config['base_url'])
            # 登录
            self.r2r_client.users.login(
                self.retrieval_config['superuser_email'],
                self.retrieval_config['superuser_password']
            )
            logger.info("R2R客户端初始化成功")
        except ImportError:
            logger.warning("R2R模块未安装，RAG检索功能将使用模拟模式")
            self.r2r_client = None
        except Exception as e:
            logger.error(f"R2R客户端初始化失败: {str(e)}")
            self.r2r_client = None

    @message_handler
    async def handle_rag_retrieval_request(
        self,
        message: RagRetrievalRequest,
        ctx: MessageContext
    ) -> RagRetrievalResponse | None:
        """处理RAG知识库检索请求"""
        start_time = datetime.now()

        try:
            logger.info(f"开始处理RAG知识库检索请求: {message.session_id}")

            # 发送开始处理消息
            await self.send_response(
                f"🔍 开始RAG知识库检索: {message.query[:50]}...",
                region="process"
            )

            # 检查R2R客户端
            if not self.r2r_client:
                await self.send_response(
                    "⚠️ R2R客户端未初始化，尝试重新连接...",
                    region="warning"
                )
                self._initialize_r2r_client()
                
                if not self.r2r_client:
                    raise Exception("无法连接到R2R知识库服务")

            # 执行RAG检索
            await self.send_response("🔄 第1步: 执行知识库检索...", region="progress")
            retrieval_result = await self._perform_rag_retrieval(message)

            # 发送检索结果统计
            await self.send_response(
                f"📊 检索结果: 找到 {retrieval_result.total_results} 个相关文档片段, "
                f"置信度: {retrieval_result.confidence_score:.2f}",
                region="info",
                result={
                    "total_results": retrieval_result.total_results,
                    "confidence_score": retrieval_result.confidence_score,
                    "knowledge_sources_count": len(retrieval_result.knowledge_sources)
                }
            )

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 构建响应
            response = RagRetrievalResponse(
                session_id=message.session_id,
                retrieval_id=retrieval_result.retrieval_id,
                query=retrieval_result.query,
                search_results=retrieval_result.search_results,
                rag_completion=retrieval_result.rag_completion,
                context_chunks=retrieval_result.context_chunks,
                relevance_scores=retrieval_result.relevance_scores,
                total_results=retrieval_result.total_results,
                processing_time=processing_time,
                confidence_score=retrieval_result.confidence_score,
                knowledge_sources=retrieval_result.knowledge_sources,
                created_at=datetime.now().isoformat()
            )

            # 发送完成消息
            await self.send_response(
                f"✅ RAG知识库检索完成! 处理时间: {processing_time:.2f}秒",
                is_final=True,
                region="success",
                result={
                    "processing_time": processing_time,
                    "total_results": response.total_results,
                    "confidence_score": response.confidence_score,
                    "has_rag_completion": bool(response.rag_completion)
                }
            )

            return response

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"RAG知识库检索失败: {str(e)}")
            await self.send_response(
                f"❌ RAG知识库检索失败: {str(e)} (处理时间: {processing_time:.2f}秒)",
                is_final=True,
                region="error",
                result={"processing_time": processing_time, "error": str(e)}
            )
            return None

    async def _perform_rag_retrieval(
        self, 
        message: RagRetrievalRequest
    ) -> RagRetrievalResult:
        """执行RAG知识库检索"""
        try:
            retrieval_id = str(uuid.uuid4())
            
            # 构建检索查询
            enhanced_query = self._build_enhanced_query(message)
            
            # 准备检索设置
            search_settings = self._prepare_search_settings(message)
            
            # 执行基础检索
            search_results = await self._execute_search(enhanced_query, search_settings)
            
            # 执行RAG生成（如果启用）
            rag_completion = None
            if self.retrieval_config['enable_rag_generation']:
                rag_completion = await self._execute_rag_generation(
                    enhanced_query, message.rag_generation_config
                )
            
            # 处理和分析结果
            processed_results = self._process_search_results(search_results)
            
            return RagRetrievalResult(
                retrieval_id=retrieval_id,
                query=enhanced_query,
                search_results=processed_results['search_results'],
                rag_completion=rag_completion,
                context_chunks=processed_results['context_chunks'],
                relevance_scores=processed_results['relevance_scores'],
                total_results=processed_results['total_results'],
                confidence_score=processed_results['confidence_score'],
                knowledge_sources=processed_results['knowledge_sources']
            )
            
        except Exception as e:
            logger.error(f"RAG检索执行失败: {str(e)}")
            # 返回空结果而不是抛出异常
            return RagRetrievalResult(
                retrieval_id=str(uuid.uuid4()),
                query=message.query,
                search_results=[],
                rag_completion=None,
                context_chunks=[],
                relevance_scores=[],
                total_results=0,
                confidence_score=0.0,
                knowledge_sources=[]
            )

    def _build_enhanced_query(self, message: RagRetrievalRequest) -> str:
        """构建增强的检索查询"""
        query_parts = [message.query]
        
        # 添加需求上下文
        if message.requirements:
            query_parts.append(f"需求背景: {message.requirements[:200]}")
        
        # 添加测试点上下文
        if message.test_points:
            test_points_text = " ".join([
                tp.get('title', '') + ' ' + tp.get('description', '')
                for tp in message.test_points[:3]  # 限制前3个测试点
            ])
            query_parts.append(f"测试点: {test_points_text[:200]}")
        
        # 添加上下文类型
        if message.context_type:
            query_parts.append(f"上下文: {message.context_type}")
        
        enhanced_query = " ".join(query_parts)
        logger.debug(f"增强查询: {enhanced_query[:100]}...")
        
        return enhanced_query

    def _prepare_search_settings(self, message: RagRetrievalRequest) -> Dict[str, Any]:
        """准备检索设置"""
        settings = {
            "use_semantic_search": self.retrieval_config['enable_semantic_search'],
            "use_fulltext_search": self.retrieval_config['enable_fulltext_search'],
            "limit": min(message.max_results, self.retrieval_config['default_max_results'])
        }
        
        # 合并用户提供的设置
        if message.search_settings:
            settings.update(message.search_settings)
        
        # 添加过滤条件
        if message.filters:
            settings["filters"] = message.filters
        
        return settings

    async def _execute_search(self, query: str, settings: Dict[str, Any]) -> Any:
        """执行检索"""
        try:
            if self.r2r_client is None:
                # 返回模拟结果
                logger.info("使用模拟检索结果")
                return self._create_mock_search_results(query, settings)

            search_response = self.r2r_client.retrieval.search(
                query=query,
                search_mode=settings.get("search_mode", "basic"),
                search_settings=settings
            )
            return search_response.results
        except Exception as e:
            logger.error(f"检索执行失败: {str(e)}")
            return self._create_mock_search_results(query, settings)

    async def _execute_rag_generation(
        self,
        query: str,
        rag_config: Dict[str, Any]
    ) -> Optional[str]:
        """执行RAG生成"""
        try:
            if self.r2r_client is None:
                # 返回模拟RAG生成结果
                logger.info("使用模拟RAG生成结果")
                return self._create_mock_rag_completion(query)

            # 准备RAG配置
            generation_config = {
                "stream": False,
                "max_tokens": 500
            }
            generation_config.update(rag_config)

            rag_response = self.r2r_client.retrieval.rag(
                query=query,
                rag_generation_config=generation_config,
                search_settings={
                    "use_semantic_search": True,
                    "limit": 5
                }
            )

            return rag_response.results.completion if rag_response.results else None

        except Exception as e:
            logger.error(f"RAG生成失败: {str(e)}")
            return self._create_mock_rag_completion(query)

    def _process_search_results(self, search_results: Any) -> Dict[str, Any]:
        """处理检索结果"""
        if not search_results:
            return {
                'search_results': [],
                'context_chunks': [],
                'relevance_scores': [],
                'total_results': 0,
                'confidence_score': 0.0,
                'knowledge_sources': []
            }
        
        try:
            # 提取搜索结果
            chunk_results = getattr(search_results, 'chunk_search_results', [])
            
            processed_chunks = []
            relevance_scores = []
            knowledge_sources = set()
            
            for chunk in chunk_results:
                chunk_data = {
                    'id': getattr(chunk, 'id', str(uuid.uuid4())),
                    'text': getattr(chunk, 'text', ''),
                    'score': getattr(chunk, 'score', 0.0),
                    'metadata': getattr(chunk, 'metadata', {})
                }
                processed_chunks.append(chunk_data)
                relevance_scores.append(chunk_data['score'])
                
                # 提取知识来源
                if 'document_id' in chunk_data['metadata']:
                    knowledge_sources.add(chunk_data['metadata']['document_id'])
            
            # 计算平均置信度
            avg_confidence = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            return {
                'search_results': [{'chunks': processed_chunks}],
                'context_chunks': processed_chunks,
                'relevance_scores': relevance_scores,
                'total_results': len(processed_chunks),
                'confidence_score': avg_confidence,
                'knowledge_sources': list(knowledge_sources)
            }
            
        except Exception as e:
            logger.error(f"结果处理失败: {str(e)}")
            return {
                'search_results': [],
                'context_chunks': [],
                'relevance_scores': [],
                'total_results': 0,
                'confidence_score': 0.0,
                'knowledge_sources': []
            }

    async def _send_response_to_requester(
        self,
        response: RagRetrievalResponse,
        ctx: MessageContext
    ):
        """发送响应到原始请求者"""
        try:
            # 这里可以根据需要发送到特定的主题或智能体
            # 目前先记录日志
            logger.info(f"RAG检索响应已准备完成: {response.retrieval_id}")
            
        except Exception as e:
            logger.error(f"发送响应失败: {str(e)}")

    def _create_mock_search_results(self, query: str, settings: Dict[str, Any]) -> Any:
        """创建模拟检索结果"""
        class MockChunk:
            def __init__(self, text: str, score: float, chunk_id: str):
                self.text = text
                self.score = score
                self.id = chunk_id
                self.metadata = {
                    "document_id": f"doc_{chunk_id}",
                    "source": "mock_knowledge_base",
                    "category": "test_case_design"
                }

        class MockSearchResults:
            def __init__(self, chunks):
                self.chunk_search_results = chunks

        # 基于查询生成模拟结果
        mock_chunks = []
        limit = settings.get("limit", 5)

        if "测试用例" in query or "test case" in query.lower():
            mock_chunks.extend([
                MockChunk(
                    "测试用例设计应遵循等价类划分原则，将输入域划分为有效等价类和无效等价类。",
                    0.95,
                    "chunk_001"
                ),
                MockChunk(
                    "边界值分析是测试用例设计的重要方法，重点测试边界条件和临界值。",
                    0.88,
                    "chunk_002"
                ),
                MockChunk(
                    "功能测试用例应覆盖正常流程、异常流程和边界条件，确保功能完整性。",
                    0.82,
                    "chunk_003"
                )
            ])

        if "登录" in query or "login" in query.lower():
            mock_chunks.extend([
                MockChunk(
                    "用户登录测试应包括：有效用户名密码、无效用户名、无效密码、空值测试等场景。",
                    0.92,
                    "chunk_004"
                ),
                MockChunk(
                    "登录安全测试需要验证密码加密、会话管理、登录失败次数限制等安全机制。",
                    0.85,
                    "chunk_005"
                )
            ])

        if "API" in query or "api" in query.lower():
            mock_chunks.extend([
                MockChunk(
                    "API测试应覆盖请求参数验证、响应格式检查、状态码验证和错误处理。",
                    0.90,
                    "chunk_006"
                ),
                MockChunk(
                    "REST API测试需要验证HTTP方法、请求头、认证授权和数据格式。",
                    0.87,
                    "chunk_007"
                )
            ])

        # 如果没有特定匹配，返回通用测试知识
        if not mock_chunks:
            mock_chunks = [
                MockChunk(
                    "软件测试是保证软件质量的重要手段，需要系统性的测试策略和方法。",
                    0.75,
                    "chunk_general_001"
                ),
                MockChunk(
                    "测试用例应具备可执行性、可重复性和可维护性的特点。",
                    0.70,
                    "chunk_general_002"
                )
            ]

        # 限制结果数量
        mock_chunks = mock_chunks[:limit]

        return MockSearchResults(mock_chunks)

    def _create_mock_rag_completion(self, query: str) -> str:
        """创建模拟RAG生成结果"""
        if "测试用例" in query:
            return """基于查询内容，以下是测试用例设计的关键要点：

1. **等价类划分**：将输入域划分为有效和无效等价类，每个等价类选择代表性测试数据。

2. **边界值分析**：重点测试边界条件，包括最小值、最大值、最小值-1、最大值+1等。

3. **场景覆盖**：确保覆盖正常流程、异常流程、边界条件和错误处理场景。

4. **可执行性**：测试用例应具备明确的前置条件、执行步骤和预期结果。"""

        elif "登录" in query:
            return """用户登录功能的测试用例设计建议：

1. **正常登录**：使用有效的用户名和密码进行登录验证。

2. **异常登录**：测试无效用户名、错误密码、空值输入等异常情况。

3. **安全测试**：验证密码加密、会话管理、登录失败限制等安全机制。

4. **界面测试**：检查登录界面的用户体验和错误提示信息。"""

        elif "API" in query:
            return """API测试用例设计的核心要素：

1. **参数验证**：测试必填参数、可选参数、参数类型和格式验证。

2. **响应检查**：验证响应状态码、数据格式、字段完整性和业务逻辑。

3. **错误处理**：测试各种错误场景的响应和错误信息。

4. **性能测试**：验证API的响应时间和并发处理能力。"""

        else:
            return f"""针对查询"{query}"，建议采用系统性的测试方法：

1. 分析需求和功能点，确定测试范围和重点。
2. 设计覆盖正常和异常场景的测试用例。
3. 考虑边界条件和特殊情况的测试。
4. 确保测试用例的可执行性和可维护性。"""
