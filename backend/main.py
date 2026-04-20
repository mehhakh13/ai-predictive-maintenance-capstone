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
# CHAT ASSISTANT ENDPOINT (Phase 1: Keyword-based)
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []
    filters: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str]
    data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None

def analyze_query_intent(message: str) -> Dict[str, Any]:
    """
    Analyze user message and determine intent + entities
    Priority order: cost > risk > building > trend > defect > recommendation
    """
    msg_lower = message.lower()

    intent = {
        'type': 'general',
        'entities': {
            'metric': None,
            'system': None,
            'building': None,
            'time_period': None,
            'defect_type': None
        }
    }

    # Priority-based intent detection (order matters!)
    # 1. Cost analysis (highest priority for cost-related queries)
    if any(word in msg_lower for word in ['cost', 'expensive', 'price', 'money', 'budget', '$', 'spend']):
        intent['type'] = 'cost_analysis'

    # 2. Risk analysis
    elif any(word in msg_lower for word in ['risk', 'predict', 'probability', 'likely', 'failure rate', 'dangerous']):
        intent['type'] = 'risk_analysis'

    # 3. Building-specific queries
    elif any(word in msg_lower for word in ['building', 'location', 'where', 'which building', 'facility']):
        intent['type'] = 'building_analysis'

    # 4. Trend analysis
    elif any(word in msg_lower for word in ['trend', 'over time', 'monthly', 'timeline', 'history', 'recent', 'last month']):
        intent['type'] = 'trend_analysis'

    # 5. Recommendations
    elif any(word in msg_lower for word in ['recommend', 'suggest', 'should', 'priority', 'what to do', 'next steps']):
        intent['type'] = 'recommendation'

    # 6. Defect/problem queries (lower priority - many queries have these words)
    elif any(word in msg_lower for word in ['defect', 'problem', 'issue', 'broken', 'common', 'frequent']):
        intent['type'] = 'defect_intelligence'

    # 7. System-specific queries
    elif any(word in msg_lower for word in ['system', 'hvac', 'electrical', 'plumbing', 'lighting']):
        intent['type'] = 'defect_intelligence'  # Show systems as defects

    # Detect metrics
    if any(word in msg_lower for word in ['top', 'highest', 'most', 'worst']):
        intent['entities']['metric'] = 'top'
    elif any(word in msg_lower for word in ['lowest', 'least', 'best', 'cheapest']):
        intent['entities']['metric'] = 'bottom'

    # Detect systems
    systems = ['hvac', 'electrical', 'plumbing', 'lighting', 'elevator', 'heating', 'cooling']
    for sys in systems:
        if sys in msg_lower:
            intent['entities']['system'] = sys

    print(f"[DEBUG] Query: '{message}' -> Intent: {intent['type']}")
    return intent

