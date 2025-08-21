"""
企业级测试用例生成智能体
基于测试点提取智能体的输出生成高质量企业级测试用例
应用专业测试设计技术，确保测试用例的完整性、可执行性和可维护性
基于AutoGen Core架构实现，遵循企业级测试标准
"""
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_core import message_handler, type_subscription, MessageContext, TopicId, AgentId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import (
    TestCaseGenerationResponse,
    TestCaseData, MindMapGenerationRequest, TestPointExtractionResponse,
    RagRetrievalRequest, RagRetrievalResponse
)
from app.core.enums import (
    TestType, TestLevel, Priority, TestCaseStatus, InputSource
)
from app.agents.database.test_case_saver_agent import TestCaseSaveRequest, TestCaseSaveResponse


class TestCaseGenerationResult(BaseModel):
    """企业级测试用例生成结果"""
    generation_strategy: str = Field(..., description="生成策略")
    generated_count: int = Field(0, description="生成的测试用例数量")
    generated_test_cases: List[TestCaseData] = Field(default_factory=list, description="生成的测试用例数据")
    test_case_categories: Dict[str, int] = Field(default_factory=dict, description="测试用例分类统计")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="质量指标")
    coverage_analysis: Dict[str, Any] = Field(default_factory=dict, description="覆盖度分析")
    automation_analysis: Dict[str, Any] = Field(default_factory=dict, description="自动化分析")
    test_execution_plan: Dict[str, Any] = Field(default_factory=dict, description="测试执行计划")
    processing_time: float = Field(0.0, description="处理时间")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


