# RAG知识库检索智能体设计文档

## 📋 概述

RAG知识库检索智能体是一个专门负责从知识库中检索相关信息的智能体，为测试用例生成提供上下文支持。该智能体基于AutoGen Core架构实现，参考了`requirement_analysis_agent.py`的优秀设计模式，并集成了`examples/test_retrieval.py`中的RAG检索逻辑。

## 🏗️ 架构设计

### 核心组件

1. **RagRetrievalAgent**: 主要智能体类
2. **RagRetrievalRequest/Response**: 消息类型定义
3. **RagRetrievalResult**: 检索结果数据模型
4. **R2R客户端集成**: 与R2R知识库系统的接口

### 设计原则

- **模块化**: 清晰的职责分离，易于维护和扩展
- **异步处理**: 基于AsyncIO的非阻塞操作
- **错误容错**: 完善的异常处理和降级机制
- **配置灵活**: 支持多种检索模式和参数配置

## 🔧 功能特性

### 1. 多模式检索
- **基础检索**: 简单的关键词匹配
- **高级检索**: 语义搜索 + 全文搜索
- **自定义检索**: 支持过滤条件和复杂查询

### 2. 智能查询增强
- 自动整合需求内容和测试点信息
- 构建上下文相关的增强查询
- 支持多种上下文类型

### 3. RAG生成支持
- 可选的RAG文本生成功能
- 可配置的生成参数
- 流式和非流式输出支持

### 4. 结果处理与分析
- 相关性评分计算
- 知识来源追踪
- 置信度评估

## 📨 消息接口

### 请求消息 (RagRetrievalRequest)

```python
{
    "session_id": "会话ID",
    "query": "检索查询",
    "requirements": "需求内容(可选)",
    "test_points": "测试点列表(可选)",
    "search_mode": "检索模式(basic/advanced/custom)",
    "search_settings": "检索设置",
    "rag_generation_config": "RAG生成配置",
    "filters": "过滤条件(可选)",
    "context_type": "上下文类型",
    "max_results": "最大结果数量"
}
```

### 响应消息 (RagRetrievalResponse)

```python
{
    "session_id": "会话ID",
    "retrieval_id": "检索ID",
    "query": "原始查询",
    "search_results": "检索结果列表",
    "rag_completion": "RAG生成的完整回答(可选)",
    "context_chunks": "上下文片段",
    "relevance_scores": "相关性评分列表",
    "total_results": "总结果数量",
    "processing_time": "处理时间",
    "confidence_score": "置信度评分",
    "knowledge_sources": "知识来源列表",
    "created_at": "创建时间"
}
```

## 🔌 集成方式

### 1. 在测试用例生成智能体中的集成

```python
# 在 test_case_generator_agent.py 的 _generatetest_cases_from_test_points 方法中
async def _retrieve_rag_context(self, message: TestPointExtractionResponse):
    # 构建RAG检索请求
    rag_request = RagRetrievalRequest(
        session_id=message.session_id,
        query="构建的查询",
        requirements="需求内容",
        test_points="测试点列表",
        # ... 其他配置
    )
    
    # 发送RAG检索请求
    await self.publish_message(
        rag_request,
        topic_id=TopicId(type=TopicTypes.RAG_RETRIEVAL.value, source=self.id.key)
    )
```

### 2. 智能体注册

```python
# 在 orchestrator_service.py 中注册
await self.agent_factory.register_agent_to_runtime(
    self.runtime,
    AgentTypes.RAG_RETRIEVAL.value,
    TopicTypes.RAG_RETRIEVAL.value,
)
```

## ⚙️ 配置说明

### RAG检索配置

```python
retrieval_config = {
    'base_url': "http://localhost:7272",  # R2R服务地址
    'superuser_email': "admin@example.com",  # 登录邮箱
    'superuser_password': "change_me_immediately",  # 登录密码
    'default_search_mode': "basic",  # 默认检索模式
    'default_max_results': 10,  # 默认最大结果数
    'default_confidence_threshold': 0.7,  # 默认置信度阈值
    'enable_semantic_search': True,  # 启用语义搜索
    'enable_fulltext_search': True,  # 启用全文搜索
    'enable_rag_generation': True  # 启用RAG生成
}
```

### 检索设置示例

```python
search_settings = {
    "use_semantic_search": True,
    "use_fulltext_search": True,
    "limit": 10,
    "filters": {
        "metadata.category": {"$eq": "test_cases"},
        "metadata.priority": {"$in": ["high", "medium"]}
    }
}
```

## 🧪 测试与验证

### 运行测试脚本

```bash
cd backend
python test_rag_agent.py
```

### 测试内容

1. **智能体配置测试**: 验证智能体初始化和配置
2. **RAG检索功能测试**: 测试查询构建和检索执行
3. **消息处理测试**: 验证消息处理流程

## 🔍 使用示例

### 基础检索示例

```python
# 创建检索请求
request = RagRetrievalRequest(
    session_id="test-session",
    query="用户登录测试用例设计",
    search_mode="basic",
    max_results=5
)

# 发送请求到RAG检索智能体
await publish_message(request, topic_id=TopicId(type=TopicTypes.RAG_RETRIEVAL.value))
```

### 高级检索示例

```python
# 创建高级检索请求
request = RagRetrievalRequest(
    session_id="test-session",
    query="API接口测试最佳实践",
    requirements="REST API用户认证接口测试需求",
    test_points=[
        {"title": "认证token验证", "type": "security"},
        {"title": "参数校验测试", "type": "functional"}
    ],
    search_mode="advanced",
    search_settings={
        "use_semantic_search": True,
        "use_fulltext_search": True,
        "limit": 8,
        "filters": {
            "metadata.test_type": {"$eq": "api_testing"}
        }
    },
    rag_generation_config={
        "stream": False,
        "max_tokens": 300
    },
    context_type="api_testing",
    max_results=8
)
```

## 🚀 部署要求

### 依赖服务

1. **R2R知识库服务**: 需要运行在配置的地址上
2. **AutoGen Core运行时**: 智能体运行环境
3. **数据库服务**: 用于存储检索结果(可选)

### 环境配置

```bash
# 安装R2R客户端
pip install r2r

# 确保R2R服务运行
# 默认地址: http://localhost:7272
```

## 🔧 扩展与定制

### 自定义检索策略

可以通过继承`RagRetrievalAgent`类来实现自定义检索策略：

```python
class CustomRagRetrievalAgent(RagRetrievalAgent):
    async def _perform_rag_retrieval(self, message):
        # 实现自定义检索逻辑
        pass
```

### 添加新的检索模式

在`_execute_search`方法中添加新的检索模式支持。

## 📝 注意事项

1. **R2R服务依赖**: 确保R2R知识库服务正常运行
2. **网络连接**: 检索功能需要网络连接到R2R服务
3. **性能考虑**: 大量并发检索请求可能影响性能
4. **错误处理**: 智能体具有完善的错误处理和降级机制

## 🤝 贡献指南

1. 遵循现有的代码风格和架构模式
2. 添加适当的日志记录和错误处理
3. 编写相应的测试用例
4. 更新相关文档

## 📄 许可证

本项目遵循项目整体的许可证协议。
