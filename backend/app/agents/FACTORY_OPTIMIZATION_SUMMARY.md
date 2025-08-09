# 智能体工厂和基类优化总结

## 🎯 优化目标

参考 `examples/agents/factory.py` 和 `examples/base.py` 的优秀设计模式，全面优化后端智能体工厂和基类，提升功能完整性、易用性和可扩展性。

## 📋 主要改进

### 1. **类型系统扩展** (`app/core/types.py`)

#### 新增智能体类型
```python
# Web平台智能体
PAGE_ANALYZER = "page_analyzer"
PAGE_ANALYSIS_STORAGE = "page_analysis_storage"
YAML_GENERATOR = "yaml_generator"
YAML_EXECUTOR = "yaml_executor"
PLAYWRIGHT_GENERATOR = "playwright_generator"
PLAYWRIGHT_EXECUTOR = "playwright_executor"
SCRIPT_DATABASE_SAVER = "script_database_saver"
IMAGE_DESCRIPTION_GENERATOR = "image_description_generator"
TEST_CASE_ELEMENT_PARSER = "test_case_element_parser"
```

#### 新增主题类型
- 为每个新智能体类型添加对应的主题类型
- 添加 `STREAM_OUTPUT` 系统主题

#### 消息区域优化
- 重命名 `MessageRegions` 为 `MessageRegion`
- 添加新的区域类型：`SUCCESS`, `WARNING`, `INFO`
- 保持向后兼容性

### 2. **智能体工厂优化** (`app/agents/factory.py`)

#### 核心功能增强
- ✅ **智能体注册系统**：`register_agent()` 方法支持动态注册
- ✅ **平台过滤支持**：按平台获取和创建智能体
- ✅ **批量创建功能**：`create_agents_for_platform()` 批量创建
- ✅ **统计信息**：`get_factory_stats()` 获取详细统计
- ✅ **多种智能体类型**：支持 AssistantAgent、UserProxyAgent、ClosureAgent

#### 新增方法
```python
# 智能体注册
register_agent(agent_type, agent_class, agent_name, topic_type, platform)

# 创建不同类型的智能体
create_assistant_agent(name, system_message, model_client_type, **kwargs)
create_user_proxy_agent(name, human_input_mode, **kwargs)
create_closure_agent(agent_id, handler_func, agent_name)

# 平台相关功能
get_available_agents(platform=None)
create_agents_for_platform(platform, **common_kwargs)
get_available_agent_types(platform=None)

# 信息查询
get_agent_info(agent_type)
is_agent_available(agent_type)
get_factory_stats()
```

#### 智能模型客户端选择
- **图片分析**：优先使用 UI-TARS，回退到 QwenVL
- **视频分析**：使用 QwenVL
- **文本处理**：使用 DeepSeek
- **支持自定义**：允许手动指定模型客户端

### 3. **BaseAgent基类优化** (`app/core/agents/base.py`)

#### 消息发送系统升级
```python
# 统一消息发送接口
send_message(content, message_type, is_final, result, region, source)

# 便捷方法
send_progress(content, progress_percent)
send_success(content, result)
send_warning(content)
send_error(error_message, is_final)
send_info(content)

# 流式消息（与examples兼容）
send_stream_message(content, message_type, is_final, result, region)

# 日志和发送结合
log_and_send(content, level, message_type, region)
```

#### 性能监控系统
```python
# 开始监控
monitor_id = agent.start_performance_monitoring("operation_name")

# 结束监控并获取数据
performance_data = agent.end_performance_monitoring(monitor_id)
```

#### 异常处理机制
```python
# 统一异常处理
await agent.handle_exception("function_name", exception, send_error_message=True)
```

#### 上下文管理
```python
# 创建上下文变量
context_vars = agent.create_context_variables(
    operation="demo",
    user_id="test_user"
)
```

### 4. **架构改进**

#### 消息流向优化
```
智能体 → send_message() → publish_message() → TopicId(STREAM_OUTPUT)
                      ↓ (fallback)
                   collector.collect_message()
```

#### 平台支持
- **TEST_CASE平台**：测试用例生成相关智能体
- **WEB平台**：Web自动化测试相关智能体
- **GENERAL平台**：通用智能体

#### 双重发布机制
- 优先使用新的 `publish_message` 机制
- 向后兼容原有的 `collector` 机制

## 🔄 API对比

### 工厂使用对比

#### 原有API
```python
# 创建智能体
agent = agent_factory.create_agent("document_parser")

# 获取可用类型
types = agent_factory.get_available_agent_types()
```

#### 新增API
```python
# 注册自定义智能体
agent_factory.register_agent(
    agent_type="custom_agent",
    agent_class=CustomAgent,
    agent_name="自定义智能体",
    platform=AgentPlatform.WEB
)

# 按平台获取智能体
web_agents = agent_factory.get_available_agents(AgentPlatform.WEB)

# 批量创建
agents = agent_factory.create_agents_for_platform(
    platform=AgentPlatform.WEB,
    custom_param="value"
)

# 创建不同类型的智能体
assistant = agent_factory.create_assistant_agent(
    name="助手",
    system_message="你是一个助手",
    model_client_type="deepseek"
)

user_proxy = agent_factory.create_user_proxy_agent(
    name="用户代理",
    human_input_mode="NEVER"
)

# 获取统计信息
stats = agent_factory.get_factory_stats()
```

### BaseAgent使用对比

#### 原有API
```python
await agent.send_response(
    content="消息",
    message_type="info",
    region="main"
)
```

#### 新增API
```python
# 便捷方法
await agent.send_progress("处理中...", 50.0)
await agent.send_success("成功", {"result": "data"})
await agent.send_warning("警告")
await agent.send_error("错误")

# 性能监控
monitor_id = agent.start_performance_monitoring("operation")
# ... 执行操作 ...
metrics = agent.end_performance_monitoring(monitor_id)

# 异常处理
try:
    # 操作
    pass
except Exception as e:
    await agent.handle_exception("operation", e)

# 上下文创建
context = agent.create_context_variables(param="value")
```

## 🏗️ 扩展性设计

### 智能体注册机制
- 支持运行时动态注册新智能体类型
- 自动处理名称映射和主题关联
- 平台分类管理

### 模型客户端智能选择
- 根据智能体类型自动选择最适合的模型
- 支持回退机制
- 允许手动覆盖

### 性能监控
- 细粒度操作监控
- 自动清理机制
- 可扩展的指标收集

## 📊 兼容性保证

- ✅ **完全向后兼容**：所有原有API继续工作
- ✅ **渐进式迁移**：可以逐步采用新功能
- ✅ **双重机制**：新旧消息发布方式并存

## 🚀 使用建议

1. **新项目**：直接使用新的API和功能
2. **现有项目**：
   - 保持现有代码不变
   - 新功能使用新API
   - 逐步迁移到便捷方法

3. **性能监控**：在关键操作中使用性能监控
4. **平台管理**：按平台组织智能体
5. **异常处理**：使用统一的异常处理机制

## 📝 示例代码

参考以下文件查看完整使用示例：
- `backend/app/agents/factory_usage_example.py` - 工厂使用示例
- `backend/app/core/agents/example_usage.py` - BaseAgent使用示例

## 🔮 未来扩展

优化后的架构为以下功能预留了扩展空间：
- 分布式智能体部署
- 智能体协作机制
- 高级性能分析
- 动态负载均衡
- 智能体生命周期管理
