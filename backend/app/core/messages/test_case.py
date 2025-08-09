"""
测试用例相关的消息定义
定义智能体之间通信的消息格式
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.core.enums import TestType, TestLevel, Priority, InputSource


# 基础消息类
class BaseMessage(BaseModel):
    """基础消息类"""
    session_id: str = Field(..., description="会话ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")


# 测试用例数据模型
class TestCaseData(BaseModel):
    """测试用例数据"""
    title: str = Field(..., description="测试用例标题")
    description: Optional[Union[str, List[str]]] = Field(None, description="测试用例描述")
    preconditions: Optional[Union[str, List[str]]] = Field(None, description="前置条件")
    test_steps: Optional[List[Dict[str, Any]]] = Field(None, description="测试步骤")
    expected_results: Optional[Union[str, List[str]]] = Field(None, description="预期结果")
    test_type: TestType = Field(..., description="测试类型")
    test_level: TestLevel = Field(..., description="测试级别")
    priority: Priority = Field(Priority.P2, description="优先级")
    input_source: InputSource = Field(..., description="输入源类型")
    source_file_path: Optional[str] = Field(None, description="源文件路径")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="源数据元信息")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    ai_confidence: Optional[float] = Field(None, description="AI置信度")

    @field_validator('description', 'preconditions', 'expected_results')
    @classmethod
    def normalize_string_fields(cls, v):
        """标准化字符串字段，将列表转换为字符串"""
        if v is None:
            return None
        elif isinstance(v, list):
            # 过滤掉 None 值，然后用换行符连接
            return "\n".join(str(item) for item in v if item is not None)
        else:
            return str(v)


# 思维导图相关消息
class MindMapNode(BaseModel):
    """思维导图节点"""
    id: str = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    type: str = Field(..., description="节点类型")
    level: int = Field(0, description="节点层级")
    data: Dict[str, Any] = Field(default_factory=dict, description="节点数据")
    style: Dict[str, Any] = Field(default_factory=dict, description="节点样式")


class MindMapEdge(BaseModel):
    """思维导图边"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    type: str = Field("default", description="边类型")
    style: Dict[str, Any] = Field(default_factory=dict, description="边样式")


class MindMapData(BaseModel):
    """思维导图数据"""
    nodes: List[MindMapNode] = Field(..., description="节点列表")
    edges: List[MindMapEdge] = Field(..., description="边列表")


# 文档解析相关消息
class DocumentParseRequest(BaseMessage):
    """文档解析请求"""
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    document_type: Optional[str] = Field(None, description="文档类型")
    analysis_target: Optional[str] = Field(None, description="分析目标")


class DocumentParseResponse(BaseMessage):
    """文档解析响应"""
    document_id: str = Field(..., description="文档ID")
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    parse_result: Dict[str, Any] = Field(..., description="解析结果")
    test_cases: List[TestCaseData] = Field(..., description="生成的测试用例")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 图片分析相关消息
class ImageAnalysisRequest(BaseMessage):
    """图片分析请求"""
    image_name: str = Field(..., description="图片名称")
    image_path: str = Field(..., description="图片路径")
    image_type: Optional[str] = Field(None, description="图片类型")
    description: Optional[str] = Field(None, description="图片描述")
    analysis_target: Optional[str] = Field(None, description="分析目标")


class ImageAnalysisResponse(BaseMessage):
    """图片分析响应"""
    image_id: str = Field(..., description="图片ID")
    image_name: str = Field(..., description="图片名称")
    image_path: str = Field(..., description="图片路径")
    analysis_result: Dict[str, Any] = Field(..., description="分析结果")
    test_cases: List[TestCaseData] = Field(..., description="生成的测试用例")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# API规范解析相关消息
class ApiSpecParseRequest(BaseMessage):
    """API规范解析请求"""
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    spec_type: Optional[str] = Field(None, description="规范类型")
    analysis_target: Optional[str] = Field(None, description="分析目标")


class ApiSpecParseResponse(BaseMessage):
    """API规范解析响应"""
    spec_id: str = Field(..., description="规范ID")
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    parse_result: Dict[str, Any] = Field(..., description="解析结果")
    test_cases: List[TestCaseData] = Field(..., description="生成的测试用例")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 数据库Schema解析相关消息
class DatabaseSchemaParseRequest(BaseMessage):
    """数据库Schema解析请求"""
    file_name: str = Field(..., description="Schema文件名称")
    file_path: str = Field(..., description="Schema文件路径")
    database_type: Optional[str] = Field(None, description="数据库类型")
    database_name: Optional[str] = Field(None, description="数据库名称")
    connection_string: Optional[str] = Field(None, description="数据库连接字符串")
    schema_sql: Optional[str] = Field(None, description="Schema SQL语句")
    analysis_target: Optional[str] = Field(None, description="分析目标")


class DatabaseSchemaParseResponse(BaseMessage):
    """数据库Schema解析响应"""
    schema_id: str = Field(..., description="Schema ID")
    database_name: str = Field(..., description="数据库名称")
    database_type: str = Field(..., description="数据库类型")
    parse_result: Dict[str, Any] = Field(..., description="解析结果")
    test_cases: List[TestCaseData] = Field(..., description="生成的测试用例")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 录屏分析相关消息
