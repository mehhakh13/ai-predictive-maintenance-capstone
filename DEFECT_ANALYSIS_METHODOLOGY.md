# Defect Analysis Methodology
## Robust Algorithms for Project Enhancement

**Date:** April 15, 2026
**Purpose:** Provide explicit, logical methods to analyze defect recurrence, severity impact, and environmental sensitivity

---

## Executive Summary

This document outlines three robust analytical methods to enhance the AI Predictive Maintenance dashboard:

1. **Defect Recurrence Analysis** - Identify the most frequently occurring defects
2. **Severity Impact Score** - Calculate which defects cause the most severe impact
3. **Environmental Sensitivity Index** - Measure which defects are most influenced by weather/seasons

Each method produces a **ranked list** that can be visualized in the dashboard.

---

## 1. DEFECT RECURRENCE ANALYSIS

### Objective
Identify which defect categories occur most frequently across time, buildings, and systems.

### Data Sources
- Primary: `/data/defect_intelligence/category_stats.csv` (34 defect categories)
- Secondary: Raw work orders from `FMUCD.csv` with temporal information
- Database: `fmucd` table with `wo_start_date`, `system_code`, `building_id`

### Algorithm: Weighted Recurrence Score (WRS)

**Step 1: Calculate Base Recurrence Metrics**

For each defect category `d`:

```
Total_Count(d) = number of work orders classified as defect d
Active_Months(d) = number of distinct months with at least one occurrence
Affected_Buildings(d) = number of unique buildings experiencing defect d
Affected_Systems(d) = number of unique system codes with defect d
```

**Step 2: Calculate Temporal Persistence**

```
Temporal_Persistence(d) = Active_Months(d) / Total_Months_in_Dataset

Where:
- Total_Months_in_Dataset = 240 (20 years × 12 months)
- This measures how consistently the defect appears over time
```

**Step 3: Calculate Spatial Distribution**

```
Spatial_Distribution(d) = (Affected_Buildings(d) / Total_Buildings) × (Affected_Systems(d) / Total_Systems)

Where:
- Total_Buildings ≈ 1,400
- Total_Systems ≈ 23
- This measures how widespread the defect is across assets
```

**Step 4: Calculate Recurrence Rate**

```
Recurrence_Rate(d) = Total_Count(d) / Active_Months(d)

- This measures average defects per active month
- Higher values indicate clustering/bursts of occurrences
```

**Step 5: Composite Weighted Recurrence Score**

```
WRS(d) = w1 × log(Total_Count(d)) +
         w2 × Temporal_Persistence(d) +
         w3 × Spatial_Distribution(d) +
         w4 × log(Recurrence_Rate(d))

Recommended weights:
w1 = 0.40  (Total occurrence count is most important)
w2 = 0.25  (Temporal consistency matters)
w3 = 0.20  (Spatial spread indicates systemic issues)
w4 = 0.15  (Rate of occurrence when active)

Note: log() is used to normalize highly skewed distributions
```

### Normalization

```
Normalized_WRS(d) = (WRS(d) - min(WRS)) / (max(WRS) - min(WRS)) × 100

Result: Score from 0-100, where 100 = most recurrent defect
```

### Output: Ranked List

| Rank | Defect Category | WRS | Total Count | Temporal Persistence | Spatial Distribution | Interpretation |
|------|----------------|-----|-------------|---------------------|---------------------|----------------|
| 1 | HVAC - Temperature Control | 95.2 | 9,913 | 0.82 | 0.45 | Highly recurrent, persistent across seasons |
| 2 | Electrical - Lighting Failure | 92.8 | 10,573 | 0.78 | 0.42 | Very frequent, widespread |
| ... | ... | ... | ... | ... | ... | ... |

### Visualization Recommendations

**Dashboard Component:** "Defect Recurrence Ranking"

1. **Bar Chart** - Top 15 defects by WRS score
   - X-axis: Normalized WRS (0-100)
   - Y-axis: Defect category names
   - Color gradient: Red (high) to yellow (moderate)

