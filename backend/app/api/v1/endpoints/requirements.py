"""
需求管理API端点
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_database
from app.database.repositories.requirement_repository import RequirementRepository, TestCaseRequirementRepository
from app.database.models.requirement import (
    RequirementResponse, RequirementListResponse, RequirementCoverageStats,
    TestCaseRequirementResponse, TestCaseInfo, RequirementType, RequirementPriority, RequirementStatus
)

router = APIRouter()


@router.get("/", response_model=RequirementListResponse)
async def get_requirements(
    project_id: Optional[str] = Query(None, description="项目ID"),
    requirement_type: Optional[RequirementType] = Query(None, description="需求类型"),
    priority: Optional[RequirementPriority] = Query(None, description="优先级"),
    status: Optional[RequirementStatus] = Query(None, description="状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_database)
):
    """获取需求列表"""
    try:
        requirement_repo = RequirementRepository()
        
        if keyword:
            # 搜索需求
            requirements = await requirement_repo.search_requirements(
                session, keyword, project_id, requirement_type, page_size
            )
            total = len(requirements)
        else:
            # 分页查询需求
            offset = (page - 1) * page_size
            requirements = await requirement_repo.get_requirements_by_project(
                session, 
                project_id or requirement_repo.DEFAULT_PROJECT_ID,
                requirement_type, priority, status,
                page_size, offset
            )
            
            # 获取总数（简化处理，实际应该有专门的计数方法）
            all_requirements = await requirement_repo.get_requirements_by_project(
                session, 
                project_id or requirement_repo.DEFAULT_PROJECT_ID,
                requirement_type, priority, status,
                1000, 0  # 获取更多数据来计算总数
            )
            total = len(all_requirements)
        
        # 转换为响应模型
        requirement_responses = []
        for req in requirements:
            requirement_responses.append(RequirementResponse(
                id=req.id,
                requirement_id=req.requirement_id,
                title=req.title,
                description=req.description,
                requirement_type=RequirementType(req.requirement_type),
                priority=RequirementPriority(req.priority),
                status=RequirementStatus(req.status),
                project_id=req.project_id,
                document_id=req.document_id,
                session_id=req.session_id,
                source_file_path=req.source_file_path,
                source_section=req.source_section,
                ai_generated=req.ai_generated,
                ai_confidence=req.ai_confidence,
                ai_model_info=req.ai_model_info,
                extra_metadata=req.extra_metadata,
                created_at=req.created_at,
                updated_at=req.updated_at
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return RequirementListResponse(
            items=requirement_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求列表失败: {str(e)}")


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: str,
    session: AsyncSession = Depends(get_database)
):
    """获取需求详情"""
    try:
        requirement_repo = RequirementRepository()
        requirement = await requirement_repo.get_by_id(session, requirement_id)
        
        if not requirement:
            raise HTTPException(status_code=404, detail="需求不存在")
        
        return RequirementResponse(
            id=requirement.id,
            requirement_id=requirement.requirement_id,
            title=requirement.title,
            description=requirement.description,
            requirement_type=RequirementType(requirement.requirement_type),
            priority=RequirementPriority(requirement.priority),
            status=RequirementStatus(requirement.status),
            project_id=requirement.project_id,
            document_id=requirement.document_id,
            session_id=requirement.session_id,
            source_file_path=requirement.source_file_path,
            source_section=requirement.source_section,
            ai_generated=requirement.ai_generated,
            ai_confidence=requirement.ai_confidence,
            ai_model_info=requirement.ai_model_info,
            extra_metadata=requirement.extra_metadata,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求详情失败: {str(e)}")


@router.get("/{requirement_id}/test-cases", response_model=List[TestCaseRequirementResponse])
async def get_requirement_test_cases(
    requirement_id: str,
    session: AsyncSession = Depends(get_database)
):
    """获取需求关联的测试用例"""
    try:
        tcr_repo = TestCaseRequirementRepository()
        relations = await tcr_repo.get_test_cases_by_requirement(session, requirement_id)
        
        result = []
        for relation in relations:
            # 构建测试用例信息
            test_case_info = None
            if hasattr(relation, 'test_case') and relation.test_case:
                test_case_info = TestCaseInfo(
                    id=relation.test_case.id,
                    title=relation.test_case.title,
                    description=relation.test_case.description,
                    test_type=relation.test_case.test_type.value if hasattr(relation.test_case.test_type, 'value') else relation.test_case.test_type,
                    test_level=relation.test_case.test_level.value if hasattr(relation.test_case.test_level, 'value') else relation.test_case.test_level,
                    priority=relation.test_case.priority.value if hasattr(relation.test_case.priority, 'value') else relation.test_case.priority,
                    status=relation.test_case.status.value if hasattr(relation.test_case.status, 'value') else relation.test_case.status,
                    created_at=relation.test_case.created_at
                )

            result.append(TestCaseRequirementResponse(
                id=relation.id,
                test_case_id=relation.test_case_id,
                requirement_id=relation.requirement_id,
                coverage_type=relation.coverage_type,
                coverage_description=relation.coverage_description,
                created_at=relation.created_at,
                test_case=test_case_info
            ))

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求测试用例失败: {str(e)}")


@router.get("/stats/coverage", response_model=RequirementCoverageStats)
async def get_requirement_coverage_stats(
    project_id: Optional[str] = Query(None, description="项目ID"),
    session: AsyncSession = Depends(get_database)
):
    """获取需求覆盖统计"""
    try:
        tcr_repo = TestCaseRequirementRepository()
        requirement_repo = RequirementRepository()
        
        stats = await tcr_repo.get_requirement_coverage_stats(
            session, 
            project_id or requirement_repo.DEFAULT_PROJECT_ID
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求覆盖统计失败: {str(e)}")


@router.get("/stats/by-type")
async def get_requirements_by_type(
    project_id: Optional[str] = Query(None, description="项目ID"),
    session: AsyncSession = Depends(get_database)
):
    """按类型统计需求"""
    try:
        requirement_repo = RequirementRepository()
        
        # 获取所有需求
        requirements = await requirement_repo.get_requirements_by_project(
            session, 
            project_id or requirement_repo.DEFAULT_PROJECT_ID,
            limit=1000
        )
        
        # 按类型分组统计
        type_stats = {}
        for req in requirements:
            req_type = req.requirement_type
            if req_type not in type_stats:
                type_stats[req_type] = {
                    "total": 0,
                    "draft": 0,
                    "approved": 0,
                    "rejected": 0,
                    "deprecated": 0
                }
            type_stats[req_type]["total"] += 1
            type_stats[req_type][req.status] += 1
        
        return type_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求类型统计失败: {str(e)}")


@router.get("/stats/by-priority")
async def get_requirements_by_priority(
    project_id: Optional[str] = Query(None, description="项目ID"),
    session: AsyncSession = Depends(get_database)
):
    """按优先级统计需求"""
    try:
        requirement_repo = RequirementRepository()
        
        # 获取所有需求
        requirements = await requirement_repo.get_requirements_by_project(
            session, 
            project_id or requirement_repo.DEFAULT_PROJECT_ID,
            limit=1000
        )
        
        # 按优先级分组统计
        priority_stats = {}
        for req in requirements:
            priority = req.priority
            if priority not in priority_stats:
                priority_stats[priority] = {
                    "total": 0,
                    "draft": 0,
                    "approved": 0,
                    "rejected": 0,
                    "deprecated": 0
                }
            priority_stats[priority]["total"] += 1
            priority_stats[priority][req.status] += 1
        
        return priority_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求优先级统计失败: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_requirements_by_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_database)
):
    """根据会话ID获取需求"""
    try:
        requirement_repo = RequirementRepository()
        requirements = await requirement_repo.get_requirements_by_session(db_session, session_id)
        
        return [
            {
                "id": req.id,
                "requirement_id": req.requirement_id,
                "title": req.title,
                "description": req.description,
                "requirement_type": req.requirement_type,
                "priority": req.priority,
                "status": req.status,
                "created_at": req.created_at.isoformat()
            }
            for req in requirements
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话需求失败: {str(e)}")
