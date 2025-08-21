# 企业级测试用例生成平台 - 数据库结构

## 概述

本目录包含企业级测试用例生成平台的完整数据库结构定义。

## 主要文件

### `final_complete_schema.sql` - 最终完整版数据库结构脚本

这是合并后的最终版本，包含：
- 所有核心表结构
- 需求管理功能
- 智能体日志系统
- 统计视图
- 默认数据

## 数据库结构

### 核心表（13个）

1. **projects** - 项目表
2. **categories** - 测试用例分类表
3. **requirements** - 需求表
4. **test_cases** - 测试用例主表
5. **test_case_requirements** - 测试用例需求关联表
6. **tags** - 标签表
7. **test_case_tags** - 测试用例标签关联表
8. **file_uploads** - 文件上传表
9. **processing_sessions** - 处理会话表
10. **agent_message_logs** - 智能体消息日志表
11. **mind_maps** - 思维导图表
12. **export_records** - 导出记录表
13. **system_configs** - 系统配置表

### 统计视图（5个）

- **v_test_case_stats** - 测试用例统计视图
- **v_project_overview** - 项目概览视图
- **v_session_stats** - 会话统计视图
- **v_requirement_coverage_stats** - 需求覆盖统计视图
- **v_session_agent_summary** - 智能体会话摘要视图

## 使用方法

### 1. 新环境部署

在新的MySQL环境中执行：

```bash
mysql -u root -p < final_complete_schema.sql
```

或者在MySQL客户端中：

```sql
source /path/to/final_complete_schema.sql;
```

### 2. 数据库配置要求

- **MySQL版本**：5.7+ 或 MariaDB 10.2+
- **字符集**：utf8mb4
- **排序规则**：utf8mb4_unicode_ci
- **JSON支持**：需要数据库支持JSON数据类型

### 3. 权限设置

```sql
CREATE USER 'testcase_app'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON test_case_automation.* TO 'testcase_app'@'%';
FLUSH PRIVILEGES;
```

## 核心特性

### 1. 多项目支持
- 支持多个测试项目管理
- 项目级别的数据隔离

### 2. 需求追溯
- 需求与测试用例关联
- 需求覆盖率统计

### 3. AI智能体集成
- 智能体消息日志记录
- 处理过程追踪
- 性能指标统计

### 4. 多种输入源支持
- 文档解析
- 图像分析
- API规范解析
- 数据库模式分析
- 视频分析

### 5. 思维导图可视化
- 测试用例关系可视化
- 自定义布局配置

### 6. 导出功能
- Excel导出
- Word导出
- PDF导出

## 默认数据

脚本会自动创建：
- 默认项目（default-project-001）
- 7个测试分类（功能、性能、安全、兼容性、可用性、接口、数据库）
- 10个系统配置项

## 注意事项

1. **外键约束**：启用了外键约束，删除数据时会级联操作
2. **JSON字段**：多个表使用JSON字段存储复杂数据
3. **索引优化**：已为常用查询添加复合索引
4. **字符集**：必须使用utf8mb4以支持完整Unicode字符

## 维护建议

1. **定期备份**：建议每日备份数据库
2. **索引监控**：根据实际查询模式调整索引
3. **日志清理**：定期清理过期的智能体日志
4. **性能监控**：监控数据库性能和存储空间

## 版本说明

这是最终完整版本，整合了：
- 基础表结构（final_schema.sql）
- 需求管理扩展（add_requirements_tables.sql）
- 智能体日志系统（migrations/add_agent_message_logs.sql）

执行此脚本将创建一个功能完整的企业级测试用例生成平台数据库。
