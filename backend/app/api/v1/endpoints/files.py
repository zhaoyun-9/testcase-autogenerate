"""
文件处理API端点 (最终版)
基于最终版数据库结构的文件处理接口
"""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import FileUpload, Project, UploadSource

router = APIRouter()

# Pydantic模型
class FileAnalysisResponse(BaseModel):
    """文件分析响应"""
    file_name: str
    file_size: int
    file_type: str
    category: str
    supported: bool
    recommended_agent: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: str
    original_name: str
    stored_name: str
    file_path: str
    file_size: int
    file_type: str
    upload_source: UploadSource
    project_id: Optional[str]
    session_id: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    """文件列表响应"""
    items: List[FileUploadResponse]
    total: int

# 支持的文件类型配置
SUPPORTED_FILE_TYPES = {
    "image": {
        "name": "图片文件",
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "maxSize": 50,  # MB
        "description": "支持常见图片格式，用于UI界面分析和测试用例生成",
        "agent": "image_analyzer"
    },
    "document": {
        "name": "文档文件",
        "extensions": [".pdf", ".docx", ".doc", ".txt", ".md"],
        "maxSize": 50,  # MB
        "description": "支持PDF、Word、文本等格式，用于需求文档分析",
        "agent": "document_parser"
    },
    "api": {
        "name": "API规范文件",
        "extensions": [".json", ".yaml", ".yml"],
        "maxSize": 10,  # MB
        "description": "支持OpenAPI/Swagger规范，用于接口测试用例生成",
        "agent": "api_spec_analyzer"
    },
    "database": {
        "name": "数据库文件",
        "extensions": [".sql", ".db", ".sqlite", ".ddl"],
        "maxSize": 100,  # MB
        "description": "支持SQL脚本和数据库文件，用于数据测试用例生成",
        "agent": "database_analyzer"
    },
    "video": {
        "name": "视频文件",
        "extensions": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"],
        "maxSize": 500,  # MB
        "description": "支持常见视频格式，用于操作流程分析和测试用例生成",
        "agent": "video_analyzer"
    }
}

def get_file_category(filename: str) -> tuple[str, str]:
    """根据文件名获取文件分类和推荐智能体"""
    file_ext = Path(filename).suffix.lower()
    
    for category, config in SUPPORTED_FILE_TYPES.items():
        if file_ext in config["extensions"]:
            return category, config["agent"]
    
    return "unknown", "unknown"

def is_file_supported(filename: str, file_size: int) -> tuple[bool, str]:
    """检查文件是否支持"""
    category, _ = get_file_category(filename)
    
    if category == "unknown":
        return False, "不支持的文件类型"
    
    config = SUPPORTED_FILE_TYPES[category]
    max_size_bytes = config["maxSize"] * 1024 * 1024  # 转换为字节
    
    if file_size > max_size_bytes:
        return False, f"文件大小超过限制 ({config['maxSize']}MB)"
    
    return True, "文件支持"

@router.get("/supported-types")
async def get_supported_file_types():
    """获取支持的文件类型"""
    return {
        "supported_types": SUPPORTED_FILE_TYPES,
        "total_categories": len(SUPPORTED_FILE_TYPES)
    }

