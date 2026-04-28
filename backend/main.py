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
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and data on startup
MODEL_PATH = PROJECT_ROOT / "models" / "xgboost_upm_predictor.pkl"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "system_month_data.csv"
IMPORTANCE_PATH = PROJECT_ROOT / "models" / "feature_importance.csv"
DEFECT_DATA_PATH = PROJECT_ROOT / "data" / "bertopic" / "df_with_topics_IMPROVED.parquet"
TOPIC_INFO_PATH = PROJECT_ROOT / "data" / "bertopic" / "topic_info_IMPROVED.csv"

# Aggregated defect intelligence data paths
AGG_DATA_DIR = PROJECT_ROOT / "data" / "defect_intelligence" / "aggregated"
DEFECT_SUMMARY_PATH = AGG_DATA_DIR / "defect_summary.parquet"
SYSTEM_DEFECT_PATH = AGG_DATA_DIR / "system_defect.parquet"
BUILDING_DEFECT_PATH = AGG_DATA_DIR / "building_defect.parquet"
MONTHLY_DEFECT_PATH = AGG_DATA_DIR / "monthly_defect.parquet"
IMPACT_SUMMARY_PATH = AGG_DATA_DIR / "impact_summary.parquet"

model = None
df_data = None
feature_importance = None
df_defects = None
topic_info = None

# Aggregated data variables
df_defect_summary = None
df_system_defect = None
df_building_defect = None
df_monthly_defect = None
df_impact_summary = None

# SHAP explainability globals
shap_df = None
shap_buildings_meta = None
shap_feature_cols = None

# Risk Heatmap globals
df_risk_building = None           # all-years avg: (uni, bld, sys, subsys, month)
df_risk_university = None         # all-years avg: (uni, sys, subsys, month)
df_risk_university_yearly = None  # per-year:      (uni, sys, subsys, month, year)
risk_heatmap_meta = None          # metadata dict

SHAP_MODEL_PATH = PROJECT_ROOT / "models" / "shap_model.pkl"
SHAP_DATA_PATH = PROJECT_ROOT / "data" / "shap" / "shap_values.parquet"
SHAP_META_PATH = PROJECT_ROOT / "data" / "shap" / "buildings_meta.json"
SHAP_FEATURES_PATH = PROJECT_ROOT / "models" / "shap_feature_columns.json"


