"""
系统配置API端点 (最终版)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import SystemConfig, ConfigType, Project, TestCase, ProcessingSession, SessionStatus

router = APIRouter()

class SystemConfigCreateRequest(BaseModel):
    """创建系统配置请求"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: str = Field(..., description="配置值")
    config_type: ConfigType = Field(ConfigType.STRING, description="配置类型")
    description: Optional[str] = Field(None, description="配置描述")

class SystemConfigUpdateRequest(BaseModel):
    """更新系统配置请求"""
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: Optional[ConfigType] = Field(None, description="配置类型")
    description: Optional[str] = Field(None, description="配置描述")

class SystemConfigResponse(BaseModel):
    """系统配置响应"""
    id: str
    config_key: str
    config_value: str
    config_type: ConfigType
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class SystemConfigListResponse(BaseModel):
    """系统配置列表响应"""
    items: List[SystemConfigResponse]
    total: int

@router.get("/configs", response_model=SystemConfigListResponse)
async def get_system_configs(
    search: Optional[str] = None,
    config_type: Optional[ConfigType] = None
):
    """获取系统配置列表"""
    try:
        async with db_manager.get_session() as session:
            query = select(SystemConfig)
            
            if search:
                query = query.where(SystemConfig.config_key.contains(search))
            
            if config_type:
                query = query.where(SystemConfig.config_type == config_type)
            
            query = query.order_by(SystemConfig.config_key)
            
            result = await session.execute(query)
            configs = result.scalars().all()
            
            items = [
                SystemConfigResponse(
                    id=config.id,
                    config_key=config.config_key,
                    config_value=config.config_value,
                    config_type=config.config_type,
                    description=config.description,
                    created_at=config.created_at.isoformat(),
                    updated_at=config.updated_at.isoformat()
                )
                for config in configs
            ]
            
            return SystemConfigListResponse(
                items=items,
                total=len(items)
            )
            
    except Exception as e:
        logger.error(f"获取系统配置列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统配置列表失败: {str(e)}")

@router.post("/configs", response_model=SystemConfigResponse)
async def create_system_config(request: SystemConfigCreateRequest):
    """创建系统配置"""
    try:
        async with db_manager.get_session() as session:
            # 检查配置键是否已存在
            existing_result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == request.config_key)
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="配置键已存在")
            
            # 创建配置
            import uuid
            config = SystemConfig(
                id=str(uuid.uuid4()),
                config_key=request.config_key,
                config_value=request.config_value,
                config_type=request.config_type,
                description=request.description
            )
            
            session.add(config)
            await session.commit()
            await session.refresh(config)
            
            return SystemConfigResponse(
                id=config.id,
                config_key=config.config_key,
                config_value=config.config_value,
                config_type=config.config_type,
                description=config.description,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建系统配置失败: {str(e)}")

@router.get("/configs/{config_key}", response_model=SystemConfigResponse)
async def get_system_config(config_key: str):
    """获取系统配置"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            return SystemConfigResponse(
                id=config.id,
                config_key=config.config_key,
                config_value=config.config_value,
                config_type=config.config_type,
                description=config.description,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")

@router.put("/configs/{config_key}", response_model=SystemConfigResponse)
async def update_system_config(config_key: str, request: SystemConfigUpdateRequest):
    """更新系统配置"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            # 更新字段
            if request.config_value is not None:
                config.config_value = request.config_value
            
            if request.config_type is not None:
                config.config_type = request.config_type
            
            if request.description is not None:
                config.description = request.description
            
            await session.commit()
            await session.refresh(config)
            
            return SystemConfigResponse(
                id=config.id,
                config_key=config.config_key,
                config_value=config.config_value,
                config_type=config.config_type,
                description=config.description,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新系统配置失败: {str(e)}")

@router.delete("/configs/{config_key}")
async def delete_system_config(config_key: str):
    """删除系统配置"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            await session.delete(config)
            await session.commit()
            
            return {"message": "配置删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除系统配置失败: {str(e)}")

@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    try:
        async with db_manager.get_session() as session:
            # 获取各种统计信息
            from app.database.models.test_case import Project, TestCase, ProcessingSession
            
            # 项目统计
            project_count_result = await session.execute(
                select(func.count(Project.id))
            )
            project_count = project_count_result.scalar() or 0
            
            # 测试用例统计
            test_case_count_result = await session.execute(
                select(func.count(TestCase.id))
            )
            test_case_count = test_case_count_result.scalar() or 0
            
            # 会话统计
            session_count_result = await session.execute(
                select(func.count(ProcessingSession.id))
            )
            session_count = session_count_result.scalar() or 0
            
            # 活跃会话统计
            active_session_count_result = await session.execute(
                select(func.count(ProcessingSession.id))
                .where(ProcessingSession.status.in_([SessionStatus.CREATED, SessionStatus.PROCESSING]))
            )
            active_session_count = active_session_count_result.scalar() or 0
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "statistics": {
                    "projects": project_count,
                    "test_cases": test_case_count,
                    "total_sessions": session_count,
                    "active_sessions": active_session_count
                },
                "database": {
                    "status": "connected",
                    "pool_size": db_manager.pool_size if hasattr(db_manager, 'pool_size') else "unknown"
                }
            }
            
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 测试数据库连接
        async with db_manager.get_session() as session:
            await session.execute(select(1))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy",
                "api": "healthy"
            }
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")

@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    try:
        import platform
        import sys
        from datetime import datetime
        
        return {
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture()[0]
            },
            "application": {
                "name": "测试用例自动化平台",
                "version": "1.0.0",
                "environment": "development"  # 可以从环境变量获取
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@router.post("/configs/batch")
async def batch_update_configs(configs: Dict[str, str]):
    """批量更新配置"""
    try:
        async with db_manager.get_session() as session:
            updated_configs = []
            
            for config_key, config_value in configs.items():
                result = await session.execute(
                    select(SystemConfig).where(SystemConfig.config_key == config_key)
                )
                config = result.scalar_one_or_none()
                
                if config:
                    config.config_value = config_value
                    updated_configs.append(config_key)
            
            await session.commit()
            
            return {
                "message": f"成功更新 {len(updated_configs)} 个配置",
                "updated_configs": updated_configs
            }
            
    except Exception as e:
        logger.error(f"批量更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量更新配置失败: {str(e)}")

@router.get("/configs/export")
async def export_configs():
    """导出所有配置"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(select(SystemConfig))
            configs = result.scalars().all()
            
            export_data = {}
            for config in configs:
                export_data[config.config_key] = {
                    "value": config.config_value,
                    "type": config.config_type,
                    "description": config.description
                }
            
            return {
                "configs": export_data,
                "export_time": datetime.utcnow().isoformat(),
                "total_count": len(export_data)
            }
            
    except Exception as e:
        logger.error(f"导出配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")
