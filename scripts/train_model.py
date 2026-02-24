#!/usr/bin/env python3
"""
Train XGBoost Model for Predictive Maintenance
Predicts UPM probability at system-month level
"""

import os
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, accuracy_score, precision_recall_curve, auc
)
import matplotlib.pyplot as plt
import seaborn as sns


def load_processed_data():
    """Load preprocessed features"""
    data_dir = "/home/sradmin/ai-predictive-maintenance-capstone/data/processed"

    print("Loading processed data...")
    X = pd.read_csv(f"{data_dir}/X_features.csv")
    y = pd.read_csv(f"{data_dir}/y_target.csv").squeeze()
    metadata = pd.read_csv(f"{data_dir}/metadata.csv")

    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")

    return X, y, metadata


def train_xgboost_model(X, y, test_size=0.2, random_state=42):
    """
    Train XGBoost classifier for UPM probability prediction
    """
    print("\n" + "="*60)
    print("Training XGBoost Model")
    print("="*60)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=None
    )

    print(f"\nTrain set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")

    # Convert to binary classification (threshold at 0.5)
    y_train_binary = (y_train > 0.5).astype(int)
    y_test_binary = (y_test > 0.5).astype(int)

    print(f"\nTarget distribution (binary):")
    print(f"Train - UPM: {y_train_binary.sum()}, PPM: {len(y_train_binary) - y_train_binary.sum()}")
    print(f"Test - UPM: {y_test_binary.sum()}, PPM: {len(y_test_binary) - y_test_binary.sum()}")

    # XGBoost parameters
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'logloss',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': random_state,
        'tree_method': 'hist',
        'enable_categorical': False,
    }

    print(f"\nXGBoost Parameters:")
    for key, val in params.items():
        print(f"  {key}: {val}")

    # Train model
    print("\nTraining model...")
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train_binary,
        eval_set=[(X_train, y_train_binary), (X_test, y_test_binary)],
        verbose=False
    )

    print("✓ Training complete")

    # Predictions
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)

    # Evaluation metrics
    print("\n" + "="*60)
    print("Model Evaluation")
    print("="*60)

    accuracy = accuracy_score(y_test_binary, y_pred)

    # Handle case where only one class in test set
    try:
        roc_auc = roc_auc_score(y_test_binary, y_pred_proba)
        print(f"\nAccuracy: {accuracy:.4f}")
        print(f"ROC-AUC: {roc_auc:.4f}")
    except ValueError:
        roc_auc = None
        print(f"\nAccuracy: {accuracy:.4f}")
        print("ROC-AUC: N/A (only one class in test set)")

    print("\nClassification Report:")
    # Use labels parameter to handle missing classes
    print(classification_report(y_test_binary, y_pred,
                               labels=[0, 1],
                               target_names=['PPM', 'UPM'],
                               zero_division=0))

    # Feature importance
    print("\nTop 10 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(feature_importance.head(10).to_string(index=False))

    return model, X_test, y_test, y_pred_proba, feature_importance


def save_model_artifacts(model, feature_importance, feature_cols):
    """Save trained model and metadata"""
    model_dir = "/home/sradmin/ai-predictive-maintenance-capstone/models"
    os.makedirs(model_dir, exist_ok=True)

    print(f"\nSaving model artifacts to {model_dir}/")

    # Save model
    model_path = f"{model_dir}/xgboost_upm_predictor.pkl"
    joblib.dump(model, model_path)
    print(f"✓ Saved model: {model_path}")

    # Save feature importance
    feature_importance.to_csv(f"{model_dir}/feature_importance.csv", index=False)
    print(f"✓ Saved feature importance")

    # Save feature columns
    with open(f"{model_dir}/feature_columns.txt", 'w') as f:
        f.write('\n'.join(feature_cols))
    print(f"✓ Saved feature columns")


def main():
    """Main training pipeline"""
    print("="*60)
    print("XGBoost Training Pipeline")
    print("="*60)

    # Load data
    X, y, metadata = load_processed_data()

    # Train model
    model, X_test, y_test, y_pred_proba, feature_importance = train_xgboost_model(X, y)

    # Save artifacts
    save_model_artifacts(model, feature_importance, X.columns.tolist())

    print("\n" + "="*60)
    print("✓ Training pipeline complete!")
    print("="*60)

    return model, feature_importance


if __name__ == "__main__":
    main()
