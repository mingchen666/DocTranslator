# 使用官方的 Python 3.11 镜像
FROM python:3.11-slim

# 设置工作目录为/app
WORKDIR /app

# 复制backend目录下的requirements.txt
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 将整个backend目录复制到容器内的/app
COPY . .

# 暴露端口（Flask 默认端口是 5000）
EXPOSE 5000

# 确保启动命令指向正确的app.py文件
CMD ["python", "app.py"]