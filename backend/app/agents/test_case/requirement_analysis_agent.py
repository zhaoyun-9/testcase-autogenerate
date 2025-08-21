"""
需求解析智能体
专门负责对其他智能体传入的软件需求文档内容进行企业级专业的需求解析
基于AutoGen Core架构实现，参考document_parser_agent.py的优秀设计模式
"""
import uuid
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import (
    RequirementAnalysisRequest, RequirementAnalysisResponse,
    TestPointExtractionRequest, TestCaseData
)
from app.core.enums import TestType, TestLevel, Priority, InputSource
from app.agents.database.requirement_saver_agent import RequirementSaveRequest


class RequirementAnalysisResult(BaseModel):
    """需求解析结果"""
    analysis_type: str = Field(..., description="解析类型")
    document_title: str = Field(..., description="文档标题")
    executive_summary: str = Field(..., description="执行摘要")
    functional_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="功能需求")
    non_functional_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="非功能需求")
    business_processes: List[Dict[str, Any]] = Field(default_factory=list, description="业务流程")
    user_stories: List[Dict[str, Any]] = Field(default_factory=list, description="用户故事")
    acceptance_criteria: List[Dict[str, Any]] = Field(default_factory=list, description="验收标准")
    stakeholders: List[Dict[str, Any]] = Field(default_factory=list, description="利益相关者")
    constraints: List[Dict[str, Any]] = Field(default_factory=list, description="约束条件")
    assumptions: List[Dict[str, Any]] = Field(default_factory=list, description="假设条件")
    dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="依赖关系")
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="风险识别")
    success_metrics: List[Dict[str, Any]] = Field(default_factory=list, description="成功指标")
    confidence_score: float = Field(0.0, description="解析置信度")


