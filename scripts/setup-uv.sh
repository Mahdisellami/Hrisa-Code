#!/bin/bash
# Set up local development with uv (modern, fast Python package manager)

set -e

echo "⚡ Setting up development environment with uv..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"

    # Check again after install
    if ! command -v uv &> /dev/null; then
        echo "❌ Error: uv installation failed"
        echo "Please install manually: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

echo "✅ uv is installed: $(uv --version)"
echo ""

# Create virtual environment with uv
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with uv..."
    uv venv
else
    echo "✅ Virtual environment already exists"
fi

# Install dependencies with uv
echo "📥 Installing dependencies..."
uv pip install -e ".[dev]"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Activate environment:  source .venv/bin/activate"
echo "  2. Start Ollama:          ollama serve"
echo "  3. Pull a model:          ollama pull codellama"
echo "  4. Start chatting:        hrisa chat"
echo ""
echo "💡 uv tips:"
echo "  - Install package:        uv pip install <package>"
echo "  - Run command:            uv run hrisa chat"
echo "  - Update dependencies:    uv pip install -e '.[dev]' --upgrade"
