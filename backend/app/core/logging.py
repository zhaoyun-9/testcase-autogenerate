"""
日志配置模块
"""
import sys
import os
from pathlib import Path
from loguru import logger
import multiprocessing

from app.core.config import settings


def get_process_safe_filename(base_filename: str) -> str:
    """获取进程安全的文件名"""
    try:
        # 获取当前进程ID
        pid = os.getpid()
        # 获取进程名称（如果是主进程则为空）
        process_name = multiprocessing.current_process().name

        # 如果是主进程，不添加后缀
        if process_name == "MainProcess":
            return base_filename

        # 为子进程添加PID后缀
        path = Path(base_filename)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        return str(parent / f"{stem}_{pid}{suffix}")
    except Exception:
        # 如果获取进程信息失败，返回原文件名
        return base_filename


def setup_logging():
    """设置日志配置"""

    # 移除默认的日志处理器
    logger.remove()

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # 获取进程安全的日志文件名
    app_log_file = get_process_safe_filename(settings.LOG_FILE)
    error_log_file = get_process_safe_filename("logs/error.log")
    agents_log_file = get_process_safe_filename("logs/agents.log")
    api_log_file = get_process_safe_filename("logs/api.log")

    # 添加文件处理器 - 所有日志
    logger.add(
        app_log_file,
        format=file_format,
        level="DEBUG",
        rotation="10 MB",  # 改为按大小轮转，避免时间轮转冲突
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,  # 启用队列模式，避免多进程冲突
        catch=True
    )

    # 添加错误日志文件
    logger.add(
        error_log_file,
        format=file_format,
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        catch=True
    )

    # 添加智能体专用日志
    logger.add(
        agents_log_file,
        format=file_format,
        level="INFO",
        rotation="5 MB",
        retention="7 days",
        filter=lambda record: "agent" in record["name"].lower(),
        backtrace=True,
        diagnose=True,
        enqueue=True,
        catch=True
    )

    # 添加API请求日志
    logger.add(
        api_log_file,
        format=file_format,
        level="INFO",
        rotation="5 MB",
        retention="7 days",
        filter=lambda record: "api" in record["name"].lower() or "endpoint" in record["name"].lower(),
        backtrace=True,
        diagnose=True,
        enqueue=True,
        catch=True
    )

    logger.info("日志系统初始化完成")


def get_logger(name: str):
    """获取指定名称的日志器"""
    return logger.bind(name=name)
