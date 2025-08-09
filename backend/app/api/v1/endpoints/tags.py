"""
标签管理API端点 (最终版)
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import Tag, Project, TestCaseTag

router = APIRouter()

class TagCreateRequest(BaseModel):
    """创建标签请求"""
    name: str = Field(..., min_length=1, max_length=100, description="标签名称")
    color: str = Field("#1890ff", description="标签颜色")
    project_id: Optional[str] = Field(None, description="项目ID")

class TagUpdateRequest(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="标签名称")
    color: Optional[str] = Field(None, description="标签颜色")

class TagResponse(BaseModel):
    """标签响应"""
    id: str
    name: str
    color: str
    project_id: Optional[str]
    usage_count: int
    created_at: str

    class Config:
        from_attributes = True

class TagListResponse(BaseModel):
    """标签列表响应"""
    items: List[TagResponse]
    total: int

@router.get("/", response_model=TagListResponse)
async def get_tags(
    project_id: Optional[str] = Query(None, description="项目ID过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    order_by: str = Query("usage_count", description="排序字段: name, usage_count, created_at")
):
    """获取标签列表"""
    try:
        async with db_manager.get_session() as session:
            query = select(Tag)
            
            if project_id:
                query = query.where(Tag.project_id == project_id)
            
            if search:
                query = query.where(Tag.name.contains(search))
            
            # 排序
            if order_by == "name":
                query = query.order_by(Tag.name)
            elif order_by == "usage_count":
                query = query.order_by(desc(Tag.usage_count))
            elif order_by == "created_at":
                query = query.order_by(desc(Tag.created_at))
            else:
                query = query.order_by(desc(Tag.usage_count))
            
            result = await session.execute(query)
            tags = result.scalars().all()
            
            items = [
                TagResponse(
                    id=tag.id,
                    name=tag.name,
                    color=tag.color,
                    project_id=tag.project_id,
                    usage_count=tag.usage_count,
                    created_at=tag.created_at.isoformat()
                )
                for tag in tags
            ]
            
            return TagListResponse(
                items=items,
                total=len(items)
            )
            
    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")

@router.post("/", response_model=TagResponse)
async def create_tag(request: TagCreateRequest):
    """创建标签"""
    try:
        async with db_manager.get_session() as session:
            # 验证项目存在（如果提供）
            if request.project_id:
                project_result = await session.execute(
                    select(Project).where(Project.id == request.project_id)
                )
                if not project_result.scalar_one_or_none():
                    raise HTTPException(status_code=404, detail="项目不存在")
            
            # 检查标签名称是否已存在
            existing_result = await session.execute(
                select(Tag).where(
                    Tag.name == request.name,
                    Tag.project_id == request.project_id
                )
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="标签名称已存在")
            
            # 创建标签
            tag = Tag(
                id=str(uuid.uuid4()),
                name=request.name,
                color=request.color,
                project_id=request.project_id,
                usage_count=0
            )
            
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
            
            return TagResponse(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                project_id=tag.project_id,
                usage_count=tag.usage_count,
                created_at=tag.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建标签失败: {str(e)}")

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str):
    """获取标签详情"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Tag).where(Tag.id == tag_id)
            )
            tag = result.scalar_one_or_none()
            
            if not tag:
                raise HTTPException(status_code=404, detail="标签不存在")
            
            return TagResponse(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                project_id=tag.project_id,
                usage_count=tag.usage_count,
                created_at=tag.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取标签详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签详情失败: {str(e)}")

@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, request: TagUpdateRequest):
    """更新标签"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Tag).where(Tag.id == tag_id)
            )
            tag = result.scalar_one_or_none()
            
            if not tag:
                raise HTTPException(status_code=404, detail="标签不存在")
            
            # 更新字段
            if request.name is not None:
                # 检查标签名称是否已存在
                existing_result = await session.execute(
                    select(Tag).where(
                        Tag.name == request.name,
                        Tag.project_id == tag.project_id,
                        Tag.id != tag_id
                    )
                )
                if existing_result.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="标签名称已存在")
                tag.name = request.name
            
            if request.color is not None:
                tag.color = request.color
            
            await session.commit()
            await session.refresh(tag)
            
            return TagResponse(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                project_id=tag.project_id,
                usage_count=tag.usage_count,
                created_at=tag.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新标签失败: {str(e)}")

@router.delete("/{tag_id}")
async def delete_tag(tag_id: str):
    """删除标签"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Tag).where(Tag.id == tag_id)
            )
            tag = result.scalar_one_or_none()
            
            if not tag:
                raise HTTPException(status_code=404, detail="标签不存在")
            
            # 检查是否有关联的测试用例
            usage_count_result = await session.execute(
                select(func.count(TestCaseTag.id)).where(TestCaseTag.tag_id == tag_id)
            )
            usage_count = usage_count_result.scalar() or 0
            
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法删除标签，存在 {usage_count} 个关联的测试用例"
                )
            
            await session.delete(tag)
            await session.commit()
            
            return {"message": "标签删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除标签失败: {str(e)}")

