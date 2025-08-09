"""
核心消息模块
定义系统中使用的消息类型和流式消息
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class StreamMessage(BaseModel):
    """流式消息基类"""
    message_id: str = Field(..., description="消息ID")
    type: str = Field(..., description="消息类型")
    source: str = Field(..., description="消息源")
    content: str = Field(..., description="消息内容")
    region: str = Field("main", description="消息区域")
    platform: str = Field("test_case", description="平台标识")
    is_final: bool = Field(False, description="是否为最终消息")
    result: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProgressMessage(StreamMessage):
    """进度消息"""
    progress: float = Field(0.0, description="进度百分比 (0-100)")
    stage: str = Field("", description="当前阶段")
    total_stages: int = Field(1, description="总阶段数")
    current_stage: int = Field(1, description="当前阶段编号")


class ErrorMessage(StreamMessage):
    """错误消息"""
    error_code: str = Field("", description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")


class CompletionMessage(StreamMessage):
    """完成消息"""
    success: bool = Field(True, description="是否成功")
    summary: str = Field("", description="处理摘要")
    metrics: Optional[Dict[str, Any]] = Field(None, description="处理指标")


# 导出主要类
__all__ = [
    "StreamMessage",
    "ProgressMessage", 
    "ErrorMessage",
    "CompletionMessage"
]
