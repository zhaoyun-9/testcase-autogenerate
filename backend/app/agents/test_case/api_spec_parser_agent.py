"""
API规范解析智能体
负责解析Swagger/OpenAPI规范文件，生成API测试用例
"""
import uuid
import json
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import (
    ApiSpecParseRequest, ApiSpecParseResponse,
    TestCaseGenerationRequest, TestCaseData
)
from app.core.enums import TestType, TestLevel, Priority, InputSource


class ApiEndpoint(BaseModel):
    """API端点信息"""
    path: str = Field(..., description="API路径")
    method: str = Field(..., description="HTTP方法")
    summary: str = Field("", description="API摘要")
    description: str = Field("", description="API描述")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="参数列表")
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体")
    responses: Dict[str, Any] = Field(default_factory=dict, description="响应定义")
    tags: List[str] = Field(default_factory=list, description="标签")
    security: List[Dict[str, Any]] = Field(default_factory=list, description="安全要求")


class ApiSpecParseResult(BaseModel):
    """API规范解析结果"""
    spec_version: str = Field("", description="规范版本")
    title: str = Field("", description="API标题")
    version: str = Field("", description="API版本")
    description: str = Field("", description="API描述")
    base_url: str = Field("", description="基础URL")
    endpoints: List[ApiEndpoint] = Field(default_factory=list, description="API端点列表")
    schemas: Dict[str, Any] = Field(default_factory=dict, description="数据模型")
    security_schemes: Dict[str, Any] = Field(default_factory=dict, description="安全方案")
    confidence_score: float = Field(0.0, description="解析置信度")