@router.get("/{tag_id}/test-cases")
async def get_tag_test_cases(tag_id: str):
    """获取标签关联的测试用例"""
    try:
        async with db_manager.get_session() as session:
            # 验证标签存在
            tag_result = await session.execute(
                select(Tag).where(Tag.id == tag_id)
            )
            tag = tag_result.scalar_one_or_none()
            
            if not tag:
                raise HTTPException(status_code=404, detail="标签不存在")
            
            # 获取关联的测试用例
            from app.database.models.test_case import TestCase
            test_cases_result = await session.execute(
                select(TestCase)
                .join(TestCaseTag, TestCase.id == TestCaseTag.test_case_id)
                .where(TestCaseTag.tag_id == tag_id)
                .order_by(desc(TestCase.updated_at))
            )
            test_cases = test_cases_result.scalars().all()
            
            return {
                "tag": {
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color
                },
                "test_cases": [
                    {
                        "id": tc.id,
                        "title": tc.title,
                        "test_type": tc.test_type,
                        "test_level": tc.test_level,
                        "priority": tc.priority,
                        "status": tc.status,
                        "created_at": tc.created_at.isoformat()
                    }
                    for tc in test_cases
                ],
                "total": len(test_cases)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取标签关联测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签关联测试用例失败: {str(e)}")

@router.post("/batch")
async def create_tags_batch(tags: List[TagCreateRequest]):
    """批量创建标签"""
    try:
        async with db_manager.get_session() as session:
            created_tags = []
            
            for tag_request in tags:
                # 验证项目存在（如果提供）
                if tag_request.project_id:
                    project_result = await session.execute(
                        select(Project).where(Project.id == tag_request.project_id)
                    )
                    if not project_result.scalar_one_or_none():
                        continue  # 跳过无效项目的标签
                
                # 检查标签名称是否已存在
                existing_result = await session.execute(
                    select(Tag).where(
                        Tag.name == tag_request.name,
                        Tag.project_id == tag_request.project_id
                    )
                )
                if existing_result.scalar_one_or_none():
                    continue  # 跳过已存在的标签
                
                # 创建标签
                tag = Tag(
                    id=str(uuid.uuid4()),
                    name=tag_request.name,
                    color=tag_request.color,
                    project_id=tag_request.project_id,
                    usage_count=0
                )
                
                session.add(tag)
                created_tags.append(tag)
            
            await session.commit()
            
            # 刷新所有创建的标签
            for tag in created_tags:
                await session.refresh(tag)
            
            return {
                "created_count": len(created_tags),
                "tags": [
                    TagResponse(
                        id=tag.id,
                        name=tag.name,
                        color=tag.color,
                        project_id=tag.project_id,
                        usage_count=tag.usage_count,
                        created_at=tag.created_at.isoformat()
                    )
                    for tag in created_tags
                ]
            }
            
    except Exception as e:
        logger.error(f"批量创建标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建标签失败: {str(e)}")

@router.get("/popular/{project_id}")
async def get_popular_tags(project_id: str, limit: int = Query(10, ge=1, le=50)):
    """获取热门标签"""
    try:
        async with db_manager.get_session() as session:
            # 验证项目存在
            project_result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            if not project_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 获取热门标签
            result = await session.execute(
                select(Tag)
                .where(Tag.project_id == project_id)
                .where(Tag.usage_count > 0)
                .order_by(desc(Tag.usage_count))
                .limit(limit)
            )
            tags = result.scalars().all()
            
            return [
                TagResponse(
                    id=tag.id,
                    name=tag.name,
                    color=tag.color,
                    project_id=tag.project_id,
                    usage_count=tag.usage_count,
                    created_at=tag.created_at.isoformat()
                )
                for tag in tags
            ]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取热门标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热门标签失败: {str(e)}")