2. **Bubble Chart** - Recurrence vs Spread
   - X-axis: Temporal Persistence
   - Y-axis: Total Count (log scale)
   - Bubble size: Spatial Distribution
   - Bubble color: Defect category

3. **Time Series Heatmap** - Monthly recurrence patterns
   - X-axis: Months (Jan-Dec)
   - Y-axis: Top 10 defect categories
   - Cell color: Count of occurrences

4. **Table View** with sortable columns:
   - Rank, Category, WRS, Count, Persistence, Distribution
   - Export to CSV functionality

---

## 2. SEVERITY IMPACT SCORE

### Objective
Calculate a comprehensive severity metric combining financial cost, operational impact, priority, and system criticality.

### Data Sources
- Primary: `category_stats.csv` (cost data per defect)
- Secondary: Work orders with `total_cost`, `wo_priority`, `labor_hours`, `system_code`
- System criticality mapping (to be created based on domain knowledge)

### Algorithm: Multi-Dimensional Severity Index (MDSI)

**Step 1: Financial Impact Score**

For each defect category `d`:

```
Avg_Cost(d) = Total_Cost(d) / Total_Count(d)
Max_Cost(d) = Maximum single work order cost for defect d
Cost_Variance(d) = Standard deviation of costs

Financial_Impact(d) = (0.5 × Normalized_Avg_Cost) +
                      (0.3 × Normalized_Max_Cost) +
                      (0.2 × Normalized_Cost_Variance)

Where normalization uses min-max scaling:
Normalized_X = (X - min(X)) / (max(X) - min(X))

Rationale:
- Average cost = typical impact (50% weight)
- Max cost = catastrophic potential (30% weight)
- Variance = unpredictability (20% weight)
```

**Step 2: Operational Impact Score**

```
Avg_Labor_Hours(d) = Total labor hours for defect d / Total_Count(d)
Avg_Duration(d) = Average work order duration (wo_end_date - wo_start_date)
Avg_Priority(d) = Mean priority value (1-100 scale)

Operational_Impact(d) = (0.35 × Normalized_Labor_Hours) +
                        (0.35 × Normalized_Duration) +
                        (0.30 × Normalized_Priority)

Rationale:
- Labor hours = resource consumption
- Duration = downtime/disruption
- Priority = urgency assigned by maintenance staff
```

**Step 3: System Criticality Multiplier**

Create a criticality weight for each system based on:

```
System_Criticality = {
    'Fire Protection': 1.5,        # Life safety critical
    'HVAC': 1.3,                   # Occupant comfort + health
    'Electrical': 1.4,             # Essential services
    'Plumbing': 1.2,               # Health + sanitation
    'Elevators': 1.3,              # Accessibility critical
    'Interior Construction': 1.0,   # Baseline
    'Equipment': 1.1,              # Operational
    'General': 1.0,                # Baseline
    ...
}

Criticality_Score(d) = Weighted average of system criticality for defect d
```

**Step 4: Cascading Failure Risk**

Measure potential for defect to cause secondary failures:

```
Cascade_Risk(d) = (Multi_System_Impact × Co_Occurrence_Rate)

Where:
Multi_System_Impact = Number of system types affected / Total systems
Co_Occurrence_Rate = Frequency of defect d appearing alongside other defects within 7 days

Data source:
- Join work orders on (building_id, wo_start_date ± 7 days)
- Count defect pairs that occur together
```

**Step 5: Composite Multi-Dimensional Severity Index**

```
MDSI(d) = w1 × Financial_Impact(d) +
          w2 × Operational_Impact(d) +
          w3 × Criticality_Score(d) +
          w4 × Cascade_Risk(d)

Recommended weights:
w1 = 0.35  (Financial impact is highly important)
w2 = 0.30  (Operational disruption matters)
w3 = 0.25  (System criticality affects severity)
w4 = 0.10  (Cascading failures are rare but severe)
```

