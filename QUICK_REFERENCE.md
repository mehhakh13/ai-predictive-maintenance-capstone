# Quick Reference: Upgraded Risk Heatmap

## What Changed?

### 1. Subsystem-Level Granularity ✅
- **Before:** 23 systems (HVAC, Plumbing, etc.)
- **After:** 71 subsystems (Terminal & Package Units, Plumbing Fixtures, etc.)
- **Benefit:** 3x more detailed risk insights

### 2. Building Names ✅
- **Before:** Numeric IDs only (e.g., "0470")
- **After:** Friendly names + IDs (e.g., "Engineering Hall (0470)")
- **Benefit:** User-friendly dashboard

### 3. ML-Based Predictions ✅ (Already Existed)
- **Method:** XGBoost classifier with lag features
- **Output:** `ml_risk` (probability 0-1)
- **Interpretation:**
  - 0.0-0.3 = Low risk
  - 0.3-0.6 = Medium risk
  - 0.6-1.0 = High risk

---

## How to Run

### Full Pipeline
```bash
./run_full_pipeline.sh
```

### Individual Phases
```bash
python3 scripts/prepare_asset_upm_data.py      # Phase 1: ~5-10 min
python3 scripts/engineer_asset_features.py     # Phase 2: ~2-5 min
python3 scripts/train_asset_upm_model.py       # Phase 3: ~3-7 min
python3 scripts/generate_heatmaps.py           # Phase 4: ~1-2 min
```

**Total time:** 10-25 minutes

---

## Output Files

```
data/dashboard/
  ├── building_level_heatmap.csv      # Main heatmap data (subsystem × month)
  ├── university_level_heatmap.csv    # Aggregated across all buildings
  └── metadata.json                    # Building names + IDs for dropdowns
```

---

## CSV Schema

### building_level_heatmap.csv
| Column | Description | Example |
|--------|-------------|---------|
| UniversityID | University identifier | 10 |
| BuildingID | Building identifier | 0470 |
| BuildingName | Building friendly name | Engineering Hall |
| SubsystemDescription | Subsystem name | Terminal & Package Units |
| MonthNum | Month (1-12) | 1 |
| ml_risk | **ML-predicted risk** (0-1) | 0.42 |
| hist_asset_rate | Historical asset failure rate | 0.12 |
| hist_shock_rate | Historical shock event rate | 0.05 |
| coverage | Number of data points | 150 |

### university_level_heatmap.csv
| Column | Description |
|--------|-------------|
| UniversityID | University identifier |
| SubsystemDescription | Subsystem name |
| MonthNum | Month (1-12) |
| ml_risk | ML-predicted risk (0-1) |
| hist_asset_rate | Historical asset failure rate |
| hist_shock_rate | Historical shock event rate |
| coverage | Number of data points |

### metadata.json
```json
{
  "universities": [10, 11, 12],
  "buildings_by_university": {
    "10": ["0470", "0230", "0152", ...]
  },
  "building_names": {
    "0470": "Engineering Hall",
    "0230": "Science Building",
    ...
  }
}
```

---

## Dashboard Integration

### Building Dropdown (Updated)
```javascript
// Load metadata
const metadata = await loadMetadata();

// Create building options with names
const buildingOptions = metadata.buildings_by_university[selectedUniversity].map(buildingId => ({
  value: buildingId,
  label: `${metadata.building_names[buildingId]} (${buildingId})`
}));
```

### Heatmap Data Loading
```javascript
// Building-level view
const data = buildingLevelData.filter(row =>
  row.UniversityID === selectedUniversity &&
  (selectedBuilding === 'all' || row.BuildingID === selectedBuilding)
);

// Pivot for heatmap: SubsystemDescription (rows) × MonthNum (columns)
const heatmapData = pivotData(data, 'SubsystemDescription', 'MonthNum', 'ml_risk');
```

---

## Key Metrics

### Granularity
- **Systems:** 23 → **Subsystems:** 71 (3x increase)
- **Heatmap cells per building:** 276 → 852 (3x increase)

### Data Volume
- **Universities:** 3 (10, 11, 12)
- **Buildings:** ~1,400
- **Subsystems:** 71
- **Months:** 12

### File Sizes
- `building_level_heatmap.csv`: ~50-100K rows (~5-10 MB)
- `university_level_heatmap.csv`: ~2-3K rows (~200-400 KB)
- `metadata.json`: <50 KB

---

## Example Query

**Question:** "What is the predicted risk for HVAC Terminal & Package Units in Engineering Hall for January?"

**Query:**
```csv
UniversityID=10, BuildingName="Engineering Hall", SubsystemDescription="Terminal & Package Units", MonthNum=1
```

**Result:**
```csv
UniversityID,BuildingID,BuildingName,SubsystemDescription,MonthNum,ml_risk,hist_asset_rate,hist_shock_rate,coverage
10,0470,Engineering Hall,Terminal & Package Units,1,0.42,0.12,0.05,150
```

**Interpretation:**
- **42% probability** of asset-driven UPM event in January
- Historical rate: 12% (model predicts higher risk)
- Based on 150 data points (reliable)

---

## Top 20 Subsystems (by occurrence)

1. Lighting and Branch Wiring
2. Distribution Systems
3. Sprinklers
4. Terminal & Package Units
5. Plumbing Fixtures
6. Communications & Security
7. Interior Doors
8. Heat Generation Systems
9. Domestic Water Distribution
10. Controls and Instrumentation
11. Commercial Equipment
12. Unclassified
13. Wall Finishes
14. Inspection
15. Electrical Service & Distribution
16. General
17. Exterior Doors
18. Fixed Furnishings
19. Elevators & Lifts
20. Cooling Generation Systems

---

## Troubleshooting

### Issue: "File not found: FMUCD.csv"
**Solution:** Ensure `FMUCD.csv` is in the project root directory

### Issue: "Memory error during Phase 1"
**Solution:** Increase available RAM or use a machine with more memory (FMUCD.csv is 1.4 GB)

### Issue: "Model performance below 0.70 ROC-AUC"
**Solution:** Review feature importance, consider adding more features or tuning hyperparameters

### Issue: "Heatmap has too many empty cells"
**Solution:** Lower `min_coverage` threshold in Phase 4 (default: 10)

---

## Next Steps

1. ✅ Run pipeline: `./run_full_pipeline.sh`
2. ✅ Verify outputs in `data/dashboard/`
3. ⬜ Update frontend to use new CSV schema
4. ⬜ Test building name dropdown
5. ⬜ Deploy to production

---

**Documentation:**
- Full details: `UPGRADE_SUMMARY.md`
- Pipeline flow: `HEATMAP_DATA_FLOW.md`
- Architecture: `PIPELINE_README.md`
