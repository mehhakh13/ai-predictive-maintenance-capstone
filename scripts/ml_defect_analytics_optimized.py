"""
Memory-Optimized Master's Level AI/ML Defect Analytics
Uses the already-cleaned dataset for efficiency
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from xgboost import XGBRegressor
import lightgbm as lgb

# Time Series
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet

# Survival Analysis
from lifelines import CoxPHFitter

# Feature Importance
import shap

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "ml_defect_analytics"
OUTPUT_DIR.mkdir(exist_ok=True)

print("="*80)
print("MASTER'S LEVEL AI/ML DEFECT ANALYTICS")
print("Using pre-cleaned dataset for memory efficiency")
print("="*80)

# ============================================================================
# DATA LOADING
# ============================================================================

def load_cleaned_data():
    """Load the already-cleaned dataset"""
    print("\n[1/6] Loading cleaned dataset...")

    df = pd.read_csv(PROCESSED_DIR / "fmucd_all_cleaned.csv", low_memory=False)

    # Parse dates
    df['WOStartDate'] = pd.to_datetime(df['WOStartDate'], errors='coerce')
    df['WOEndDate'] = pd.to_datetime(df['WOEndDate'], errors='coerce')

    # Convert numeric columns
    numeric_cols = ['TotalCost', 'WODuration', 'WOPriority', 'LaborCost',
                    'MinTemp.(°C)', 'MaxTemp.(°C)', 'Humidity(%)',
                    'Precipitation(mm)', 'Snow(mm)', 'WindSpeed(m/s)',
                    'Atmospheric pressure(hPa)']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    print(f"   Loaded {len(df):,} cleaned records")
    print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    return df

# ============================================================================
# MODEL 1: TIME SERIES FORECASTING
# ============================================================================

def build_recurrence_forecasting(df):
    """Time series forecasting for recurrence prediction"""
    print("\n" + "="*80)
    print("MODEL 1: RECURRENCE PREDICTION (Time Series Forecasting)")
    print("="*80)

    print("\n[2/6] Preparing time series data...")

    # Aggregate to monthly level
    df['YearMonth'] = df['WOStartDate'].dt.to_period('M')

    # Top 5 subsystems
    top_subsystems = df['SubsystemDescription'].value_counts().head(5).index.tolist()

    results = []

    for subsystem in top_subsystems[:3]:  # Top 3 for demo
        print(f"\n   📊 {subsystem}")

        subsystem_df = df[df['SubsystemDescription'] == subsystem]
        ts = subsystem_df.groupby('YearMonth').size().reset_index()
        ts.columns = ['YearMonth', 'count']
        ts['ds'] = ts['YearMonth'].dt.to_timestamp()
        ts = ts.sort_values('ds')

        if len(ts) < 24:
            continue

        # Split 80/20
        split_idx = int(len(ts) * 0.8)
        train = ts[:split_idx]
        test = ts[split_idx:]

        model_scores = {'subsystem': subsystem}

        # ARIMA
        try:
            print("      Training ARIMA(2,1,2)...", end='')
            model = ARIMA(train['count'], order=(2, 1, 2))
            fit = model.fit()
            pred = fit.forecast(steps=len(test))
            mae = mean_absolute_error(test['count'], pred)
            model_scores['arima_mae'] = mae
            print(f" MAE: {mae:.2f}")
        except:
            model_scores['arima_mae'] = None
            print(" Failed")

        # Prophet
        try:
            print("      Training Prophet...", end='')
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            model.fit(train[['ds', 'count']].rename(columns={'count': 'y'}))
            future = model.make_future_dataframe(periods=len(test), freq='MS')
            forecast = model.predict(future)
            pred = forecast['yhat'].tail(len(test)).values
            mae = mean_absolute_error(test['count'], pred)
            model_scores['prophet_mae'] = mae
            print(f" MAE: {mae:.2f}")
        except:
            model_scores['prophet_mae'] = None
            print(" Failed")

        # XGBoost with lags
        try:
            print("      Training XGBoost with lag features...", end='')
            ts_ml = ts.copy()
            for lag in [1, 2, 3]:
                ts_ml[f'lag_{lag}'] = ts_ml['count'].shift(lag)
            ts_ml = ts_ml.dropna()

            X = ts_ml[[c for c in ts_ml.columns if c.startswith('lag_')]]
            y = ts_ml['count']

            if len(X) > 20:
                split = int(len(X) * 0.8)
                X_train, X_test = X[:split], X[split:]
                y_train, y_test = y[:split], y[split:]

                model = XGBRegressor(n_estimators=50, max_depth=4, random_state=42, verbose=0)
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, pred)
                model_scores['xgb_mae'] = mae
                print(f" MAE: {mae:.2f}")
            else:
                model_scores['xgb_mae'] = None
                print(" Insufficient data")
        except:
            model_scores['xgb_mae'] = None
            print(" Failed")

        # Best model
        scores = {k: v for k, v in model_scores.items() if v and 'mae' in k}
        if scores:
            best = min(scores, key=scores.get)
            model_scores['best_model'] = best.replace('_mae', '')
            print(f"      ✅ Best: {model_scores['best_model']} (MAE: {scores[best]:.2f})")

        results.append(model_scores)

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "recurrence_forecast_comparison.csv", index=False)
    print(f"\n   ✅ Saved: recurrence_forecast_comparison.csv")

    return results_df

# ============================================================================
# MODEL 2: SURVIVAL ANALYSIS
# ============================================================================

def build_survival_analysis(df):
    """Survival analysis for time-to-failure"""
    print("\n" + "="*80)
    print("MODEL 2: TIME-TO-FAILURE PREDICTION (Survival Analysis)")
    print("="*80)

    print("\n[3/6] Calculating time between failures...")

    # Sort and calculate time since last failure
    df_sorted = df.sort_values(['SubsystemDescription', 'UniversityID', 'WOStartDate'])
    df_sorted['PrevDate'] = df_sorted.groupby(['SubsystemDescription', 'UniversityID'])['WOStartDate'].shift(1)
    df_sorted['DaysSinceFailure'] = (df_sorted['WOStartDate'] - df_sorted['PrevDate']).dt.total_seconds() / 86400

    survival_df = df_sorted[df_sorted['DaysSinceFailure'].notna()].copy()
    survival_df['IsUPM'] = (survival_df['PPM/UPM'] == 'UPM').astype(int)
    survival_df['AvgTemp'] = (survival_df['MinTemp.(°C)'] + survival_df['MaxTemp.(°C)']) / 2

    print(f"   Prepared {len(survival_df):,} survival records")

    # Cox model
    try:
        print("\n   Training Cox Proportional Hazards Model...")

        cox_features = ['TotalCost', 'WODuration', 'WOPriority', 'AvgTemp', 'Humidity(%)']
        cox_df = survival_df[['DaysSinceFailure', 'IsUPM'] + cox_features].dropna()

        # Sample for speed (10K records)
        if len(cox_df) > 10000:
            cox_df = cox_df.sample(n=10000, random_state=42)

        print(f"      Training on {len(cox_df):,} samples")

        model = CoxPHFitter()
        model.fit(cox_df, duration_col='DaysSinceFailure', event_col='IsUPM')

        c_index = model.concordance_index_
        print(f"      C-index (concordance): {c_index:.4f}")

        # Feature importance
        coefs = model.summary[['coef', 'exp(coef)', 'p']].sort_values('coef', key=abs, ascending=False)
        print("\n      Top Risk Factors (Hazard Ratios):")
        for idx, row in coefs.head(5).iterrows():
            print(f"        {idx}: HR={row['exp(coef)']:.3f}, p={row['p']:.4f}")

        # Save
        results = {
            'model': 'Cox Proportional Hazards',
            'c_index': float(c_index),
            'n_samples': len(cox_df),
            'coefficients': coefs.to_dict()
        }

        with open(OUTPUT_DIR / "survival_cox_model.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n   ✅ Saved: survival_cox_model.json")

        return coefs

    except Exception as e:
        print(f"   ❌ Cox model failed: {e}")
        return None

# ============================================================================
# MODEL 3: ENVIRONMENTAL IMPACT - ML + SHAP
# ============================================================================

def build_environmental_models(df):
    """ML models for environmental impact prediction"""
    print("\n" + "="*80)
    print("MODEL 3: ENVIRONMENTAL IMPACT PREDICTION (ML + SHAP)")
    print("="*80)

    print("\n[4/6] Aggregating to monthly level...")

    df['YearMonth'] = df['WOStartDate'].dt.to_period('M')
    df['Month'] = df['WOStartDate'].dt.month

    # Sample subsystems to reduce compute
    top_subsystems = df['SubsystemDescription'].value_counts().head(20).index
    df_sample = df[df['SubsystemDescription'].isin(top_subsystems)].copy()

    monthly = df_sample.groupby(['SubsystemDescription', 'YearMonth']).agg({
        'WOID': 'count',
        'MinTemp.(°C)': 'mean',
        'MaxTemp.(°C)': 'mean',
        'Humidity(%)': 'mean',
        'Precipitation(mm)': 'sum',
        'Snow(mm)': 'sum',
        'WindSpeed(m/s)': 'mean',
        'Atmospheric pressure(hPa)': 'mean'
    }).reset_index()

    monthly.columns = ['Subsystem', 'YearMonth', 'FailureCount', 'MinTemp', 'MaxTemp',
                       'Humidity', 'Precip', 'Snow', 'Wind', 'Pressure']

    # Features
    monthly['AvgTemp'] = (monthly['MinTemp'] + monthly['MaxTemp']) / 2
    monthly['TempRange'] = monthly['MaxTemp'] - monthly['MinTemp']
    monthly['Month'] = monthly['YearMonth'].dt.month

    # One-hot encode subsystem
    monthly_encoded = pd.get_dummies(monthly, columns=['Subsystem'], prefix='Sub')

    feature_cols = [c for c in monthly_encoded.columns if c not in ['YearMonth', 'FailureCount']]
    X = monthly_encoded[feature_cols].fillna(0)
    y = monthly_encoded['FailureCount']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"   Train: {len(X_train):,}, Test: {len(X_test):,}")
    print("\n[5/6] Training models...")

    models = {
        'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1),
        'XGBoost': XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbosity=0),
        'LightGBM': lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1)
    }

    results = []

    for name, model in models.items():
        print(f"\n   {name}:")
        model.fit(X_train, y_train)

        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)

        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)

        print(f"      Train - MAE: {train_mae:.2f}, R²: {train_r2:.4f}")
        print(f"      Test  - MAE: {test_mae:.2f}, R²: {test_r2:.4f}")

        results.append({
            'model': name,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "environmental_model_comparison.csv", index=False)
    print(f"\n   ✅ Saved: environmental_model_comparison.csv")

    # SHAP analysis
    print("\n[6/6] SHAP Feature Importance...")

    try:
        best_model = models['XGBoost']
        explainer = shap.TreeExplainer(best_model)

        # Sample for speed
        X_sample = X_test.sample(n=min(100, len(X_test)), random_state=42)
        shap_values = explainer.shap_values(X_sample)

        # Non-encoded feature importance (weather + time)
        weather_features = ['MinTemp', 'MaxTemp', 'AvgTemp', 'TempRange', 'Humidity',
                           'Precip', 'Snow', 'Wind', 'Pressure', 'Month']

        weather_cols = [c for c in X.columns if any(f in c for f in weather_features)]

        importance = pd.DataFrame({
            'feature': X.columns,
            'shap_importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('shap_importance', ascending=False)

        # Aggregate weather features
        weather_importance = importance[importance['feature'].isin(weather_cols)].head(10)

        print("\n      Top 10 Weather Features:")
        for _, row in weather_importance.iterrows():
            print(f"        {row['feature']}: {row['shap_importance']:.4f}")

        importance.to_csv(OUTPUT_DIR / "shap_feature_importance.csv", index=False)
        print(f"\n   ✅ Saved: shap_feature_importance.csv")

    except Exception as e:
        print(f"   ⚠️  SHAP failed: {e}")

    return results_df

# ============================================================================
# MAIN
# ============================================================================

def main():
    df = load_cleaned_data()

    recurrence_results = build_recurrence_forecasting(df)
    survival_results = build_survival_analysis(df)
    environmental_results = build_environmental_models(df)

    print("\n" + "="*80)
    print("✅ MASTER'S LEVEL ML PIPELINE COMPLETE!")
    print("="*80)
    print(f"\nOutput: {OUTPUT_DIR}/")
    print("\nGenerated files:")
    print("  1. recurrence_forecast_comparison.csv - Time series model comparison")
    print("  2. survival_cox_model.json - Survival analysis results (C-index)")
    print("  3. environmental_model_comparison.csv - ML model comparison (R², MAE)")
    print("  4. shap_feature_importance.csv - Feature importance analysis")
    print("\n🎓 Ready for Master's capstone presentation!")

if __name__ == "__main__":
    main()
