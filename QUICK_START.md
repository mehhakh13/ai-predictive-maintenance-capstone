# Quick Start Guide: Risk Heatmap with University & Building Filtering

## 🚀 Quick Deploy for Demos (FREE!)

**Want to demo this app publicly in 5 minutes?** Use GitHub Codespaces!

👉 **[See CODESPACES_DEPLOYMENT.md](./CODESPACES_DEPLOYMENT.md)** for full guide

**TL;DR:**
1. Go to your GitHub repo → Click "Code" → "Codespaces" → "Create codespace"
2. Wait ~2 minutes for auto-setup
3. Run: `./start-codespaces.sh`
4. Set ports 5173 & 8000 to "Public" in Ports tab
5. Share the frontend URL: `https://your-codespace-name-5173.app.github.dev`

**Free tier:** 60 hours/month (perfect for 1-2 day demos!)

---

## Local Development Setup

## Prerequisites

- Python 3.x with pandas, numpy, scikit-learn, xgboost
- Node.js and npm for frontend
- Dataset: `FMUCD_USA.parquet` in project root

## Step 1: Run the Backend Pipeline

Navigate to project root and run all 4 phases sequentially:

```bash
cd /home/sradmin/ai-predictive-maintenance-capstone

# Phase 1: Data Preparation (with UniversityID filtering)
python3 scripts/prepare_asset_upm_data.py

# Phase 2: Feature Engineering
python3 scripts/engineer_asset_features.py

# Phase 3: Model Training
python3 scripts/train_asset_upm_model.py

# Phase 4: Heatmap Generation (building-level outputs)
python3 scripts/generate_heatmaps.py
```

**Expected Outputs:**
```
data/dashboard/
├── building_level_heatmap.csv    ← Building-specific risk data
├── university_level_heatmap.csv  ← All Buildings aggregation
└── metadata.json                 ← Dropdown options
```

## Step 2: Start the Frontend

```bash
cd ai-predictive-maintenance-capstone/frontend
npm install  # First time only
npm start
```

Frontend should open at `http://localhost:3000`

## Step 3: Navigate to Risk Heatmap

Click on "Risk Heatmap" in the navigation or go to:
```
http://localhost:3000/risk-heatmap
```

## Step 4: Test the Filters

### Test 1: University Selection
1. Select **University 10** from the dropdown
2. Keep **All Buildings** selected
3. Observe heatmap showing averaged data across all buildings

### Test 2: Building Selection
1. Keep **University 10** selected
2. Select **Building 1** from the building dropdown
3. Observe heatmap updating to show Building 1 specific data

### Test 3: University Switch
1. Change university to **University 11**
2. Notice building dropdown resets to **All Buildings**
3. Notice building dropdown now shows buildings for University 11

### Test 4: Compare Different Buildings
1. Select **University 10** → **Building 1**
2. Note HVAC risk in January (should be high, ~65%)
3. Select **University 10** → **Building 2**
4. Compare HVAC risk in January (may differ)

## What to Expect

### University 10 (5 buildings)
- Building dropdown: All Buildings, Building 1, 2, 3, 4, 5

### University 11 (4 buildings)
- Building dropdown: All Buildings, Building 1, 2, 3, 4

### University 12 (6 buildings)
- Building dropdown: All Buildings, Building 1, 2, 3, 4, 5, 6

### Heatmap Display
- **Rows**: System types (HVAC, Electrical, Plumbing, etc.)
- **Columns**: Months (Jan-Dec)
- **Cell Color**: Risk level (green=low, red=high)
- **Risk Thresholds**:
  - Green: < 15%
  - Yellow: 15-30%
  - Orange: 30-50%
  - Orange-Red: 50-70%
  - Red: ≥ 70%

### Interactive Features
- **Click a cell**: Opens detail modal with ML prediction and historical rates
- **Hover over cell**: Shows tooltip with system, month, and risk
- **Show/Hide Values**: Toggle button to display risk percentages in cells
- **Search systems**: Filter systems by name

## Troubleshooting

### Issue: Pipeline script fails
**Check:**
- FMUCD_USA.parquet exists in project root
- All required Python packages installed: `pip install pandas numpy scikit-learn xgboost`
- Data contains UniversityID 10, 11, 12

### Issue: Frontend doesn't load data
**Check:**
- Mock data generators are being used (default)
- Check browser console for errors (F12)
- Verify useRiskHeatmapData hook is being called correctly

