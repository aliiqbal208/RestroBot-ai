#!/bin/bash

# Docker setup and run script for RestroBot

echo "========================================================================"
echo "RestroBot Docker Setup"
echo "========================================================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your OPENAI_API_KEY before proceeding."
    echo "Then run this script again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Build and start containers
echo "Building and starting containers..."
docker-compose up --build -d

echo ""
echo "Waiting for database to be ready..."
sleep 5

# Check if database is ready
until docker-compose exec -T db pg_isready -U restrobot > /dev/null 2>&1; do
    echo "Waiting for database..."
    sleep 2
done

echo "✓ Database is ready"
echo ""

echo "========================================================================"
echo "Setup Complete!"
echo "========================================================================"
echo ""
echo "To run RestroBot:"
echo "  docker-compose run --rm app"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop containers:"
echo "  docker-compose down"
echo ""
echo "To remove all data and start fresh:"
echo "  docker-compose down -v"
echo ""
