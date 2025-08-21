# 测试用例自动化平台 - 前端

基于 Vue3 + Element Plus 的现代化测试用例自动化生成平台前端应用。

## ✨ 特性

### 🚀 核心功能
- **多样化输入支持** - 支持图片、文档、API规范、数据库Schema、录屏等多种输入方式
- **智能测试用例生成** - 基于AI技术自动生成专业的测试用例
- **思维导图可视化** - 支持测试用例的思维导图展示和编辑
- **Excel导出** - 支持测试用例批量导出为Excel格式
- **实时进度监控** - 通过SSE协议实时显示生成进度
- **测试用例管理** - 完整的CRUD操作、分类、标签、优先级管理

### 🎨 设计特色
- **企业级UI设计** - 现代化、科技感的界面设计
- **响应式布局** - 适配各种屏幕尺寸
- **暗色主题支持** - 支持明暗主题切换
- **流畅动画效果** - 丰富的交互动画和过渡效果
- **玻璃态效果** - 现代化的视觉效果

## 🛠️ 技术栈

- **框架**: Vue 3 + TypeScript
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite
- **样式**: SCSS + CSS变量
- **图表**: ECharts + Vue-ECharts
- **HTTP客户端**: Axios
- **工具库**: Lodash-ES, Day.js
- **开发工具**: ESLint, Prettier

## 📁 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口定义
│   ├── components/        # 通用组件
│   │   ├── FileUpload/    # 文件上传组件
│   │   ├── ProgressMonitor/ # 进度监控组件
│   │   ├── TestCaseList/  # 测试用例列表组件
│   │   ├── MindmapRenderer/ # 思维导图渲染组件
│   │   └── ...
│   ├── layout/            # 布局组件
│   ├── router/            # 路由配置
│   ├── stores/            # 状态管理
│   ├── styles/            # 全局样式
│   ├── types/             # TypeScript类型定义
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   │   ├── dashboard/     # 仪表盘
│   │   ├── test-case/     # 测试用例相关页面
│   │   │   ├── generate/  # 用例生成页面
│   │   │   ├── management/ # 用例管理页面
│   │   │   └── mindmap/   # 思维导图页面
│   │   └── settings/      # 设置页面
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## 🚀 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 7.0.0 或 yarn >= 1.22.0

### 安装依赖
```bash
npm install
# 或
yarn install
```

### 开发环境运行
```bash
npm run dev
# 或
yarn dev
```

### 构建生产版本
```bash
npm run build
# 或
yarn build
```

### 代码检查和格式化
```bash
# ESLint检查
npm run lint

# Prettier格式化
npm run format
```

## 🔧 配置说明

### 环境变量
创建 `.env.local` 文件配置环境变量：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=测试用例自动化平台
```

### 代理配置
在 `vite.config.ts` 中配置开发服务器代理：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 📱 页面功能

### 仪表盘 (`/dashboard`)
- 测试用例统计概览
- 图表数据可视化
- 快速操作入口

### 测试用例生成 (`/test-case/generate`)
- 多种输入方式选择
- 智能配置参数
- 实时生成进度监控
- 结果预览和导出

### 测试用例管理 (`/test-case/management`)
- 测试用例列表展示
- 高级搜索和过滤
- 批量操作功能
- 详情查看和编辑

### 思维导图 (`/test-case/mindmap`)
- 交互式思维导图展示
- 多种布局和主题
- 节点编辑功能
- 导出多种格式

### 系统设置 (`/settings`)
- 个人偏好设置
- 外观主题配置
- 生成参数配置
- 导出选项设置

## 🎨 设计系统

### 颜色规范
```scss
// 主色调
--primary-color: #2563eb;
--accent-color: #06b6d4;

// 功能色
--success-color: #10b981;
--warning-color: #f59e0b;
--error-color: #ef4444;

// 中性色
--gray-50: #f8fafc;
--gray-900: #0f172a;
```

### 间距规范
```scss
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;
```

### 圆角规范
```scss
--border-radius: 8px;
--border-radius-lg: 12px;
```

## 🔌 API集成

### 请求拦截器
- 自动添加认证头
- 请求进度条显示
- 错误统一处理

### 响应拦截器
- 业务错误处理
- 状态码处理
- 消息提示

### SSE集成
- 实时进度监控
- 自动重连机制
- 事件类型处理

## 📦 组件库

### 通用组件
- `FileUpload` - 文件上传组件，支持多种文件类型
- `ProgressMonitor` - 进度监控组件，支持SSE实时更新
- `TestCaseList` - 测试用例列表组件，支持多种视图模式
- `MindmapRenderer` - 思维导图渲染组件
- `ExportDialog` - 导出对话框组件

### 业务组件
- `TestCaseDetailDialog` - 测试用例详情对话框
- `BatchEditDialog` - 批量编辑对话框

## 🚀 部署

### 构建优化
- 代码分割和懒加载
- 资源压缩和优化
- CDN资源配置

### 部署配置
支持部署到各种静态托管平台：
- Nginx
- Apache
- Vercel
- Netlify

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给它一个星标！
