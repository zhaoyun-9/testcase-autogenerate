"""
API v1 路由聚合 (最终版)
基于最终版数据库结构的统一API设计
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    projects,
    categories,
    test_case_management,
    test_case_simple,
    test_case_generator,
    requirements,
    tags,
    files,
    sessions,
    mindmaps,
    exports,
    system,
    agent_logs
)

api_router = APIRouter()

# 项目管理
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["项目管理"]
)

# 分类管理
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["分类管理"]
)

# 测试用例管理
api_router.include_router(
    test_case_management.router,
    prefix="/test-cases",
    tags=["测试用例管理"]
)

# 测试用例管理（简化版）
api_router.include_router(
    test_case_simple.router,
    prefix="/test-cases-simple",
    tags=["测试用例管理（简化版）"]
)

# 测试用例生成
api_router.include_router(
    test_case_generator.router,
    prefix="/generate",
    tags=["测试用例生成"]
)

# 需求管理
api_router.include_router(
    requirements.router,
    prefix="/requirements",
    tags=["需求管理"]
)

# 标签管理
api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["标签管理"]
)

# 文件处理
api_router.include_router(
    files.router,
    prefix="/files",
    tags=["文件处理"]
)

# 处理会话
api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["处理会话"]
)

# 思维导图
api_router.include_router(
    mindmaps.router,
    prefix="/mindmaps",
    tags=["思维导图"]
)

# 导出功能
api_router.include_router(
    exports.router,
    prefix="/exports",
    tags=["导出功能"]
)

# 系统配置
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["系统配置"]
)

# 智能体日志
api_router.include_router(
    agent_logs.router,
    prefix="/agent-logs",
    tags=["智能体日志"]
)
