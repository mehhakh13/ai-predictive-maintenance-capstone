# PredicX - Predictive Maintenance Dashboard (MVP)

**Explainable AI-Powered Risk Intelligence Platform for Smart Campuses**

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Supabase

Create a `.env` file in the project root:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

### 3. Ensure Supabase Tables Exist

Make sure these tables are populated in Supabase:
- `fmucd_canada`
- `fmucd_california`

### 4. Run the Complete Pipeline

**Option A: Run everything automatically**
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

**Option B: Run steps manually**
```bash
# Step 1: Feature Engineering
python scripts/feature_engineering.py

# Step 2: Train XGBoost Model
python scripts/train_model.py

# Step 3: Launch Dashboard
streamlit run dashboard/app.py
```

## Dashboard Features

### 1. Risk Heatmap (Systems × Months)
- Visual grid showing UPM risk for each system across months
- Color-coded: Red = High Risk, Yellow = Medium, Green = Low
- Helps identify seasonal patterns

### 2. Monthly UPM/PPM Predictions
- Time series forecast of maintenance work orders
- Predicted vs actual comparison
- Trend analysis

### 3. Projected Cost Dashboard
- Financial impact analysis
- Cost breakdown by system type
- Monthly cost trends
- Potential savings calculation

### 4. SHAP Explainability
- Top 15 most important features
- Feature impact breakdown:
  - Temporal factors (month, season)
  - Weather factors (temperature, snow, humidity)
  - System factors (system type)
  - Historical factors (failure rates)

## Architecture

```
PredicX MVP
│
├── scripts/
│   ├── feature_engineering.py  # Load from Supabase + feature creation
│   └── train_model.py           # XGBoost training
│
├── dashboard/
│   └── app.py                   # Streamlit dashboard
│
├── data/processed/              # Generated during pipeline
│   ├── X_features.csv
│   ├── y_target.csv
│   └── metadata.csv
│
└── models/                      # Generated during training
    ├── xgboost_upm_predictor.pkl
    └── feature_importance.csv
```

## Model Details

- **Algorithm**: XGBoost Classifier
- **Target**: UPM probability (binary: UPM vs PPM)
- **Granularity**: System-Month level
- **Features**: 30+ engineered features including:
  - Temporal: month, season, quarter
  - Weather: temperature, humidity, snow, precipitation
  - Historical: rolling failure rates
  - System: one-hot encoded system types
  - Cost: average costs, labor hours
  - Building: size, age, facility condition index

## Data Flow

1. **Load from Supabase** → Raw work order data
2. **Feature Engineering** → System-month aggregations
3. **Model Training** → XGBoost classifier
4. **Predictions** → UPM probability scores
5. **Dashboard** → 4 interactive visualizations

## Customization

### Change Data Source
Edit `scripts/feature_engineering.py`:
```python
# Load both Canada and California
main(table_names=["fmucd_canada", "fmucd_california"])

# Or limit rows for testing
main(table_names=["fmucd_canada"], limit_per_table=10000)
```

### Adjust Model Parameters
Edit `scripts/train_model.py`:
```python
params = {
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 200,
    # ... adjust as needed
}
```

## Troubleshooting

### "Model or data not found"
- Run feature engineering first: `python scripts/feature_engineering.py`
- Then train model: `python scripts/train_model.py`

### Supabase connection issues
- Check `.env` file exists and has correct credentials
- Verify Supabase tables exist and are populated

### Out of memory
- Reduce data: `main(limit_per_table=50000)` in feature_engineering.py
- Use smaller batch sizes in Supabase queries

## Future Enhancements

- [ ] Real-time SHAP waterfall plots for individual predictions
- [ ] What-if simulator (cold wave / heat wave scenarios)
- [ ] Building-specific risk drilldowns
- [ ] Automatic retraining pipeline
- [ ] Integration with weather forecast APIs
- [ ] Alert system for high-risk predictions

## Team

**Group 09** - AI Predictive Maintenance Capstone Project

## Tech Stack

- **ML**: XGBoost, scikit-learn, SHAP
- **Dashboard**: Streamlit, Plotly
- **Database**: Supabase (PostgreSQL)
- **Language**: Python 3.9+
