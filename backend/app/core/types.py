"""
核心类型定义
定义系统中使用的枚举类型和常量
"""
from enum import Enum
from typing import Dict


class AgentTypes(Enum):
    """智能体类型枚举"""
    # 测试用例平台智能体
    DOCUMENT_PARSER = "document_parser"
    IMAGE_ANALYZER = "image_analyzer"
    API_SPEC_PARSER = "api_spec_parser"
    DATABASE_SCHEMA_PARSER = "database_schema_parser"
    VIDEO_ANALYZER = "video_analyzer"
    REQUIREMENT_ANALYZER = "requirement_analyzer"
    TEST_POINT_EXTRACTOR = "test_point_extractor"
    TEST_CASE_GENERATOR = "test_case_generator"
    TEST_CASE_SAVER = "test_case_saver"
    REQUIREMENT_SAVER = "requirement_saver"
    MIND_MAP_GENERATOR = "mind_map_generator"
    EXCEL_EXPORTER = "excel_exporter"
    SESSION_STATUS = "session_status"
    RAG_RETRIEVAL = "rag_retrieval"


class TopicTypes(Enum):
    """主题类型枚举"""
    # 测试用例平台主题
    DOCUMENT_PARSER = "document_parser_topic"
    IMAGE_ANALYZER = "image_analyzer_topic"
    API_SPEC_PARSER = "api_spec_parser_topic"
    DATABASE_SCHEMA_PARSER = "database_schema_parser_topic"
    VIDEO_ANALYZER = "video_analyzer_topic"
    REQUIREMENT_ANALYZER = "requirement_analyzer_topic"
    TEST_POINT_EXTRACTOR = "test_point_extractor_topic"
    TEST_CASE_GENERATOR = "test_case_generator_topic"
    TEST_CASE_SAVER = "test_case_saver_topic"
    REQUIREMENT_SAVER = "requirement_saver_topic"
    MIND_MAP_GENERATOR = "mind_map_generator_topic"
    EXCEL_EXPORTER = "excel_exporter_topic"
    SESSION_STATUS = "session_status_topic"
    RAG_RETRIEVAL = "rag_retrieval_topic"

    # 系统主题
    STREAM_OUTPUT = "stream_output_topic"


class AgentPlatform(Enum):
    """智能体平台类型"""
    TEST_CASE = "test_case"
    GENERAL = "general"
    WEB = "web"


