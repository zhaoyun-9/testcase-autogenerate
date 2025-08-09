"""
思维导图API端点 (最终版)
"""
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import MindMap, Project, ProcessingSession

router = APIRouter()

class MindMapCreateRequest(BaseModel):
    """创建思维导图请求"""
    name: str = Field(..., min_length=1, max_length=255, description="思维导图名称")
    session_id: str = Field(..., description="关联会话ID")
    project_id: Optional[str] = Field(None, description="项目ID")
    mind_map_data: Dict[str, Any] = Field(..., description="思维导图数据")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="布局配置")

class MindMapUpdateRequest(BaseModel):
    """更新思维导图请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="思维导图名称")
    mind_map_data: Optional[Dict[str, Any]] = Field(None, description="思维导图数据")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="布局配置")

class MindMapResponse(BaseModel):
    """思维导图响应"""
    id: str
    name: str
    session_id: str
    project_id: Optional[str]
    project_name: Optional[str] = None
    mind_map_data: Dict[str, Any]
    layout_config: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class MindMapListResponse(BaseModel):
    """思维导图列表响应"""
    items: List[MindMapResponse]
    total: int

@router.get("/", response_model=MindMapListResponse)
async def get_mindmaps(
    project_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """获取思维导图列表"""
    try:
        async with db_manager.get_session() as session:
            query = select(MindMap)
            
            if project_id:
                query = query.where(MindMap.project_id == project_id)
            
            if session_id:
                query = query.where(MindMap.session_id == session_id)
            
            query = query.order_by(desc(MindMap.updated_at))
            
            result = await session.execute(query)
            mindmaps = result.scalars().all()
            
            # 构建响应
            items = []
            for mindmap in mindmaps:
                # 获取项目名称
                project_name = None
                if mindmap.project_id:
                    project_result = await session.execute(
                        select(Project.name).where(Project.id == mindmap.project_id)
                    )
                    project_name = project_result.scalar()
                
                items.append(MindMapResponse(
                    id=mindmap.id,
                    name=mindmap.name,
                    session_id=mindmap.session_id,
                    project_id=mindmap.project_id,
                    project_name=project_name,
                    mind_map_data=mindmap.mind_map_data,
                    layout_config=mindmap.layout_config,
                    created_at=mindmap.created_at.isoformat(),
                    updated_at=mindmap.updated_at.isoformat()
                ))
            
            return MindMapListResponse(
                items=items,
                total=len(items)
            )
            
    except Exception as e:
        logger.error(f"获取思维导图列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取思维导图列表失败: {str(e)}")

@router.post("/", response_model=MindMapResponse)
async def create_mindmap(request: MindMapCreateRequest):
    """创建思维导图"""
    try:
        async with db_manager.get_session() as session:
            # 验证会话存在
            session_result = await session.execute(
                select(ProcessingSession).where(ProcessingSession.id == request.session_id)
            )
            if not session_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="会话不存在")
            
            # 验证项目存在（如果提供）
            if request.project_id:
                project_result = await session.execute(
                    select(Project).where(Project.id == request.project_id)
                )
                if not project_result.scalar_one_or_none():
                    raise HTTPException(status_code=404, detail="项目不存在")
            
            # 创建思维导图
            mindmap = MindMap(
                id=str(uuid.uuid4()),
                name=request.name,
                session_id=request.session_id,
                project_id=request.project_id,
                mind_map_data=request.mind_map_data,
                layout_config=request.layout_config
            )
            
            session.add(mindmap)
            await session.commit()
            await session.refresh(mindmap)
            
            # 获取项目名称
            project_name = None
            if mindmap.project_id:
                project_result = await session.execute(
                    select(Project.name).where(Project.id == mindmap.project_id)
                )
                project_name = project_result.scalar()
            
            return MindMapResponse(
                id=mindmap.id,
                name=mindmap.name,
                session_id=mindmap.session_id,
                project_id=mindmap.project_id,
                project_name=project_name,
                mind_map_data=mindmap.mind_map_data,
                layout_config=mindmap.layout_config,
                created_at=mindmap.created_at.isoformat(),
                updated_at=mindmap.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建思维导图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建思维导图失败: {str(e)}")

@router.get("/{mindmap_id}", response_model=MindMapResponse)
async def get_mindmap(mindmap_id: str):
    """获取思维导图详情"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MindMap).where(MindMap.id == mindmap_id)
            )
            mindmap = result.scalar_one_or_none()
            
            if not mindmap:
                raise HTTPException(status_code=404, detail="思维导图不存在")
            
            # 获取项目名称
            project_name = None
            if mindmap.project_id:
                project_result = await session.execute(
                    select(Project.name).where(Project.id == mindmap.project_id)
                )
                project_name = project_result.scalar()
            
            return MindMapResponse(
                id=mindmap.id,
                name=mindmap.name,
                session_id=mindmap.session_id,
                project_id=mindmap.project_id,
                project_name=project_name,
                mind_map_data=mindmap.mind_map_data,
                layout_config=mindmap.layout_config,
                created_at=mindmap.created_at.isoformat(),
                updated_at=mindmap.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取思维导图详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取思维导图详情失败: {str(e)}")

@router.put("/{mindmap_id}", response_model=MindMapResponse)
async def update_mindmap(mindmap_id: str, request: MindMapUpdateRequest):
    """更新思维导图"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MindMap).where(MindMap.id == mindmap_id)
            )
            mindmap = result.scalar_one_or_none()
            
            if not mindmap:
                raise HTTPException(status_code=404, detail="思维导图不存在")
            
            # 更新字段
            if request.name is not None:
                mindmap.name = request.name
            
            if request.mind_map_data is not None:
                mindmap.mind_map_data = request.mind_map_data
            
            if request.layout_config is not None:
                mindmap.layout_config = request.layout_config
            
            await session.commit()
            await session.refresh(mindmap)
            
            # 获取项目名称
            project_name = None
            if mindmap.project_id:
                project_result = await session.execute(
                    select(Project.name).where(Project.id == mindmap.project_id)
                )
                project_name = project_result.scalar()
            
            return MindMapResponse(
                id=mindmap.id,
                name=mindmap.name,
                session_id=mindmap.session_id,
                project_id=mindmap.project_id,
                project_name=project_name,
                mind_map_data=mindmap.mind_map_data,
                layout_config=mindmap.layout_config,
                created_at=mindmap.created_at.isoformat(),
                updated_at=mindmap.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新思维导图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新思维导图失败: {str(e)}")

@router.delete("/{mindmap_id}")
async def delete_mindmap(mindmap_id: str):
    """删除思维导图"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MindMap).where(MindMap.id == mindmap_id)
            )
            mindmap = result.scalar_one_or_none()
            
            if not mindmap:
                raise HTTPException(status_code=404, detail="思维导图不存在")
            
            await session.delete(mindmap)
            await session.commit()
            
            return {"message": "思维导图删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除思维导图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除思维导图失败: {str(e)}")

