#!/bin/bash
#
# Full Pipeline Execution Script
# Runs all 4 phases of the predictive maintenance risk heatmap pipeline
#
# Phase 1: Data Preparation & Classification (FMUCD.csv -> monthly_asset_upm.parquet)
# Phase 2: Feature Engineering (monthly_asset_upm.parquet -> asset_features.parquet)
# Phase 3: Model Training & Prediction (asset_features.parquet -> predictions + model)
# Phase 4: Heatmap Generation (predictions -> dashboard CSVs)
#

set -e  # Exit on error

echo "================================================================================"
echo "PREDICTIVE MAINTENANCE RISK HEATMAP - FULL PIPELINE"
echo "================================================================================"
echo ""
echo "This pipeline now uses:"
echo "  - SubsystemDescription (71 unique subsystems, more granular than 23 systems)"
echo "  - BuildingName (friendly names instead of just BuildingID)"
echo "  - ML-based risk prediction (XGBoost classifier)"
echo ""
echo "================================================================================"
echo ""

# Phase 1
echo "Starting Phase 1: Data Preparation & Classification..."
python3 scripts/prepare_asset_upm_data.py
if [ $? -eq 0 ]; then
    echo "✓ Phase 1 complete"
else
    echo "✗ Phase 1 failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo ""

# Phase 2
echo "Starting Phase 2: Feature Engineering..."
python3 scripts/engineer_asset_features.py
if [ $? -eq 0 ]; then
    echo "✓ Phase 2 complete"
else
    echo "✗ Phase 2 failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo ""

# Phase 3
echo "Starting Phase 3: Model Training & Prediction..."
python3 scripts/train_asset_upm_model.py
if [ $? -eq 0 ]; then
    echo "✓ Phase 3 complete"
else
    echo "✗ Phase 3 failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo ""

# Phase 4
echo "Starting Phase 4: Heatmap Generation..."
python3 scripts/generate_heatmaps.py
if [ $? -eq 0 ]; then
    echo "✓ Phase 4 complete"
else
    echo "✗ Phase 4 failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo "PIPELINE COMPLETE!"
echo "================================================================================"
echo ""
echo "Outputs:"
echo "  - data/processed/monthly_asset_upm.parquet (monthly aggregations)"
echo "  - data/processed/asset_features.parquet (engineered features)"
echo "  - data/processed/predictions_with_metadata.parquet (ML predictions)"
echo "  - models/asset_upm_predictor.pkl (trained XGBoost model)"
echo "  - data/dashboard/building_level_heatmap.csv (building-level heatmap)"
echo "  - data/dashboard/university_level_heatmap.csv (university-level heatmap)"
echo "  - data/dashboard/metadata.json (dropdown metadata)"
echo ""
echo "The heatmap now shows:"
echo "  - Subsystem-level granularity (not just system-level)"
echo "  - Building names (not just IDs)"
echo "  - ML-predicted risk (not just historical counts)"
echo ""
