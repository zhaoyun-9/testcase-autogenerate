"""
需求数据模型
定义需求相关的数据库表结构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, JSON, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import enum

from .base import Base


# 需求类型枚举
class RequirementType(str, enum.Enum):
    """需求类型"""
    FUNCTIONAL = "functional"           # 功能需求
    NON_FUNCTIONAL = "non_functional"   # 非功能需求
    BUSINESS = "business"               # 业务需求
    TECHNICAL = "technical"             # 技术需求
    INTERFACE = "interface"             # 接口需求
    PERFORMANCE = "performance"         # 性能需求
    SECURITY = "security"               # 安全需求
    USABILITY = "usability"             # 可用性需求


# 需求优先级枚举
class RequirementPriority(str, enum.Enum):
    """需求优先级"""
    HIGH = "high"       # 高优先级
    MEDIUM = "medium"   # 中优先级
    LOW = "low"         # 低优先级


# 需求状态枚举
class RequirementStatus(str, enum.Enum):
    """需求状态"""
    DRAFT = "draft"         # 草稿
    APPROVED = "approved"   # 已批准
    REJECTED = "rejected"   # 已拒绝
    DEPRECATED = "deprecated"  # 已废弃


# 数据库表模型
class Requirement(Base):
    """需求表"""
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(100), nullable=False, comment="需求编号")
    title = Column(String(500), nullable=False, comment="需求标题")
    description = Column(Text, comment="需求描述")
    
    # 分类信息
    requirement_type = Column(String(50), nullable=False, comment="需求类型")
    priority = Column(String(20), default="medium", comment="优先级")
    status = Column(String(20), default="draft", comment="状态")
    
    # 关联信息
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, comment="项目ID")
    document_id = Column(String(36), comment="源文档ID")
    session_id = Column(String(36), comment="会话ID")
    
    # 源信息
    source_file_path = Column(String(500), comment="源文件路径")
    source_section = Column(String(200), comment="源文档章节")
    
    # AI相关信息
    ai_generated = Column(Boolean, default=True, comment="是否AI生成")
    ai_confidence = Column(Float, comment="AI置信度")
    ai_model_info = Column(JSON, comment="AI模型信息")
    
    # 元数据
    extra_metadata = Column(JSON, comment="扩展元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系定义
    test_case_requirements = relationship("TestCaseRequirement", back_populates="requirement")


class TestCaseRequirement(Base):
    """测试用例需求关联表"""
    __tablename__ = "test_case_requirements"

    id = Column(String(36), primary_key=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False, comment="测试用例ID")
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False, comment="需求ID")
    
    # 覆盖信息
    coverage_type = Column(String(50), default="full", comment="覆盖类型: full/partial")
    coverage_description = Column(Text, comment="覆盖描述")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系定义
    requirement = relationship("Requirement", back_populates="test_case_requirements")


# Pydantic模型用于API
class RequirementCreateRequest(BaseModel):
    """创建需求请求模型"""
    requirement_id: str = Field(..., description="需求编号")
    title: str = Field(..., description="需求标题")
    description: Optional[str] = Field(None, description="需求描述")
    requirement_type: RequirementType = Field(..., description="需求类型")
    priority: RequirementPriority = Field(RequirementPriority.MEDIUM, description="优先级")
    status: RequirementStatus = Field(RequirementStatus.DRAFT, description="状态")
    project_id: Optional[str] = Field(None, description="项目ID")
    document_id: Optional[str] = Field(None, description="源文档ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    source_file_path: Optional[str] = Field(None, description="源文件路径")
    source_section: Optional[str] = Field(None, description="源文档章节")
    ai_generated: bool = Field(True, description="是否AI生成")
    ai_confidence: Optional[float] = Field(None, description="AI置信度")
    ai_model_info: Optional[Dict[str, Any]] = Field(None, description="AI模型信息")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


class RequirementResponse(BaseModel):
    """需求响应模型"""
    id: str
    requirement_id: str
    title: str
    description: Optional[str]
    requirement_type: RequirementType
    priority: RequirementPriority
    status: RequirementStatus
    project_id: str
    document_id: Optional[str]
    session_id: Optional[str]
    source_file_path: Optional[str]
    source_section: Optional[str]
    ai_generated: bool
    ai_confidence: Optional[float]
    ai_model_info: Optional[Dict[str, Any]]
    extra_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseRequirementCreateRequest(BaseModel):
    """创建测试用例需求关联请求模型"""
    test_case_id: str = Field(..., description="测试用例ID")
    requirement_id: str = Field(..., description="需求ID")
    coverage_type: str = Field("full", description="覆盖类型")
    coverage_description: Optional[str] = Field(None, description="覆盖描述")


# 简化的测试用例信息模型（避免循环导入）
class TestCaseInfo(BaseModel):
    """测试用例基本信息"""
    id: str
    title: str
    description: Optional[str]
    test_type: str
    test_level: str
    priority: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TestCaseRequirementResponse(BaseModel):
    """测试用例需求关联响应模型"""
    id: str
    test_case_id: str
    requirement_id: str
    coverage_type: str
    coverage_description: Optional[str]
    created_at: datetime
    requirement: Optional[RequirementResponse] = None
    test_case: Optional[TestCaseInfo] = None

    class Config:
        from_attributes = True


class RequirementListResponse(BaseModel):
    """需求列表响应模型"""
    items: List[RequirementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# 需求统计模型
class RequirementCoverageStats(BaseModel):
    """需求覆盖统计"""
    total_requirements: int = Field(..., description="总需求数")
    covered_requirements: int = Field(..., description="已覆盖需求数")
    uncovered_requirements: int = Field(..., description="未覆盖需求数")
    coverage_rate: float = Field(..., description="覆盖率")
    requirements_by_type: Dict[str, int] = Field(..., description="按类型分组的需求数")
    requirements_by_priority: Dict[str, int] = Field(..., description="按优先级分组的需求数")
