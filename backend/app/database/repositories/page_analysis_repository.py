"""
页面分析数据仓库
提供页面分析结果的数据访问层
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from loguru import logger

from .base import BaseRepository
from ..models.page_analysis import PageAnalysisResult, PageElement


class PageAnalysisRepository(BaseRepository[PageAnalysisResult]):
    """页面分析结果仓库"""
    
    def __init__(self):
        super().__init__(PageAnalysisResult)
    
    async def create_with_elements(self, 
                                 session: AsyncSession,
                                 analysis_data: Dict[str, Any],
                                 elements_data: List[Dict[str, Any]]) -> PageAnalysisResult:
        """创建页面分析结果及其元素"""
        try:
            # 创建页面分析结果
            page_analysis = await self.create(session, **analysis_data)
            
            # 创建页面元素
            for element_data in elements_data:
                element_data['page_analysis_id'] = page_analysis.id
                page_element = PageElement(**element_data)
                session.add(page_element)
            
            # 更新元素数量
            page_analysis.elements_count = len(elements_data)
            
            await session.flush()
            await session.refresh(page_analysis)
            
            return page_analysis
            
        except Exception as e:
            logger.error(f"创建页面分析结果及元素失败: {e}")
            raise

    async def get_by_analysis_id(self, session: AsyncSession, analysis_id: str) -> Optional[PageAnalysisResult]:
        """根据分析ID获取页面分析结果"""
        try:
            result = await session.execute(
                select(PageAnalysisResult).where(PageAnalysisResult.analysis_id == analysis_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据分析ID获取页面分析结果失败: {e}")
            raise
    
    async def get_with_elements(self, session: AsyncSession, analysis_id: str) -> Optional[Dict[str, Any]]:
        """获取页面分析结果及其元素"""
        try:
            # 获取页面分析结果
            page_analysis = await self.get_by_analysis_id(session, analysis_id)
            if not page_analysis:
                return None
            
            # 获取关联的页面元素
            elements_result = await session.execute(
                select(PageElement).where(PageElement.page_analysis_id == page_analysis.id)
            )
            page_elements = elements_result.scalars().all()
            
            return {
                "page_analysis": page_analysis,
                "page_elements": page_elements
            }
            
        except Exception as e:
            logger.error(f"获取页面分析结果及元素失败: {e}")
            raise

    async def search_by_page_name(self, 
                                session: AsyncSession, 
                                page_name: str,
                                limit: int = 10) -> List[PageAnalysisResult]:
        """根据页面名称搜索页面分析结果"""
        try:
            result = await session.execute(
                select(PageAnalysisResult)
                .where(PageAnalysisResult.page_name.like(f"%{page_name}%"))
                .order_by(desc(PageAnalysisResult.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据页面名称搜索失败: {e}")
            raise
    
    async def get_by_session_id(self, 
                              session: AsyncSession, 
                              session_id: str,
                              limit: int = 20) -> List[PageAnalysisResult]:
        """根据会话ID获取页面分析结果"""
        try:
            result = await session.execute(
                select(PageAnalysisResult)
                .where(PageAnalysisResult.session_id == session_id)
                .order_by(desc(PageAnalysisResult.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据会话ID获取页面分析结果失败: {e}")
            raise

    async def get_by_page_ids(self, 
                            session: AsyncSession, 
                            page_ids: List[str]) -> List[PageAnalysisResult]:
        """根据页面ID列表获取页面分析结果"""
        try:
            if not page_ids:
                return []
            
            result = await session.execute(
                select(PageAnalysisResult)
                .where(PageAnalysisResult.id.in_(page_ids))
                .order_by(desc(PageAnalysisResult.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据页面ID列表获取页面分析结果失败: {e}")
            raise

    async def get_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """获取页面分析统计信息"""
        try:
            # 总数统计
            total_count_result = await session.execute(
                select(func.count(PageAnalysisResult.id))
            )
            total_count = total_count_result.scalar()
            
            # 平均置信度
            avg_confidence_result = await session.execute(
                select(func.avg(PageAnalysisResult.confidence_score))
            )
            avg_confidence = avg_confidence_result.scalar() or 0.0
            
            # 页面类型分布
            page_type_result = await session.execute(
                select(PageAnalysisResult.page_type, func.count(PageAnalysisResult.id))
                .group_by(PageAnalysisResult.page_type)
            )
            page_type_distribution = dict(page_type_result.fetchall())
            
            return {
                "total_analyses": total_count,
                "average_confidence": float(avg_confidence),
                "page_type_distribution": page_type_distribution
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise


class PageElementRepository(BaseRepository[PageElement]):
    """页面元素仓库"""
    
    def __init__(self):
        super().__init__(PageElement)
    
    async def get_by_analysis_id(self, 
                               session: AsyncSession, 
                               page_analysis_id: str) -> List[PageElement]:
        """根据页面分析ID获取所有元素"""
        try:
            result = await session.execute(
                select(PageElement).where(PageElement.page_analysis_id == page_analysis_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据分析ID获取页面元素失败: {e}")
            raise

    async def get_testable_elements(self, 
                                  session: AsyncSession,
                                  page_analysis_id: str) -> List[PageElement]:
        """获取可测试的页面元素"""
        try:
            result = await session.execute(
                select(PageElement)
                .where(and_(
                    PageElement.page_analysis_id == page_analysis_id,
                    PageElement.is_testable == True
                ))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取可测试页面元素失败: {e}")
            raise
    
    async def search_by_type(self, 
                           session: AsyncSession,
                           element_type: str,
                           page_analysis_id: Optional[str] = None) -> List[PageElement]:
        """根据元素类型搜索"""
        try:
            query = select(PageElement).where(PageElement.element_type == element_type)
            
            if page_analysis_id:
                query = query.where(PageElement.page_analysis_id == page_analysis_id)
            
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据元素类型搜索失败: {e}")
            raise

    async def search_by_name(self, 
                           session: AsyncSession,
                           element_name: str,
                           page_analysis_id: Optional[str] = None) -> List[PageElement]:
        """根据元素名称搜索"""
        try:
            query = select(PageElement).where(PageElement.element_name.like(f"%{element_name}%"))
            
            if page_analysis_id:
                query = query.where(PageElement.page_analysis_id == page_analysis_id)
            
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据元素名称搜索失败: {e}")
            raise
