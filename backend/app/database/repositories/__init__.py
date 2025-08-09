"""
数据库仓库模块
提供数据访问层的抽象
"""

from .base import BaseRepository
from .page_analysis_repository import PageAnalysisRepository, PageElementRepository

__all__ = [
    'BaseRepository',
    'PageAnalysisRepository',
    'PageElementRepository',
]
