# 数据库智能体模块

## 📋 概述

本模块包含专门负责数据库操作的智能体，将数据库相关功能从业务逻辑中分离出来，实现更清晰的架构设计。

## 🏗️ 架构设计

### 分层架构
```
业务智能体 (TestCaseGeneratorAgent)
    ↓ 消息传递
数据库智能体 (TestCaseSaverAgent)
    ↓ 调用
仓储层 (TestCaseRepository)
    ↓ 操作
数据模型层 (TestCase, User, Project...)
    ↓ 映射
数据库层 (MySQL)
```

### 职责分离
- **业务智能体**: 专注于业务逻辑处理（如测试用例生成）
- **数据库智能体**: 专门处理数据持久化操作
- **仓储层**: 提供数据访问抽象
- **模型层**: 定义数据结构和关系

## 🔧 核心组件

### 1. TestCaseSaverAgent
测试用例数据库保存智能体，负责：
- 接收测试用例保存请求
- 数据验证和转换
- 批量保存操作
- 错误处理和回滚
- 保存结果反馈

### 2. TestCaseRepository
测试用例仓储类，提供：
- 基础CRUD操作
- 复杂查询方法
- 批量操作支持
- 系统数据管理
- 事务处理

### 3. 数据模型
兼容新数据库结构的模型定义：
- 完整的字段映射
- 枚举类型定义
- 关联关系配置
- Pydantic模型支持

## 🚀 使用方法

### 1. 基本使用
```python
from app.agents.database.test_case_saver_agent import TestCaseSaverAgent, TestCaseSaveRequest

# 创建保存智能体
saver_agent = TestCaseSaverAgent()

# 构建保存请求
save_request = TestCaseSaveRequest(
    session_id="session-123",
    test_cases=test_cases_data,
    project_id="project-id",
    created_by="user-id"
)

# 保存测试用例
result = await saver_agent._save_test_cases_to_database(save_request)
```

### 2. 仓储使用
```python
from app.database.repositories.test_case_repository import TestCaseRepository

# 创建仓储实例
repo = TestCaseRepository()

# 使用数据库会话
async with db_manager.get_session() as session:
    # 创建测试用例
    test_case = await repo.create_test_case(session, test_case_data)
    
    # 查询测试用例
    test_cases = await repo.get_test_cases_by_project(session, project_id)
    
    # 搜索测试用例
    results = await repo.search_test_cases(session, keyword="登录")
```

### 3. 智能体间通信
```python
# 在生成智能体中发送到保存智能体
await self.publish_message(
    save_request,
    topic_id=TopicId(type=TopicTypes.TEST_CASE_SAVER.value, source=self.id.key)
)
```

## 📊 数据流程

### 测试用例生成和保存流程
```
1. 用户请求 → TestCaseGeneratorAgent
2. 生成测试用例数据
3. 发送保存请求 → TestCaseSaverAgent
4. 数据验证和转换
5. 调用 TestCaseRepository
6. 执行数据库操作
7. 返回保存结果
8. 通知用户完成
```

### 错误处理流程
```
1. 捕获异常
2. 记录错误日志
3. 回滚事务
4. 构建错误响应
5. 通知调用方
```

## 🔒 数据安全

### 1. 系统数据管理
- 自动创建AI用户和默认项目
- 确保外键约束满足
- 防止孤立数据产生

### 2. 事务处理
- 批量操作使用事务
- 异常时自动回滚
- 数据一致性保证

### 3. 权限控制
- 基于用户ID的权限验证
- 项目级别的数据隔离
- 操作日志记录

## 📈 性能优化

### 1. 批量操作
- 支持批量创建测试用例
- 减少数据库连接次数
- 提高处理效率

### 2. 连接池管理
- 异步数据库连接
- 连接池复用
- 自动连接回收

### 3. 查询优化
- 索引优化查询
- 分页查询支持
- 条件查询优化

## 🧪 测试

### 运行示例
```bash
cd backend
python examples/test_case_generation_example.py
```

### 单元测试
```bash
pytest tests/test_database_agents.py
```

## 📝 配置

### 数据库配置
```python
# 在 app/core/config.py 中配置
DATABASE_URL = "mysql+asyncmy://user:password@localhost:3306/database"
```

### 智能体配置
```python
# 系统常量
DEFAULT_PROJECT_ID = "project-default"
AI_USER_ID = "user-ai-agent"
```

## 🔄 扩展

### 添加新的数据库智能体
1. 继承 BaseAgent
2. 实现消息处理方法
3. 添加到类型定义
4. 注册到路由

### 添加新的仓储类
1. 继承 BaseRepository
2. 实现特定业务方法
3. 添加到模块导出

## 📞 支持

如有问题或建议，请联系开发团队或提交Issue。