@type_subscription(topic_type=TopicTypes.REQUIREMENT_ANALYZER.value)
class RequirementAnalysisAgent(BaseAgent):
    """需求解析智能体，专门负责企业级专业的需求解析"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化需求解析智能体"""
        super().__init__(
            agent_id=AgentTypes.REQUIREMENT_ANALYZER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.REQUIREMENT_ANALYZER.value, "需求解析智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )
        
        # 需求解析配置
        self.analysis_config = {
            'enable_functional_analysis': True,
            'enable_non_functional_analysis': True,
            'enable_business_process_analysis': True,
            'enable_stakeholder_analysis': True,
            'enable_risk_analysis': True,
            'enable_dependency_analysis': True,
            'confidence_threshold': 0.7,
            'max_requirements_per_category': 50
        }
        
        logger.info(f"需求解析智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_requirement_analysis_request(
        self,
        message: RequirementAnalysisRequest,
        ctx: MessageContext
    ) -> None:
        """处理需求解析请求"""
        start_time = datetime.now()

        try:
            logger.info(f"开始处理需求解析请求: {message.session_id}")

            # 发送开始处理消息
            await self.send_response(
                f"🔍 开始企业级需求解析: {message.source_type}",
                region="process"
            )

            # 发送需求信息
            content_length = len(message.requirement_content)
            await self.send_response(
                f"📄 需求信息: 内容长度 {content_length} 字符, 来源: {message.source_type}",
                region="info"
            )

            # 执行需求解析
            await self.send_response("🔄 第1步: 开始深度需求解析...", region="progress")
            analysis_result = await self._analyze_requirement_content(message)

            # 发送解析结果统计
            await self.send_response(
                f"📊 解析结果: 功能需求 {len(analysis_result.functional_requirements)} 个, "
                f"非功能需求 {len(analysis_result.non_functional_requirements)} 个, "
                f"业务流程 {len(analysis_result.business_processes)} 个",
                region="info",
                result={
                    "functional_requirements_count": len(analysis_result.functional_requirements),
                    "non_functional_requirements_count": len(analysis_result.non_functional_requirements),
                    "business_processes_count": len(analysis_result.business_processes),
                    "stakeholders_count": len(analysis_result.stakeholders),
                    "confidence_score": analysis_result.confidence_score
                }
            )

            # 生成测试用例建议
            await self.send_response("🔄 第2步: 基于需求解析生成测试用例建议...", region="progress")
            test_cases = await self._generate_test_cases_from_analysis(
                analysis_result, message
            )

            # 发送测试用例生成结果
            await self.send_response(
                f"✅ 成功生成 {len(test_cases)} 个测试用例建议",
                region="success",
                result={"test_cases_count": len(test_cases)}
            )

            # 保存需求到数据库
            if analysis_result.functional_requirements or analysis_result.non_functional_requirements:
                await self.send_response("🔄 第3步: 保存解析的需求到数据库...", region="progress")
                await self._save_analyzed_requirements_to_database(analysis_result, message)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 构建响应
            response = RequirementAnalysisResponse(
                session_id=message.session_id,
                analysis_id=str(uuid.uuid4()),
                requirement_content=message.requirement_content,
                analysis_result=analysis_result.model_dump(),
                requirements=analysis_result.functional_requirements + analysis_result.non_functional_requirements,
                business_processes=analysis_result.business_processes,
                stakeholders=analysis_result.stakeholders,
                constraints=analysis_result.constraints,
                dependencies=analysis_result.dependencies,
                processing_time=processing_time,
                created_at=datetime.now().isoformat()
            )

            # 发送完成消息
            await self.send_response(
                f"✅ 需求解析完成! 处理时间: {processing_time:.2f}秒",
                is_final=False,
                region="success",
                result={
                    "processing_time": processing_time,
                    "total_requirements": len(response.requirements),
                    "total_business_processes": len(response.business_processes),
                    "total_stakeholders": len(response.stakeholders),
                    "confidence_score": analysis_result.confidence_score
                }
            )

            # 发送到测试点提取智能体
            await self.send_response("🔄 转发到测试点提取智能体进行专业测试点提取...", region="info")
            await self._send_to_test_point_extractor(response)

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"需求解析失败: {str(e)}")
            await self.send_response(
                f"❌ 需求解析失败: {str(e)} (处理时间: {processing_time:.2f}秒)",
                is_final=True,
                region="error",
                result={"processing_time": processing_time, "error": str(e)}
            )

    async def _analyze_requirement_content(
        self, 
        message: RequirementAnalysisRequest
    ) -> RequirementAnalysisResult:
        """分析需求内容"""
        try:
            # 创建AI分析智能体
            agent = self._create_requirement_analysis_agent()
            
            # 构建分析提示
            analysis_prompt = self._build_requirement_analysis_prompt(message)
            
            # 执行AI分析
            analysis_result = await self._run_ai_analysis(agent, analysis_prompt)
            
            # 解析AI响应
            return self._parse_ai_analysis_result(analysis_result, message)
            
        except Exception as e:
            logger.error(f"AI需求分析失败: {str(e)}")
            # 返回基础解析结果
            return RequirementAnalysisResult(
                analysis_type="basic",
                document_title="需求文档",
                executive_summary="解析失败，请检查输入内容",
                functional_requirements=[],
                non_functional_requirements=[],
                business_processes=[],
                user_stories=[],
                acceptance_criteria=[],
                stakeholders=[],
                constraints=[],
                assumptions=[],
                dependencies=[],
                risks=[],
                success_metrics=[],
                confidence_score=0.3
            )

    def _create_requirement_analysis_agent(self):
        """创建需求分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="requirement_analyzer",
            system_message=self._build_requirement_analysis_system_prompt(),
            model_client_type="deepseek"
        )

    def _build_requirement_analysis_system_prompt(self) -> str:
        """构建需求分析系统提示"""
        return """
你是资深的企业级需求分析专家，拥有丰富的软件需求工程经验，擅长从复杂的需求文档中提取和分析各类需求信息。

你的专业能力包括：
1. 深度理解业务需求和技术需求
2. 识别功能需求和非功能需求
3. 分析业务流程和用户故事
4. 识别利益相关者和约束条件
5. 评估需求依赖关系和风险
6. 制定验收标准和成功指标

