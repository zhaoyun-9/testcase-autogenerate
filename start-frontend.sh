#!/bin/bash

# 测试用例生成平台前端启动脚本

echo "🚀 启动测试用例生成平台前端..."

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js 18+"
    exit 1
fi

# 检查Node.js版本
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ 错误: Node.js版本过低，需要18+，当前版本: $(node -v)"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查是否存在package.json
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 未找到package.json文件"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    
    # 检查包管理器
    if command -v pnpm &> /dev/null; then
        echo "使用 pnpm 安装依赖..."
        pnpm install
    elif command -v yarn &> /dev/null; then
        echo "使用 yarn 安装依赖..."
        yarn install
    else
        echo "使用 npm 安装依赖..."
        npm install
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    
    echo "✅ 依赖安装完成"
fi

# 复制环境配置文件
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "📋 复制环境配置文件..."
    cp .env.example .env
    echo "✅ 环境配置文件已创建，可根据需要修改 .env 文件"
fi

# 启动开发服务器
echo "🌐 启动开发服务器..."
echo "前端地址: http://localhost:5173"
echo "后端API: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 检查包管理器并启动
if command -v pnpm &> /dev/null; then
    pnpm dev
elif command -v yarn &> /dev/null; then
    yarn dev
else
    npm run dev
fi
