#!/bin/bash

# Setup script for Self-Improving Coding Agent

echo "🤖 Setting up Self-Improving Coding Agent..."
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop."
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi
echo "✓ Docker is running"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Pull Docker image
echo "Pulling Python Docker image..."
docker pull python:3.11-slim
echo "✓ Docker image ready"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p workspace
mkdir -p chroma_db
echo "✓ Directories created"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please edit .env and add your API keys:"
    echo "  - OPENAI_API_KEY=your_key_here"
    echo "  - ANTHROPIC_API_KEY=your_key_here"
    echo ""
else
    echo "✓ .env file exists"
    echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "To start the agent:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Add your API keys to .env"
echo "  3. Run: streamlit run main.py"
echo ""