### Normalization

```
Normalized_MDSI(d) = (MDSI(d) - min(MDSI)) / (max(MDSI) - min(MDSI)) × 100

Result: Severity score from 0-100, where 100 = most severe defect
```

### Output: Ranked List

| Rank | Defect Category | MDSI | Avg Cost | Avg Hours | Criticality | Cascade Risk | Risk Level |
|------|----------------|------|----------|-----------|-------------|--------------|------------|
| 1 | Safety - Fire Alarm System | 97.3 | $663 | 4.2 hrs | 1.5 | 0.23 | CRITICAL |
| 2 | Electrical - Power Outage | 94.1 | $566 | 3.8 hrs | 1.4 | 0.31 | CRITICAL |
| 3 | HVAC - Temperature Control | 89.7 | $559 | 3.5 hrs | 1.3 | 0.18 | HIGH |
| ... | ... | ... | ... | ... | ... | ... | ... |

Risk Level Classification:
- CRITICAL: MDSI ≥ 85
- HIGH: 70 ≤ MDSI < 85
- MEDIUM: 50 ≤ MDSI < 70
- LOW: MDSI < 50

### Visualization Recommendations

**Dashboard Component:** "Defect Severity Impact"

1. **Radar Chart** - Multi-dimensional view for top defects
   - Axes: Financial Impact, Operational Impact, Criticality, Cascade Risk
   - Multiple polygons overlaid (one per defect)

2. **Severity Matrix** - 2D classification
   - X-axis: Financial Impact (Low/Medium/High)
   - Y-axis: Operational Impact (Low/Medium/High)
   - Bubble size: MDSI score
   - Bubble color: Risk level (Red/Orange/Yellow/Green)

3. **Waterfall Chart** - Component breakdown for selected defect
   - Show how each component (Financial, Operational, etc.) contributes to total MDSI

4. **Priority Table** with filtering:
   - Filter by risk level (Critical/High/Medium/Low)
   - Filter by system type
   - Sort by any column

---

## 3. ENVIRONMENTAL SENSITIVITY INDEX

### Objective
Quantify how strongly each defect category is influenced by environmental factors (weather, temperature, seasons).

### Data Sources
- Primary: Work orders joined with weather data (`fmucd` table)
- Weather variables: `avg_temp`, `humidity_pct`, `precipitation_mm`, `snow_mm`, `wind_speed_ms`
- Temporal: `month`, `season`, `quarter`

### Algorithm: Environmental Correlation & Variance Analysis

**Step 1: Seasonal Variation Analysis**

For each defect category `d`:

```
Monthly_Counts(d) = [count_jan, count_feb, ..., count_dec]

Seasonal_Variance(d) = Coefficient of Variation (CV) of monthly counts
                     = std(Monthly_Counts) / mean(Monthly_Counts)

Interpretation:
- CV near 0 = defect occurs uniformly year-round (low seasonal sensitivity)
- CV > 0.5 = strong seasonal pattern (high sensitivity)
```

**Step 2: Temperature Sensitivity**

```
For defect d:
1. Group work orders by temperature bins:
   [-20°C to -10°C], [-10°C to 0°C], [0°C to 10°C], [10°C to 20°C], [20°C to 30°C]

2. Calculate occurrence rate per bin:
   Rate(bin) = Count(d in bin) / Total_WO(bin)

3. Temperature_Correlation(d) = Pearson correlation coefficient between:
   - X = avg_temp for each work order
   - Y = binary indicator (1 if defect d, 0 otherwise)

4. Temperature_Sensitivity(d) = |Temperature_Correlation(d)|

   - Range: 0 to 1
   - Higher = stronger relationship with temperature
```

**Step 3: Precipitation Sensitivity**

