"""
测试用例管理API端点
提供测试用例的CRUD操作、查询、统计等功能
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from loguru import logger
import uuid
from datetime import datetime

from app.database.connection import db_manager
from app.database.models.test_case import TestCase, TestType, TestLevel, Priority, TestCaseStatus, Project, Category, Tag, TestCaseTag
from app.core.enum_utils import validate_enum_value, validate_enum_list, get_enum_choices

router = APIRouter()


class TestCaseQuery(BaseModel):
    """测试用例查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    test_type: Optional[List[str]] = Field(None, description="测试类型过滤")
    test_level: Optional[List[str]] = Field(None, description="测试级别过滤")
    priority: Optional[List[str]] = Field(None, description="优先级过滤")
    status: Optional[List[str]] = Field(None, description="状态过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    session_id: Optional[str] = Field(None, description="会话ID过滤")


class TestCaseResponse(BaseModel):
    """测试用例响应模型"""
    id: str
    title: str
    description: Optional[str]
    test_type: str
    test_level: str
    priority: str
    status: str
    preconditions: Optional[str]
    test_steps: List[dict]
    expected_results: Optional[str]
    tags: List[str]
    category: Optional[str]
    session_id: Optional[str]
    created_at: str
    updated_at: Optional[str]


class PaginatedTestCaseResponse(BaseModel):
    """分页测试用例响应"""
    data: List[TestCaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestCaseStats(BaseModel):
    """测试用例统计信息"""
    total_count: int
    by_type: dict
    by_priority: dict
    by_status: dict
    by_level: dict
    recent_activity: dict


class TestCaseCreateRequest(BaseModel):
    """创建测试用例请求"""
    title: str
    description: Optional[str] = None
    test_type: str
    test_level: str
    priority: str = "P2"
    status: str = "draft"
    preconditions: Optional[str] = None
    test_steps: List[dict] = []
    expected_results: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = None
    session_id: Optional[str] = None


class TestCaseUpdateRequest(BaseModel):
    """更新测试用例请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[str] = None
    test_level: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[dict]] = None
    expected_results: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[str]


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求"""
    ids: List[str]
    status: str


@router.post("", response_model=TestCaseResponse)
async def create_test_case(request: TestCaseCreateRequest):
    """
    创建测试用例
    """
    try:
        # 验证枚举值
        test_type = validate_enum_value(request.test_type, TestType, "测试类型")
        test_level = validate_enum_value(request.test_level, TestLevel, "测试级别")
        priority = validate_enum_value(request.priority, Priority, "优先级")
        status = validate_enum_value(request.status, TestCaseStatus, "状态")

        async with db_manager.get_session() as session:
            # 创建新的测试用例
            test_case = TestCase(
                id=str(uuid.uuid4()),
                title=request.title,
                description=request.description,
                test_type=test_type,
                test_level=test_level,
                priority=priority,
                status=status,
                preconditions=request.preconditions,
                test_steps=request.test_steps,
                expected_results=request.expected_results,
                category_id=request.category,
                session_id=request.session_id,
                project_id=request.project_id or 'default-project-001'
            )

            session.add(test_case)
            await session.commit()
            await session.refresh(test_case)

            logger.info(f"创建测试用例成功: {test_case.id}")

            return TestCaseResponse(
                id=test_case.id,
                title=test_case.title,
                description=test_case.description,
                test_type=test_case.test_type,
                test_level=test_case.test_level,
                priority=test_case.priority,
                status=test_case.status,
                preconditions=test_case.preconditions,
                test_steps=test_case.test_steps or [],
                expected_results=test_case.expected_results,
                tags=[],  # TODO: 实现标签关联
                category=test_case.category.name if test_case.category else None,
                session_id=test_case.session_id,
                created_at=test_case.created_at.isoformat() if test_case.created_at else "",
                updated_at=test_case.updated_at.isoformat() if test_case.updated_at else None
            )

    except Exception as e:
        logger.error(f"创建测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建测试用例失败: {str(e)}")


@router.get("", response_model=PaginatedTestCaseResponse)
async def get_test_cases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    test_type: Optional[List[str]] = Query(None, description="测试类型过滤"),
    test_level: Optional[List[str]] = Query(None, description="测试级别过滤"),
    priority: Optional[List[str]] = Query(None, description="优先级过滤"),
    status: Optional[List[str]] = Query(None, description="状态过滤"),
    tags: Optional[List[str]] = Query(None, description="标签过滤"),
    session_id: Optional[str] = Query(None, description="会话ID过滤")
):
    """
    获取测试用例列表（分页）
    """
    try:
        # 验证枚举值
        validated_test_types = validate_enum_list(test_type, TestType, "测试类型") if test_type else None
        validated_test_levels = validate_enum_list(test_level, TestLevel, "测试级别") if test_level else None
        validated_priorities = validate_enum_list(priority, Priority, "优先级") if priority else None
        validated_statuses = validate_enum_list(status, TestCaseStatus, "状态") if status else None

        async with db_manager.get_session() as session:
            # 构建基础查询，预加载关联数据
            query = select(TestCase).options(
                selectinload(TestCase.test_case_tags).selectinload(TestCaseTag.tag),
                selectinload(TestCase.category)
            )
            count_query = select(func.count(TestCase.id))

            # 添加过滤条件
            filters = []

            if search:
                search_filter = or_(
                    TestCase.title.ilike(f"%{search}%"),
                    TestCase.description.ilike(f"%{search}%"),
                    TestCase.expected_results.ilike(f"%{search}%")
                )
                filters.append(search_filter)

            if validated_test_types:
                filters.append(TestCase.test_type.in_([t.value for t in validated_test_types]))

            if validated_test_levels:
                filters.append(TestCase.test_level.in_([l.value for l in validated_test_levels]))

            if validated_priorities:
                filters.append(TestCase.priority.in_([p.value for p in validated_priorities]))

            if validated_statuses:
                filters.append(TestCase.status.in_([s.value for s in validated_statuses]))
            
            if session_id:
                filters.append(TestCase.session_id == session_id)
            
            if tags:
                # TODO: 实现标签过滤，需要通过test_case_tags关联表
                # 暂时跳过标签过滤
                pass
            
            if filters:
                query = query.where(and_(*filters))
                count_query = count_query.where(and_(*filters))
            
            # 获取总数
            total_result = await session.execute(count_query)
            total = total_result.scalar()
            
            # 分页查询
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size).order_by(TestCase.created_at.desc())
            
            result = await session.execute(query)
            test_cases = result.scalars().all()
            
            # 转换为响应模型
            test_case_responses = []
            for tc in test_cases:
                # 获取标签
                tags = [tag_rel.tag.name for tag_rel in tc.test_case_tags] if tc.test_case_tags else []

                test_case_responses.append(TestCaseResponse(
                    id=tc.id,
                    title=tc.title,
                    description=tc.description,
                    test_type=tc.test_type,
                    test_level=tc.test_level,
                    priority=tc.priority,
                    status=tc.status,
                    preconditions=tc.preconditions,
                    test_steps=tc.test_steps or [],
                    expected_results=tc.expected_results,
                    tags=tags,
                    category=tc.category.name if tc.category else None,
                    session_id=tc.session_id,
                    created_at=tc.created_at.isoformat() if tc.created_at else "",
                    updated_at=tc.updated_at.isoformat() if tc.updated_at else None
                ))
            
            total_pages = (total + page_size - 1) // page_size
            
            return PaginatedTestCaseResponse(
                data=test_case_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
    except Exception as e:
        logger.error(f"获取测试用例列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试用例列表失败: {str(e)}")


@router.get("/stats", response_model=TestCaseStats)
async def get_test_case_stats():
    """
    获取测试用例统计信息
    """
    try:
        async with db_manager.get_session() as session:
            # 总数统计
            total_result = await session.execute(select(func.count(TestCase.id)))
            total_count = total_result.scalar()
            
            # 按类型统计
            type_stats = {}
            for test_type in TestType:
                type_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.test_type == test_type.value)
                )
                type_stats[test_type.value] = type_result.scalar()
            
            # 按优先级统计
            priority_stats = {}
            for priority in Priority:
                priority_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.priority == priority.value)
                )
                priority_stats[priority.value] = priority_result.scalar()
            
            # 按状态统计
            status_stats = {}
            for status in TestCaseStatus:
                status_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.status == status.value)
                )
                status_stats[status.value] = status_result.scalar()
            
            # 按级别统计
            level_stats = {}
            for level in TestLevel:
                level_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.test_level == level.value)
                )
                level_stats[level.value] = level_result.scalar()
            
            # 最近活动统计（这里简化处理，实际可以根据created_at字段统计）
            recent_activity = {
                "created_today": 0,
                "created_this_week": 0,
                "created_this_month": 0
            }
            
            return TestCaseStats(
                total_count=total_count,
                by_type=type_stats,
                by_priority=priority_stats,
                by_status=status_stats,
                by_level=level_stats,
                recent_activity=recent_activity
            )
            
    except Exception as e:
        logger.error(f"获取测试用例统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试用例统计失败: {str(e)}")