@type_subscription(topic_type=TopicTypes.API_SPEC_PARSER.value)
class ApiSpecParserAgent(BaseAgent):
    """API规范解析智能体，负责解析Swagger/OpenAPI规范文件"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化API规范解析智能体"""
        super().__init__(
            agent_id=AgentTypes.API_SPEC_PARSER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.API_SPEC_PARSER.value, "API规范解析智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )
        
        # 支持的规范格式
        self.supported_formats = {
            '.json': self._parse_json_spec,
            '.yaml': self._parse_yaml_spec,
            '.yml': self._parse_yaml_spec
        }
        
        logger.info(f"API规范解析智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_api_spec_parse_request(
        self, 
        message: ApiSpecParseRequest, 
        ctx: MessageContext
    ) -> None:
        """处理API规范解析请求"""
        try:
            logger.info(f"开始处理API规范解析请求: {message.session_id}")
            
            await self.send_response(
                f"🔍 开始解析API规范: {message.file_name}",
                region="process"
            )
            
            # 解析API规范
            parse_result = await self._parse_api_spec(message)
            
            # 生成测试用例
            test_cases = await self._generate_test_cases_from_api_spec(
                parse_result, message
            )
            
            # 构建响应
            response = ApiSpecParseResponse(
                session_id=message.session_id,
                spec_id=str(uuid.uuid4()),
                file_name=message.file_name,
                file_path=message.file_path,
                parse_result=parse_result.model_dump(),
                test_cases=test_cases,
                processing_time=0.0,
                created_at=datetime.now().isoformat()
            )
            
            await self.send_response(
                f"✅ API规范解析完成，发现 {len(parse_result.endpoints)} 个端点",
                is_final=True,
                result=response.model_dump()
            )
            
            # 发送到测试用例生成智能体
            await self._send_to_test_case_generator(response)
            
        except Exception as e:
            logger.error(f"API规范解析失败: {str(e)}")
            await self.send_response(
                f"❌ API规范解析失败: {str(e)}",
                is_final=True,
                error=str(e)
            )

    async def _parse_api_spec(self, message: ApiSpecParseRequest) -> ApiSpecParseResult:
        """解析API规范文件"""
        try:
            file_path = Path(message.file_path)
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.supported_formats:
                raise ValueError(f"不支持的API规范格式: {file_extension}")
            
            await self.send_response(f"📖 正在解析 {file_extension} 格式的API规范...")
            
            # 调用对应的解析方法
            parser_func = self.supported_formats[file_extension]
            spec_data = await parser_func(file_path)
            
            # 解析规范内容
            parse_result = await self._analyze_api_spec_content(spec_data, message)
            
            return parse_result
            
        except Exception as e:
            logger.error(f"API规范解析失败: {str(e)}")
            raise

    async def _parse_json_spec(self, file_path: Path) -> Dict[str, Any]:
        """解析JSON格式的API规范"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON规范解析失败: {str(e)}")
            raise

    async def _parse_yaml_spec(self, file_path: Path) -> Dict[str, Any]:
        """解析YAML格式的API规范"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"YAML规范解析失败: {str(e)}")
            raise

    async def _analyze_api_spec_content(
        self, 
        spec_data: Dict[str, Any], 
        message: ApiSpecParseRequest
    ) -> ApiSpecParseResult:
        """分析API规范内容"""
        try:
            # 检测规范版本
            spec_version = self._detect_spec_version(spec_data)
            
            await self.send_response(f"📋 检测到 {spec_version} 规范")
            
            # 提取基本信息
            info = spec_data.get('info', {})
            title = info.get('title', message.file_name)
            version = info.get('version', '1.0.0')
            description = info.get('description', '')
            
            # 提取服务器信息
            base_url = self._extract_base_url(spec_data)
            
            # 解析API端点
            endpoints = await self._parse_endpoints(spec_data, spec_version)
            
            await self.send_response(f"🔗 解析到 {len(endpoints)} 个API端点")
            
            # 提取数据模型
            schemas = self._extract_schemas(spec_data, spec_version)
            
            # 提取安全方案
            security_schemes = self._extract_security_schemes(spec_data, spec_version)
            
            return ApiSpecParseResult(
                spec_version=spec_version,
                title=title,
                version=version,
                description=description,
                base_url=base_url,
                endpoints=endpoints,
                schemas=schemas,
                security_schemes=security_schemes,
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"API规范内容分析失败: {str(e)}")
            raise

    def _detect_spec_version(self, spec_data: Dict[str, Any]) -> str:
        """检测API规范版本"""
        if 'openapi' in spec_data:
            return f"OpenAPI {spec_data['openapi']}"
        elif 'swagger' in spec_data:
            return f"Swagger {spec_data['swagger']}"
        else:
            return "Unknown"

    def _extract_base_url(self, spec_data: Dict[str, Any]) -> str:
        """提取基础URL"""
        # OpenAPI 3.x
        if 'servers' in spec_data and spec_data['servers']:
            return spec_data['servers'][0].get('url', '')
        
        # Swagger 2.x
        if 'host' in spec_data:
            scheme = spec_data.get('schemes', ['http'])[0]
            host = spec_data['host']
            base_path = spec_data.get('basePath', '')
            return f"{scheme}://{host}{base_path}"
        
        return ""

    async def _parse_endpoints(
        self, 
        spec_data: Dict[str, Any], 
        spec_version: str
    ) -> List[ApiEndpoint]:
        """解析API端点"""
        try:
            endpoints = []
            paths = spec_data.get('paths', {})
            
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                        endpoint = ApiEndpoint(
                            path=path,
                            method=method.upper(),
                            summary=operation.get('summary', ''),
                            description=operation.get('description', ''),
                            parameters=operation.get('parameters', []),
                            request_body=operation.get('requestBody'),
                            responses=operation.get('responses', {}),
                            tags=operation.get('tags', []),
                            security=operation.get('security', [])
                        )
                        endpoints.append(endpoint)
            
            return endpoints
            
        except Exception as e:
            logger.error(f"解析API端点失败: {str(e)}")
            return []

    def _extract_schemas(self, spec_data: Dict[str, Any], spec_version: str) -> Dict[str, Any]:
        """提取数据模型"""
        try:
            # OpenAPI 3.x
            if 'components' in spec_data and 'schemas' in spec_data['components']:
                return spec_data['components']['schemas']
            
            # Swagger 2.x
            if 'definitions' in spec_data:
                return spec_data['definitions']
            
            return {}
            
        except Exception as e:
            logger.error(f"提取数据模型失败: {str(e)}")
            return {}

    def _extract_security_schemes(self, spec_data: Dict[str, Any], spec_version: str) -> Dict[str, Any]:
        """提取安全方案"""
        try:
            # OpenAPI 3.x
            if 'components' in spec_data and 'securitySchemes' in spec_data['components']:
                return spec_data['components']['securitySchemes']
            
            # Swagger 2.x
            if 'securityDefinitions' in spec_data:
                return spec_data['securityDefinitions']
            
            return {}
            
        except Exception as e:
            logger.error(f"提取安全方案失败: {str(e)}")
            return {}

    async def _generate_test_cases_from_api_spec(
        self, 
        parse_result: ApiSpecParseResult,
        message: ApiSpecParseRequest
    ) -> List[TestCaseData]:
        """从API规范生成测试用例"""
        test_cases = []
        
        try:
            # 为每个API端点生成测试用例
            for endpoint in parse_result.endpoints:
                # 基础功能测试用例
                basic_test_case = TestCaseData(
                    title=f"测试 {endpoint.method} {endpoint.path}",
                    description=f"测试API端点: {endpoint.summary or endpoint.description}",
                    test_type=TestType.INTERFACE,
                    test_level=TestLevel.INTEGRATION,
                    priority=self._determine_api_priority(endpoint),
                    input_source=InputSource.API_SPEC,
                    source_metadata={
                        "api_spec": message.file_name,
                        "endpoint_path": endpoint.path,
                        "endpoint_method": endpoint.method,
                        "endpoint_tags": endpoint.tags
                    },
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(basic_test_case)
                
                # 参数验证测试用例
                if endpoint.parameters:
                    param_test_case = TestCaseData(
                        title=f"测试 {endpoint.method} {endpoint.path} 参数验证",
                        description=f"测试API参数验证逻辑",
                        test_type=TestType.INTERFACE,
                        test_level=TestLevel.INTEGRATION,
                        priority=Priority.P2,
                        input_source=InputSource.API_SPEC,
                        source_metadata={
                            "api_spec": message.file_name,
                            "endpoint_path": endpoint.path,
                            "endpoint_method": endpoint.method,
                            "test_focus": "parameter_validation"
                        },
                        ai_confidence=parse_result.confidence_score
                    )
                    test_cases.append(param_test_case)
                
                # 错误处理测试用例
                error_test_case = TestCaseData(
                    title=f"测试 {endpoint.method} {endpoint.path} 错误处理",
                    description=f"测试API错误响应处理",
                    test_type=TestType.INTERFACE,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P2,
                    input_source=InputSource.API_SPEC,
                    source_metadata={
                        "api_spec": message.file_name,
                        "endpoint_path": endpoint.path,
                        "endpoint_method": endpoint.method,
                        "test_focus": "error_handling"
                    },
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(error_test_case)
                
                # 安全测试用例（如果有安全要求）
                if endpoint.security:
                    security_test_case = TestCaseData(
                        title=f"测试 {endpoint.method} {endpoint.path} 安全认证",
                        description=f"测试API安全认证机制",
                        test_type=TestType.SECURITY,
                        test_level=TestLevel.INTEGRATION,
                        priority=Priority.P1,
                        input_source=InputSource.API_SPEC,
                        source_metadata={
                            "api_spec": message.file_name,
                            "endpoint_path": endpoint.path,
                            "endpoint_method": endpoint.method,
                            "test_focus": "security"
                        },
                        ai_confidence=parse_result.confidence_score
                    )
                    test_cases.append(security_test_case)
            
            # 生成性能测试用例
            if len(parse_result.endpoints) > 0:
                performance_test_case = TestCaseData(
                    title=f"API性能测试 - {parse_result.title}",
                    description="测试API整体性能表现",
                    test_type=TestType.PERFORMANCE,
                    test_level=TestLevel.SYSTEM,
                    priority=Priority.P2,
                    input_source=InputSource.API_SPEC,
                    source_metadata={
                        "api_spec": message.file_name,
                        "test_focus": "performance",
                        "endpoints_count": len(parse_result.endpoints)
                    },
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(performance_test_case)
            
            logger.info(f"从API规范生成了 {len(test_cases)} 个测试用例")
            return test_cases
            
        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            return []

    def _determine_api_priority(self, endpoint: ApiEndpoint) -> Priority:
        """确定API测试优先级"""
        # 根据HTTP方法确定优先级
        method_priority = {
            'POST': Priority.P1,    # 创建操作，高优先级
            'PUT': Priority.P1,     # 更新操作，高优先级
            'DELETE': Priority.P1,  # 删除操作，高优先级
            'GET': Priority.P2,     # 查询操作，中优先级
            'PATCH': Priority.P2,   # 部分更新，中优先级
            'HEAD': Priority.P3,    # 头部信息，低优先级
            'OPTIONS': Priority.P3  # 选项信息，低优先级
        }
        
        # 根据标签调整优先级
        if any(tag.lower() in ['auth', 'login', 'security'] for tag in endpoint.tags):
            return Priority.P0  # 安全相关，最高优先级
        
        return method_priority.get(endpoint.method, Priority.P2)

    async def _send_to_test_case_generator(self, response: ApiSpecParseResponse):
        """发送到测试用例生成智能体"""
        try:
            generation_request = TestCaseGenerationRequest(
                session_id=response.session_id,
                source_type="api_spec",
                source_data=response.model_dump(),
                test_cases=response.test_cases,
                generation_config={
                    "auto_save": True,
                    "generate_mind_map": True
                }
            )
            
            await self.publish_message(
                generation_request,
                topic_id=TopicId(type=TopicTypes.TEST_CASE_GENERATOR.value, source=self.id.key)
            )
            
            logger.info(f"已发送到测试用例生成智能体: {response.session_id}")
            
        except Exception as e:
            logger.error(f"发送到测试用例生成智能体失败: {str(e)}")
