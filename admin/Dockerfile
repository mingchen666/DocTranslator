# 使用官方的 Node.js 镜像作为构建环境
FROM node:20 AS build-stage

# 安装 pnpm
RUN npm install -g pnpm

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install

# 复制项目文件
COPY . .

# 复制 .env.production 文件
COPY .env.production .env.production

# 构建项目
RUN pnpm run build:prod
