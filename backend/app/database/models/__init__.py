"""
数据库模型模块
定义所有数据库表的SQLAlchemy模型
"""

from .base import BaseModel
from .page_analysis import PageAnalysisResult, PageElement
from .requirement import (
    Requirement, TestCaseRequirement,
    RequirementType, RequirementPriority, RequirementStatus,
    RequirementCreateRequest, RequirementResponse,
    TestCaseRequirementCreateRequest, TestCaseRequirementResponse
)

__all__ = [
    'BaseModel',
    'PageAnalysisResult',
    'PageElement',
    'Requirement',
    'TestCaseRequirement',
    'RequirementType',
    'RequirementPriority',
    'RequirementStatus',
    'RequirementCreateRequest',
    'RequirementResponse',
    'TestCaseRequirementCreateRequest',
    'TestCaseRequirementResponse',
]
