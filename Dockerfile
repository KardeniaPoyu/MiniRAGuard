# ============================================================
# MiniRAGuard AI · Dockerfile
# 基础镜像：python:3.11-slim（Debian Bookworm）
# ============================================================

FROM python:3.11-slim

# ---------- 系统依赖 ----------
# libgomp1：torch / sentence-transformers 需要
# curl：健康检查用（可选）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------- 安装 Python 依赖 ----------
# 先只复制 requirements.txt，利用 Docker 层缓存加速重复构建
COPY requirements.txt .

# torch CPU-only version (pre-install to save space and ensure CPU-only build)
RUN pip install --no-cache-dir torch>=2.1.0 \
    --index-url https://download.pytorch.org/whl/cpu

# 其余依赖（跳过 torch 行，因已安装）
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 复制项目代码 ----------
# .dockerignore 中应排除：.env  .venv  __pycache__  vector_store  cache.db
COPY . .

# To build the vector index during container build:
# RUN python -c "from miniraguard.core.rag_tool import retrieve_legal_context; retrieve_legal_context('init', './examples/rent_assistant/data/vector_store')"

EXPOSE 8000

# ---------- 健康检查 ----------
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Run the Rental Assistant demo by default
CMD ["uvicorn", "examples.rent_assistant.backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2"]
