"""
数据库模型基类
提供通用的字段和方法
"""
import uuid
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """数据库模型基类"""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        # 自动生成表名（类名转下划线格式）
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    # 主键ID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]):
        """从字典更新属性"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
