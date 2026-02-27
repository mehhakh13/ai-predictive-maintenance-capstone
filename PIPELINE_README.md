# Risk Heatmap Feature Pipeline

A comprehensive predictive maintenance pipeline that estimates monthly asset-driven UPM risk by system, separating shock vs asset failures, and outputs dashboard-ready heatmap CSVs.

## Overview

This pipeline processes 3.3M work orders from FMUCD_USA.parquet (spanning Sept 2002 - May 2021) to:
1. Classify UPM events into shock/asset/unknown categories
2. Predict asset-driven UPM probability using machine learning
3. Generate comprehensive risk heatmaps for dashboard visualization

## Quick Start

### Run Full Pipeline

```bash
./scripts/run_full_pipeline.sh
```

This executes all 4 phases in sequence (~20 minutes total).

### Run Individual Phases

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

## Pipeline Architecture

### Phase 1: Data Preparation & Classification
**Script**: `scripts/prepare_asset_upm_data.py`

**What it does**:
- Loads FMUCD_USA.parquet (3.3M work orders)
- Classifies UPM events into **shock** (external/sudden) vs **asset** (internal degradation) vs **unknown**
- Creates monthly aggregations by (University, Building, System)
- Generates smart monthly grids (only for each entity's active period)
- Zero-fills missing months within active periods

**Classification Strategy**:
- **Shock keywords**: damage, broken, vandal, storm, freeze, etc.
- **Asset keywords**: wear, corroded, leak, clog, fail, deteriorate, etc.
- **Contextual patterns**: "water leak", "broken door", etc. (higher confidence)
- **Expected**: 70-80% classified as "unknown" (acceptable - model learns patterns)

**Output**: `data/processed/monthly_asset_upm.parquet` (~500K rows)

**Key columns**:
- Entity: UniversityID, BuildingID, SystemDescription
- Time: year, month, month_date
- Events: UPM_total_event, UPM_asset_event, UPM_shock_event
- Context: BuiltYear, Size, Type, FCI, DMC, CRV (building)
- Weather: MinTemp, MaxTemp, Humidity, Precipitation, Snow (monthly)
- WO: WOPriority, WODuration (monthly avg)

---

### Phase 2: Feature Engineering
**Script**: `scripts/engineer_asset_features.py`

**What it does**:
- Creates lag features for temporal patterns (CRITICAL for ML)
- Adds cyclical temporal encoding (month_sin, month_cos)
- Creates derived features (building_age, avg_temp, temp_range)
- One-hot encodes top 15 systems
- Creates binary target: `target_asset_upm = (UPM_asset_event > 0)`

**Lag Features** (most important for prediction):
- `asset_upm_last_1m`: Previous month's asset UPM count
- `asset_upm_last_3m`: Sum of last 3 months (excluding current)
- `asset_upm_last_6m`: Sum of last 6 months (excluding current)
- `months_since_asset_upm`: Months since last asset UPM (999 if never)

**Temporal Features**:
- `month_sin`, `month_cos`: Cyclical encoding (captures seasonality)
- `season`: 0=Winter, 1=Spring, 2=Summer, 3=Fall

**Output**: `data/processed/asset_features.parquet` (~500K rows, ~40 features)

---

### Phase 3: Model Training & Prediction
**Script**: `scripts/train_asset_upm_model.py`

**What it does**:
- Trains XGBoost classifier to predict asset-driven UPM probability
- Uses time-based train/test split (80/20 by month rank)
- Handles class imbalance with `scale_pos_weight`
- Evaluates on test set (target ROC-AUC >0.70)
- Generates predictions on ALL data

**Model Details**:
- **Algorithm**: XGBoost Classifier
- **Target**: Binary (1 if asset UPM occurred, 0 otherwise)
- **Train**: First 80% of months (2002-2017)
- **Test**: Last 20% of months (2017-2021)
- **Hyperparameters**:
  - max_depth: 6
  - learning_rate: 0.05
  - n_estimators: 300
  - scale_pos_weight: auto (handles imbalance)

**Output**:
- `models/asset_upm_predictor.pkl` (trained model)
- `models/asset_feature_importance.csv` (feature rankings)
- `models/asset_feature_columns.txt` (feature list)
- `models/roc_curve.png` (ROC curve plot)
- `models/precision_recall_curve.png` (PR curve plot)
- `data/processed/predictions_with_metadata.parquet` (with `risk_prob_asset` column)

**Expected Performance**:
- ROC-AUC >0.70 (good predictive power)
- Lag features should rank in top 10 importance

---

### Phase 4: Heatmap CSV Generation
**Script**: `scripts/generate_heatmaps.py`

**What it does**:
- Aggregates ML predictions by (System, Month)
- Aggregates historical events by (System, Month)
- Filters for reliability (coverage ≥10 entities)
- Outputs dashboard-ready CSV files

**Outputs**:

#### ML Heatmap (`data/dashboard/ml_heatmap.csv`):
```csv
SystemDescription,MonthNum,ml_risk,coverage
HVAC,1,0.45,150
HVAC,2,0.52,148
Electrical,1,0.38,120
...
```
- `ml_risk`: Mean predicted risk (0-1) across all entities
- `coverage`: Number of entities for this system-month combination
- **Use case**: Future risk prediction, proactive planning

#### Historical Heatmap (`data/dashboard/historical_heatmap.csv`):
```csv
SystemDescription,MonthNum,hist_total_rate,hist_asset_rate,hist_shock_rate,coverage
HVAC,1,0.12,0.08,0.04,500
HVAC,2,0.15,0.10,0.05,498
...
```
- `hist_*_rate`: Events per entity (event_count / coverage)
- **Use case**: Historical benchmarking, trend analysis

---

## File Structure

```
.
├── FMUCD_USA.parquet                          # Input data (3.3M rows)
│
├── scripts/
│   ├── prepare_asset_upm_data.py              # Phase 1
│   ├── engineer_asset_features.py             # Phase 2
│   ├── train_asset_upm_model.py               # Phase 3
│   ├── generate_heatmaps.py                   # Phase 4
│   └── run_full_pipeline.sh                   # Full pipeline runner
│
├── data/
│   ├── processed/
│   │   ├── monthly_asset_upm.parquet          # After Phase 1 (~500K rows)
│   │   ├── asset_features.parquet             # After Phase 2 (~500K rows, ~40 features)
│   │   └── predictions_with_metadata.parquet  # After Phase 3 (with risk_prob_asset)
│   │
│   └── dashboard/
│       ├── ml_heatmap.csv                     # ML risk predictions (final output)
│       └── historical_heatmap.csv             # Historical rates (final output)
│
├── models/
│   ├── asset_upm_predictor.pkl                # Trained XGBoost model
│   ├── asset_feature_importance.csv           # Feature rankings
│   ├── asset_feature_columns.txt              # Feature list
│   ├── roc_curve.png                          # ROC curve visualization
│   └── precision_recall_curve.png             # PR curve visualization
│
└── PIPELINE_README.md                         # This file
```

## Key Differences from Existing Pipeline

| Aspect | Existing Pipeline | New Pipeline |
|--------|-------------------|--------------|
| **Data Source** | Supabase | Parquet file (FMUCD_USA.parquet) |
| **Classification** | Binary UPM vs PPM | Shock vs Asset UPM |
| **Prediction Target** | All UPM | Asset UPM only |
| **Monthly Grid** | No zero-filling | Complete grid with smart generation |
| **Output Format** | Streamlit dashboard | CSV files for dashboard consumption |
| **Time Coverage** | Limited | Full 227-month history (2002-2021) |

## Validation Checkpoints

### After Phase 1:
- ✓ UPM classification: ~20% shock/asset, ~80% unknown
- ✓ Event counts preserved before/after aggregation
- ✓ Complete monthly grids for each entity's active period
- ✓ No unexpected nulls in critical columns

### After Phase 2:
- ✓ Lag features verified with spot checks
- ✓ No NaNs in final feature matrix
- ✓ Target distribution: 10-20% positive (reasonable imbalance)
- ✓ Feature count: ~40 features

### After Phase 3:
- ✓ ROC-AUC >0.70 on test set
- ✓ Train-Test gap <0.10 (not overfitting)
- ✓ Lag features in top 10 importance
- ✓ Predictions distributed across 0-1 range

### After Phase 4:
- ✓ CSV schema matches specification
- ✓ Risk scores in 0-1 range
- ✓ Coverage ≥10 for all rows
- ✓ HVAC risk higher in winter than summer (sanity check)

## Usage Tips

### Running Specific Phases

If you need to re-run only part of the pipeline:

```bash
# Re-run feature engineering only (if you modify lag logic)
python scripts/engineer_asset_features.py

# Re-run model training with different hyperparameters
python scripts/train_asset_upm_model.py

# Re-generate heatmaps with different coverage threshold
# (modify min_coverage in generate_heatmaps.py)
python scripts/generate_heatmaps.py
```

### Debugging

Each script prints detailed progress and validation checks. Look for:
- ✓ (checkmark) = validation passed
- ⚠ (warning) = unexpected behavior (may be OK, investigate)
- ERROR = critical failure

### Performance Optimization

If pipeline is slow:
- **Phase 1**: Most time in classification (can parallelize)
- **Phase 3**: Training time scales with n_estimators (reduce from 300 to 100 for testing)

## Expected Outputs

### Console Output

Each phase prints:
1. Progress indicators (e.g., [1/6], [2/6], ...)
2. Data statistics (row counts, distributions, etc.)
3. Validation checks with ✓/⚠/ERROR indicators
4. Summary statistics

### Files Generated

**Intermediate** (can be deleted after pipeline completes):
- `data/processed/monthly_asset_upm.parquet`
- `data/processed/asset_features.parquet`
- `data/processed/predictions_with_metadata.parquet`

**Final outputs** (keep these):
- `data/dashboard/ml_heatmap.csv` ← Use in dashboard
- `data/dashboard/historical_heatmap.csv` ← Use in dashboard
- `models/asset_upm_predictor.pkl` ← Use for future predictions
- `models/asset_feature_importance.csv` ← Understand model behavior

## Troubleshooting

### Common Issues

**Issue**: "FMUCD_USA.parquet not found"
- **Solution**: Ensure file exists in project root directory

**Issue**: "Memory error during classification"
- **Solution**: Process in chunks (modify prepare_asset_upm_data.py)

**Issue**: "ROC-AUC <0.70"
- **Solution**:
  - Check feature engineering (lag features correct?)
  - Try different hyperparameters (increase n_estimators, adjust max_depth)
  - Inspect feature importance (are lag features ranking high?)

**Issue**: "Empty heatmap CSV"
- **Solution**: Lower min_coverage threshold (default 10, try 5)

## Next Steps

After running the pipeline:

1. **Review model performance**:
   - Check `models/roc_curve.png` and `precision_recall_curve.png`
   - Review `models/asset_feature_importance.csv` (lag features should rank high)

2. **Examine heatmap CSVs**:
   - Open `data/dashboard/ml_heatmap.csv` in Excel/pandas
   - Validate: HVAC higher risk in winter? Electrical systems stable year-round?

3. **Integrate with dashboard**:
   - Load CSVs into dashboard visualization tool
   - Create heatmaps by System (rows) x Month (columns)
   - Color-code by risk level (green=low, red=high)

4. **Iterate if needed**:
   - Adjust classification keywords (in Phase 1)
   - Add more features (in Phase 2)
   - Tune hyperparameters (in Phase 3)
   - Change coverage thresholds (in Phase 4)

## Dependencies

All required packages in `requirements.txt`:
- pandas (data manipulation)
- numpy (numerical operations)
- xgboost (gradient boosting)
- scikit-learn (ML utilities, metrics)
- joblib (model serialization)
- pyarrow (parquet I/O)
- matplotlib (plotting)

Install with:
```bash
pip install -r requirements.txt
```

## Performance Metrics

**Execution time** (approximate):
- Phase 1: ~5 minutes (classification is compute-intensive)
- Phase 2: ~3 minutes (lag features on ~500K rows)
- Phase 3: ~10 minutes (XGBoost training)
- Phase 4: ~1 minute (aggregation)
- **Total**: ~20 minutes end-to-end

**Data sizes**:
- Input: 89 MB (FMUCD_USA.parquet)
- Intermediate: ~50 MB (monthly_asset_upm.parquet)
- Intermediate: ~60 MB (asset_features.parquet)
- Intermediate: ~60 MB (predictions_with_metadata.parquet)
- Output CSVs: <1 MB each (ml_heatmap.csv, historical_heatmap.csv)

## Contact & Support

For issues or questions about this pipeline, refer to:
- Pipeline plan document (detailed methodology)
- Code comments in each script (inline documentation)
- Validation checkpoints (debugging guidance)
