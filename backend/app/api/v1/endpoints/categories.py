"""
分类管理API端点 (最终版)
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import Category, Project, TestCase

router = APIRouter()

class CategoryCreateRequest(BaseModel):
    """创建分类请求"""
    name: str = Field(..., min_length=1, max_length=255, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[str] = Field(None, description="父分类ID")
    project_id: str = Field(..., description="项目ID")
    sort_order: int = Field(0, description="排序")

class CategoryUpdateRequest(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[str] = Field(None, description="父分类ID")
    sort_order: Optional[int] = Field(None, description="排序")

class CategoryResponse(BaseModel):
    """分类响应"""
    id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]
    project_id: str
    sort_order: int
    test_case_count: int = 0
    children: List['CategoryResponse'] = []
    created_at: str

    class Config:
        from_attributes = True

class CategoryListResponse(BaseModel):
    """分类列表响应"""
    items: List[CategoryResponse]
    total: int

@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    project_id: Optional[str] = Query(None, description="项目ID过滤"),
    parent_id: Optional[str] = Query(None, description="父分类ID过滤"),
    include_children: bool = Query(False, description="是否包含子分类")
):
    """获取分类列表"""
    try:
        async with db_manager.get_session() as session:
            query = select(Category)
            
            if project_id:
                query = query.where(Category.project_id == project_id)
            
            if parent_id is not None:
                query = query.where(Category.parent_id == parent_id)
            
            query = query.order_by(Category.sort_order, Category.name)
            
            result = await session.execute(query)
            categories = result.scalars().all()
            
            # 构建响应
            items = []
            for category in categories:
                # 获取测试用例数量
                test_case_count_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.category_id == category.id)
                )
                test_case_count = test_case_count_result.scalar() or 0
                
                category_response = CategoryResponse(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    parent_id=category.parent_id,
                    project_id=category.project_id,
                    sort_order=category.sort_order,
                    test_case_count=test_case_count,
                    created_at=category.created_at.isoformat()
                )
                
                # 如果需要包含子分类
                if include_children:
                    children_result = await session.execute(
                        select(Category).where(Category.parent_id == category.id)
                        .order_by(Category.sort_order, Category.name)
                    )
                    children = children_result.scalars().all()
                    
                    for child in children:
                        child_test_case_count_result = await session.execute(
                            select(func.count(TestCase.id)).where(TestCase.category_id == child.id)
                        )
                        child_test_case_count = child_test_case_count_result.scalar() or 0
                        
                        category_response.children.append(CategoryResponse(
                            id=child.id,
                            name=child.name,
                            description=child.description,
                            parent_id=child.parent_id,
                            project_id=child.project_id,
                            sort_order=child.sort_order,
                            test_case_count=child_test_case_count,
                            created_at=child.created_at.isoformat()
                        ))
                
                items.append(category_response)
            
            return CategoryListResponse(
                items=items,
                total=len(items)
            )
            
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")

@router.post("/", response_model=CategoryResponse)
async def create_category(request: CategoryCreateRequest):
    """创建分类"""
    try:
        async with db_manager.get_session() as session:
            # 验证项目存在
            project_result = await session.execute(
                select(Project).where(Project.id == request.project_id)
            )
            if not project_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 验证父分类存在（如果提供）
            if request.parent_id:
                parent_result = await session.execute(
                    select(Category).where(Category.id == request.parent_id)
                )
                if not parent_result.scalar_one_or_none():
                    raise HTTPException(status_code=404, detail="父分类不存在")
            
            # 检查同级分类名称是否重复
            existing_result = await session.execute(
                select(Category).where(
                    Category.name == request.name,
                    Category.project_id == request.project_id,
                    Category.parent_id == request.parent_id
                )
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="同级分类名称已存在")
            
            # 创建分类
            category = Category(
                id=str(uuid.uuid4()),
                name=request.name,
                description=request.description,
                parent_id=request.parent_id,
                project_id=request.project_id,
                sort_order=request.sort_order
            )
            
            session.add(category)
            await session.commit()
            await session.refresh(category)
            
            return CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_id=category.parent_id,
                project_id=category.project_id,
                sort_order=category.sort_order,
                test_case_count=0,
                created_at=category.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    """获取分类详情"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Category).where(Category.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                raise HTTPException(status_code=404, detail="分类不存在")
            
            # 获取测试用例数量
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.category_id == category.id)
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            return CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_id=category.parent_id,
                project_id=category.project_id,
                sort_order=category.sort_order,
                test_case_count=test_case_count,
                created_at=category.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类详情失败: {str(e)}")

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, request: CategoryUpdateRequest):
    """更新分类"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Category).where(Category.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                raise HTTPException(status_code=404, detail="分类不存在")
            
            # 更新字段
            if request.name is not None:
                # 检查同级分类名称是否重复
                existing_result = await session.execute(
                    select(Category).where(
                        Category.name == request.name,
                        Category.project_id == category.project_id,
                        Category.parent_id == category.parent_id,
                        Category.id != category_id
                    )
                )
                if existing_result.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="同级分类名称已存在")
                category.name = request.name
            
            if request.description is not None:
                category.description = request.description
            
            if request.parent_id is not None:
                # 验证父分类存在
                if request.parent_id:
                    parent_result = await session.execute(
                        select(Category).where(Category.id == request.parent_id)
                    )
                    if not parent_result.scalar_one_or_none():
                        raise HTTPException(status_code=404, detail="父分类不存在")
                    
                    # 防止循环引用
                    if request.parent_id == category_id:
                        raise HTTPException(status_code=400, detail="不能将分类设置为自己的父分类")
                
                category.parent_id = request.parent_id
            
            if request.sort_order is not None:
                category.sort_order = request.sort_order
            
            await session.commit()
            await session.refresh(category)
            
            # 获取测试用例数量
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.category_id == category.id)
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            return CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_id=category.parent_id,
                project_id=category.project_id,
                sort_order=category.sort_order,
                test_case_count=test_case_count,
                created_at=category.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")

@router.delete("/{category_id}")
async def delete_category(category_id: str):
    """删除分类"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Category).where(Category.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                raise HTTPException(status_code=404, detail="分类不存在")
            
            # 检查是否有子分类
            children_result = await session.execute(
                select(func.count(Category.id)).where(Category.parent_id == category_id)
            )
            children_count = children_result.scalar() or 0
            
            if children_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法删除分类，存在 {children_count} 个子分类"
                )
            
            # 检查是否有关联的测试用例
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.category_id == category_id)
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            if test_case_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法删除分类，存在 {test_case_count} 个关联的测试用例"
                )
            
            await session.delete(category)
            await session.commit()
            
            return {"message": "分类删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")