@type_subscription(topic_type=TopicTypes.TEST_CASE_GENERATOR.value)
class TestCaseGeneratorAgent(BaseAgent):
    """
    企业级测试用例生成智能体

    核心职责：
    1. 接收测试点提取智能体的专业输出
    2. 基于测试点生成企业级高质量测试用例
    3. 应用专业测试设计技术和最佳实践
    4. 确保测试用例的完整性、可执行性和可维护性
    5. 提供全面的质量分析和覆盖度评估

    企业级特性：
    - 测试点驱动：基于专业测试点生成详细测试用例
    - 质量保证：应用测试工程最佳实践
    - 分类管理：支持多种测试类型和级别
    - 自动化友好：考虑自动化测试需求
    - 可追溯性：维护测试点到测试用例的映射关系
    - 标准化：遵循企业级测试用例标准

    工作流程：
    1. 接收 TestPointExtractionResponse 消息
    2. 基于测试点生成企业级测试用例
    3. 保存测试用例到数据库
    4. 生成测试用例思维导图
    5. 返回完整的生成结果和质量分析
    """

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化企业级测试用例生成智能体"""
        super().__init__(
            agent_id=AgentTypes.TEST_CASE_GENERATOR.value,
            agent_name=AGENT_NAMES.get(AgentTypes.TEST_CASE_GENERATOR.value, "测试用例生成智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )

        # 企业级生成配置
        self.enterprise_config = {
            'enable_detailed_steps': True,
            'enable_preconditions': True,
            'enable_expected_results': True,
            'enable_test_data_generation': True,
            'enable_automation_hints': True,
            'enable_risk_assessment': True,
            'enable_traceability': True,
            'quality_threshold': 0.8,
            'max_test_cases_per_point': 5,
            'test_case_naming_convention': 'enterprise',
            'include_negative_scenarios': True,
            'include_boundary_conditions': True,
            'include_error_handling': True
        }

        # 测试设计技术配置
        self.test_design_techniques = {
            'equivalence_partitioning': True,
            'boundary_value_analysis': True,
            'decision_table_testing': True,
            'state_transition_testing': True,
            'use_case_testing': True,
            'error_guessing': True,
            'exploratory_testing': True,
            'pairwise_testing': True
        }



        # 质量指标跟踪
        self.quality_metrics = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0,
            "total_test_cases_generated": 0,
            "average_quality_score": 0.0,
            "automation_feasibility_score": 0.0,
            "coverage_completeness_score": 0.0
        }

        logger.info(f"企业级测试用例生成智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_test_point_extraction_response(
        self,
        message: TestPointExtractionResponse,
        ctx: MessageContext
    ) -> None:
        """
        处理测试点提取智能体的响应 - 企业级测试用例生成

        这是主要入口点，专门处理来自测试点提取智能体的专业输出
        基于测试点生成高质量的企业级测试用例
        """
        start_time = datetime.now()
        self.quality_metrics["total_requests"] += 1

        try:
            logger.info(f"开始处理测试点提取响应: {message.session_id}")

            # 发送开始处理消息
            await self.send_response(
                f"🏭 开始企业级测试用例生成，基于专业测试点提取结果",
                region="process"
            )

            # 分析测试点提取结果
            total_test_points = (
                len(message.functional_test_points) +
                len(message.non_functional_test_points) +
                len(message.integration_test_points) +
                len(message.acceptance_test_points) +
                len(message.boundary_test_points) +
                len(message.exception_test_points)
            )

            await self.send_response(
                f"📊 测试点分析: 功能测试点 {len(message.functional_test_points)} 个, "
                f"非功能测试点 {len(message.non_functional_test_points)} 个, "
                f"集成测试点 {len(message.integration_test_points)} 个, "
                f"总计 {total_test_points} 个测试点",
                region="info",
                result={
                    "functional_test_points_count": len(message.functional_test_points),
                    "non_functional_test_points_count": len(message.non_functional_test_points),
                    "integration_test_points_count": len(message.integration_test_points),
                    "acceptance_test_points_count": len(message.acceptance_test_points),
                    "boundary_test_points_count": len(message.boundary_test_points),
                    "exception_test_points_count": len(message.exception_test_points),
                    "total_test_points": total_test_points
                }
            )

            # 步骤1: 基于测试点生成企业级测试用例
            await self.send_response("🔄 第1步: 基于测试点生成企业级测试用例...", region="progress")
            generation_result = await self._generatetest_cases_from_test_points(message)

            if generation_result.generated_count == 0:
                await self.send_response("⚠️ 未能生成任何测试用例", region="warning")
                await self._handle_emptygeneration(message, generation_result)
                return

            # 发送生成结果统计
            await self.send_response(
                f"✅ 企业级测试用例生成完成: 共生成 {generation_result.generated_count} 个测试用例",
                region="success",
                result={
                    "generated_count": generation_result.generated_count,
                    "generation_time": generation_result.processing_time,
                    "test_case_categories": generation_result.test_case_categories,
                    "quality_score": generation_result.quality_metrics.get("overall_quality_score", 0.0)
                }
            )

            # 步骤2: 保存测试用例到数据库
            await self.send_response("🔄 第2步: 保存企业级测试用例到数据库...", region="progress")
            save_result = await self._sendsave_request(message, generation_result)

            # 步骤3: 生成思维导图（如果需要）
            mind_map_generated = False
            if save_result.success:
                await self.send_response("🔄 第3步: 生成测试用例思维导图...", region="progress")
                await self._sendmind_map_request(message, save_result.saved_test_cases)
                mind_map_generated = True
                await self.send_response("✅ 思维导图生成完成", region="success")

            # 步骤4: 发送最终响应
            await self._sendfinal_response(
                message, generation_result, save_result, mind_map_generated, start_time
            )

            # 更新质量指标
            self.quality_metrics["successful_generations"] += 1
            self.quality_metrics["total_test_cases_generated"] += generation_result.generated_count
            self._update_quality_metrics(generation_result)
            self._update_average_processing_time(start_time)

        except Exception as e:
            await self._handlegeneration_error(message, e, start_time)
            self.quality_metrics["failed_generations"] += 1


    def _update_average_processing_time(self, start_time: datetime):
        """更新平均处理时间"""
        processing_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.quality_metrics["average_processing_time"]
        total_requests = self.quality_metrics["total_requests"]

        # 计算新的平均值
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.quality_metrics["average_processing_time"] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.quality_metrics,
            "success_rate": (
                self.quality_metrics["successful_generations"] /
                max(self.quality_metrics["total_requests"], 1)
            ) * 100,
            "agent_name": self.agent_name,
            "agent_id": getattr(self, 'agent_id', 'test_case_generator')
        }

    # ==================== 企业级测试用例生成核心方法 ====================

    async def _generatetest_cases_from_test_points(
        self,
        message: TestPointExtractionResponse
    ) -> TestCaseGenerationResult:
        """基于测试点生成企业级测试用例"""
        try:
            start_time = datetime.now()
            result = TestCaseGenerationResult(
                generation_strategy="test_point_driven"
            )

            # 调用RAG系统查询需求相关的上下文
            await self.send_response("🔍 调用RAG知识库检索相关上下文...", region="progress")
            rag_context = await self._retrieve_rag_context(message)

            # 解析RAG上下文并构建增强提示
            enhanced_context = self._parse_rag_context(rag_context) if rag_context else {}

            await self.send_response(
                "🏭 正在基于专业测试点和RAG上下文生成企业级测试用例...",
                region="progress"
            )

            # 生成各类测试用例
            all_test_cases = []
            test_case_categories = {}

            # 1. 处理功能测试点 - 使用RAG增强上下文
            if message.functional_test_points:
                await self.send_response(f"📝 处理 {len(message.functional_test_points)} 个功能测试点...", region="progress")
                functional_cases = await self._generate_functional_test_cases(
                    message.functional_test_points, message, enhanced_context
                )
                all_test_cases.extend(functional_cases)
                test_case_categories["functional"] = len(functional_cases)

            # 2. 处理非功能测试点 - 使用RAG增强上下文
            if message.non_functional_test_points:
                await self.send_response(f"⚡ 处理 {len(message.non_functional_test_points)} 个非功能测试点...", region="progress")
                non_functional_cases = await self._generate_non_functional_test_cases(
                    message.non_functional_test_points, message, enhanced_context
                )
                all_test_cases.extend(non_functional_cases)
                test_case_categories["non_functional"] = len(non_functional_cases)

            # 3. 处理集成测试点 - 使用RAG增强上下文
            if message.integration_test_points:
                await self.send_response(f"🔗 处理 {len(message.integration_test_points)} 个集成测试点...", region="progress")
                integration_cases = await self._generate_integration_test_cases(
                    message.integration_test_points, message, enhanced_context
                )
                all_test_cases.extend(integration_cases)
                test_case_categories["integration"] = len(integration_cases)

            # 4. 处理验收测试点 - 使用RAG增强上下文
            if message.acceptance_test_points:
                await self.send_response(f"✅ 处理 {len(message.acceptance_test_points)} 个验收测试点...", region="progress")
                acceptance_cases = await self._generate_acceptance_test_cases(
                    message.acceptance_test_points, message, enhanced_context
                )
                all_test_cases.extend(acceptance_cases)
                test_case_categories["acceptance"] = len(acceptance_cases)

            # 5. 处理边界测试点 - 使用RAG增强上下文
            if message.boundary_test_points:
                await self.send_response(f"🎯 处理 {len(message.boundary_test_points)} 个边界测试点...", region="progress")
                boundary_cases = await self._generate_boundary_test_cases(
                    message.boundary_test_points, message, enhanced_context
                )
                all_test_cases.extend(boundary_cases)
                test_case_categories["boundary"] = len(boundary_cases)

            # 6. 处理异常测试点 - 使用RAG增强上下文
            if message.exception_test_points:
                await self.send_response(f"🚨 处理 {len(message.exception_test_points)} 个异常测试点...", region="progress")
                exception_cases = await self._generate_exception_test_cases(
                    message.exception_test_points, message, enhanced_context
                )
                all_test_cases.extend(exception_cases)
                test_case_categories["exception"] = len(exception_cases)

            # 计算质量指标
            quality_metrics = await self._calculate_quality_metrics(all_test_cases, message)

            # 生成覆盖度分析
            coverage_analysis = await self._analyze_test_coverage(all_test_cases, message)

            # 生成自动化分析
            automation_analysis = await self._analyze_automation_feasibility(all_test_cases, message)

            # 生成测试执行计划
            test_execution_plan = await self._generate_test_execution_plan(all_test_cases, message)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 构建结果
            result.generated_count = len(all_test_cases)
            result.generated_test_cases = all_test_cases
            result.test_case_categories = test_case_categories
            result.quality_metrics = quality_metrics
            result.coverage_analysis = coverage_analysis
            result.automation_analysis = automation_analysis
            result.test_execution_plan = test_execution_plan
            result.processing_time = processing_time

            await self.send_response(
                f"📊 企业级测试用例生成完成: 总计 {len(all_test_cases)} 个测试用例, "
                f"质量评分: {quality_metrics.get('overall_quality_score', 0.0):.2f}",
                region="success",
                result={
                    "total_count": len(all_test_cases),
                    "categories": test_case_categories,
                    "quality_score": quality_metrics.get('overall_quality_score', 0.0),
                    "automation_score": automation_analysis.get('overall_automation_score', 0.0),
                    "coverage_score": coverage_analysis.get('overall_coverage_score', 0.0)
                }
            )

            logger.info(f"成功生成了 {len(all_test_cases)} 个企业级测试用例")
            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"企业级测试用例生成失败: {str(e)}")
            await self.send_response(
                f"❌ 企业级测试用例生成失败: {str(e)} (耗时: {processing_time:.2f}秒)",
                region="error"
            )
            raise

    async def _generate_functional_test_cases(
        self,
        functional_test_points: List[Dict[str, Any]],
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """生成功能测试用例"""
        test_cases = []

        try:
            for test_point in functional_test_points:
                # 基于测试点生成详细测试用例 - 传递RAG上下文
                enhanced_cases = await self._create_detailed_test_cases_from_point(
                    test_point, TestType.FUNCTIONAL, TestLevel.SYSTEM, message, enhanced_context
                )
                test_cases.extend(enhanced_cases)

            return test_cases

        except Exception as e:
            logger.error(f"生成功能测试用例失败: {str(e)}")
            return []

    async def _generate_non_functional_test_cases(
        self,
        non_functional_test_points: List[Dict[str, Any]],
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """生成非功能测试用例"""
        test_cases = []

        try:
            for test_point in non_functional_test_points:
                # 根据非功能测试点类型确定测试类型
                test_type = self._map_non_functional_test_type(test_point.get("type", "performance"))

                enhanced_cases = await self._create_detailed_test_cases_from_point(
                    test_point, test_type, TestLevel.SYSTEM, message, enhanced_context
                )
                test_cases.extend(enhanced_cases)

            return test_cases

        except Exception as e:
            logger.error(f"生成非功能测试用例失败: {str(e)}")
            return []

    async def _generate_integration_test_cases(
        self,
        integration_test_points: List[Dict[str, Any]],
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """生成集成测试用例"""
        test_cases = []

        try:
            for test_point in integration_test_points:
                enhanced_cases = await self._create_detailed_test_cases_from_point(
                    test_point, TestType.INTERFACE, TestLevel.INTEGRATION, message, enhanced_context
                )
                test_cases.extend(enhanced_cases)

            return test_cases

        except Exception as e:
            logger.error(f"生成集成测试用例失败: {str(e)}")
            return []

    async def _generate_acceptance_test_cases(
        self,
        acceptance_test_points: List[Dict[str, Any]],
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """生成验收测试用例"""
        test_cases = []

        try:
            for test_point in acceptance_test_points:
                enhanced_cases = await self._create_detailed_test_cases_from_point(
                    test_point, TestType.FUNCTIONAL, TestLevel.ACCEPTANCE, message, enhanced_context
                )
                test_cases.extend(enhanced_cases)

            return test_cases

        except Exception as e:
            logger.error(f"生成验收测试用例失败: {str(e)}")
            return []

    async def _generate_boundary_test_cases(
        self,
        boundary_test_points: List[Dict[str, Any]],
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """生成边界测试用例"""
        test_cases = []

        try:
            for test_point in boundary_test_points:
                enhanced_cases = await self._create_detailed_test_cases_from_point(
                    test_point, TestType.FUNCTIONAL, TestLevel.UNIT, message, enhanced_context
                )
                test_cases.extend(enhanced_cases)

            return test_cases

        except Exception as e:
            logger.error(f"生成边界测试用例失败: {str(e)}")
            return []

    async def _generate_exception_test_cases(
        self,
        exception_test_points: List[Dict[str, Any]],
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """生成异常测试用例"""
        test_cases = []

        try:
            for test_point in exception_test_points:
                enhanced_cases = await self._create_detailed_test_cases_from_point(
                    test_point, TestType.FUNCTIONAL, TestLevel.SYSTEM, message, enhanced_context
                )
                test_cases.extend(enhanced_cases)

            return test_cases

        except Exception as e:
            logger.error(f"生成异常测试用例失败: {str(e)}")
            return []

    async def _create_detailed_test_cases_from_point(
        self,
        test_point: Dict[str, Any],
        test_type: TestType,
        test_level: TestLevel,
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> List[TestCaseData]:
        """基于测试点创建详细的测试用例"""
        try:
            test_cases = []

            # 获取测试点基本信息
            test_point_id = test_point.get("id", f"TP-{uuid.uuid4().hex[:8].upper()}")
            test_point_name = test_point.get("name", "未命名测试点")
            test_point_description = test_point.get("description", "")
            priority = self._map_priority(test_point.get("priority", "P2"))

            # 获取测试场景
            test_scenarios = test_point.get("test_scenarios", [test_point_name])
            if not test_scenarios:
                test_scenarios = [test_point_name]

            # 为每个测试场景生成测试用例
            for i, scenario in enumerate(test_scenarios):
                # 使用AI生成详细的测试用例内容 - 传递RAG上下文
                detailed_content = await self._ai_generate_detailed_test_case_content(
                    test_point, scenario, test_type, test_level, message, enhanced_context
                )

                # 创建测试用例
                test_case = TestCaseData(
                    title=f"{test_point_name} - {scenario}" if len(test_scenarios) > 1 else test_point_name,
                    description=f"{test_point_description}\n测试场景: {scenario}",
                    test_type=test_type,
                    test_level=test_level,
                    priority=priority,
                    input_source=InputSource.MANUAL,
                    preconditions=detailed_content.get("preconditions", ""),
                    test_steps=detailed_content.get("test_steps", []),
                    expected_results=detailed_content.get("expected_results", ""),
                    test_data=detailed_content.get("test_data", ""),
                    source_metadata={
                        "test_point_id": test_point_id,
                        "test_point_name": test_point_name,
                        "test_scenario": scenario,
                        "test_technique": test_point.get("test_technique"),
                        "automation_feasibility": test_point.get("automation_feasibility"),
                        "risk_level": test_point.get("risk_level"),
                        "business_impact": test_point.get("business_impact"),
                        "category": test_point.get("category"),
                        "related_requirements": test_point.get("related_requirements", []),
                        "generation_method": "test_point_driven",
                        "ai_enhanced": True
                    },
                    ai_confidence=0.85  # 基于测试点的生成置信度较高
                )

                test_cases.append(test_case)

            return test_cases

        except Exception as e:
            logger.error(f"创建详细测试用例失败: {str(e)}")
            # 返回基础测试用例
            return [TestCaseData(
                title=test_point.get("name", "测试用例"),
                description=test_point.get("description", ""),
                test_type=test_type,
                test_level=test_level,
                priority=self._map_priority(test_point.get("priority", "P2")),
                input_source=InputSource.MANUAL,
                source_metadata={
                    "test_point_id": test_point.get("id"),
                    "generation_method": "fallback",
                    "ai_enhanced": False
                },
                ai_confidence=0.5
            )]

    async def _ai_generate_detailed_test_case_content(
        self,
        test_point: Dict[str, Any],
        scenario: str,
        test_type: TestType,
        test_level: TestLevel,
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用AI生成详细的测试用例内容 - 集成RAG上下文"""
        try:
            # 创建AI增强智能体
            agent = self._createtest_case_generator()

            # 构建生成提示 - 传递RAG上下文
            generation_prompt = self._buildtest_case_prompt(
                test_point, scenario, test_type, test_level, message, enhanced_context
            )

            # 执行AI生成
            generation_result = await self._run_ai_test_case_generation(agent, generation_prompt)

            # 解析结果 - 增强JSON清理和错误处理
            return self._parse_ai_json_response(generation_result)

        except Exception as e:
            logger.error(f"AI生成详细测试用例内容失败: {str(e)}")
            logger.error(f"原始AI响应: {generation_result[:500] if 'generation_result' in locals() else 'N/A'}")
            return self._get_default_test_case_content(test_point, scenario)

    def _parse_ai_json_response(self, ai_response: str) -> Dict[str, Any]:
        """解析AI生成的JSON响应，增强错误处理"""
        try:
            # 第一步：基础清理
            cleaned_response = ai_response.strip()

            # 移除markdown代码块标记
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1]
            if "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[0]

            # 移除可能的前后空白和换行
            cleaned_response = cleaned_response.strip()

            # 第二步：尝试直接解析
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.warning(f"第一次JSON解析失败: {str(e)}")

                # 第三步：更激进的清理
                # 移除注释（// 和 /* */ 风格）
                import re
                cleaned_response = re.sub(r'//.*?$', '', cleaned_response, flags=re.MULTILINE)
                cleaned_response = re.sub(r'/\*.*?\*/', '', cleaned_response, flags=re.DOTALL)

                # 移除多余的逗号
                cleaned_response = re.sub(r',\s*}', '}', cleaned_response)
                cleaned_response = re.sub(r',\s*]', ']', cleaned_response)

                # 修复常见的引号问题
                cleaned_response = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', cleaned_response)

                # 第四步：再次尝试解析
                try:
                    return json.loads(cleaned_response)
                except json.JSONDecodeError as e2:
                    logger.error(f"第二次JSON解析也失败: {str(e2)}")
                    logger.error(f"清理后的响应: {cleaned_response[:200]}...")

                    # 第五步：尝试提取JSON对象
                    json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass

                    # 如果所有方法都失败，返回默认结构
                    raise ValueError(f"无法解析AI响应为有效JSON: {str(e2)}")

        except Exception as e:
            logger.error(f"JSON解析过程中发生错误: {str(e)}")
            raise

    def _createtest_case_generator(self):
        """创建企业级测试用例生成智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="enterprise_test_case_generator",
            system_message=self._buildtest_case_system_prompt(),
            model_client_type="deepseek"
        )

    def _buildtest_case_system_prompt(self) -> str:
        """构建企业级测试用例生成系统提示"""
        return """