### Issue: Dropdowns are empty
**Check:**
- metadata is loaded correctly in useRiskHeatmapData hook
- generateMockMetadata() is returning correct structure
- Browser console shows metadata object

### Issue: Heatmap shows no data
**Check:**
- University and building are selected (not null)
- mlHeatmap array has data: `console.log(mlHeatmap)`
- Filters are not excluding all data

### Issue: Building dropdown doesn't reset
**Check:**
- useEffect dependency array includes [selectedUniversity, metadata]
- setSelectedBuilding('all') is being called
- Component is re-rendering after university change

## Connecting Real Data (Future)

When pipeline outputs are ready, update `frontend/src/hooks/useRiskHeatmapData.js`:

### Option 1: Load from API
```javascript
const buildingResponse = await fetch('/api/heatmap/building');
const buildingData = await buildingResponse.json();

const uniResponse = await fetch('/api/heatmap/university');
const uniData = await uniResponse.json();

const metaResponse = await fetch('/api/heatmap/metadata');
const metaData = await metaResponse.json();
```

### Option 2: Load CSV files directly
```javascript
import Papa from 'papaparse';

const buildingData = await loadCSV('/data/dashboard/building_level_heatmap.csv');
const uniData = await loadCSV('/data/dashboard/university_level_heatmap.csv');

async function loadCSV(path) {
  const response = await fetch(path);
  const text = await response.text();
  const result = Papa.parse(text, { header: true, dynamicTyping: true });
  return result.data;
}
```

## Feature Checklist

After completing the setup, verify these features work:

- [ ] Pipeline runs successfully and generates 3 files
- [ ] Frontend loads without errors
- [ ] University dropdown shows 10, 11, 12
- [ ] Building dropdown shows correct buildings for each university
- [ ] "All Buildings" option appears first in building dropdown
- [ ] Changing university resets building to "All Buildings"
- [ ] Heatmap displays correctly with color coding
- [ ] Clicking a cell shows detail modal
- [ ] KPI cards show correct metrics
- [ ] Insights panel shows recommendations
- [ ] Risk charts display trend and bar chart
- [ ] System search filter works
- [ ] Show/Hide values toggle works

## Data Validation

### Check Building-Level CSV
```bash
head -n 5 data/dashboard/building_level_heatmap.csv
```

Expected format:
```
UniversityID,BuildingID,SystemDescription,MonthNum,ml_risk,hist_asset_rate,hist_shock_rate,coverage
10,1,HVAC,1,0.65,0.12,0.05,150
10,1,HVAC,2,0.68,0.14,0.06,148
...
```

### Check University-Level CSV
```bash
head -n 5 data/dashboard/university_level_heatmap.csv
```

Expected format:
```
UniversityID,SystemDescription,MonthNum,ml_risk,hist_asset_rate,hist_shock_rate,coverage
10,HVAC,1,0.60,0.11,0.04,750
10,HVAC,2,0.62,0.12,0.05,745
...
```

### Check Metadata JSON
```bash
cat data/dashboard/metadata.json
```

Expected format:
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

## Performance Benchmarks

### Pipeline Runtime (approximate)
- Phase 1: 2-5 minutes
- Phase 2: 1-2 minutes
- Phase 3: 3-5 minutes (model training)
- Phase 4: < 1 minute
- **Total**: ~10-15 minutes

### Data Sizes (approximate)
- monthly_asset_upm.parquet: 50-100 MB
- asset_features.parquet: 60-120 MB
- predictions_with_metadata.parquet: 70-140 MB
- building_level_heatmap.csv: 500 KB - 2 MB
- university_level_heatmap.csv: 50-200 KB
- metadata.json: < 1 KB

### Frontend Load Time
- Initial data load: < 500ms (mock data)
- Filter change: < 50ms (client-side filtering)
- Heatmap render: < 100ms

## Next Steps

1. Run the pipeline to generate real data
2. Update frontend to load real CSV files
3. Add API endpoints for serving data (optional)
4. Deploy to production
5. Add additional features:
   - Export filtered data to CSV
   - Save/load custom filter presets
   - Compare multiple buildings side-by-side
   - Historical comparison (year-over-year)
   - Alert thresholds and notifications

## Support

For issues or questions:
1. Check HEATMAP_UPDATE_SUMMARY.md for detailed implementation notes
2. Check HEATMAP_DATA_FLOW.md for system architecture
3. Review browser console for frontend errors
4. Check pipeline script output for backend errors
