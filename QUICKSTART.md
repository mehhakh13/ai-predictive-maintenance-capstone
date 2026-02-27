# Risk Heatmap Pipeline - Quick Start Guide

## Prerequisites

Ensure you have:
1. `FMUCD_USA.parquet` file in the project root directory ✓
2. Python 3.10+ installed
3. Required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

## Run the Full Pipeline

### Option 1: One Command (Recommended)

```bash
./scripts/run_full_pipeline.sh
```

This runs all 4 phases sequentially (~20 minutes total).

### Option 2: Run Phases Individually

```bash
# Phase 1: Data Preparation & Classification (~5 min)
python scripts/prepare_asset_upm_data.py

# Phase 2: Feature Engineering (~3 min)
python scripts/engineer_asset_features.py

# Phase 3: Model Training & Prediction (~10 min)
python scripts/train_asset_upm_model.py

# Phase 4: Heatmap CSV Generation (~1 min)
python scripts/generate_heatmaps.py
```

## Expected Outputs

After successful execution, you'll have:

### Dashboard Files (Main Outputs)
```
data/dashboard/
├── ml_heatmap.csv              ← ML risk predictions
└── historical_heatmap.csv       ← Historical rates
```

### Model Files
```
models/
├── asset_upm_predictor.pkl              ← Trained model
├── asset_feature_importance.csv         ← Feature rankings
├── asset_feature_columns.txt            ← Feature list
├── roc_curve.png                        ← ROC curve
└── precision_recall_curve.png           ← PR curve
```

### Intermediate Files (Can be deleted after pipeline completes)
```
data/processed/
├── monthly_asset_upm.parquet
├── asset_features.parquet
└── predictions_with_metadata.parquet
```

## What Each Output Contains

### ml_heatmap.csv
**Columns**: SystemDescription, MonthNum, ml_risk, coverage

ML-based risk predictions aggregated by system and month.
- `ml_risk`: 0-1 probability of asset UPM event
- `coverage`: Number of entities (≥10 for reliability)

**Use case**: Future risk forecasting, resource allocation

### historical_heatmap.csv
**Columns**: SystemDescription, MonthNum, hist_total_rate, hist_asset_rate, hist_shock_rate, coverage

Historical event rates by system and month.
- `hist_*_rate`: Events per entity
- Separate rates for total/asset/shock UPM

**Use case**: Historical benchmarking, trend analysis

## Validation Checklist

After running, verify:

- [ ] Phase 1 completed successfully (check console for "PHASE 1 COMPLETE!")
- [ ] Phase 2 completed successfully (check console for "PHASE 2 COMPLETE!")
- [ ] Phase 3 completed successfully (check console for "PHASE 3 COMPLETE!")
  - [ ] Test ROC-AUC >0.70 (good model performance)
  - [ ] Train-Test gap <0.10 (not overfitting)
- [ ] Phase 4 completed successfully (check console for "PHASE 4 COMPLETE!")
- [ ] Output files exist:
  - [ ] `data/dashboard/ml_heatmap.csv`
  - [ ] `data/dashboard/historical_heatmap.csv`
  - [ ] `models/asset_upm_predictor.pkl`

## Troubleshooting

### "File not found: FMUCD_USA.parquet"
**Solution**: Ensure the file is in the project root directory (not in `data/` folder)

### "Memory error"
**Solution**:
- Close other applications
- Process runs fine on systems with 8GB+ RAM
- For low-memory systems, add chunking (modify Phase 1 script)

### "ROC-AUC <0.70"
**Possible causes**:
1. Data issues (check Phase 1 output for classification quality)
2. Feature engineering issues (check Phase 2 lag features)
3. Model hyperparameters (try increasing `n_estimators` to 500 in Phase 3)

**Solution**: Review console output for each phase, check validation results

### "Empty heatmap CSV"
**Solution**: Lower `min_coverage` threshold in `scripts/generate_heatmaps.py`:
```python
# Change line ~50 and ~80 from:
ml_heatmap = create_ml_heatmap(df, min_coverage=10)
# To:
ml_heatmap = create_ml_heatmap(df, min_coverage=5)
```

## Next Steps

After successful pipeline execution:

1. **Review Model Performance**
   ```bash
   # View ROC curve
   open models/roc_curve.png  # macOS
   xdg-open models/roc_curve.png  # Linux

   # Check feature importance
   cat models/asset_feature_importance.csv | head -20
   ```

2. **Examine Heatmap Data**
   ```bash
   # Preview ML heatmap
   head -20 data/dashboard/ml_heatmap.csv

   # Preview historical heatmap
   head -20 data/dashboard/historical_heatmap.csv
   ```

3. **Integrate with Dashboard**
   - Load CSVs into your visualization tool (Tableau, Power BI, Streamlit, etc.)
   - Create heatmap: Systems (rows) × Months (columns)
   - Color-code by risk level

4. **Iterate if Needed**
   - Modify classification keywords (Phase 1)
   - Add custom features (Phase 2)
   - Tune hyperparameters (Phase 3)
   - Adjust coverage thresholds (Phase 4)

## Key Insights to Look For

When reviewing outputs, check:

1. **Seasonal Patterns**: HVAC systems should show higher risk in winter/summer
2. **System Rankings**: Which systems have highest average risk?
3. **Model Features**: Which lag features are most important?
4. **Shock vs Asset**: What % of UPM events are asset-driven (predictable)?

## Documentation

For detailed methodology and implementation details, see:
- `PIPELINE_README.md` - Comprehensive pipeline documentation
- Code comments in each script - Implementation details

## Support

For issues or questions:
1. Check console output for error messages
2. Review validation checkpoints in PIPELINE_README.md
3. Examine intermediate outputs to identify failure point