你是资深的企业级测试工程师，拥有丰富的测试用例设计经验，擅长基于专业测试点生成高质量、可执行的企业级测试用例。

你的专业能力包括：
1. 测试用例设计和优化
2. 测试步骤详细化和标准化
3. 测试数据设计和管理
4. 前置条件和预期结果定义
5. 测试技术应用和最佳实践
6. 企业级测试标准遵循

**重要：必须严格按照以下JSON格式返回企业级测试用例内容，不要包含任何额外的文本、说明或markdown标记：**
{
    "preconditions": "详细的前置条件描述，包括系统状态、数据准备、环境要求等",
    "test_steps": [
        {
            "step_number": 1,
            "action": "具体的操作步骤描述",
            "input_data": "输入的测试数据",
            "expected_result": "该步骤的预期结果",
            "notes": "特殊说明或注意事项"
        },
        {
            "step_number": 2,
            "action": "下一个操作步骤",
            "input_data": "相应的测试数据",
            "expected_result": "预期的结果",
            "notes": "相关说明"
        }
    ],
    "expected_results": "整体测试用例的预期结果，包括功能验证点和质量标准",
    "test_data": "测试数据要求和示例，包括正常数据、边界数据、异常数据",
    "cleanup_steps": "测试后清理步骤，确保环境恢复",
    "automation_hints": "自动化测试建议，包括关键验证点和自动化策略",
    "risk_considerations": "风险考虑和缓解措施",
    "quality_attributes": {
        "completeness": "完整性评分 (0-1)",
        "clarity": "清晰度评分 (0-1)",
        "executability": "可执行性评分 (0-1)",
        "maintainability": "可维护性评分 (0-1)"
    }
}

