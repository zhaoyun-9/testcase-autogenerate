# 测试用例生成平台

<div align="center">

![Platform Logo](https://img.shields.io/badge/测试用例生成平台-blue?style=for-the-badge)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=flat-square)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.3+-4FC08D?style=flat-square)](https://vuejs.org/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.6.4-orange?style=flat-square)](https://github.com/microsoft/autogen)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue?style=flat-square)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**🚀 基于AI多智能体协作的测试用例自动生成平台**

支持多种输入源 | 智能分析生成 | 思维导图可视化 | 专业导出功能

</div>

---

## 📋 项目概述

测试用例生成平台是一套基于AI多智能体协作的自动化测试用例生成系统。通过先进的人工智能技术，支持从图片、文档、API规范、数据库模式、视频等多种输入源智能生成专业的测试用例，并提供思维导图可视化、分类管理、优先级分配等企业级功能。

### 🎯 核心价值

- **🤖 AI驱动**: 基于DeepSeek-Chat和QwenVL模型的智能分析
- **🔄 多智能体**: AutoGen框架实现的协作式处理流程
- **📊 可视化**: 专业的思维导图展示和编辑功能
- **🏢 企业级**: 完整的分类、标签、优先级管理体系
- **📤 标准化**: 支持Excel、Word、PDF等格式的专业导出

## 🏗️ 技术架构

### 前端技术栈
- **Vue 3.3+** + **TypeScript** - 渐进式前端框架
- **Element Plus** - 企业级Vue组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP客户端
- **Vite** - 现代化构建工具
- **G6** - 图可视化引擎（思维导图）

### 后端技术栈
- **FastAPI 0.104+** - 高性能异步Web框架
- **SSE (Server-Sent Events)** - 实时流式数据传输
- **AutoGen 0.6.4** - 微软多智能体协作框架
- **MySQL 8.0+** - 关系型数据库
- **SQLAlchemy 2.0+** - 异步ORM框架
- **Pydantic V2** - 数据验证和序列化
- **Uvicorn** - ASGI服务器

### AI模型集成
- **DeepSeek-Chat** - 主要的大语言模型，用于文本理解和生成
- **QwenVL** - 视觉理解模型，用于图片和视频分析
- **Volcengine Ark SDK** - 视频分析和处理

## ✨ 核心功能

### 🔄 多智能体协作处理流程

系统采用AutoGen多智能体协作架构，实现智能化的测试用例生成流程：

```mermaid
graph LR
    A[输入源] --> B[文件解析智能体]
    A --> C[图片分析智能体]
    A --> D[视频分析智能体]
    B --> E[测试用例生成智能体]
    C --> E
    D --> E
    E --> F[思维导图生成智能体]
    E --> G[数据库保存智能体]
    F --> H[最终输出]
    G --> H
```

### 📥 多样化输入支持

| 输入类型 | 支持格式 | 处理智能体 | 应用场景 |
|---------|---------|-----------|---------|
| 📸 **图片分析** | JPG, PNG, GIF, BMP, WebP | 图片分析智能体 | 流程图、思维导图、UI截图解析 |
| 📄 **文档解析** | PDF, DOCX, DOC, TXT, MD | 文档解析智能体 | 需求文档、规格说明书提取 |
| 🔌 **API规范** | JSON, YAML, YML | API解析智能体 | Swagger/OpenAPI规范解析 |
| 🗄️ **数据库模式** | SQL, DDL | 数据库解析智能体 | 表结构分析，数据测试用例生成 |
| 🎥 **视频分析** | MP4, AVI, MOV, WMV, FLV | 视频分析智能体 | 操作录屏，用户行为序列分析 |
| ✍️ **手动输入** | 文本 | 需求分析智能体 | 直接输入需求描述 |

### 🧠 智能测试用例生成

- **🎯 智能分类**: 自动识别功能、性能、安全、兼容性、可用性、接口、数据库测试
- **📊 级别划分**: 单元、集成、系统、验收测试自动分类
- **⭐ 优先级分配**: P0-P4优先级智能评估和手动调整
- **🔗 需求追溯**: 测试用例与需求的双向关联
- **📝 标准格式**: 包含前置条件、测试步骤、预期结果的完整用例

### 🗺️ 思维导图可视化

- **🎨 专业渲染**: 基于G6引擎的高质量图形渲染
- **✏️ 在线编辑**: 支持节点拖拽、编辑、样式调整
- **🔄 实时同步**: 测试用例与思维导图双向同步
- **💾 持久化存储**: 思维导图数据与会话关联存储
- **📱 响应式设计**: 适配不同屏幕尺寸

### 📊 管理功能

- **🏗️ 项目管理**: 多项目支持，项目级数据隔离
- **📂 分类体系**: 层级分类管理，支持自定义分类
- **🏷️ 标签系统**: 灵活的标签分类和筛选
- **👥 协作功能**: 支持团队协作和权限管理
- **📈 统计分析**: 丰富的统计视图和数据分析

### 📤 专业导出功能

- **📋 Excel导出**: 标准化测试用例Excel模板
- **📝 Word导出**: 专业的测试用例文档格式
- **📄 PDF导出**: 高质量的PDF报告生成
- **🎛️ 自定义配置**: 灵活的导出字段和格式配置

## 📁 项目结构

```
TestCaseAutomation/
├── 📁 frontend/                    # Vue.js 前端项目
│   ├── 📁 src/
│   │   ├── 📁 api/                # API接口定义
│   │   ├── 📁 components/         # 通用组件
│   │   │   ├── 📁 common/         # 基础组件
│   │   │   ├── 📁 test-case/      # 测试用例相关组件
│   │   │   └── 📁 mind-map/       # 思维导图组件
│   │   ├── 📁 views/              # 页面视图
│   │   │   ├── 📁 test-case/      # 测试用例页面
│   │   │   │   ├── generate/      # 生成页面
│   │   │   │   ├── manage/        # 管理页面
│   │   │   │   └── export/        # 导出页面
│   │   │   └── 📁 dashboard/      # 仪表板
│   │   ├── 📁 stores/             # Pinia状态管理
│   │   ├── 📁 utils/              # 工具函数
│   │   ├── 📁 types/              # TypeScript类型定义
│   │   └── 📁 assets/             # 静态资源
│   ├── 📁 public/                 # 公共静态资源
│   ├── 📄 package.json            # 前端依赖配置
│   ├── 📄 vite.config.ts          # Vite构建配置
│   └── 📄 tsconfig.json           # TypeScript配置
├── 📁 backend/                     # FastAPI 后端项目
│   ├── 📁 app/
│   │   ├── 📁 api/                # API路由模块
│   │   │   ├── 📁 endpoints/      # API端点
│   │   │   └── 📁 deps.py         # 依赖注入
│   │   ├── 📁 agents/             # AutoGen智能体模块
│   │   │   ├── 📁 base/           # 基础智能体类
│   │   │   ├── 📁 document/       # 文档解析智能体
│   │   │   ├── 📁 image/          # 图片分析智能体
│   │   │   ├── 📁 video/          # 视频分析智能体
│   │   │   ├── 📁 test_case/      # 测试用例生成智能体
│   │   │   └── 📁 database/       # 数据库操作智能体
│   │   ├── 📁 core/               # 核心模块
│   │   │   ├── 📄 config.py       # 配置管理
│   │   │   ├── 📄 security.py     # 安全相关
│   │   │   └── 📄 database.py     # 数据库连接
│   │   ├── 📁 database/           # 数据库模块
│   │   │   ├── 📁 models/         # SQLAlchemy模型
│   │   │   ├── 📁 repositories/   # 数据访问层
│   │   │   └── 📁 migrations/     # 数据库迁移
│   │   ├── 📁 services/           # 业务服务层
│   │   │   ├── 📁 test_case/      # 测试用例服务
│   │   │   ├── 📁 file_upload/    # 文件上传服务
│   │   │   └── 📁 export/         # 导出服务
│   │   └── 📁 utils/              # 工具函数
│   ├── 📁 tests/                  # 测试文件
│   ├── 📄 main.py                 # FastAPI应用入口
│   ├── 📄 requirements.txt        # Python依赖
│   └── 📄 .env.example            # 环境变量示例
├── 📁 database/                    # 数据库相关
│   ├── 📄 final_complete_schema.sql # 完整数据库结构
│   ├── 📄 DEPLOYMENT_GUIDE.md     # 数据库部署指南
│   ├── 📄 README.md               # 数据库说明
│   └── 📁 migrations/             # 历史迁移文件
├── 📁 uploads/                     # 文件上传目录
│   ├── 📁 documents/              # 文档文件
│   ├── 📁 images/                 # 图片文件
│   ├── 📁 videos/                 # 视频文件
│   └── 📁 exports/                # 导出文件
├── 📁 logs/                       # 日志文件
├── 📄 README.md                   # 项目说明文档
├── 📄 docker-compose.yml          # Docker编排配置
└── 📄 .gitignore                  # Git忽略配置
```

## 🚀 快速开始

### 📋 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| **Python** | 3.9+ | 后端运行环境 |
| **Node.js** | 18+ | 前端构建环境 |
| **MySQL** | 8.0+ | 主数据库 |
| **Redis** | 6.0+ | 缓存（可选） |

### ⚡ 一键部署（推荐）

#### 方式一：自动化脚本部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd TestCaseAutomation

# 2. 运行自动化部署脚本
python deploy.py

# 3. 按提示完成配置
# - 数据库连接信息
# - AI模型API密钥
# - 其他配置项
```

自动化脚本将完成：
- ✅ 环境检查和依赖安装
- ✅ 数据库初始化
- ✅ 配置文件生成
- ✅ 服务启动

#### 方式二：Docker一键部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd TestCaseAutomation

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库和API密钥

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps
```

### 🔧 手动部署（开发环境）

#### 步骤1: 项目克隆和环境准备

```bash
# 克隆项目
git clone <repository-url>
cd TestCaseAutomation

# 创建必要的目录
mkdir -p uploads/{documents,images,videos,exports}
mkdir -p logs
```

#### 步骤2: 数据库初始化

```bash
# 方式1: 使用完整SQL脚本（推荐）
mysql -u root -p < database/final_complete_schema.sql

# 方式2: 手动创建
mysql -u root -p
mysql> CREATE DATABASE test_case_automation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> USE test_case_automation;
mysql> SOURCE database/final_complete_schema.sql;
mysql> EXIT;
```

#### 步骤3: 后端环境配置

```bash
cd backend

# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 创建环境配置文件
cp .env.example .env
```

编辑 `backend/.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/test_case_automation

# AI模型配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

QWENVL_API_KEY=your_qwenvl_api_key_here
QWENVL_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 文件上传配置
UPLOAD_DIR=../uploads
MAX_FILE_SIZE=100  # MB

# 其他配置
DEBUG=True
LOG_LEVEL=INFO
```

#### 步骤4: 前端环境配置

```bash
cd frontend-mine-old

# 安装Node.js依赖
npm install
# 或使用yarn
yarn install

# 创建前端环境配置（可选）
cp .env.example .env.local
```

编辑 `frontend/.env.local`（可选）：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 其他前端配置
VITE_APP_TITLE=测试用例生成平台
```

#### 步骤5: 启动服务

**启动后端服务：**

```bash
cd backend
# 确保虚拟环境已激活
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端服务：**

```bash
cd frontend-mine-old
npm run dev
# 或
yarn dev
```

#### 步骤6: 验证部署

访问以下地址验证部署是否成功：

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 **前端界面** | http://localhost:5173 | Vue.js应用主界面 |
| 🔧 **后端API** | http://localhost:8000 | FastAPI服务 |
| 📚 **API文档** | http://localhost:8000/docs | Swagger UI文档 |
| 📖 **ReDoc文档** | http://localhost:8000/redoc | ReDoc API文档 |
| 🔍 **健康检查** | http://localhost:8000/health | 服务健康状态 |

### 🐳 生产环境部署

#### Docker Compose部署

1. **准备配置文件**

```bash
# 复制环境配置
cp .env.example .env

# 编辑生产环境配置
vim .env
```

2. **生产环境配置示例**

```env
# 生产环境配置
NODE_ENV=production
DEBUG=False

# 数据库配置（生产环境）
DATABASE_URL=mysql+aiomysql://testcase_user:secure_password@db:3306/test_case_automation

# AI模型配置
DEEPSEEK_API_KEY=your_production_deepseek_key
QWENVL_API_KEY=your_production_qwenvl_key

# 安全配置
SECRET_KEY=your_super_secret_key_here
ALLOWED_HOSTS=your-domain.com,localhost

# 文件存储配置
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=200

# Redis配置（可选）
REDIS_URL=redis://redis:6379/0
```

3. **启动生产服务**

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend-mine-old
```

4. **生产环境维护**

```bash
# 更新服务
docker-compose pull
docker-compose up -d

# 备份数据库
docker-compose exec db mysqldump -u root -p test_case_automation > backup.sql

# 清理日志
docker-compose exec backend find /app/logs -name "*.log" -mtime +7 -delete
```

## 🎯 使用指南

### 📝 基本使用流程

1. **选择输入方式**
   - 上传图片、文档、API规范、视频文件
   - 或直接输入需求描述

2. **AI智能分析**
   - 系统自动选择合适的智能体进行分析
   - 实时显示处理进度和日志

3. **查看生成结果**
   - 查看生成的测试用例列表
   - 查看对应的思维导图

4. **编辑和管理**
   - 在线编辑测试用例内容
   - 调整优先级和分类
   - 添加标签

5. **导出和分享**
   - 选择导出格式（Excel/Word/PDF）
   - 下载生成的文件

### 🔧 高级功能

#### 智能体日志监控
- 实时查看智能体处理过程
- 监控处理性能和错误信息
- 分析处理结果质量

#### 批量操作
- 批量导入多个文件
- 批量编辑测试用例
- 批量导出选定用例

#### 项目管理
- 创建和管理多个项目
- 项目级别的数据隔离
- 团队协作功能

## 🛠️ 开发指南

### 📚 API文档

| 文档类型 | 访问地址 | 说明 |
|---------|---------|------|
| **Swagger UI** | http://localhost:8000/docs | 交互式API文档 |
| **ReDoc** | http://localhost:8000/redoc | 美观的API文档 |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | API规范文件 |

### 🤖 智能体架构详解

系统采用AutoGen 0.6.4多智能体协作架构：

```python
# 智能体类型和职责
AGENT_TYPES = {
    "DocumentParserAgent": "文档解析和内容提取",
    "ImageAnalysisAgent": "图片内容分析和理解",
    "VideoAnalysisAgent": "视频内容分析和行为提取",
    "APISpecParserAgent": "API规范解析和接口分析",
    "DatabaseSchemaAgent": "数据库模式分析",
    "TestCaseGeneratorAgent": "测试用例生成和优化",
    "MindMapGeneratorAgent": "思维导图生成和布局",
    "DatabaseSaverAgent": "数据持久化和存储"
}
```

### 🔄 智能体通信流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant M as 管理器
    participant P as 解析智能体
    participant G as 生成智能体
    participant S as 存储智能体

    U->>M: 上传文件/输入需求
    M->>P: 分配解析任务
    P->>P: 分析内容
    P->>G: 发送解析结果
    G->>G: 生成测试用例
    G->>S: 发送生成结果
    S->>S: 保存到数据库
    S->>M: 返回保存状态
    M->>U: 返回最终结果
```

### 🧪 测试指南

#### 运行单元测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端测试
cd frontend-mine-old
npm run test
```

#### 运行集成测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
pytest tests/integration/ -v
```

### 📦 构建和部署

#### 前端构建

```bash
cd frontend-mine-old
npm run build
# 构建产物在 dist/ 目录
```

#### 后端打包

```bash
cd backend
# 创建生产环境镜像
docker build -t testcase-backend:latest .
```

### 🤝 贡献指南

1. **Fork项目** - 点击右上角Fork按钮
2. **创建分支** - `git checkout -b feature/your-feature`
3. **提交代码** - `git commit -am 'Add some feature'`
4. **推送分支** - `git push origin feature/your-feature`
5. **创建PR** - 在GitHub上创建Pull Request

#### 代码规范

- **Python**: 遵循PEP 8规范，使用black格式化
- **TypeScript**: 遵循ESLint配置，使用Prettier格式化
- **提交信息**: 使用约定式提交格式

#### 开发环境设置

```bash
# 安装开发工具
pip install black flake8 pytest
npm install -g eslint prettier

# 设置Git钩子
pre-commit install
```

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🆘 支持与反馈

### 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/your-org/TestCaseAutomation)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/TestCaseAutomation/issues)
- **功能建议**: [GitHub Discussions](https://github.com/your-org/TestCaseAutomation/discussions)
- **技术文档**: [项目Wiki](https://github.com/your-org/TestCaseAutomation/wiki)

### 🐛 问题报告

提交问题时请包含：
- 操作系统和版本
- Python和Node.js版本
- 错误日志和截图
- 复现步骤

### 💡 功能建议

欢迎提交功能建议和改进意见，请在Issues中使用相应的标签。

---

<div align="center">

**🎉 感谢使用测试用例生成平台！**

如果这个项目对您有帮助，请给我们一个 ⭐ Star！

</div>
