"""
需求仓储类
负责需求相关的数据库操作
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from .base import BaseRepository
from ..models.requirement import (
    Requirement, TestCaseRequirement,
    RequirementCreateRequest, RequirementResponse,
    TestCaseRequirementCreateRequest, TestCaseRequirementResponse,
    RequirementType, RequirementPriority, RequirementStatus,
    RequirementCoverageStats
)
from ..models.test_case import Project, TestCase


class RequirementRepository(BaseRepository[Requirement]):
    """需求仓储类"""
    
    def __init__(self):
        super().__init__(Requirement)
        
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
                from ..models.test_case import ProjectStatus
                default_project = Project(
                    id=self.DEFAULT_PROJECT_ID,
                    name="默认项目",
                    description="系统默认需求项目",
                    status=ProjectStatus.ACTIVE
                )
                session.add(default_project)
                await session.flush()
                logger.info("创建默认项目成功")
            
            return True
            
        except Exception as e:
            logger.error(f"确保系统数据失败: {str(e)}")
            return False
    
    async def create_requirement(
        self, 
        session: AsyncSession, 
        requirement_data: RequirementCreateRequest
    ) -> Requirement:
        """创建需求"""
        try:
            # 确保系统数据存在
            await self.ensure_system_data(session)
            
            # 创建需求记录
            requirement = Requirement(
                id=str(uuid.uuid4()),
                requirement_id=requirement_data.requirement_id,
                title=requirement_data.title,
                description=requirement_data.description,
                requirement_type=requirement_data.requirement_type.value if hasattr(requirement_data.requirement_type, 'value') else requirement_data.requirement_type,
                priority=requirement_data.priority.value if hasattr(requirement_data.priority, 'value') else requirement_data.priority,
                status=requirement_data.status.value if hasattr(requirement_data.status, 'value') else requirement_data.status,
                project_id=requirement_data.project_id or self.DEFAULT_PROJECT_ID,
                document_id=requirement_data.document_id,
                session_id=requirement_data.session_id,
                source_file_path=requirement_data.source_file_path,
                source_section=requirement_data.source_section,
                ai_generated=requirement_data.ai_generated,
                ai_confidence=requirement_data.ai_confidence,
                ai_model_info=requirement_data.ai_model_info,
                extra_metadata=requirement_data.extra_metadata
            )
            
            session.add(requirement)
            await session.flush()  # 获取ID
            await session.commit()
            await session.refresh(requirement)
            
            logger.info(f"创建需求成功: {requirement.id}")
            return requirement
            
        except Exception as e:
            await session.rollback()
            logger.error(f"创建需求失败: {str(e)}")
            raise
    
    async def batch_create_requirements(
        self,
        session: AsyncSession,
        requirements_data: List[RequirementCreateRequest]
    ) -> List[Requirement]:
        """批量创建需求"""
        try:
            # 确保系统数据存在
            await self.ensure_system_data(session)
            
            created_requirements = []
            
            for req_data in requirements_data:
                requirement = Requirement(
                    id=str(uuid.uuid4()),
                    requirement_id=req_data.requirement_id,
                    title=req_data.title,
                    description=req_data.description,
                    requirement_type=req_data.requirement_type.value if hasattr(req_data.requirement_type, 'value') else req_data.requirement_type,
                    priority=req_data.priority.value if hasattr(req_data.priority, 'value') else req_data.priority,
                    status=req_data.status.value if hasattr(req_data.status, 'value') else req_data.status,
                    project_id=req_data.project_id or self.DEFAULT_PROJECT_ID,
                    document_id=req_data.document_id,
                    session_id=req_data.session_id,
                    source_file_path=req_data.source_file_path,
                    source_section=req_data.source_section,
                    ai_generated=req_data.ai_generated,
                    ai_confidence=req_data.ai_confidence,
                    ai_model_info=req_data.ai_model_info,
                    extra_metadata=req_data.extra_metadata
                )
                
                session.add(requirement)
                created_requirements.append(requirement)
            
            await session.flush()
            await session.commit()
            
            # 刷新所有对象
            for req in created_requirements:
                await session.refresh(req)
            
            logger.info(f"批量创建需求成功: {len(created_requirements)} 个")
            return created_requirements
            
        except Exception as e:
            await session.rollback()
            logger.error(f"批量创建需求失败: {str(e)}")
            raise
    
    async def get_requirements_by_project(
        self,
        session: AsyncSession,
        project_id: str,
        requirement_type: Optional[RequirementType] = None,
        priority: Optional[RequirementPriority] = None,
        status: Optional[RequirementStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Requirement]:
        """根据项目获取需求列表"""
        try:
            query = select(Requirement).where(Requirement.project_id == project_id)
            
            # 添加过滤条件
            if requirement_type:
                query = query.where(Requirement.requirement_type == requirement_type)
            if priority:
                query = query.where(Requirement.priority == priority)
            if status:
                query = query.where(Requirement.status == status)
            
            # 排序和分页
            query = query.order_by(desc(Requirement.created_at)).limit(limit).offset(offset)
            
            result = await session.execute(query)
            requirements = result.scalars().all()
            
            logger.info(f"查询到 {len(requirements)} 个需求")
            return requirements
            
        except Exception as e:
            logger.error(f"查询需求失败: {str(e)}")
            return []
    
    async def get_requirements_by_session(
        self,
        session: AsyncSession,
        session_id: str
    ) -> List[Requirement]:
        """根据会话ID获取需求列表"""
        try:
            query = select(Requirement).where(Requirement.session_id == session_id)
            query = query.order_by(desc(Requirement.created_at))
            
            result = await session.execute(query)
            requirements = result.scalars().all()
            
            logger.info(f"会话 {session_id} 查询到 {len(requirements)} 个需求")
            return requirements
            
        except Exception as e:
            logger.error(f"根据会话查询需求失败: {str(e)}")
            return []
    
    async def search_requirements(
        self,
        session: AsyncSession,
        keyword: str,
        project_id: Optional[str] = None,
        requirement_type: Optional[RequirementType] = None,
        limit: int = 50
    ) -> List[Requirement]:
        """搜索需求"""
        try:
            query = select(Requirement)
            
            # 关键词搜索
            search_conditions = [
                Requirement.title.contains(keyword),
                Requirement.description.contains(keyword),
                Requirement.requirement_id.contains(keyword)
            ]
            query = query.where(or_(*search_conditions))
            
            # 添加过滤条件
            if project_id:
                query = query.where(Requirement.project_id == project_id)
            if requirement_type:
                query = query.where(Requirement.requirement_type == requirement_type)
            
            # 排序和限制
            query = query.order_by(desc(Requirement.created_at)).limit(limit)
            
            result = await session.execute(query)
            requirements = result.scalars().all()
            
            logger.info(f"搜索关键词 '{keyword}' 找到 {len(requirements)} 个需求")
            return requirements
            
        except Exception as e:
            logger.error(f"搜索需求失败: {str(e)}")
            return []


class TestCaseRequirementRepository(BaseRepository[TestCaseRequirement]):
    """测试用例需求关联仓储类"""
    
    def __init__(self):
        super().__init__(TestCaseRequirement)
    
    async def create_test_case_requirement(
        self,
        session: AsyncSession,
        relation_data: TestCaseRequirementCreateRequest
    ) -> TestCaseRequirement:
        """创建测试用例需求关联"""
        try:
            relation = TestCaseRequirement(
                id=str(uuid.uuid4()),
                test_case_id=relation_data.test_case_id,
                requirement_id=relation_data.requirement_id,
                coverage_type=relation_data.coverage_type,
                coverage_description=relation_data.coverage_description
            )
            
            session.add(relation)
            await session.flush()
            await session.commit()
            await session.refresh(relation)
            
            logger.info(f"创建测试用例需求关联成功: {relation.id}")
            return relation
            
        except Exception as e:
            await session.rollback()
            logger.error(f"创建测试用例需求关联失败: {str(e)}")
            raise
    
    async def batch_create_test_case_requirements(
        self,
        session: AsyncSession,
        test_case_id: str,
        requirement_ids: List[str],
        coverage_type: str = "full"
    ) -> List[TestCaseRequirement]:
        """批量创建测试用例需求关联"""
        try:
            created_relations = []
            
            for req_id in requirement_ids:
                relation = TestCaseRequirement(
                    id=str(uuid.uuid4()),
                    test_case_id=test_case_id,
                    requirement_id=req_id,
                    coverage_type=coverage_type
                )
                
                session.add(relation)
                created_relations.append(relation)
            
            await session.flush()
            await session.commit()
            
            # 刷新所有对象
            for relation in created_relations:
                await session.refresh(relation)
            
            logger.info(f"批量创建测试用例需求关联成功: {len(created_relations)} 个")
            return created_relations
            
        except Exception as e:
            await session.rollback()
            logger.error(f"批量创建测试用例需求关联失败: {str(e)}")
            raise
    
    async def get_requirements_by_test_case(
        self,
        session: AsyncSession,
        test_case_id: str
    ) -> List[TestCaseRequirement]:
        """获取测试用例关联的需求"""
        try:
            query = select(TestCaseRequirement).options(
                selectinload(TestCaseRequirement.requirement)
            ).where(TestCaseRequirement.test_case_id == test_case_id)
            
            result = await session.execute(query)
            relations = result.scalars().all()
            
            logger.info(f"测试用例 {test_case_id} 关联了 {len(relations)} 个需求")
            return relations
            
        except Exception as e:
            logger.error(f"查询测试用例需求关联失败: {str(e)}")
            return []
    
    async def get_test_cases_by_requirement(
        self,
        session: AsyncSession,
        requirement_id: str
    ) -> List[TestCaseRequirement]:
        """获取需求关联的测试用例（包含测试用例详细信息）"""
        try:
            # 使用JOIN查询，同时获取测试用例信息
            query = select(TestCaseRequirement, TestCase).join(
                TestCase, TestCaseRequirement.test_case_id == TestCase.id
            ).where(
                TestCaseRequirement.requirement_id == requirement_id
            ).order_by(TestCaseRequirement.created_at.desc())

            result = await session.execute(query)
            rows = result.all()

            # 将测试用例信息附加到关联对象上
            relations = []
            for relation, test_case in rows:
                # 将测试用例信息附加到关联对象
                relation.test_case = test_case
                relations.append(relation)

            logger.info(f"需求 {requirement_id} 关联了 {len(relations)} 个测试用例")
            return relations

        except Exception as e:
            logger.error(f"查询需求测试用例关联失败: {str(e)}")
            return []
    
    async def get_requirement_coverage_stats(
        self,
        session: AsyncSession,
        project_id: str
    ) -> RequirementCoverageStats:
        """获取需求覆盖统计"""
        try:
            # 总需求数
            total_query = select(func.count(Requirement.id)).where(
                Requirement.project_id == project_id
            )
            total_result = await session.execute(total_query)
            total_requirements = total_result.scalar() or 0
            
            # 已覆盖需求数
            covered_query = select(func.count(func.distinct(TestCaseRequirement.requirement_id))).select_from(
                TestCaseRequirement.__table__.join(Requirement.__table__)
            ).where(Requirement.project_id == project_id)
            covered_result = await session.execute(covered_query)
            covered_requirements = covered_result.scalar() or 0
            
            # 计算覆盖率
            coverage_rate = (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0.0
            uncovered_requirements = total_requirements - covered_requirements
            
            # 按类型分组统计
            type_query = select(
                Requirement.requirement_type,
                func.count(Requirement.id)
            ).where(
                Requirement.project_id == project_id
            ).group_by(Requirement.requirement_type)
            type_result = await session.execute(type_query)
            requirements_by_type = {row[0]: row[1] for row in type_result}
            
            # 按优先级分组统计
            priority_query = select(
                Requirement.priority,
                func.count(Requirement.id)
            ).where(
                Requirement.project_id == project_id
            ).group_by(Requirement.priority)
            priority_result = await session.execute(priority_query)
            requirements_by_priority = {row[0]: row[1] for row in priority_result}
            
            return RequirementCoverageStats(
                total_requirements=total_requirements,
                covered_requirements=covered_requirements,
                uncovered_requirements=uncovered_requirements,
                coverage_rate=round(coverage_rate, 2),
                requirements_by_type=requirements_by_type,
                requirements_by_priority=requirements_by_priority
            )
            
        except Exception as e:
            logger.error(f"获取需求覆盖统计失败: {str(e)}")
            return RequirementCoverageStats(
                total_requirements=0,
                covered_requirements=0,
                uncovered_requirements=0,
                coverage_rate=0.0,
                requirements_by_type={},
                requirements_by_priority={}
            )
