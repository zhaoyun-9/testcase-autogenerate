"""
应用配置
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""

    # 应用基本配置
    APP_NAME: str = "TestCaseAutomation"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]

    # 调试和开发配置
    ENABLE_RELOAD: bool = True  # 是否启用自动重载
    ENABLE_DEBUGGER: bool = False  # 是否在调试器模式下运行
    RUN_MODE: str = "development"  # development, debug, production
    
    # 数据库配置
    DATABASE_URL: str = "mysql+aiomysql://root:mysql@localhost:3306/test_case_automation"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # MySQL数据库配置（作为备选）
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "mysql"
    MYSQL_DATABASE: str = "test_case_automation"

    @property
    def database_url(self) -> str:
        """获取数据库连接URL - 优先使用DATABASE_URL环境变量"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # 如果没有DATABASE_URL，则使用MySQL配置构建
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI模型配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    QWENVL_API_KEY: str = ""
    QWENVL_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # Volcengine Ark配置
    ARK_API_KEY: str = ""
    ARK_VIDEO_MODEL_ID: str = "ep-20241210140356-8xqvs"
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 100  # MB
    UPLOAD_PATH: str = "uploads"
    EXPORT_PATH: str = "exports"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 安全配置
    SECRET_KEY: str = "your_secret_key_here_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取应用设置实例"""
    return settings
