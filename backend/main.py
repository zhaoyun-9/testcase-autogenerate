"""
企业级测试用例生成系统 - 后端主应用
基于FastAPI + AutoGen的智能测试用例生成平台
"""
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import time
from pathlib import Path

# 导入配置和日志
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

# 导入数据库
from app.database.connection import db_manager

# 导入API路由
from app.api.v1.api import api_router
from app.api.v1.endpoints.test_case_generator import router as test_case_generator_router
from app.api.v1.endpoints.test_case_management import router as test_case_management_router
from app.api.v1.endpoints.export import router as export_router
from app.api.v1.endpoints.files import router as files_router

# 设置日志
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动企业级测试用例生成系统...")
    
    try:
        # 初始化数据库连接
        await db_manager.initialize()
        logger.info("✅ 数据库连接初始化完成")
        
        # 创建必要的目录
        upload_dirs = [
            "uploads/documents",
            "uploads/images", 
            "uploads/api_specs",
            "uploads/database_schemas",
            "uploads/videos",
            "exports/excel",
            "exports/word",
            "exports/pdf",
            "temp"
        ]
        
        for dir_path in upload_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ 上传目录创建完成")
        
        # 初始化智能体工厂
        from app.agents.factory import agent_factory
        await agent_factory.initialize()
        logger.info("✅ 智能体工厂初始化完成")
        
        logger.info("🎉 系统启动完成!")
        
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {str(e)}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("🔄 正在关闭系统...")
    
    try:
        # 关闭数据库连接
        await db_manager.close()
        logger.info("✅ 数据库连接已关闭")
        
        # 清理智能体资源
        await agent_factory.cleanup()
        logger.info("✅ 智能体资源已清理")
        
        logger.info("👋 系统已安全关闭")
        
    except Exception as e:
        logger.error(f"❌ 系统关闭时出错: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="企业级测试用例生成系统",
    description="""
    ## 🧪 企业级测试用例生成系统

    基于AI智能体的测试用例自动生成平台，支持多种输入源和专业的测试用例管理。

    ### 🌟 核心功能

    - **📄 文档解析**: 支持Word、PDF等需求文档智能解析
    - **🖼️ 图片分析**: 流程图、思维导图、UI截图智能识别
    - **🔌 API规范**: Swagger/OpenAPI规范文件解析
    - **🗄️ 数据库Schema**: 数据库表结构导入生成数据测试用例
    - **🎥 录屏分析**: 操作录屏视频生成用户行为测试用例
    - **🧠 思维导图**: 专业测试用例思维导图生成和编辑
    - **📊 用例管理**: 完整的测试用例分类、标签、优先级管理
    - **📋 批量处理**: 支持多文件批量处理
    - **📤 导出功能**: Excel、Word、PDF等格式导出

    ### 🤖 AI智能体架构

    系统采用AutoGen多智能体协作架构：
    - 文档解析智能体
    - 图片分析智能体  
    - API规范解析智能体
    - 数据库Schema解析智能体
    - 录屏分析智能体
    - 测试用例生成智能体
    - 思维导图生成智能体
    - Excel导出智能体

    ### 🔧 技术栈

    - **后端**: FastAPI + AutoGen + MySQL
    - **前端**: React + TypeScript + Ant Design + Three.js
    - **AI模型**: DeepSeek-Chat + QwenVL
    - **实时通信**: SSE (Server-Sent Events)
    """,
    version="1.0.0",
    contact={
        "name": "测试用例生成系统",
        "url": "https://github.com/your-repo/test-case-automation",
        "email": "support@testcase.ai"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan,
    docs_url=None,  # 禁用默认docs
    redoc_url=None,  # 禁用默认redoc
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "内部服务器错误",
            "status_code": 500,
            "path": str(request.url)
        }
    )


# 注册API路由
api_prefix = "/api/v1"

# 注册所有API路由
app.include_router(
    api_router,
    prefix=api_prefix
)

# 所有API路由已通过api_router统一注册


# 静态文件服务
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
exports_dir = os.path.join(os.path.dirname(__file__), "exports")

# 确保目录存在
os.makedirs(static_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(exports_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")


# 自定义OpenAPI文档
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 添加自定义配置
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# 自定义文档页面
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API文档",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico"
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API文档",
        redoc_js_url="/static/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico"
    )


# 根路径
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "🧪 企业级测试用例生成系统",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
        "features": [
            "智能文件解析（文档、图片、视频、API规范、数据库Schema）",
            "直接需求输入",
            "自动智能体选择",
            "实时流式处理",
            "测试用例生成",
            "思维导图生成",
            "Excel导出"
        ]
    }


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """系统健康检查"""
    try:
        # 检查数据库连接
        db_status = await db_manager.health_check()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "database": db_status,
            "uptime": time.time() - start_time if 'start_time' in globals() else 0
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# 记录启动时间
start_time = time.time()


def detect_debugger():
    """检测是否在调试器中运行"""
    import sys
    return (
        hasattr(sys, 'gettrace') and sys.gettrace() is not None or
        'pydevd' in sys.modules or
        'debugpy' in sys.modules or
        'pdb' in sys.modules
    )


if __name__ == "__main__":
    # 检测调试器状态
    in_debugger = detect_debugger()

    if in_debugger:
        logger.info("🐛 检测到调试器环境，禁用自动重载以避免冲突")
        # 调试器模式：禁用reload避免冲突
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # 调试时禁用reload
            log_level="debug",
            access_log=True,
            use_colors=True,
            loop="asyncio"
        )
    else:
        # 正常开发模式：启用reload
        logger.info("🚀 正常开发模式，启用自动重载")

        # 配置 uvicorn 以避免日志冲突
        config = uvicorn.Config(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG and settings.ENABLE_RELOAD,
            log_level="info" if not settings.DEBUG else "debug",
            access_log=True,
            use_colors=True,
            loop="asyncio",
            # 避免多进程日志冲突的配置
            reload_excludes=["logs/*", "*.log"],  # 排除日志文件的监控
            reload_includes=["*.py"],  # 只监控Python文件
            workers=1  # 开发模式使用单进程
        )

        server = uvicorn.Server(config)
        server.run()