企业级测试用例要求：
- 测试步骤要详细、具体、可执行
- 前置条件要明确、完整、可验证
- 预期结果要清晰、可量化、可验证
- 测试数据要全面、有代表性
- 考虑正常流程、异常流程、边界条件
- 包含自动化测试建议
- 遵循企业级测试标准和最佳实践
- 确保测试用例的可追溯性和可维护性

**格式要求：**
1. 只返回有效的JSON对象，不要包含任何其他文本
2. 所有字符串值必须用双引号包围
3. 数字值不要用引号包围
4. 确保JSON语法完全正确，没有多余的逗号
5. 不要使用注释或其他非标准JSON元素

注意：
- 返回有效的JSON格式，去掉 ```json 和 ```
- 测试步骤要逻辑清晰，步骤间有合理的依赖关系
- 考虑不同用户角色和权限场景
- 包含错误处理和异常情况的验证
"""

    def _buildtest_case_prompt(
        self,
        test_point: Dict[str, Any],
        scenario: str,
        test_type: TestType,
        test_level: TestLevel,
        message: TestPointExtractionResponse,
        enhanced_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建企业级测试用例生成提示 - 集成RAG上下文信息"""

        # 构建基础提示
        base_prompt = f"""
请基于以下专业测试点信息和RAG知识库上下文，生成企业级高质量测试用例：

测试点信息：
- ID: {test_point.get('id', 'N/A')}
- 名称: {test_point.get('name', 'N/A')}
- 描述: {test_point.get('description', 'N/A')}
- 类别: {test_point.get('category', 'N/A')}
- 优先级: {test_point.get('priority', 'N/A')}
- 测试技术: {test_point.get('test_technique', 'N/A')}
- 风险级别: {test_point.get('risk_level', 'N/A')}
- 业务影响: {test_point.get('business_impact', 'N/A')}
- 自动化可行性: {test_point.get('automation_feasibility', 'N/A')}

测试场景: {scenario}
测试类型: {test_type.value}
测试级别: {test_level.value}

测试点详细信息：
{json.dumps(test_point, ensure_ascii=False, indent=2)}

覆盖度分析：
{json.dumps(message.test_coverage_analysis, ensure_ascii=False, indent=2)}"""

        # 添加RAG上下文信息
        if enhanced_context:
            rag_context_prompt = self._build_rag_context_prompt(enhanced_context)
            base_prompt += f"\n\n{rag_context_prompt}"

        # 添加生成要求
        base_prompt += """

请生成符合企业级标准的详细测试用例，包括：
1. 详细的前置条件设置
2. 具体的测试执行步骤
3. 明确的预期结果验证
4. 全面的测试数据要求
5. 清理和恢复步骤
6. 自动化测试建议
7. 风险考虑和质量属性评估

确保测试用例具有高度的可执行性、可维护性和可追溯性。

**重要：请严格按照以下JSON格式返回结果，不要包含任何额外的文本或说明：**

```json
{
    "preconditions": "详细的前置条件描述",
    "test_steps": [
        {
            "step_number": 1,
            "action": "具体的操作描述",
            "input_data": "输入数据说明",
            "expected_result": "该步骤的预期结果",
            "notes": "备注信息"
        }
    ],
    "expected_results": "整体预期结果描述",
    "test_data": "测试数据要求说明",
    "cleanup_steps": "清理和恢复步骤",
    "automation_hints": "自动化实现建议",
    "risk_considerations": "风险考虑",
    "quality_attributes": {
        "completeness": 0.9,
        "clarity": 0.9,
        "testability": 0.9,
        "maintainability": 0.8
    }
}
```"""

        return base_prompt

    def _build_rag_context_prompt(self, enhanced_context: Dict[str, Any]) -> str:
        """构建RAG上下文提示信息"""
        context_parts = []

        # 添加业务领域知识
        if enhanced_context.get("domain_knowledge"):
            context_parts.append(f"""
📋 业务领域知识上下文：
{enhanced_context["domain_knowledge"][:500]}""")

        # 添加测试方法论
        if enhanced_context.get("test_methodologies"):
            context_parts.append(f"""
🔬 测试方法论指导：
{enhanced_context["test_methodologies"][:500]}""")

        # 添加场景模板
        if enhanced_context.get("scenario_templates"):
            context_parts.append(f"""
📝 相似场景模板：
{enhanced_context["scenario_templates"][:400]}""")

        # 添加质量标准
        if enhanced_context.get("quality_standards"):
            context_parts.append(f"""
⭐ 质量标准要求：
{enhanced_context["quality_standards"][:400]}""")

        # 添加行业标准
        if enhanced_context.get("industry_standards"):
            standards_text = "\n".join([f"- {std}" for std in enhanced_context["industry_standards"][:3]])
            context_parts.append(f"""
🏛️ 行业标准参考：
{standards_text}""")

        # 添加测试技术
        if enhanced_context.get("test_techniques"):
            techniques_text = "\n".join([f"- {tech}" for tech in enhanced_context["test_techniques"][:3]])
            context_parts.append(f"""
🛠️ 推荐测试技术：
{techniques_text}""")

        # 添加最佳实践
        if enhanced_context.get("best_practices"):
            practices_text = "\n".join([f"- {practice}" for practice in enhanced_context["best_practices"][:3]])
            context_parts.append(f"""
💡 最佳实践建议：
{practices_text}""")

        # 添加合规要求
        if enhanced_context.get("compliance_requirements"):
            compliance_text = "\n".join([f"- {req}" for req in enhanced_context["compliance_requirements"][:3]])
            context_parts.append(f"""
⚖️ 合规要求：
{compliance_text}""")

        if context_parts:
            return f"""
🧠 RAG知识库上下文信息：
{''.join(context_parts)}

请在生成测试用例时充分考虑以上上下文信息，确保测试用例符合业务领域特点、遵循测试方法论、参考相似场景模板、满足质量标准要求。"""
        else:
            return ""

    async def _run_ai_test_case_generation(self, agent, prompt: str) -> str:
        """执行AI测试用例生成"""
        try:
            stream = agent.run_stream(task=prompt)
            async for event in stream:  # type: ignore
                if isinstance(event, ModelClientStreamingChunkEvent):
                    continue

                if isinstance(event, TaskResult):
                    messages = event.messages
                    if messages and hasattr(messages[-1], 'content'):
                        return messages[-1].content

            return self._get_default_ai_generation_result()

        except Exception as e:
            logger.error(f"AI测试用例生成执行失败: {str(e)}")
            return self._get_default_ai_generation_result()

    def _get_default_test_case_content(
        self,
        test_point: Dict[str, Any],
        scenario: str
    ) -> Dict[str, Any]:
        """获取默认测试用例内容"""
        return {
            "preconditions": f"系统已启动，相关功能可用，测试环境已准备",
            "test_steps": [
                {
                    "step_number": 1,
                    "action": f"执行 {scenario}",
                    "input_data": "相应的测试数据",
                    "expected_result": "操作成功执行",
                    "notes": "基于测试点生成的默认步骤"
                }
            ],
            "expected_results": f"{scenario} 执行成功，满足预期要求",
            "test_data": "根据测试场景准备相应的测试数据",
            "cleanup_steps": "清理测试数据，恢复系统状态",
            "automation_hints": "可考虑自动化实现",
            "risk_considerations": "注意数据安全和系统稳定性",
            "quality_attributes": {
                "completeness": 0.7,
                "clarity": 0.7,
                "executability": 0.8,
                "maintainability": 0.7
            }
        }

    def _get_default_ai_generation_result(self) -> str:
        """获取默认AI生成结果"""
        return """
{
    "preconditions": "系统已启动，用户已登录，测试环境已准备",
    "test_steps": [
        {
            "step_number": 1,
            "action": "执行测试操作",
            "input_data": "测试数据",
            "expected_result": "操作成功",
            "notes": "默认测试步骤"
        }
    ],
    "expected_results": "测试通过，功能正常",
    "test_data": "准备相应的测试数据",
    "cleanup_steps": "清理测试数据",
    "automation_hints": "可考虑自动化",
    "risk_considerations": "注意系统稳定性",
    "quality_attributes": {
        "completeness": 0.8,
        "clarity": 0.8,
        "executability": 0.8,
        "maintainability": 0.8
    }
}
"""

    # ==================== 质量分析和评估方法 ====================

    async def _calculate_quality_metrics(
        self,
        test_cases: List[TestCaseData],
        message: TestPointExtractionResponse
    ) -> Dict[str, Any]:
        """计算测试用例质量指标"""
        try:
            if not test_cases:
                return {"overall_quality_score": 0.0, "analysis_status": "no_test_cases"}

            # 计算各项质量指标
            completeness_scores = []
            clarity_scores = []
            executability_scores = []
            maintainability_scores = []

            for test_case in test_cases:
                # 从源数据中获取质量属性
                quality_attrs = test_case.source_metadata.get("quality_attributes", {})
                completeness_scores.append(quality_attrs.get("completeness", 0.8))
                clarity_scores.append(quality_attrs.get("clarity", 0.8))
                executability_scores.append(quality_attrs.get("executability", 0.8))
                maintainability_scores.append(quality_attrs.get("maintainability", 0.8))

            # 计算平均分
            avg_completeness = sum(completeness_scores) / len(completeness_scores)
            avg_clarity = sum(clarity_scores) / len(clarity_scores)
            avg_executability = sum(executability_scores) / len(executability_scores)
            avg_maintainability = sum(maintainability_scores) / len(maintainability_scores)

            # 计算整体质量分数
            overall_quality_score = (
                avg_completeness * 0.25 +
                avg_clarity * 0.25 +
                avg_executability * 0.3 +
                avg_maintainability * 0.2
            )

            return {
                "overall_quality_score": round(overall_quality_score, 3),
                "completeness_score": round(avg_completeness, 3),
                "clarity_score": round(avg_clarity, 3),
                "executability_score": round(avg_executability, 3),
                "maintainability_score": round(avg_maintainability, 3),
                "total_test_cases": len(test_cases),
                "quality_distribution": {
                    "high_quality": len([tc for tc in test_cases if tc.ai_confidence > 0.8]),
                    "medium_quality": len([tc for tc in test_cases if 0.6 <= tc.ai_confidence <= 0.8]),
                    "low_quality": len([tc for tc in test_cases if tc.ai_confidence < 0.6])
                },
                "analysis_status": "completed"
            }

        except Exception as e:
            logger.error(f"计算质量指标失败: {str(e)}")
            return {"overall_quality_score": 0.5, "analysis_status": "failed", "error": str(e)}

    async def _analyze_test_coverage(
        self,
        test_cases: List[TestCaseData],
        message: TestPointExtractionResponse
    ) -> Dict[str, Any]:
        """分析测试覆盖度"""
        try:
            # 统计各类测试用例数量
            test_type_coverage = {}
            test_level_coverage = {}
            priority_coverage = {}

            for test_case in test_cases:
                # 测试类型覆盖度
                test_type = test_case.test_type.value
                test_type_coverage[test_type] = test_type_coverage.get(test_type, 0) + 1

                # 测试级别覆盖度
                test_level = test_case.test_level.value
                test_level_coverage[test_level] = test_level_coverage.get(test_level, 0) + 1

                # 优先级覆盖度
                priority = test_case.priority.value
                priority_coverage[priority] = priority_coverage.get(priority, 0) + 1

            # 计算覆盖度分数
            total_test_points = (
                len(message.functional_test_points) +
                len(message.non_functional_test_points) +
                len(message.integration_test_points) +
                len(message.acceptance_test_points) +
                len(message.boundary_test_points) +
                len(message.exception_test_points)
            )

            coverage_ratio = len(test_cases) / max(total_test_points, 1)
            overall_coverage_score = min(coverage_ratio, 1.0)

            return {
                "overall_coverage_score": round(overall_coverage_score, 3),
                "test_type_coverage": test_type_coverage,
                "test_level_coverage": test_level_coverage,
                "priority_coverage": priority_coverage,
                "total_test_cases": len(test_cases),
                "total_test_points": total_test_points,
                "coverage_ratio": round(coverage_ratio, 3),
                "coverage_gaps": self._identify_coverage_gaps(message, test_cases),
                "analysis_status": "completed"
            }

        except Exception as e:
            logger.error(f"分析测试覆盖度失败: {str(e)}")
            return {"overall_coverage_score": 0.5, "analysis_status": "failed", "error": str(e)}

    async def _analyze_automation_feasibility(
        self,
        test_cases: List[TestCaseData],
        message: TestPointExtractionResponse
    ) -> Dict[str, Any]:
        """分析自动化可行性"""
        try:
            automation_scores = []
            high_automation = 0
            medium_automation = 0
            low_automation = 0

            for test_case in test_cases:
                # 从测试点获取自动化可行性
                automation_feasibility = test_case.source_metadata.get("automation_feasibility", "medium")

                if automation_feasibility == "high":
                    automation_scores.append(0.9)
                    high_automation += 1
                elif automation_feasibility == "medium":
                    automation_scores.append(0.6)
                    medium_automation += 1
                else:
                    automation_scores.append(0.3)
                    low_automation += 1

            overall_automation_score = sum(automation_scores) / len(automation_scores) if automation_scores else 0.5

            return {
                "overall_automation_score": round(overall_automation_score, 3),
                "automation_distribution": {
                    "high_automation": high_automation,
                    "medium_automation": medium_automation,
                    "low_automation": low_automation
                },
                "automation_recommendations": self._generate_automation_recommendations(test_cases),
                "automation_tools": ["Selenium", "Postman", "JMeter", "Cypress"],
                "analysis_status": "completed"
            }

        except Exception as e:
            logger.error(f"分析自动化可行性失败: {str(e)}")
            return {"overall_automation_score": 0.5, "analysis_status": "failed", "error": str(e)}

    async def _generate_test_execution_plan(
        self,
        test_cases: List[TestCaseData],
        message: TestPointExtractionResponse
    ) -> Dict[str, Any]:
        """生成测试执行计划"""
        try:
            # 按优先级分组
            priority_groups = {}
            for test_case in test_cases:
                priority = test_case.priority.value
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(test_case)

            # 生成执行序列
            execution_sequence = []
            for priority in ["P0", "P1", "P2", "P3", "P4"]:
                if priority in priority_groups:
                    execution_sequence.append({
                        "phase": f"优先级 {priority} 测试",
                        "test_cases_count": len(priority_groups[priority]),
                        "estimated_time": len(priority_groups[priority]) * 15,  # 假设每个用例15分钟
                        "parallel_execution": priority in ["P2", "P3", "P4"],
                        "dependencies": ["前置环境准备"] if priority == "P0" else [f"优先级 P{int(priority[1])-1} 测试完成"]
                    })

            return {
                "execution_sequence": execution_sequence,
                "total_estimated_time": sum([phase["estimated_time"] for phase in execution_sequence]),
                "parallel_phases": len([phase for phase in execution_sequence if phase["parallel_execution"]]),
                "critical_path": [phase["phase"] for phase in execution_sequence if not phase["parallel_execution"]],
                "resource_requirements": {
                    "test_environments": 2,
                    "test_data_sets": 3,
                    "testers_required": max(1, len(test_cases) // 20)
                },
                "analysis_status": "completed"
            }

        except Exception as e:
            logger.error(f"生成测试执行计划失败: {str(e)}")
            return {"analysis_status": "failed", "error": str(e)}

    def _identify_coverage_gaps(
        self,
        message: TestPointExtractionResponse,
        test_cases: List[TestCaseData]
    ) -> List[str]:
        """识别覆盖度缺口"""
        gaps = []

        # 检查是否有未覆盖的测试点类型
        if message.functional_test_points and not any(tc.test_type == TestType.FUNCTIONAL for tc in test_cases):
            gaps.append("功能测试覆盖不足")

        if message.non_functional_test_points and not any(tc.test_type in [TestType.PERFORMANCE, TestType.SECURITY] for tc in test_cases):
            gaps.append("非功能测试覆盖不足")

        if message.integration_test_points and not any(tc.test_level == TestLevel.INTEGRATION for tc in test_cases):
            gaps.append("集成测试覆盖不足")

        if message.boundary_test_points and len([tc for tc in test_cases if "boundary" in tc.source_metadata.get("test_technique", "").lower()]) == 0:
            gaps.append("边界测试覆盖不足")

        return gaps

    def _generate_automation_recommendations(self, test_cases: List[TestCaseData]) -> List[str]:
        """生成自动化建议"""
        recommendations = []

        high_automation_count = len([tc for tc in test_cases if tc.source_metadata.get("automation_feasibility") == "high"])
        total_count = len(test_cases)

        if high_automation_count / total_count > 0.7:
            recommendations.append("建议优先实现高自动化可行性的测试用例")

        if any(tc.test_type == TestType.PERFORMANCE for tc in test_cases):
            recommendations.append("性能测试建议使用JMeter或LoadRunner")

        if any(tc.test_type == TestType.FUNCTIONAL for tc in test_cases):
            recommendations.append("功能测试建议使用Selenium或Cypress")

        if any(tc.test_type == TestType.INTERFACE for tc in test_cases):
            recommendations.append("接口测试建议使用Postman或RestAssured")

        return recommendations

    def _map_non_functional_test_type(self, nfr_type: str) -> TestType:
        """映射非功能需求类型到测试类型"""
        mapping = {
            "performance": TestType.PERFORMANCE,
            "security": TestType.SECURITY,
            "usability": TestType.USABILITY,
            "reliability": TestType.FUNCTIONAL,
            "scalability": TestType.PERFORMANCE,
            "compatibility": TestType.COMPATIBILITY,
            "maintainability": TestType.FUNCTIONAL,
            "availability": TestType.FUNCTIONAL
        }
        return mapping.get(nfr_type.lower(), TestType.FUNCTIONAL)

    def _map_priority(self, priority_str: str) -> Priority:
        """映射优先级"""
        mapping = {
            "high": Priority.P1,
            "medium": Priority.P2,
            "low": Priority.P3,
            "critical": Priority.P0,
            "P0": Priority.P0,
            "P1": Priority.P1,
            "P2": Priority.P2,
            "P3": Priority.P3,
            "P4": Priority.P4
        }
        return mapping.get(priority_str, Priority.P2)

    # ==================== 企业级响应处理方法 ====================

    async def _sendsave_request(
        self,
        message: TestPointExtractionResponse,
        generation_result: TestCaseGenerationResult
    ) -> TestCaseSaveResponse:
        """发送企业级保存请求到数据库智能体"""
        try:
            # 构建保存请求
            save_request = TestCaseSaveRequest(
                session_id=message.session_id,
                test_cases=generation_result.generated_test_cases,
                project_id=None,  # 可以从消息中获取
                created_by="test_point_extractor",
                source_metadata={
                    "source_type": "test_point_extraction",
                    "extraction_id": message.extraction_id,
                    "generation_strategy": generation_result.generation_strategy,
                    "quality_metrics": generation_result.quality_metrics,
                    "coverage_analysis": generation_result.coverage_analysis,
                    "automation_analysis": generation_result.automation_analysis,
                    "test_execution_plan": generation_result.test_execution_plan,
                    "test_case_categories": generation_result.test_case_categories
                }
            )

            logger.info(f"已发送企业级保存请求到数据库智能体: {message.session_id}")

            test_case_save_response = await self.send_message(
                save_request,
                AgentId(type=TopicTypes.TEST_CASE_SAVER.value, key=self.id.key)
            )
            return test_case_save_response

        except Exception as e:
            logger.error(f"发送企业级保存请求失败: {str(e)}")
            return TestCaseSaveResponse(
                session_id=message.session_id,
                success=False,
                errors=[str(e)]
            )

    async def _sendmind_map_request(
        self,
        message: TestPointExtractionResponse,
        saved_test_cases: List[Dict[str, Any]]
    ):
        """发送企业级思维导图生成请求"""
        try:
            await self.send_response("🧠 正在生成企业级测试用例思维导图...")

            # 构建思维导图生成请求
            mind_map_request = MindMapGenerationRequest(
                session_id=message.session_id,
                test_case_ids=[tc["id"] for tc in saved_test_cases],
                source_data={
                    "extraction_result": message.extraction_result,
                    "test_coverage_analysis": message.test_coverage_analysis,
                    "test_priority_matrix": message.test_priority_matrix
                },
                generation_config={
                    "layout_type": "enterprise",
                    "include_test_points": True,
                    "include_coverage_analysis": True,
                    "include_priority_matrix": True,
                    "group_by_category": True
                }
            )

            # 发送到思维导图生成智能体
            await self.publish_message(
                mind_map_request,
                topic_id=TopicId(type=TopicTypes.MIND_MAP_GENERATOR.value, source=self.id.key)
            )

            logger.info(f"已发送企业级思维导图生成请求: {message.session_id}")

        except Exception as e:
            logger.error(f"发送企业级思维导图生成请求失败: {str(e)}")

    async def _handle_emptygeneration(
        self,
        message: TestPointExtractionResponse,
        generation_result: TestCaseGenerationResult
    ):
        """处理空的企业级生成结果"""
        response = TestCaseGenerationResponse(
            session_id=message.session_id,
            generation_id=str(uuid.uuid4()),
            source_type="test_point_extraction",
            generated_count=0,
            test_case_ids=[],
            mind_map_generated=False,
            processing_time=generation_result.processing_time,
            created_at=datetime.now().isoformat()
        )

        await self.send_response(
            "⚠️ 未生成任何企业级测试用例",
            is_final=True,
            result=response.model_dump()
        )

    async def _sendfinal_response(
        self,
        message: TestPointExtractionResponse,
        generation_result: TestCaseGenerationResult,
        save_result: TestCaseSaveResponse,
        mind_map_generated: bool,
        start_time: datetime
    ):
        """发送企业级最终响应"""
        processing_time = (datetime.now() - start_time).total_seconds()

        response = TestCaseGenerationResponse(
            session_id=message.session_id,
            generation_id=str(uuid.uuid4()),
            source_type="test_point_extraction",
            generated_count=generation_result.generated_count,
            test_case_ids=[tc["id"] for tc in save_result.saved_test_cases] if save_result.success else [],
            mind_map_generated=mind_map_generated,
            processing_time=processing_time,
            created_at=datetime.now().isoformat()
        )

        if save_result.success:
            await self.send_response(
                f"🏆 企业级测试用例处理完成！生成 {generation_result.generated_count} 个高质量测试用例，"
                f"成功保存 {save_result.saved_count} 个，质量评分: {generation_result.quality_metrics.get('overall_quality_score', 0.0):.2f}",
                is_final=False,
                result={
                    **response.model_dump(),
                    "quality_metrics": generation_result.quality_metrics,
                    "coverage_analysis": generation_result.coverage_analysis,
                    "automation_analysis": generation_result.automation_analysis,
                    "test_execution_plan": generation_result.test_execution_plan,
                    "test_case_categories": generation_result.test_case_categories
                }
            )
        else:
            await self.send_response(
                f"⚠️ 企业级测试用例生成完成，但保存时出现问题：成功 {save_result.saved_count} 个，失败 {save_result.failed_count} 个",
                is_final=True,
                result=response.model_dump()
            )

    async def _handlegeneration_error(
        self,
        message: TestPointExtractionResponse,
        error: Exception,
        start_time: datetime
    ):
        """处理企业级生成错误"""
        processing_time = (datetime.now() - start_time).total_seconds()

        error_response = TestCaseGenerationResponse(
            session_id=message.session_id,
            generation_id=str(uuid.uuid4()),
            source_type="test_point_extraction",
            generated_count=0,
            test_case_ids=[],
            mind_map_generated=False,
            processing_time=processing_time,
            created_at=datetime.now().isoformat()
        )

        await self.send_response(
            f"❌ 企业级测试用例生成失败: {str(error)}",
            is_final=True,
            result=error_response.model_dump()
        )

        logger.error(f"企业级测试用例生成失败: {message.session_id}, 错误: {str(error)}")

    def _update_quality_metrics(self, generation_result: TestCaseGenerationResult):
        """更新质量指标"""
        if generation_result.quality_metrics:
            current_avg_quality = self.quality_metrics["average_quality_score"]
            total_requests = self.quality_metrics["total_requests"]
            new_quality_score = generation_result.quality_metrics.get("overall_quality_score", 0.0)

            # 计算新的平均质量分数
            new_avg_quality = ((current_avg_quality * (total_requests - 1)) + new_quality_score) / total_requests
            self.quality_metrics["average_quality_score"] = new_avg_quality

        if generation_result.automation_analysis:
            automation_score = generation_result.automation_analysis.get("overall_automation_score", 0.0)
            current_avg_automation = self.quality_metrics["automation_feasibility_score"]
            total_requests = self.quality_metrics["total_requests"]

            new_avg_automation = ((current_avg_automation * (total_requests - 1)) + automation_score) / total_requests
            self.quality_metrics["automation_feasibility_score"] = new_avg_automation

        if generation_result.coverage_analysis:
            coverage_score = generation_result.coverage_analysis.get("overall_coverage_score", 0.0)
            current_avg_coverage = self.quality_metrics["coverage_completeness_score"]
            total_requests = self.quality_metrics["total_requests"]

            new_avg_coverage = ((current_avg_coverage * (total_requests - 1)) + coverage_score) / total_requests
            self.quality_metrics["coverage_completeness_score"] = new_avg_coverage

    async def _retrieve_rag_context(
        self,
        message: TestPointExtractionResponse
    ) -> Optional[Dict[str, Any]]:
        """
        调用RAG知识库检索相关上下文 - 多维度分层检索策略

        采用4个维度的RAG查询来获取全面的上下文信息：
        1. 业务领域上下文 - 获取行业标准和业务知识
        2. 测试方法论上下文 - 获取测试技术和最佳实践
        3. 相似场景上下文 - 获取相似功能的测试用例模板
        4. 质量标准上下文 - 获取质量要求和合规标准
        """
        try:
            await self.send_response("🔍 开始多维度RAG上下文检索...", region="progress")

            # 解析需求分析结果
            analysis_result = message.requirement_analysis_result or {}

            # 构建多维度RAG查询
            rag_contexts = {}

            # 1. 业务领域上下文查询
            domain_context = await self._retrieve_domain_context(analysis_result, message)
            if domain_context:
                rag_contexts["domain"] = domain_context
                await self.send_response("✅ 业务领域上下文检索完成", region="info")

            # 2. 测试方法论上下文查询
            methodology_context = await self._retrieve_methodology_context(message)
            if methodology_context:
                rag_contexts["methodology"] = methodology_context
                await self.send_response("✅ 测试方法论上下文检索完成", region="info")

            # 3. 相似场景上下文查询
            scenario_context = await self._retrieve_scenario_context(analysis_result, message)
            if scenario_context:
                rag_contexts["scenarios"] = scenario_context
                await self.send_response("✅ 相似场景上下文检索完成", region="info")

            # 4. 质量标准上下文查询
            quality_context = await self._retrieve_quality_context(analysis_result, message)
            if quality_context:
                rag_contexts["quality"] = quality_context
                await self.send_response("✅ 质量标准上下文检索完成", region="info")

            # 汇总检索结果
            total_contexts = len(rag_contexts)
            if total_contexts > 0:
                await self.send_response(
                    f"🎯 RAG多维度检索完成: 获取到 {total_contexts} 个维度的上下文信息",
                    region="success"
                )
                return rag_contexts
            else:
                await self.send_response("⚠️ 未获取到RAG上下文信息", region="warning")
                return None

        except Exception as e:
            logger.error(f"RAG多维度上下文检索失败: {str(e)}")
            await self.send_response(
                f"❌ RAG上下文检索失败: {str(e)}",
                region="error"
            )
            return None

    async def _retrieve_domain_context(
        self,
        analysis_result: Dict[str, Any],
        message: TestPointExtractionResponse
    ) -> Optional[RagRetrievalResponse]:
        """检索业务领域上下文"""
        try:
            # 构建业务领域查询
            domain_query_parts = []

            # 从需求分析中提取业务领域信息
            if analysis_result.get("document_title"):
                domain_query_parts.append(analysis_result["document_title"])

            if analysis_result.get("executive_summary"):
                # 提取关键业务词汇
                summary = analysis_result["executive_summary"][:200]
                domain_query_parts.append(summary)

            # 添加业务流程信息
            business_processes = analysis_result.get("business_processes", [])
            if business_processes:
                for process in business_processes[:2]:
                    if process.get("name"):
                        domain_query_parts.append(process["name"])

            # 构建领域查询
            domain_query = " ".join(domain_query_parts) + " 行业标准 测试规范 业务规则"

            # 发送RAG检索请求
            rag_request = RagRetrievalRequest(
                session_id=message.session_id,
                query=domain_query,
                requirements=analysis_result.get("executive_summary", ""),
                search_mode="advanced",
                search_settings={
                    "use_semantic_search": True,
                    "use_fulltext_search": True,
                    "limit": 5,
                    "filters": {
                        "metadata.context_type": {"$in": ["domain_knowledge", "industry_standards", "business_rules"]}
                    }
                },
                rag_generation_config={
                    "stream": False,
                    "max_tokens": 400
                },
                context_type="domain_knowledge",
                max_results=5
            )

            return await self._send_rag_request(rag_request)

        except Exception as e:
            logger.error(f"业务领域上下文检索失败: {str(e)}")
            return None

    async def _retrieve_methodology_context(
        self,
        message: TestPointExtractionResponse
    ) -> Optional[RagRetrievalResponse]:
        """检索测试方法论上下文"""
        try:
            # 构建测试方法论查询
            methodology_query_parts = []

            # 分析测试点类型
            test_types = []
            if message.functional_test_points:
                test_types.append("功能测试")
            if message.non_functional_test_points:
                test_types.append("非功能测试")
            if message.integration_test_points:
                test_types.append("集成测试")
            if message.boundary_test_points:
                test_types.append("边界测试")
            if message.exception_test_points:
                test_types.append("异常测试")

            methodology_query_parts.extend(test_types)

            # 添加测试技术关键词
            methodology_query_parts.extend([
                "测试用例设计", "测试方法", "测试技术", "等价类划分",
                "边界值分析", "决策表测试", "状态转换测试"
            ])

            methodology_query = " ".join(methodology_query_parts)

            # 发送RAG检索请求
            rag_request = RagRetrievalRequest(
                session_id=message.session_id,
                query=methodology_query,
                test_points=message.functional_test_points[:3] + message.non_functional_test_points[:2],
                search_mode="advanced",
                search_settings={
                    "use_semantic_search": True,
                    "limit": 6,
                    "filters": {
                        "metadata.context_type": {"$in": ["test_methodology", "test_techniques", "best_practices"]}
                    }
                },
                rag_generation_config={
                    "stream": False,
                    "max_tokens": 500
                },
                context_type="test_methodology",
                max_results=6
            )

            return await self._send_rag_request(rag_request)

        except Exception as e:
            logger.error(f"测试方法论上下文检索失败: {str(e)}")
            return None

    async def _retrieve_scenario_context(
        self,
        analysis_result: Dict[str, Any],
        message: TestPointExtractionResponse
    ) -> Optional[RagRetrievalResponse]:
        """检索相似场景上下文"""
        try:
            # 构建相似场景查询
            scenario_query_parts = []

            # 提取功能需求作为场景描述
            functional_reqs = analysis_result.get("functional_requirements", [])
            if functional_reqs:
                for req in functional_reqs[:3]:
                    if req.get("title"):
                        scenario_query_parts.append(req["title"])
                    if req.get("description"):
                        scenario_query_parts.append(req["description"][:100])

            # 提取用户故事
            user_stories = analysis_result.get("user_stories", [])
            if user_stories:
                for story in user_stories[:2]:
                    if story.get("story"):
                        scenario_query_parts.append(story["story"][:100])

            # 添加场景关键词
            scenario_query_parts.extend([
                "测试用例模板", "测试场景", "用例设计", "测试步骤"
            ])

            scenario_query = " ".join(scenario_query_parts)

            # 发送RAG检索请求
            rag_request = RagRetrievalRequest(
                session_id=message.session_id,
                query=scenario_query,
                requirements=analysis_result.get("executive_summary", ""),
                test_points=message.functional_test_points[:2],
                search_mode="advanced",
                search_settings={
                    "use_semantic_search": True,
                    "limit": 5,
                    "filters": {
                        "metadata.context_type": {"$in": ["test_scenarios", "test_templates", "similar_cases"]}
                    }
                },
                rag_generation_config={
                    "stream": False,
                    "max_tokens": 400
                },
                context_type="test_scenarios",
                max_results=5
            )

            return await self._send_rag_request(rag_request)

        except Exception as e:
            logger.error(f"相似场景上下文检索失败: {str(e)}")
            return None

    async def _retrieve_quality_context(
        self,
        analysis_result: Dict[str, Any],
        message: TestPointExtractionResponse
    ) -> Optional[RagRetrievalResponse]:
        """检索质量标准上下文"""
        try:
            # 构建质量标准查询
            quality_query_parts = []

            # 提取非功能需求
            non_functional_reqs = analysis_result.get("non_functional_requirements", [])
            if non_functional_reqs:
                for req in non_functional_reqs[:3]:
                    if req.get("title"):
                        quality_query_parts.append(req["title"])

            # 提取约束条件
            constraints = analysis_result.get("constraints", [])
            if constraints:
                for constraint in constraints[:2]:
                    if constraint.get("description"):
                        quality_query_parts.append(constraint["description"][:100])

            # 添加质量关键词
            quality_query_parts.extend([
                "质量标准", "测试覆盖度", "验收标准", "合规要求",
                "性能标准", "安全标准", "可用性标准"
            ])

            quality_query = " ".join(quality_query_parts)

            # 发送RAG检索请求
            rag_request = RagRetrievalRequest(
                session_id=message.session_id,
                query=quality_query,
                test_points=message.non_functional_test_points[:3],
                search_mode="advanced",
                search_settings={
                    "use_semantic_search": True,
                    "limit": 4,
                    "filters": {
                        "metadata.context_type": {"$in": ["quality_standards", "compliance", "acceptance_criteria"]}
                    }
                },
                rag_generation_config={
                    "stream": False,
                    "max_tokens": 300
                },
                context_type="quality_standards",
                max_results=4
            )

            return await self._send_rag_request(rag_request)

        except Exception as e:
            logger.error(f"质量标准上下文检索失败: {str(e)}")
            return None

    async def _send_rag_request(self, rag_request: RagRetrievalRequest) -> Optional[RagRetrievalResponse]:
        """发送RAG检索请求"""
        try:
            # 发送到RAG检索智能体
            await self.publish_message(
                rag_request,
                topic_id=TopicId(type=TopicTypes.RAG_RETRIEVAL.value, source=self.id.key)
            )

            # 注意：这里应该等待响应，但在当前架构中，我们需要通过消息处理器来接收响应
            # 为了简化，这里返回None，实际的RAG响应会通过消息处理器处理
            logger.info("RAG检索请求已发送")
            return None

        except Exception as e:
            logger.error(f"RAG请求发送失败: {str(e)}")
            return None

    def _parse_rag_context(self, rag_contexts: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析RAG上下文信息，提取关键信息用于测试用例生成

        Args:
            rag_contexts: 多维度RAG检索结果

        Returns:
            解析后的上下文信息字典
        """
        try:
            enhanced_context = {
                "domain_knowledge": "",
                "test_methodologies": "",
                "scenario_templates": "",
                "quality_standards": "",
                "best_practices": [],
                "industry_standards": [],
                "test_techniques": [],
                "compliance_requirements": []
            }

            # 解析业务领域上下文
            if "domain" in rag_contexts:
                domain_context = rag_contexts["domain"]
                if hasattr(domain_context, 'rag_completion') and domain_context.rag_completion:
                    enhanced_context["domain_knowledge"] = domain_context.rag_completion

                # 提取行业标准
                if hasattr(domain_context, 'search_results'):
                    for result in domain_context.search_results[:3]:
                        if isinstance(result, dict) and result.get("text"):
                            if "标准" in result["text"] or "规范" in result["text"]:
                                enhanced_context["industry_standards"].append(result["text"][:200])

            # 解析测试方法论上下文
            if "methodology" in rag_contexts:
                methodology_context = rag_contexts["methodology"]
                if hasattr(methodology_context, 'rag_completion') and methodology_context.rag_completion:
                    enhanced_context["test_methodologies"] = methodology_context.rag_completion

                # 提取测试技术
                if hasattr(methodology_context, 'search_results'):
                    for result in methodology_context.search_results[:3]:
                        if isinstance(result, dict) and result.get("text"):
                            if any(tech in result["text"] for tech in ["等价类", "边界值", "决策表", "状态转换"]):
                                enhanced_context["test_techniques"].append(result["text"][:200])

            # 解析场景模板上下文
            if "scenarios" in rag_contexts:
                scenario_context = rag_contexts["scenarios"]
                if hasattr(scenario_context, 'rag_completion') and scenario_context.rag_completion:
                    enhanced_context["scenario_templates"] = scenario_context.rag_completion

                # 提取最佳实践
                if hasattr(scenario_context, 'search_results'):
                    for result in scenario_context.search_results[:3]:
                        if isinstance(result, dict) and result.get("text"):
                            if "最佳实践" in result["text"] or "模板" in result["text"]:
                                enhanced_context["best_practices"].append(result["text"][:200])

            # 解析质量标准上下文
            if "quality" in rag_contexts:
                quality_context = rag_contexts["quality"]
                if hasattr(quality_context, 'rag_completion') and quality_context.rag_completion:
                    enhanced_context["quality_standards"] = quality_context.rag_completion

                # 提取合规要求
                if hasattr(quality_context, 'search_results'):
                    for result in quality_context.search_results[:3]:
                        if isinstance(result, dict) and result.get("text"):
                            if "合规" in result["text"] or "标准" in result["text"]:
                                enhanced_context["compliance_requirements"].append(result["text"][:200])

            logger.info(f"RAG上下文解析完成: 获取到 {len([k for k, v in enhanced_context.items() if v])} 个有效上下文")
            return enhanced_context

        except Exception as e:
            logger.error(f"RAG上下文解析失败: {str(e)}")
            return {}
