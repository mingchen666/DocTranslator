#!/bin/bash

# 设置脚本在遇到错误时立即退出
set -e

echo "=========================================="
echo "🚀 开始一键部署 DocTranslator"
echo "=========================================="

# 1. 检查并创建 Docker 网络
echo "📡 检查 Docker 网络..."
if ! docker network ls | grep -q my-network; then
  echo "   -> 创建网络 my-network..."
  docker network create my-network
else
  echo "   -> 网络 my-network 已存在，跳过创建。"
fi

# 2. 创建本地存储目录
echo "📁 创建本地存储目录..."
mkdir -p ./backend-storage

# 3. 停止并删除旧容器（如果存在，避免冲突）
echo "🧹 清理旧容器..."
docker stop backend-container 2>/dev/null || true
docker rm backend-container 2>/dev/null || true
docker stop nginx-container 2>/dev/null || true
docker rm nginx-container 2>/dev/null || true

# 4. 构建后端镜像
echo "🔨 构建后端 Docker 镜像..."
docker build -t doctranslator ./backend

# 5. 启动后端容器
echo "🌐 启动后端容器..."
docker run -d \
  --name backend-container \
  --network my-network \
  -p 5000:5000 \
  -p 5001:5001 \
  -v ./backend-storage:/app/storage \
  doctranslator

# 6. 启动 Nginx 容器
echo "🌍 启动 Nginx 容器..."
docker run -d \
  --name nginx-container \
  -p 1475:80 \
  -p 8081:8081 \
  -v $(pwd)/nginx/nginx.conf:/etc/nginx/conf.d/default.conf \
  -v $(pwd)/frontend/dist:/usr/share/nginx/html/frontend \
  -v $(pwd)/admin/dist:/usr/share/nginx/html/admin \
  --network my-network \
  nginx:stable-alpine

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "前端地址: http://localhost:1475"
echo "管理端地址: http://localhost:8081"
echo "后端 API: http://localhost:5000"
echo "=========================================="
echo ""
echo "📌 提示："
echo "   - 首次部署请使用此脚本。"
echo "   - 日常更新请使用 './update.sh' 脚本。"
