FROM python:3.10-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=true
ENV SKIP_RAG=true

# 安装系统依赖（如 OCR 库可能需要的依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 过滤掉桌面版专用的 pywebview，并安装核心依赖
# 为了保持兼容性，我们先安装基础依赖，重型库通过环境变量 SKIP_RAG 跳过实际运行
RUN sed -i '/pywebview/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# 复制后端和前端代码
COPY backend /app/backend
COPY admin_frontend/dist /app/frontend

# 暴露端口
EXPOSE 8000

WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
