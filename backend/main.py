#!/usr/bin/env python3
"""
FastAPI Backend for PredicX Dashboard
Serves predictions, data, and model insights
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

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


@app.on_event("startup")
async def load_model_and_data():
    """Load model and data on server start"""
    global model, df_data, feature_importance

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