```
Compare defect occurrence rates during:
- Dry periods: precipitation_mm = 0
- Light rain: 0 < precipitation_mm ≤ 5
- Heavy rain: precipitation_mm > 5
- Snow events: snow_mm > 0

Precipitation_Ratio(d) = max(Rate across conditions) / min(Rate across conditions)

Normalized:
Precipitation_Sensitivity(d) = (Precipitation_Ratio - 1) / max(Precipitation_Ratio - 1)

Range: 0 to 1, where 1 = maximum variation across precipitation conditions
```

**Step 4: Extreme Weather Events**

Define extreme conditions:
```
Extreme_Cold = avg_temp < 5th percentile
Extreme_Heat = avg_temp > 95th percentile
Heavy_Precip = precipitation_mm > 90th percentile
High_Wind = wind_speed_ms > 90th percentile

For defect d:
Extreme_Event_Rate(d) = Count(d during extreme events) / Count(d total)
Baseline_Rate = Count(extreme events) / Count(total WO)

Extreme_Sensitivity(d) = Extreme_Event_Rate(d) / Baseline_Rate

If > 1: Defect occurs MORE frequently during extreme weather
If < 1: Defect occurs LESS frequently during extreme weather
If ≈ 1: No relationship with extreme weather
```

**Step 5: Multi-Variable Weather Correlation**

Use multiple regression to capture combined weather effects:

```
For defect d, fit logistic regression:
P(defect = d) ~ β0 + β1(temp) + β2(humidity) + β3(precip) + β4(wind) + β5(pressure)

Extract:
Pseudo_R2(d) = McFadden's R-squared (measures model fit)
Weather_Contribution(d) = sum of |standardized coefficients|

Interpretation:
- Higher R² = weather variables explain more variance
- Higher coefficients = stronger individual variable effects
```

**Step 6: Composite Environmental Sensitivity Index**

```
ESI(d) = w1 × Seasonal_Variance(d) +
         w2 × Temperature_Sensitivity(d) +
         w3 × Precipitation_Sensitivity(d) +
         w4 × Extreme_Sensitivity(d) +
         w5 × Pseudo_R2(d)

Recommended weights:
w1 = 0.25  (Seasonal patterns are primary indicator)
w2 = 0.25  (Temperature is major driver)
w3 = 0.20  (Precipitation affects many defects)
w4 = 0.15  (Extreme events reveal sensitivity)
w5 = 0.15  (Overall weather explanatory power)
```

### Normalization

```
Normalized_ESI(d) = (ESI(d) - min(ESI)) / (max(ESI) - min(ESI)) × 100

Result: Environmental sensitivity score from 0-100
- 0-25: Low sensitivity (defect occurs year-round regardless of weather)
- 25-50: Moderate sensitivity (some seasonal/weather influence)
- 50-75: High sensitivity (strongly affected by weather)
- 75-100: Extreme sensitivity (primarily weather-driven)
```

### Output: Ranked List

| Rank | Defect Category | ESI | Seasonal CV | Temp Corr | Precip Sens | Extreme Ratio | Dominant Factor | Peak Season |
|------|----------------|-----|-------------|-----------|-------------|---------------|-----------------|-------------|
| 1 | HVAC - Temperature Control | 94.3 | 0.68 | 0.72 | 0.12 | 2.3 | Temperature | Summer/Winter |
| 2 | Water Damage - General Leak | 87.1 | 0.55 | 0.31 | 0.83 | 1.9 | Precipitation | Spring |
| 3 | Plumbing - Frozen Pipes | 91.8 | 0.91 | -0.85 | 0.22 | 3.1 | Extreme Cold | Winter |
| 4 | Structural - Window Damage | 72.4 | 0.42 | 0.08 | 0.61 | 1.7 | Wind/Precip | Fall/Winter |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

### Seasonal Peak Detection

For each high-ESI defect, identify peak months:

```
Peak_Months(d) = months where count > mean + 1.5 × std

Categorize:
- Winter peaks: Dec, Jan, Feb → likely cold-related
- Spring peaks: Mar, Apr, May → likely precipitation/thaw-related
- Summer peaks: Jun, Jul, Aug → likely heat-related
- Fall peaks: Sep, Oct, Nov → likely variable weather/transition
```

