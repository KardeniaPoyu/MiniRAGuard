#!/bin/bash
# 数律智检 · 标准化一键部署脚本

echo "================================================================"
echo "🚀 正在启动 数律智检 混合架构部署 (Docker 版)"
echo "================================================================"

# 1. 检查环境变量
if [ ! -f .env ]; then
    echo "❌ 错误: 未找到 .env 配置文件！"
    echo "请运行 'bash scripts/setup_env.sh' 进行初始化。"
    exit 1
fi

# 2. 拉起容器服务
echo "📦 正在执行构建并冷启动容器服务..."
docker-compose down --remove-orphans
docker-compose up -d --build

# 3. 动态健康检查
echo "⏳ 正在等待后端服务就绪..."
MAX_RETRIES=15
COUNT=0
while [ $COUNT -lt $MAX_RETRIES ]; do
    # 显式尝试连接 8000 端口
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        echo "✅ 后端服务已就绪！"
        break
    fi
    echo "   ...等待中 ($((COUNT+1))/$MAX_RETRIES)"
    sleep 3
    COUNT=$((COUNT+1))
done

if [ $COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️ 警告: 服务启动超时，请运行 'docker-compose logs backend' 查看错误详情。"
else
    echo "================================================================"
    echo "🎉 部署成功！"
    echo "📍 管理后台 (Admin): http://localhost"
    echo "🏥 后端接口 (API):     http://localhost:8000/docs"
    echo "================================================================"
fi
