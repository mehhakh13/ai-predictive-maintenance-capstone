# Risk Heatmap Update: University & Building Filtering

## Overview

The Risk Heatmap feature has been updated to support **University** and **Building** dropdown filtering, allowing users to view risk predictions at different levels of granularity.

## Changes Summary

### 1. Backend Updates

#### `scripts/prepare_asset_upm_data.py` (Phase 1)
- **Added early filtering** to UniversityID ∈ {10, 11, 12}
- Reduces data volume and speeds up the entire pipeline
- Location: Lines 122-127

#### `scripts/generate_heatmaps.py` (Phase 4)
Completely rewritten to support building-level filtering:

**New Functions:**
- `create_building_level_heatmap()` - Generates heatmap grouped by (UniversityID, BuildingID, SystemDescription, MonthNum)
- `create_university_level_heatmap()` - Generates aggregated "All Buildings" view grouped by (UniversityID, SystemDescription, MonthNum)
- `create_metadata()` - Creates metadata JSON with university and building lists for dropdowns

**New Outputs:**
- `data/dashboard/building_level_heatmap.csv` - Building-specific risk data
- `data/dashboard/university_level_heatmap.csv` - University-wide aggregations
- `data/dashboard/metadata.json` - Dropdown options metadata

**Data Schema:**

Building-level CSV:
```csv
UniversityID,BuildingID,SystemDescription,MonthNum,ml_risk,hist_asset_rate,hist_shock_rate,coverage
10,1,HVAC,1,0.65,0.12,0.05,150
10,1,HVAC,2,0.68,0.14,0.06,148
...
```

University-level CSV:
```csv
UniversityID,SystemDescription,MonthNum,ml_risk,hist_asset_rate,hist_shock_rate,coverage
10,HVAC,1,0.60,0.11,0.04,750
10,HVAC,2,0.62,0.12,0.05,745
...
```

Metadata JSON:
```json
{
  "universities": [10, 11, 12],
  "buildings_by_university": {
    "10": [1, 2, 3, 4, 5],
    "11": [1, 2, 3, 4],
    "12": [1, 2, 3, 4, 5, 6]
  }
}
```

### 2. Frontend Updates

#### `frontend/src/hooks/useRiskHeatmapData.js`
- **Updated hook signature**: Now accepts `(selectedUniversity, selectedBuilding)` parameters
- **New mock data generators**:
  - `generateMockBuildingHeatmap()` - Building-level data for all 3 universities
  - `generateMockUniversityHeatmap()` - University-level aggregations
  - `generateMockMetadata()` - Dropdown metadata
- **Smart filtering logic**:
  - If `selectedBuilding === 'all'`: Uses university-level aggregation
  - If specific building selected: Filters building-level data
  - Returns data in the same format expected by existing components

#### `frontend/src/pages/RiskHeatmapPage.jsx`
- **Added state management** for university and building selection
- **New dropdown filters**:
  - University dropdown (10, 11, 12)
  - Building dropdown (dynamically populated based on selected university)
- **Auto-reset logic**: When university changes, building resets to "All Buildings"
- **Visual indicators**: Shows current selection below filters
- **Icons added**: School icon for university, Building2 icon for building

### 3. Key Features

#### Dropdown Behavior
1. **University Dropdown**:
   - Always shows Universities 10, 11, 12
   - Defaults to University 10

2. **Building Dropdown**:
   - Shows "All Buildings" + specific buildings for selected university
   - Dynamically updates when university changes
   - Defaults to "All Buildings"

#### Data Aggregation
- **"All Buildings" view**:
  - Uses pre-aggregated university-level data
  - Averages risk across all buildings in that university
  - More efficient than client-side aggregation

- **Specific building view**:
  - Shows risk for that exact building
  - Filtered from building-level dataset

#### Backward Compatibility
- All existing components (KpiRow, Heatmap, InsightsPanel, etc.) work unchanged
- They receive filtered data in the same format as before
- No changes needed to heatmap rendering logic

## Data Pipeline Workflow

### Running the Updated Pipeline

