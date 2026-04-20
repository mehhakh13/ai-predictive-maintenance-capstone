# Implementation Notes - Risk Heatmap Upgrade

## Date: 2026-03-07

---

## Changes Made

### 1. Data Source Migration
- **From:** `FMUCD_USA.parquet` (89 MB, pre-filtered, no BuildingName/SubsystemDescription)
- **To:** `FMUCD.csv` (1.4 GB, full dataset, includes BuildingName/SubsystemDescription)

### 2. Granularity Upgrade
- **From:** System-level (23 unique systems)
- **To:** Subsystem-level (71 unique subsystems)
- **Impact:** 3x more detailed risk predictions

### 3. Building Name Support
- **Added:** BuildingName column to all pipeline outputs
- **Handling:** Nulls (49.5% of data) filled with "Building [ID]" placeholder
- **Implementation:** BuildingName stored as metadata, not part of entity key

### 4. Data Processing Improvements

#### Issue 1: Null BuildingNames (49.5% of data)
**Problem:** Grouping by BuildingName caused 74% data loss

**Solution:**
- Group by `BuildingID` (always present), not `BuildingName`
- Extract `BuildingName` as aggregated field (take first non-null value)
- Fill remaining nulls with placeholder

#### Issue 2: String-Type Numeric Columns
**Problem:** CSV columns stored as strings ("1.0" instead of 1.0)

**Solution:**
- Added explicit type conversion for 12 numeric columns
- Uses `pd.to_numeric(errors='coerce')` to handle non-numeric values

---

## File Changes

### Phase 1: `scripts/prepare_asset_upm_data.py`

**Key Changes:**
1. Load `FMUCD.csv` instead of `FMUCD_USA.parquet`
2. Convert numeric columns to proper types
3. Group by `[UniversityID, BuildingID, SubsystemDescription]` (not BuildingName)
4. Add `BuildingName` as aggregated metadata field
5. Fill null BuildingNames with `"Building [ID]"` placeholder

**Entity Columns:**
```python
# Before
entity_cols = ['UniversityID', 'BuildingID', 'SystemDescription', ...]

# After
entity_cols = ['UniversityID', 'BuildingID', 'SubsystemDescription', ...]
# Note: BuildingName is metadata, added via aggregation
```

### Phase 2: `scripts/engineer_asset_features.py`

