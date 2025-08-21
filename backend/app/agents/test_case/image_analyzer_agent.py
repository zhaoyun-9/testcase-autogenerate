"""
图片分析智能体
负责分析流程图、思维导图、UI截图等图片，提取测试用例相关信息
"""
import uuid
import json
import base64
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import (
    ImageAnalysisRequest, ImageAnalysisResponse,
    TestCaseData
)
from app.core.enums import TestType, TestLevel, Priority, InputSource


class ImageAnalysisResult(BaseModel):
    """图片分析结果"""
    image_type: str = Field(..., description="图片类型")
    detected_elements: List[Dict[str, Any]] = Field(default_factory=list, description="检测到的元素")
    workflow_steps: List[Dict[str, Any]] = Field(default_factory=list, description="工作流步骤")
    ui_components: List[Dict[str, Any]] = Field(default_factory=list, description="UI组件")
    test_scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="测试场景")
    confidence_score: float = Field(0.0, description="分析置信度")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="分析元数据")


@type_subscription(topic_type=TopicTypes.IMAGE_ANALYZER.value)
class ImageAnalyzerAgent(BaseAgent):
    """图片分析智能体，负责分析各种类型的图片并提取测试信息"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化图片分析智能体"""
        super().__init__(
            agent_id=AgentTypes.IMAGE_ANALYZER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.IMAGE_ANALYZER.value, "图片分析智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )

        # 支持的图片类型
        self.supported_image_types = {
            'flowchart': self._analyze_flowchart,
            'mindmap': self._analyze_mindmap,
            'ui_screenshot': self._analyze_ui_screenshot,
            'wireframe': self._analyze_wireframe,
            'diagram': self._analyze_diagram
        }

        logger.info(f"图片分析智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_image_analysis_request(
        self,
        message: ImageAnalysisRequest,
        ctx: MessageContext
    ) -> None:
        """处理图片分析请求"""
        try:
            logger.info(f"开始处理图片分析请求: {message.session_id}")

            await self.send_response(
                f"🔍 开始分析图片: {message.image_name}",
                region="process"
            )

            # 分析图片
            analysis_result = await self._analyze_image(message)

            # 生成测试用例
            test_cases = await self._generate_test_cases_from_image(
                analysis_result, message
            )

            # 构建响应
            response = ImageAnalysisResponse(
                session_id=message.session_id,
                image_id=str(uuid.uuid4()),
                image_name=message.image_name,
                image_path=message.image_path,
                analysis_result=analysis_result.model_dump(),
                test_cases=test_cases,
                processing_time=0.0,
                created_at=datetime.now().isoformat()
            )

            await self.send_response(
                "✅ 图片分析完成，已生成测试用例",
                is_final=True,
                result=response.model_dump()
            )

            # 发送到测试点提取智能体
            await self._send_to_test_point_extractor(response)

        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            await self.send_response(
                f"❌ 图片分析失败: {str(e)}",
                is_final=True,
                error=str(e)
            )

    async def _analyze_image(self, message: ImageAnalysisRequest) -> ImageAnalysisResult:
        """分析图片内容"""
        try:
            # 读取图片数据
            image_data = await self._load_image_data(message.image_path)

            # 检测图片类型
            image_type = await self._detect_image_type(image_data, message)

            await self.send_response(f"📊 检测到图片类型: {image_type}")

            # 使用对应的分析方法
            if image_type in self.supported_image_types:
                analyzer_func = self.supported_image_types[image_type]
                analysis_result = await analyzer_func(image_data, message)
            else:
                # 使用通用分析方法
                analysis_result = await self._analyze_generic_image(image_data, message)

            analysis_result.image_type = image_type
            return analysis_result

        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise

    async def _load_image_data(self, image_path: str) -> str:
        """加载图片数据并转换为base64"""
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"加载图片失败: {str(e)}")
            raise

    async def _detect_image_type(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> str:
        """检测图片类型"""
        try:
            # 如果用户指定了图片类型，直接使用
            if message.image_type:
                return message.image_type

            # 使用AI检测图片类型
            agent = self._create_image_type_detector()
            prompt = self._build_image_type_detection_prompt(message)

            # 构建多模态消息
            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            # 执行检测
            result = await self._run_multimodal_analysis(agent, multimodal_message)

            # 解析结果
            detected_type = self._parse_image_type_result(result)
            return detected_type

        except Exception as e:
            logger.warning(f"图片类型检测失败，使用默认类型: {str(e)}")
            return "diagram"

    async def _analyze_flowchart(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> ImageAnalysisResult:
        """分析流程图"""
        try:
            await self.send_response("🔄 正在分析流程图...")

            agent = self._create_flowchart_analyzer()
            prompt = self._build_flowchart_analysis_prompt(message)

            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            result = await self._run_multimodal_analysis(agent, multimodal_message)
            return self._parse_flowchart_result(result)

        except Exception as e:
            logger.error(f"流程图分析失败: {str(e)}")
            return self._create_default_analysis_result("flowchart")

    async def _analyze_mindmap(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> ImageAnalysisResult:
        """分析思维导图"""
        try:
            await self.send_response("🧠 正在分析思维导图...")

            agent = self._create_mindmap_analyzer()
            prompt = self._build_mindmap_analysis_prompt(message)

            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            result = await self._run_multimodal_analysis(agent, multimodal_message)
            return self._parse_mindmap_result(result)

        except Exception as e:
            logger.error(f"思维导图分析失败: {str(e)}")
            return self._create_default_analysis_result("mindmap")

    async def _analyze_ui_screenshot(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> ImageAnalysisResult:
        """分析UI截图"""
        try:
            await self.send_response("📱 正在分析UI截图...")

            agent = self._create_ui_analyzer()
            prompt = self._build_ui_analysis_prompt(message)

            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            result = await self._run_multimodal_analysis(agent, multimodal_message)
            return self._parse_ui_result(result)

        except Exception as e:
            logger.error(f"UI截图分析失败: {str(e)}")
            return self._create_default_analysis_result("ui_screenshot")

    async def _analyze_wireframe(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> ImageAnalysisResult:
        """分析线框图"""
        try:
            await self.send_response("📐 正在分析线框图...")

            agent = self._create_wireframe_analyzer()
            prompt = self._build_wireframe_analysis_prompt(message)

            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            result = await self._run_multimodal_analysis(agent, multimodal_message)
            return self._parse_wireframe_result(result)

        except Exception as e:
            logger.error(f"线框图分析失败: {str(e)}")
            return self._create_default_analysis_result("wireframe")

    async def _analyze_diagram(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> ImageAnalysisResult:
        """分析通用图表"""
        try:
            await self.send_response("📊 正在分析图表...")

            agent = self._create_diagram_analyzer()
            prompt = self._build_diagram_analysis_prompt(message)

            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            result = await self._run_multimodal_analysis(agent, multimodal_message)
            return self._parse_diagram_result(result)

        except Exception as e:
            logger.error(f"图表分析失败: {str(e)}")
            return self._create_default_analysis_result("diagram")

    async def _analyze_generic_image(
        self,
        image_data: str,
        message: ImageAnalysisRequest
    ) -> ImageAnalysisResult:
        """通用图片分析"""
        try:
            await self.send_response("🔍 正在进行通用图片分析...")

            agent = self._create_generic_analyzer()
            prompt = self._build_generic_analysis_prompt(message)

            multimodal_message = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]

            result = await self._run_multimodal_analysis(agent, multimodal_message)
            return self._parse_generic_result(result)

        except Exception as e:
            logger.error(f"通用图片分析失败: {str(e)}")
            return self._create_default_analysis_result("unknown")

    def _create_image_type_detector(self):
        """创建图片类型检测智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="image_type_detector",
            system_message=self._build_image_type_detection_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _create_flowchart_analyzer(self):
        """创建流程图分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="flowchart_analyzer",
            system_message=self._build_flowchart_analysis_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _create_mindmap_analyzer(self):
        """创建思维导图分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="mindmap_analyzer",
            system_message=self._build_mindmap_analysis_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _create_ui_analyzer(self):
        """创建UI分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="ui_analyzer",
            system_message=self._build_ui_analysis_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _create_wireframe_analyzer(self):
        """创建线框图分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="wireframe_analyzer",
            system_message=self._build_wireframe_analysis_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _create_diagram_analyzer(self):
        """创建图表分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="diagram_analyzer",
            system_message=self._build_diagram_analysis_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _create_generic_analyzer(self):
        """创建通用分析智能体"""
        from app.agents.factory import agent_factory

        return agent_factory.create_assistant_agent(
            name="generic_analyzer",
            system_message=self._build_generic_analysis_system_prompt(),
            model_client_type="qwenvl",
            model_client_stream=False
        )

    def _build_image_type_detection_system_prompt(self) -> str:
        """构建图片类型检测系统提示"""
        return """
你是专业的图片类型识别专家，能够准确识别各种类型的图片。

支持的图片类型：
- flowchart: 流程图，包含开始、结束、判断、处理等节点
- mindmap: 思维导图，树状或放射状结构
- ui_screenshot: UI界面截图，包含按钮、输入框等界面元素
- wireframe: 线框图，简单的界面布局图
- diagram: 其他类型的图表或示意图

请仔细观察图片内容，返回最匹配的图片类型，只返回类型名称，不要其他内容。
"""

    def _build_flowchart_analysis_system_prompt(self) -> str:
        """构建流程图分析系统提示"""
        return """
你是专业的流程图分析专家，擅长从流程图中提取业务流程和测试场景。

你的任务是：
1. 识别流程图中的所有节点和连接关系
2. 理解业务流程的逻辑
3. 识别关键的决策点和分支
4. 提取可测试的场景和路径

请按照以下JSON格式返回分析结果：
{
    "detected_elements": [
        {
            "type": "start/process/decision/end",
            "text": "节点文本",
            "position": {"x": 0, "y": 0},
            "connections": ["连接的节点ID"]
        }
    ],
    "workflow_steps": [
        {
            "step_id": "步骤ID",
            "description": "步骤描述",
            "type": "normal/decision",
            "next_steps": ["下一步骤ID"]
        }
    ],
    "test_scenarios": [
        {
            "title": "测试场景标题",
            "description": "测试场景描述",
            "path": ["步骤1", "步骤2", "步骤3"],
            "test_type": "functional",
            "priority": "P1"
        }
    ],
    "confidence_score": 0.95
}
"""

    def _build_mindmap_analysis_system_prompt(self) -> str:
        """构建思维导图分析系统提示"""
        return """
你是专业的思维导图分析专家，擅长从思维导图中提取结构化信息和测试点。

你的任务是：
1. 识别思维导图的中心主题
2. 分析各个分支和子分支
3. 理解层级关系和逻辑结构
4. 提取可测试的功能点

请按照以下JSON格式返回分析结果：
{
    "detected_elements": [
        {
            "type": "center/branch/leaf",
            "text": "节点文本",
            "level": 1,
            "parent": "父节点ID",
            "children": ["子节点ID"]
        }
    ],
    "test_scenarios": [
        {
            "title": "测试场景标题",
            "description": "基于分支内容的测试描述",
            "category": "功能分类",
            "test_type": "functional",
            "priority": "P2"
        }
    ],
    "confidence_score": 0.90
}
"""

    def _build_ui_analysis_system_prompt(self) -> str:
        """构建UI分析系统提示"""
        return """
你是专业的UI界面分析专家，擅长从UI截图中识别界面元素和交互流程。

你的任务是：
1. 识别所有可交互的UI元素
2. 分析界面布局和功能区域
3. 理解用户可能的操作流程
4. 生成UI测试场景

请按照以下JSON格式返回分析结果：
{
    "ui_components": [
        {
            "type": "button/input/dropdown/link/image",
            "text": "元素文本或标识",
            "position": {"x": 0, "y": 0, "width": 100, "height": 30},
            "interactive": true,
            "function": "元素功能描述"
        }
    ],
    "test_scenarios": [
        {
            "title": "UI测试场景",
            "description": "测试描述",
            "steps": ["操作步骤1", "操作步骤2"],
            "elements": ["涉及的元素"],
            "test_type": "functional",
            "priority": "P1"
        }
    ],
    "confidence_score": 0.85
}
"""

    def _build_wireframe_analysis_system_prompt(self) -> str:
        """构建线框图分析系统提示"""
        return """
你是专业的线框图分析专家，擅长从线框图中理解界面设计和功能布局。

请分析线框图并返回JSON格式的结果，包含界面元素和测试场景。
"""

    def _build_diagram_analysis_system_prompt(self) -> str:
        """构建图表分析系统提示"""
        return """
你是专业的图表分析专家，擅长从各种图表中提取信息和测试点。

请分析图表并返回JSON格式的结果，包含图表元素和相关测试场景。
"""

    def _build_generic_analysis_system_prompt(self) -> str:
        """构建通用分析系统提示"""
        return """
你是专业的图片分析专家，能够分析各种类型的图片并提取测试相关信息。

请分析图片内容并返回JSON格式的结果。
"""

    async def _run_multimodal_analysis(self, agent, multimodal_message) -> str:
        """执行多模态分析"""
        try:
            # 构建多模态消息
            # 发送消息并获取响应
            result = await agent.run(
                task=multimodal_message,
            )

            # 提取最后一条消息作为结果
            if result.messages:
                last_message = result.messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                else:
                    return str(last_message)

            # 返回默认结果
            return """
{
    "detected_elements": [],
    "workflow_steps": [],
    "ui_components": [],
    "test_scenarios": [
        {
            "title": "基础功能测试",
            "description": "测试基本功能",
            "test_type": "functional",
            "priority": "P2"
        }
    ],
    "confidence_score": 0.8
}
"""
        except Exception as e:
            logger.error(f"多模态分析执行失败: {str(e)}")
            # 返回默认结果而不是抛出异常
            return """
{
    "detected_elements": [],
    "workflow_steps": [],
    "ui_components": [],
    "test_scenarios": [
        {
            "title": "图片分析失败",
            "description": "图片分析过程中出现错误",
            "test_type": "functional",
            "priority": "P3"
        }
    ],
    "confidence_score": 0.3
}
"""

    def _parse_image_type_result(self, result: str) -> str:
        """解析图片类型检测结果"""
        try:
            # 清理结果字符串
            result = result.strip().lower()

            # 检查是否包含支持的类型
            for image_type in self.supported_image_types.keys():
                if image_type in result:
                    return image_type

            return "diagram"  # 默认类型

        except Exception as e:
            logger.warning(f"解析图片类型失败: {str(e)}")
            return "diagram"

    def _parse_flowchart_result(self, result: str) -> ImageAnalysisResult:
        """解析流程图分析结果"""
        try:
            data = json.loads(result)
            return ImageAnalysisResult(
                image_type="flowchart",
                detected_elements=data.get("detected_elements", []),
                workflow_steps=data.get("workflow_steps", []),
                ui_components=[],
                test_scenarios=data.get("test_scenarios", []),
                confidence_score=data.get("confidence_score", 0.8),
                analysis_metadata={"analysis_type": "flowchart"}
            )
        except Exception as e:
            logger.warning(f"解析流程图结果失败: {str(e)}")
            return self._create_default_analysis_result("flowchart")

    def _parse_mindmap_result(self, result: str) -> ImageAnalysisResult:
        """解析思维导图分析结果"""
        try:
            data = json.loads(result)
            return ImageAnalysisResult(
                image_type="mindmap",
                detected_elements=data.get("detected_elements", []),
                workflow_steps=[],
                ui_components=[],
                test_scenarios=data.get("test_scenarios", []),
                confidence_score=data.get("confidence_score", 0.8),
                analysis_metadata={"analysis_type": "mindmap"}
            )
        except Exception as e:
            logger.warning(f"解析思维导图结果失败: {str(e)}")
            return self._create_default_analysis_result("mindmap")

    def _parse_ui_result(self, result: str) -> ImageAnalysisResult:
        """解析UI分析结果"""
        try:
            data = json.loads(result)
            return ImageAnalysisResult(
                image_type="ui_screenshot",
                detected_elements=[],
                workflow_steps=[],
                ui_components=data.get("ui_components", []),
                test_scenarios=data.get("test_scenarios", []),
                confidence_score=data.get("confidence_score", 0.8),
                analysis_metadata={"analysis_type": "ui_screenshot"}
            )
        except Exception as e:
            logger.warning(f"解析UI结果失败: {str(e)}")
            return self._create_default_analysis_result("ui_screenshot")

    def _parse_wireframe_result(self, result: str) -> ImageAnalysisResult:
        """解析线框图分析结果"""
        try:
            data = json.loads(result)
            return ImageAnalysisResult(
                image_type="wireframe",
                detected_elements=data.get("detected_elements", []),
                workflow_steps=[],
                ui_components=data.get("ui_components", []),
                test_scenarios=data.get("test_scenarios", []),
                confidence_score=data.get("confidence_score", 0.8),
                analysis_metadata={"analysis_type": "wireframe"}
            )
        except Exception as e:
            logger.warning(f"解析线框图结果失败: {str(e)}")
            return self._create_default_analysis_result("wireframe")

    def _parse_diagram_result(self, result: str) -> ImageAnalysisResult:
        """解析图表分析结果"""
        try:
            data = json.loads(result)
            return ImageAnalysisResult(
                image_type="diagram",
                detected_elements=data.get("detected_elements", []),
                workflow_steps=data.get("workflow_steps", []),
                ui_components=[],
                test_scenarios=data.get("test_scenarios", []),
                confidence_score=data.get("confidence_score", 0.8),
                analysis_metadata={"analysis_type": "diagram"}
            )
        except Exception as e:
            logger.warning(f"解析图表结果失败: {str(e)}")
            return self._create_default_analysis_result("diagram")

    def _parse_generic_result(self, result: str) -> ImageAnalysisResult:
        """解析通用分析结果"""
        try:
            data = json.loads(result)
            return ImageAnalysisResult(
                image_type="unknown",
                detected_elements=data.get("detected_elements", []),
                workflow_steps=data.get("workflow_steps", []),
                ui_components=data.get("ui_components", []),
                test_scenarios=data.get("test_scenarios", []),
                confidence_score=data.get("confidence_score", 0.6),
                analysis_metadata={"analysis_type": "generic"}
            )
        except Exception as e:
            logger.warning(f"解析通用结果失败: {str(e)}")
            return self._create_default_analysis_result("unknown")

    def _create_default_analysis_result(self, image_type: str) -> ImageAnalysisResult:
        """创建默认分析结果"""
        return ImageAnalysisResult(
            image_type=image_type,
            detected_elements=[],
            workflow_steps=[],
            ui_components=[],
            test_scenarios=[
                {
                    "title": f"基于{image_type}的测试场景",
                    "description": "默认生成的测试场景",
                    "test_type": "functional",
                    "priority": "P3"
                }
            ],
            confidence_score=0.5,
            analysis_metadata={"analysis_type": image_type, "fallback": True}
        )

    async def _generate_test_cases_from_image(
        self,
        analysis_result: ImageAnalysisResult,
        message: ImageAnalysisRequest
    ) -> List[TestCaseData]:
        """从图片分析结果生成测试用例"""
        test_cases = []

        try:
            # 基于测试场景生成测试用例
            for scenario in analysis_result.test_scenarios:
                test_case = TestCaseData(
                    title=scenario.get("title", "未命名测试用例"),
                    description=scenario.get("description", ""),
                    test_type=self._map_test_type(scenario.get("test_type", "functional")),
                    test_level=TestLevel.SYSTEM,
                    priority=self._map_priority(scenario.get("priority", "P2")),
                    input_source=InputSource.IMAGE,
                    ai_confidence=analysis_result.confidence_score
                )
                test_cases.append(test_case)

            # 基于UI组件生成交互测试用例
            if analysis_result.ui_components:
                for component in analysis_result.ui_components:
                    if component.get("interactive", False):
                        test_case = TestCaseData(
                            title=f"测试{component.get('text', '界面元素')}交互",
                            description=f"测试{component.get('function', '功能')}的交互行为",
                            test_type=TestType.FUNCTIONAL,
                            test_level=TestLevel.SYSTEM,
                            priority=Priority.P2,
                            input_source=InputSource.IMAGE,
                            source_metadata={
                                "image_name": message.image_name,
                                "component_data": component
                            },
                            ai_confidence=analysis_result.confidence_score
                        )
                        test_cases.append(test_case)

            # 基于工作流步骤生成流程测试用例
            if analysis_result.workflow_steps:
                test_case = TestCaseData(
                    title="工作流程完整性测试",
                    description="测试完整的业务流程",
                    test_type=TestType.FUNCTIONAL,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P1,
                    input_source=InputSource.IMAGE,
                    source_metadata={
                        "image_name": message.image_name,
                        "workflow_steps": analysis_result.workflow_steps
                    },
                    ai_confidence=analysis_result.confidence_score
                )
                test_cases.append(test_case)

            logger.info(f"从图片生成了 {len(test_cases)} 个测试用例")
            return test_cases

        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            return []

    def _map_test_type(self, test_type_str: str) -> TestType:
        """映射测试类型"""
        mapping = {
            "functional": TestType.FUNCTIONAL,
            "performance": TestType.PERFORMANCE,
            "security": TestType.SECURITY,
            "compatibility": TestType.COMPATIBILITY,
            "usability": TestType.USABILITY,
            "interface": TestType.INTERFACE,
            "database": TestType.DATABASE
        }
        return mapping.get(test_type_str.lower(), TestType.FUNCTIONAL)

    def _map_priority(self, priority_str: str) -> Priority:
        """映射优先级"""
        mapping = {
            "high": Priority.P1,
            "medium": Priority.P2,
            "low": Priority.P3,
            "P0": Priority.P0,
            "P1": Priority.P1,
            "P2": Priority.P2,
            "P3": Priority.P3,
            "P4": Priority.P4
        }
        return mapping.get(priority_str, Priority.P2)

    def _build_image_type_detection_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建图片类型检测提示"""
        return f"""
请分析这张图片的类型。

图片名称: {message.image_name}
用户描述: {message.description or "无"}

请仔细观察图片内容，判断它属于以下哪种类型：
- flowchart: 流程图
- mindmap: 思维导图
- ui_screenshot: UI界面截图
- wireframe: 线框图
- diagram: 其他图表

只返回类型名称，不要其他内容。
"""

    def _build_flowchart_analysis_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建流程图分析提示"""
        return f"""
请分析这张流程图，提取业务流程和测试场景。

图片名称: {message.image_name}
用户描述: {message.description or "无"}
分析目标: {message.analysis_target or "生成测试用例"}

请识别流程图中的所有节点、连接关系和业务逻辑，生成对应的测试场景。
"""

    def _build_mindmap_analysis_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建思维导图分析提示"""
        return f"""
请分析这张思维导图，提取结构化信息和测试点。

图片名称: {message.image_name}
用户描述: {message.description or "无"}
分析目标: {message.analysis_target or "生成测试用例"}

请识别思维导图的层级结构和各个分支，生成对应的测试场景。
"""

    def _build_ui_analysis_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建UI分析提示"""
        return f"""
请分析这张UI界面截图，识别界面元素和交互流程。

图片名称: {message.image_name}
用户描述: {message.description or "无"}
分析目标: {message.analysis_target or "生成测试用例"}

请识别所有可交互的UI元素，分析用户可能的操作流程，生成UI测试场景。
"""

    def _build_wireframe_analysis_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建线框图分析提示"""
        return f"""
请分析这张线框图，理解界面设计和功能布局。

图片名称: {message.image_name}
用户描述: {message.description or "无"}
分析目标: {message.analysis_target or "生成测试用例"}

请分析线框图的布局和功能设计，生成相应的测试场景。
"""

    def _build_diagram_analysis_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建图表分析提示"""
        return f"""
请分析这张图表，提取相关信息和测试点。

图片名称: {message.image_name}
用户描述: {message.description or "无"}
分析目标: {message.analysis_target or "生成测试用例"}

请分析图表内容，理解其表达的信息，生成相关的测试场景。
"""

    def _build_generic_analysis_prompt(self, message: ImageAnalysisRequest) -> str:
        """构建通用分析提示"""
        return f"""
请分析这张图片，提取测试相关信息。

图片名称: {message.image_name}
用户描述: {message.description or "无"}
分析目标: {message.analysis_target or "生成测试用例"}

请尽可能从图片中提取有用的信息，生成相关的测试场景。
"""

    async def _send_to_test_point_extractor(self, response: ImageAnalysisResponse):
        """发送到测试点提取智能体"""
        try:
            from app.core.messages.test_case import TestPointExtractionRequest

            # 构建需求解析结果
            requirement_analysis_result = {
                "source_type": "image",
                "image_name": response.image_name,
                "image_analysis": response.analysis_result,
                "requirements": [tc.model_dump() for tc in response.test_cases],
                "ui_elements": response.analysis_result.get("ui_elements", []),
                "user_interactions": response.analysis_result.get("user_interactions", []),
                "business_flows": response.analysis_result.get("business_flows", []),
                "functional_areas": response.analysis_result.get("functional_areas", []),
                "visual_elements": response.analysis_result.get("visual_elements", [])
            }

            extraction_request = TestPointExtractionRequest(
                session_id=response.session_id,
                requirement_analysis_result=requirement_analysis_result,
                extraction_config={
                    "enable_functional_testing": True,
                    "enable_non_functional_testing": True,
                    "enable_integration_testing": True,
                    "enable_acceptance_testing": True,
                    "enable_boundary_testing": True,
                    "enable_exception_testing": True,
                    "test_depth": "comprehensive",
                    "focus_areas": ["ui_testing", "user_experience", "visual_validation", "interaction_testing"]
                },
                test_strategy="image_driven"
            )

            await self.publish_message(
                extraction_request,
                topic_id=TopicId(type=TopicTypes.TEST_POINT_EXTRACTOR.value, source=self.id.key)
            )

            logger.info(f"已发送到测试点提取智能体: {response.session_id}")

        except Exception as e:
            logger.error(f"发送到测试点提取智能体失败: {str(e)}")