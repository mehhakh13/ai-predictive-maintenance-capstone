"""
Phase 2: Feature Engineering for Asset UPM Risk Prediction

This script:
1. Loads monthly_asset_upm.parquet (~500K rows)
2. Creates lag features (1m, 3m, 6m, months_since_asset_upm) by entity
3. Adds temporal encoding (month_sin, month_cos, season)
4. Creates derived features (building_age, avg_temp, temp_range)
5. One-hot encodes top 15 systems
6. Creates binary target: target_asset_upm = (UPM_asset_event > 0)
7. Handles NaNs with appropriate strategies
8. Outputs: data/processed/asset_features.parquet (~500K rows, ~40 features)
"""

import pandas as pd
import numpy as np


def create_lag_features(df, entity_cols):
    """
    Create lag features for asset UPM events.

    CRITICAL: Data must be sorted by entity + time before calling this function.

    Features created:
    - asset_upm_last_1m: Previous month's asset UPM count
    - asset_upm_last_3m: Sum of last 3 months (excluding current)
    - asset_upm_last_6m: Sum of last 6 months (excluding current)
    - months_since_asset_upm: Number of months since last asset UPM (999 if never)
    """
    print("\n  Creating lag features by entity...")

    # Sort by entity + time (CRITICAL)
    df = df.sort_values(entity_cols + ['year', 'month']).reset_index(drop=True)

    # Group by entity
    entity_group = df.groupby(entity_cols, group_keys=False)

    # 1-month lag (shift 1)
    print("    - asset_upm_last_1m (shift 1)")
    df['asset_upm_last_1m'] = entity_group['UPM_asset_event'].shift(1).fillna(0).astype(int)

    # 3-month rolling sum (exclude current month)
    print("    - asset_upm_last_3m (rolling 3, exclude current)")
    df['asset_upm_last_3m'] = (
        entity_group['UPM_asset_event']
        .rolling(window=4, min_periods=1)
        .sum()
        .shift(1)
        .fillna(0)
        .astype(int)
    )

    # 6-month rolling sum (exclude current month)
    print("    - asset_upm_last_6m (rolling 6, exclude current)")
    df['asset_upm_last_6m'] = (
        entity_group['UPM_asset_event']
        .rolling(window=7, min_periods=1)
        .sum()
        .shift(1)
        .fillna(0)
        .astype(int)
    )

    # Months since last asset UPM
    print("    - months_since_asset_upm (custom calculation)")

    def months_since_last_event(series):
        """Calculate months since last non-zero event (999 if never occurred)"""
        result = []
        last_event_idx = None

        for idx, val in enumerate(series.values):
            if val > 0:
                last_event_idx = idx

            if last_event_idx is None:
                result.append(999)  # Never occurred
            else:
                result.append(idx - last_event_idx)

        return pd.Series(result, index=series.index)

    df['months_since_asset_upm'] = entity_group['UPM_asset_event'].transform(months_since_last_event)

    return df


def create_temporal_features(df):
    """
    Create temporal encoding features.

    Features:
    - month_sin, month_cos: Cyclical encoding of month (1-12)
    - season: 0=Winter, 1=Spring, 2=Summer, 3=Fall
    """
    print("\n  Creating temporal features...")

    # Cyclical encoding of month
    print("    - month_sin, month_cos (cyclical encoding)")
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    # Season (0-3)
    print("    - season (0=Winter, 1=Spring, 2=Summer, 3=Fall)")
    def get_season(month):
        if month in [12, 1, 2]:
            return 0  # Winter
        elif month in [3, 4, 5]:
            return 1  # Spring
        elif month in [6, 7, 8]:
            return 2  # Summer
        else:
            return 3  # Fall

    df['season'] = df['month'].apply(get_season)

    return df


def create_derived_features(df):
    """
    Create derived features from existing columns.

    Features:
    - building_age: year - BuiltYear
    - avg_temp: (MinTemp + MaxTemp) / 2
    - temp_range: MaxTemp - MinTemp
    """
    print("\n  Creating derived features...")

    # Building age
    print("    - building_age")
    df['building_age'] = df['year'] - df['BuiltYear']
    # Handle negative ages (data errors) - set to 0
    df.loc[df['building_age'] < 0, 'building_age'] = 0

    # Temperature features
    print("    - avg_temp, temp_range")
    df['avg_temp'] = (df['MinTemp'] + df['MaxTemp']) / 2
    df['temp_range'] = df['MaxTemp'] - df['MinTemp']

    return df


def encode_systems(df, top_n=15):
    """
    One-hot encode top N systems, group rest as 'Other'.

    Returns df with system_* columns added.
    """
    print(f"\n  One-hot encoding top {top_n} systems...")

    # Get top N systems by occurrence
    top_systems = df['SystemDescription'].value_counts().head(top_n).index.tolist()
    print(f"    Top {top_n} systems: {top_systems[:5]}... (and {top_n-5} more)")

    # Create 'Other' category
    df['system_category'] = df['SystemDescription'].apply(
        lambda x: x if x in top_systems else 'Other'
    )

    # One-hot encode
    system_dummies = pd.get_dummies(df['system_category'], prefix='system')

    # Add to df
    df = pd.concat([df, system_dummies], axis=1)

    print(f"    Created {len(system_dummies.columns)} system columns")

    return df


