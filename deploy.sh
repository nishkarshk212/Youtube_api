#!/bin/bash

# YouTube Music API Deployment Script

echo "🚀 Deploying YouTube Music API..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before deploying."
    exit 1
fi

# Build and start containers
echo "🔨 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Deployment complete!"
echo "📊 API Dashboard: http://localhost"
echo "📚 API Documentation: http://localhost/docs"
echo "🔍 Health Check: http://localhost/api/health"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"
