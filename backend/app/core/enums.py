"""
核心枚举定义
统一的枚举定义，避免重复和类型冲突
"""
import enum


class TestType(str, enum.Enum):
    """测试类型枚举"""
    FUNCTIONAL = "FUNCTIONAL"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    COMPATIBILITY = "COMPATIBILITY"
    USABILITY = "USABILITY"
    INTERFACE = "INTERFACE"
    DATABASE = "DATABASE"


class TestLevel(str, enum.Enum):
    """测试级别枚举"""
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    SYSTEM = "SYSTEM"
    ACCEPTANCE = "ACCEPTANCE"


class Priority(str, enum.Enum):
    """优先级枚举"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TestCaseStatus(str, enum.Enum):
    """测试用例状态枚举"""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"


class InputSource(str, enum.Enum):
    """输入源类型枚举"""
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    API_SPEC = "API_SPEC"
    DATABASE_SCHEMA = "DATABASE_SCHEMA"
    VIDEO = "VIDEO"
    MANUAL = "MANUAL"


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class SessionType(str, enum.Enum):
    """会话类型枚举"""
    DOCUMENT_PARSE = "document_parse"
    IMAGE_ANALYSIS = "image_analysis"
    API_SPEC_PARSE = "api_spec_parse"
    DATABASE_SCHEMA_PARSE = "database_schema_parse"
    VIDEO_ANALYSIS = "video_analysis"
    MANUAL_INPUT = "manual_input"


class SessionStatus(str, enum.Enum):
    """会话状态枚举"""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadSource(str, enum.Enum):
    """上传源类型枚举"""
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    API_SPEC = "API_SPEC"
    DATABASE_SCHEMA = "DATABASE_SCHEMA"
    VIDEO = "VIDEO"


class ExportType(str, enum.Enum):
    """导出类型枚举"""
    EXCEL = "EXCEL"
    WORD = "WORD"
    PDF = "PDF"


class ExportStatus(str, enum.Enum):
    """导出状态枚举"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ConfigType(str, enum.Enum):
    """配置类型枚举"""
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
