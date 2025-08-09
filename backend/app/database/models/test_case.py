"""
测试用例数据模型 (最终版)
匹配最终版数据库结构，极简设计，只保留核心功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, JSON, Enum, ForeignKey, Boolean, DECIMAL, BigInteger
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import enum

from .base import Base


# 导入统一的枚举定义
from app.core.enums import (
    TestType, TestLevel, Priority, TestCaseStatus, InputSource,
    ProjectStatus, SessionType, SessionStatus, UploadSource,
    ExportType, ExportStatus, ConfigType
)


# 数据库表模型 (最终版)

class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProjectStatus, values_callable=lambda obj: [e.value for e in obj]), default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    test_cases = relationship("TestCase", back_populates="project")
    categories = relationship("Category", back_populates="project")
    tags = relationship("Tag", back_populates="project")
    file_uploads = relationship("FileUpload", back_populates="project")
    processing_sessions = relationship("ProcessingSession", back_populates="project")
    mind_maps = relationship("MindMap", back_populates="project")
    export_records = relationship("ExportRecord", back_populates="project")


class Category(Base):
    """测试用例分类表"""
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parent_id = Column(String(36), ForeignKey("categories.id"))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", overlaps="parent")
    test_cases = relationship("TestCase", back_populates="category")


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default='#1890ff')
    project_id = Column(String(36), ForeignKey("projects.id"))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="tags")
    test_case_tags = relationship("TestCaseTag", back_populates="tag")

class TestCase(Base):
    """测试用例主表"""
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    preconditions = Column(Text)
    test_steps = Column(JSON)
    expected_results = Column(Text)

    # 分类信息
    test_type = Column(Enum(TestType), nullable=False)
    test_level = Column(Enum(TestLevel), nullable=False)
    priority = Column(Enum(Priority), default=Priority.P2)
    status = Column(Enum(TestCaseStatus), default=TestCaseStatus.DRAFT)

    # 关联信息
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"))
    session_id = Column(String(36))

    # 输入源信息
    input_source = Column(Enum(InputSource))
    source_file_path = Column(String(500))

    # AI生成信息
    ai_generated = Column(Boolean, default=False)
    ai_confidence = Column(Float)
    ai_model_info = Column(JSON)

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="test_cases")
    category = relationship("Category", back_populates="test_cases")
    test_case_tags = relationship("TestCaseTag", back_populates="test_case")


class TestCaseTag(Base):
    """测试用例标签关联表"""
    __tablename__ = "test_case_tags"

    id = Column(String(36), primary_key=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    test_case = relationship("TestCase", back_populates="test_case_tags")
    tag = relationship("Tag", back_populates="test_case_tags")

class FileUpload(Base):
    """文件上传记录表"""
    __tablename__ = "file_uploads"

    id = Column(String(36), primary_key=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    mime_type = Column(String(100))
    upload_source = Column(String(50), nullable=False)  # 暂时改为字符串，避免枚举序列化问题
    session_id = Column(String(36))
    project_id = Column(String(36), ForeignKey("projects.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="file_uploads")


class ProcessingSession(Base):
    """处理会话表"""
    __tablename__ = "processing_sessions"

    id = Column(String(36), primary_key=True)
    session_type = Column(Enum(SessionType), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.CREATED)
    progress = Column(DECIMAL(5, 2), default=0.00)
    project_id = Column(String(36), ForeignKey("projects.id"))
    input_data = Column(JSON)
    output_data = Column(JSON)
    config_data = Column(JSON)
    agent_type = Column(String(50))
    processing_time = Column(Float)
    error_message = Column(Text)
    generated_count = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 新增字段用于存储智能体关键输出摘要
    agent_logs_summary = Column(JSON)
    key_metrics = Column(JSON)
    processing_stages = Column(JSON)

    # 关联关系
    project = relationship("Project", back_populates="processing_sessions")
    agent_message_logs = relationship("AgentMessageLog", back_populates="session", cascade="all, delete-orphan")


class AgentMessageLog(Base):
    """智能体消息日志表"""
    __tablename__ = "agent_message_logs"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("processing_sessions.id"), nullable=False)
    message_id = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)
    agent_name = Column(String(100), nullable=False)
    message_type = Column(Enum('progress', 'info', 'success', 'warning', 'error', 'metrics', 'completion', name='message_type_enum'), nullable=False)
    content = Column(Text, nullable=False)
    region = Column(String(50), default='process')
    source = Column(String(100))
    is_final = Column(Boolean, default=False)
    result_data = Column(JSON)
    error_info = Column(JSON)
    metrics_data = Column(JSON)
    processing_stage = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ProcessingSession", back_populates="agent_message_logs")


class MindMap(Base):
    """思维导图表"""
    __tablename__ = "mind_maps"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    session_id = Column(String(36), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"))
    mind_map_data = Column(JSON, nullable=False)
    layout_config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="mind_maps")


class ExportRecord(Base):
    """导出记录表"""
    __tablename__ = "export_records"

    id = Column(String(36), primary_key=True)
    export_type = Column(Enum(ExportType), nullable=False)
    test_case_ids = Column(JSON)
    session_id = Column(String(36))
    project_id = Column(String(36), ForeignKey("projects.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    export_config = Column(JSON)
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    project = relationship("Project", back_populates="export_records")


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(String(36), primary_key=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(Text)
    config_type = Column(Enum(ConfigType), default=ConfigType.STRING)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic模型用于API (最终版)
class TestCaseCreateRequest(BaseModel):
    """创建测试用例请求模型"""
    title: str = Field(..., description="测试用例标题")
    description: Optional[str] = Field(None, description="测试用例描述")
    preconditions: Optional[str] = Field(None, description="前置条件")
    test_steps: Optional[List[Dict[str, Any]]] = Field(None, description="测试步骤")
    expected_results: Optional[str] = Field(None, description="预期结果")
    test_type: TestType = Field(..., description="测试类型")
    test_level: TestLevel = Field(..., description="测试级别")
    priority: Priority = Field(Priority.P2, description="优先级")
    project_id: Optional[str] = Field(None, description="项目ID")
    category_id: Optional[str] = Field(None, description="分类ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    input_source: Optional[InputSource] = Field(None, description="输入源类型")
    source_file_path: Optional[str] = Field(None, description="源文件路径")
    ai_generated: bool = Field(False, description="是否AI生成")
    ai_confidence: Optional[float] = Field(None, description="AI置信度")
    ai_model_info: Optional[Dict[str, Any]] = Field(None, description="AI模型信息")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class TestCaseResponse(BaseModel):
    """测试用例响应模型"""
    id: str
    title: str
    description: Optional[str]
    preconditions: Optional[str]
    test_steps: Optional[List[Dict[str, Any]]]
    expected_results: Optional[str]
    test_type: TestType
    test_level: TestLevel
    priority: Priority
    status: TestCaseStatus
    project_id: str
    category_id: Optional[str]
    session_id: Optional[str]
    input_source: Optional[InputSource]
    source_file_path: Optional[str]
    ai_generated: bool
    ai_confidence: Optional[float]
    ai_model_info: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """分类响应模型"""
    id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]
    project_id: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    """标签响应模型"""
    id: str
    name: str
    color: str
    project_id: Optional[str]
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True
