#!/bin/bash
# Automated Ollama Setup Script for Phase 2 Chatbot

set -e  # Exit on error

echo "============================================================"
echo "  Phase 2 Chatbot - Ollama Setup (FREE)"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if Ollama is installed
echo "Step 1: Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is installed"
    ollama --version
else
    print_error "Ollama is not installed"
    echo ""
    echo "Install Ollama:"
    echo "  Linux/Mac: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Windows: Download from https://ollama.com/download"
    echo ""
    exit 1
fi

# Check if Ollama service is running
echo ""
echo "Step 2: Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_success "Ollama service is running"
else
    print_error "Ollama service is not running"
    echo ""
    print_info "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3

    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama service started"
    else
        print_error "Failed to start Ollama service"
        echo "Try manually: ollama serve"
        exit 1
    fi
fi

# Check if model is available
echo ""
echo "Step 3: Checking for AI models..."
MODEL="llama3.1:8b"

if ollama list | grep -q "$MODEL"; then
    print_success "Model '$MODEL' is available"
else
    print_info "Model '$MODEL' not found. Downloading... (this may take 5-10 minutes)"
    echo ""

    if ollama pull "$MODEL"; then
        print_success "Model downloaded successfully"
    else
        print_error "Failed to download model"
        echo ""
        echo "Try manually: ollama pull $MODEL"
        echo "Or choose a smaller model: ollama pull phi3"
        exit 1
    fi
fi

# Test the model
echo ""
echo "Step 4: Testing model..."
TEST_RESPONSE=$(curl -s http://localhost:11434/api/generate \
  -d '{"model": "'"$MODEL"'", "prompt": "Say hello", "stream": false}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('response', ''))" 2>/dev/null || echo "")

if [ -n "$TEST_RESPONSE" ]; then
    print_success "Model is working"
else
    print_error "Model test failed"
    echo "Try: ollama run $MODEL"
    exit 1
fi

# Check Python dependencies
echo ""
echo "Step 5: Checking Python dependencies..."

if python3 -c "import fastapi, uvicorn, pandas" 2>/dev/null; then
    print_success "Python dependencies installed"
else
    print_info "Installing Python dependencies..."
    pip3 install -r ../requirements.txt
    print_success "Dependencies installed"
fi

# Create .env file if it doesn't exist
echo ""
echo "Step 6: Configuring backend..."

if [ ! -f .env ]; then
    cat > .env <<EOF
# Use Ollama (free, local)
USE_OLLAMA=true

# Ollama settings
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
EOF
    print_success "Created .env configuration file"
else
    print_success ".env file already exists"
fi

# Verify data files
echo ""
echo "Step 7: Checking data files..."

if [ -f "../data/processed/predictions_with_metadata.parquet" ]; then
    print_success "Data files found"
else
    print_error "Data files not found"
    echo "Make sure predictions_with_metadata.parquet exists in data/processed/"
    exit 1
fi

# Summary
echo ""
echo "============================================================"
echo "  Setup Complete! 🎉"
echo "============================================================"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  python3 main.py"
echo ""
echo "To test the chat:"
echo "  curl -X POST http://localhost:8000/api/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"What are the most expensive systems?\"}'"
echo ""
echo "Or run tests:"
echo "  python3 backend/test_chat_phase2.py"
echo ""
echo "Available models:"
ollama list
echo ""
echo "To switch models, edit backend/.env:"
echo "  OLLAMA_MODEL=phi3          # Smaller/faster"
echo "  OLLAMA_MODEL=llama3.1:8b   # Recommended"
echo "  OLLAMA_MODEL=mistral       # Alternative"
echo ""
print_success "Everything is ready!"
echo ""
