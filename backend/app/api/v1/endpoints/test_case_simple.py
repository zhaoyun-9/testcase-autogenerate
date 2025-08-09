"""
简化的测试用例API端点 - 避免tags字段问题
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, text
from loguru import logger
import uuid
from datetime import datetime

from app.database.connection import db_manager
from app.core.enum_utils import validate_enum_value, get_enum_choices
from app.core.enums import TestType, TestLevel, Priority, TestCaseStatus

router = APIRouter()


class SimpleTestCaseResponse(BaseModel):
    """简化的测试用例响应模型"""
    id: str
    title: str
    description: Optional[str]
    test_type: str
    test_level: str
    priority: str
    status: str
    preconditions: Optional[str]
    expected_results: Optional[str]
    created_at: str
    updated_at: Optional[str]


class SimplePaginatedResponse(BaseModel):
    """简化的分页响应"""
    data: List[SimpleTestCaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/simple", response_model=SimplePaginatedResponse)
async def get_test_cases_simple(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取测试用例列表（简化版本，避免tags字段问题）
    """
    try:
        async with db_manager.get_session() as session:
            # 构建基础查询 - 直接使用SQL避免ORM问题
            base_sql = """
                SELECT 
                    id, title, description, test_type, test_level, priority, status,
                    preconditions, expected_results, created_at, updated_at
                FROM test_cases
            """
            
            count_sql = "SELECT COUNT(*) FROM test_cases"
            
            # 添加搜索条件
            where_conditions = []
            params = {}
            
            if search:
                where_conditions.append(
                    "(title LIKE :search OR description LIKE :search OR expected_results LIKE :search)"
                )
                params['search'] = f"%{search}%"
            
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                base_sql += where_clause
                count_sql += where_clause
            
            # 获取总数
            count_result = await session.execute(text(count_sql), params)
            total = count_result.scalar()
            
            # 分页查询
            offset = (page - 1) * page_size
            query_sql = base_sql + f" ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}"
            
            result = await session.execute(text(query_sql), params)
            rows = result.fetchall()
            
            # 转换为响应模型
            test_case_responses = []
            for row in rows:
                test_case_responses.append(SimpleTestCaseResponse(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    test_type=row[3],
                    test_level=row[4],
                    priority=row[5],
                    status=row[6],
                    preconditions=row[7],
                    expected_results=row[8],
                    created_at=row[9].isoformat() if row[9] else "",
                    updated_at=row[10].isoformat() if row[10] else None
                ))
            
            total_pages = (total + page_size - 1) // page_size
            
            return SimplePaginatedResponse(
                data=test_case_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
    except Exception as e:
        logger.error(f"获取测试用例列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试用例列表失败: {str(e)}")


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


@router.get("/count")
async def get_test_case_count():
    """
    获取测试用例总数
    """
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM test_cases"))
            count = result.scalar()
            return {"count": count}
            
    except Exception as e:
        logger.error(f"获取测试用例总数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试用例总数失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    try:
        async with db_manager.get_session() as session:
            await session.execute(text("SELECT 1"))
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
            
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