**Key Changes:**
1. Update entity columns to use `SubsystemDescription`
2. Remove `BuildingName` from entity key (it's just metadata)
3. One-hot encode subsystems instead of systems
4. Increase from top 15 systems → top 20 subsystems

**Function Renamed:**
```python
# Before
encode_systems(df, top_n=15)

# After
encode_subsystems(df, top_n=20)
```

### Phase 3: `scripts/train_asset_upm_model.py`

**Key Changes:**
1. Exclude `SubsystemDescription` and `BuildingName` from features
2. Update excluded columns list

**Excluded Columns:**
```python
exclude_cols = [
    'UniversityID', 'BuildingID', 'BuildingName',  # Entity IDs
    'SystemDescription', 'SubsystemDescription',   # System/subsystem names
    'year', 'month', 'month_date',                 # Time IDs
    'target_asset_upm', 'UPM_total_event',         # Targets
    'UPM_asset_event', 'UPM_shock_event',          # Event counts
    'subsystem_category', 'Type',                  # Intermediate columns
]
```

### Phase 4: `scripts/generate_heatmaps.py`

**Key Changes:**
1. Group by `SubsystemDescription` instead of `SystemDescription`
2. Include `BuildingName` in output CSVs
3. Add `building_names` mapping to metadata

**Building-Level CSV Schema:**
```python
[
    'UniversityID',        # University ID
    'BuildingID',          # Building ID
    'BuildingName',        # Building name (or "Building [ID]")
    'SubsystemDescription',# Subsystem name
    'MonthNum',            # Month (1-12)
    'ml_risk',             # ML-predicted risk (0-1)
    'hist_asset_rate',     # Historical asset failure rate
    'hist_shock_rate',     # Historical shock event rate
    'coverage'             # Number of data points
]
```

**Metadata JSON Structure:**
```json
{
  "universities": [10, 11, 12],
  "buildings_by_university": {
    "10": ["0470", "0230", "0152", ...],
    "11": [...],
    "12": [...]
  },
  "building_names": {
    "0470": "Engineering Hall",
    "0230": "Science Building",
    "0152": "Building 0152",  // Null name filled with placeholder
    ...
  }
}
```

---

## Data Quality Notes

### BuildingName Coverage
- **Present:** ~50.5% of rows have actual building names
- **Missing:** ~49.5% of rows have null BuildingName
- **Handling:** Filled with "Building [BuildingID]" placeholder

**Examples:**
- `"Engineering Hall"` (actual name from data)
- `"Building 0470"` (placeholder for null name)

### SubsystemDescription Coverage
- **Present:** ~100% of rows (only 4 nulls out of 1.9M rows)
- **Missing:** Negligible (<0.001%)

### Date Parsing
- **Valid dates:** 75.6% of rows after filtering to universities 10, 11, 12
- **Invalid dates:** 24.4% dropped (parse errors)
- **Impact:** Acceptable loss for data quality

---

## Expected Data Volumes

### Input Data (after filtering to universities 10, 11, 12)
- Total rows: ~1,985,000
- After date parsing: ~1,501,000 (75.6%)
- PPM events: ~965,000
- UPM events: ~515,000

### Phase 1 Output (`monthly_asset_upm.parquet`)
- Estimated rows: ~400,000-600,000
- Entity combinations: ~50,000-70,000 (UniversityID × BuildingID × SubsystemDescription)
- Average months per entity: ~6-10 months

### Phase 2 Output (`asset_features.parquet`)
- Same row count as Phase 1
- Additional columns: ~40-50 features (lag, temporal, derived, one-hot encoded)

### Phase 3 Output (`predictions_with_metadata.parquet`)
- Same row count as Phase 2
- New column: `risk_prob_asset` (0-1 probability)

### Phase 4 Output (Dashboard CSVs)
- **Building-level:** ~50,000-100,000 rows
  - ~1,400 buildings × 71 subsystems × 12 months (filtered by coverage ≥10)
- **University-level:** ~2,000-3,000 rows
  - 3 universities × 71 subsystems × 12 months (filtered by coverage ≥10)

---

## Pipeline Execution Time

Based on data volumes:

| Phase | Step | Estimated Time |
|-------|------|----------------|
| Phase 1 | Load CSV | 1-2 min |
| Phase 1 | Filter + classify | 3-5 min |
| Phase 1 | Aggregate + grid | 2-3 min |
| Phase 1 | **Total** | **6-10 min** |
| Phase 2 | Lag features | 1-2 min |
| Phase 2 | Encoding | 1-2 min |
| Phase 2 | **Total** | **2-4 min** |
| Phase 3 | Model training | 2-4 min |
| Phase 3 | Prediction | 1-2 min |
| Phase 3 | **Total** | **3-6 min** |
| Phase 4 | Aggregation | 1-2 min |
| Phase 4 | **Total** | **1-2 min** |
| **TOTAL** | | **12-22 min** |

---

## Validation Checks

The pipeline includes automated validation:

### Phase 1
- ✓ Event count preservation (UPM events before vs after)
- ✓ Grid completeness (all entities have complete monthly grids)
- ✓ Null checks in critical columns
- ✓ Event distribution (% rows with events)

### Phase 2
- ✓ Lag feature spot check (first entity, first 10 months)
- ✓ Feature count verification
- ✓ No NaNs in final dataset
- ✓ Target distribution (class balance)

### Phase 3
- ✓ Model performance (ROC-AUC > 0.70)
- ✓ Overfitting check (train-test gap < 0.10)
- ✓ Feature importance (lag features in top 10)
- ✓ Prediction distribution (risk scores in [0, 1])

### Phase 4
- ✓ Schema validation (expected columns present)
- ✓ Risk scores in [0, 1] range
- ✓ Coverage threshold (all rows have coverage ≥10)
- ✓ No NaNs in output CSVs
- ✓ University filter check (only 10, 11, 12)

---

## Known Limitations

1. **BuildingName Accuracy**
   - ~50% of buildings have actual names
   - ~50% use placeholder "Building [ID]"
   - No impact on predictions (BuildingName is metadata only)

2. **Data Sparsity at Subsystem Level**
   - Some subsystems have limited data (<10 entities)
   - Coverage filter (≥10) removes these for reliability
   - Results in some subsystems not appearing in heatmap

3. **Date Parsing Losses**
   - 24.4% of rows lost due to invalid dates
   - Trade-off between data quality and volume
   - Acceptable for analysis purposes

4. **Model Generalization**
   - Model trained on universities 10, 11, 12
   - May not generalize well to other universities
   - Time-based split tests future generalization within these universities

---

## Next Steps (Post-Pipeline)

1. **Verify Outputs**
   ```bash
   ls -lh data/processed/
   ls -lh data/dashboard/
   ls -lh models/
   ```

2. **Inspect Sample Data**
   ```bash
   head -20 data/dashboard/building_level_heatmap.csv
   cat data/dashboard/metadata.json
   ```

3. **Check Model Performance**
   ```bash
   cat models/asset_feature_importance.csv | head -20
   ```

4. **Test Frontend Integration**
   - Load metadata.json
   - Parse building_names mapping
   - Load building_level_heatmap.csv
   - Verify subsystem rows display correctly

---

## Troubleshooting

### Issue: "File not found: FMUCD.csv"
**Solution:** Ensure FMUCD.csv is in project root directory

### Issue: "Memory error"
**Solution:** Increase available RAM (need ~4-8 GB for full CSV processing)

### Issue: "Event count mismatch"
**Cause:** Data loss during aggregation or filtering
**Check:** Review validation output in Phase 1

### Issue: "Model performance below 0.70"
**Cause:** Possible overfitting or poor features
**Check:** Feature importance, try different hyperparameters

### Issue: "Too many null BuildingNames"
**Expected:** ~50% of buildings will have placeholder names
**Not a problem:** BuildingName is metadata only, doesn't affect predictions

---

## Technical Debt / Future Improvements

1. **BuildingName Enrichment**
   - Create manual mapping of BuildingID → BuildingName
   - Use external building database
   - Crowdsource building names from users

2. **Model Improvements**
   - Try LightGBM or CatBoost
   - Add interaction features (building_age × weather)
   - Cross-validation instead of single split
   - Hyperparameter tuning (grid search)

3. **Subsystem Classification Refinement**
   - Review subsystem classification accuracy
   - Add more granular subsystem categories
   - Use hierarchical structure (System → Subsystem → Component)

4. **Performance Optimization**
   - Parallelize Phase 1 classification
   - Cache intermediate results
   - Add incremental update capability (only process new data)

5. **Frontend Enhancements**
   - Add subsystem search/filter
   - Show system → subsystem hierarchy
   - Add "Group by System" view for comparison
   - Export functionality (CSV, PDF)

---

**Author:** AI Assistant
**Date:** 2026-03-07
**Version:** 2.0 (Subsystem + BuildingName upgrade)