@router.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    """分析文件"""
    try:
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 获取文件信息
        category, recommended_agent = get_file_category(file.filename)
        supported, message = is_file_supported(file.filename, file_size)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file.filename)
        
        return FileAnalysisResponse(
            file_name=file.filename,
            file_size=file_size,
            file_type=Path(file.filename).suffix.lower(),
            category=category,
            supported=supported,
            recommended_agent=recommended_agent if supported else None,
            analysis_result={
                "mime_type": mime_type,
                "message": message,
                "category_info": SUPPORTED_FILE_TYPES.get(category, {})
            }
        )
        
    except Exception as e:
        logger.error(f"文件分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    upload_source: str = Form(...),
    project_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """上传文件"""
    try:
        # 验证文件
        content = await file.read()
        file_size = len(content)
        
        supported, message = is_file_supported(file.filename, file_size)
        if not supported:
            raise HTTPException(status_code=400, detail=message)
        
        # 验证上传源
        logger.info(f"收到的 upload_source: '{upload_source}', 类型: {type(upload_source)}")
        try:
            # 尝试直接使用值创建枚举
            upload_source_enum = UploadSource(upload_source)
            logger.info(f"成功创建枚举: {upload_source_enum}")
        except ValueError as e:
            logger.warning(f"通过值创建枚举失败: {e}")
            # 如果失败，尝试使用枚举成员名称
            try:
                upload_source_enum = UploadSource[upload_source]
                logger.info(f"通过名称创建枚举成功: {upload_source_enum}")
            except KeyError as e2:
                logger.error(f"通过名称创建枚举也失败: {e2}")
                valid_values = [e.value for e in UploadSource]
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的上传源类型。有效值: {valid_values}"
                )
        
        # 验证项目存在（如果提供）
        if project_id:
            async with db_manager.get_session() as session:
                project_result = await session.execute(
                    select(Project).where(Project.id == project_id)
                )
                if not project_result.scalar_one_or_none():
                    raise HTTPException(status_code=404, detail="项目不存在")
        
        # 生成存储文件名
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        stored_name = f"{file_id}{file_ext}"
        
        # 创建上传目录
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # 保存文件
        file_path = upload_dir / stored_name
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file.filename)
        
        # 保存文件记录到数据库
        logger.info(f"准备保存到数据库，upload_source_enum: {upload_source_enum}, 类型: {type(upload_source_enum)}")
        async with db_manager.get_session() as session:
            try:
                file_upload = FileUpload(
                    id=file_id,
                    original_name=file.filename,
                    stored_name=stored_name,
                    file_path=str(file_path),
                    file_size=file_size,
                    file_type=Path(file.filename).suffix.lower(),
                    mime_type=mime_type,
                    upload_source=upload_source_enum.value,  # 存储枚举值而不是枚举对象
                    session_id=session_id,
                    project_id=project_id
                )
                logger.info(f"FileUpload 对象创建成功")
            except Exception as e:
                logger.error(f"创建 FileUpload 对象失败: {e}")
                raise
            
            session.add(file_upload)
            await session.commit()
            await session.refresh(file_upload)
            
            # 返回字典而不是 Pydantic 模型，避免枚举序列化问题
            return {
                "id": file_upload.id,
                "original_name": file_upload.original_name,
                "stored_name": file_upload.stored_name,
                "file_path": file_upload.file_path,
                "file_size": file_upload.file_size,
                "file_type": file_upload.file_type,
                "upload_source": file_upload.upload_source,  # 现在直接是字符串值
                "project_id": file_upload.project_id,
                "session_id": file_upload.session_id,
                "created_at": file_upload.created_at.isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/", response_model=FileListResponse)
async def get_files(
    project_id: Optional[str] = Query(None, description="项目ID过滤"),
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    upload_source: Optional[UploadSource] = Query(None, description="上传源过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取文件列表"""
    try:
        async with db_manager.get_session() as session:
            query = select(FileUpload)
            
            # 过滤条件
            if project_id:
                query = query.where(FileUpload.project_id == project_id)
            
            if session_id:
                query = query.where(FileUpload.session_id == session_id)
            
            if upload_source:
                query = query.where(FileUpload.upload_source == upload_source)
            
            # 排序
            query = query.order_by(desc(FileUpload.created_at))
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # 执行查询
            result = await session.execute(query)
            files = result.scalars().all()
            
            # 获取总数
            count_query = select(FileUpload)
            if project_id:
                count_query = count_query.where(FileUpload.project_id == project_id)
            if session_id:
                count_query = count_query.where(FileUpload.session_id == session_id)
            if upload_source:
                count_query = count_query.where(FileUpload.upload_source == upload_source)
            
            total_result = await session.execute(
                select(func.count()).select_from(count_query.subquery())
            )
            total = total_result.scalar()
            
            items = [
                FileUploadResponse(
                    id=file.id,
                    original_name=file.original_name,
                    stored_name=file.stored_name,
                    file_path=file.file_path,
                    file_size=file.file_size,
                    file_type=file.file_type,
                    upload_source=file.upload_source,
                    project_id=file.project_id,
                    session_id=file.session_id,
                    created_at=file.created_at.isoformat()
                )
                for file in files
            ]
            
            return FileListResponse(
                items=items,
                total=total
            )
            
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """删除文件"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(FileUpload).where(FileUpload.id == file_id)
            )
            file = result.scalar_one_or_none()
            
            if not file:
                raise HTTPException(status_code=404, detail="文件不存在")
            
            # 删除物理文件
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
            
            # 删除数据库记录
            await session.delete(file)
            await session.commit()
            
            return {"message": "文件删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
