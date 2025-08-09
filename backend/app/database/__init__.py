"""
数据库模块初始化
提供数据库连接和基础配置
"""

from .connection import DatabaseManager, db_manager, get_database, init_database, close_database

__all__ = [
    'DatabaseManager',
    'db_manager',
    'get_database',
    'init_database',
    'close_database',
]
