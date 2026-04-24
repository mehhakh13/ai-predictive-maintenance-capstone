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
from schemas.chat_models import ChatRequest, ChatResponse
from services.data_service import get_data_service
from services.session_manager import get_session_manager
import config

# Choose LLM backend based on configuration
if config.USE_OLLAMA:
    from services.ollama_service import get_ollama_service as get_llm_service
    print("✓ Using Ollama (Local/Free)")
else:
    from services.llm_service import get_llm_service
    print("✓ Using Claude API")

app = FastAPI(title="PredicX API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and data on startup
MODEL_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/models/xgboost_upm_predictor.pkl"
DATA_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/data/processed/system_month_data.csv"
IMPORTANCE_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/models/feature_importance.csv"
PREDICTIONS_PATH = "/home/sradmin/ai-predictive-maintenance-capstone/data/processed/predictions_with_metadata.parquet"

model = None
df_data = None
feature_importance = None
df_predictions = None
df_defect_summary = None
df_impact_summary = None
df_monthly_defect = None
df_building_defect = None


@app.on_event("startup")
async def load_model_and_data():
    """Load model and data on server start"""
    global model, df_data, feature_importance, df_predictions
    global df_defect_summary, df_impact_summary, df_monthly_defect, df_building_defect

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

        # Load predictions data for chat assistant
        if os.path.exists(PREDICTIONS_PATH):
            df_predictions = pd.read_parquet(PREDICTIONS_PATH)
            print(f"✓ Predictions data loaded: {len(df_predictions)} records")

            # Prepare summary data for chat assistant
            # Estimate cost based on UPM events (simplified for now)
            df_predictions['estimated_cost'] = df_predictions['UPM_total_event'] * 500  # $500 per UPM event estimate

            if 'SubsystemDescription' in df_predictions.columns:
                df_defect_summary = df_predictions.groupby('SubsystemDescription').agg({
                    'estimated_cost': ['sum', 'mean'],
                    'UPM_total_event': 'sum',
                    'risk_prob_asset': 'mean'
                }).reset_index()
                df_defect_summary.columns = ['defect_category', 'total_cost', 'avg_cost', 'count', 'avg_risk']
                df_defect_summary['count'] = df_defect_summary['count'].astype(int)
                df_defect_summary['percentage'] = (df_defect_summary['count'] / df_defect_summary['count'].sum()) * 100
                df_defect_summary = df_defect_summary.sort_values('total_cost', ascending=False)
                print(f"✓ Defect summary created: {len(df_defect_summary)} categories")

            # Create impact summary based on risk probability
            if 'SubsystemDescription' in df_predictions.columns and 'risk_prob_asset' in df_predictions.columns:
                df_impact_summary = df_predictions.groupby('SubsystemDescription').agg({
                    'risk_prob_asset': ['mean', 'max'],
                    'estimated_cost': 'sum',
                    'UPM_total_event': 'sum'
                }).reset_index()
                df_impact_summary.columns = ['defect_category', 'avg_risk', 'max_risk', 'total_cost', 'count']
                df_impact_summary['count'] = df_impact_summary['count'].astype(int)
                df_impact_summary['total_impact'] = df_impact_summary['avg_risk'] * df_impact_summary['count']
                df_impact_summary['risk_level'] = pd.cut(
                    df_impact_summary['avg_risk'],
                    bins=[-np.inf, 0.3, 0.6, np.inf],
                    labels=['Low', 'Medium', 'Critical']
                )
                print(f"✓ Impact summary created")

            # Create monthly summary
            if 'month_date' in df_predictions.columns:
                df_monthly_defect = df_predictions.groupby('month_date').agg({
                    'estimated_cost': 'sum',
                    'UPM_total_event': 'sum',
                    'risk_prob_asset': 'mean'
                }).reset_index()
                df_monthly_defect.columns = ['month', 'total_cost', 'count', 'avg_risk']
                df_monthly_defect['count'] = df_monthly_defect['count'].astype(int)
                df_monthly_defect = df_monthly_defect.sort_values('month')
                print(f"✓ Monthly defect data created")

            # Create building summary
            if 'BuildingID' in df_predictions.columns:
                group_cols = ['BuildingID']
                if 'BuildingName' in df_predictions.columns:
                    group_cols.append('BuildingName')
                if 'UniversityID' in df_predictions.columns:
                    group_cols.append('UniversityID')

                df_building_defect = df_predictions.groupby(group_cols).agg({
                    'UPM_total_event': 'sum',
                    'estimated_cost': 'sum',
                    'risk_prob_asset': 'mean'
                }).reset_index()

                cols = [*group_cols, 'count', 'total_cost', 'total_impact']
                df_building_defect.columns = cols
                df_building_defect['count'] = df_building_defect['count'].astype(int)

                # Add university_name column for compatibility
                if 'UniversityID' in df_building_defect.columns:
                    df_building_defect['university_name'] = 'University ' + df_building_defect['UniversityID'].astype(str)
                if 'BuildingName' in df_building_defect.columns:
                    df_building_defect['building_name'] = df_building_defect['BuildingName']
                elif 'BuildingID' in df_building_defect.columns:
                    df_building_defect['building_name'] = df_building_defect['BuildingID']

                print(f"✓ Building defect data created")

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


@app.get("/api/debug/chat-data")
async def debug_chat_data():
    """Debug endpoint to check chat data status"""
    return {
        "df_predictions_loaded": df_predictions is not None,
        "df_predictions_rows": len(df_predictions) if df_predictions is not None else 0,
        "df_defect_summary_loaded": df_defect_summary is not None,
        "df_defect_summary_rows": len(df_defect_summary) if df_defect_summary is not None else 0,
        "df_impact_summary_loaded": df_impact_summary is not None,
        "df_monthly_defect_loaded": df_monthly_defect is not None,
        "df_building_defect_loaded": df_building_defect is not None,
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


# ============================================================================
# PHASE 2: AI-POWERED CHAT with Session Management
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_assistant(request: ChatRequest):
    """
    AI-powered chat assistant with conversation history
    Uses Claude API with function calling for intelligent responses
    """
    try:
        # Get or create session
        session_manager = get_session_manager()
        session = session_manager.get_or_create_session(request.session_id)

        # Add user message to session
        session.add_message("user", request.message)

        # Get LLM service
        llm_service = get_llm_service()

        # Get conversation history (limit to last 10 messages for context window)
        conversation_history = session.get_history(limit=10)

        # Call Claude API with function calling
        result = llm_service.chat(
            user_message=request.message,
            conversation_history=conversation_history[:-1]  # Exclude current message (already in user_message)
        )

        # Add assistant response to session
        session.add_message("assistant", result["response"])

        # Return response with session ID
        return ChatResponse(
            response=result["response"],
            suggestions=result["suggestions"],
            session_id=session.session_id,  # Return session ID for frontend
            data=result.get("data"),
            chart_type=result.get("chart_type"),
            function_calls=result.get("function_calls", [])
        )

    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()

        return ChatResponse(
            response="I encountered an error processing your request. Please try again or rephrase your question.",
            suggestions=[
                "What are the most expensive systems?",
                "Show me high-risk systems",
                "Which buildings need attention?"
            ]
        )


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/sessions")
async def list_sessions():
    """List all chat sessions"""
    session_manager = get_session_manager()
    return {"sessions": session_manager.list_sessions()}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session with full conversation history"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


@app.post("/api/sessions")
async def create_session():
    """Create a new chat session"""
    session_manager = get_session_manager()
    session = session_manager.create_session()

    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat()
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    session_manager = get_session_manager()
    success = session_manager.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "deleted", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
