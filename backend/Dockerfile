FROM python:3.11-bookworm

WORKDIR /app

RUN sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

COPY . .

EXPOSE 5000 5001

CMD ["sh", "-c", "python migrate_startup.py && python mcp_server.py & gunicorn --bind 0.0.0.0:5000 --workers 4 --preload --timeout 120 --access-logfile - app:app & wait"]
