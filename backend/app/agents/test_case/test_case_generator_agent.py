"""
测试用例生成智能体 - 全面优化版本
专注于测试用例的生成逻辑，通过消息机制与其他智能体协作
遵循单一职责原则，参考 examples/agents/factory.py 和 examples/base.py 的设计模式
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
    TestCaseGenerationRequest, TestCaseGenerationResponse,
    TestCaseData, MindMapGenerationRequest
)
from app.core.enums import (
    TestType, TestLevel, Priority, TestCaseStatus, InputSource
)
from app.agents.database.test_case_saver_agent import TestCaseSaveRequest, TestCaseSaveResponse


class TestCaseGenerationResult(BaseModel):
    """测试用例生成结果"""
    generated_count: int = Field(0, description="生成的测试用例数量")
    generated_test_cases: List[TestCaseData] = Field(default_factory=list, description="生成的测试用例数据")
    processing_time: float = Field(0.0, description="处理时间")
    errors: List[str] = Field(default_factory=list, description="错误信息")


@type_subscription(topic_type=TopicTypes.TEST_CASE_GENERATOR.value)
class TestCaseGeneratorAgent(BaseAgent):
    """
    测试用例生成智能体 - 优化版本
    
    职责：
    1. 接收测试用例生成请求
    2. 生成和增强测试用例
    3. 通过消息机制协调保存和思维导图生成
    4. 统一的错误处理和响应机制
    
    设计原则：
    - 单一职责：只负责测试用例生成
    - 消息驱动：通过AutoGen消息机制与其他智能体通信
    - 错误处理：统一的异常处理和响应机制
    - 性能监控：记录生成指标和性能数据
    """

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化测试用例生成智能体"""
        super().__init__(
            agent_id=AgentTypes.TEST_CASE_GENERATOR.value,
            agent_name=AGENT_NAMES.get(AgentTypes.TEST_CASE_GENERATOR.value, "测试用例生成智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )
        
        # 初始化性能指标
        self.generation_metrics = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0,
            "total_test_cases_generated": 0
        }
        
        # 初始化AI增强配置
        self.ai_enhancement_config = {
            "enabled": True,
            "model_type": "deepseek",
            "stream_enabled": False,
            "max_retries": 3
        }

        logger.info(f"测试用例生成智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_test_case_generation_request(
        self,
        message: TestCaseGenerationRequest,
        ctx: MessageContext
    ) -> None:
        """
        处理测试用例生成请求 - 优化版本
        
        流程：
        1. 生成测试用例
        2. 发送保存请求到数据库智能体
        3. 发送思维导图生成请求（如果需要）
        4. 统一响应处理
        """
        start_time = datetime.now()
        self.generation_metrics["total_requests"] += 1
        
        try:
            logger.info(f"开始处理测试用例生成请求: {message.session_id}")

            # 发送开始处理消息
            await self.send_response(
                f"🔧 开始生成测试用例，来源: {message.source_type}",
                region="process"
            )

            # 发送输入数据统计
            source_data_size = len(str(message.source_data)) if message.source_data else 0
            await self.send_response(
                f"📊 输入数据统计: 数据大小 {source_data_size} 字符, 配置项 {len(message.generation_config)} 个",
                region="info",
                result={
                    "source_data_size": source_data_size,
                    "config_count": len(message.generation_config),
                    "source_type": message.source_type
                }
            )

            # 步骤1: 生成测试用例
            await self.send_response("🔄 第1步: 开始AI智能生成测试用例...", region="progress")
            generation_result = await self._generate_test_cases(message)

            if generation_result.generated_count == 0:
                await self.send_response("⚠️ 未能生成任何测试用例", region="warning")
                await self._handle_empty_generation(message, generation_result)
                return

            # 发送生成结果统计
            await self.send_response(
                f"✅ 测试用例生成完成: 共生成 {generation_result.generated_count} 个测试用例",
                region="success",
                result={
                    "generated_count": generation_result.generated_count,
                    "generation_time": generation_result.processing_time
                }
            )

            # 步骤2: 通过消息机制保存测试用例
            await self.send_response("🔄 第2步: 保存测试用例到数据库...", region="progress")
            save_result = await self._send_save_request(message, generation_result)

            # 发送保存结果
            if save_result.success:
                await self.send_response(
                    f"✅ 数据库保存完成: 成功保存 {save_result.saved_count} 个测试用例",
                    region="success",
                    result={"saved_count": save_result.saved_count}
                )
            else:
                await self.send_response(
                    f"⚠️ 数据库保存部分失败: 成功 {save_result.saved_count} 个, 失败 {save_result.failed_count} 个",
                    region="warning",
                    result={
                        "saved_count": save_result.saved_count,
                        "failed_count": save_result.failed_count
                    }
                )

            # 步骤3: 生成思维导图（如果需要）
            mind_map_generated = False
            if message.generation_config.get("generate_mind_map", False) and save_result.success:
                await self.send_response("🔄 第3步: 生成测试用例思维导图...", region="progress")
                await self._send_mind_map_request(message, save_result.saved_test_cases)
                mind_map_generated = True
                await self.send_response("✅ 思维导图生成完成", region="success")
            elif message.generation_config.get("generate_mind_map", False):
                await self.send_response("⚠️ 跳过思维导图生成（数据库保存失败）", region="warning")

            # 步骤4: 发送最终响应
            await self._send_final_response(
                message, generation_result, save_result, mind_map_generated, start_time
            )
            
            # 更新成功指标
            self.generation_metrics["successful_generations"] += 1
            self.generation_metrics["total_test_cases_generated"] += generation_result.generated_count
            self._update_average_processing_time(start_time)
            
        except Exception as e:
            await self._handle_generation_error(message, e, start_time)
            self.generation_metrics["failed_generations"] += 1

    async def _generate_test_cases(
        self,
        message: TestCaseGenerationRequest
    ) -> TestCaseGenerationResult:
        """生成测试用例（核心逻辑）"""
        try:
            start_time = datetime.now()
            result = TestCaseGenerationResult()

            await self.send_response(
                "📝 正在分析输入数据并准备生成测试用例...",
                region="progress"
            )

            # 处理测试用例数据
            data_processing_start = datetime.now()
            processed_test_cases = await self._process_test_case_data(message)
            data_processing_time = (datetime.now() - data_processing_start).total_seconds()

            await self.send_response(
                f"✅ 数据处理完成: 生成 {len(processed_test_cases)} 个测试用例 (耗时: {data_processing_time:.2f}秒)",
                region="success",
                result={
                    "generated_count": len(processed_test_cases),
                    "data_processing_time": data_processing_time
                }
            )

            # 计算总处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            # 发送性能指标
            if len(processed_test_cases) > 0:
                await self.send_response(
                    f"📊 生成性能指标: 平均每个用例 {processing_time/len(processed_test_cases):.3f}秒",
                    region="info",
                    result={
                        "total_processing_time": processing_time,
                        "average_time_per_case": processing_time/len(processed_test_cases),
                        "generation_rate": len(processed_test_cases)/processing_time if processing_time > 0 else 0
                    }
                )

            result.generated_count = len(processed_test_cases)
            result.generated_test_cases = processed_test_cases
            result.processing_time = processing_time

            logger.info(f"成功生成了 {len(processed_test_cases)} 个测试用例")
            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"生成测试用例失败: {str(e)}")
            await self.send_response(
                f"❌ 测试用例生成失败: {str(e)} (耗时: {processing_time:.2f}秒)",
                region="error"
            )
            raise

    async def _process_test_case_data(
        self, 
        message: TestCaseGenerationRequest
    ) -> List[TestCaseData]:
        """处理测试用例数据"""
        try:
            processed_cases = []

            # 借助RAG知识库系统，获取当前用例的上下文信息
            i = 1
            for test_case_data in message.test_cases:
                # 增强测试用例数据
                await self.send_response(
                    f"📝 正在增强第 {i} 条测试用例数据...",
                    region="progress"
                )
                enhanced_case = await self._enhance_test_case(test_case_data, message)
                processed_cases.append(enhanced_case)
                i += 1
            
            return processed_cases
            
        except Exception as e:
            logger.error(f"处理测试用例数据失败: {str(e)}")
            raise

    async def _enhance_test_case(
        self, 
        test_case_data: TestCaseData, 
        message: TestCaseGenerationRequest
    ) -> TestCaseData:
        """增强测试用例数据"""
        try:
            # 如果缺少详细信息，使用AI生成
            if not test_case_data.test_steps or not test_case_data.expected_results:
                enhanced_data = await self._ai_enhance_test_case(test_case_data, message)
                
                # 更新测试用例数据
                if enhanced_data.get("test_steps"):
                    test_case_data.test_steps = enhanced_data["test_steps"]
                if enhanced_data.get("expected_results"):
                    test_case_data.expected_results = enhanced_data["expected_results"]
                if enhanced_data.get("preconditions"):
                    test_case_data.preconditions = enhanced_data["preconditions"]
            
            return test_case_data
            
        except Exception as e:
            logger.warning(f"增强测试用例失败，使用原始数据: {str(e)}")
            return test_case_data

    async def _ai_enhance_test_case(
        self, 
        test_case_data: TestCaseData, 
        message: TestCaseGenerationRequest
    ) -> Dict[str, Any]:
        """使用AI增强测试用例"""
        try:
            if not self.ai_enhancement_config["enabled"]:
                return {}
                
            # 创建AI增强智能体
            agent = self._create_test_case_enhancer()
            
            # 构建增强提示
            enhancement_prompt = self._build_enhancement_prompt(test_case_data, message)
            
            # 执行AI增强
            enhancement_result = await self._run_ai_enhancement(agent, enhancement_prompt)

            return json.loads(enhancement_result.replace("```json", "").replace("```", ""))
            
        except Exception as e:
            logger.error(f"AI增强测试用例失败: {str(e)}")
            return {}

    def _create_test_case_enhancer(self):
        """创建测试用例增强智能体"""
        from app.agents.factory import agent_factory
        
        return agent_factory.create_assistant_agent(
            name="test_case_enhancer",
            system_message=self._build_enhancement_system_prompt(),
            model_client_type=self.ai_enhancement_config["model_type"],
            model_client_stream=self.ai_enhancement_config["stream_enabled"]
        )

    def _build_enhancement_system_prompt(self) -> str:
        """构建增强系统提示"""
        return """
你是专业的测试用例设计专家，擅长完善和优化测试用例。

你的任务是：
1. 根据测试用例标题和描述，生成详细的测试步骤
2. 设计合理的前置条件
3. 明确预期结果
4. 确保测试用例的完整性和可执行性

请按照以下JSON格式返回增强结果：
{
    "preconditions": "前置条件描述",
    "test_steps": [
        {
            "step_number": 1,
            "action": "操作描述",
            "data": "测试数据",
            "expected": "步骤预期结果"
        }
    ],
    "expected_results": "整体预期结果描述"
}

要求：
- 测试步骤要具体、可执行
- 前置条件要明确、完整
- 预期结果要清晰、可验证
- 确保逻辑连贯性
"""

    def _build_enhancement_prompt(
        self, 
        test_case_data: TestCaseData, 
        message: TestCaseGenerationRequest
    ) -> str:
        """构建增强提示"""
        return f"""
请为以下测试用例生成详细的前置条件、测试步骤和预期结果：

测试用例标题: {test_case_data.title}
测试用例描述: {test_case_data.description}
测试类型: {test_case_data.test_type}
测试级别: {test_case_data.test_level}
优先级: {test_case_data.priority}

来源信息:
- 来源类型: {message.source_type}
- 生成配置: {json.dumps(message.generation_config, ensure_ascii=False, indent=2)}

请生成详细的前置条件、测试步骤和预期结果。
"""

    async def _run_ai_enhancement(self, agent, prompt: str) -> str:
        """执行AI增强"""
        try:
            stream = agent.run_stream(task=prompt)
            async for event in stream:
                # 流式消息
                if isinstance(event, ModelClientStreamingChunkEvent):
                    # 临时注释，不在前端显示流式内容
                    # await self.send_response(content=event.content, source=self.id.key)
                    continue

                # 最终的完整结果
                if isinstance(event, TaskResult):
                    messages = event.messages
                    if messages and hasattr(messages[-1], 'content'):
                        return messages[-1].content

            # 返回默认结果
            return self._get_default_enhancement_result()

        except Exception as e:
            logger.error(f"AI增强执行失败: {str(e)}")
            return self._get_default_enhancement_result()

    def _get_default_enhancement_result(self) -> str:
        """获取默认增强结果"""
        return """
{
    "preconditions": "系统已启动，用户已登录",
    "test_steps": [
        {
            "step_number": 1,
            "action": "执行测试操作",
            "data": "测试数据",
            "expected": "操作成功"
        }
    ],
    "expected_results": "测试通过，功能正常"
}
"""

    async def _send_save_request(
        self,
        message: TestCaseGenerationRequest,
        generation_result: TestCaseGenerationResult
    ) -> TestCaseSaveResponse:
        """发送保存请求到数据库智能体"""
        try:
            # 构建保存请求
            save_request = TestCaseSaveRequest(
                session_id=message.session_id,
                test_cases=generation_result.generated_test_cases,
                project_id=message.generation_config.get("project_id"),
                created_by=message.generation_config.get("created_by"),
                source_metadata={
                    "source_type": message.source_type,
                    "generation_config": message.generation_config,
                    "source_data": message.source_data
                }
            )
            logger.info(f"已发送保存请求到数据库智能体: {message.session_id}")

            # 发送消息到数据库保存智能体
            test_case_save_response = await self.send_message(
                save_request,
                AgentId(type=TopicTypes.TEST_CASE_SAVER.value, key=self.id.key)
            )
            return test_case_save_response
        except Exception as e:
            logger.error(f"发送保存请求失败: {str(e)}")
            return TestCaseSaveResponse(
                session_id=message.session_id,
                success=False,
                errors=[str(e)]
            )

    async def _send_mind_map_request(
        self,
        message: TestCaseGenerationRequest,
        saved_test_cases: List[Dict[str, Any]]
    ):
        """发送思维导图生成请求"""
        try:
            await self.send_response("🧠 正在生成测试用例思维导图...")

            # 构建思维导图生成请求
            mind_map_request = MindMapGenerationRequest(
                session_id=message.session_id,
                test_case_ids=[tc["id"] for tc in saved_test_cases],
                source_data=message.source_data,
                generation_config=message.generation_config
            )

            # 发送到思维导图生成智能体
            await self.publish_message(
                mind_map_request,
                topic_id=TopicId(type=TopicTypes.MIND_MAP_GENERATOR.value, source=self.id.key)
            )

            logger.info(f"已发送思维导图生成请求: {message.session_id}")

        except Exception as e:
            logger.error(f"发送思维导图生成请求失败: {str(e)}")

    async def _handle_empty_generation(
        self,
        message: TestCaseGenerationRequest,
        generation_result: TestCaseGenerationResult
    ):
        """处理空生成结果"""
        response = TestCaseGenerationResponse(
            session_id=message.session_id,
            generation_id=str(uuid.uuid4()),
            source_type=message.source_type,
            generated_count=0,
            test_case_ids=[],
            mind_map_generated=False,
            processing_time=generation_result.processing_time,
            created_at=datetime.now().isoformat()
        )

        await self.send_response(
            "⚠️ 未生成任何测试用例",
            is_final=True,
            result=response.model_dump()
        )

    async def _send_final_response(
        self,
        message: TestCaseGenerationRequest,
        generation_result: TestCaseGenerationResult,
        save_result: TestCaseSaveResponse,
        mind_map_generated: bool,
        start_time: datetime
    ):
        """发送最终响应"""
        processing_time = (datetime.now() - start_time).total_seconds()

        response = TestCaseGenerationResponse(
            session_id=message.session_id,
            generation_id=str(uuid.uuid4()),
            source_type=message.source_type,
            generated_count=generation_result.generated_count,
            test_case_ids=[tc["id"] for tc in save_result.saved_test_cases] if save_result.success else [],
            mind_map_generated=mind_map_generated,
            processing_time=processing_time,
            created_at=datetime.now().isoformat()
        )

        if save_result.success:
            await self.send_response(
                f"✅ 测试用例处理完成！生成 {generation_result.generated_count} 个，成功保存 {save_result.saved_count} 个",
                is_final=False,
                result=response.model_dump()
            )
        else:
            await self.send_response(
                f"⚠️ 测试用例生成完成，但保存时出现问题：成功 {save_result.saved_count} 个，失败 {save_result.failed_count} 个",
                is_final=True,
                result=response.model_dump()
            )

    async def _handle_generation_error(
        self,
        message: TestCaseGenerationRequest,
        error: Exception,
        start_time: datetime
    ):
        """处理生成错误"""
        processing_time = (datetime.now() - start_time).total_seconds()

        error_response = TestCaseGenerationResponse(
            session_id=message.session_id,
            generation_id=str(uuid.uuid4()),
            source_type=message.source_type,
            generated_count=0,
            test_case_ids=[],
            mind_map_generated=False,
            processing_time=processing_time,
            created_at=datetime.now().isoformat()
        )

        await self.send_response(
            f"❌ 测试用例生成失败: {str(error)}",
            is_final=True,
            result=error_response.model_dump()
        )

        logger.error(f"测试用例生成失败: {message.session_id}, 错误: {str(error)}")

    def _update_average_processing_time(self, start_time: datetime):
        """更新平均处理时间"""
        processing_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.generation_metrics["average_processing_time"]
        total_requests = self.generation_metrics["total_requests"]

        # 计算新的平均值
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.generation_metrics["average_processing_time"] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.generation_metrics,
            "success_rate": (
                self.generation_metrics["successful_generations"] /
                max(self.generation_metrics["total_requests"], 1)
            ) * 100,
            "agent_name": self.agent_name,
            "agent_id": self.id.key
        }