def create_target(df):
    """
    Create binary target variable.

    target_asset_upm = 1 if UPM_asset_event > 0, else 0
    """
    print("\n  Creating target variable...")
    df['target_asset_upm'] = (df['UPM_asset_event'] > 0).astype(int)

    print(f"    Target distribution:")
    print(f"      Positive (1): {df['target_asset_upm'].sum():,} ({df['target_asset_upm'].mean()*100:.1f}%)")
    print(f"      Negative (0): {(df['target_asset_upm']==0).sum():,} ({(df['target_asset_upm']==0).mean()*100:.1f}%)")

    return df


def handle_missing_values(df):
    """
    Fill NaNs with appropriate strategies.

    - Lag features: Already filled with 0
    - Building context: Median imputation
    - Weather: Already interpolated in Phase 1, but fill any remaining with median
    - WO characteristics: Median imputation
    """
    print("\n  Handling missing values...")

    # Building context - median imputation
    building_cols = ['BuiltYear', 'Size', 'FCI', 'DMC', 'CRV', 'building_age']
    for col in building_cols:
        if col in df.columns:
            null_count_before = df[col].isna().sum()
            if null_count_before > 0:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"    - {col}: Filled {null_count_before:,} nulls with median ({median_val:.2f})")

    # Weather - median imputation for any remaining nulls
    weather_cols = ['MinTemp', 'MaxTemp', 'Humidity', 'Precipitation', 'Snow', 'avg_temp', 'temp_range']
    for col in weather_cols:
        if col in df.columns:
            null_count_before = df[col].isna().sum()
            if null_count_before > 0:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"    - {col}: Filled {null_count_before:,} nulls with median ({median_val:.2f})")

    # WO characteristics - median imputation
    wo_cols = ['WOPriority', 'WODuration']
    for col in wo_cols:
        if col in df.columns:
            null_count_before = df[col].isna().sum()
            if null_count_before > 0:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"    - {col}: Filled {null_count_before:,} nulls with median ({median_val:.2f})")

    # Check for any remaining nulls
    print("\n  Final null check:")
    null_cols = df.columns[df.isna().any()].tolist()
    if null_cols:
        print(f"    WARNING: {len(null_cols)} columns still have nulls:")
        for col in null_cols:
            print(f"      - {col}: {df[col].isna().sum():,} nulls")
    else:
        print("    ✓ No nulls remaining in dataset")

    return df


def main():
    print("=" * 80)
    print("PHASE 2: FEATURE ENGINEERING")
    print("=" * 80)

    # Load data
    print("\n[1/7] Loading monthly_asset_upm.parquet...")
    input_path = 'data/processed/monthly_asset_upm.parquet'
    df = pd.read_parquet(input_path)
    print(f"  Loaded {len(df):,} rows x {len(df.columns)} columns")

    # Define entity columns
    entity_cols = ['UniversityID', 'BuildingID', 'SystemDescription']

    # Create lag features
    print("\n[2/7] Creating lag features...")
    df = create_lag_features(df, entity_cols)

    # Create temporal features
    print("\n[3/7] Creating temporal features...")
    df = create_temporal_features(df)

    # Create derived features
    print("\n[4/7] Creating derived features...")
    df = create_derived_features(df)

    # One-hot encode systems
    print("\n[5/7] Encoding system categories...")
    df = encode_systems(df, top_n=15)

    # Create target
    print("\n[6/7] Creating target variable...")
    df = create_target(df)

    # Handle missing values
    print("\n[7/7] Handling missing values...")
    df = handle_missing_values(df)

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    # Check 1: Lag features spot check
    print("\n✓ Lag features spot check (first entity, first 10 months):")
    first_entity = df.groupby(entity_cols).head(10).iloc[:10]
    lag_cols = ['month_date', 'UPM_asset_event', 'asset_upm_last_1m', 'asset_upm_last_3m',
                'asset_upm_last_6m', 'months_since_asset_upm']
    print(first_entity[lag_cols].to_string(index=False))

    # Check 2: Feature count
    print(f"\n✓ Feature count:")
    feature_cols = [col for col in df.columns if col not in entity_cols + ['month_date', 'year', 'month', 'SystemDescription', 'system_category', 'Type']]
    print(f"  Total features: {len(feature_cols)}")
    print(f"  Feature list:")
    for col in sorted(feature_cols):
        print(f"    - {col}")

    # Check 3: No NaNs in final dataset
    print(f"\n✓ NaN check:")
    total_nulls = df.isna().sum().sum()
    print(f"  Total NaNs in dataset: {total_nulls:,}")

    # Check 4: Target distribution
    print(f"\n✓ Target distribution:")
    print(f"  Class balance: {df['target_asset_upm'].value_counts(normalize=True).to_dict()}")

    # Check 5: Feature distributions
    print(f"\n✓ Feature distributions (sample):")
    sample_features = ['asset_upm_last_1m', 'building_age', 'avg_temp', 'season']
    for col in sample_features:
        if col in df.columns:
            print(f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}, median={df[col].median():.2f}")

    # Save output
    print("\n" + "=" * 80)
    output_path = 'data/processed/asset_features.parquet'
    print(f"Saving to {output_path}...")
    df.to_parquet(output_path, index=False)
    print(f"✓ Saved {len(df):,} rows x {len(df.columns)} columns")

    print("\n" + "=" * 80)
    print("PHASE 2 COMPLETE!")
    print("=" * 80)
    print(f"\nOutput: {output_path}")
    print(f"Size: {len(df):,} rows x {len(df.columns)} columns")
    print(f"Features: ~{len(feature_cols)} features created")
    print("\nNext step: Run scripts/train_asset_upm_model.py")


if __name__ == '__main__':
    main()
