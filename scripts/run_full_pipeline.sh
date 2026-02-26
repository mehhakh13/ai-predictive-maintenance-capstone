#!/bin/bash

# Risk Heatmap Feature Pipeline - Full Execution Script
# This script runs all 4 phases in sequence

set -e  # Exit on error

echo "================================================================================"
echo "RISK HEATMAP FEATURE PIPELINE - FULL EXECUTION"
echo "================================================================================"
echo ""
echo "This script will run all 4 phases:"
echo "  Phase 1: Data Preparation & Classification"
echo "  Phase 2: Feature Engineering"
echo "  Phase 3: Model Training & Prediction"
echo "  Phase 4: Heatmap CSV Generation"
echo ""
echo "Estimated time: ~20 minutes"
echo ""
echo "================================================================================"
echo ""

# Check if FMUCD_USA.parquet exists
if [ ! -f "FMUCD_USA.parquet" ]; then
    echo "ERROR: FMUCD_USA.parquet not found in current directory"
    echo "Please ensure the file exists before running the pipeline"
    exit 1
fi

# Phase 1
echo ""
echo "================================================================================"
echo "PHASE 1: DATA PREPARATION & CLASSIFICATION"
echo "================================================================================"
echo ""
python scripts/prepare_asset_upm_data.py
if [ $? -ne 0 ]; then
    echo "ERROR: Phase 1 failed"
    exit 1
fi

# Phase 2
echo ""
echo "================================================================================"
echo "PHASE 2: FEATURE ENGINEERING"
echo "================================================================================"
echo ""
python scripts/engineer_asset_features.py
if [ $? -ne 0 ]; then
    echo "ERROR: Phase 2 failed"
    exit 1
fi

# Phase 3
echo ""
echo "================================================================================"
echo "PHASE 3: MODEL TRAINING & PREDICTION"
echo "================================================================================"
echo ""
python scripts/train_asset_upm_model.py
if [ $? -ne 0 ]; then
    echo "ERROR: Phase 3 failed"
    exit 1
fi

# Phase 4
echo ""
echo "================================================================================"
echo "PHASE 4: HEATMAP CSV GENERATION"
echo "================================================================================"
echo ""
python scripts/generate_heatmaps.py
if [ $? -ne 0 ]; then
    echo "ERROR: Phase 4 failed"
    exit 1
fi

# Final summary
echo ""
echo "================================================================================"
echo "PIPELINE EXECUTION COMPLETE!"
echo "================================================================================"
echo ""
echo "Generated outputs:"
echo ""
echo "Intermediate files:"
echo "  - data/processed/monthly_asset_upm.parquet"
echo "  - data/processed/asset_features.parquet"
echo "  - data/processed/predictions_with_metadata.parquet"
echo ""
echo "Model artifacts:"
echo "  - models/asset_upm_predictor.pkl"
echo "  - models/asset_feature_importance.csv"
echo "  - models/asset_feature_columns.txt"
echo "  - models/roc_curve.png"
echo "  - models/precision_recall_curve.png"
echo ""
echo "Dashboard outputs:"
echo "  - data/dashboard/ml_heatmap.csv"
echo "  - data/dashboard/historical_heatmap.csv"
echo ""
echo "================================================================================"
echo "Next steps:"
echo "  - Review model performance in Phase 3 output"
echo "  - Examine heatmap CSVs in data/dashboard/"
echo "  - Integrate CSVs with dashboard for visualization"
echo "================================================================================"