def generate_response(intent: Dict[str, Any], filters: Dict = {}) -> ChatResponse:
    """
    Generate response based on intent and available data
    """
    intent_type = intent['type']

    try:
        # COST ANALYSIS
        if intent_type == 'cost_analysis':
            if df_defect_summary is not None:
                top_costs = df_defect_summary.nlargest(5, 'total_cost')

                response = "💰 **Top 5 Most Expensive Defect Categories:**\n\n"
                chart_data = []

                for idx, row in top_costs.iterrows():
                    cost = row['total_cost']
                    count = row['count']
                    category = row['defect_category']
                    response += f"**{idx+1}. {category}**\n"
                    response += f"   • Total Cost: ${cost:,.0f}\n"
                    response += f"   • Occurrences: {count:,}\n"
                    response += f"   • Avg Cost: ${row['avg_cost']:,.0f}\n\n"

                    chart_data.append({
                        'category': category[:30],
                        'total_cost': float(cost),
                        'count': int(count)
                    })

                return ChatResponse(
                    response=response,
                    suggestions=[
                        "Show me HVAC cost breakdown",
                        "Which buildings have highest costs?",
                        "How can we reduce maintenance costs?"
                    ],
                    data={'chart_data': chart_data},
                    chart_type='cost_bar'
                )

        # RISK ANALYSIS
        elif intent_type == 'risk_analysis':
            if df_impact_summary is not None:
                # Sort by average risk probability (show top risky systems)
                high_risk = df_impact_summary.nlargest(5, 'avg_risk')

                response = "⚠️ **Top 5 Highest Risk Systems:**\n\n"

                for idx, (_, row) in enumerate(high_risk.iterrows(), 1):
                    category = row['defect_category']
                    avg_risk = row['avg_risk'] * 100  # Convert to percentage
                    count = row['count']
                    total_cost = row['total_cost']

                    response += f"**{idx}. {category}**\n"
                    response += f"   • Risk Probability: {avg_risk:.1f}%\n"
                    response += f"   • UPM Events: {count:,}\n"
                    response += f"   • Estimated Cost: ${total_cost:,.0f}\n\n"

                return ChatResponse(
                    response=response,
                    suggestions=[
                        "What's driving these risks?",
                        "Show me risk trends over time",
                        "Which buildings have highest risk?"
                    ]
                )

        # DEFECT INTELLIGENCE
        elif intent_type == 'defect_intelligence':
            if df_defect_summary is not None:
                top_defects = df_defect_summary.nlargest(5, 'count')

                response = "🔧 **Most Frequent Defect Types:**\n\n"

                for idx, row in top_defects.iterrows():
                    category = row['defect_category']
                    count = row['count']
                    pct = row['percentage']
                    response += f"**{idx+1}. {category}**\n"
                    response += f"   • Occurrences: {count:,} ({pct:.1f}%)\n"
                    response += f"   • Avg Cost: ${row['avg_cost']:,.0f}\n\n"

                return ChatResponse(
                    response=response,
                    suggestions=[
                        "Show me defect trends",
                        "Which buildings have most defects?",
                        "How do we prevent these issues?"
                    ]
                )

        # TREND ANALYSIS
        elif intent_type == 'trend_analysis':
            if df_monthly_defect is not None:
                recent_months = df_monthly_defect.sort_values('month', ascending=False).head(6)

                response = "📈 **Recent Defect Trends (Last 6 Months):**\n\n"

                total_recent = recent_months['count'].sum()
                total_cost_recent = recent_months['total_cost'].sum()

                response += f"• Total Defects: {total_recent:,}\n"
                response += f"• Total Cost: ${total_cost_recent:,.0f}\n"
                response += f"• Average per Month: {total_recent/6:,.0f} defects\n\n"

                response += "**Monthly Breakdown:**\n"
                for _, row in recent_months.iterrows():
                    response += f"• {row['month']}: {row['count']:,} defects (${row['total_cost']:,.0f})\n"

                return ChatResponse(
                    response=response,
                    suggestions=[
                        "What's the trend for HVAC defects?",
                        "Compare this year vs last year",
                        "Forecast next month's defects"
                    ]
                )

        # BUILDING ANALYSIS
        elif intent_type == 'building_analysis':
            if df_building_defect is not None:
                # Sort by impact score (total_impact column)
                building_summary = df_building_defect.sort_values('total_impact', ascending=False).head(5)

                response = "🏢 **Top 5 Buildings by Maintenance Impact:**\n\n"

                for idx, row in building_summary.iterrows():
                    bldg_name = row.get('building_name', row.get('BuildingName', row.get('BuildingID', 'Unknown')))
                    uni_name = row.get('university_name', f"University {row.get('UniversityID', 'Unknown')}")

                    response += f"**{building_summary.index.get_loc(idx)+1}. {bldg_name}** ({uni_name})\n"
                    response += f"   • Total Events: {int(row['count']):,}\n"
                    response += f"   • Total Cost: ${row['total_cost']:,.0f}\n"
                    response += f"   • Risk Score: {row['total_impact']:.2f}\n\n"

                return ChatResponse(
                    response=response,
                    suggestions=[
                        "What systems fail most in this building?",
                        "Show me monthly trends for buildings",
                        "Which university has the most issues?"
                    ]
                )

        # RECOMMENDATION
        elif intent_type == 'recommendation':
            response = "💡 **Maintenance Recommendations:**\n\n"

            if df_impact_summary is not None:
                critical = df_impact_summary[df_impact_summary['risk_level'] == 'Critical'].head(3)

                response += "**Priority Actions:**\n"
                for idx, row in critical.iterrows():
                    response += f"{idx+1}. Address **{row['defect_category']}**\n"
                    response += f"   • {row['count']:,} cases with ${row['total_cost']:,.0f} in costs\n"

                response += "\n**Suggested Focus Areas:**\n"
                response += "• Implement preventive maintenance for high-frequency defects\n"
                response += "• Allocate budget to critical risk categories\n"
                response += "• Schedule inspections for buildings with highest impact scores\n"

            return ChatResponse(
                response=response,
                suggestions=[
                    "What's the ROI of preventive maintenance?",
                    "Create a maintenance schedule",
                    "Show me budget optimization options"
                ]
            )

    except Exception as e:
        print(f"Error generating response: {e}")

    # DEFAULT RESPONSE
    response = """👋 **Hello! I'm your Maintenance Intelligence Assistant.**

I can help you analyze:
• 💰 **Cost Analysis** - Find expensive defects and cost drivers
• ⚠️ **Risk Predictions** - Identify high-risk systems
• 🔧 **Defect Patterns** - Analyze failure trends
• 🏢 **Building Insights** - Compare building performance
• 📈 **Trends** - Track changes over time
• 💡 **Recommendations** - Get maintenance suggestions

**Try asking:**
• "What are the most expensive defects?"
• "Show me high-risk systems"
• "Which buildings need attention?"
• "What's trending this month?"
"""

    return ChatResponse(
        response=response,
        suggestions=[
            "What are the most expensive defects?",
            "Show me high-risk systems",
            "Which buildings have most issues?",
            "What defects are trending?"
        ]
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_assistant(request: ChatRequest):
    """
    Chat assistant endpoint - Phase 1 (keyword-based)
    """
    try:
        # Analyze user message
        intent = analyze_query_intent(request.message)

        # Generate response
        response = generate_response(intent, request.filters)

        return response

    except Exception as e:
        print(f"Chat error: {e}")
        return ChatResponse(
            response=f"I encountered an error processing your request. Please try rephrasing your question.",
            suggestions=[
                "What are the most expensive defects?",
                "Show me high-risk systems",
                "Help"
            ]
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
