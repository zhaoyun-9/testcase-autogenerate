"""
安全的日志配置模块
专门处理多进程环境下的日志冲突问题
"""
import sys
import os
import logging
from pathlib import Path
from loguru import logger
import multiprocessing
import threading
from datetime import datetime

from app.core.config import settings


class ProcessSafeLogger:
    """进程安全的日志器"""
    
    def __init__(self):
        self._initialized = False
        self._lock = threading.Lock()
        self.process_id = os.getpid()
        self.process_name = multiprocessing.current_process().name
    
    def get_safe_filename(self, base_filename: str) -> str:
        """获取进程安全的文件名"""
        try:
            path = Path(base_filename)
            
            # 如果是主进程，使用原文件名
            if self.process_name == "MainProcess":
                return str(path)
            
            # 子进程使用带PID的文件名
            stem = path.stem
            suffix = path.suffix
            parent = path.parent
            
            return str(parent / f"{stem}_{self.process_id}{suffix}")
        except Exception:
            return base_filename
    
    def setup_logging(self):
        """设置进程安全的日志配置"""
        with self._lock:
            if self._initialized:
                return
            
            try:
                # 移除默认处理器
                logger.remove()
                
                # 创建日志目录
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)
                
                # 控制台格式
                console_format = (
                    "<green>{time:HH:mm:ss}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan> | "
                    "<level>{message}</level>"
                )
                
                # 文件格式
                file_format = (
                    "{time:YYYY-MM-DD HH:mm:ss} | "
                    "{level: <8} | "
                    "PID:{process.id} | "
                    "{name}:{function}:{line} | "
                    "{message}"
                )
                
                # 控制台处理器
                logger.add(
                    sys.stdout,
                    format=console_format,
                    level=settings.LOG_LEVEL,
                    colorize=True,
                    catch=True
                )
                
                # 主日志文件
                main_log = self.get_safe_filename(settings.LOG_FILE)
                logger.add(
                    main_log,
                    format=file_format,
                    level="DEBUG",
                    rotation="10 MB",
                    retention="7 days",
                    compression="zip",
                    enqueue=True,  # 队列模式，避免冲突
                    catch=True
                )
                
                # 错误日志
                error_log = self.get_safe_filename("logs/error.log")
                logger.add(
                    error_log,
                    format=file_format,
                    level="ERROR",
                    rotation="5 MB",
                    retention="7 days",
                    enqueue=True,
                    catch=True
                )
                
                # 智能体日志（仅主进程）
                if self.process_name == "MainProcess":
                    agents_log = self.get_safe_filename("logs/agents.log")
                    logger.add(
                        agents_log,
                        format=file_format,
                        level="INFO",
                        rotation="5 MB",
                        retention="3 days",
                        filter=lambda record: "agent" in record["name"].lower(),
                        enqueue=True,
                        catch=True
                    )
                
                self._initialized = True
                logger.info(f"日志系统初始化完成 - 进程: {self.process_name}({self.process_id})")
                
            except Exception as e:
                print(f"日志初始化失败: {e}")
                # 降级到基本日志
                self._setup_fallback_logging()
    
    def _setup_fallback_logging(self):
        """设置降级日志配置"""
        try:
            logger.remove()
            logger.add(
                sys.stdout,
                format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
                level="INFO",
                colorize=True,
                catch=True
            )
            logger.warning("使用降级日志配置")
        except Exception as e:
            print(f"降级日志配置也失败: {e}")


# 全局日志器实例
_safe_logger = ProcessSafeLogger()


def setup_logging():
    """设置日志配置"""
    _safe_logger.setup_logging()


def get_logger(name: str):
    """获取指定名称的日志器"""
    return logger.bind(name=name)


def cleanup_process_logs():
    """清理当前进程的日志文件"""
    try:
        if _safe_logger.process_name != "MainProcess":
            logs_dir = Path("logs")
            pattern = f"*_{_safe_logger.process_id}.log"
            for log_file in logs_dir.glob(pattern):
                try:
                    log_file.unlink()
                    print(f"清理进程日志: {log_file}")
                except Exception:
                    pass
    except Exception:
        pass


# 注册进程退出时的清理函数
import atexit
atexit.register(cleanup_process_logs)
