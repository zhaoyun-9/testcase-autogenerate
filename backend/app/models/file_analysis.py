"""
文件分析相关的数据模型
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FileAnalysisRequest(BaseModel):
    """文件分析请求"""
    filename: str = Field(..., description="文件名")
    content_type: Optional[str] = Field(None, description="MIME类型")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    description: Optional[str] = Field(None, description="文件描述")


class FileAnalysisResponse(BaseModel):
    """文件分析响应"""
    fileType: str = Field(..., description="文件类型(扩展名)")
    fileCategory: str = Field(..., description="文件类别")
    recommendedAgent: str = Field(..., description="推荐的智能体")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    supportedFormats: List[str] = Field(..., description="支持的格式列表")
    fileSizeMB: float = Field(..., description="文件大小(MB)")
    contentType: Optional[str] = Field(None, description="MIME类型")
    categoryInfo: Dict[str, Any] = Field(..., description="类别详细信息")
    analysisDetails: Optional[Dict[str, Any]] = Field(None, description="分析详情")


class SupportedFileTypesResponse(BaseModel):
    """支持的文件类型响应"""
    categories: Dict[str, Dict[str, Any]] = Field(..., description="文件类别信息")
    totalCategories: int = Field(..., description="总类别数")
    maxFileSize: int = Field(..., description="最大文件大小(MB)")
    supportedExtensions: List[str] = Field(..., description="所有支持的扩展名")


class FileValidationRequest(BaseModel):
    """文件验证请求"""
    files: List[Dict[str, Any]] = Field(..., description="文件信息列表")
    maxTotalSize: Optional[float] = Field(500, description="最大总大小(MB)")


class FileValidationResponse(BaseModel):
    """文件验证响应"""
    files: List[Dict[str, Any]] = Field(..., description="文件验证结果")
    totalSizeMB: float = Field(..., description="总文件大小(MB)")
    totalSizeValid: bool = Field(..., description="总大小是否有效")
    validFiles: int = Field(..., description="有效文件数")
    totalFiles: int = Field(..., description="总文件数")


class AgentRecommendation(BaseModel):
    """智能体推荐"""
    agent_type: str = Field(..., description="智能体类型")
    confidence: float = Field(..., description="推荐置信度", ge=0.0, le=1.0)
    reason: str = Field(..., description="推荐理由")
    capabilities: List[str] = Field(..., description="智能体能力列表")
    estimated_processing_time: Optional[int] = Field(None, description="预估处理时间(秒)")


class FileProcessingConfig(BaseModel):
    """文件处理配置"""
    analysis_target: str = Field(..., description="分析目标")
    generate_mindmap: bool = Field(True, description="是否生成思维导图")
    export_excel: bool = Field(False, description="是否导出Excel")
    max_test_cases: int = Field(50, description="最大测试用例数", ge=1, le=200)
    tags: List[str] = Field(default_factory=list, description="标签列表")
    priority: str = Field("P2", description="优先级")
    test_level: str = Field("system", description="测试级别")


class FileUploadResult(BaseModel):
    """文件上传结果"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size_mb: float = Field(..., description="文件大小(MB)")
    selected_agent: str = Field(..., description="选择的智能体")
    upload_time: str = Field(..., description="上传时间")
    status: str = Field(..., description="状态")


class FileProcessingStatus(BaseModel):
    """文件处理状态"""
    file_id: str = Field(..., description="文件ID")
    status: str = Field(..., description="处理状态")
    progress: float = Field(..., description="处理进度", ge=0.0, le=100.0)
    current_stage: str = Field(..., description="当前阶段")
    start_time: str = Field(..., description="开始时间")
    estimated_completion: Optional[str] = Field(None, description="预计完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")


class BatchFileOperation(BaseModel):
    """批量文件操作"""
    operation: str = Field(..., description="操作类型")
    file_ids: List[str] = Field(..., description="文件ID列表")
    config: Optional[Dict[str, Any]] = Field(None, description="操作配置")


class BatchOperationResult(BaseModel):
    """批量操作结果"""
    operation_id: str = Field(..., description="操作ID")
    total_files: int = Field(..., description="总文件数")
    successful_files: int = Field(..., description="成功文件数")
    failed_files: int = Field(..., description="失败文件数")
    results: List[Dict[str, Any]] = Field(..., description="详细结果")
    start_time: str = Field(..., description="开始时间")
    completion_time: Optional[str] = Field(None, description="完成时间")
