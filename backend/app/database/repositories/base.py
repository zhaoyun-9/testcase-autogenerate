"""
基础仓库类
提供通用的CRUD操作
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """基础仓库类"""
    
    def __init__(self, model_class: type[ModelType]):
        self.model_class = model_class
    
    async def create(self, session: AsyncSession, **kwargs) -> ModelType:
        """创建新记录"""
        try:
            instance = self.model_class(**kwargs)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"创建{self.model_class.__name__}失败: {e}")
            raise
    
    async def get_by_id(self, session: AsyncSession, id: str) -> Optional[ModelType]:
        """根据ID获取记录"""
        try:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取{self.model_class.__name__}失败: {e}")
            raise
    
    async def get_all(
        self, 
        session: AsyncSession, 
        limit: int = 100, 
        offset: int = 0,
        order_by: str = "created_at",
        desc: bool = True
    ) -> List[ModelType]:
        """获取所有记录"""
        try:
            query = select(self.model_class)
            
            # 排序
            order_column = getattr(self.model_class, order_by, self.model_class.created_at)
            if desc:
                order_column = order_column.desc()
            query = query.order_by(order_column)
            
            # 分页
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取{self.model_class.__name__}列表失败: {e}")
            raise
    
    async def update(self, session: AsyncSession, id: str, **kwargs) -> Optional[ModelType]:
        """更新记录"""
        try:
            # 先获取记录
            instance = await self.get_by_id(session, id)
            if not instance:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            await session.flush()
            await session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"更新{self.model_class.__name__}失败: {e}")
            raise
    
    async def delete(self, session: AsyncSession, id: str) -> bool:
        """删除记录"""
        try:
            result = await session.execute(
                delete(self.model_class).where(self.model_class.id == id)
            )
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"删除{self.model_class.__name__}失败: {e}")
            raise
    
    async def count(self, session: AsyncSession, **filters) -> int:
        """统计记录数量"""
        try:
            query = select(func.count(self.model_class.id))
            
            # 应用过滤条件
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
            
            result = await session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"统计{self.model_class.__name__}数量失败: {e}")
            raise
    
    async def exists(self, session: AsyncSession, **filters) -> bool:
        """检查记录是否存在"""
        try:
            query = select(self.model_class.id)
            
            # 应用过滤条件
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
            
            result = await session.execute(query.limit(1))
            return result.scalar() is not None
        except Exception as e:
            logger.error(f"检查{self.model_class.__name__}存在性失败: {e}")
            raise