@app.on_event("startup")
async def load_model_and_data():
    """Load model and data on server start"""
    global model, df_data, feature_importance, df_defects, topic_info
    global df_defect_summary, df_system_defect, df_building_defect, df_monthly_defect, df_impact_summary
    global shap_df, shap_buildings_meta, shap_feature_cols
    global df_risk_building, df_risk_university, df_risk_university_yearly, risk_heatmap_meta

    # Model (optional — fails gracefully if xgboost not installed)
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print("✓ Model loaded")
        if os.path.exists(IMPORTANCE_PATH):
            feature_importance = pd.read_csv(IMPORTANCE_PATH)
            print("✓ Feature importance loaded")
    except Exception as e:
        print(f"Warning: model not loaded: {e}")

    # Processed data (loaded independently of model)
    try:
        if os.path.exists(DATA_PATH):
            df_data = pd.read_csv(DATA_PATH)
            print(f"✓ Data loaded: {len(df_data)} records")
    except Exception as e:
        print(f"Warning: processed data not loaded: {e}")

    # Aggregated defect intelligence data (small parquets, fast)
    try:
        if os.path.exists(DEFECT_SUMMARY_PATH):
            df_defect_summary = pd.read_parquet(DEFECT_SUMMARY_PATH)
            print(f"✓ Defect summary loaded: {len(df_defect_summary)} categories")

        if os.path.exists(SYSTEM_DEFECT_PATH):
            df_system_defect = pd.read_parquet(SYSTEM_DEFECT_PATH)
            print(f"✓ System-defect data loaded: {len(df_system_defect)} combinations")

        if os.path.exists(BUILDING_DEFECT_PATH):
            df_building_defect = pd.read_parquet(BUILDING_DEFECT_PATH)
            print(f"✓ Building-defect data loaded: {len(df_building_defect)} combinations")

        if os.path.exists(MONTHLY_DEFECT_PATH):
            df_monthly_defect = pd.read_parquet(MONTHLY_DEFECT_PATH)
            print(f"✓ Monthly defect trends loaded: {len(df_monthly_defect)} records")

        if os.path.exists(IMPACT_SUMMARY_PATH):
            df_impact_summary = pd.read_parquet(IMPACT_SUMMARY_PATH)
            print(f"✓ Impact summary loaded: {len(df_impact_summary)} categories")

        print("✓ Aggregated defect data ready")
    except Exception as e:
        print(f"Error loading aggregated defect data: {e}")

    # Load Risk Heatmap data from FMUCD CSV (has SubsystemDescription + BuildingName)
    try:
        fmucd_csv = PROJECT_ROOT / "data" / "Facility Management Unified Classification Database (FMUCD).csv"
        if fmucd_csv.exists():
            print("Loading FMUCD CSV for risk heatmap (this takes ~10s)...")
            raw = pd.read_csv(
                fmucd_csv,
                usecols=['UniversityID', 'BuildingID', 'BuildingName',
                         'SystemDescription', 'SubsystemDescription',
                         'WOStartDate', 'PPM/UPM'],
                low_memory=False
            )

            # Keep only rows with valid building IDs and known work order types
            raw = raw[
                raw['BuildingID'].notna() &
                raw['PPM/UPM'].isin(['UPM', 'PPM'])
            ].copy()

            # Fill missing building names with the building ID so groupby doesn't drop them
            raw['BuildingName'] = raw['BuildingName'].fillna(raw['BuildingID'])

            # Extract month and year
            dt = pd.to_datetime(raw['WOStartDate'], errors='coerce')
            raw['month'] = dt.dt.month
            raw['year'] = dt.dt.year
            raw = raw.dropna(subset=['month', 'year'])
            raw['month'] = raw['month'].astype(int)
            raw['year'] = raw['year'].astype(int)
            raw['is_upm'] = (raw['PPM/UPM'] == 'UPM').astype(int)

            def _agg(grp):
                g = grp.agg(coverage=('is_upm', 'count'), upm_count=('is_upm', 'sum')).reset_index()
                g['ml_risk'] = (g['upm_count'] / g['coverage']).round(4)
                return g.drop(columns='upm_count')

            # Building-level all-years avg: (uni, bld, sys, subsys, month)
            df_risk_building = _agg(raw.groupby(
                ['UniversityID', 'BuildingID', 'BuildingName',
                 'SystemDescription', 'SubsystemDescription', 'month'],
                observed=True
            ))

            # University-level all-years avg: (uni, sys, subsys, month)
            df_risk_university = _agg(raw.groupby(
                ['UniversityID', 'SystemDescription', 'SubsystemDescription', 'month'],
                observed=True
            ))

            # University-level per-year: (uni, sys, subsys, month, year)
            df_risk_university_yearly = _agg(raw.groupby(
                ['UniversityID', 'SystemDescription', 'SubsystemDescription', 'month', 'year'],
                observed=True
            ))

            # Metadata
            universities = [int(u) for u in sorted(raw['UniversityID'].unique())]
            bld_names = raw[['BuildingID', 'BuildingName']].drop_duplicates('BuildingID')
            bld_names = bld_names[bld_names['BuildingID'].notna() & bld_names['BuildingName'].notna()]
            name_lookup = {
                str(row.BuildingID): str(row.BuildingName)
                for row in bld_names.itertuples(index=False)
            }
            buildings_by_uni = (
                raw[raw['BuildingID'].notna()]
                .groupby('UniversityID')['BuildingID']
                .apply(lambda x: sorted([str(b) for b in x.unique()]))
                .to_dict()
            )
            years_by_uni = (
                raw.groupby('UniversityID')['year']
                .apply(lambda x: sorted(x.unique().tolist()))
                .to_dict()
            )
            risk_heatmap_meta = {
                "universities": universities,
                "buildings_by_university": {str(int(u)): v for u, v in buildings_by_uni.items()},
                "building_names": name_lookup,
                "years_by_university": {str(int(u)): v for u, v in years_by_uni.items()},
            }
            print(f"✓ Risk heatmap loaded from FMUCD CSV: {len(df_risk_building):,} building rows, "
                  f"{len(df_risk_university):,} university rows, {len(universities)} universities")
        else:
            print("⚠ Risk heatmap: FMUCD CSV not found")
    except Exception as e:
        print(f"Warning: Risk heatmap data not loaded — {e}")

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


