"""
测试用例仓储类 (最终版)
基于最终版数据库结构的测试用例数据操作
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .base import BaseRepository
from ..models.test_case import (
    TestCase, Tag, TestCaseTag, Project, Category,
    TestCaseCreateRequest, TestCaseResponse
)
from app.core.enums import (
    TestType, TestLevel, Priority,
    TestCaseStatus, InputSource, ProjectStatus
)


class TestCaseRepository(BaseRepository[TestCase]):
    """测试用例仓储类 (最终版)"""
    
    def __init__(self):
        super().__init__(TestCase)
        
        # 系统常量
        self.DEFAULT_PROJECT_ID = "default-project-001"
    
    async def ensure_system_data(self, session: AsyncSession) -> bool:
        """确保系统数据存在（默认项目）"""
        try:
            # 检查默认项目是否存在
            project_result = await session.execute(
                select(Project).where(Project.id == self.DEFAULT_PROJECT_ID)
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                # 创建默认项目
                default_project = Project(
                    id=self.DEFAULT_PROJECT_ID,
                    name="默认项目",
                    description="系统默认测试用例项目",
                    status=ProjectStatus.ACTIVE
                )
                session.add(default_project)
                await session.flush()
                logger.info("创建默认项目成功")
            
            return True
            
        except Exception as e:
            logger.error(f"确保系统数据失败: {str(e)}")
            return False
    
    async def create_test_case(
        self, 
        session: AsyncSession, 
        test_case_data: TestCaseCreateRequest
    ) -> TestCase:
        """创建测试用例"""
        try:
            # 确保系统数据存在
            await self.ensure_system_data(session)
            
            # 创建测试用例记录
            test_case = TestCase(
                id=str(uuid.uuid4()),
                title=test_case_data.title,
                description=test_case_data.description,
                preconditions=test_case_data.preconditions,
                test_steps=test_case_data.test_steps,
                expected_results=test_case_data.expected_results,
                test_type=test_case_data.test_type,
                test_level=test_case_data.test_level,
                priority=test_case_data.priority,
                status=TestCaseStatus.DRAFT,
                project_id=test_case_data.project_id or self.DEFAULT_PROJECT_ID,
                category_id=test_case_data.category_id,
                session_id=test_case_data.session_id,  # 添加 session_id 字段
                input_source=test_case_data.input_source,
                source_file_path=test_case_data.source_file_path,
                ai_generated=test_case_data.ai_generated,
                ai_confidence=test_case_data.ai_confidence,
                ai_model_info=test_case_data.ai_model_info
            )
            
            session.add(test_case)
            await session.flush()  # 获取ID
            
            # 处理标签
            if test_case_data.tags:
                await self.create_test_case_tags(
                    session, 
                    test_case.id, 
                    test_case_data.tags,
                    test_case_data.project_id or self.DEFAULT_PROJECT_ID
                )
            
            await session.commit()
            await session.refresh(test_case)
            
            logger.info(f"创建测试用例成功: {test_case.id}")
            return test_case
            
        except Exception as e:
            await session.rollback()
            logger.error(f"创建测试用例失败: {str(e)}")
            raise
    
    async def create_test_case_tags(
        self,
        session: AsyncSession,
        test_case_id: str,
        tag_names: List[str],
        project_id: str
    ) -> List[TestCaseTag]:
        """创建测试用例标签关联"""
        try:
            created_tags = []
            
            for tag_name in tag_names:
                # 查找或创建标签
                tag_result = await session.execute(
                    select(Tag).where(
                        and_(
                            Tag.name == tag_name,
                            Tag.project_id == project_id
                        )
                    )
                )
                tag = tag_result.scalar_one_or_none()
                
                if not tag:
                    # 创建新标签
                    tag = Tag(
                        id=str(uuid.uuid4()),
                        name=tag_name,
                        project_id=project_id,
                        usage_count=0
                    )
                    session.add(tag)
                    await session.flush()
                
                # 创建关联关系
                test_case_tag = TestCaseTag(
                    id=str(uuid.uuid4()),
                    test_case_id=test_case_id,
                    tag_id=tag.id
                )
                session.add(test_case_tag)
                created_tags.append(test_case_tag)
                
                # 更新标签使用次数
                tag.usage_count += 1
            
            return created_tags
            
        except Exception as e:
            logger.error(f"创建测试用例标签失败: {str(e)}")
            raise
    
    async def get_test_cases_by_project(
        self,
        session: AsyncSession,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[TestCase], int]:
        """根据项目ID获取测试用例列表"""
        try:
            query = select(TestCase).where(TestCase.project_id == project_id)
            
            # 应用过滤条件
            if filters:
                if filters.get('test_type'):
                    query = query.where(TestCase.test_type == filters['test_type'])
                
                if filters.get('test_level'):
                    query = query.where(TestCase.test_level == filters['test_level'])
                
                if filters.get('priority'):
                    query = query.where(TestCase.priority == filters['priority'])
                
                if filters.get('status'):
                    query = query.where(TestCase.status == filters['status'])
                
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.where(
                        or_(
                            TestCase.title.like(search_term),
                            TestCase.description.like(search_term)
                        )
                    )
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()
            
            # 分页和排序
            query = query.order_by(desc(TestCase.updated_at))
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # 执行查询
            result = await session.execute(query)
            test_cases = result.scalars().all()
            
            return test_cases, total
            
        except Exception as e:
            logger.error(f"获取测试用例列表失败: {str(e)}")
            raise
    
    async def get_test_case_by_id(
        self,
        session: AsyncSession,
        test_case_id: str
    ) -> Optional[TestCase]:
        """根据ID获取测试用例"""
        try:
            result = await session.execute(
                select(TestCase).where(TestCase.id == test_case_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取测试用例失败: {str(e)}")
            raise
    
    async def update_test_case(
        self,
        session: AsyncSession,
        test_case_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[TestCase]:
        """更新测试用例"""
        try:
            test_case = await self.get_test_case_by_id(session, test_case_id)
            if not test_case:
                return None
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(test_case, field):
                    setattr(test_case, field, value)
            
            await session.commit()
            await session.refresh(test_case)
            
            logger.info(f"更新测试用例成功: {test_case_id}")
            return test_case
            
        except Exception as e:
            await session.rollback()
            logger.error(f"更新测试用例失败: {str(e)}")
            raise
    
    async def delete_test_case(
        self,
        session: AsyncSession,
        test_case_id: str
    ) -> bool:
        """删除测试用例"""
        try:
            test_case = await self.get_test_case_by_id(session, test_case_id)
            if not test_case:
                return False
            
            # 删除关联的标签
            await session.execute(
                select(TestCaseTag).where(TestCaseTag.test_case_id == test_case_id)
            )
            
            # 删除测试用例
            await session.delete(test_case)
            await session.commit()
            
            logger.info(f"删除测试用例成功: {test_case_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"删除测试用例失败: {str(e)}")
            raise
    
    async def get_test_case_statistics(
        self,
        session: AsyncSession,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取测试用例统计信息"""
        try:
            query = select(TestCase)
            if project_id:
                query = query.where(TestCase.project_id == project_id)
            
            # 总数统计
            total_result = await session.execute(
                select(func.count()).select_from(query.subquery())
            )
            total = total_result.scalar()
            
            # 按状态统计
            status_stats = {}
            for status in TestCaseStatus:
                status_result = await session.execute(
                    select(func.count()).select_from(
                        query.where(TestCase.status == status).subquery()
                    )
                )
                status_stats[status.value] = status_result.scalar()
            
            # 按类型统计
            type_stats = {}
            for test_type in TestType:
                type_result = await session.execute(
                    select(func.count()).select_from(
                        query.where(TestCase.test_type == test_type).subquery()
                    )
                )
                type_stats[test_type.value] = type_result.scalar()
            
            # AI生成统计
            ai_generated_result = await session.execute(
                select(func.count()).select_from(
                    query.where(TestCase.ai_generated == True).subquery()
                )
            )
            ai_generated_count = ai_generated_result.scalar()
            
            return {
                'total': total,
                'by_status': status_stats,
                'by_type': type_stats,
                'ai_generated': ai_generated_count,
                'manual_created': total - ai_generated_count
            }
            
        except Exception as e:
            logger.error(f"获取测试用例统计失败: {str(e)}")
            raise
