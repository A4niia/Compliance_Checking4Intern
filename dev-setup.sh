#!/bin/bash

if [ "$IS_DEVCONTAINER" = "True" ]; then
    echo "-- Correcting permissions..."
    sudo chown 1000:1000 .venv
    sudo chown 1000:1000 .python
    sudo chown 1000:1000 .uv_cache
fi

echo "-- Loading .env"
source .env

echo "-- Installing Python"
uv python install

echo "-- Installing dependencies"
uv sync

echo "-- Installing CLI"
${PROJECT_NAME} --install-completion

# NEW — Check Ollama installed on host
echo ""
echo "-- Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama already installed"
else
    echo "✗ Ollama not found"
    echo ""
    echo "Please install Ollama manually:"
    echo "  Windows/Mac: https://ollama.com/download"
    echo "  Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if Ollama is running
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "-- Starting Ollama..."
    ollama serve &
    sleep 3
    echo "✓ Ollama started"
fi

# Pull model
echo "-- Pulling mistral model (~4GB, first time only)..."
ollama pull mistral
echo "✓ Model ready"

echo ""
echo "================================================"
echo "Setup complete!"
echo "Run: uv run policy-checker --source ait --verbose"
echo "================================================"