@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(test_case_id: str):
    """
    获取单个测试用例详情
    """
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(TestCase).where(TestCase.id == test_case_id)
            )
            test_case = result.scalar_one_or_none()
            
            if not test_case:
                raise HTTPException(status_code=404, detail="测试用例不存在")
            
            return TestCaseResponse(
                id=test_case.id,
                title=test_case.title,
                description=test_case.description,
                test_type=test_case.test_type,
                test_level=test_case.test_level,
                priority=test_case.priority,
                status=test_case.status,
                preconditions=test_case.preconditions,
                test_steps=test_case.test_steps or [],
                expected_results=test_case.expected_results,
                tags=[],  # TODO: 实现标签关联
                category=test_case.category.name if test_case.category else None,
                session_id=test_case.session_id,
                created_at=test_case.created_at.isoformat() if test_case.created_at else "",
                updated_at=test_case.updated_at.isoformat() if test_case.updated_at else None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取测试用例详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试用例详情失败: {str(e)}")


@router.delete("/{test_case_id}")
async def delete_test_case(test_case_id: str):
    """
    删除测试用例
    """
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(TestCase).where(TestCase.id == test_case_id)
            )
            test_case = result.scalar_one_or_none()
            
            if not test_case:
                raise HTTPException(status_code=404, detail="测试用例不存在")
            
            await session.delete(test_case)
            await session.commit()
            
            return {"message": "测试用例删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除测试用例失败: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_test_cases(request: BatchDeleteRequest):
    """
    批量删除测试用例
    """
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(TestCase).where(TestCase.id.in_(request.ids))
            )
            test_cases = result.scalars().all()
            
            if not test_cases:
                raise HTTPException(status_code=404, detail="没有找到要删除的测试用例")
            
            for test_case in test_cases:
                await session.delete(test_case)
            
            await session.commit()
            
            return {"message": f"成功删除 {len(test_cases)} 个测试用例"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除测试用例失败: {str(e)}")



@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(test_case_id: str, request: TestCaseUpdateRequest):
    """
    更新测试用例
    """
    try:
        async with db_manager.get_session() as session:
            # 查找测试用例
            result = await session.execute(
                select(TestCase).where(TestCase.id == test_case_id)
            )
            test_case = result.scalar_one_or_none()

            if not test_case:
                raise HTTPException(status_code=404, detail="测试用例不存在")

            # 更新字段
            update_data = request.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(test_case, field, value)

            test_case.updated_at = datetime.now()

            await session.commit()
            await session.refresh(test_case)

            logger.info(f"更新测试用例成功: {test_case_id}")

            return TestCaseResponse(
                id=test_case.id,
                title=test_case.title,
                description=test_case.description,
                test_type=test_case.test_type,
                test_level=test_case.test_level,
                priority=test_case.priority,
                status=test_case.status,
                preconditions=test_case.preconditions,
                test_steps=test_case.test_steps or [],
                expected_results=test_case.expected_results,
                tags=[],  # TODO: 实现标签关联
                category=test_case.category.name if test_case.category else None,
                session_id=test_case.session_id,
                created_at=test_case.created_at.isoformat() if test_case.created_at else "",
                updated_at=test_case.updated_at.isoformat() if test_case.updated_at else None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新测试用例失败: {str(e)}")


@router.post("/batch-update-status")
async def batch_update_status(request: BatchUpdateStatusRequest):
    """
    批量更新测试用例状态
    """
    try:
        async with db_manager.get_session() as session:
            # 更新测试用例状态
            result = await session.execute(
                select(TestCase).where(TestCase.id.in_(request.ids))
            )
            test_cases = result.scalars().all()

            if not test_cases:
                raise HTTPException(status_code=404, detail="没有找到要更新的测试用例")

            for test_case in test_cases:
                test_case.status = request.status
                test_case.updated_at = datetime.now()

            await session.commit()

            logger.info(f"批量更新测试用例状态成功: {len(test_cases)}个")
            return {"message": f"成功更新{len(test_cases)}个测试用例状态"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新测试用例状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量更新测试用例状态失败: {str(e)}")


@router.get("/enums")
async def get_test_case_enums():
    """
    获取测试用例相关的所有枚举值
    """
    return {
        "test_types": get_enum_choices(TestType),
        "test_levels": get_enum_choices(TestLevel),
        "priorities": get_enum_choices(Priority),
        "statuses": get_enum_choices(TestCaseStatus)
    }