@router.get("/session/{session_id}", response_model=MindMapResponse)
async def get_mindmap_by_session(session_id: str):
    """根据会话ID获取思维导图"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MindMap).where(MindMap.session_id == session_id)
            )
            mindmap = result.scalar_one_or_none()
            
            if not mindmap:
                raise HTTPException(status_code=404, detail="该会话没有关联的思维导图")
            
            # 获取项目名称
            project_name = None
            if mindmap.project_id:
                project_result = await session.execute(
                    select(Project.name).where(Project.id == mindmap.project_id)
                )
                project_name = project_result.scalar()
            
            return MindMapResponse(
                id=mindmap.id,
                name=mindmap.name,
                session_id=mindmap.session_id,
                project_id=mindmap.project_id,
                project_name=project_name,
                mind_map_data=mindmap.mind_map_data,
                layout_config=mindmap.layout_config,
                created_at=mindmap.created_at.isoformat(),
                updated_at=mindmap.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据会话获取思维导图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"根据会话获取思维导图失败: {str(e)}")

@router.post("/{mindmap_id}/export")
async def export_mindmap(mindmap_id: str, format: str = "json"):
    """导出思维导图"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MindMap).where(MindMap.id == mindmap_id)
            )
            mindmap = result.scalar_one_or_none()
            
            if not mindmap:
                raise HTTPException(status_code=404, detail="思维导图不存在")
            
            if format.lower() == "json":
                return {
                    "format": "json",
                    "data": {
                        "name": mindmap.name,
                        "mind_map_data": mindmap.mind_map_data,
                        "layout_config": mindmap.layout_config,
                        "created_at": mindmap.created_at.isoformat(),
                        "updated_at": mindmap.updated_at.isoformat()
                    }
                }
            else:
                raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出思维导图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出思维导图失败: {str(e)}")
