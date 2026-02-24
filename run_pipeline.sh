#!/bin/bash
# Complete pipeline execution script for PredicX

echo "=========================================="
echo "PredicX - Predictive Maintenance Pipeline"
echo "=========================================="
echo ""

# Step 1: Feature Engineering
echo "[Step 1/3] Running Feature Engineering..."
python3 scripts/feature_engineering.py

if [ $? -ne 0 ]; then
    echo "❌ Feature engineering failed"
    exit 1
fi

echo "✓ Feature engineering complete"
echo ""

# Step 2: Model Training
echo "[Step 2/3] Training XGBoost Model..."
python3 scripts/train_model.py

if [ $? -ne 0 ]; then
    echo "❌ Model training failed"
    exit 1
fi

echo "✓ Model training complete"
echo ""

# Step 3: Launch Dashboard
echo "[Step 3/3] Launching Streamlit Dashboard..."
echo ""
echo "Dashboard will open at http://localhost:8501"
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run dashboard/app.py
