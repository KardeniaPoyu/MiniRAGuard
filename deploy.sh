#!/bin/bash
# Qingju One-Click Deployment Script

echo "🚀 Starting Qingju Deployment..."

# Ensure .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Run 'bash scripts/setup_env.sh' first and configure your keys."
    exit 1
fi

# Build and start services
echo "📦 Building and starting containers..."
docker-compose down
docker-compose up -d --build

echo "✅ Deployment complete!"
echo "📍 Backend/Admin available at: http://localhost (or your server IP)"
echo "🏥 Health check: http://localhost/health"
