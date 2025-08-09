"""
视频分析智能体
负责分析录屏视频、操作演示视频等，提取用户行为序列并生成测试用例
基于Volcengine Ark SDK和QwenVL模型实现视频内容理解
"""
import os
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

# 导入Volcengine Ark SDK
try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    logger.warning("Volcengine Ark SDK未安装，请运行: pip install volcengine-python-sdk[ark]")
    Ark = None

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import (
    VideoAnalysisRequest, VideoAnalysisResponse,
    TestCaseGenerationRequest, TestCaseData
)


class VideoAnalysisResult(BaseModel):
    """视频分析结果"""
    video_type: str = Field(..., description="视频类型")
    duration: float = Field(..., description="视频时长(秒)")
    frame_count: int = Field(0, description="帧数")
    resolution: str = Field("", description="分辨率")
    user_actions: List[Dict[str, Any]] = Field(default_factory=list, description="用户操作序列")
    ui_elements: List[Dict[str, Any]] = Field(default_factory=list, description="UI元素")
    test_scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="测试场景")
    business_flows: List[Dict[str, Any]] = Field(default_factory=list, description="业务流程")
    key_frames: List[Dict[str, Any]] = Field(default_factory=list, description="关键帧")
    confidence_score: float = Field(0.0, description="分析置信度")
    analysis_summary: str = Field("", description="分析摘要")


