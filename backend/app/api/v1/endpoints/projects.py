"""
项目管理API端点 (最终版)
基于最终版数据库结构的项目管理接口
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, delete
from sqlalchemy.orm import selectinload
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import Project, TestCase, Category, Tag, ProjectStatus
from app.core.enum_utils import get_enum_choices

router = APIRouter()

# Pydantic模型
class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")

class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")

class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    test_case_count: int = 0
    category_count: int = 0
    tag_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    """项目详情响应"""
    recent_test_cases: List[dict] = []
    recent_activities: List[dict] = []
    statistics: dict = {}

class ProjectListResponse(BaseModel):
    """项目列表响应"""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int

class ProjectStatsResponse(BaseModel):
    """项目统计响应"""
    total_projects: int
    active_projects: int
    archived_projects: int
    total_test_cases: int
    recent_activity: List[dict] = []

class ProjectActivityResponse(BaseModel):
    """项目活动响应"""
    id: str
    type: str
    description: str
    user: str
    created_at: str
    metadata: Optional[dict] = None

class ProjectActivityListResponse(BaseModel):
    """项目活动列表响应"""
    items: List[ProjectActivityResponse]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态过滤")
):
    """获取项目列表"""
    try:
        # 验证status参数
        project_status = None
        if status:
            try:
                # 尝试直接匹配
                project_status = ProjectStatus(status)
            except ValueError:
                try:
                    # 尝试大写匹配
                    project_status = ProjectStatus(status.upper())
                except ValueError:
                    # 尝试通过枚举名匹配
                    status_upper = status.upper()
                    for ps in ProjectStatus:
                        if ps.name == status_upper:
                            project_status = ps
                            break

                    if not project_status:
                        raise HTTPException(
                            status_code=400,
                            detail=f"无效的状态值: {status}. 可选值: {[s.value for s in ProjectStatus]} 或 {[s.name.lower() for s in ProjectStatus]}"
                        )

        async with db_manager.get_session() as session:
            # 构建查询
            query = select(Project)

            # 搜索过滤
            if search:
                query = query.where(Project.name.contains(search))

            # 状态过滤
            if project_status:
                query = query.where(Project.status == project_status)
            
            # 排序
            query = query.order_by(desc(Project.updated_at))
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # 执行查询
            result = await session.execute(query)
            projects = result.scalars().all()
            
            # 获取统计信息
            project_responses = []
            for project in projects:
                # 获取测试用例数量
                test_case_count_result = await session.execute(
                    select(func.count(TestCase.id)).where(TestCase.project_id == project.id)
                )
                test_case_count = test_case_count_result.scalar() or 0
                
                # 获取分类数量
                category_count_result = await session.execute(
                    select(func.count(Category.id)).where(Category.project_id == project.id)
                )
                category_count = category_count_result.scalar() or 0
                
                # 获取标签数量
                tag_count_result = await session.execute(
                    select(func.count(Tag.id)).where(Tag.project_id == project.id)
                )
                tag_count = tag_count_result.scalar() or 0
                
                # 确保状态是有效的ProjectStatus枚举
                try:
                    project_status = ProjectStatus(project.status) if isinstance(project.status, str) else project.status
                except ValueError:
                    # 如果状态无效，使用默认状态
                    project_status = ProjectStatus.ACTIVE
                    logger.warning(f"项目 {project.id} 的状态 '{project.status}' 无效，使用默认状态 'active'")

                project_responses.append(ProjectResponse(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    status=project_status,
                    test_case_count=test_case_count,
                    category_count=category_count,
                    tag_count=tag_count,
                    created_at=project.created_at.isoformat(),
                    updated_at=project.updated_at.isoformat()
                ))
            
            return ProjectListResponse(
                items=project_responses,
                total=total,
                page=page,
                page_size=page_size
            )

    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.get("/stats", response_model=ProjectStatsResponse)
async def get_projects_stats():
    """获取项目总体统计信息"""
    try:
        async with db_manager.get_session() as session:
            # 总项目数
            total_projects_result = await session.execute(
                select(func.count(Project.id))
            )
            total_projects = total_projects_result.scalar() or 0

            # 活跃项目数
            active_projects_result = await session.execute(
                select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)
            )
            active_projects = active_projects_result.scalar() or 0

            # 已归档项目数
            archived_projects_result = await session.execute(
                select(func.count(Project.id)).where(Project.status == ProjectStatus.ARCHIVED)
            )
            archived_projects = archived_projects_result.scalar() or 0

            # 总测试用例数
            total_test_cases_result = await session.execute(
                select(func.count(TestCase.id))
            )
            total_test_cases = total_test_cases_result.scalar() or 0

            # 最近活动（这里简化处理，实际应该有专门的活动记录表）
            recent_activity = []

            return ProjectStatsResponse(
                total_projects=total_projects,
                active_projects=active_projects,
                archived_projects=archived_projects,
                total_test_cases=total_test_cases,
                recent_activity=recent_activity
            )

    except Exception as e:
        logger.error(f"获取项目统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目统计失败: {str(e)}")

@router.post("/", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest):
    """创建项目"""
    try:
        async with db_manager.get_session() as session:
            # 检查项目名称是否已存在
            existing_result = await session.execute(
                select(Project).where(Project.name == request.name)
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="项目名称已存在")
            
            # 创建项目
            import uuid
            project = Project(
                id=str(uuid.uuid4()),
                name=request.name,
                description=request.description,
                status=ProjectStatus.ACTIVE
            )
            
            session.add(project)
            await session.commit()
            await session.refresh(project)
            
            return ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                test_case_count=0,
                category_count=0,
                tag_count=0,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """获取项目详情"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 获取统计信息
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.project_id == project.id)
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            category_count_result = await session.execute(
                select(func.count(Category.id)).where(Category.project_id == project.id)
            )
            category_count = category_count_result.scalar() or 0
            
            tag_count_result = await session.execute(
                select(func.count(Tag.id)).where(Tag.project_id == project.id)
            )
            tag_count = tag_count_result.scalar() or 0
            
            # 确保状态是有效的ProjectStatus枚举
            try:
                project_status = ProjectStatus(project.status) if isinstance(project.status, str) else project.status
            except ValueError:
                # 如果状态无效，使用默认状态
                project_status = ProjectStatus.ACTIVE
                logger.warning(f"项目 {project.id} 的状态 '{project.status}' 无效，使用默认状态 'active'")

            return ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project_status,
                test_case_count=test_case_count,
                category_count=category_count,
                tag_count=tag_count,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """更新项目"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 更新字段
            if request.name is not None:
                # 检查名称是否已存在
                existing_result = await session.execute(
                    select(Project).where(
                        Project.name == request.name,
                        Project.id != project_id
                    )
                )
                if existing_result.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="项目名称已存在")
                project.name = request.name
            
            if request.description is not None:
                project.description = request.description
            
            if request.status is not None:
                project.status = request.status
            
            await session.commit()
            await session.refresh(project)
            
            # 获取统计信息
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.project_id == project.id)
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            category_count_result = await session.execute(
                select(func.count(Category.id)).where(Category.project_id == project.id)
            )
            category_count = category_count_result.scalar() or 0
            
            tag_count_result = await session.execute(
                select(func.count(Tag.id)).where(Tag.project_id == project.id)
            )
            tag_count = tag_count_result.scalar() or 0
            
            # 确保状态是有效的ProjectStatus枚举
            try:
                project_status = ProjectStatus(project.status) if isinstance(project.status, str) else project.status
            except ValueError:
                # 如果状态无效，使用默认状态
                project_status = ProjectStatus.ACTIVE
                logger.warning(f"项目 {project.id} 的状态 '{project.status}' 无效，使用默认状态 'active'")

            return ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project_status,
                test_case_count=test_case_count,
                category_count=category_count,
                tag_count=tag_count,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新项目失败: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 检查是否有关联的测试用例
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.project_id == project.id)
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            if test_case_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法删除项目，存在 {test_case_count} 个关联的测试用例"
                )
            
            await session.delete(project)
            await session.commit()
            
            return {"message": "项目删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str):
    """获取项目统计信息"""
    try:
        async with db_manager.get_session() as session:
            # 验证项目存在
            project_result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 获取详细统计
            stats = {}
            
            # 测试用例统计
            test_case_stats_result = await session.execute(
                select(
                    TestCase.test_type,
                    TestCase.test_level,
                    TestCase.priority,
                    TestCase.status,
                    func.count(TestCase.id).label('count')
                ).where(TestCase.project_id == project_id)
                .group_by(TestCase.test_type, TestCase.test_level, TestCase.priority, TestCase.status)
            )
            
            stats['test_cases'] = {
                'by_type': {},
                'by_level': {},
                'by_priority': {},
                'by_status': {},
                'total': 0
            }
            
            for row in test_case_stats_result:
                stats['test_cases']['by_type'][row.test_type] = stats['test_cases']['by_type'].get(row.test_type, 0) + row.count
                stats['test_cases']['by_level'][row.test_level] = stats['test_cases']['by_level'].get(row.test_level, 0) + row.count
                stats['test_cases']['by_priority'][row.priority] = stats['test_cases']['by_priority'].get(row.priority, 0) + row.count
                stats['test_cases']['by_status'][row.status] = stats['test_cases']['by_status'].get(row.status, 0) + row.count
                stats['test_cases']['total'] += row.count
            
            return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目统计失败: {str(e)}")

@router.post("/batch-delete")
async def batch_delete_projects(project_ids: List[str]):
    """批量删除项目"""
    try:
        async with db_manager.get_session() as session:
            deleted_count = 0

            for project_id in project_ids:
                # 验证项目存在
                project_result = await session.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = project_result.scalar_one_or_none()

                if project:
                    # 删除相关的测试用例
                    await session.execute(
                        delete(TestCase).where(TestCase.project_id == project_id)
                    )

                    # 删除项目
                    await session.delete(project)
                    deleted_count += 1

            await session.commit()

            return {
                "message": f"成功删除 {deleted_count} 个项目",
                "deleted_count": deleted_count
            }

    except Exception as e:
        logger.error(f"批量删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除项目失败: {str(e)}")

@router.post("/{project_id}/duplicate")
async def duplicate_project(project_id: str, name: str):
    """复制项目"""
    try:
        async with db_manager.get_session() as session:
            # 获取原项目
            original_project_result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            original_project = original_project_result.scalar_one_or_none()

            if not original_project:
                raise HTTPException(status_code=404, detail="项目不存在")

            # 创建新项目
            new_project = Project(
                name=name,
                description=f"{original_project.description} (副本)" if original_project.description else "项目副本",
                status=ProjectStatus.ACTIVE
            )

            session.add(new_project)
            await session.flush()  # 获取新项目ID

            # 复制测试用例（简化处理）
            test_cases_result = await session.execute(
                select(TestCase).where(TestCase.project_id == project_id)
            )
            test_cases = test_cases_result.scalars().all()

            for test_case in test_cases:
                new_test_case = TestCase(
                    project_id=new_project.id,
                    title=f"{test_case.title} (副本)",
                    description=test_case.description,
                    test_type=test_case.test_type,
                    test_level=test_case.test_level,
                    priority=test_case.priority,
                    preconditions=test_case.preconditions,
                    test_steps=test_case.test_steps,
                    expected_results=test_case.expected_results,
                    status=test_case.status
                )
                session.add(new_test_case)

            await session.commit()

            # 返回新项目信息
            return ProjectResponse(
                id=new_project.id,
                name=new_project.name,
                description=new_project.description,
                status=new_project.status,
                test_case_count=len(test_cases),
                category_count=0,
                tag_count=0,
                created_at=new_project.created_at.isoformat(),
                updated_at=new_project.updated_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"复制项目失败: {str(e)}")

@router.get("/{project_id}/export")
async def export_project(project_id: str, format: str = Query("excel", description="导出格式")):
    """导出项目数据"""
    try:
        async with db_manager.get_session() as session:
            # 验证项目存在
            project_result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar_one_or_none()

            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")

            # TODO: 实现具体的导出逻辑
            # 这里应该调用导出服务来生成文件

            return {"message": f"项目导出功能开发中，格式: {format}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出项目失败: {str(e)}")

@router.get("/{project_id}/activity", response_model=ProjectActivityListResponse)
async def get_project_activity(
    project_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, description="活动类型过滤")
):
    """获取项目活动日志"""
    try:
        async with db_manager.get_session() as session:
            # 验证项目存在
            project_result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar_one_or_none()

            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")

            # TODO: 实现活动日志查询
            # 这里应该查询专门的活动记录表

            # 临时返回空数据
            return ProjectActivityListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目活动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目活动失败: {str(e)}")


@router.get("/enums")
async def get_project_enums():
    """
    获取项目相关的所有枚举值
    """
    return {
        "statuses": get_enum_choices(ProjectStatus)
    }
