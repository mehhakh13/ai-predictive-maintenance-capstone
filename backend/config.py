"""
Configuration settings for the Predictive Maintenance Backend
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path("/home/sradmin/ai-predictive-maintenance-capstone")
DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

# Data file paths
PREDICTIONS_DATA_PATH = DATA_DIR / "predictions_with_metadata.parquet"
SYSTEM_MONTH_DATA_PATH = DATA_DIR / "system_month_data.csv"
FEATURE_IMPORTANCE_PATH = MODELS_DIR / "feature_importance.csv"
MODEL_PATH = MODELS_DIR / "xgboost_upm_predictor.pkl"

# LLM Backend Selection (Phase 2)
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"  # Default: Use Ollama (free)

# Ollama settings (Local/Free)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")  # Using phi3 (already downloaded)
OLLAMA_TIMEOUT = 180  # seconds (increased for CPU-only mode - allows time for tool execution)

# Claude API settings (Paid - optional)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Claude Sonnet 4 (working model)

# Chat settings
MAX_CONVERSATION_HISTORY = 10  # Keep last N messages
DEFAULT_TEMPERATURE = 0.1  # Low temperature for factual responses
MAX_TOKENS = 4000  # Increased for Phase 2

# Cost estimation (since we don't have actual cost data)
COST_PER_UPM_EVENT = 500  # Estimated cost per UPM event in dollars

# API settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]