### Visualization Recommendations

**Dashboard Component:** "Environmental Sensitivity Analysis"

1. **Sensitivity Ranking Bar Chart**
   - X-axis: ESI score (0-100)
   - Y-axis: Defect categories (top 15)
   - Color coding: Low (green), Moderate (yellow), High (orange), Extreme (red)

2. **Seasonal Pattern Heatmap**
   - X-axis: Months (Jan-Dec)
   - Y-axis: High-ESI defect categories
   - Cell color: Normalized occurrence count
   - Highlights seasonal peaks

3. **Weather Correlation Matrix**
   - Rows: Defect categories
   - Columns: Weather variables (Temp, Humidity, Precip, Wind, etc.)
   - Cell color: Correlation strength (-1 to +1)
   - Red = positive correlation, Blue = negative

4. **Temperature Response Curves**
   - X-axis: Temperature bins (-20°C to +30°C)
   - Y-axis: Defect occurrence rate
   - Multiple lines (one per high-sensitivity defect)
   - Shows optimal/problematic temperature ranges

5. **Interactive Drill-Down Panel**
   - Select a defect category
   - View: Monthly trends, weather correlations, extreme event analysis
   - Export seasonal maintenance recommendations

6. **Extreme Weather Impact Table**
   - Columns: Defect, Baseline Rate, Extreme Cold Rate, Extreme Heat Rate, Heavy Precip Rate
   - Highlight cells where ratio > 1.5 (significantly elevated risk)

---

## IMPLEMENTATION PLAN

### Phase 1: Data Preparation (Week 1)

**Task 1.1:** Extract temporal features
```sql
-- Create aggregated view with temporal and weather features
CREATE VIEW defect_temporal AS
SELECT
    category_name,
    EXTRACT(MONTH FROM wo_start_date) as month,
    EXTRACT(YEAR FROM wo_start_date) as year,
    building_id,
    system_code,
    total_cost,
    labor_hours,
    wo_priority,
    avg_temp,
    humidity_pct,
    precipitation_mm,
    snow_mm,
    wind_speed_ms
FROM fmucd f
JOIN defect_intelligence d ON f.work_order_id = d.work_order_id
WHERE category_name IS NOT NULL;
```

**Task 1.2:** Create system criticality lookup table
```python
# data/system_criticality.csv
system_criticality = {
    'Fire Protection': 1.5,
    'HVAC': 1.3,
    'Electrical': 1.4,
    'Plumbing': 1.2,
    'Elevators': 1.3,
    'Interior Construction': 1.0,
    'Equipment': 1.1,
    # ... complete for all 23 systems
}
```

### Phase 2: Algorithm Implementation (Week 2)

**File Structure:**
```
/scripts/defect_analysis/
├── recurrence_analysis.py      # Implements WRS algorithm
├── severity_analysis.py         # Implements MDSI algorithm
├── environmental_analysis.py    # Implements ESI algorithm
├── utils.py                     # Shared normalization functions
└── visualizations.py            # Generates all charts
```

**Key Functions:**
```python
# recurrence_analysis.py
def calculate_wrs(defect_data):
    """Calculate Weighted Recurrence Score for all defects"""
    # Implementation of algorithm from Section 1
    return wrs_df

# severity_analysis.py
def calculate_mdsi(defect_data, system_criticality):
    """Calculate Multi-Dimensional Severity Index"""
    # Implementation of algorithm from Section 2
    return mdsi_df

# environmental_analysis.py
def calculate_esi(defect_data, weather_data):
    """Calculate Environmental Sensitivity Index"""
    # Implementation of algorithm from Section 3
    return esi_df
```

### Phase 3: Integration with Dashboard (Week 3)

