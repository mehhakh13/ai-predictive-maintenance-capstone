# Risk Heatmap Data Flow - University & Building Filtering

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Raw Data Source                              │
│              FMUCD_USA.parquet (3.3M work orders)               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ Filter to UniversityID ∈ {10, 11, 12}
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: Data Preparation                     │
│         scripts/prepare_asset_upm_data.py                       │
│                                                                  │
│  • Classify UPM → shock/asset/unknown                          │
│  • Create monthly aggregations by (Uni, Bldg, System)         │
│  • Zero-fill missing months                                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ data/processed/monthly_asset_upm.parquet
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Phase 2: Feature Engineering                     │
│          scripts/engineer_asset_features.py                     │
│                                                                  │
│  • Create lag features (1/3/6 months)                          │
│  • Cyclical temporal encoding                                   │
│  • months_since_last_event                                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ data/processed/asset_features.parquet
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Phase 3: Model Training                        │
│           scripts/train_asset_upm_model.py                      │
│                                                                  │
│  • Train XGBoost classifier                                     │
│  • Generate risk_prob_asset predictions                         │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ data/processed/predictions_with_metadata.parquet
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Phase 4: Heatmap Generation                      │
│            scripts/generate_heatmaps.py (UPDATED)               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Building-Level Aggregation                          │      │
│  │  Group by: (UniversityID, BuildingID,               │      │
│  │             SystemDescription, MonthNum)             │      │
│  │                                                       │      │
│  │  Columns:                                            │      │
│  │  • ml_risk = mean(risk_prob_asset)                  │      │
│  │  • hist_asset_rate = mean(UPM_asset_event)          │      │
│  │  • hist_shock_rate = mean(UPM_shock_event)          │      │
│  │  • coverage = count(rows)                            │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     │ building_level_heatmap.csv                │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  University-Level Aggregation (All Buildings)        │      │
│  │  Group by: (UniversityID,                            │      │
│  │             SystemDescription, MonthNum)             │      │
│  │                                                       │      │
│  │  Columns: Same as building-level                     │      │
│  │  (aggregated across all buildings)                   │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     │ university_level_heatmap.csv              │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Metadata Generation                                 │      │
│  │  {                                                    │      │
│  │    "universities": [10, 11, 12],                    │      │
│  │    "buildings_by_university": {                      │      │
│  │      "10": [1, 2, 3, 4, 5],                         │      │
│  │      "11": [1, 2, 3, 4],                            │      │
│  │      "12": [1, 2, 3, 4, 5, 6]                       │      │
│  │    }                                                  │      │
│  │  }                                                    │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     │ metadata.json                             │
└─────────────────────┴───────────────────────────────────────────┘
                      │
                      │ Dashboard Files:
                      │ • building_level_heatmap.csv
                      │ • university_level_heatmap.csv
                      │ • metadata.json
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Application                          │
│               frontend/src/pages/RiskHeatmapPage.jsx            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  User Interface                                      │      │
│  │                                                       │      │
│  │  ┌────────────────┐  ┌──────────────────┐          │      │
│  │  │ University: 10 ▼│  │ Building: All ▼  │          │      │
│  │  └────────────────┘  └──────────────────┘          │      │
│  │                                                       │      │
│  │  Selection: University 10 - All Buildings            │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Data Loading Hook                                   │      │
│  │  frontend/src/hooks/useRiskHeatmapData.js            │      │
│  │                                                       │      │
│  │  useRiskHeatmapData(selectedUniversity,              │      │
│  │                     selectedBuilding)                │      │
│  │                                                       │      │
│  │  If selectedBuilding === 'all':                      │      │
│  │    → Load university_level_heatmap.csv               │      │
│  │    → Filter by UniversityID                          │      │
│  │                                                       │      │
│  │  Else:                                                │      │
│  │    → Load building_level_heatmap.csv                 │      │
│  │    → Filter by UniversityID AND BuildingID           │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     │ Filtered heatmap data                     │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Visualization Components                            │      │
│  │                                                       │      │
│  │  • KpiRow - Summary metrics                         │      │
│  │  • Heatmap - Systems × Months grid                  │      │
│  │  • InsightsPanel - Top risks & recommendations      │      │
│  │  • RiskCharts - Trends & bar charts                 │      │
│  │  • CellDetailModal - Drill-down on click            │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Data Examples

### Building-Level Heatmap Row
```
UniversityID: 10
BuildingID: 1
SystemDescription: "HVAC"
MonthNum: 1 (January)
ml_risk: 0.65
hist_asset_rate: 0.12
hist_shock_rate: 0.05
coverage: 150
```

**Interpretation**: In January, Building 1 at University 10 has:
- 65% predicted probability of asset-driven UPM for HVAC
- Historically, 12% of months had asset UPM events
- Historically, 5% of months had shock UPM events
- Based on 150 data points