class VideoAnalysisRequest(BaseMessage):
    """录屏分析请求"""
    video_name: str = Field(..., description="视频名称")
    video_path: str = Field(..., description="视频路径")
    video_type: Optional[str] = Field(None, description="视频类型")
    description: Optional[str] = Field(None, description="视频描述")
    analysis_target: Optional[str] = Field(None, description="分析目标")


# 直接需求输入相关消息
class DirectRequirementRequest(BaseMessage):
    """直接需求输入请求"""
    requirement_text: str = Field(..., description="需求文本")
    requirement_title: Optional[str] = Field(None, description="需求标题")
    analysis_target: Optional[str] = Field("生成测试用例", description="分析目标")


class DirectRequirementResponse(BaseMessage):
    """直接需求输入响应"""
    requirement_id: str = Field(..., description="需求ID")
    requirement_text: str = Field(..., description="需求文本")
    analysis_result: Dict[str, Any] = Field(..., description="分析结果")
    test_cases: List[TestCaseData] = Field(..., description="生成的测试用例")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


class VideoAnalysisResponse(BaseMessage):
    """录屏分析响应"""
    video_id: str = Field(..., description="视频ID")
    video_name: str = Field(..., description="视频名称")
    video_path: str = Field(..., description="视频路径")
    analysis_result: Dict[str, Any] = Field(..., description="分析结果")
    test_cases: List[TestCaseData] = Field(..., description="生成的测试用例")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 测试用例生成相关消息
class TestCaseGenerationRequest(BaseMessage):
    """测试用例生成请求"""
    source_type: str = Field(..., description="源类型")
    source_data: Dict[str, Any] = Field(..., description="源数据")
    test_cases: List[TestCaseData] = Field(..., description="测试用例数据")
    generation_config: Dict[str, Any] = Field(default_factory=dict, description="生成配置")


class TestCaseGenerationResponse(BaseMessage):
    """测试用例生成响应"""
    generation_id: str = Field(..., description="生成ID")
    source_type: str = Field(..., description="源类型")
    generated_count: int = Field(..., description="生成数量")
    test_case_ids: List[str] = Field(..., description="测试用例ID列表")
    mind_map_generated: bool = Field(False, description="是否生成思维导图")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 思维导图生成相关消息
class MindMapGenerationRequest(BaseMessage):
    """思维导图生成请求"""
    test_case_ids: List[str] = Field(..., description="测试用例ID列表")
    source_data: Dict[str, Any] = Field(..., description="源数据")
    generation_config: Dict[str, Any] = Field(default_factory=dict, description="生成配置")


class MindMapGenerationResponse(BaseMessage):
    """思维导图生成响应"""
    mind_map_id: str = Field(..., description="思维导图ID")
    mind_map_data: MindMapData = Field(..., description="思维导图数据")
    layout_config: Dict[str, Any] = Field(..., description="布局配置")
    nodes_count: int = Field(..., description="节点数量")
    edges_count: int = Field(..., description="边数量")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# Excel导出相关消息
class ExcelExportRequest(BaseMessage):
    """Excel导出请求"""
    test_case_ids: List[str] = Field(..., description="测试用例ID列表")
    export_config: Dict[str, Any] = Field(default_factory=dict, description="导出配置")
    template_type: str = Field("standard", description="模板类型")


class ExcelExportResponse(BaseMessage):
    """Excel导出响应"""
    export_id: str = Field(..., description="导出ID")
    file_path: str = Field(..., description="文件路径")
    file_name: str = Field(..., description="文件名")
    exported_count: int = Field(..., description="导出数量")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 批量处理相关消息
class BatchProcessRequest(BaseMessage):
    """批量处理请求"""
    process_type: str = Field(..., description="处理类型")
    input_files: List[Dict[str, Any]] = Field(..., description="输入文件列表")
    process_config: Dict[str, Any] = Field(default_factory=dict, description="处理配置")


class BatchProcessResponse(BaseMessage):
    """批量处理响应"""
    process_id: str = Field(..., description="处理ID")
    process_type: str = Field(..., description="处理类型")
    total_files: int = Field(..., description="总文件数")
    processed_files: int = Field(..., description="已处理文件数")
    failed_files: int = Field(..., description="失败文件数")
    results: List[Dict[str, Any]] = Field(..., description="处理结果")
    processing_time: float = Field(..., description="处理时间")
    created_at: str = Field(..., description="创建时间")


# 系统状态相关消息
class SystemStatusRequest(BaseMessage):
    """系统状态请求"""
    check_type: str = Field("all", description="检查类型")


class SystemStatusResponse(BaseMessage):
    """系统状态响应"""
    status: str = Field(..., description="系统状态")
    agents_status: Dict[str, Any] = Field(..., description="智能体状态")
    database_status: Dict[str, Any] = Field(..., description="数据库状态")
    performance_metrics: Dict[str, Any] = Field(..., description="性能指标")
    created_at: str = Field(..., description="创建时间")