@router.get("/{category_id}/tree")
async def get_category_tree(category_id: str):
    """获取分类树结构"""
    try:
        async with db_manager.get_session() as session:
            # 获取根分类
            root_result = await session.execute(
                select(Category).where(Category.id == category_id)
            )
            root_category = root_result.scalar_one_or_none()
            
            if not root_category:
                raise HTTPException(status_code=404, detail="分类不存在")
            
            async def build_tree(category):
                # 获取子分类
                children_result = await session.execute(
                    select(Category).where(Category.parent_id == category.id)
                    .order_by(Category.sort_order, Category.name)
                )
                children = children_result.scalars().all()
                
                # 获取测试用例数量
                test_case_count_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.category_id == category.id)
                )
                test_case_count = test_case_count_result.scalar() or 0
                
                tree_node = {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "parent_id": category.parent_id,
                    "project_id": category.project_id,
                    "sort_order": category.sort_order,
                    "test_case_count": test_case_count,
                    "created_at": category.created_at.isoformat(),
                    "children": []
                }
                
                # 递归构建子树
                for child in children:
                    child_tree = await build_tree(child)
                    tree_node["children"].append(child_tree)
                
                return tree_node
            
            tree = await build_tree(root_category)
            return tree
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类树失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类树失败: {str(e)}")
