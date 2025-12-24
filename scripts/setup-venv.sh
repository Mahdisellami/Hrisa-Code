#!/bin/bash
# Set up local development with Python venv

set -e

echo "🐍 Setting up Python virtual environment..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate and install
echo "📥 Installing dependencies..."
source venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Activate environment:  source venv/bin/activate"
echo "  2. Start Ollama:          ollama serve"
echo "  3. Pull a model:          ollama pull codellama"
echo "  4. Start chatting:        hrisa chat"
echo ""
echo "To deactivate later:        deactivate"
