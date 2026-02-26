"""
Phase 3: Model Training & Prediction for Asset UPM Risk

This script:
1. Loads asset_features.parquet (~500K rows, ~40 features)
2. Defines feature columns for modeling
3. Creates time-based train/test split (80/20 by month rank)
4. Trains XGBoost classifier with class imbalance handling
5. Evaluates model on test set (target ROC-AUC >0.70)
6. Generates predictions on ALL data (train + test)
7. Saves model artifacts and predictions
8. Outputs: models/asset_upm_predictor.pkl, data/processed/predictions_with_metadata.parquet
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve,
    classification_report, confusion_matrix
)
import joblib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


def get_feature_columns(df):
    """
    Define feature columns for modeling.

    Excludes:
    - Entity identifiers (UniversityID, BuildingID, SystemDescription)
    - Time identifiers (year, month, month_date)
    - Target and event counts
    - Intermediate columns (system_category, Type)
    """
    exclude_cols = [
        # Entity identifiers
        'UniversityID', 'BuildingID', 'SystemDescription',

        # Time identifiers
        'year', 'month', 'month_date',

        # Target and event counts (these are what we're predicting)
        'target_asset_upm', 'UPM_total_event', 'UPM_asset_event', 'UPM_shock_event',

        # Intermediate columns
        'system_category', 'Type',
    ]

    feature_cols = [col for col in df.columns if col not in exclude_cols]

    return feature_cols


def create_time_based_split(df, train_ratio=0.8):
    """
    Create time-based train/test split.

    Split by month rank (not random) to test generalization to future.
    Train: First 80% of months
    Test: Last 20% of months
    """
    print("\n  Creating time-based split...")

    # Get unique months sorted
    unique_months = sorted(df['month_date'].unique())
    n_months = len(unique_months)

    split_idx = int(n_months * train_ratio)
    train_months = unique_months[:split_idx]
    test_months = unique_months[split_idx:]

    print(f"    Total months: {n_months}")
    print(f"    Train months: {len(train_months)} ({train_months[0]} to {train_months[-1]})")
    print(f"    Test months: {len(test_months)} ({test_months[0]} to {test_months[-1]})")

    # Create masks
    train_mask = df['month_date'].isin(train_months)
    test_mask = df['month_date'].isin(test_months)

    print(f"    Train samples: {train_mask.sum():,}")
    print(f"    Test samples: {test_mask.sum():,}")

    return train_mask, test_mask


def train_xgboost_model(X_train, y_train, X_test, y_test):
    """
    Train XGBoost classifier with class imbalance handling.

    Returns trained model and evaluation metrics.
    """
    print("\n  Training XGBoost model...")

    # Calculate class weights
    n_positive = y_train.sum()
    n_negative = len(y_train) - n_positive
    scale_pos_weight = n_negative / n_positive

    print(f"    Class distribution in training:")
    print(f"      Positive (1): {n_positive:,} ({n_positive/len(y_train)*100:.1f}%)")
    print(f"      Negative (0): {n_negative:,} ({n_negative/len(y_train)*100:.1f}%)")
    print(f"      scale_pos_weight: {scale_pos_weight:.2f}")

    # Define model parameters
    params = {
        'objective': 'binary:logistic',
        'max_depth': 6,
        'learning_rate': 0.05,
        'n_estimators': 300,
        'scale_pos_weight': scale_pos_weight,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'eval_metric': 'auc',
    }

    print(f"    Model parameters: {params}")

    # Train model
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=False
    )

    print(f"    ✓ Model trained with {model.n_estimators} estimators")

    return model


def evaluate_model(model, X_train, y_train, X_test, y_test):
    """
    Evaluate model performance on train and test sets.

    Returns evaluation metrics and predictions.
    """
    print("\n  Evaluating model...")

    # Predictions
    y_train_pred_proba = model.predict_proba(X_train)[:, 1]
    y_test_pred_proba = model.predict_proba(X_test)[:, 1]

    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # ROC-AUC
    train_auc = roc_auc_score(y_train, y_train_pred_proba)
    test_auc = roc_auc_score(y_test, y_test_pred_proba)

    print(f"\n    ROC-AUC Scores:")
    print(f"      Train: {train_auc:.4f}")
    print(f"      Test:  {test_auc:.4f}")
    print(f"      Gap:   {abs(train_auc - test_auc):.4f}")

    if test_auc >= 0.70:
        print(f"    ✓ Test AUC {test_auc:.4f} meets target (>0.70)")
    else:
        print(f"    ⚠ Test AUC {test_auc:.4f} below target (0.70)")

    # Classification report (test set)
    print(f"\n    Classification Report (Test Set):")
    print(classification_report(y_test, y_test_pred, target_names=['No Asset UPM', 'Asset UPM']))

    # Confusion matrix (test set)
    print(f"\n    Confusion Matrix (Test Set):")
    cm = confusion_matrix(y_test, y_test_pred)
    print(f"                 Predicted")
    print(f"                 0       1")
    print(f"    Actual 0  {cm[0,0]:6,}  {cm[0,1]:6,}")
    print(f"           1  {cm[1,0]:6,}  {cm[1,1]:6,}")

    return {
        'train_auc': train_auc,
        'test_auc': test_auc,
        'y_test_pred_proba': y_test_pred_proba,
        'y_train_pred_proba': y_train_pred_proba,
    }


def plot_roc_curve(y_test, y_test_pred_proba, output_dir):
    """
    Plot and save ROC curve.
    """
    fpr, tpr, _ = roc_curve(y_test, y_test_pred_proba)
    auc = roc_auc_score(y_test, y_test_pred_proba)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.4f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Asset UPM Prediction')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    output_path = output_dir / 'roc_curve.png'
    plt.savefig(output_path, dpi=100)
    print(f"    ✓ Saved ROC curve to {output_path}")
    plt.close()


def plot_precision_recall_curve(y_test, y_test_pred_proba, output_dir):
    """
    Plot and save Precision-Recall curve.
    """
    precision, recall, _ = precision_recall_curve(y_test, y_test_pred_proba)

    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, linewidth=2)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve - Asset UPM Prediction')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    output_path = output_dir / 'precision_recall_curve.png'
    plt.savefig(output_path, dpi=100)
    print(f"    ✓ Saved Precision-Recall curve to {output_path}")
    plt.close()


def save_feature_importance(model, feature_cols, output_dir):
    """
    Save feature importance rankings.
    """
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    output_path = output_dir / 'asset_feature_importance.csv'
    importance_df.to_csv(output_path, index=False)
    print(f"    ✓ Saved feature importance to {output_path}")

    # Print top 15 features
    print(f"\n    Top 15 Features:")
    for idx, row in importance_df.head(15).iterrows():
        print(f"      {row['feature']:30s} {row['importance']:.4f}")

    return importance_df


def main():
    print("=" * 80)
    print("PHASE 3: MODEL TRAINING & PREDICTION")
    print("=" * 80)

    # Load data
    print("\n[1/8] Loading asset_features.parquet...")
    input_path = 'data/processed/asset_features.parquet'
    df = pd.read_parquet(input_path)
    print(f"  Loaded {len(df):,} rows x {len(df.columns)} columns")

    # Get feature columns
    print("\n[2/8] Defining feature columns...")
    feature_cols = get_feature_columns(df)
    print(f"  Total features: {len(feature_cols)}")
    print(f"  Sample features: {feature_cols[:10]}")

    # Create train/test split
    print("\n[3/8] Creating time-based train/test split...")
    train_mask, test_mask = create_time_based_split(df, train_ratio=0.8)

    # Prepare feature matrices
    X_train = df.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, 'target_asset_upm']
    X_test = df.loc[test_mask, feature_cols]
    y_test = df.loc[test_mask, 'target_asset_upm']

    print(f"  X_train shape: {X_train.shape}")
    print(f"  X_test shape: {X_test.shape}")

    # Train model
    print("\n[4/8] Training XGBoost model...")
    model = train_xgboost_model(X_train, y_train, X_test, y_test)

    # Evaluate model
    print("\n[5/8] Evaluating model performance...")
    eval_results = evaluate_model(model, X_train, y_train, X_test, y_test)

    # Save visualizations
    print("\n[6/8] Saving evaluation plots...")
    output_dir = Path('models')
    output_dir.mkdir(exist_ok=True)

    plot_roc_curve(y_test, eval_results['y_test_pred_proba'], output_dir)
    plot_precision_recall_curve(y_test, eval_results['y_test_pred_proba'], output_dir)

    # Save feature importance
    print("\n[7/8] Saving feature importance...")
    importance_df = save_feature_importance(model, feature_cols, output_dir)

    # Generate predictions on ALL data
    print("\n[8/8] Generating predictions on full dataset...")
    X_all = df[feature_cols]
    df['risk_prob_asset'] = model.predict_proba(X_all)[:, 1]

    print(f"  Predictions generated for {len(df):,} rows")
    print(f"  Risk probability distribution:")
    print(f"    Min:    {df['risk_prob_asset'].min():.4f}")
    print(f"    25th:   {df['risk_prob_asset'].quantile(0.25):.4f}")
    print(f"    Median: {df['risk_prob_asset'].median():.4f}")
    print(f"    75th:   {df['risk_prob_asset'].quantile(0.75):.4f}")
    print(f"    Max:    {df['risk_prob_asset'].max():.4f}")

    # Save model
    print("\n" + "=" * 80)
    print("SAVING ARTIFACTS")
    print("=" * 80)

    model_path = output_dir / 'asset_upm_predictor.pkl'
    joblib.dump(model, model_path)
    print(f"\n✓ Saved model to {model_path}")

    # Save feature columns list
    feature_cols_path = output_dir / 'asset_feature_columns.txt'
    with open(feature_cols_path, 'w') as f:
        f.write('\n'.join(feature_cols))
    print(f"✓ Saved feature columns to {feature_cols_path}")

    # Save predictions with metadata
    predictions_path = 'data/processed/predictions_with_metadata.parquet'
    df.to_parquet(predictions_path, index=False)
    print(f"✓ Saved predictions to {predictions_path}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    # Check 1: Model performance
    print(f"\n✓ Model Performance:")
    print(f"  Train ROC-AUC: {eval_results['train_auc']:.4f}")
    print(f"  Test ROC-AUC:  {eval_results['test_auc']:.4f}")
    print(f"  Target met: {eval_results['test_auc'] >= 0.70}")

    # Check 2: Overfitting check
    print(f"\n✓ Overfitting Check:")
    gap = abs(eval_results['train_auc'] - eval_results['test_auc'])
    print(f"  Train-Test AUC Gap: {gap:.4f}")
    print(f"  Acceptable (<0.10): {gap < 0.10}")

    # Check 3: Feature importance
    print(f"\n✓ Feature Importance:")
    lag_features = [f for f in importance_df.head(10)['feature'] if 'last' in f or 'since' in f]
    print(f"  Lag features in top 10: {len(lag_features)}")
    print(f"  Features: {lag_features}")

    # Check 4: Prediction distribution
    print(f"\n✓ Prediction Distribution:")
    print(f"  All zeros: {(df['risk_prob_asset'] == 0).sum():,}")
    print(f"  All ones:  {(df['risk_prob_asset'] == 1).sum():,}")
    print(f"  In (0,1):  {((df['risk_prob_asset'] > 0) & (df['risk_prob_asset'] < 1)).sum():,}")

    print("\n" + "=" * 80)
    print("PHASE 3 COMPLETE!")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  - Model: {model_path}")
    print(f"  - Feature importance: {output_dir / 'asset_feature_importance.csv'}")
    print(f"  - Feature columns: {feature_cols_path}")
    print(f"  - Predictions: {predictions_path}")
    print(f"\nTest ROC-AUC: {eval_results['test_auc']:.4f}")
    print("\nNext step: Run scripts/generate_heatmaps.py")


if __name__ == '__main__':
    main()