@type_subscription(topic_type=TopicTypes.VIDEO_ANALYZER.value)
class VideoAnalyzerAgent(BaseAgent):
    """视频分析智能体，负责分析各种类型的视频并提取测试信息"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化视频分析智能体"""
        super().__init__(
            agent_id=AgentTypes.VIDEO_ANALYZER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.VIDEO_ANALYZER.value, "视频分析智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )

        # 支持的视频类型
        self.supported_video_types = {
            'screen_recording': self._analyze_screen_recording,
            'demo_video': self._analyze_demo_video,
            'tutorial_video': self._analyze_tutorial_video,
            'test_execution': self._analyze_test_execution,
            'user_journey': self._analyze_user_journey
        }

        # 支持的视频格式
        self.supported_formats = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}

        # 初始化Volcengine Ark客户端
        self.ark_client = None
        self.ark_model = None
        self._initialize_ark_client()

        logger.info(f"视频分析智能体初始化完成: {self.agent_name}")

    def _initialize_ark_client(self):
        """初始化Volcengine Ark客户端"""
        try:
            if Ark is None:
                logger.warning("Volcengine Ark SDK未安装，视频分析功能将受限")
                return

            # 从环境变量获取API Key和模型ID
            api_key = os.getenv('ARK_API_KEY')
            model_id = os.getenv('ARK_VIDEO_MODEL_ID', 'ep-20241210140356-8xqvs')  # 默认模型ID

            if not api_key:
                logger.warning("ARK_API_KEY环境变量未设置，视频分析功能将受限")
                return

            self.ark_client = Ark(api_key=api_key)
            self.ark_model = model_id
            logger.info("Volcengine Ark客户端初始化成功")

        except Exception as e:
            logger.error(f"初始化Volcengine Ark客户端失败: {str(e)}")

    @message_handler
    async def handle_video_analysis_request(
        self,
        message: VideoAnalysisRequest,
        ctx: MessageContext
    ) -> None:
        """处理视频分析请求"""
        try:
            logger.info(f"开始处理视频分析请求: {message.session_id}")

            await self.send_response(
                f"🎬 开始分析视频: {message.video_name}",
                region="process"
            )

            # 分析视频
            analysis_result = await self._analyze_video(message)

            # 生成测试用例
            test_cases = await self._generate_test_cases_from_video(
                analysis_result, message
            )

            # 构建响应
            response = VideoAnalysisResponse(
                session_id=message.session_id,
                video_id=str(uuid.uuid4()),
                video_name=message.video_name,
                video_path=message.video_path,
                analysis_result=analysis_result.model_dump(),
                test_cases=test_cases,
                processing_time=0.0,
                created_at=datetime.now().isoformat()
            )

            await self.send_response(
                f"✅ 视频分析完成，识别到 {len(analysis_result.user_actions)} 个用户操作",
                region="result"
            )

            # 发送到测试用例生成智能体
            test_case_request = TestCaseGenerationRequest(
                session_id=message.session_id,
                source_type="video",
                source_data=response.model_dump(),
                generation_config={
                    "include_user_actions": True,
                    "include_ui_elements": True,
                    "include_business_flows": True,
                    "test_case_format": "standard"
                }
            )

            await self.publish_message(
                test_case_request,
                topic_id=TopicId(type=TopicTypes.TEST_CASE_GENERATOR.value, source=self.agent_id)
            )

            logger.info(f"视频分析请求处理完成: {message.session_id}")

        except Exception as e:
            logger.error(f"处理视频分析请求失败: {message.session_id} - {str(e)}")
            await self.send_response(
                f"❌ 视频分析失败: {str(e)}",
                region="error"
            )
            raise

    async def _analyze_video(self, message: VideoAnalysisRequest) -> VideoAnalysisResult:
        """分析视频内容"""
        try:
            # 检查视频文件
            video_path = Path(message.video_path)
            if not video_path.exists():
                raise FileNotFoundError(f"视频文件不存在: {message.video_path}")

            file_extension = video_path.suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"不支持的视频格式: {file_extension}")

            await self.send_response(f"📹 正在分析 {file_extension} 格式视频...")

            # 获取视频基本信息
            video_info = await self._get_video_info(video_path)

            # 检测视频类型
            video_type = await self._detect_video_type(message)

            await self.send_response(f"🎯 检测到视频类型: {video_type}")

            # 使用对应的分析方法
            if video_type in self.supported_video_types:
                analyzer_func = self.supported_video_types[video_type]
                analysis_result = await analyzer_func(video_path, message)
            else:
                # 使用通用分析方法
                analysis_result = await self._analyze_generic_video(video_path, message)

            # 更新基本信息
            analysis_result.video_type = video_type
            analysis_result.duration = video_info.get('duration', 0.0)
            analysis_result.frame_count = video_info.get('frame_count', 0)
            analysis_result.resolution = video_info.get('resolution', '')

            return analysis_result

        except Exception as e:
            logger.error(f"视频分析失败: {str(e)}")
            raise

    async def _get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """获取视频基本信息"""
        try:
            # 这里可以使用ffmpeg或其他工具获取视频信息
            # 暂时返回默认值
            return {
                'duration': 60.0,
                'frame_count': 1800,
                'resolution': '1920x1080'
            }
        except Exception as e:
            logger.warning(f"获取视频信息失败: {str(e)}")
            return {
                'duration': 0.0,
                'frame_count': 0,
                'resolution': 'unknown'
            }

    async def _detect_video_type(self, message: VideoAnalysisRequest) -> str:
        """检测视频类型"""
        try:
            # 根据文件名和描述推断视频类型
            video_name = message.video_name.lower()
            description = (message.description or "").lower()

            if any(keyword in video_name or keyword in description 
                   for keyword in ['screen', 'recording', '录屏', '屏幕']):
                return 'screen_recording'
            elif any(keyword in video_name or keyword in description 
                     for keyword in ['demo', '演示', '示例']):
                return 'demo_video'
            elif any(keyword in video_name or keyword in description 
                     for keyword in ['tutorial', '教程', '指导']):
                return 'tutorial_video'
            elif any(keyword in video_name or keyword in description 
                     for keyword in ['test', '测试', 'execution']):
                return 'test_execution'
            elif any(keyword in video_name or keyword in description 
                     for keyword in ['journey', '流程', 'workflow']):
                return 'user_journey'
            else:
                return 'screen_recording'  # 默认为录屏类型

        except Exception as e:
            logger.warning(f"检测视频类型失败: {str(e)}")
            return 'screen_recording'

    async def _analyze_screen_recording(
        self,
        video_path: Path,
        message: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """分析录屏视频"""
        try:
            await self.send_response("🖥️ 正在分析录屏视频...")

            # 使用Volcengine Ark SDK分析视频
            if self.ark_client and self.ark_model:
                analysis_result = await self._analyze_video_with_ark(
                    video_path, message, "录屏视频"
                )
            else:
                # 使用本地模型分析
                analysis_result = await self._analyze_video_with_local_model(
                    video_path, message, "录屏视频"
                )

            return analysis_result

        except Exception as e:
            logger.error(f"录屏视频分析失败: {str(e)}")
            return self._create_default_analysis_result("screen_recording")

    async def _analyze_demo_video(
        self,
        video_path: Path,
        message: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """分析演示视频"""
        try:
            await self.send_response("🎯 正在分析演示视频...")

            if self.ark_client and self.ark_model:
                analysis_result = await self._analyze_video_with_ark(
                    video_path, message, "演示视频"
                )
            else:
                analysis_result = await self._analyze_video_with_local_model(
                    video_path, message, "演示视频"
                )

            return analysis_result

        except Exception as e:
            logger.error(f"演示视频分析失败: {str(e)}")
            return self._create_default_analysis_result("demo_video")

    async def _analyze_generic_video(
        self,
        video_path: Path,
        message: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """通用视频分析"""
        try:
            await self.send_response("🔍 正在进行通用视频分析...")

            if self.ark_client and self.ark_model:
                analysis_result = await self._analyze_video_with_ark(
                    video_path, message, "通用视频"
                )
            else:
                analysis_result = await self._analyze_video_with_local_model(
                    video_path, message, "通用视频"
                )

            return analysis_result

        except Exception as e:
            logger.error(f"通用视频分析失败: {str(e)}")
            return self._create_default_analysis_result("generic")

    async def _analyze_video_with_ark(
        self,
        video_path: Path,
        message: VideoAnalysisRequest,
        video_type_desc: str
    ) -> VideoAnalysisResult:
        """使用Volcengine Ark SDK分析视频"""
        try:
            await self.send_response(f"🚀 使用Volcengine Ark分析{video_type_desc}...")

            # 构建分析提示词
            analysis_prompt = self._build_video_analysis_prompt(message, video_type_desc)

            # 创建视频分析请求
            response = self.ark_client.chat.completions.create(
                model=self.ark_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": f"file://{video_path.absolute()}"
                                }
                            },
                            {
                                "type": "text",
                                "text": analysis_prompt
                            }
                        ]
                    }
                ]
            )

            # 解析响应
            analysis_content = response.choices[0].message.content
            return self._parse_ark_analysis_result(analysis_content)

        except Exception as e:
            logger.error(f"Volcengine Ark视频分析失败: {str(e)}")
            # 降级到本地模型
            return await self._analyze_video_with_local_model(video_path, message, video_type_desc)

    async def _analyze_video_with_local_model(
        self,
        video_path: Path,
        message: VideoAnalysisRequest,
        video_type_desc: str
    ) -> VideoAnalysisResult:
        """使用本地模型分析视频"""
        try:
            await self.send_response(f"🤖 使用本地模型分析{video_type_desc}...")

            # 提取关键帧
            key_frames = await self._extract_key_frames(video_path)

            # 使用QwenVL模型分析关键帧
            if self.model_client_instance:
                analysis_result = await self._analyze_frames_with_qwenvl(
                    key_frames, message, video_type_desc
                )
            else:
                # 创建基础分析结果
                analysis_result = self._create_default_analysis_result(video_type_desc)

            return analysis_result

        except Exception as e:
            logger.error(f"本地模型视频分析失败: {str(e)}")
            return self._create_default_analysis_result(video_type_desc)

    def _build_video_analysis_prompt(
        self,
        message: VideoAnalysisRequest,
        video_type_desc: str
    ) -> str:
        """构建视频分析提示词"""
        prompt = f"""
请分析这个{video_type_desc}，提取以下信息：

1. 用户操作序列：
   - 识别用户的每个操作步骤（点击、输入、滚动等）
   - 记录操作的目标元素和位置
   - 分析操作的时间顺序

2. UI元素识别：
   - 识别界面中的按钮、输入框、菜单等元素
   - 记录元素的位置、类型和属性
   - 分析元素之间的关系

3. 业务流程：
   - 识别完整的业务操作流程
   - 分析流程的逻辑关系
   - 提取关键的业务节点

4. 测试场景：
   - 基于用户操作生成测试场景
   - 包括正常流程和异常情况
   - 考虑边界条件和错误处理

请以JSON格式返回分析结果，包含以下字段：
- user_actions: 用户操作序列
- ui_elements: UI元素列表
- business_flows: 业务流程
- test_scenarios: 测试场景
- key_frames: 关键帧信息
- analysis_summary: 分析摘要
- confidence_score: 分析置信度(0-1)

分析目标：{message.analysis_target or '生成测试用例'}
视频描述：{message.description or '无'}
"""
        return prompt.strip()

    def _parse_ark_analysis_result(self, analysis_content: str) -> VideoAnalysisResult:
        """解析Volcengine Ark分析结果"""
        try:
            # 尝试解析JSON
            result_data = json.loads(analysis_content)

            return VideoAnalysisResult(
                video_type="analyzed",
                duration=0.0,
                user_actions=result_data.get("user_actions", []),
                ui_elements=result_data.get("ui_elements", []),
                business_flows=result_data.get("business_flows", []),
                test_scenarios=result_data.get("test_scenarios", []),
                key_frames=result_data.get("key_frames", []),
                analysis_summary=result_data.get("analysis_summary", ""),
                confidence_score=result_data.get("confidence_score", 0.8)
            )

        except json.JSONDecodeError:
            logger.warning("Ark返回结果不是有效JSON，使用文本解析")
            return VideoAnalysisResult(
                video_type="analyzed",
                duration=0.0,
                analysis_summary=analysis_content,
                confidence_score=0.6
            )

    def _create_default_analysis_result(self, video_type: str) -> VideoAnalysisResult:
        """创建默认分析结果"""
        return VideoAnalysisResult(
            video_type=video_type,
            duration=0.0,
            user_actions=[],
            ui_elements=[],
            business_flows=[],
            test_scenarios=[],
            key_frames=[],
            analysis_summary="视频分析完成，但未能提取详细信息",
            confidence_score=0.3
        )

    async def _extract_key_frames(self, video_path: Path) -> List[str]:
        """提取视频关键帧"""
        try:
            # 这里可以使用ffmpeg或opencv提取关键帧
            # 暂时返回空列表
            await self.send_response("🎞️ 正在提取关键帧...")
            return []
        except Exception as e:
            logger.warning(f"提取关键帧失败: {str(e)}")
            return []

    async def _analyze_frames_with_qwenvl(
        self,
        key_frames: List[str],
        message: VideoAnalysisRequest,
        video_type_desc: str
    ) -> VideoAnalysisResult:
        """使用QwenVL模型分析关键帧"""
        try:
            await self.send_response("🧠 使用QwenVL分析关键帧...")

            # 如果没有关键帧，创建基础结果
            if not key_frames:
                return self._create_default_analysis_result(video_type_desc)

            # 构建多模态消息
            analysis_prompt = self._build_frame_analysis_prompt(message, video_type_desc)

            # 这里可以调用QwenVL模型分析帧序列
            # 暂时返回基础结果
            return self._create_default_analysis_result(video_type_desc)

        except Exception as e:
            logger.error(f"QwenVL帧分析失败: {str(e)}")
            return self._create_default_analysis_result(video_type_desc)

    def _build_frame_analysis_prompt(
        self,
        message: VideoAnalysisRequest,
        video_type_desc: str
    ) -> str:
        """构建帧分析提示词"""
        return f"""
请分析这些视频关键帧，识别用户操作序列和UI元素：

视频类型：{video_type_desc}
分析目标：{message.analysis_target or '生成测试用例'}
视频描述：{message.description or '无'}

请提取：
1. 用户操作步骤
2. UI界面元素
3. 操作流程
4. 测试场景

以JSON格式返回结果。
"""

    async def _generate_test_cases_from_video(
        self,
        analysis_result: VideoAnalysisResult,
        message: VideoAnalysisRequest
    ) -> List[TestCaseData]:
        """根据视频分析结果生成测试用例"""
        try:
            await self.send_response("📝 正在生成测试用例...")

            test_cases = []

            # 基于用户操作生成测试用例
            for i, action in enumerate(analysis_result.user_actions):
                test_case = TestCaseData(
                    id=str(uuid.uuid4()),
                    title=f"测试用例 {i+1}: {action.get('description', '用户操作')}",
                    description=action.get('description', ''),
                    priority="medium",
                    category="functional",
                    steps=[
                        {
                            "step_number": 1,
                            "action": action.get('action', ''),
                            "expected_result": action.get('expected_result', ''),
                            "data": action.get('data', {})
                        }
                    ],
                    expected_results=[action.get('expected_result', '')],
                    test_data={},
                    tags=["video_generated", analysis_result.video_type],
                    source="video_analysis",
                    created_at=datetime.now().isoformat()
                )
                test_cases.append(test_case)

            # 基于业务流程生成测试用例
            for i, flow in enumerate(analysis_result.business_flows):
                test_case = TestCaseData(
                    id=str(uuid.uuid4()),
                    title=f"业务流程测试 {i+1}: {flow.get('name', '业务流程')}",
                    description=flow.get('description', ''),
                    priority="high",
                    category="business",
                    steps=flow.get('steps', []),
                    expected_results=flow.get('expected_results', []),
                    test_data={},
                    tags=["video_generated", "business_flow"],
                    source="video_analysis",
                    created_at=datetime.now().isoformat()
                )
                test_cases.append(test_case)

            # 基于测试场景生成测试用例
            for i, scenario in enumerate(analysis_result.test_scenarios):
                test_case = TestCaseData(
                    id=str(uuid.uuid4()),
                    title=f"场景测试 {i+1}: {scenario.get('name', '测试场景')}",
                    description=scenario.get('description', ''),
                    priority=scenario.get('priority', 'medium'),
                    category=scenario.get('category', 'functional'),
                    steps=scenario.get('steps', []),
                    expected_results=scenario.get('expected_results', []),
                    test_data=scenario.get('test_data', {}),
                    tags=["video_generated", "scenario"],
                    source="video_analysis",
                    created_at=datetime.now().isoformat()
                )
                test_cases.append(test_case)

            await self.send_response(f"✅ 生成了 {len(test_cases)} 个测试用例")
            return test_cases

        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            return []

    # 添加其他视频类型的分析方法
    async def _analyze_tutorial_video(
        self,
        video_path: Path,
        message: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """分析教程视频"""
        try:
            await self.send_response("📚 正在分析教程视频...")
            return await self._analyze_generic_video(video_path, message)
        except Exception as e:
            logger.error(f"教程视频分析失败: {str(e)}")
            return self._create_default_analysis_result("tutorial_video")

    async def _analyze_test_execution(
        self,
        video_path: Path,
        message: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """分析测试执行视频"""
        try:
            await self.send_response("🧪 正在分析测试执行视频...")
            return await self._analyze_generic_video(video_path, message)
        except Exception as e:
            logger.error(f"测试执行视频分析失败: {str(e)}")
            return self._create_default_analysis_result("test_execution")

    async def _analyze_user_journey(
        self,
        video_path: Path,
        message: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """分析用户旅程视频"""
        try:
            await self.send_response("🛤️ 正在分析用户旅程视频...")
            return await self._analyze_generic_video(video_path, message)
        except Exception as e:
            logger.error(f"用户旅程视频分析失败: {str(e)}")
            return self._create_default_analysis_result("user_journey")
