#!/bin/bash

# RestroBot Quick Setup Script

echo "========================================================================"
echo "RestroBot Setup"
echo "========================================================================"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✓ .env file found"
    
    # Check if API key is set (handle both quoted and unquoted values)
    if grep -q 'OPENAI_API_KEY=.*sk-' .env; then
        echo "✓ OPENAI_API_KEY appears to be set"
    else
        echo "⚠ WARNING: OPENAI_API_KEY not properly set in .env file"
        echo ""
        echo "Please edit .env and add your OpenAI API key:"
        echo "  OPENAI_API_KEY=sk-your-actual-key-here"
        echo ""
        echo "Get your API key from: https://platform.openai.com/api-keys"
        exit 1
    fi
else
    echo "✗ .env file not found"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your OpenAI API key:"
    echo "  OPENAI_API_KEY=sk-your-actual-key-here"
    echo ""
    echo "Get your API key from: https://platform.openai.com/api-keys"
    exit 1
fi

echo ""
echo "========================================================================"
echo "Starting RestroBot..."
echo "========================================================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the bot
python3 main.py
