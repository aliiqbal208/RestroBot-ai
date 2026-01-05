#!/bin/bash
# Start RestroBot - AI Web Application

echo "=========================================="
echo " 🍽️  RestroBot - AI"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo ""
fi

# Start database and API
echo "Starting database and API server..."
docker-compose -f docker-compose-web.yml up -d db api

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check API health
echo "Checking API health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ API is running"
else
    echo "⚠️  API might still be starting... checking logs:"
    docker-compose -f docker-compose-web.yml logs api | tail -n 20
fi

echo ""
echo "=========================================="
echo "Services Started!"
echo "=========================================="
echo ""
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "To start the frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose-web.yml down"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose-web.yml logs -f"
echo ""
echo "=========================================="