1. **Phase 1**: Data Preparation
```bash
cd /home/sradmin/ai-predictive-maintenance-capstone
python scripts/prepare_asset_upm_data.py
```
- Now filters to UniversityID ∈ {10, 11, 12}
- Output: `data/processed/monthly_asset_upm.parquet`

2. **Phase 2**: Feature Engineering
```bash
python scripts/engineer_asset_features.py
```
- No changes (uses filtered data from Phase 1)
- Output: `data/processed/asset_features.parquet`

3. **Phase 3**: Model Training
```bash
python scripts/train_asset_upm_model.py
```
- No changes (trains on filtered universities)
- Output: `models/asset_upm_predictor.pkl`, `data/processed/predictions_with_metadata.parquet`

4. **Phase 4**: Heatmap Generation
```bash
python scripts/generate_heatmaps.py
```
- **NEW**: Creates building-level and university-level heatmaps
- Outputs:
  - `data/dashboard/building_level_heatmap.csv`
  - `data/dashboard/university_level_heatmap.csv`
  - `data/dashboard/metadata.json`

## Frontend Integration

### Using Real Data (when pipeline completes)

Update `frontend/src/hooks/useRiskHeatmapData.js` to load from CSV/API:

```javascript
// Replace mock data with actual API calls
const buildingResponse = await fetch('/api/heatmap/building');
const buildingData = await buildingResponse.json();

const uniResponse = await fetch('/api/heatmap/university');
const uniData = await uniResponse.json();

const metaResponse = await fetch('/api/heatmap/metadata');
const metaData = await metaResponse.json();
```

Or load from CSV files directly:
```javascript
const buildingData = await loadCSV('/data/dashboard/building_level_heatmap.csv');
const uniData = await loadCSV('/data/dashboard/university_level_heatmap.csv');
const metaData = await loadJSON('/data/dashboard/metadata.json');
```

## Testing

### Manual Testing Steps

1. **Start Frontend**:
```bash
cd frontend
npm start
```

2. **Navigate to Risk Heatmap page**:
   - URL: `http://localhost:3000/risk-heatmap`

3. **Test University Dropdown**:
   - Select University 10 → Should show heatmap data
   - Select University 11 → Should update heatmap
   - Select University 12 → Should update heatmap

4. **Test Building Dropdown**:
   - Keep "All Buildings" selected → Should show aggregated data
   - Select a specific building → Should show building-specific data
   - Change university → Building dropdown should reset to "All Buildings"

5. **Verify Data Updates**:
   - KPI cards should update with each filter change
   - Heatmap cells should show different risks
   - InsightsPanel should show relevant insights

### Expected Behavior

- **University 10, All Buildings**: Shows average risk across all 5 buildings
- **University 10, Building 1**: Shows risk for only Building 1
- **University 11, All Buildings**: Shows average risk across all 4 buildings
- And so on...

## Files Modified

### Backend
1. `/scripts/prepare_asset_upm_data.py` - Added UniversityID filter
2. `/scripts/generate_heatmaps.py` - Complete rewrite for building-level output

### Frontend
1. `/frontend/src/hooks/useRiskHeatmapData.js` - Updated to support filtering
2. `/frontend/src/pages/RiskHeatmapPage.jsx` - Added dropdown UI

### New Files
- This summary document

## Next Steps

1. **Run the updated pipeline** to generate real building-level data
2. **Update frontend data loading** to use real CSV/API data instead of mocks
3. **Add backend API endpoints** (optional) to serve the CSV data as JSON
4. **Performance optimization** if needed (caching, lazy loading, etc.)
5. **Additional features**:
   - Export filtered data
   - Save favorite views
   - Compare buildings side-by-side

## Notes

- The "Shock vs Asset UPM" logic is preserved in both building and university-level aggregations
- Historical rates (`hist_asset_rate`, `hist_shock_rate`) are calculated as averages of the binary event indicators
- Coverage filtering (≥10 entities) is applied to ensure statistical reliability
- All existing heatmap visualizations, KPIs, and insights work unchanged with filtered data

## Questions or Issues?

If you encounter any issues:
1. Check that all 4 pipeline phases completed successfully
2. Verify the CSV outputs exist in `data/dashboard/`
3. Check browser console for JavaScript errors
4. Ensure the frontend is loading data correctly in the Network tab
