#!/bin/bash
# Quick database access script for RestroBot

echo "=========================================="
echo "RestroBot Database Shell"
echo "=========================================="
echo ""
echo "Connecting to PostgreSQL database..."
echo ""

# Connect to the database
docker-compose exec db psql -U restrobot -d restrobot

echo ""
echo "Database session ended."