**Backend API Endpoints:**
```python
# backend/main.py

@app.get("/api/defect-recurrence")
async def get_defect_recurrence():
    """Return ranked list by WRS"""
    # Load precomputed results
    df = pd.read_csv('data/dashboard/defect_recurrence.csv')
    return df.to_dict('records')

@app.get("/api/defect-severity")
async def get_defect_severity():
    """Return ranked list by MDSI"""
    df = pd.read_csv('data/dashboard/defect_severity.csv')
    return df.to_dict('records')

@app.get("/api/environmental-sensitivity")
async def get_environmental_sensitivity():
    """Return ranked list by ESI with seasonal patterns"""
    df = pd.read_csv('data/dashboard/environmental_sensitivity.csv')
    seasonal = pd.read_csv('data/dashboard/seasonal_patterns.csv')
    return {
        'rankings': df.to_dict('records'),
        'seasonal_patterns': seasonal.to_dict('records')
    }
```

**Frontend Components:**
```
/frontend/src/components/
├── DefectRecurrencePage.jsx      # New page for WRS rankings
├── DefectSeverityPage.jsx        # New page for MDSI rankings
├── EnvironmentalSensitivityPage.jsx  # New page for ESI analysis
└── charts/
    ├── RecurrenceBarChart.jsx
    ├── SeverityRadarChart.jsx
    ├── SeasonalHeatmap.jsx
    └── WeatherCorrelationMatrix.jsx
```

### Phase 4: Validation & Testing (Week 4)

**Validation Approach:**

1. **Face Validity:** Review rankings with domain experts
   - Do high-recurrence defects match maintenance experience?
   - Are severity scores logical given known critical systems?
   - Do seasonal patterns align with climate expectations?

2. **Statistical Validation:**
   - Bootstrap confidence intervals for scores
   - Sensitivity analysis: vary weights by ±20%, observe rank changes
   - Cross-validation: split data by time, verify consistency

3. **Comparative Analysis:**
   - Compare WRS rankings to raw count rankings (correlation should be high but not perfect)
   - Compare MDSI to cost-only rankings (should capture more nuance)
   - Compare ESI to simple seasonal variance (should show improvement)

**Expected Correlation Matrix:**
```
              WRS    MDSI    ESI    Raw_Count  Avg_Cost
WRS          1.00   0.45   0.22      0.85      0.38
MDSI         0.45   1.00   0.18      0.41      0.72
ESI          0.22   0.18   1.00      0.15      0.09
Raw_Count    0.85   0.41   0.15      1.00      0.33
Avg_Cost     0.38   0.72   0.09      0.33      1.00
```

---

## EXPECTED OUTCOMES

### Dashboard Enhancements

**New Page: "Defect Intelligence Center"**

**Tab 1: Recurrence Analysis**
- Top 15 most recurrent defects (bar chart)
- Temporal persistence trends (line chart)
- Spatial distribution map (bubble chart)
- Downloadable CSV: ranked_recurrence.csv

**Tab 2: Severity Impact**
- Severity matrix (2D scatter)
- Multi-dimensional radar charts
- Critical defect alerts (threshold: MDSI ≥ 85)
- Downloadable CSV: ranked_severity.csv

**Tab 3: Environmental Sensitivity**
- Sensitivity rankings (bar chart)
- Seasonal heatmaps (12-month view)
- Weather correlation matrix
- Temperature response curves
- Extreme weather alerts
- Downloadable CSV: ranked_environmental_sensitivity.csv

### Sample Output Files

**1. defect_recurrence.csv**
```csv
rank,category,wrs_score,total_count,temporal_persistence,spatial_distribution,active_months,affected_buildings
1,HVAC - Temperature Control,95.2,9913,0.82,0.45,197,634
2,Electrical - Lighting Failure,92.8,10573,0.78,0.42,188,601
3,Structural - Door/Lock Issue,89.3,9165,0.75,0.39,181,558
...
```

