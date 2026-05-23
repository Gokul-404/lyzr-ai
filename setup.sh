#!/bin/bash
# GitAgent Interviewer Setup Script

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         GitAgent Interviewer Setup & Installation             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo "✓ Virtual environment activated (Windows)"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Setup .env
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠ IMPORTANT: Edit .env and add your credentials:"
    echo "  - GITHUB_TOKEN (from https://github.com/settings/tokens)"
    echo "  - ANTHROPIC_API_KEY (optional)"
else
    echo "✓ .env already exists"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   Setup Complete!                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your GITHUB_TOKEN:"
echo "   nano .env"
echo ""
echo "2. Run the quick start check:"
echo "   python quickstart.py"
echo ""
echo "3. Try the demo:"
echo "   python demo.py"
echo ""
echo "4. Run an interview:"
echo "   python main.py <github_username>"
echo ""
