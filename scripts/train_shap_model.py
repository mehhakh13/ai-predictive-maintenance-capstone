#!/usr/bin/env python3
"""
SHAP Explainability Feature - Model Training + SHAP Value Computation
Trains XGBoost on building x subsystem x month (University 1)
Pre-computes SHAP values for all rows and saves as parquet for the API
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import joblib
import json
from pathlib import Path
from sklearn.metrics import roc_auc_score, classification_report

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "shap" / "prepared_data.parquet"
MODEL_DIR = PROJECT_ROOT / "models"
SHAP_OUTPUT = PROJECT_ROOT / "data" / "shap" / "shap_values.parquet"


def load_feature_cols():
    with open(MODEL_DIR / "shap_feature_columns.json") as f:
        return json.load(f)


def time_based_split(df, train_ratio=0.8):
    """Split by month chronologically — no data leakage from future."""
    unique_months = sorted(
        df[['year', 'month']].drop_duplicates()
        .apply(lambda r: f"{r['year']:04d}-{r['month']:02d}", axis=1)
        .tolist()
    )
    split_idx = int(len(unique_months) * train_ratio)
    train_months = set(unique_months[:split_idx])

    df['_ym'] = df['year'].apply(lambda y: f"{y:04d}") + '-' + df['month'].apply(lambda m: f"{m:02d}")
    mask = df['_ym'].isin(train_months)
    df.drop(columns=['_ym'], inplace=True)

    print(f"  Train: {mask.sum():,} rows ({unique_months[0]} → {unique_months[split_idx-1]})")
    print(f"  Test:  {(~mask).sum():,} rows ({unique_months[split_idx]} → {unique_months[-1]})")
    return mask


def train_model(X_train, y_train, X_test, y_test):
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

    print(f"  Positive: {n_pos:,} ({n_pos/len(y_train)*100:.1f}%)  "
          f"Negative: {n_neg:,}  scale_pos_weight: {scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        objective='binary:logistic',
        max_depth=6,
        learning_rate=0.05,
        n_estimators=300,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='auc',
        verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    train_auc = roc_auc_score(y_train, model.predict_proba(X_train)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"  Train AUC: {train_auc:.4f}  |  Test AUC: {test_auc:.4f}")

    if test_auc >= 0.70:
        print(f"  ✓ Meets target (> 0.70)")
    else:
        print(f"  ⚠ Below target (0.70) — consider feature review")

    y_pred = model.predict(X_test)
    print("\n  Classification Report (test):")
    print(classification_report(y_test, y_pred, target_names=['PPM', 'UPM'], zero_division=0))

    return model, test_auc


def compute_and_save_shap(model, df, X_all, feature_cols):
    print("Computing SHAP values (TreeExplainer — this may take a minute)...")
    explainer = shap.TreeExplainer(model)
    shap_matrix = explainer.shap_values(X_all)
    expected_value = float(explainer.expected_value)

    print(f"  Base value (expected): {expected_value:.4f}")
    print(f"  SHAP matrix shape: {shap_matrix.shape}")

    # Build output: metadata + risk_prob + shap + val per feature
    desc_cols = [c for c in ['upm_descriptions', 'ppm_descriptions',
                              'hist_upm_descriptions', 'hist_ppm_descriptions']
                 if c in df.columns]
    meta_cols = ['BuildingID', 'BuildingName', 'SubsystemDescription', 'year', 'month'] + desc_cols
    result = df[meta_cols].copy().reset_index(drop=True)
    result['risk_prob'] = model.predict_proba(X_all)[:, 1]
    result['shap_base'] = expected_value

    for i, feat in enumerate(feature_cols):
        result[f'shap_{feat}'] = shap_matrix[:, i]

    for feat in feature_cols:
        result[f'val_{feat}'] = X_all[feat].values

    result.to_parquet(SHAP_OUTPUT, index=False)
    print(f"  Saved → data/shap/shap_values.parquet ({len(result):,} rows)")

    # Save expected value separately for the API
    with open(MODEL_DIR / "shap_expected_value.json", 'w') as f:
        json.dump({'expected_value': expected_value}, f)

    return expected_value


def print_top_features(model, feature_cols, top_n=15):
    importance = sorted(
        zip(feature_cols, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    print(f"\n  Top {top_n} features by XGBoost importance:")
    for feat, imp in importance[:top_n]:
        bar = '█' * int(imp * 200)
        print(f"    {feat:<40s} {imp:.4f}  {bar}")


def main():
    print("=" * 70)
    print("SHAP MODEL TRAINING")
    print("=" * 70)

    df = pd.read_parquet(DATA_PATH)
    print(f"Loaded: {len(df):,} rows")

    feature_cols = load_feature_cols()
    print(f"Features: {len(feature_cols)}")

    X = df[feature_cols].copy()
    y = df['target_upm']

    print("\n[1/4] Time-based split...")
    train_mask = time_based_split(df)
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]

    print("\n[2/4] Training XGBoost...")
    model, test_auc = train_model(X_train, y_train, X_test, y_test)

    print_top_features(model, feature_cols)

    print("\n[3/4] Saving model...")
    joblib.dump(model, MODEL_DIR / "shap_model.pkl")
    print(f"  Saved → models/shap_model.pkl")

    print("\n[4/4] Computing & saving SHAP values...")
    expected_value = compute_and_save_shap(model, df, X, feature_cols)

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"  models/shap_model.pkl")
    print(f"  models/shap_feature_columns.json")
    print(f"  models/shap_expected_value.json")
    print(f"  data/shap/shap_values.parquet")
    print(f"  Test AUC: {test_auc:.4f}")
    print()
    print("Next: start backend with  uvicorn backend.main:app --reload")


if __name__ == '__main__':
    main()
