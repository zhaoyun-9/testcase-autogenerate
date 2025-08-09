"""
页面分析相关数据库模型
用于存储页面分析结果和页面元素信息
"""
from sqlalchemy import Column, String, Text, JSON, DECIMAL, Integer, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class PageAnalysisResult(BaseModel):
    """页面分析结果表模型"""
    
    __tablename__ = 'page_analysis_results'
    
    # 关联信息
    session_id = Column(String(100), nullable=False, index=True)  # 增加长度以支持UUID_数字格式
    analysis_id = Column(String(36), nullable=False, unique=True)
    
    # 页面基本信息
    page_name = Column(String(255), nullable=False)
    page_url = Column(String(1000))
    page_type = Column(String(50), default='unknown')
    page_description = Column(Text)
    
    # 分析结果
    analysis_summary = Column(Text)
    confidence_score = Column(DECIMAL(5, 2), default=0.0)

    # 完整的分析数据（JSON格式存储）
    raw_analysis_json = Column(JSON)  # 智能体输出的原始JSON数据
    parsed_ui_elements = Column(JSON)  # 解析后的UI元素数据
    analysis_metadata = Column(JSON)  # 分析元数据（处理时间、智能体信息等）
    
    # 统计信息
    elements_count = Column(Integer, default=0)
    processing_time = Column(DECIMAL(10, 3))  # 处理时间（秒）
    
    # 关系
    page_elements = relationship("PageElement", back_populates="page_analysis", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_page_analysis_session_id', 'session_id'),
        Index('idx_page_analysis_page_name', 'page_name'),
        Index('idx_page_analysis_page_type', 'page_type'),
        Index('idx_page_analysis_created_at', 'created_at'),
        Index('idx_page_analysis_confidence', 'confidence_score'),
    )
    
    def __repr__(self):
        return f"<PageAnalysisResult(id={self.id}, page_name={self.page_name}, confidence={self.confidence_score})>"

    def to_dict_safe(self) -> dict:
        """安全的字典转换，处理可能的序列化问题"""
        def safe_serialize(value):
            """安全序列化值"""
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if hasattr(value, 'isoformat'):  # datetime对象
                return value.isoformat()
            if isinstance(value, (dict, list)):
                return value
            return str(value)

        return {
            "id": safe_serialize(self.id),
            "session_id": safe_serialize(self.session_id),
            "analysis_id": safe_serialize(self.analysis_id),
            "page_name": safe_serialize(self.page_name),
            "page_url": safe_serialize(self.page_url),
            "page_type": safe_serialize(self.page_type),
            "page_description": safe_serialize(self.page_description),
            "analysis_summary": safe_serialize(self.analysis_summary),
            "confidence_score": safe_serialize(self.confidence_score),
            "raw_analysis_json": safe_serialize(self.raw_analysis_json),
            "parsed_ui_elements": safe_serialize(self.parsed_ui_elements),
            "analysis_metadata": safe_serialize(self.analysis_metadata),
            "elements_count": safe_serialize(self.elements_count),
            "processing_time": safe_serialize(self.processing_time),
            "created_at": safe_serialize(self.created_at),
            "updated_at": safe_serialize(self.updated_at)
        }


class PageElement(BaseModel):
    """页面元素表模型"""
    
    __tablename__ = 'page_elements'
    
    # 关联页面分析结果
    page_analysis_id = Column(String(36), ForeignKey('page_analysis_results.id', ondelete='CASCADE'), nullable=False)
    
    # 元素基本信息
    element_name = Column(String(255))
    element_type = Column(String(100), nullable=False)
    element_description = Column(Text)
    
    # 元素完整信息（JSON格式存储，包含所有属性）
    element_data = Column(JSON)  # 完整的元素数据（位置、属性、视觉特征等）

    # 核心属性（用于快速查询和索引）
    confidence_score = Column(DECIMAL(5, 2), default=0.0)
    is_testable = Column(Boolean, default=True)  # 是否可测试
    
    # 关系
    page_analysis = relationship("PageAnalysisResult", back_populates="page_elements")
    
    # 索引
    __table_args__ = (
        Index('idx_page_elements_analysis_id', 'page_analysis_id'),
        Index('idx_page_elements_type', 'element_type'),
        Index('idx_page_elements_testable', 'is_testable'),
        Index('idx_page_elements_confidence', 'confidence_score'),
    )
    
    def __repr__(self):
        return f"<PageElement(id={self.id}, name={self.element_name}, type={self.element_type})>"

    def to_dict_safe(self) -> dict:
        """安全的字典转换，处理可能的序列化问题"""
        def safe_serialize(value):
            """安全序列化值"""
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if hasattr(value, 'isoformat'):  # datetime对象
                return value.isoformat()
            if isinstance(value, (dict, list)):
                return value
            return str(value)

        return {
            "id": safe_serialize(self.id),
            "page_analysis_id": safe_serialize(self.page_analysis_id),
            "element_name": safe_serialize(self.element_name),
            "element_type": safe_serialize(self.element_type),
            "element_description": safe_serialize(self.element_description),
            "element_data": safe_serialize(self.element_data),
            "confidence_score": safe_serialize(self.confidence_score),
            "is_testable": safe_serialize(self.is_testable),
            "created_at": safe_serialize(self.created_at),
            "updated_at": safe_serialize(self.updated_at)
        }
