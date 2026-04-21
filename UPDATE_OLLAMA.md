# Update Ollama to Latest Version

Your Ollama is outdated (v0.1.26). You need v0.21.0+ for llama3.1:8b.

## Quick Fix

Run these commands:

```bash
# Update Ollama
curl -fsSL https://ollama.com/install.sh | sudo sh

# Verify new version
ollama --version

# Start/restart Ollama service
ollama serve &

# Now pull the model
ollama pull llama3.1:8b
```

## Alternative: Use Older Model

If you can't update, use an older model that works with v0.1.26:

```bash
# Try llama2 instead (works with older Ollama)
ollama pull llama2

# Update backend config
echo "OLLAMA_MODEL=llama2" >> backend/.env

# Then start the server
cd backend
python3 main.py
```

## Alternative: Use Smaller Model

```bash
# Phi-3 also works with older versions
ollama pull phi3

# Update backend config
echo "OLLAMA_MODEL=phi3" >> backend/.env

# Then start the server
cd backend
python3 main.py
```

## Recommended: Update Ollama

The best option is to update Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sudo sh
```

Then continue with the setup script:

```bash
cd backend
bash setup_ollama.sh
```
