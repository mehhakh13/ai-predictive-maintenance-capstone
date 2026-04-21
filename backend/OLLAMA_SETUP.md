# Ollama Setup Guide - Free Local AI

This guide will help you set up Ollama to run Phase 2 chat **completely free** without any API keys or cloud services.

## What is Ollama?

Ollama lets you run large language models (like Llama, Mistral) **locally on your computer** for free. No API keys, no internet needed, no usage limits!

## Installation

### Linux (Ubuntu/Debian)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### macOS

```bash
# Download from website
# Visit: https://ollama.com/download

# Or use Homebrew
brew install ollama
```

### Windows

1. Download installer from: https://ollama.com/download
2. Run the installer
3. Open terminal and verify: `ollama --version`

## Getting Started

### 1. Start Ollama Service

```bash
# Start Ollama in the background
ollama serve
```

Leave this terminal running or run it in the background:
```bash
# Run as background service (Linux)
nohup ollama serve > /dev/null 2>&1 &

# Or use systemd (Linux)
sudo systemctl start ollama
```

### 2. Download a Model

Choose a model based on your hardware:

#### Recommended: Llama 3.1 8B (Needs ~8GB RAM)
```bash
ollama pull llama3.1:8b
```

#### Smaller: Phi-3 (Needs ~4GB RAM)
```bash
ollama pull phi3
```

#### Larger: Llama 3.1 70B (Needs ~48GB RAM)
```bash
ollama pull llama3.1:70b
```

#### Other Options:
```bash
ollama pull mistral        # Mistral 7B
ollama pull gemma:7b       # Google Gemma
ollama pull codellama      # Code-specialized
```

**Download takes 5-10 minutes depending on your internet speed.**

### 3. Test the Model

```bash
# Test chat
ollama run llama3.1:8b

# Try a question
>>> What are the benefits of predictive maintenance?
```

Press `Ctrl+D` to exit.

### 4. Configure Backend

The backend is already configured to use Ollama by default. No changes needed!

If you want to switch models, create a `.env` file:

```bash
cd backend
echo "OLLAMA_MODEL=llama3.1:8b" > .env
```

### 5. Start the Backend

```bash
cd backend
python3 main.py
```

You should see:
```
✓ Using Ollama (Local/Free)
✓ Ollama Service initialized with 12 tools
  Model: llama3.1:8b
  Base URL: http://localhost:11434
```

## Testing

### Quick Test

```bash
# In another terminal
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the most expensive systems?"}'
```

### Full Test Suite

```bash
python3 backend/test_chat_phase2.py
```

## Performance Comparison

| Model | Size | RAM Needed | Speed | Quality |
|-------|------|------------|-------|---------|
| phi3 | 2.3GB | 4GB | ⚡⚡⚡ Fast | ⭐⭐⭐ Good |
| llama3.1:8b | 4.7GB | 8GB | ⚡⚡ Medium | ⭐⭐⭐⭐ Great |
| mistral | 4.1GB | 8GB | ⚡⚡ Medium | ⭐⭐⭐⭐ Great |
| llama3.1:70b | 40GB | 48GB | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent |

**Recommendation:** Use `llama3.1:8b` for best balance of speed and quality.

## Troubleshooting

### "Cannot connect to Ollama"

**Problem:** Backend can't reach Ollama

**Solutions:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve

# Check firewall
sudo ufw allow 11434
```

### "Model not found"

**Problem:** Model not downloaded

**Solution:**
```bash
# List available models
ollama list

# Pull the model you need
ollama pull llama3.1:8b
```

### "Out of memory"

**Problem:** Not enough RAM for the model

**Solutions:**
1. Use a smaller model: `ollama pull phi3`
2. Close other applications
3. Upgrade RAM or use cloud VM

### Slow responses

**Solutions:**
1. Use a smaller model (phi3)
2. Use GPU acceleration (if you have NVIDIA GPU)
3. Reduce context length in config.py

### Model gives poor answers

**Solutions:**
1. Use a larger model: `llama3.1:70b`
2. Adjust temperature in `config.py`: `DEFAULT_TEMPERATURE = 0.3`
3. Try different model: `mistral` or `gemma`

## Switching Between Ollama and Claude

### Use Ollama (Free)
```bash
export USE_OLLAMA=true
python3 backend/main.py
```

### Use Claude API (Paid)
```bash
export USE_OLLAMA=false
export ANTHROPIC_API_KEY=your_key_here
python3 backend/main.py
```

Or in `.env` file:
```
USE_OLLAMA=false
ANTHROPIC_API_KEY=sk-ant-...
```

## Advanced Configuration

### Custom Ollama URL

If running Ollama on another machine:

```bash
export OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### GPU Acceleration (NVIDIA)

Ollama automatically uses GPU if available. Verify:

```bash
ollama run llama3.1:8b --verbose
```

Should show: "GPU: NVIDIA ..."

### Multiple Models

You can have multiple models and switch:

```bash
ollama pull llama3.1:8b
ollama pull mistral
ollama pull phi3

# Switch in .env
OLLAMA_MODEL=mistral
```

## Cost Comparison

| Backend | Setup Cost | Monthly Cost | Per Message |
|---------|-----------|--------------|-------------|
| **Ollama** | $0 | $0 | $0 |
| Claude API | $0 | Variable | ~$0.01 |
| OpenAI API | $0 | Variable | ~$0.02 |

Ollama = **100% FREE** 🎉

## Common Issues

### Port 11434 already in use

```bash
# Find process using port
lsof -i :11434

# Kill it
kill -9 <PID>

# Or change Ollama port
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

### Model download interrupted

```bash
# Resume download
ollama pull llama3.1:8b
```

### Want to remove models

```bash
# List models
ollama list

# Remove model
ollama rm llama3.1:8b
```

## Performance Tips

1. **Use SSD:** Models load faster from SSD
2. **Close browsers:** Free up RAM
3. **Use smaller context:** Reduce MAX_CONVERSATION_HISTORY
4. **Try different models:** Each has different strengths

## Recommended Setup

For most users:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start service
ollama serve &

# Download recommended model
ollama pull llama3.1:8b

# Test it
ollama run llama3.1:8b

# Start backend
cd backend
python3 main.py
```

Done! You now have a completely free AI assistant. 🚀

## Next Steps

1. Test the chatbox in your frontend
2. Try different models to find your favorite
3. Adjust temperature/settings for better responses
4. Deploy to production (Ollama can run on server too!)

## Resources

- Ollama Website: https://ollama.com
- Model Library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
- Discord: https://discord.gg/ollama

---

**Questions?** Check the troubleshooting section or open an issue!
