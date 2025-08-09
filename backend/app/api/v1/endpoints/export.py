"""
导出API端点
提供测试用例导出功能，包括Excel、CSV、PDF等格式
"""
import uuid
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from loguru import logger

from app.core.messages.test_case import ExcelExportRequest
from app.services.test_case.orchestrator_service import get_test_case_orchestrator

router = APIRouter()


class ExportRequest(BaseModel):
    """导出请求模型"""
    test_case_ids: Optional[List[str]] = Field(None, description="测试用例ID列表，为空则导出所有")
    session_id: Optional[str] = Field(None, description="会话ID，用于导出特定会话的测试用例")
    export_config: dict = Field(default_factory=dict, description="导出配置")
    template_type: str = Field("standard", description="模板类型")


class ExportResponse(BaseModel):
    """导出响应模型"""
    export_id: str = Field(..., description="导出ID")
    status: str = Field(..., description="导出状态")
    message: str = Field(..., description="状态消息")
    download_url: Optional[str] = Field(None, description="下载链接")


@router.post("/test-cases/excel", response_model=ExportResponse)
async def export_test_cases_to_excel(request: ExportRequest):
    """
    导出测试用例到Excel格式
    """
    try:
        # 生成导出会话ID
        export_session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"开始Excel导出请求: {export_session_id}")
        
        # 构建Excel导出请求
        excel_request = ExcelExportRequest(
            session_id=export_session_id,
            test_case_ids=request.test_case_ids or [],
            export_config=request.export_config,
            template_type=request.template_type
        )
        
        # 获取编排器并执行导出
        orchestrator = get_test_case_orchestrator()
        await orchestrator.export_to_excel(excel_request)
        
        return ExportResponse(
            export_id=export_session_id,
            status="processing",
            message="Excel导出已启动，请等待完成",
            download_url=f"/api/v1/export/download/{export_session_id}"
        )
        
    except Exception as e:
        logger.error(f"Excel导出请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/download/{export_id}")
async def download_export_file(export_id: str):
    """
    下载导出的文件
    """
    try:
        # 查找导出文件
        export_dir = Path("exports/excel")
        
        # 查找匹配的文件
        export_files = list(export_dir.glob(f"*{export_id}*.xlsx"))
        
        if not export_files:
            raise HTTPException(status_code=404, detail="导出文件不存在或已过期")
        
        # 获取最新的文件
        latest_file = max(export_files, key=lambda f: f.stat().st_mtime)
        
        if not latest_file.exists():
            raise HTTPException(status_code=404, detail="导出文件不存在")
        
        logger.info(f"下载导出文件: {latest_file}")
        
        return FileResponse(
            path=str(latest_file),
            filename=latest_file.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载导出文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/status/{export_id}")
async def get_export_status(export_id: str):
    """
    获取导出状态
    """
    try:
        # 检查导出文件是否存在
        export_dir = Path("exports/excel")
        export_files = list(export_dir.glob(f"*{export_id}*.xlsx"))
        
        if export_files:
            latest_file = max(export_files, key=lambda f: f.stat().st_mtime)
            return {
                "export_id": export_id,
                "status": "completed",
                "message": "导出完成",
                "file_name": latest_file.name,
                "file_size": latest_file.stat().st_size,
                "download_url": f"/api/v1/export/download/{export_id}"
            }
        else:
            return {
                "export_id": export_id,
                "status": "processing",
                "message": "正在导出中..."
            }
            
    except Exception as e:
        logger.error(f"获取导出状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/formats")
async def get_export_formats():
    """
    获取支持的导出格式
    """
    return {
        "formats": [
            {
                "key": "excel",
                "name": "Excel格式",
                "description": "Microsoft Excel (.xlsx)",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
            {
                "key": "csv",
                "name": "CSV格式",
                "description": "逗号分隔值 (.csv)",
                "mime_type": "text/csv"
            },
            {
                "key": "pdf",
                "name": "PDF格式",
                "description": "便携式文档格式 (.pdf)",
                "mime_type": "application/pdf"
            }
        ]
    }


@router.get("/templates/{format}")
async def get_export_templates(format: str):
    """
    获取指定格式的导出模板
    """
    templates = {
        "excel": [
            {
                "key": "standard",
                "name": "标准模板",
                "description": "包含所有测试用例字段的标准Excel模板"
            },
            {
                "key": "simple",
                "name": "简化模板",
                "description": "只包含核心字段的简化Excel模板"
            }
        ],
        "csv": [
            {
                "key": "standard",
                "name": "标准CSV",
                "description": "标准CSV格式导出"
            }
        ],
        "pdf": [
            {
                "key": "report",
                "name": "测试报告",
                "description": "格式化的PDF测试报告"
            }
        ]
    }
    
    return {
        "format": format,
        "templates": templates.get(format, [])
    }
