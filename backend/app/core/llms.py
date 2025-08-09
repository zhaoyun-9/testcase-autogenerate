"""
LLM模型客户端配置
支持DeepSeek和QwenVL模型
"""
from typing import Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from loguru import logger

from app.core.config import settings


def get_deepseek_model_client() -> OpenAIChatCompletionClient:
    """获取DeepSeek模型客户端"""
    try:
        client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com/v1",
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,  # 添加 structured_output 字段
                "family": "unknown",
                "multiple_system_messages": True
            }
        )
        logger.info("DeepSeek模型客户端创建成功")
        return client
    except Exception as e:
        logger.error(f"创建DeepSeek模型客户端失败: {str(e)}")
        raise


def get_qwenvl_model_client() -> OpenAIChatCompletionClient:
    """获取QwenVL模型客户端"""
    try:
        client = OpenAIChatCompletionClient(
            model="qwen-vl-plus",
            api_key=settings.QWENVL_API_KEY,
            base_url=settings.QWENVL_BASE_URL or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_info={
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,  # 添加 structured_output 字段
                "family": "unknown",
                "multiple_system_messages": True
            }
        )
        logger.info("QwenVL模型客户端创建成功")
        return client
    except Exception as e:
        logger.error(f"创建QwenVL模型客户端失败: {str(e)}")
        raise


def get_model_client(model_type: str = "deepseek") -> OpenAIChatCompletionClient:
    """根据类型获取模型客户端"""
    if model_type.lower() == "qwenvl":
        return get_qwenvl_model_client()
    else:
        return get_deepseek_model_client()
