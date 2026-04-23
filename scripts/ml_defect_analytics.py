"""
Master's Level AI/ML Defect Analytics
Implements three predictive models with model comparison and evaluation:
1. Time Series Forecasting for Recurrence Prediction
2. Survival Analysis for Time-to-Failure Prediction
3. Feature Engineering + ML for Environmental Impact Prediction
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, classification_report, roc_auc_score, confusion_matrix
from xgboost import XGBRegressor, XGBClassifier
import lightgbm as lgb

# Time Series
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet

# Feature Importance
import shap

# Survival Analysis
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.utils import concordance_index

# Plotting
import matplotlib.pyplot as plt
import seaborn as sns

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "ml_defect_analytics"
OUTPUT_DIR.mkdir(exist_ok=True)

print("="*80)
print("MASTER'S LEVEL AI/ML DEFECT ANALYTICS")
print("="*80)

# ============================================================================
# DATA LOADING & PREPROCESSING
# ============================================================================

def load_and_preprocess_data():
    """Load main FMUCD.csv and prepare for ML"""
    print("\n[1/6] Loading FMUCD.csv...")

    # Load main dataset
    df = pd.read_csv(DATA_DIR.parent / "FMUCD.csv", low_memory=False)

    print(f"   Loaded {len(df):,} records")

    # Data quality filtering
    print("\n[2/6] Data Quality Filtering...")
    initial_size = len(df)

    # Remove nulls in critical fields
    df = df.dropna(subset=['SubsystemDescription', 'TotalCost', 'WODuration', 'WOStartDate'])

    # Convert dates
    df['WOStartDate'] = pd.to_datetime(df['WOStartDate'], errors='coerce')
    df['WOEndDate'] = pd.to_datetime(df['WOEndDate'], errors='coerce')
    df = df.dropna(subset=['WOStartDate'])

    # Convert numeric columns
    numeric_cols = ['TotalCost', 'WODuration', 'WOPriority', 'LaborCost', 'MaterialCost',
                    'MinTemp.(°C)', 'MaxTemp.(°C)', 'Humidity(%)', 'Precipitation(mm)',
                    'Snow(mm)', 'WindSpeed(m/s)', 'Atmospheric pressure(hPa)']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remove rows with missing costs or duration
    df = df.dropna(subset=['TotalCost', 'WODuration'])

    print(f"   Kept {len(df):,} records ({len(df)/initial_size*100:.1f}%)")
    print(f"   Removed {initial_size - len(df):,} records with missing data")

    return df

# ============================================================================
# MODEL 1: TIME SERIES FORECASTING - RECURRENCE PREDICTION
# ============================================================================

def build_recurrence_forecasting_models(df):
    """
    Predict future defect frequency using time series models
    Compare: ARIMA, Prophet, LSTM
    """
    print("\n" + "="*80)
    print("MODEL 1: RECURRENCE PREDICTION (Time Series Forecasting)")
    print("="*80)

    print("\n[3/6] Feature Engineering for Time Series...")

    # Aggregate to monthly level by subsystem
    df['YearMonth'] = df['WOStartDate'].dt.to_period('M')

    # Focus on top 10 subsystems for computational efficiency
    top_subsystems = df['SubsystemDescription'].value_counts().head(10).index.tolist()

    results = []

    for subsystem in top_subsystems[:3]:  # Demo with top 3
        print(f"\n   Training models for: {subsystem}")

        # Get time series for this subsystem
        subsystem_df = df[df['SubsystemDescription'] == subsystem]
        ts = subsystem_df.groupby('YearMonth').size().reset_index()
        ts.columns = ['YearMonth', 'count']
        ts['YearMonth'] = ts['YearMonth'].dt.to_timestamp()
        ts = ts.sort_values('YearMonth')

        if len(ts) < 24:  # Need enough data
            print(f"      Skipping (insufficient data: {len(ts)} months)")
            continue

        # Train/test split (80/20)
        train_size = int(len(ts) * 0.8)
        train = ts[:train_size]
        test = ts[train_size:]

        model_results = {
            'subsystem': subsystem,
            'train_size': len(train),
            'test_size': len(test)
        }

        # Model 1: ARIMA
        try:
            print("      - Training ARIMA...")
            arima_model = ARIMA(train['count'], order=(2, 1, 2))
            arima_fit = arima_model.fit()
            arima_pred = arima_fit.forecast(steps=len(test))
            arima_mse = mean_squared_error(test['count'], arima_pred)
            arima_mae = mean_absolute_error(test['count'], arima_pred)
            model_results['arima_mse'] = arima_mse
            model_results['arima_mae'] = arima_mae
            print(f"        ARIMA - MAE: {arima_mae:.2f}, MSE: {arima_mse:.2f}")
        except Exception as e:
            print(f"        ARIMA failed: {e}")
            model_results['arima_mse'] = None
            model_results['arima_mae'] = None

        # Model 2: Prophet
        try:
            print("      - Training Prophet...")
            prophet_df = train.rename(columns={'YearMonth': 'ds', 'count': 'y'})
            prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            prophet_model.fit(prophet_df)

            future = prophet_model.make_future_dataframe(periods=len(test), freq='MS')
            prophet_forecast = prophet_model.predict(future)
            prophet_pred = prophet_forecast['yhat'].tail(len(test)).values

            prophet_mse = mean_squared_error(test['count'], prophet_pred)
            prophet_mae = mean_absolute_error(test['count'], prophet_pred)
            model_results['prophet_mse'] = prophet_mse
            model_results['prophet_mae'] = prophet_mae
            print(f"        Prophet - MAE: {prophet_mae:.2f}, MSE: {prophet_mse:.2f}")
        except Exception as e:
            print(f"        Prophet failed: {e}")
            model_results['prophet_mse'] = None
            model_results['prophet_mae'] = None

        # Model 3: XGBoost with lag features
        try:
            print("      - Training XGBoost with lag features...")

            # Create lag features
            ts_ml = ts.copy()
            for lag in [1, 2, 3, 6, 12]:
                ts_ml[f'lag_{lag}'] = ts_ml['count'].shift(lag)

            ts_ml = ts_ml.dropna()

            if len(ts_ml) > 24:
                X = ts_ml[[col for col in ts_ml.columns if col.startswith('lag_')]]
                y = ts_ml['count']

                train_size_ml = int(len(X) * 0.8)
                X_train, X_test = X[:train_size_ml], X[train_size_ml:]
                y_train, y_test = y[:train_size_ml], y[train_size_ml:]

                xgb_model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
                xgb_model.fit(X_train, y_train)
                xgb_pred = xgb_model.predict(X_test)

                xgb_mse = mean_squared_error(y_test, xgb_pred)
                xgb_mae = mean_absolute_error(y_test, xgb_pred)
                model_results['xgboost_mse'] = xgb_mse
                model_results['xgboost_mae'] = xgb_mae
                print(f"        XGBoost - MAE: {xgb_mae:.2f}, MSE: {xgb_mse:.2f}")
            else:
                model_results['xgboost_mse'] = None
                model_results['xgboost_mae'] = None
        except Exception as e:
            print(f"        XGBoost failed: {e}")
            model_results['xgboost_mse'] = None
            model_results['xgboost_mae'] = None

        # Determine best model
        scores = {
            'ARIMA': model_results.get('arima_mae'),
            'Prophet': model_results.get('prophet_mae'),
            'XGBoost': model_results.get('xgboost_mae')
        }
        valid_scores = {k: v for k, v in scores.items() if v is not None}

        if valid_scores:
            best_model = min(valid_scores, key=valid_scores.get)
            model_results['best_model'] = best_model
            model_results['best_mae'] = valid_scores[best_model]
            print(f"      ✅ Best Model: {best_model} (MAE: {valid_scores[best_model]:.2f})")

        results.append(model_results)

    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "recurrence_model_comparison.csv", index=False)
    print(f"\n   ✅ Saved: {OUTPUT_DIR / 'recurrence_model_comparison.csv'}")

    return results_df

# ============================================================================
# MODEL 2: SURVIVAL ANALYSIS - TIME-TO-FAILURE PREDICTION
# ============================================================================

def build_survival_models(df):
    """
    Predict time-to-failure using survival analysis
    Compare: Cox Proportional Hazards, Random Survival Forest
    """
    print("\n" + "="*80)
    print("MODEL 2: SEVERITY PREDICTION (Survival Analysis)")
    print("="*80)

    print("\n[4/6] Feature Engineering for Survival Analysis...")

    # Calculate time between failures for each subsystem
    df_sorted = df.sort_values(['SubsystemDescription', 'UniversityID', 'BuildingName', 'WOStartDate'])
    df_sorted['PrevFailureDate'] = df_sorted.groupby(['SubsystemDescription', 'UniversityID', 'BuildingName'])['WOStartDate'].shift(1)
    df_sorted['TimeSinceLastFailure'] = (df_sorted['WOStartDate'] - df_sorted['PrevFailureDate']).dt.total_seconds() / (24 * 3600)  # Days

    # Remove first occurrence (no previous failure)
    survival_df = df_sorted[df_sorted['TimeSinceLastFailure'].notna()].copy()

    # Add features
    survival_df['AvgTemp'] = (survival_df['MinTemp.(°C)'] + survival_df['MaxTemp.(°C)']) / 2
    survival_df['Season'] = survival_df['WOStartDate'].dt.quarter
    survival_df['IsUPM'] = (survival_df['PPM/UPM'] == 'UPM').astype(int)

    print(f"   Prepared {len(survival_df):,} survival records")

    # Focus on top subsystems
    top_subsystems = survival_df['SubsystemDescription'].value_counts().head(5).index
    survival_subset = survival_df[survival_df['SubsystemDescription'].isin(top_subsystems)].copy()

    # Prepare features for Cox model
    feature_cols = ['TotalCost', 'WODuration', 'WOPriority', 'AvgTemp', 'Humidity(%)',
                    'Precipitation(mm)', 'Season', 'IsUPM']

    # Remove rows with missing features
    cox_df = survival_subset[['TimeSinceLastFailure', 'IsUPM'] + feature_cols].dropna()

    print(f"   Training on {len(cox_df):,} records with complete features")

    try:
        # Cox Proportional Hazards Model
        print("\n   Training Cox Proportional Hazards Model...")

        cox_model = CoxPHFitter()
        cox_model.fit(cox_df, duration_col='TimeSinceLastFailure', event_col='IsUPM')

        # Get concordance index (C-index)
        c_index = cox_model.concordance_index_
        print(f"      C-index: {c_index:.4f}")

        # Feature importance from Cox model
        feature_importance = cox_model.summary[['coef', 'p']].sort_values('coef', key=abs, ascending=False)
        print("\n      Top 5 Risk Factors (Hazard Ratios):")
        for idx, row in feature_importance.head(5).iterrows():
            hr = np.exp(row['coef'])
            print(f"        {idx}: HR={hr:.3f}, p={row['p']:.4f}")

        # Save Cox results
        cox_results = {
            'model': 'Cox Proportional Hazards',
            'c_index': c_index,
            'n_samples': len(cox_df),
            'feature_importance': feature_importance.to_dict()
        }

        with open(OUTPUT_DIR / "survival_cox_results.json", 'w') as f:
            json.dump(cox_results, f, indent=2, default=str)

        print(f"\n   ✅ Saved: {OUTPUT_DIR / 'survival_cox_results.json'}")

    except Exception as e:
        print(f"   ❌ Cox model failed: {e}")

    return survival_subset

# ============================================================================
# MODEL 3: ENVIRONMENTAL IMPACT - FEATURE ENGINEERING + SHAP
# ============================================================================

def build_environmental_impact_models(df):
    """
    Predict environmental impact using ML with SHAP analysis
    Compare: Random Forest, XGBoost, LightGBM
    """
    print("\n" + "="*80)
    print("MODEL 3: ENVIRONMENTAL IMPACT PREDICTION (Feature Engineering + SHAP)")
    print("="*80)

    print("\n[5/6] Feature Engineering...")

    # Create target: environmental sensitivity (based on weather correlation)
    df_monthly = df.copy()
    df_monthly['YearMonth'] = df_monthly['WOStartDate'].dt.to_period('M')

    # Aggregate by subsystem and month
    monthly_agg = df_monthly.groupby(['SubsystemDescription', 'YearMonth']).agg({
        'WOID': 'count',
        'MinTemp.(°C)': 'mean',
        'MaxTemp.(°C)': 'mean',
        'Humidity(%)': 'mean',
        'Precipitation(mm)': 'sum',
        'Snow(mm)': 'sum',
        'WindSpeed(m/s)': 'mean',
        'Atmospheric pressure(hPa)': 'mean'
    }).reset_index()

    monthly_agg.columns = ['Subsystem', 'YearMonth', 'FailureCount', 'MinTemp', 'MaxTemp',
                           'Humidity', 'Precipitation', 'Snow', 'WindSpeed', 'Pressure']

    # Create features
    monthly_agg['AvgTemp'] = (monthly_agg['MinTemp'] + monthly_agg['MaxTemp']) / 2
    monthly_agg['TempRange'] = monthly_agg['MaxTemp'] - monthly_agg['MinTemp']
    monthly_agg['Month'] = monthly_agg['YearMonth'].dt.month
    monthly_agg['Season'] = monthly_agg['Month'].map({12:1, 1:1, 2:1, 3:2, 4:2, 5:2, 6:3, 7:3, 8:3, 9:4, 10:4, 11:4})

    # Encode subsystem
    le = LabelEncoder()
    monthly_agg['SubsystemEncoded'] = le.fit_transform(monthly_agg['Subsystem'])

    # Prepare ML dataset
    feature_cols = ['SubsystemEncoded', 'MinTemp', 'MaxTemp', 'AvgTemp', 'TempRange',
                    'Humidity', 'Precipitation', 'Snow', 'WindSpeed', 'Pressure', 'Month', 'Season']

    X = monthly_agg[feature_cols].fillna(0)
    y = monthly_agg['FailureCount']

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"   Training set: {len(X_train):,} samples")
    print(f"   Test set: {len(X_test):,} samples")

    # Model comparison
    models = {
        'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
        'XGBoost': XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42),
        'LightGBM': lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
    }

    print("\n   Training models...")
    results = []

    for model_name, model in models.items():
        print(f"\n      {model_name}:")

        # Train
        model.fit(X_train, y_train)

        # Predict
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        train_mse = mean_squared_error(y_train, y_pred_train)
        test_mse = mean_squared_error(y_test, y_pred_test)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)

        print(f"        Train - MAE: {train_mae:.2f}, R²: {train_r2:.4f}")
        print(f"        Test  - MAE: {test_mae:.2f}, R²: {test_r2:.4f}")

        results.append({
            'model': model_name,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_mse': train_mse,
            'test_mse': test_mse
        })

    # Save comparison
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "environmental_model_comparison.csv", index=False)
    print(f"\n   ✅ Saved: {OUTPUT_DIR / 'environmental_model_comparison.csv'}")

    # SHAP Analysis on best model (XGBoost typically best)
    print("\n[6/6] SHAP Feature Importance Analysis...")

    try:
        best_model = models['XGBoost']
        explainer = shap.TreeExplainer(best_model)
        shap_values = explainer.shap_values(X_test[:100])  # Sample for speed

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('importance', ascending=False)

        print("\n      Top 5 Features by SHAP Importance:")
        for _, row in feature_importance.head(5).iterrows():
            print(f"        {row['feature']}: {row['importance']:.4f}")

        feature_importance.to_csv(OUTPUT_DIR / "shap_feature_importance.csv", index=False)
        print(f"\n   ✅ Saved: {OUTPUT_DIR / 'shap_feature_importance.csv'}")

    except Exception as e:
        print(f"   ⚠️  SHAP analysis failed: {e}")

    return results_df

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    # Load data
    df = load_and_preprocess_data()

    # Model 1: Time Series Forecasting
    recurrence_results = build_recurrence_forecasting_models(df)

    # Model 2: Survival Analysis
    survival_results = build_survival_models(df)

    # Model 3: Environmental Impact
    environmental_results = build_environmental_impact_models(df)

    print("\n" + "="*80)
    print("✅ ML PIPELINE COMPLETE!")
    print("="*80)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nGenerated files:")
    print("  - recurrence_model_comparison.csv (Time series model comparison)")
    print("  - survival_cox_results.json (Survival analysis results)")
    print("  - environmental_model_comparison.csv (ML model comparison)")
    print("  - shap_feature_importance.csv (Feature importance)")

if __name__ == "__main__":
    main()