class MessageTypes(Enum):
    """消息类型枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    PROGRESS = "progress"
    COMPLETION = "completion"
    HEARTBEAT = "heartbeat"


class MessageRegion(Enum):
    """消息区域枚举"""
    MAIN = "main"
    PROCESS = "process"
    RESULT = "result"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"


# 保持向后兼容
MessageRegions = MessageRegion


# 智能体名称映射
AGENT_NAMES: Dict[str, str] = {
    # 测试用例平台智能体
    AgentTypes.DOCUMENT_PARSER.value: "文档解析智能体",
    AgentTypes.IMAGE_ANALYZER.value: "图片分析智能体",
    AgentTypes.API_SPEC_PARSER.value: "API规范解析智能体",
    AgentTypes.DATABASE_SCHEMA_PARSER.value: "数据库Schema解析智能体",
    AgentTypes.VIDEO_ANALYZER.value: "录屏分析智能体",
    AgentTypes.REQUIREMENT_ANALYZER.value: "需求解析智能体",
    AgentTypes.TEST_POINT_EXTRACTOR.value: "测试点提取智能体",
    AgentTypes.TEST_CASE_GENERATOR.value: "测试用例生成智能体",
    AgentTypes.TEST_CASE_SAVER.value: "测试用例保存智能体",
    AgentTypes.REQUIREMENT_SAVER.value: "需求存储智能体",
    AgentTypes.MIND_MAP_GENERATOR.value: "思维导图生成智能体",
    AgentTypes.EXCEL_EXPORTER.value: "Excel导出智能体",
    AgentTypes.SESSION_STATUS.value: "会话状态更新智能体",
    AgentTypes.RAG_RETRIEVAL.value: "RAG知识库检索智能体",
}

# 主题名称映射
TOPIC_NAMES: Dict[str, str] = {
    # 测试用例平台主题
    TopicTypes.DOCUMENT_PARSER.value: "文档解析主题",
    TopicTypes.IMAGE_ANALYZER.value: "图片分析主题",
    TopicTypes.API_SPEC_PARSER.value: "API规范解析主题",
    TopicTypes.DATABASE_SCHEMA_PARSER.value: "数据库Schema解析主题",
    TopicTypes.VIDEO_ANALYZER.value: "录屏分析主题",
    TopicTypes.REQUIREMENT_ANALYZER.value: "需求解析主题",
    TopicTypes.TEST_POINT_EXTRACTOR.value: "测试点提取主题",
    TopicTypes.TEST_CASE_GENERATOR.value: "测试用例生成主题",
    TopicTypes.MIND_MAP_GENERATOR.value: "思维导图生成主题",
    TopicTypes.EXCEL_EXPORTER.value: "Excel导出主题",
    TopicTypes.TEST_CASE_SAVER.value: "测试用例保存主题",
    TopicTypes.REQUIREMENT_SAVER.value: "需求存储主题",
    TopicTypes.SESSION_STATUS.value: "会话状态更新主题",
    TopicTypes.RAG_RETRIEVAL.value: "RAG知识库检索主题",

    # 系统主题
    TopicTypes.STREAM_OUTPUT.value: "流式输出主题",
}

# 支持的文件类型
SUPPORTED_DOCUMENT_TYPES = [".pdf", ".docx", ".doc", ".txt", ".md"]
SUPPORTED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
SUPPORTED_API_SPEC_TYPES = [".json", ".yaml", ".yml"]
SUPPORTED_VIDEO_TYPES = [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"]
SUPPORTED_DATABASE_SCHEMA_TYPES = [".sql", ".json", ".xml"]

# 文件类型到智能体的映射
FILE_TYPE_TO_AGENT_MAPPING = {
    # 文档类型
    ".pdf": AgentTypes.DOCUMENT_PARSER.value,
    ".docx": AgentTypes.DOCUMENT_PARSER.value,
    ".doc": AgentTypes.DOCUMENT_PARSER.value,
    ".txt": AgentTypes.DOCUMENT_PARSER.value,
    ".md": AgentTypes.DOCUMENT_PARSER.value,

    # 图片类型
    ".jpg": AgentTypes.IMAGE_ANALYZER.value,
    ".jpeg": AgentTypes.IMAGE_ANALYZER.value,
    ".png": AgentTypes.IMAGE_ANALYZER.value,
    ".gif": AgentTypes.IMAGE_ANALYZER.value,
    ".bmp": AgentTypes.IMAGE_ANALYZER.value,
    ".webp": AgentTypes.IMAGE_ANALYZER.value,

    # API规范类型
    ".json": AgentTypes.API_SPEC_PARSER.value,  # 可能是API规范或数据库Schema
    ".yaml": AgentTypes.API_SPEC_PARSER.value,
    ".yml": AgentTypes.API_SPEC_PARSER.value,

    # 视频类型
    ".mp4": AgentTypes.VIDEO_ANALYZER.value,
    ".avi": AgentTypes.VIDEO_ANALYZER.value,
    ".mov": AgentTypes.VIDEO_ANALYZER.value,
    ".wmv": AgentTypes.VIDEO_ANALYZER.value,
    ".flv": AgentTypes.VIDEO_ANALYZER.value,
    ".webm": AgentTypes.VIDEO_ANALYZER.value,

    # 数据库Schema类型
    ".sql": AgentTypes.DATABASE_SCHEMA_PARSER.value,
    ".xml": AgentTypes.DATABASE_SCHEMA_PARSER.value,
}

# 最大文件大小 (MB)
MAX_FILE_SIZE = {
    "document": 50,
    "image": 20,
    "api_spec": 10,
    "video": 500,
    "database_schema": 5
}

# 文件类型分类
FILE_TYPE_CATEGORIES = {
    "document": SUPPORTED_DOCUMENT_TYPES,
    "image": SUPPORTED_IMAGE_TYPES,
    "api_spec": SUPPORTED_API_SPEC_TYPES,
    "video": SUPPORTED_VIDEO_TYPES,
    "database_schema": SUPPORTED_DATABASE_SCHEMA_TYPES,
}

# 默认配置
DEFAULT_CONFIG = {
    "session_timeout": 3600,  # 1小时
    "max_concurrent_sessions": 100,
    "ai_timeout": 30,  # AI处理超时时间(秒)
    "enable_debug": False,
    "enable_cache": True,
    "cache_ttl": 1800,  # 缓存TTL(秒)
}
