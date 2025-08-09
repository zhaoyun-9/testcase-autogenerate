"""
数据库连接管理
提供数据库连接池和会话管理
"""
import os
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import MetaData

from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# 元数据
metadata = MetaData()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self, database_url: Optional[str] = None):
        """初始化数据库连接"""
        if self._initialized:
            return

        # 获取数据库URL - 优先使用传入参数，然后使用配置类
        if not database_url:
            database_url = settings.database_url
            logger.info(f"使用配置的数据库URL: {database_url.split('@')[-1] if '@' in database_url else database_url}")

        try:
            # 创建异步引擎
            self.engine = create_async_engine(
                database_url,
                echo=settings.DATABASE_ECHO,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_recycle=settings.DATABASE_POOL_RECYCLE,
                # 添加连接参数以优化MySQL连接（aiomysql兼容）
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                    # 设置连接超时
                    "connect_timeout": 60,
                    # 设置锁等待超时（MySQL特定）
                    "init_command": "SET SESSION innodb_lock_wait_timeout = 120"
                }
            )

            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                # 设置会话超时
                autoflush=True,
                autocommit=False
            )
            
            self._initialized = True
            logger.info("数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    async def create_tables(self):
        """创建数据库表"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 导入Base以避免循环导入
            from app.database.models.base import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
    
    async def drop_tables(self):
        """删除数据库表"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 导入Base以避免循环导入
            from app.database.models.base import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"数据库表删除失败: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入用）"""
    async with db_manager.get_session() as session:
        yield session


async def init_database():
    """初始化数据库"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_database():
    """关闭数据库连接"""
    await db_manager.close()