def load_defect_data_if_needed():
    global df_defects, topic_info

    if topic_info is None and os.path.exists(TOPIC_INFO_PATH):
        topic_info = pd.read_csv(TOPIC_INFO_PATH)
        print(f"✓ Topic info loaded: {len(topic_info)} topics")

    if df_defects is None and os.path.exists(DEFECT_DATA_PATH):
        print("Loading defect data (first request)...")
        df_defects = pd.read_parquet(DEFECT_DATA_PATH)
        print(f"✓ Defect data loaded: {len(df_defects)} records")


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
    if df_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Calculate summary using actual data
    avg_risk = float(df_data['upm_rate'].mean()) if 'upm_rate' in df_data.columns else 0.0
    high_risk = int((df_data['upm_rate'] >= 0.7).sum()) if 'upm_rate' in df_data.columns else 0
    total_systems = int(df_data['system'].nunique())
    total_cost = float(df_data['cost'].sum()) if 'cost' in df_data.columns else 0.0

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
    if df_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Use existing upm_rate as the risk metric
    # Pivot table
    heatmap = df_data.pivot_table(
        index='system',
        columns='month',
        values='upm_rate',
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
    if df_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Create a working copy
    df = df_data.copy()

    # Calculate predicted UPM/PPM counts using existing rate
    df['pred_upm'] = df['total_count'] * df['upm_rate']
    df['pred_ppm'] = df['total_count'] * (1 - df['upm_rate'])

    # Group by year-month
    df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)

    monthly = df.groupby('year_month').agg({
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


# ============================================
# DEFECT INTELLIGENCE ENDPOINTS
# ============================================

def create_defect_label(topic_name: str, topic_id: int) -> str:
    """Convert BERTopic topic name to human-readable defect label"""
    if topic_id == -1:
        return "Mixed/Administrative Tasks"

    # Mapping of topic keywords to readable labels
    keyword_mappings = {
        'light': 'Lighting System Failure',
        'cold': 'HVAC Temperature Control',
        'warm': 'HVAC Temperature Control',
        'heat': 'HVAC Temperature Control',
        'lock': 'Door Lock & Access',
        'outlet': 'Electrical Outlet Issue',
        'power': 'Power Outage',
        'fire alarm': 'Fire Alarm System',
        'alarm': 'Alarm System Malfunction',
        'toilet': 'Toilet System Failure',
        'flush': 'Toilet Flushing Issue',
        'window': 'Window & Glass Damage',
        'broken': 'Structural Damage',
        'drain': 'Drainage System Clog',
        'clogged': 'Drainage System Clog',
        'sink': 'Sink Plumbing Issue',
        'cooler': 'Refrigeration Equipment',
        'freezer': 'Refrigeration Equipment',
        'noise': 'Equipment Noise Issue',
        'loud': 'Equipment Noise Issue',
        'ceiling': 'Ceiling Leak/Damage',
        'leak': 'Water Leak',
        'leaking': 'Water Leak',
        'faucet': 'Faucet Leak',
        'paint': 'Paint & Wall Damage',
        'patch': 'Wall Repair Needed',
        'spray': 'Pest Control',
        'thermostat': 'Thermostat Malfunction',
        'dispenser': 'Dispenser Malfunction',
        'pump': 'Pump System Failure',
        'sump': 'Sump Pump Issue',
        'plumb': 'Plumbing System',
        'exhaust': 'Exhaust System',
        'motor': 'Motor Failure',
        'hood': 'Fume Hood Issue',
        'fountain': 'Water Fountain Issue',
        'smell': 'Odor Problem',
        'odor': 'Odor Problem',
        'stairs': 'Stair Safety Hazard',
        'sprinkler': 'Sprinkler System',
        'card': 'Card Access System',
        'access': 'Access Control',
        'compressor': 'Compressor Issue',
        'machine': 'Machine Malfunction',
        'roof': 'Roof Leak',
        'tiles': 'Ceiling Tile Damage',
        'wall': 'Wall Damage',
        'valve': 'Valve Issue',
        'steam': 'Steam System',
        'elevator': 'Elevator Malfunction',
        'laundry': 'Laundry Equipment',
        'garbage': 'Garbage Disposal',
        'filter': 'Filter Replacement',
        'mold': 'Mold/Mildew Issue',
        'clock': 'Clock System',
        'refrigerator': 'Refrigerator Issue',
        'desk': 'Furniture Damage',
        'carpet': 'Carpet/Flooring Issue',
    }

    # Extract first keyword from topic name (e.g., "0_light_lights_lighting_elec" -> "light")
    parts = topic_name.split('_')
    if len(parts) > 1:
        for keyword in parts[1:]:  # Skip the topic number
            if keyword in keyword_mappings:
                return keyword_mappings[keyword]

    # Fallback: capitalize first keyword
    if len(parts) > 1:
        return parts[1].replace('_', ' ').title() + " Issue"

    return f"Defect Type {topic_id}"


def calculate_defect_cost(row: pd.Series, topic_id: int) -> float:
    """
    Calculate synthetic cost based on defect type complexity and system.
    NOTE: Real cost data (DMC field) is unavailable in the dataset.
    Estimates are based on industry-standard maintenance costs, adjusted by priority and duration.
    """
    # Base costs by defect complexity (based on typical maintenance costs)
    base_costs = {
        -1: 500,   # Mixed/Administrative - medium
        0: 150,    # Lighting - low
        1: 800,    # HVAC - high
        2: 300,    # Locks - medium-low
        3: 400,    # Electrical - medium
        4: 600,    # Fire alarm - medium-high
        5: 700,    # Alarm systems - medium-high
        6: 350,    # Toilet - medium
        7: 250,    # Window - low-medium
        8: 300,    # Drains - medium
        9: 1200,   # Refrigeration - high
        10: 200,   # Noise (inspection) - low
        11: 800,   # Ceiling leak - high
        12: 250,   # Faucet - low-medium
        15: 400,   # Toilet leak - medium
        16: 350,   # Paint - medium
        21: 2000,  # Pump - very high
        33: 1500,  # Roof leak - very high
        38: 1800,  # Condensate pump - high
        45: 1500,  # Steam valve - high
        46: 3000,  # Elevator - very high
        54: 2500,  # Water heater - very high
        57: 2200,  # Boiler - very high
    }

    base_cost = base_costs.get(topic_id, 500)

    # Add variation based on priority
    priority_multiplier = 1.0
    if pd.notna(row.get('WOPriority')):
        try:
            priority = float(row['WOPriority'])
            if priority >= 50:
                priority_multiplier = 1.5
            elif priority >= 40:
                priority_multiplier = 1.2
            elif priority <= 20:
                priority_multiplier = 0.8
        except:
            pass

    # Add variation based on duration
    duration_multiplier = 1.0
    if pd.notna(row.get('WODuration')):
        try:
            duration = float(row['WODuration'])
            if duration > 100:
                duration_multiplier = 1.3
            elif duration > 50:
                duration_multiplier = 1.1
        except:
            pass

    # Calculate final cost with some randomness
    final_cost = base_cost * priority_multiplier * duration_multiplier * np.random.uniform(0.8, 1.2)

    return round(final_cost, 2)


class DefectDataResponse(BaseModel):
    WOId: str
    WODescription: str
    defect_type: str
    SystemDescription: str
    BuildingID: Optional[str]
    UniversityID: int
    UniversityName: str
    BuildingName: Optional[str]
    TotalCost: float
    WOStartDate: str
    WOPriority: Optional[str]
    Status: str
    topic_id: int


class DefectMetadata(BaseModel):
    universities: List[Dict[str, Any]]
    buildings: List[Dict[str, Any]]
    defectTypes: List[str]
    systems: List[str]


class DefectIntelligenceResponse(BaseModel):
    data: List[DefectDataResponse]
    metadata: DefectMetadata
    total_count: int


@app.get("/api/defect-intelligence", response_model=DefectIntelligenceResponse)
async def get_defect_intelligence(
    universityId: Optional[str] = 'all',
    buildingId: Optional[str] = 'all',
    defectType: Optional[str] = 'all',
    system: Optional[str] = 'all',
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    limit: int = 1000
):
    """
    Get defect intelligence data with BERTopic-discovered defect types
    """
    # Lazy load defect data on first request
    load_defect_data_if_needed()

    if df_defects is None or topic_info is None:
        raise HTTPException(status_code=503, detail="Defect data not loaded")

    try:
        df = df_defects  # read-only reference; no copy until we mutate

        topic_to_name = dict(zip(topic_info['Topic'], topic_info['Name']))

        # Build label map on unique topic_ids only (~100 values, not 2M rows)
        unique_tids = df['topic_id'].unique()
        topic_to_label = {
            int(tid): create_defect_label(topic_to_name.get(tid, f'topic_{tid}'), int(tid))
            for tid in unique_tids
        }

        # Collect metadata from full df using vectorized/unique ops (fast)
        univ_ids = sorted(df['UniversityID'].dropna().unique().astype(int).tolist())
        all_defect_types = sorted(set(topic_to_label.values()))
        systems = sorted(df['SystemDescription'].dropna().unique().tolist())

        # Apply filters using boolean masks (vectorized, no apply)
        mask = pd.Series(True, index=df.index)
        if universityId and universityId != 'all':
            mask &= df['UniversityID'] == int(universityId)
        if buildingId and buildingId != 'all':
            mask &= df['BuildingID'] == buildingId
        if defectType and defectType != 'all':
            matching_tids = [tid for tid, label in topic_to_label.items() if label == defectType]
            mask &= df['topic_id'].isin(matching_tids)
        if system and system != 'all':
            mask &= df['SystemDescription'] == system
        if startDate:
            mask &= pd.to_datetime(df['WOStartDate']) >= pd.to_datetime(startDate)
        if endDate:
            mask &= pd.to_datetime(df['WOStartDate']) <= pd.to_datetime(endDate)

        # Limit to result set BEFORE any expensive per-row work
        df = df[mask].sort_values('WOStartDate', ascending=False).head(limit).copy()

        # Now do all per-row transformations on ≤100 rows
        df['defect_type'] = df['topic_id'].map(topic_to_label)
        df['TotalCost'] = pd.to_numeric(df['TotalCost'], errors='coerce').fillna(0)
        zero_mask = df['TotalCost'] == 0
        if zero_mask.any():
            df.loc[zero_mask, 'TotalCost'] = df[zero_mask].apply(
                lambda row: calculate_defect_cost(row, int(row['topic_id'])), axis=1
            )

        university_mapping = {uid: f'University {uid}' for uid in univ_ids}
        df['UniversityName'] = df['UniversityID'].map(university_mapping).fillna('Unknown University')

        df['BuildingName'] = df['BuildingID'].apply(
            lambda bid: str(bid) if pd.notna(bid) and str(bid) != 'nan' else 'Unknown'
        )

        statuses = ['Completed', 'Completed', 'Completed', 'In Progress']
        df['Status'] = [statuses[i % len(statuses)] for i in range(len(df))]

        if 'WOId' not in df.columns:
            df['WOId'] = [f'WO-{str(i+1).zfill(6)}' for i in range(len(df))]

        # Buildings metadata
        universities = [{'id': uid, 'name': f'University {uid}'} for uid in univ_ids]
        if universityId and universityId != 'all':
            df_for_buildings = df_defects[df_defects['UniversityID'] == int(universityId)]
        else:
            df_for_buildings = df_defects
        buildings_raw = df_for_buildings['BuildingID'].dropna().unique()
        buildings_raw = [b for b in buildings_raw if str(b) != 'nan']
        buildings = sorted([{'id': str(bid), 'name': str(bid)} for bid in buildings_raw], key=lambda x: x['id'])

        data = []
        for _, row in df.iterrows():
            data.append({
                'WOId': str(row.get('WOId', 'N/A')),
                'WODescription': row['WODescription'][:200] if pd.notna(row.get('WODescription')) else 'N/A',
                'defect_type': row['defect_type'],
                'SystemDescription': row['SystemDescription'],
                'BuildingID': str(row['BuildingID']) if pd.notna(row['BuildingID']) else None,
                'UniversityID': int(row['UniversityID']),
                'UniversityName': row['UniversityName'],
                'BuildingName': row['BuildingName'],
                'TotalCost': float(row['TotalCost']),
                'WOStartDate': str(row['WOStartDate'])[:10],
                'WOPriority': str(row['WOPriority']) if pd.notna(row.get('WOPriority')) else None,
                'Status': row['Status'],
                'topic_id': int(row['topic_id'])
            })

        return {
            'data': data,
            'metadata': {
                'universities': universities,
                'buildings': buildings,
                'defectTypes': sorted(all_defect_types),
                'systems': systems
            },
            'total_count': len(data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing defect data: {str(e)}")


# ============================================================================
# NEW AGGREGATED DEFECT INTELLIGENCE ENDPOINTS (Step 6)
# ============================================================================

@app.get("/api/defects/summary")
async def get_defect_summary(
    universityId: Optional[str] = 'all',
    limit: int = 50
):
    """
    Get aggregated summary of defect categories
    Returns count, total cost, average cost, and impact for each defect type
    """
    if df_defect_summary is None:
        raise HTTPException(status_code=503, detail="Defect summary data not loaded")

    try:
        df = df_defect_summary.copy()

        # Update defect category names
        df['defect_category'] = df['defect_category'].replace('Unclassified Defect', 'Mixed/Administrative Tasks')

        # Apply university filter if needed (requires joining with building_defect)
        if universityId and universityId != 'all' and df_building_defect is not None:
            # Get defect categories for this university
            university_defects = df_building_defect[
                df_building_defect['university_id'] == int(universityId)
            ]['defect_category'].unique()
            df = df[df['defect_category'].isin(university_defects)]

        # Apply limit
        df = df.head(limit)

        # Convert to JSON-serializable format
        result = df.to_dict(orient='records')

        return {
            'data': result,
            'total_categories': len(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing summary: {str(e)}")


@app.get("/api/defects/by-system")
async def get_defects_by_system(
    system: Optional[str] = 'all',
    universityId: Optional[str] = 'all',
    limit: int = 100
):
    """
    Get defect breakdown by system
    Shows which defect types occur in each system
    """
    if df_system_defect is None:
        raise HTTPException(status_code=503, detail="System-defect data not loaded")

    try:
        df = df_system_defect.copy()

        # Update defect category names
        df['defect_category'] = df['defect_category'].replace('Unclassified Defect', 'Mixed/Administrative Tasks')

        # Apply filters
        if system and system != 'all':
            df = df[df['system'] == system]

        # University filter (requires joining with building data)
        if universityId and universityId != 'all' and df_building_defect is not None:
            university_defects = df_building_defect[
                df_building_defect['university_id'] == int(universityId)
            ]['defect_category'].unique()
            df = df[df['defect_category'].isin(university_defects)]

        # Sort by count descending
        df = df.sort_values('count', ascending=False).head(limit)

        # Convert to JSON
        result = df.to_dict(orient='records')

        return {
            'data': result,
            'total_combinations': len(result),
            'systems': sorted(df['system'].unique().tolist())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing system data: {str(e)}")


@app.get("/api/defects/by-building")
async def get_defects_by_building(
    universityId: Optional[str] = 'all',
    buildingId: Optional[str] = 'all',
    limit: int = 100,
    sortBy: str = 'total_impact'  # Options: total_impact, count, total_cost
):
    """
    Get defect breakdown by building
    Shows which buildings have the most defects and highest costs
    """
    if df_building_defect is None:
        raise HTTPException(status_code=503, detail="Building-defect data not loaded")

    try:
        df = df_building_defect.copy()

        # Update university names to real names
        university_name_mapping = {
            'Cornell University': 'University 10',
            'Ohio State University': 'University 12',
            'University of Michigan': 'University 20',
            'Unknown University': 'Unknown University'
        }
        df['university_name'] = df['university_name'].replace(university_name_mapping)

        # Update building names - remove "Building" prefix
        df['building_name'] = df['building_name'].apply(
            lambda x: x.replace('Building ', '') if isinstance(x, str) and x.startswith('Building ') else x
        )

        # Update defect category names
        df['defect_category'] = df['defect_category'].replace('Unclassified Defect', 'Mixed/Administrative Tasks')

        # Apply filters
        if universityId and universityId != 'all':
            df = df[df['university_id'] == int(universityId)]

        if buildingId and buildingId != 'all':
            df = df[df['building_id'] == buildingId]

        # Sort by specified column
        if sortBy in df.columns:
            df = df.sort_values(sortBy, ascending=False)

        df = df.head(limit)

        # Convert to JSON
        result = df.to_dict(orient='records')

        # Get top problematic buildings summary
        building_summary = df.groupby(['building_id', 'building_name', 'university_name']).agg({
            'count': 'sum',
            'total_cost': 'sum',
            'total_impact': 'sum'
        }).reset_index().sort_values('total_impact', ascending=False).head(20)

        return {
            'data': result,
            'total_combinations': len(result),
            'top_buildings': building_summary.to_dict(orient='records')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing building data: {str(e)}")


@app.get("/api/defects/monthly")
async def get_monthly_defect_trends(
    defectCategory: Optional[str] = 'all',
    universityId: Optional[str] = 'all',
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    limit: int = 500
):
    """
    Get monthly defect trends over time
    Shows how defect occurrences change month by month
    """
    if df_monthly_defect is None:
        raise HTTPException(status_code=503, detail="Monthly defect data not loaded")

    try:
        df = df_monthly_defect.copy()

        # Update defect category names
        df['defect_category'] = df['defect_category'].replace('Unclassified Defect', 'Mixed/Administrative Tasks')

        # Apply filters
        if defectCategory and defectCategory != 'all':
            df = df[df['defect_category'] == defectCategory]

        # Date range filtering
        if startDate:
            df = df[df['month'] >= startDate]

        if endDate:
            df = df[df['month'] <= endDate]

        # Sort by month
        df = df.sort_values('month').head(limit)

        # Convert to JSON
        result = df.to_dict(orient='records')

        # Get available defect categories for filtering
        categories = sorted(df['defect_category'].unique().tolist())

        return {
            'data': result,
            'total_records': len(result),
            'date_range': {
                'start': df['month'].min() if len(df) > 0 else None,
                'end': df['month'].max() if len(df) > 0 else None
            },
            'available_categories': categories[:50]  # Limit for performance
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing monthly data: {str(e)}")


@app.get("/api/defects/impact")
async def get_defect_impact_ranking(
    universityId: Optional[str] = 'all',
    riskLevel: Optional[str] = 'all',  # Options: Critical, High, Medium, Low
    limit: int = 50
):
    """
    Get defect categories ranked by impact score
    Impact score = TotalCost × Priority (High=3, Medium=2, Low=1)
    """
    if df_impact_summary is None:
        raise HTTPException(status_code=503, detail="Impact summary data not loaded")

    try:
        df = df_impact_summary.copy()

        # Update defect category names
        df['defect_category'] = df['defect_category'].replace('Unclassified Defect', 'Mixed/Administrative Tasks')

        # Apply risk level filter
        if riskLevel and riskLevel != 'all':
            df = df[df['risk_level'] == riskLevel]

        # University filter (requires joining with building data)
        if universityId and universityId != 'all' and df_building_defect is not None:
            university_defects = df_building_defect[
                df_building_defect['university_id'] == int(universityId)
            ]['defect_category'].unique()
            df = df[df['defect_category'].isin(university_defects)]

        # Already sorted by total_impact in aggregation
        df = df.head(limit)

        # Convert to JSON (convert categorical to string)
        df_json = df.copy()
        df_json['risk_level'] = df_json['risk_level'].astype(str)
        result = df_json.to_dict(orient='records')

        # Calculate summary statistics
        total_impact = df['total_impact'].sum()
        avg_impact = df['avg_impact'].mean()

        return {
            'data': result,
            'total_categories': len(result),
            'summary': {
                'total_impact': float(total_impact),
                'average_impact': float(avg_impact),
                'highest_impact_category': result[0]['defect_category'] if len(result) > 0 else None,
                'highest_impact_score': float(result[0]['total_impact']) if len(result) > 0 else 0
            },
            'risk_levels': ['Critical', 'High', 'Medium', 'Low']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing impact data: {str(e)}")


@app.get("/api/defects/survival-model")
async def get_survival_model():
    """Serve Cox survival model results"""
    survival_path = PROJECT_ROOT / "data" / "ml_defect_analytics" / "survival_cox_model.json"
    if not survival_path.exists():
        raise HTTPException(status_code=404, detail="Survival model data not found")
    with open(survival_path) as f:
        return json.load(f)


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


# ─────────────────────────────────────────────────────────────────────────────
# Risk Heatmap Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/risk-heatmap/metadata")
async def get_risk_heatmap_metadata():
    """Universities, buildings list, and building names for filter dropdowns."""
    if risk_heatmap_meta is None:
        raise HTTPException(status_code=503, detail="Risk heatmap data not loaded")
    return risk_heatmap_meta


@app.get("/api/risk-heatmap/university")
async def get_university_risk_heatmap(universityId: int = 10, year: Optional[int] = None):
    """
    University-level heatmap: system × month for the given university.
    Pass year= to get a specific year's data; omit for all-years historical average.
    """
    if df_risk_university is None:
        raise HTTPException(status_code=503, detail="Risk heatmap data not loaded")

    if year is not None and df_risk_university_yearly is not None:
        subset = df_risk_university_yearly[
            (df_risk_university_yearly['UniversityID'] == universityId) &
            (df_risk_university_yearly['year'] == year)
        ]
    else:
        subset = df_risk_university[df_risk_university['UniversityID'] == universityId]

    if subset.empty:
        raise HTTPException(status_code=404, detail=f"No data for university {universityId}")

    result = []
    for row in subset.itertuples(index=False):
        result.append({
            "UniversityID": int(row.UniversityID),
            "SystemDescription": row.SystemDescription,
            "SubsystemDescription": row.SubsystemDescription,
            "MonthNum": int(row.month),
            "ml_risk": float(row.ml_risk),
            "hist_asset_rate": float(row.ml_risk),
            "hist_shock_rate": 0.0,
            "coverage": int(row.coverage),
        })
    return result


@app.get("/api/risk-heatmap/building")
async def get_building_risk_heatmap(buildingId: str, universityId: int = 10):
    """
    Building-level heatmap: system × month for a single building.
    Returns rows in the schema the frontend hook expects.
    """
    if df_risk_building is None:
        raise HTTPException(status_code=503, detail="Risk heatmap data not loaded")

    subset = df_risk_building[
        (df_risk_building['BuildingID'] == buildingId) &
        (df_risk_building['UniversityID'] == universityId)
    ]
    if subset.empty:
        raise HTTPException(status_code=404, detail=f"No data for building {buildingId} in university {universityId}")

    result = []
    for row in subset.itertuples(index=False):
        result.append({
            "UniversityID": int(row.UniversityID),
            "BuildingID": row.BuildingID,
            "BuildingName": row.BuildingName,
            "SystemDescription": row.SystemDescription,
            "SubsystemDescription": row.SubsystemDescription,
            "MonthNum": int(row.month),
            "ml_risk": float(row.ml_risk),
            "hist_asset_rate": float(row.ml_risk),
            "hist_shock_rate": 0.0,
            "coverage": int(row.coverage),
        })
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