### University-Level Heatmap Row (All Buildings)
```
UniversityID: 10
SystemDescription: "HVAC"
MonthNum: 1 (January)
ml_risk: 0.60
hist_asset_rate: 0.11
hist_shock_rate: 0.04
coverage: 750
```

**Interpretation**: In January, across all buildings at University 10:
- 60% average predicted probability of asset-driven UPM for HVAC
- Historically, 11% average asset UPM event rate
- Historically, 4% average shock UPM event rate
- Based on 750 data points (aggregated from all buildings)

## Filtering Logic Flow

```
User selects University 10 + Building "All"
        │
        ▼
useRiskHeatmapData(10, 'all')
        │
        ├─ Load university_level_heatmap.csv
        │
        ├─ Filter: UniversityID === 10
        │
        └─ Return filtered data
                │
                ▼
        Heatmap displays HVAC, Electrical, etc.
        for University 10 (averaged across all buildings)

─────────────────────────────────────────────────

User selects University 10 + Building 3
        │
        ▼
useRiskHeatmapData(10, 3)
        │
        ├─ Load building_level_heatmap.csv
        │
        ├─ Filter: UniversityID === 10 AND BuildingID === 3
        │
        └─ Return filtered data
                │
                ▼
        Heatmap displays HVAC, Electrical, etc.
        for Building 3 only

─────────────────────────────────────────────────

User changes University from 10 to 11
        │
        ▼
useEffect triggers
        │
        ├─ Update availableBuildings from metadata
        │   (Buildings for Uni 11: [1, 2, 3, 4])
        │
        ├─ Reset selectedBuilding to 'all'
        │
        └─ Re-render with new filters
                │
                ▼
        Heatmap displays University 11 - All Buildings
```

## Performance Considerations

### Data Volume
- **Building-Level CSV**: ~5,000-10,000 rows
  - 3 universities × ~5 buildings avg × ~10 systems × 12 months
- **University-Level CSV**: ~500-1,000 rows
  - 3 universities × ~10 systems × 12 months
- **Metadata JSON**: < 1 KB

### Optimization Strategies
1. **Load once on mount**: All data loaded initially, filtering done client-side
2. **Pre-aggregation**: University-level data pre-computed in backend
3. **Coverage filtering**: Only rows with ≥10 data points included
4. **Lazy loading** (future): Load building data on-demand when specific building selected

## Coverage Filtering

Minimum coverage threshold = **10 entities** per cell

**Why?**
- Ensures statistical reliability
- Prevents misleading predictions from sparse data
- Reduces heatmap clutter

**What gets filtered out?**
- Rare system-month combinations with < 10 observations
- New buildings with insufficient history
- Seasonal systems with limited data

**Example:**
```
Building 10-1, System "Fire Protection", Month 7
→ Only 5 data points available
→ EXCLUDED from heatmap (coverage < 10)
```

## Frontend State Management

```javascript
// Component State
const [selectedUniversity, setSelectedUniversity] = useState(10);
const [selectedBuilding, setSelectedBuilding] = useState('all');
const [availableBuildings, setAvailableBuildings] = useState([]);

// Data Loading
const { mlHeatmap, historicalHeatmap, metadata, loading, error } =
  useRiskHeatmapData(selectedUniversity, selectedBuilding);

// Effect: Update buildings when university changes
useEffect(() => {
  if (metadata && selectedUniversity) {
    const buildings = metadata.buildings_by_university[selectedUniversity];
    setAvailableBuildings(buildings);
    setSelectedBuilding('all'); // Reset to "All Buildings"
  }
}, [selectedUniversity, metadata]);
```

## Error Handling

### Backend Pipeline
- **Missing universities**: Warning if data contains universities outside {10, 11, 12}
- **Low coverage**: Rows with coverage < 10 automatically filtered
- **Validation checks**: Schema, risk range [0,1], NaN checks

### Frontend
- **Loading state**: Shows spinner while data loads
- **Error state**: Displays error message if data loading fails
- **Empty data**: Handles case where no data matches filter criteria
- **Invalid selections**: University dropdown only shows valid options from metadata

## Testing Checklist

- [ ] Backend pipeline runs without errors
- [ ] CSV files generated in `data/dashboard/`
- [ ] Metadata JSON contains correct universities and buildings
- [ ] Frontend loads without console errors
- [ ] University dropdown shows [10, 11, 12]
- [ ] Building dropdown updates when university changes
- [ ] "All Buildings" shows aggregated data
- [ ] Specific building shows building-specific data
- [ ] Heatmap updates correctly on filter change
- [ ] KPIs update correctly on filter change
- [ ] No data shown when invalid selection