**2. defect_severity.csv**
```csv
rank,category,mdsi_score,avg_cost,avg_labor_hours,criticality_score,cascade_risk,risk_level
1,Safety - Fire Alarm System,97.3,663,4.2,1.5,0.23,CRITICAL
2,Electrical - Power Outage,94.1,566,3.8,1.4,0.31,CRITICAL
3,HVAC - Temperature Control,89.7,559,3.5,1.3,0.18,HIGH
...
```

**3. environmental_sensitivity.csv**
```csv
rank,category,esi_score,seasonal_cv,temp_correlation,precip_sensitivity,extreme_ratio,peak_season,sensitivity_level
1,HVAC - Temperature Control,94.3,0.68,0.72,0.12,2.3,Summer/Winter,EXTREME
2,Plumbing - Frozen Pipes,91.8,0.91,-0.85,0.22,3.1,Winter,EXTREME
3,Water Damage - General Leak,87.1,0.55,0.31,0.83,1.9,Spring,HIGH
...
```

**4. seasonal_patterns.csv**
```csv
category,jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec
HVAC - Temperature Control,892,834,645,543,512,1023,1156,1089,678,601,723,817
Water Damage - General Leak,234,267,512,634,589,423,312,298,401,445,478,389
...
```

---

## SUCCESS METRICS

To ensure the methodology achieves its goals:

1. **Actionability:** Rankings should enable:
   - Prioritized preventive maintenance schedules
   - Targeted resource allocation
   - Season-specific preparation plans

2. **Robustness:** Algorithms should:
   - Produce stable rankings when retested on different time windows
   - Show logical relationships between scores and real-world observations
   - Handle edge cases (rare defects, missing data)

3. **Interpretability:** Results should:
   - Be explainable to non-technical stakeholders
   - Include clear breakdowns of score components
   - Provide actionable insights (e.g., "Increase HVAC inspections in July")

4. **Integration:** Dashboard should:
   - Load rankings in <2 seconds
   - Allow filtering and sorting
   - Export data for reports
   - Sync with existing risk heatmap and cost analysis pages

---

## REFERENCES & JUSTIFICATION

### Statistical Methods
- **Coefficient of Variation:** Standard measure of relative variability (used in seasonal analysis)
- **Pearson Correlation:** Quantifies linear relationships (temperature sensitivity)
- **Logistic Regression:** Models binary outcomes (defect occurrence probability)
- **McFadden's R²:** Appropriate for categorical outcomes (weather model fit)

### Weighting Rationale
All weights were chosen based on:
1. Domain knowledge (e.g., financial impact is critical in facilities management)
2. Data quality (e.g., higher weight to well-populated fields)
3. Discriminatory power (e.g., features that separate defects effectively)

Weights can be tuned based on stakeholder priorities.

### Normalization Approach
Min-max scaling ensures:
- All components contribute proportionally
- Scores are interpretable (0-100 scale)
- Extreme outliers don't dominate (log transformations applied where needed)

---

## NEXT STEPS

1. **Review this methodology** with your team
2. **Customize weights** based on your priorities
3. **Implement Phase 1** (data preparation)
4. **Build Python scripts** for each algorithm
5. **Validate results** with maintenance staff
6. **Integrate into dashboard**
7. **Document findings** in final report

**Estimated Timeline:** 4 weeks for full implementation and testing

**Team Recommendation:**
- 1 person: Data preparation & database queries
- 1 person: Algorithm implementation (Python)
- 1 person: Dashboard frontend (React)
- 1 person: Validation & documentation

---

## CONCLUSION

These three robust algorithms provide:
- **Explicit mathematical formulations** (no black boxes)
- **Logical justification** for each component
- **Clear, ranked outputs** ready for visualization
- **Actionable insights** for maintenance optimization

Implementing these methods will demonstrate:
1. Deep understanding of the data
2. Rigorous analytical thinking
3. Practical application of data science
4. Value delivery to stakeholders

This approach positions your project for excellent results by transforming raw data into strategic maintenance intelligence.

---

**Document Version:** 1.0
**Last Updated:** April 15, 2026
**Status:** Ready for Implementation
