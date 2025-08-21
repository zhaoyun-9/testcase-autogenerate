"""
文件处理服务
统一处理各种类型的文件上传、验证、存储和分析
"""
import os
import uuid
import mimetypes
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from enum import Enum

from fastapi import UploadFile, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.services.core.agent_selector import agent_selector, AgentRecommendation
from app.core.types import (
    FILE_TYPE_CATEGORIES, 
    MAX_FILE_SIZE,
    AgentTypes
)


class InputType(Enum):
    """输入类型"""
    FILE_UPLOAD = "file_upload"
    DIRECT_REQUIREMENT = "direct_requirement"
    BATCH_FILES = "batch_files"
    URL_IMPORT = "url_import"


class ProcessingMode(Enum):
    """处理模式"""
    STANDARD = "standard"
    FAST = "fast"
    DETAILED = "detailed"
    CUSTOM = "custom"


class FileUploadResult(BaseModel):
    """文件上传结果"""
    file_id: str
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    file_category: str
    suggested_agent: str
    agent_recommendation: Optional[Dict[str, Any]] = None
    mime_type: str
    upload_time: str


class ProcessingConfig(BaseModel):
    """处理配置"""
    mode: ProcessingMode = ProcessingMode.STANDARD
    generate_mind_map: bool = True
    export_excel: bool = False
    auto_categorize: bool = True
    priority_assignment: bool = True
    max_test_cases: Optional[int] = None
    custom_prompts: Optional[Dict[str, str]] = None


class InputData(BaseModel):
    """统一输入数据"""
    input_type: InputType
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processing_config: ProcessingConfig
    
    # 文件相关
    files: Optional[List[UploadFile]] = None
    
    # 直接输入相关
    requirement_text: Optional[str] = None
    requirement_title: Optional[str] = None
    
    # URL导入相关
    import_urls: Optional[List[str]] = None
    
    # 通用字段
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """验证结果"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class FileProcessor:
    """文件处理器"""
    
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的文件类型
        self.supported_extensions = {
            'documents': ['.pdf', '.docx', '.doc', '.txt', '.md'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'api_specs': ['.json', '.yaml', '.yml'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'database': ['.sql', '.json', '.xml']
        }
    
    def validate_input(self, input_data: InputData) -> ValidationResult:
        """验证输入数据"""
        errors = []
        warnings = []
        suggestions = []
        
        # 基础验证
        if not input_data.session_id:
            errors.append("会话ID不能为空")
        
        # 根据输入类型验证
        if input_data.input_type == InputType.FILE_UPLOAD:
            if not input_data.files or len(input_data.files) == 0:
                errors.append("文件上传模式下必须提供文件")
        elif input_data.input_type == InputType.DIRECT_REQUIREMENT:
            if not input_data.requirement_text:
                errors.append("直接输入模式下必须提供需求文本")
            elif len(input_data.requirement_text.strip()) < 10:
                warnings.append("需求文本过短，可能影响测试用例质量")
        elif input_data.input_type == InputType.BATCH_FILES:
            if not input_data.files or len(input_data.files) < 2:
                errors.append("批量处理模式下至少需要2个文件")
        elif input_data.input_type == InputType.URL_IMPORT:
            if not input_data.import_urls or len(input_data.import_urls) == 0:
                errors.append("URL导入模式下必须提供URL列表")
        
        # 配置验证
        if (input_data.processing_config.max_test_cases and 
            input_data.processing_config.max_test_cases < 1):
            errors.append("最大测试用例数量必须大于0")
        
        # 生成建议
        if input_data.processing_config.mode == ProcessingMode.FAST:
            suggestions.append("快速模式可能会影响测试用例的详细程度")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_file(self, file: UploadFile) -> tuple[str, str]:
        """验证单个文件"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 获取文件扩展名
        file_extension = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        # 检查文件类型
        file_category = None
        for category, extensions in self.supported_extensions.items():
            if file_extension in extensions:
                file_category = category
                break
        
        if not file_category:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        return file_extension, file_category
    
    def check_file_size(self, file_size: int, file_category: str) -> None:
        """检查文件大小"""
        max_size_mb = MAX_FILE_SIZE.get(file_category, 10)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超限。最大允许: {max_size_mb}MB，当前: {file_size / 1024 / 1024:.2f}MB"
            )
    
    async def upload_file(self, file: UploadFile, session_id: Optional[str] = None) -> FileUploadResult:
        """上传单个文件"""
        try:
            # 验证文件
            file_extension, file_category = self.validate_file(file)
            
            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)
            
            # 检查文件大小
            self.check_file_size(file_size, file_category)
            
            # 生成文件ID和存储路径
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file_id[:8]}_{file.filename}"
            
            # 确定存储目录
            category_dir = self.base_upload_dir / file_category
            if session_id:
                category_dir = category_dir / session_id
            category_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = category_dir / safe_filename
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            # 获取MIME类型
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # 智能体推荐
            recommendation = await agent_selector.select_agent(
                str(file_path), file_content, file_extension
            )
            
            result = FileUploadResult(
                file_id=file_id,
                file_name=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_extension,
                file_category=file_category,
                suggested_agent=recommendation.primary_agent,
                agent_recommendation={
                    'primary_agent': recommendation.primary_agent,
                    'alternative_agents': recommendation.alternative_agents,
                    'confidence': recommendation.confidence,
                    'reasoning': recommendation.reasoning
                },
                mime_type=mime_type,
                upload_time=datetime.now().isoformat()
            )
            
            logger.info(f"文件上传成功: {file.filename} -> {recommendation.primary_agent}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {file.filename} - {e}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    async def upload_multiple_files(self, files: List[UploadFile], 
                                   session_id: Optional[str] = None) -> List[FileUploadResult]:
        """批量上传文件"""
        results = []
        errors = []
        
        for file in files:
            try:
                result = await self.upload_file(file, session_id)
                results.append(result)
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        if errors and not results:
            raise HTTPException(
                status_code=400,
                detail=f"所有文件上传失败: {'; '.join(errors)}"
            )
        elif errors:
            logger.warning(f"部分文件上传失败: {'; '.join(errors)}")
        
        return results
    
    async def analyze_file_content(self, file_path: str) -> AgentRecommendation:
        """分析文件内容并推荐智能体"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            file_extension = Path(file_path).suffix
            recommendation = await agent_selector.select_agent(
                file_path, content, file_extension
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"文件内容分析失败: {file_path} - {e}")
            raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")
    
    def cleanup_session_files(self, session_id: str):
        """清理会话相关文件"""
        try:
            for category in self.supported_extensions.keys():
                session_dir = self.base_upload_dir / category / session_id
                if session_dir.exists():
                    import shutil
                    shutil.rmtree(session_dir)
                    logger.info(f"清理会话文件: {session_dir}")
        except Exception as e:
            logger.error(f"清理会话文件失败: {session_id} - {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        stat = path.stat()
        return {
            'file_name': path.name,
            'file_size': stat.st_size,
            'file_type': path.suffix,
            'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }


# 全局实例
file_processor = FileProcessor()
