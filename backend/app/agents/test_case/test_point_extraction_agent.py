"""
测试点提取智能体
专门负责从需求解析结果中提取专业的测试点，进行企业级测试覆盖度分析
基于AutoGen Core架构实现，参考requirement_analysis_agent.py的优秀设计模式
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
    TestPointExtractionRequest, TestPointExtractionResponse,
    TestCaseData
)
from app.core.enums import TestType, TestLevel, Priority, InputSource


class TestPointExtractionResult(BaseModel):
    """测试点提取结果"""
    extraction_strategy: str = Field(..., description="提取策略")
    coverage_analysis: Dict[str, Any] = Field(default_factory=dict, description="覆盖度分析")
    functional_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="功能测试点")
    non_functional_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="非功能测试点")
    integration_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="集成测试点")
    acceptance_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="验收测试点")
    boundary_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="边界测试点")
    exception_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="异常测试点")
    security_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="安全测试点")
    performance_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="性能测试点")
    usability_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="可用性测试点")
    compatibility_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="兼容性测试点")
    test_data_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="测试数据需求")
    test_environment_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="测试环境需求")
    test_dependency_matrix: List[Dict[str, Any]] = Field(default_factory=list, description="测试依赖矩阵")
    test_priority_matrix: List[Dict[str, Any]] = Field(default_factory=list, description="测试优先级矩阵")
    risk_based_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="基于风险的测试点")
    regression_test_points: List[Dict[str, Any]] = Field(default_factory=list, description="回归测试点")
    automation_feasibility: Dict[str, Any] = Field(default_factory=dict, description="自动化可行性分析")
    test_execution_sequence: List[Dict[str, Any]] = Field(default_factory=list, description="测试执行序列")
    confidence_score: float = Field(0.0, description="提取置信度")


@type_subscription(topic_type=TopicTypes.TEST_POINT_EXTRACTOR.value)
class TestPointExtractionAgent(BaseAgent):
    """测试点提取智能体，专门负责企业级专业的测试点提取和分析"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化测试点提取智能体"""
        super().__init__(
            agent_id=AgentTypes.TEST_POINT_EXTRACTOR.value,
            agent_name=AGENT_NAMES.get(AgentTypes.TEST_POINT_EXTRACTOR.value, "测试点提取智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )
        
        # 测试点提取配置
        self.extraction_config = {
            'enable_functional_extraction': True,
            'enable_non_functional_extraction': True,
            'enable_integration_extraction': True,
            'enable_boundary_extraction': True,
            'enable_exception_extraction': True,
            'enable_security_extraction': True,
            'enable_performance_extraction': True,
            'enable_usability_extraction': True,
            'enable_compatibility_extraction': True,
            'enable_risk_based_extraction': True,
            'enable_automation_analysis': True,
            'confidence_threshold': 0.75,
            'max_test_points_per_category': 100,
            'priority_levels': ['P0', 'P1', 'P2', 'P3', 'P4'],
            'test_techniques': [
                'equivalence_partitioning',
                'boundary_value_analysis',
                'decision_table_testing',
                'state_transition_testing',
                'use_case_testing',
                'exploratory_testing'
            ]
        }
        
        logger.info(f"测试点提取智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_test_point_extraction_request(
        self,
        message: TestPointExtractionRequest,
        ctx: MessageContext
    ) -> None:
        """处理测试点提取请求"""
        start_time = datetime.now()

        try:
            logger.info(f"开始处理测试点提取请求: {message.session_id}")

            # 发送开始处理消息
            await self.send_response(
                f"🎯 开始企业级测试点提取: 基于需求解析结果",
                region="process"
            )

            # 分析需求解析结果
            analysis_result = message.requirement_analysis_result
            requirements_count = len(analysis_result.get('requirements', []))
            business_processes_count = len(analysis_result.get('business_processes', []))
            
            await self.send_response(
                f"📊 需求分析输入: {requirements_count} 个需求, {business_processes_count} 个业务流程",
                region="info"
            )

            # 执行测试点提取
            await self.send_response("🔄 第1步: 开始专业测试点提取分析...", region="progress")
            extraction_result = await self._extract_test_points(message)

            # 发送提取结果统计
            total_test_points = (
                len(extraction_result.functional_test_points) +
                len(extraction_result.non_functional_test_points) +
                len(extraction_result.integration_test_points) +
                len(extraction_result.acceptance_test_points) +
                len(extraction_result.boundary_test_points) +
                len(extraction_result.exception_test_points)
            )

            await self.send_response(
                f"📈 测试点提取完成: 功能测试点 {len(extraction_result.functional_test_points)} 个, "
                f"非功能测试点 {len(extraction_result.non_functional_test_points)} 个, "
                f"集成测试点 {len(extraction_result.integration_test_points)} 个, "
                f"总计 {total_test_points} 个测试点",
                region="info",
                result={
                    "functional_test_points_count": len(extraction_result.functional_test_points),
                    "non_functional_test_points_count": len(extraction_result.non_functional_test_points),
                    "integration_test_points_count": len(extraction_result.integration_test_points),
                    "acceptance_test_points_count": len(extraction_result.acceptance_test_points),
                    "boundary_test_points_count": len(extraction_result.boundary_test_points),
                    "exception_test_points_count": len(extraction_result.exception_test_points),
                    "total_test_points": total_test_points,
                    "confidence_score": extraction_result.confidence_score
                }
            )

            # 生成测试用例
            await self.send_response("🔄 第2步: 基于测试点生成测试用例...", region="progress")
            test_cases = await self._generate_test_cases_from_test_points(
                extraction_result, message
            )

            # 发送测试用例生成结果
            await self.send_response(
                f"✅ 成功生成 {len(test_cases)} 个测试用例",
                region="success",
                result={"test_cases_count": len(test_cases)}
            )

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 构建响应
            response = TestPointExtractionResponse(
                session_id=message.session_id,
                extraction_id=str(uuid.uuid4()),
                requirement_analysis_result=message.requirement_analysis_result,
                extraction_result=extraction_result.model_dump(),
                functional_test_points=extraction_result.functional_test_points,
                non_functional_test_points=extraction_result.non_functional_test_points,
                integration_test_points=extraction_result.integration_test_points,
                acceptance_test_points=extraction_result.acceptance_test_points,
                boundary_test_points=extraction_result.boundary_test_points,
                exception_test_points=extraction_result.exception_test_points,
                test_coverage_analysis=extraction_result.coverage_analysis,
                test_priority_matrix=extraction_result.test_priority_matrix,
                processing_time=processing_time,
                created_at=datetime.now().isoformat()
            )

            # 发送完成消息
            await self.send_response(
                f"✅ 测试点提取完成! 处理时间: {processing_time:.2f}秒",
                is_final=False,
                region="success",
                result={
                    "processing_time": processing_time,
                    "total_test_points": total_test_points,
                    "coverage_score": extraction_result.coverage_analysis.get("overall_coverage", 0.0),
                    "confidence_score": extraction_result.confidence_score
                }
            )

            # 发送到测试用例生成智能体
            await self.send_response("🔄 转发到测试用例生成智能体进行用例生成...", region="info")
            await self._send_to_test_case_generator(response, test_cases)

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"测试点提取失败: {str(e)}")
            await self.send_response(
                f"❌ 测试点提取失败: {str(e)} (处理时间: {processing_time:.2f}秒)",
                is_final=True,
                region="error",
                result={"processing_time": processing_time, "error": str(e)}
            )

    async def _extract_test_points(
        self,
        message: TestPointExtractionRequest
    ) -> TestPointExtractionResult:
        """提取测试点"""
        try:
            # 创建AI分析智能体
            agent = self._create_test_point_extraction_agent()

            # 构建提取提示
            extraction_prompt = self._build_test_point_extraction_prompt(message)

            # 执行AI分析
            extraction_result = await self._run_ai_extraction(agent, extraction_prompt)

            # 解析AI响应
            return self._parse_ai_extraction_result(extraction_result, message)

        except Exception as e:
            logger.error(f"AI测试点提取失败: {str(e)}")
            # 返回基础提取结果
            return TestPointExtractionResult(
                extraction_strategy="basic",
                coverage_analysis={"overall_coverage": 0.5, "analysis_status": "failed"},
                functional_test_points=[],
                non_functional_test_points=[],
                integration_test_points=[],
                acceptance_test_points=[],
                boundary_test_points=[],
                exception_test_points=[],
                security_test_points=[],
                performance_test_points=[],
                usability_test_points=[],
                compatibility_test_points=[],
                test_data_requirements=[],
                test_environment_requirements=[],
                test_dependency_matrix=[],
                test_priority_matrix=[],
                risk_based_test_points=[],
                regression_test_points=[],
                automation_feasibility={"automation_score": 0.3, "analysis_status": "failed"},
                test_execution_sequence=[],
                confidence_score=0.3
            )

    def _create_test_point_extraction_agent(self):
        """创建测试点提取智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="test_point_extractor",
            system_message=self._build_test_point_extraction_system_prompt(),
            model_client_type="deepseek"
        )

    def _build_test_point_extraction_system_prompt(self) -> str:
        """构建测试点提取系统提示"""
        return """
你是资深的企业级测试工程专家，拥有丰富的测试设计和测试策略制定经验，擅长从需求分析结果中提取专业的测试点。

你的专业能力包括：
1. 测试覆盖度分析和测试点识别
2. 测试技术应用（等价类划分、边界值分析、决策表测试等）
3. 测试优先级评估和风险分析
4. 测试自动化可行性分析
5. 测试数据和环境需求分析
6. 测试执行策略制定

请按照以下JSON格式返回企业级测试点提取结果：
{
    "extraction_strategy": "comprehensive",
    "coverage_analysis": {
        "overall_coverage": 0.95,
        "functional_coverage": 0.98,
        "non_functional_coverage": 0.90,
        "integration_coverage": 0.85,
        "boundary_coverage": 0.92,
        "exception_coverage": 0.88,
        "coverage_gaps": ["特定边界条件", "并发场景"],
        "coverage_recommendations": ["增加压力测试", "完善异常处理测试"]
    },
    "functional_test_points": [
        {
            "id": "FTP-001",
            "name": "用户登录功能测试",
            "description": "验证用户登录功能的正确性",
            "category": "核心功能",
            "priority": "P0",
            "test_technique": "equivalence_partitioning",
            "preconditions": ["用户账户存在", "系统正常运行"],
            "test_scenarios": [
                "有效用户名和密码登录",
                "无效用户名登录",
                "无效密码登录"
            ],
            "expected_results": ["登录成功", "显示错误信息"],
            "test_data_requirements": ["有效用户账户", "无效用户数据"],
            "automation_feasibility": "high",
            "risk_level": "high",
            "business_impact": "critical",
            "related_requirements": ["REQ-001", "REQ-002"]
        }
    ],
    "non_functional_test_points": [
        {
            "id": "NFTP-001",
            "name": "登录响应时间测试",
            "description": "验证登录响应时间不超过2秒",
            "category": "性能测试",
            "type": "performance",
            "priority": "P1",
            "test_technique": "load_testing",
            "performance_criteria": "响应时间 < 2秒",
            "load_conditions": "并发用户数: 1000",
            "test_environment": "生产环境模拟",
            "monitoring_metrics": ["响应时间", "吞吐量", "错误率"],
            "automation_feasibility": "high",
            "related_requirements": ["NFR-001"]
        }
    ],
    "integration_test_points": [
        {
            "id": "ITP-001",
            "name": "用户服务与认证服务集成测试",
            "description": "验证用户服务与认证服务的集成",
            "category": "服务集成",
            "priority": "P1",
            "integration_type": "service_to_service",
            "components": ["用户服务", "认证服务"],
            "integration_scenarios": ["正常认证流程", "认证失败处理"],
            "data_flow": "用户请求 -> 用户服务 -> 认证服务 -> 返回结果",
            "test_environment": "集成测试环境",
            "automation_feasibility": "medium"
        }
    ],
    "acceptance_test_points": [
        {
            "id": "ATP-001",
            "name": "用户注册验收测试",
            "description": "验证用户注册功能满足业务需求",
            "category": "业务验收",
            "priority": "P0",
            "user_story": "作为新用户，我希望能够注册账户，以便使用系统功能",
            "acceptance_criteria": [
                "用户可以通过邮箱注册",
                "注册后自动发送验证邮件",
                "验证后账户激活"
            ],
            "business_scenarios": ["正常注册流程", "重复邮箱注册"],
            "stakeholders": ["最终用户", "产品经理"],
            "automation_feasibility": "medium"
        }
    ],
    "boundary_test_points": [
        {
            "id": "BTP-001",
            "name": "密码长度边界测试",
            "description": "测试密码长度的边界条件",
            "category": "边界值测试",
            "priority": "P2",
            "test_technique": "boundary_value_analysis",
            "boundary_conditions": [
                "最小长度: 8位",
                "最大长度: 128位",
                "边界值: 7位, 8位, 9位, 127位, 128位, 129位"
            ],
            "test_values": ["7位密码", "8位密码", "128位密码", "129位密码"],
            "expected_behaviors": ["拒绝", "接受", "接受", "拒绝"],
            "automation_feasibility": "high"
        }
    ],
    "exception_test_points": [
        {
            "id": "ETP-001",
            "name": "网络异常处理测试",
            "description": "测试网络异常情况下的系统行为",
            "category": "异常处理",
            "priority": "P2",
            "exception_types": ["网络超时", "连接中断", "服务不可用"],
            "test_scenarios": [
                "登录时网络超时",
                "数据传输中连接中断",
                "依赖服务不可用"
            ],
            "expected_behaviors": [
                "显示超时错误信息",
                "数据回滚",
                "降级处理"
            ],
            "recovery_mechanisms": ["重试机制", "缓存机制", "备用服务"],
            "automation_feasibility": "medium"
        }
    ],
    "security_test_points": [
        {
            "id": "STP-001",
            "name": "SQL注入防护测试",
            "description": "测试系统对SQL注入攻击的防护能力",
            "category": "安全测试",
            "priority": "P1",
            "security_type": "injection_attack",
            "attack_vectors": [
                "登录表单SQL注入",
                "搜索框SQL注入",
                "URL参数SQL注入"
            ],
            "test_payloads": ["' OR '1'='1", "'; DROP TABLE users; --"],
            "expected_behaviors": ["输入被过滤", "显示错误信息", "记录安全日志"],
            "security_controls": ["输入验证", "参数化查询", "WAF防护"],
            "automation_feasibility": "high"
        }
    ],
    "performance_test_points": [
        {
            "id": "PTP-001",
            "name": "系统并发性能测试",
            "description": "测试系统在高并发下的性能表现",
            "category": "性能测试",
            "priority": "P1",
            "performance_type": "load_test",
            "load_scenarios": [
                "正常负载: 1000并发用户",
                "峰值负载: 5000并发用户",
                "压力测试: 10000并发用户"
            ],
            "performance_metrics": [
                "响应时间 < 2秒",
                "吞吐量 > 1000 TPS",
                "错误率 < 0.1%"
            ],
            "test_duration": "30分钟",
            "monitoring_tools": ["JMeter", "Grafana", "Prometheus"],
            "automation_feasibility": "high"
        }
    ],
    "usability_test_points": [
        {
            "id": "UTP-001",
            "name": "用户界面易用性测试",
            "description": "测试用户界面的易用性和用户体验",
            "category": "可用性测试",
            "priority": "P2",
            "usability_aspects": [
                "界面直观性",
                "操作便捷性",
                "错误提示清晰性"
            ],
            "test_scenarios": [
                "新用户首次使用",
                "常用功能操作",
                "错误恢复操作"
            ],
            "success_criteria": [
                "任务完成率 > 90%",
                "用户满意度 > 4.0/5.0",
                "错误恢复时间 < 30秒"
            ],
            "test_methods": ["用户测试", "专家评审", "A/B测试"],
            "automation_feasibility": "low"
        }
    ],
    "compatibility_test_points": [
        {
            "id": "CTP-001",
            "name": "浏览器兼容性测试",
            "description": "测试系统在不同浏览器上的兼容性",
            "category": "兼容性测试",
            "priority": "P2",
            "compatibility_matrix": [
                "Chrome 最新版本",
                "Firefox 最新版本",
                "Safari 最新版本",
                "Edge 最新版本"
            ],
            "test_scenarios": [
                "基本功能操作",
                "界面显示效果",
                "JavaScript功能"
            ],
            "expected_results": "所有浏览器功能一致",
            "automation_feasibility": "high"
        }
    ],
    "test_data_requirements": [
        {
            "category": "用户数据",
            "description": "测试用户账户数据",
            "data_types": ["有效用户", "无效用户", "特殊字符用户"],
            "data_volume": "1000条记录",
            "data_sources": ["测试数据库", "数据生成工具"],
            "data_privacy": "脱敏处理"
        }
    ],
    "test_environment_requirements": [
        {
            "environment_type": "集成测试环境",
            "description": "用于集成测试的环境配置",
            "infrastructure": ["应用服务器", "数据库服务器", "缓存服务器"],
            "configuration": "与生产环境一致",
            "data_setup": "测试数据初始化",
            "monitoring": "性能监控工具"
        }
    ],
    "test_dependency_matrix": [
        {
            "test_point_id": "FTP-001",
            "dependencies": ["用户数据准备", "认证服务可用"],
            "dependency_type": "data_dependency",
            "impact_level": "high"
        }
    ],
    "test_priority_matrix": [
        {
            "priority": "P0",
            "description": "关键业务功能",
            "test_points": ["FTP-001", "ATP-001"],
            "execution_order": 1,
            "risk_level": "high"
        }
    ],
    "risk_based_test_points": [
        {
            "risk_id": "RISK-001",
            "risk_description": "用户数据泄露风险",
            "risk_level": "high",
            "mitigation_test_points": ["STP-001", "STP-002"],
            "test_approach": "安全测试优先"
        }
    ],
    "regression_test_points": [
        {
            "id": "RTP-001",
            "name": "核心功能回归测试",
            "description": "验证核心功能在变更后仍正常工作",
            "scope": "核心业务流程",
            "trigger_conditions": ["代码变更", "配置变更"],
            "test_points": ["FTP-001", "FTP-002", "FTP-003"],
            "automation_level": "full"
        }
    ],
    "automation_feasibility": {
        "overall_automation_score": 0.85,
        "high_automation": ["功能测试", "性能测试", "安全测试"],
        "medium_automation": ["集成测试", "兼容性测试"],
        "low_automation": ["可用性测试", "探索性测试"],
        "automation_tools": ["Selenium", "JMeter", "Postman"],
        "automation_strategy": "优先自动化高频、高风险测试点"
    },
    "test_execution_sequence": [
        {
            "phase": "单元测试阶段",
            "order": 1,
            "test_types": ["功能测试", "边界测试"],
            "parallel_execution": true
        },
        {
            "phase": "集成测试阶段",
            "order": 2,
            "test_types": ["集成测试", "接口测试"],
            "dependencies": ["单元测试通过"]
        }
    ],
    "confidence_score": 0.92
}

注意：
- 深入分析需求解析结果，识别所有可测试点
- 应用专业测试技术和方法
- 考虑测试的可执行性和自动化可行性
- 确保测试覆盖度和质量
- 返回有效的JSON格式，去掉 ```json 和 ```
- 分析要专业、全面、可操作
"""

    def _build_test_point_extraction_prompt(
        self,
        message: TestPointExtractionRequest
    ) -> str:
        """构建测试点提取提示"""
        analysis_result = message.requirement_analysis_result

        return f"""
请基于以下需求解析结果，进行企业级专业的测试点提取和分析：

项目ID: {message.project_id or "未指定"}
测试策略: {message.test_strategy or "综合测试策略"}
提取配置: {json.dumps(message.extraction_config or {}, ensure_ascii=False, indent=2)}

需求解析结果：
{json.dumps(analysis_result, ensure_ascii=False, indent=2)[:20000]}  # 限制内容长度避免token超限

请根据需求解析结果，进行全面的企业级测试点提取，包括：

1. **功能测试点提取**：
   - 基于功能需求识别测试点
   - 应用等价类划分和边界值分析
   - 考虑正常流程和异常流程

2. **非功能测试点提取**：
   - 性能测试点（响应时间、吞吐量、并发）
   - 安全测试点（认证、授权、数据保护）
   - 可用性测试点（易用性、可访问性）
   - 兼容性测试点（浏览器、操作系统、设备）

3. **集成测试点提取**：
   - 系统间接口测试
   - 数据流测试
   - 服务依赖测试

4. **验收测试点提取**：
   - 基于用户故事的验收测试
   - 业务场景测试
   - 端到端流程测试

5. **专项测试点提取**：
   - 边界条件测试
   - 异常处理测试
   - 压力测试和稳定性测试

6. **测试覆盖度分析**：
   - 需求覆盖度评估
   - 测试技术应用分析
   - 覆盖度缺口识别

7. **测试优先级和风险分析**：
   - 基于业务影响的优先级排序
   - 风险评估和缓解测试
   - 回归测试点识别

8. **自动化可行性分析**：
   - 自动化测试点识别
   - 自动化工具推荐
   - 自动化策略制定

请确保提取结果专业、全面、可执行，并提供详细的测试覆盖度分析。
"""

    async def _run_ai_extraction(self, agent, prompt: str) -> str:
        """执行AI提取"""
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
                    "extraction_strategy": "comprehensive",
                    "coverage_analysis": {
                        "overall_coverage": 0.8,
                        "functional_coverage": 0.85,
                        "coverage_gaps": [],
                        "coverage_recommendations": []
                    },
                    "functional_test_points": [],
                    "non_functional_test_points": [],
                    "integration_test_points": [],
                    "acceptance_test_points": [],
                    "boundary_test_points": [],
                    "exception_test_points": [],
                    "security_test_points": [],
                    "performance_test_points": [],
                    "usability_test_points": [],
                    "compatibility_test_points": [],
                    "test_data_requirements": [],
                    "test_environment_requirements": [],
                    "test_dependency_matrix": [],
                    "test_priority_matrix": [],
                    "risk_based_test_points": [],
                    "regression_test_points": [],
                    "automation_feasibility": {
                        "overall_automation_score": 0.8,
                        "automation_strategy": "优先自动化核心功能"
                    },
                    "test_execution_sequence": [],
                    "confidence_score": 0.8
                }
                """
        except Exception as e:
            logger.error(f"AI提取执行失败: {str(e)}")
            # 返回默认结果而不是抛出异常
            return """
{
    "extraction_strategy": "basic",
    "coverage_analysis": {
        "overall_coverage": 0.5,
        "analysis_status": "failed"
    },
    "functional_test_points": [],
    "non_functional_test_points": [],
    "integration_test_points": [],
    "acceptance_test_points": [],
    "boundary_test_points": [],
    "exception_test_points": [],
    "security_test_points": [],
    "performance_test_points": [],
    "usability_test_points": [],
    "compatibility_test_points": [],
    "test_data_requirements": [],
    "test_environment_requirements": [],
    "test_dependency_matrix": [],
    "test_priority_matrix": [],
    "risk_based_test_points": [],
    "regression_test_points": [],
    "automation_feasibility": {
        "overall_automation_score": 0.5,
        "analysis_status": "failed"
    },
    "test_execution_sequence": [],
    "confidence_score": 0.5
}
"""

    def _parse_ai_extraction_result(
        self,
        ai_result: str,
        message: TestPointExtractionRequest
    ) -> TestPointExtractionResult:
        """解析AI提取结果"""
        try:
            # 尝试解析JSON
            result_data = json.loads(ai_result.replace("```json", "").replace("```", ""))

            return TestPointExtractionResult(
                extraction_strategy=result_data.get("extraction_strategy", "comprehensive"),
                coverage_analysis=result_data.get("coverage_analysis", {}),
                functional_test_points=result_data.get("functional_test_points", []),
                non_functional_test_points=result_data.get("non_functional_test_points", []),
                integration_test_points=result_data.get("integration_test_points", []),
                acceptance_test_points=result_data.get("acceptance_test_points", []),
                boundary_test_points=result_data.get("boundary_test_points", []),
                exception_test_points=result_data.get("exception_test_points", []),
                security_test_points=result_data.get("security_test_points", []),
                performance_test_points=result_data.get("performance_test_points", []),
                usability_test_points=result_data.get("usability_test_points", []),
                compatibility_test_points=result_data.get("compatibility_test_points", []),
                test_data_requirements=result_data.get("test_data_requirements", []),
                test_environment_requirements=result_data.get("test_environment_requirements", []),
                test_dependency_matrix=result_data.get("test_dependency_matrix", []),
                test_priority_matrix=result_data.get("test_priority_matrix", []),
                risk_based_test_points=result_data.get("risk_based_test_points", []),
                regression_test_points=result_data.get("regression_test_points", []),
                automation_feasibility=result_data.get("automation_feasibility", {}),
                test_execution_sequence=result_data.get("test_execution_sequence", []),
                confidence_score=result_data.get("confidence_score", 0.5)
            )

        except json.JSONDecodeError:
            logger.warning("AI返回结果不是有效JSON，使用默认解析")
            return TestPointExtractionResult(
                extraction_strategy="basic",
                coverage_analysis={"overall_coverage": 0.3, "analysis_status": "json_parse_failed"},
                functional_test_points=[],
                non_functional_test_points=[],
                integration_test_points=[],
                acceptance_test_points=[],
                boundary_test_points=[],
                exception_test_points=[],
                security_test_points=[],
                performance_test_points=[],
                usability_test_points=[],
                compatibility_test_points=[],
                test_data_requirements=[],
                test_environment_requirements=[],
                test_dependency_matrix=[],
                test_priority_matrix=[],
                risk_based_test_points=[],
                regression_test_points=[],
                automation_feasibility={"overall_automation_score": 0.3, "analysis_status": "failed"},
                test_execution_sequence=[],
                confidence_score=0.3
            )

    async def _generate_test_cases_from_test_points(
        self,
        extraction_result: TestPointExtractionResult,
        message: TestPointExtractionRequest
    ) -> List[TestCaseData]:
        """从测试点生成测试用例"""
        test_cases = []

        try:
            # 基于功能测试点生成测试用例
            for test_point in extraction_result.functional_test_points:
                test_case = TestCaseData(
                    title=f"功能测试: {test_point.get('name', '未命名功能测试点')}",
                    description=test_point.get("description", ""),
                    test_type=TestType.FUNCTIONAL,
                    test_level=TestLevel.SYSTEM,
                    priority=self._map_priority(test_point.get("priority", "P2")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "test_point_id": test_point.get("id"),
                        "test_point_type": "functional",
                        "test_technique": test_point.get("test_technique"),
                        "category": test_point.get("category"),
                        "automation_feasibility": test_point.get("automation_feasibility"),
                        "risk_level": test_point.get("risk_level"),
                        "business_impact": test_point.get("business_impact"),
                        "related_requirements": test_point.get("related_requirements", [])
                    },
                    ai_confidence=extraction_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于非功能测试点生成测试用例
            for test_point in extraction_result.non_functional_test_points:
                test_type = self._map_non_functional_test_type(test_point.get("type", "performance"))
                test_case = TestCaseData(
                    title=f"非功能测试: {test_point.get('name', '未命名非功能测试点')}",
                    description=test_point.get("description", ""),
                    test_type=test_type,
                    test_level=TestLevel.SYSTEM,
                    priority=self._map_priority(test_point.get("priority", "P2")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "test_point_id": test_point.get("id"),
                        "test_point_type": "non_functional",
                        "nfr_type": test_point.get("type"),
                        "performance_criteria": test_point.get("performance_criteria"),
                        "load_conditions": test_point.get("load_conditions"),
                        "monitoring_metrics": test_point.get("monitoring_metrics", []),
                        "automation_feasibility": test_point.get("automation_feasibility")
                    },
                    ai_confidence=extraction_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于集成测试点生成测试用例
            for test_point in extraction_result.integration_test_points:
                test_case = TestCaseData(
                    title=f"集成测试: {test_point.get('name', '未命名集成测试点')}",
                    description=test_point.get("description", ""),
                    test_type=TestType.INTERFACE,
                    test_level=TestLevel.INTEGRATION,
                    priority=self._map_priority(test_point.get("priority", "P1")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "test_point_id": test_point.get("id"),
                        "test_point_type": "integration",
                        "integration_type": test_point.get("integration_type"),
                        "components": test_point.get("components", []),
                        "data_flow": test_point.get("data_flow"),
                        "automation_feasibility": test_point.get("automation_feasibility")
                    },
                    ai_confidence=extraction_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于验收测试点生成测试用例
            for test_point in extraction_result.acceptance_test_points:
                test_case = TestCaseData(
                    title=f"验收测试: {test_point.get('name', '未命名验收测试点')}",
                    description=test_point.get("description", ""),
                    test_type=TestType.FUNCTIONAL,
                    test_level=TestLevel.ACCEPTANCE,
                    priority=self._map_priority(test_point.get("priority", "P0")),
                    input_source=InputSource.MANUAL,
                    source_metadata={
                        "test_point_id": test_point.get("id"),
                        "test_point_type": "acceptance",
                        "user_story": test_point.get("user_story"),
                        "acceptance_criteria": test_point.get("acceptance_criteria", []),
                        "business_scenarios": test_point.get("business_scenarios", []),
                        "stakeholders": test_point.get("stakeholders", [])
                    },
                    ai_confidence=extraction_result.confidence_score
                )
                test_cases.append(test_case)

            logger.info(f"从测试点生成了 {len(test_cases)} 个测试用例")
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

    async def _send_to_test_case_generator(
        self,
        response: TestPointExtractionResponse,
        test_cases: List[TestCaseData]
    ):
        """发送到测试用例生成智能体"""
        try:
            # 直接发送 TestPointExtractionResponse，而不是 TestCaseGenerationRequest
            await self.publish_message(
                response,
                topic_id=TopicId(type=TopicTypes.TEST_CASE_GENERATOR.value, source=self.id.key)
            )

            logger.info(f"已发送测试点提取响应到测试用例生成智能体: {response.session_id}")

        except Exception as e:
            logger.error(f"发送到测试用例生成智能体失败: {str(e)}")
