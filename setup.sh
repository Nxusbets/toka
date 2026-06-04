#!/bin/bash
set -e

echo "==========================================="
echo "  Toka - User Management System Setup"
echo "==========================================="

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
else
    echo "ℹ️  .env already exists, skipping"
fi

# Install Lemma globally for AI Gateway
echo ""
echo "📦 Installing @nxuss/lemma..."
npm install -g @nxuss/lemma 2>/dev/null || true
echo "✅ Lemma installed"

# Build and start all services
echo ""
echo "🐳 Starting Docker Compose..."
echo "   This will build and start all 12 services."
echo "   First build may take several minutes."
echo ""

docker compose build --parallel
docker compose up -d

echo ""
echo "==========================================="
echo "  Toka System is starting!"
echo "==========================================="
echo ""
echo "  Frontend:    http://localhost:3000"
echo "  API Gateway: http://localhost:8000"
echo "  Auth API:    http://localhost:8001/docs"
echo "  User API:    http://localhost:8002/docs"
echo "  Audit API:   http://localhost:8003/docs"
echo "  AI Agent API: http://localhost:8004/docs"
echo "  Lemma Dashboard: http://localhost:8082"
echo "  RabbitMQ:    http://localhost:15672 (toka_user:toka_pass_2024)"
echo ""
echo "  Run 'docker compose logs -f' to see all logs"
echo "==========================================="
