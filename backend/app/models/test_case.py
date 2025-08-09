"""
测试用例数据模型
定义测试用例相关的数据库表结构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, JSON, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import enum

Base = declarative_base()


class TestType(str, enum.Enum):
    """测试类型枚举"""
    FUNCTIONAL = "functional"  # 功能测试
    PERFORMANCE = "performance"  # 性能测试
    SECURITY = "security"  # 安全测试
    COMPATIBILITY = "compatibility"  # 兼容性测试
    USABILITY = "usability"  # 可用性测试
    INTERFACE = "interface"  # 接口测试
    DATABASE = "database"  # 数据库测试


class TestLevel(str, enum.Enum):
    """测试级别枚举"""
    UNIT = "unit"  # 单元测试
    INTEGRATION = "integration"  # 集成测试
    SYSTEM = "system"  # 系统测试
    ACCEPTANCE = "acceptance"  # 验收测试


class Priority(str, enum.Enum):
    """优先级枚举"""
    P0 = "P0"  # 最高优先级
    P1 = "P1"  # 高优先级
    P2 = "P2"  # 中优先级
    P3 = "P3"  # 低优先级
    P4 = "P4"  # 最低优先级


class TestCaseStatus(str, enum.Enum):
    """测试用例状态枚举"""
    DRAFT = "draft"  # 草稿
    REVIEW = "review"  # 待审核
    APPROVED = "approved"  # 已批准
    DEPRECATED = "deprecated"  # 已废弃


class InputSource(str, enum.Enum):
    """输入源类型枚举"""
    IMAGE = "image"  # 图片
    DOCUMENT = "document"  # 文档
    API_SPEC = "api_spec"  # API规范
    DATABASE_SCHEMA = "database_schema"  # 数据库Schema
    VIDEO = "video"  # 录屏视频
    MANUAL = "manual"  # 手动输入


# 数据库表模型
class TestCaseProject(Base):
    """测试用例项目表"""
    __tablename__ = "test_case_projects"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    test_cases = relationship("TestCase", back_populates="project")


class TestCaseCategory(Base):
    """测试用例分类表"""
    __tablename__ = "test_case_categories"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    parent_id = Column(String(36), ForeignKey("test_case_categories.id"), comment="父分类ID")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    parent = relationship("TestCaseCategory", remote_side="TestCaseCategory.id")
    test_cases = relationship("TestCase", back_populates="category")


class TestCase(Base):
    """测试用例主表"""
    __tablename__ = "test_cases"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False, comment="测试用例标题")
    description = Column(Text, comment="测试用例描述")
    preconditions = Column(Text, comment="前置条件")
    test_steps = Column(JSON, comment="测试步骤")
    expected_results = Column(Text, comment="预期结果")
    
    # 分类信息
    test_type = Column(Enum(TestType), nullable=False, comment="测试类型")
    test_level = Column(Enum(TestLevel), nullable=False, comment="测试级别")
    priority = Column(Enum(Priority), default=Priority.P2, comment="优先级")
    status = Column(Enum(TestCaseStatus), default=TestCaseStatus.DRAFT, comment="状态")
    
    # 关联信息
    project_id = Column(String(36), ForeignKey("test_case_projects.id"), comment="项目ID")
    category_id = Column(String(36), ForeignKey("test_case_categories.id"), comment="分类ID")
    session_id = Column(String(36), comment="生成会话ID")
    
    # 输入源信息
    input_source = Column(Enum(InputSource), comment="输入源类型")
    source_file_path = Column(String(500), comment="源文件路径")
    source_metadata = Column(JSON, comment="源数据元信息")
    
    # AI生成信息
    ai_generated = Column(Boolean, default=True, comment="是否AI生成")
    ai_confidence = Column(Float, comment="AI置信度")
    ai_model_info = Column(JSON, comment="AI模型信息")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), comment="创建人")
    updated_by = Column(String(100), comment="更新人")
    
    # 关联关系
    project = relationship("TestCaseProject", back_populates="test_cases")
    category = relationship("TestCaseCategory", back_populates="test_cases")
    tags = relationship("TestCaseTag", back_populates="test_case")
    mind_maps = relationship("TestCaseMindMap", back_populates="test_case")


class TestCaseTag(Base):
    """测试用例标签表"""
    __tablename__ = "test_case_tags"
    
    id = Column(String(36), primary_key=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), comment="测试用例ID")
    tag_name = Column(String(100), nullable=False, comment="标签名称")
    tag_color = Column(String(20), comment="标签颜色")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    test_case = relationship("TestCase", back_populates="tags")


class TestCaseMindMap(Base):
    """测试用例思维导图表"""
    __tablename__ = "test_case_mind_maps"
    
    id = Column(String(36), primary_key=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), comment="测试用例ID")
    mind_map_data = Column(JSON, nullable=False, comment="思维导图数据")
    layout_config = Column(JSON, comment="布局配置")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    test_case = relationship("TestCase", back_populates="mind_maps")


# Pydantic模型用于API
class TestCaseBase(BaseModel):
    """测试用例基础模型"""
    title: str = Field(..., description="测试用例标题")
    description: Optional[str] = Field(None, description="测试用例描述")
    preconditions: Optional[str] = Field(None, description="前置条件")
    test_steps: Optional[List[Dict[str, Any]]] = Field(None, description="测试步骤")
    expected_results: Optional[str] = Field(None, description="预期结果")
    test_type: TestType = Field(..., description="测试类型")
    test_level: TestLevel = Field(..., description="测试级别")
    priority: Priority = Field(Priority.P2, description="优先级")
    status: TestCaseStatus = Field(TestCaseStatus.DRAFT, description="状态")


class TestCaseCreate(TestCaseBase):
    """创建测试用例模型"""
    project_id: Optional[str] = Field(None, description="项目ID")
    category_id: Optional[str] = Field(None, description="分类ID")
    input_source: Optional[InputSource] = Field(None, description="输入源类型")
    source_file_path: Optional[str] = Field(None, description="源文件路径")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="源数据元信息")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class TestCaseUpdate(BaseModel):
    """更新测试用例模型"""
    title: Optional[str] = Field(None, description="测试用例标题")
    description: Optional[str] = Field(None, description="测试用例描述")
    preconditions: Optional[str] = Field(None, description="前置条件")
    test_steps: Optional[List[Dict[str, Any]]] = Field(None, description="测试步骤")
    expected_results: Optional[str] = Field(None, description="预期结果")
    test_type: Optional[TestType] = Field(None, description="测试类型")
    test_level: Optional[TestLevel] = Field(None, description="测试级别")
    priority: Optional[Priority] = Field(None, description="优先级")
    status: Optional[TestCaseStatus] = Field(None, description="状态")
    category_id: Optional[str] = Field(None, description="分类ID")


class TestCaseResponse(TestCaseBase):
    """测试用例响应模型"""
    id: str
    project_id: Optional[str]
    category_id: Optional[str]
    input_source: Optional[InputSource]
    source_file_path: Optional[str]
    ai_generated: bool
    ai_confidence: Optional[float]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """测试用例列表响应模型"""
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MindMapData(BaseModel):
    """思维导图数据模型"""
    nodes: List[Dict[str, Any]] = Field(..., description="节点数据")
    edges: List[Dict[str, Any]] = Field(..., description="边数据")
    layout: Optional[Dict[str, Any]] = Field(None, description="布局配置")


class TestCaseMindMapCreate(BaseModel):
    """创建思维导图模型"""
    test_case_id: str = Field(..., description="测试用例ID")
    mind_map_data: MindMapData = Field(..., description="思维导图数据")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="布局配置")


class TestCaseMindMapResponse(BaseModel):
    """思维导图响应模型"""
    id: str
    test_case_id: str
    mind_map_data: MindMapData
    layout_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
