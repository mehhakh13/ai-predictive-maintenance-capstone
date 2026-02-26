#!/usr/bin/env python3
"""
Quick training script with simplified preprocessing
"""

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def load_and_prepare_data(limit=50000):
    """Load and prepare data quickly"""
    print("="*60)
    print("Quick Train Pipeline")
    print("="*60)

    # Load data
    print(f"\nLoading {limit} rows from Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    response = supabase.table("fmucd_canada").select("*").limit(limit).execute()
    df = pd.DataFrame(response.data)

    print(f"Loaded {len(df)} rows")

    # Convert dates
    df['wostartdate'] = pd.to_datetime(df['wostartdate'], errors='coerce')

    # Drop rows without dates or system
    df = df.dropna(subset=['wostartdate', 'systemdescription'])

    print(f"After dropping nulls: {len(df)} rows")

    # Extract features
    df['year'] = df['wostartdate'].dt.year
    df['month'] = df['wostartdate'].dt.month
    df['season'] = df['month'].apply(lambda x:
        0 if x in [12, 1, 2] else
        1 if x in [3, 4, 5] else
        2 if x in [6, 7, 8] else 3
    )

    # Target
    df['target'] = (df['ppm_upm'] == 'UPM').astype(int)

    # Numeric features
    numeric_cols = ['mintemp_c', 'maxtemp_c', 'humidity_pct', 'snowmm',
                   'precipitationmm', 'totalcost', 'laborhours', 'woduration']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Aggregate to system-month level
    print("\nAggregating to system-month level...")
    print(f"Before aggregation: {len(df)} rows")
    print(f"Unique systems: {df['systemdescription'].nunique()}")
    print(f"Date range: {df['year'].min()}-{df['year'].max()}")

    grouped = df.groupby(['systemdescription', 'year', 'month']).agg({
        'target': ['sum', 'count', 'mean'],
        'mintemp_c': 'mean',
        'maxtemp_c': 'mean',
        'humidity_pct': 'mean',
        'snowmm': 'mean',
        'precipitationmm': 'mean',
        'totalcost': 'mean',
        'laborhours': 'mean',
        'woduration': 'mean',
    }).reset_index()

    # Flatten columns
    grouped.columns = ['system', 'year', 'month', 'upm_count', 'total_count',
                      'upm_rate', 'min_temp', 'max_temp', 'humidity',
                      'snow', 'precip', 'cost', 'labor_hrs', 'duration']

    # Add season
    grouped['season'] = grouped['month'].apply(lambda x:
        0 if x in [12, 1, 2] else
        1 if x in [3, 4, 5] else
        2 if x in [6, 7, 8] else 3
    )

    # One-hot encode top 5 systems
    top_systems = grouped['system'].value_counts().head(5).index
    for sys in top_systems:
        grouped[f'is_{sys.lower().replace(" ", "_")}'] = (grouped['system'] == sys).astype(int)

    print(f"Final dataset: {len(grouped)} system-month records")

    return grouped


def train_model(df):
    """Train XGBoost model"""
    print("\nTraining XGBoost model...")

    # Features
    feature_cols = ['month', 'season', 'min_temp', 'max_temp', 'humidity',
                   'snow', 'precip', 'total_count']

    # Add system columns
    system_cols = [col for col in df.columns if col.startswith('is_')]
    feature_cols.extend(system_cols)

    # Debug: Check before cleaning
    print(f"Before dropna: {len(df)} rows")
    print(f"Checking columns: {feature_cols + ['upm_rate']}")

    # Check which columns have nulls
    null_counts = df[feature_cols + ['upm_rate']].isnull().sum()
    print("\nNull counts in feature columns:")
    print(null_counts[null_counts > 0])

    # Remove rows with missing features
    df_clean = df.dropna(subset=feature_cols + ['upm_rate'])

    print(f"After dropna: {len(df_clean)} rows")

    X = df_clean[feature_cols]
    y = (df_clean['upm_rate'] > 0.5).astype(int)

    print(f"Training samples: {len(X)}")
    print(f"Features: {len(feature_cols)}")
    print(f"Target distribution: UPM={y.sum()}, PPM={(1-y).sum()}")

    if len(X) < 10:
        print("ERROR: Not enough samples to train")
        return None, None, None, None

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train
    model = xgb.XGBClassifier(
        max_depth=4,
        learning_rate=0.1,
        n_estimators=100,
        random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.3f}")

    try:
        print(f"ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.3f}")
    except:
        print("ROC-AUC: N/A")

    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop features:")
    print(importance.head(10).to_string(index=False))

    return model, df_clean, feature_cols, importance


def save_artifacts(model, df, feature_cols, importance):
    """Save model and data"""
    print("\nSaving artifacts...")

    # Create directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)

    # Save model
    joblib.dump(model, 'models/xgboost_upm_predictor.pkl')

    # Save data
    df.to_csv('data/processed/system_month_data.csv', index=False)

    # Save feature importance
    importance.to_csv('models/feature_importance.csv', index=False)

    # Save feature list
    with open('models/feature_columns.txt', 'w') as f:
        f.write('\n'.join(feature_cols))

    print("✓ Saved to models/ and data/processed/")


def main():
    """Main pipeline"""
    df = load_and_prepare_data(limit=50000)
    model, df_clean, feature_cols, importance = train_model(df)

    if model:
        save_artifacts(model, df_clean, feature_cols, importance)
        print("\n" + "="*60)
        print("✓ Training complete!")
        print("="*60)
    else:
        print("\n❌ Training failed")


if __name__ == "__main__":
    main()