请按照以下JSON格式返回企业级需求分析结果：
{
    "analysis_type": "enterprise",
    "document_title": "文档标题",
    "executive_summary": "执行摘要，概述主要需求和目标",
    "functional_requirements": [
        {
            "id": "FR-001",
            "title": "功能需求标题",
            "description": "详细描述",
            "priority": "high/medium/low",
            "complexity": "high/medium/low",
            "category": "核心功能/辅助功能/管理功能",
            "acceptance_criteria": ["验收标准1", "验收标准2"],
            "business_value": "业务价值描述"
        }
    ],
    "non_functional_requirements": [
        {
            "id": "NFR-001",
            "title": "非功能需求标题",
            "description": "详细描述",
            "type": "performance/security/usability/reliability/scalability",
            "priority": "high/medium/low",
            "measurable_criteria": "可量化标准",
            "testing_approach": "测试方法"
        }
    ],
    "business_processes": [
        {
            "id": "BP-001",
            "name": "业务流程名称",
            "description": "流程描述",
            "steps": ["步骤1", "步骤2", "步骤3"],
            "actors": ["参与者1", "参与者2"],
            "inputs": ["输入1", "输入2"],
            "outputs": ["输出1", "输出2"],
            "business_rules": ["业务规则1", "业务规则2"]
        }
    ],
    "user_stories": [
        {
            "id": "US-001",
            "title": "用户故事标题",
            "as_a": "作为某种用户",
            "i_want": "我希望",
            "so_that": "以便于",
            "acceptance_criteria": ["验收标准1", "验收标准2"],
            "priority": "high/medium/low",
            "story_points": 估算点数
        }
    ],
    "stakeholders": [
        {
            "name": "利益相关者名称",
            "role": "角色",
            "responsibilities": ["职责1", "职责2"],
            "influence": "high/medium/low",
            "interest": "high/medium/low"
        }
    ],
    "constraints": [
        {
            "type": "technical/business/legal/time/budget",
            "description": "约束描述",
            "impact": "影响程度",
            "mitigation": "缓解措施"
        }
    ],
    "dependencies": [
        {
            "type": "internal/external/technical/business",
            "description": "依赖描述",
            "impact": "影响程度",
            "risk_level": "high/medium/low"
        }
    ],
    "risks": [
        {
            "description": "风险描述",
            "probability": "high/medium/low",
            "impact": "high/medium/low",
            "mitigation": "缓解策略"
        }
    ],
    "success_metrics": [
        {
            "metric": "成功指标名称",
            "description": "指标描述",
            "target": "目标值",
            "measurement_method": "测量方法"
        }
    ],
    "confidence_score": 0.95
}

注意：
- 深入分析需求内容，准确识别各类需求信息
- 优先识别核心业务需求和关键功能点
- 为每个需求分配合适的优先级和复杂度
- 确保返回有效的JSON格式，去掉 ```json 和 ```
- 分析要全面、专业、结构化
"""

    def _build_requirement_analysis_prompt(
        self,
        message: RequirementAnalysisRequest
    ) -> str:
        """构建需求分析提示"""
        return f"""
请对以下软件需求内容进行企业级专业分析：

来源类型: {message.source_type}
项目ID: {message.project_id or "default-project-001"}
分析配置: {json.dumps(message.analysis_config or {}, ensure_ascii=False, indent=2)}

需求内容：
{message.requirement_content[:15000]}  # 限制内容长度避免token超限

请根据需求内容，进行全面的企业级需求分析，包括：
1. 功能需求识别和分类
2. 非功能需求提取和量化
3. 业务流程梳理和建模
4. 用户故事编写和优先级排序
5. 利益相关者识别和分析
6. 约束条件和依赖关系分析
7. 风险识别和缓解策略
8. 成功指标定义和测量方法

