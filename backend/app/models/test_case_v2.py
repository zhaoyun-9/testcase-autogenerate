"""
测试用例数据模型 v2.0
兼容新的数据库表结构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, JSON, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import enum

Base = declarative_base()


# 枚举定义
class TestType(str, enum.Enum):
    """测试类型枚举"""
    FUNCTIONAL = "functional"  # 功能测试
    PERFORMANCE = "performance"  # 性能测试
    SECURITY = "security"  # 安全测试
    COMPATIBILITY = "compatibility"  # 兼容性测试
    USABILITY = "usability"  # 可用性测试
    INTERFACE = "interface"  # 接口测试
    DATABASE = "database"  # 数据库测试
    SMOKE = "smoke"  # 冒烟测试
    REGRESSION = "regression"  # 回归测试
    INTEGRATION = "integration"  # 集成测试


class TestLevel(str, enum.Enum):
    """测试级别枚举"""
    UNIT = "unit"  # 单元测试
    INTEGRATION = "integration"  # 集成测试
    SYSTEM = "system"  # 系统测试
    ACCEPTANCE = "acceptance"  # 验收测试
    API = "api"  # API测试
    UI = "ui"  # UI测试


class TestMethod(str, enum.Enum):
    """测试方法枚举"""
    MANUAL = "manual"  # 手动测试
    AUTOMATED = "automated"  # 自动化测试
    SEMI_AUTOMATED = "semi_automated"  # 半自动化测试


class Priority(str, enum.Enum):
    """优先级枚举"""
    P0 = "P0"  # 最高优先级
    P1 = "P1"  # 高优先级
    P2 = "P2"  # 中优先级
    P3 = "P3"  # 低优先级
    P4 = "P4"  # 最低优先级


class Severity(str, enum.Enum):
    """严重程度枚举"""
    BLOCKER = "blocker"  # 阻塞
    CRITICAL = "critical"  # 严重
    MAJOR = "major"  # 主要
    MINOR = "minor"  # 次要
    TRIVIAL = "trivial"  # 轻微


class TestCaseStatus(str, enum.Enum):
    """测试用例状态枚举"""
    DRAFT = "draft"  # 草稿
    REVIEW = "review"  # 待审核
    APPROVED = "approved"  # 已批准
    DEPRECATED = "deprecated"  # 已废弃
    ARCHIVED = "archived"  # 已归档


class ReviewStatus(str, enum.Enum):
    """审核状态枚举"""
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    CHANGES_REQUESTED = "changes_requested"  # 需要修改


class ExecutionResult(str, enum.Enum):
    """执行结果枚举"""
    PASS = "pass"  # 通过
    FAIL = "fail"  # 失败
    BLOCKED = "blocked"  # 阻塞
    SKIP = "skip"  # 跳过


class InputSource(str, enum.Enum):
    """输入源类型枚举"""
    IMAGE = "image"  # 图片
    DOCUMENT = "document"  # 文档
    API_SPEC = "api_spec"  # API规范
    DATABASE_SCHEMA = "database_schema"  # 数据库Schema
    VIDEO = "video"  # 录屏视频
    MANUAL = "manual"  # 手动输入
    TEMPLATE = "template"  # 模板
    IMPORT = "import"  # 导入


# 数据库表模型
class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(500))
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))
    status = Column(Enum('active', 'inactive', 'suspended'), default='active')
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True)
    description = Column(Text)
    project_type = Column(Enum('web', 'mobile', 'api', 'desktop', 'other'), default='web')
    status = Column(Enum('planning', 'active', 'suspended', 'completed', 'archived'), default='planning')
    priority = Column(Enum('low', 'medium', 'high', 'critical'), default='medium')
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    budget = Column(Float)
    progress = Column(Float, default=0.0)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    updated_by = Column(String(36), ForeignKey("users.id"))
    
    # 关联关系
    test_cases = relationship("TestCase", back_populates="project")


class TestCaseCategory(Base):
    """测试用例分类表"""
    __tablename__ = "test_case_categories"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    description = Column(Text)
    parent_id = Column(String(36), ForeignKey("test_case_categories.id"))
    project_id = Column(String(36), ForeignKey("projects.id"))
    level = Column(Integer, default=1)
    path = Column(String(1000))
    sort_order = Column(Integer, default=0)
    icon = Column(String(100))
    color = Column(String(20))
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # 关联关系
    parent = relationship("TestCaseCategory", remote_side="TestCaseCategory.id")
    test_cases = relationship("TestCase", back_populates="category")


class TestCaseTemplate(Base):
    """测试用例模板表"""
    __tablename__ = "test_case_templates"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category_id = Column(String(36), ForeignKey("test_case_categories.id"))
    project_id = Column(String(36), ForeignKey("projects.id"))
    template_type = Column(Enum(TestType), nullable=False)
    template_data = Column(JSON, nullable=False)
    fields_config = Column(JSON)
    validation_rules = Column(JSON)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"))


class TestCase(Base):
    """测试用例主表"""
    __tablename__ = "test_cases"
    
    id = Column(String(36), primary_key=True)
    case_number = Column(String(50), unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    preconditions = Column(Text)
    test_steps = Column(JSON)
    expected_results = Column(Text)
    actual_results = Column(Text)
    
    # 分类信息
    test_type = Column(Enum(TestType), nullable=False)
    test_level = Column(Enum(TestLevel), nullable=False)
    test_method = Column(Enum(TestMethod), default=TestMethod.MANUAL)
    priority = Column(Enum(Priority), default=Priority.P2)
    severity = Column(Enum(Severity), default=Severity.MAJOR)
    status = Column(Enum(TestCaseStatus), default=TestCaseStatus.DRAFT)
    
    # 关联信息
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("test_case_categories.id"))
    template_id = Column(String(36), ForeignKey("test_case_templates.id"))
    parent_case_id = Column(String(36), ForeignKey("test_cases.id"))
    
    # 输入源信息
    input_source = Column(Enum(InputSource))
    source_file_path = Column(String(500))
    source_metadata = Column(JSON)
    
    # AI生成信息
    ai_generated = Column(Boolean, default=False)
    ai_confidence = Column(Float)
    ai_model_info = Column(JSON)
    ai_prompt = Column(Text)
    
    # 执行信息
    execution_count = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    last_execution_at = Column(DateTime)
    last_execution_result = Column(Enum(ExecutionResult))
    
    # 版本信息
    version = Column(String(20), default='1.0')
    is_latest = Column(Boolean, default=True)
    
    # 审核信息
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    reviewed_by = Column(String(36), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_comments = Column(Text)
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"))
    assigned_to = Column(String(36), ForeignKey("users.id"))
    
    # 扩展字段
    custom_fields = Column(JSON)
    attachments = Column(JSON)
    
    # 关联关系
    project = relationship("Project", back_populates="test_cases")
    category = relationship("TestCaseCategory", back_populates="test_cases")
    tags = relationship("TestCaseTag", back_populates="test_case")
    mind_maps = relationship("TestCaseMindMap", back_populates="test_case")


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default='#1890ff')
    description = Column(Text)
    project_id = Column(String(36), ForeignKey("projects.id"))
    category = Column(Enum('system', 'project', 'custom'), default='custom')
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))


class TestCaseTag(Base):
    """测试用例标签关联表"""
    __tablename__ = "test_case_tags"
    
    id = Column(String(36), primary_key=True)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # 关联关系
    test_case = relationship("TestCase", back_populates="tags")


class TestCaseMindMap(Base):
    """测试用例思维导图表"""
    __tablename__ = "mind_maps"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"))
    mind_map_data = Column(JSON, nullable=False)
    layout_config = Column(JSON)
    style_config = Column(JSON)
    version = Column(String(20), default='1.0')
    is_latest = Column(Boolean, default=True)
    status = Column(Enum('draft', 'published', 'archived'), default='draft')
    is_public = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    export_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"))
    
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
    test_method: TestMethod = Field(TestMethod.MANUAL, description="测试方法")
    priority: Priority = Field(Priority.P2, description="优先级")
    severity: Severity = Field(Severity.MAJOR, description="严重程度")
    status: TestCaseStatus = Field(TestCaseStatus.DRAFT, description="状态")


class TestCaseCreate(TestCaseBase):
    """创建测试用例模型"""
    project_id: str = Field(..., description="项目ID")
    category_id: Optional[str] = Field(None, description="分类ID")
    template_id: Optional[str] = Field(None, description="模板ID")
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
    test_method: Optional[TestMethod] = Field(None, description="测试方法")
    priority: Optional[Priority] = Field(None, description="优先级")
    severity: Optional[Severity] = Field(None, description="严重程度")
    status: Optional[TestCaseStatus] = Field(None, description="状态")
    category_id: Optional[str] = Field(None, description="分类ID")
    assigned_to: Optional[str] = Field(None, description="分配给")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class TestCaseResponse(TestCaseBase):
    """测试用例响应模型"""
    id: str
    case_number: Optional[str]
    project_id: str
    category_id: Optional[str]
    version: str
    is_latest: bool
    review_status: ReviewStatus
    execution_count: int
    pass_count: int
    fail_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True
