"""
Configuration settings for the Predictive Maintenance Backend
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path("/home/sradmin/ai-predictive-maintenance-capstone")
DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

# Data file paths
PREDICTIONS_DATA_PATH = DATA_DIR / "predictions_with_metadata.parquet"
SYSTEM_MONTH_DATA_PATH = DATA_DIR / "system_month_data.csv"
FEATURE_IMPORTANCE_PATH = MODELS_DIR / "feature_importance.csv"
MODEL_PATH = MODELS_DIR / "xgboost_upm_predictor.pkl"

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"  # Can be changed to "mistral", "phi3", etc.
OLLAMA_TIMEOUT = 60  # seconds

# Chat settings
MAX_CONVERSATION_HISTORY = 10  # Keep last N messages
DEFAULT_TEMPERATURE = 0.1  # Low temperature for factual responses
MAX_TOKENS = 2000

# Cost estimation (since we don't have actual cost data)
COST_PER_UPM_EVENT = 500  # Estimated cost per UPM event in dollars

# API settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