请确保分析结果专业、全面、可操作。
"""

    async def _run_ai_analysis(self, agent, prompt: str) -> str:
        """执行AI分析"""
        try:
            stream = agent.run_stream(task=prompt)
            async for event in stream:  # type: ignore
                # 流式消息，只是为了在前端界面流式显示
                if isinstance(event, ModelClientStreamingChunkEvent):
                    # 临时注释，不在前端显示流式内容
                    # await self.send_response(content=event.content, source=self.id.key)
                    continue

                # 最终的完整结果
                if isinstance(event, TaskResult):
                    messages = event.messages
                    # 从最后一条消息中获取完整内容
                    if messages and hasattr(messages[-1], 'content'):
                        return messages[-1].content

            # 如果没有获取到结果，返回默认值
            return """
                {
                    "analysis_type": "enterprise",
                    "document_title": "需求分析文档",
                    "executive_summary": "需求分析完成",
                    "functional_requirements": [],
                    "non_functional_requirements": [],
                    "business_processes": [],
                    "user_stories": [],
                    "acceptance_criteria": [],
                    "stakeholders": [],
                    "constraints": [],
                    "assumptions": [],
                    "dependencies": [],
                    "risks": [],
                    "success_metrics": [],
                    "confidence_score": 0.8
                }
                """
        except Exception as e:
            logger.error(f"AI分析执行失败: {str(e)}")
            # 返回默认结果而不是抛出异常
            return """
{
    "analysis_type": "enterprise",
    "document_title": "解析失败",
    "executive_summary": "需求分析失败，请检查输入内容",
    "functional_requirements": [],
    "non_functional_requirements": [],
    "business_processes": [],
    "user_stories": [],
    "acceptance_criteria": [],
    "stakeholders": [],
    "constraints": [],
    "assumptions": [],
    "dependencies": [],
    "risks": [],
    "success_metrics": [],
    "confidence_score": 0.5
}
"""

    def _parse_ai_analysis_result(
        self,
        ai_result: str,
        message: RequirementAnalysisRequest
    ) -> RequirementAnalysisResult:
        """解析AI分析结果"""
        try:
            # 尝试解析JSON
            result_data = json.loads(ai_result.replace("```json", "").replace("```", ""))

            return RequirementAnalysisResult(
                analysis_type=result_data.get("analysis_type", "enterprise"),
                document_title=result_data.get("document_title", "需求分析文档"),
                executive_summary=result_data.get("executive_summary", ""),
                functional_requirements=result_data.get("functional_requirements", []),
                non_functional_requirements=result_data.get("non_functional_requirements", []),
                business_processes=result_data.get("business_processes", []),
                user_stories=result_data.get("user_stories", []),
                acceptance_criteria=result_data.get("acceptance_criteria", []),
                stakeholders=result_data.get("stakeholders", []),
                constraints=result_data.get("constraints", []),
                assumptions=result_data.get("assumptions", []),
                dependencies=result_data.get("dependencies", []),
                risks=result_data.get("risks", []),
                success_metrics=result_data.get("success_metrics", []),
                confidence_score=result_data.get("confidence_score", 0.5)
            )

        except json.JSONDecodeError:
            logger.warning("AI返回结果不是有效JSON，使用默认解析")
            return RequirementAnalysisResult(
                analysis_type="basic",
                document_title="解析失败",
                executive_summary="需求分析失败，请检查输入内容",
                functional_requirements=[],
                non_functional_requirements=[],
                business_processes=[],
                user_stories=[],
                acceptance_criteria=[],
                stakeholders=[],
                constraints=[],
                assumptions=[],
                dependencies=[],
                risks=[],
                success_metrics=[],
                confidence_score=0.3
            )

    async def _generate_test_cases_from_analysis(
        self,
        analysis_result: RequirementAnalysisResult,
        message: RequirementAnalysisRequest
    ) -> List[TestCaseData]:
        """从需求分析结果生成测试用例"""
        test_cases = []

        try:
            # 基于功能需求生成测试用例
            for req in analysis_result.functional_requirements:
                test_case = TestCaseData(
                    title=f"测试功能需求: {req.get('title', '未命名功能需求')}",
                    description=req.get("description", ""),
                    test_type=TestType.FUNCTIONAL,
                    test_level=TestLevel.SYSTEM,
                    priority=self._map_priority(req.get("priority", "medium")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "requirement_id": req.get("id"),
                        "requirement_type": "functional",
                        "business_value": req.get("business_value"),
                        "complexity": req.get("complexity")
                    },
                    ai_confidence=analysis_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于非功能需求生成测试用例
            for req in analysis_result.non_functional_requirements:
                test_type = self._map_non_functional_test_type(req.get("type", "performance"))
                test_case = TestCaseData(
                    title=f"测试非功能需求: {req.get('title', '未命名非功能需求')}",
                    description=req.get("description", ""),
                    test_type=test_type,
                    test_level=TestLevel.SYSTEM,
                    priority=self._map_priority(req.get("priority", "medium")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "requirement_id": req.get("id"),
                        "requirement_type": "non_functional",
                        "nfr_type": req.get("type"),
                        "measurable_criteria": req.get("measurable_criteria"),
                        "testing_approach": req.get("testing_approach")
                    },
                    ai_confidence=analysis_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于业务流程生成测试用例
            for process in analysis_result.business_processes:
                test_case = TestCaseData(
                    title=f"测试业务流程: {process.get('name', '未命名业务流程')}",
                    description=f"验证业务流程: {process.get('description', '')}",
                    test_type=TestType.FUNCTIONAL,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P1,  # 业务流程通常是高优先级
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "process_id": process.get("id"),
                        "process_steps": process.get("steps", []),
                        "process_actors": process.get("actors", []),
                        "business_rules": process.get("business_rules", [])
                    },
                    ai_confidence=analysis_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于用户故事生成测试用例
            for story in analysis_result.user_stories:
                test_case = TestCaseData(
                    title=f"测试用户故事: {story.get('title', '未命名用户故事')}",
                    description=f"作为{story.get('as_a', '用户')}，我希望{story.get('i_want', '')}，以便于{story.get('so_that', '')}",
                    test_type=TestType.FUNCTIONAL,
                    test_level=TestLevel.ACCEPTANCE,
                    priority=self._map_priority(story.get("priority", "medium")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "story_id": story.get("id"),
                        "story_points": story.get("story_points"),
                        "acceptance_criteria": story.get("acceptance_criteria", [])
                    },
                    ai_confidence=analysis_result.confidence_score
                )
                test_cases.append(test_case)

            logger.info(f"从需求分析生成了 {len(test_cases)} 个测试用例")
            return test_cases

        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            return []

    def _map_non_functional_test_type(self, nfr_type: str) -> TestType:
        """映射非功能需求类型到测试类型"""
        mapping = {
            "performance": TestType.PERFORMANCE,
            "security": TestType.SECURITY,
            "usability": TestType.USABILITY,
            "reliability": TestType.FUNCTIONAL,
            "scalability": TestType.PERFORMANCE,
            "compatibility": TestType.COMPATIBILITY,
            "maintainability": TestType.FUNCTIONAL
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

    async def _send_to_test_point_extractor(
        self,
        response: RequirementAnalysisResponse
    ):
        """发送到测试点提取智能体"""
        try:
            extraction_request = TestPointExtractionRequest(
                session_id=response.session_id,
                requirement_analysis_result=response.analysis_result,
                extraction_config={
                    "enable_functional_extraction": True,
                    "enable_non_functional_extraction": True,
                    "enable_integration_extraction": True,
                    "enable_boundary_extraction": True,
                    "enable_exception_extraction": True,
                    "enable_security_extraction": True,
                    "enable_performance_extraction": True,
                    "enable_risk_based_extraction": True,
                    "confidence_threshold": 0.75
                },
                test_strategy="comprehensive",
                project_id="default-project-001"  # 可以从原始请求中获取
            )

            await self.publish_message(
                extraction_request,
                topic_id=TopicId(type=TopicTypes.TEST_POINT_EXTRACTOR.value, source=self.id.key)
            )

            logger.info(f"已发送到测试点提取智能体: {response.session_id}")

        except Exception as e:
            logger.error(f"发送到测试点提取智能体失败: {str(e)}")



    async def _save_analyzed_requirements_to_database(
        self,
        analysis_result: RequirementAnalysisResult,
        message: RequirementAnalysisRequest
    ) -> None:
        """保存分析的需求到数据库"""
        try:
            # 合并功能需求和非功能需求
            all_requirements = []

            # 添加功能需求
            for req in analysis_result.functional_requirements:
                req_data = {
                    "id": req.get("id", f"FR-{uuid.uuid4().hex[:8].upper()}"),
                    "title": req.get("title", "未命名功能需求"),
                    "description": req.get("description", ""),
                    "type": "functional",
                    "priority": req.get("priority", "medium"),
                    "category": req.get("category", "核心功能"),
                    "complexity": req.get("complexity", "medium"),
                    "business_value": req.get("business_value", ""),
                    "acceptance_criteria": req.get("acceptance_criteria", []),
                    "confidence": analysis_result.confidence_score
                }
                all_requirements.append(req_data)

            # 添加非功能需求
            for req in analysis_result.non_functional_requirements:
                req_data = {
                    "id": req.get("id", f"NFR-{uuid.uuid4().hex[:8].upper()}"),
                    "title": req.get("title", "未命名非功能需求"),
                    "description": req.get("description", ""),
                    "type": "non_functional",
                    "priority": req.get("priority", "medium"),
                    "nfr_type": req.get("type", "performance"),
                    "measurable_criteria": req.get("measurable_criteria", ""),
                    "testing_approach": req.get("testing_approach", ""),
                    "confidence": analysis_result.confidence_score
                }
                all_requirements.append(req_data)

            await self.send_response(
                f"💾 开始保存 {len(all_requirements)} 个分析的需求到数据库...",
                region="process"
            )

            # 构建需求保存请求
            requirement_save_request = RequirementSaveRequest(
                session_id=message.session_id,
                document_id=str(uuid.uuid4()),
                file_name="需求分析结果",
                file_path="requirement_analysis",
                requirements=all_requirements,
                project_id=message.project_id,
                ai_model_info={
                    "model": "deepseek-chat",
                    "generation_time": datetime.now().isoformat(),
                    "agent_version": "1.0",
                    "agent_type": "requirement_analyzer",
                    "session_id": message.session_id,
                    "confidence_score": analysis_result.confidence_score,
                    "analysis_type": analysis_result.analysis_type
                }
            )

            # 发送到需求存储智能体
            await self.publish_message(
                requirement_save_request,
                topic_id=TopicId(type=TopicTypes.REQUIREMENT_SAVER.value, source=self.id.key)
            )

            logger.info(f"已发送需求保存请求到需求存储智能体: {message.session_id}")

        except Exception as e:
            logger.error(f"保存分析的需求到数据库失败: {str(e)}")
            await self.send_response(
                f"⚠️ 需求保存失败: {str(e)}",
                region="warning"
            )
