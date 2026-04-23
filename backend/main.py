#!/usr/bin/env python3
"""
FastAPI Backend for PredicX Dashboard
Serves predictions, data, and model insights
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import joblib
import json
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

app = FastAPI(title="PredicX API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and data on startup
MODEL_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/models/xgboost_upm_predictor.pkl"
DATA_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/data/processed/system_month_data.csv"
IMPORTANCE_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/models/feature_importance.csv"

model = None
df_data = None
feature_importance = None

# SHAP explainability globals
shap_df = None
shap_buildings_meta = None
shap_feature_cols = None

SHAP_MODEL_PATH = PROJECT_ROOT / "models" / "shap_model.pkl"
SHAP_DATA_PATH = PROJECT_ROOT / "data" / "shap" / "shap_values.parquet"
SHAP_META_PATH = PROJECT_ROOT / "data" / "shap" / "buildings_meta.json"
SHAP_FEATURES_PATH = PROJECT_ROOT / "models" / "shap_feature_columns.json"


@app.on_event("startup")
async def load_model_and_data():
    """Load model and data on server start"""
    global model, df_data, feature_importance
    global shap_df, shap_buildings_meta, shap_feature_cols

    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print("✓ Model loaded")

        if os.path.exists(DATA_PATH):
            df_data = pd.read_csv(DATA_PATH)
            print(f"✓ Data loaded: {len(df_data)} records")

        if os.path.exists(IMPORTANCE_PATH):
            feature_importance = pd.read_csv(IMPORTANCE_PATH)
            print("✓ Feature importance loaded")

    except Exception as e:
        print(f"Error loading model/data: {e}")

    # Load SHAP artifacts
    try:
        if SHAP_DATA_PATH.exists():
            shap_df = pd.read_parquet(SHAP_DATA_PATH)
            print(f"✓ SHAP values loaded: {len(shap_df):,} rows")

        if SHAP_META_PATH.exists():
            with open(SHAP_META_PATH) as f:
                shap_buildings_meta = json.load(f)
            print(f"✓ SHAP buildings meta loaded: {len(shap_buildings_meta)} buildings")

        if SHAP_FEATURES_PATH.exists():
            with open(SHAP_FEATURES_PATH) as f:
                shap_feature_cols = json.load(f)
            print(f"✓ SHAP feature columns loaded: {len(shap_feature_cols)} features")

    except Exception as e:
        print(f"Warning: SHAP data not loaded — {e}")


# Response models
class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    data_loaded: bool
    total_records: int


class HeatmapData(BaseModel):
    systems: List[str]
    months: List[int]
    risk_matrix: List[List[float]]


class MonthlyPrediction(BaseModel):
    month: str
    predicted_upm: float
    predicted_ppm: float
    actual_upm: float
    actual_ppm: float


class CostData(BaseModel):
    system: str
    upm_cost: float
    ppm_cost: float
    total_cost: float


class RecurrentDefectData(BaseModel):
    defect_type: str
    count: int
    rank: int


class FeatureImportanceData(BaseModel):
    feature: str
    importance: float


class SummaryStats(BaseModel):
    avg_upm_risk: float
    high_risk_count: int
    total_systems: int
    total_cost: float


# API Endpoints

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "data_loaded": df_data is not None,
        "total_records": len(df_data) if df_data is not None else 0
    }


@app.get("/api/summary", response_model=SummaryStats)
async def get_summary_stats():
    """Get summary statistics"""
    if df_data is None or model is None:
        raise HTTPException(status_code=503, detail="Model or data not loaded")

    # Get feature columns
    with open("/home/sradmin/ai-predictive-maintenance-capstone/models/feature_columns.txt") as f:
        feature_cols = [line.strip() for line in f.readlines()]

    # Make predictions
    X = df_data[feature_cols]
    predictions = model.predict_proba(X)[:, 1]

    avg_risk = float(np.mean(predictions))
    high_risk = int(np.sum(predictions >= 0.7))
    total_systems = int(df_data['system'].nunique())
    total_cost = float(df_data['cost'].sum())

    return {
        "avg_upm_risk": avg_risk,
        "high_risk_count": high_risk,
        "total_systems": total_systems,
        "total_cost": total_cost
    }


@app.get("/api/recurrent-defects", response_model=List[RecurrentDefectData])
async def get_recurrent_defects():
    """Get top recurrent defect types by work order count"""
    if df_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    if 'cluster_name' not in df_data.columns:
        raise HTTPException(status_code=500, detail="cluster_name column not found")

    defect_counts = (
        df_data['cluster_name']
        .dropna()
        .astype(str)
        .str.strip()
    )
    defect_counts = defect_counts[defect_counts != ""].value_counts().head(10)

    result = []
    for rank, (defect_type, count) in enumerate(defect_counts.items(), start=1):
        result.append({
            "defect_type": defect_type,
            "count": int(count),
            "rank": rank
        })

    return result


@app.get("/api/heatmap", response_model=HeatmapData)
async def get_risk_heatmap():
    """Get risk heatmap data (Systems × Months)"""
    if df_data is None or model is None:
        raise HTTPException(status_code=503, detail="Model or data not loaded")

    # Get feature columns
    with open("/home/sradmin/ai-predictive-maintenance-capstone/models/feature_columns.txt") as f:
        feature_cols = [line.strip() for line in f.readlines()]

    # Make predictions
    X = df_data[feature_cols]
    df_data['prediction'] = model.predict_proba(X)[:, 1]

    # Pivot table
    heatmap = df_data.pivot_table(
        index='system',
        columns='month',
        values='prediction',
        aggfunc='mean'
    )

    # Sort by average risk
    heatmap['avg'] = heatmap.mean(axis=1)
    heatmap = heatmap.sort_values('avg', ascending=False).drop('avg', axis=1)

    # Take top 15
    heatmap = heatmap.head(15)

    # Fill missing months with 0
    for month in range(1, 13):
        if month not in heatmap.columns:
            heatmap[month] = 0.0

    heatmap = heatmap[sorted(heatmap.columns)]

    return {
        "systems": heatmap.index.tolist(),
        "months": list(range(1, 13)),
        "risk_matrix": heatmap.fillna(0).values.tolist()
    }


@app.get("/api/monthly-predictions", response_model=List[MonthlyPrediction])
async def get_monthly_predictions():
    """Get monthly UPM/PPM predictions"""
    if df_data is None or model is None:
        raise HTTPException(status_code=503, detail="Model or data not loaded")

    # Get feature columns
    with open("/home/sradmin/ai-predictive-maintenance-capstone/models/feature_columns.txt") as f:
        feature_cols = [line.strip() for line in f.readlines()]

    # Make predictions
    X = df_data[feature_cols]
    df_data['prediction'] = model.predict_proba(X)[:, 1]

    # Calculate predicted UPM/PPM counts
    df_data['pred_upm'] = df_data['total_count'] * df_data['prediction']
    df_data['pred_ppm'] = df_data['total_count'] * (1 - df_data['prediction'])

    # Group by year-month
    df_data['year_month'] = df_data['year'].astype(str) + '-' + df_data['month'].astype(str).str.zfill(2)

    monthly = df_data.groupby('year_month').agg({
        'pred_upm': 'sum',
        'pred_ppm': 'sum',
        'upm_count': 'sum',
    }).reset_index()

    monthly['actual_ppm'] = monthly['upm_count'] * 0  # Placeholder

    result = []
    for _, row in monthly.iterrows():
        result.append({
            "month": row['year_month'],
            "predicted_upm": float(row['pred_upm']),
            "predicted_ppm": float(row['pred_ppm']),
            "actual_upm": float(row['upm_count']),
            "actual_ppm": 0.0  # Placeholder
        })

    return result


@app.get("/api/cost-analysis", response_model=List[CostData])
async def get_cost_analysis():
    """Get cost breakdown by system"""
    if df_data is None or model is None:
        raise HTTPException(status_code=503, detail="Model or data not loaded")

    # Get feature columns
    with open("/home/sradmin/ai-predictive-maintenance-capstone/models/feature_columns.txt") as f:
        feature_cols = [line.strip() for line in f.readlines()]

    # Make predictions
    X = df_data[feature_cols]
    df_data['prediction'] = model.predict_proba(X)[:, 1]

    # Calculate costs
    df_data['upm_cost'] = df_data['cost'] * df_data['prediction']
    df_data['ppm_cost'] = df_data['cost'] * (1 - df_data['prediction'])

    # Group by system
    system_costs = df_data.groupby('system').agg({
        'upm_cost': 'sum',
        'ppm_cost': 'sum'
    }).reset_index()

    system_costs['total_cost'] = system_costs['upm_cost'] + system_costs['ppm_cost']
    system_costs = system_costs.sort_values('total_cost', ascending=False).head(10)

    result = []
    for _, row in system_costs.iterrows():
        result.append({
            "system": row['system'],
            "upm_cost": float(row['upm_cost']),
            "ppm_cost": float(row['ppm_cost']),
            "total_cost": float(row['total_cost'])
        })

    return result


@app.get("/api/feature-importance", response_model=List[FeatureImportanceData])
async def get_feature_importance():
    """Get feature importance data"""
    if feature_importance is None:
        raise HTTPException(status_code=503, detail="Feature importance not loaded")

    result = []
    for _, row in feature_importance.head(15).iterrows():
        result.append({
            "feature": row['feature'],
            "importance": float(row['importance'])
        })

    return result


# ─────────────────────────────────────────────────────────────────────────────
# SHAP Explainability Endpoints
# ─────────────────────────────────────────────────────────────────────────────

# Human-readable labels and units for each feature
FEATURE_META = {
    'min_temp':           {'label': 'Min Temperature',       'unit': '°C'},
    'max_temp':           {'label': 'Max Temperature',       'unit': '°C'},
    'avg_temp':           {'label': 'Avg Temperature',       'unit': '°C'},
    'temp_range':         {'label': 'Temp Range',            'unit': '°C'},
    'humidity':           {'label': 'Humidity',              'unit': '%'},
    'precipitation':      {'label': 'Precipitation',         'unit': 'mm'},
    'snow':               {'label': 'Snowfall',              'unit': 'mm'},
    'cloudness':          {'label': 'Cloud Cover',           'unit': '%'},
    'fci':                {'label': 'Facility Condition Index', 'unit': ''},
    'building_age':       {'label': 'Building Age',          'unit': 'yrs'},
    'size':               {'label': 'Building Size',         'unit': 'sqm'},
    'upm_last_1m':        {'label': 'UPM Last 1 Month',      'unit': 'events'},
    'upm_last_3m':        {'label': 'UPM Last 3 Months',     'unit': 'events'},
    'upm_last_6m':        {'label': 'UPM Last 6 Months',     'unit': 'events'},
    'months_since_upm':   {'label': 'Months Since Last UPM', 'unit': 'months'},
    'avg_labor_hours':    {'label': 'Avg Labor Hours',       'unit': 'hrs'},
    'avg_wo_duration':    {'label': 'Avg WO Duration',       'unit': 'days'},
    'wo_count':           {'label': 'Work Order Count',      'unit': 'WOs'},
    'avg_total_cost':     {'label': 'Avg WO Cost',           'unit': '$'},
    'total_monthly_cost': {'label': 'Total Monthly Cost',    'unit': '$'},
    'month_sin':          {'label': 'Seasonality (sin)',      'unit': ''},
    'month_cos':          {'label': 'Seasonality (cos)',      'unit': ''},
    'season':             {'label': 'Season',                'unit': ''},
}
SEASON_NAMES = ['Winter', 'Spring', 'Summer', 'Fall']


def _format_feature_value(feat: str, value: float) -> str:
    if feat == 'season':
        idx = int(round(value))
        return SEASON_NAMES[max(0, min(3, idx))]
    meta = FEATURE_META.get(feat)
    if meta is None:
        return str(round(value, 3))
    unit = meta['unit']
    if unit == '$':
        return f"${value:,.0f}"
    elif unit in ('°C',):
        return f"{value:.1f}{unit}"
    elif unit in ('%',):
        return f"{value:.1f}{unit}"
    elif unit == '':
        return f"{value:.4f}"
    else:
        return f"{value:.1f} {unit}"


def _build_contributors(row: pd.Series, feature_cols: list, top_n: int = 10) -> list:
    contributors = []
    for feat in feature_cols:
        shap_col = f'shap_{feat}'
        val_col = f'val_{feat}'
        if shap_col not in row.index:
            continue
        sv = float(row[shap_col])
        fv = float(row[val_col]) if val_col in row.index else 0.0

        # Skip tiny-impact features and subsystem "Not active" (one-hot = 0)
        if feat.startswith('subsystem_') and fv == 0:
            continue

        if feat.startswith('subsystem_'):
            label = feat.replace('subsystem_', 'System: ')
            display_val = 'Active'
        else:
            meta = FEATURE_META.get(feat, {'label': feat, 'unit': ''})
            label = meta['label']
            display_val = _format_feature_value(feat, fv)

        # Merge month_sin / month_cos into one entry
        if feat in ('month_sin', 'month_cos'):
            label = 'Seasonal Pattern'

        contributors.append({
            'feature': feat,
            'label': label,
            'shap_value': round(sv, 4),
            'feature_value': round(fv, 4),
            'display_value': display_val,
            'direction': 'increases' if sv > 0 else 'decreases',
        })

    # Merge month_sin + month_cos SHAP by summing
    seasonal = [c for c in contributors if c['label'] == 'Seasonal Pattern']
    others = [c for c in contributors if c['label'] != 'Seasonal Pattern']
    if seasonal:
        merged_sv = sum(c['shap_value'] for c in seasonal)
        others.append({
            'feature': 'seasonality',
            'label': 'Seasonal Pattern',
            'shap_value': round(merged_sv, 4),
            'feature_value': None,
            'display_value': '',
            'direction': 'increases' if merged_sv > 0 else 'decreases',
        })

    # Sort by absolute SHAP value, return top N
    others.sort(key=lambda c: abs(c['shap_value']), reverse=True)
    return others[:top_n]


@app.get("/api/shap/buildings")
async def get_shap_buildings():
    """List of buildings in University 1 with available year/month combinations."""
    if shap_buildings_meta is None:
        raise HTTPException(status_code=503, detail="SHAP data not loaded — run prepare_shap_data.py and train_shap_model.py first")
    return shap_buildings_meta


@app.get("/api/shap/explain")
async def get_shap_explanation(
    building_id: str = Query(..., description="Building ID"),
    year: int = Query(..., description="Year (e.g. 2019)"),
    month: int = Query(..., description="Month number 1-12"),
):
    """
    Return SHAP contributors for every subsystem in the given building / year / month.
    Each subsystem entry includes its risk probability and the top 10 feature contributors.
    """
    if shap_df is None or shap_feature_cols is None:
        raise HTTPException(status_code=503, detail="SHAP data not loaded — run pipeline scripts first")

    subset = shap_df[
        (shap_df['BuildingID'].astype(str) == str(building_id)) &
        (shap_df['year'] == year) &
        (shap_df['month'] == month)
    ]

    if subset.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data for building={building_id}, year={year}, month={month}"
        )

    building_name = str(subset['BuildingName'].iloc[0]) if 'BuildingName' in subset.columns else building_id

    SEP = '|||'

    def split_descriptions(val):
        if not val or not isinstance(val, str):
            return []
        return [d.strip() for d in val.split(SEP) if d.strip()]

    subsystems = []
    for _, row in subset.iterrows():
        contributors = _build_contributors(row, shap_feature_cols, top_n=10)
        subsystems.append({
            'subsystem': str(row['SubsystemDescription']),
            'risk_prob': round(float(row['risk_prob']), 4),
            'shap_base': round(float(row['shap_base']), 4),
            'contributors': contributors,
            'this_month_upm': split_descriptions(row.get('upm_descriptions', '')),
            'this_month_ppm': split_descriptions(row.get('ppm_descriptions', '')),
            'hist_upm': split_descriptions(row.get('hist_upm_descriptions', '')),
            'hist_ppm': split_descriptions(row.get('hist_ppm_descriptions', '')),
        })

    # Sort by risk probability descending
    subsystems.sort(key=lambda s: s['risk_prob'], reverse=True)

    return {
        'building_id': building_id,
        'building_name': building_name,
        'year': year,
        'month': month,
        'subsystems': subsystems,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
