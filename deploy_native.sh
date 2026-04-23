#!/bin/bash

echo "=== 开始轻量化网页部署 ==="

# 1. 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到 python3，请先安装 (sudo apt install python3)"
    exit 1
fi

# 2. 安装依赖
echo "正在安装极简依赖..."
pip3 install -r backend/requirements_minimal.txt

# 3. 设置生产环境变量
export PRODUCTION=true
export SKIP_RAG=true

# 4. 启动后端 (后台运行)
echo "正在启动后台服务 (端口 8000)..."
# 使用 nohup 保证退出终端后服务依然运行
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

echo "=== 部署完成！ ==="
echo "服务已在后台运行，端口: 8000"
echo "你可以通过 'tail -f server.log' 查看运行日志"
