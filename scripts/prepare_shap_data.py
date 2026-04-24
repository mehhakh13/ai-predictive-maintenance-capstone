#!/usr/bin/env python3
"""
SHAP Explainability Feature - Data Preparation
University 1 (Canada) only: best data quality (FCI 95.6%, all weather 100%, TotalCost 100%)
Aggregates raw work orders to building x subsystem x month level
WOPriority intentionally excluded: it's label leakage (priority 1/2/4 = 99% UPM, priority 3/5 = 99% PPM)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "fmucd_canada.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "shap"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)


def load_and_filter():
    print("Loading CSV (University 1 only)...")
    df = pd.read_csv(CSV_PATH, low_memory=False)

    # University 1 = Canada, best across-the-board data quality
    df = df[df['UniversityID'] == 1].copy()

    # Option C: only buildings with FCI data (per decision)
    df = df[df['FCI (facility condition index)'].notna()].copy()

    print(f"  After filter: {len(df):,} rows, {df['BuildingID'].nunique()} buildings")
    return df


def preprocess(df):
    print("Preprocessing...")
    df['WOStartDate'] = pd.to_datetime(df['WOStartDate'], errors='coerce')
    df = df.dropna(subset=['WOStartDate', 'BuildingID', 'SubsystemDescription']).copy()

    df['year'] = df['WOStartDate'].dt.year
    df['month'] = df['WOStartDate'].dt.month
    df['is_upm'] = (df['PPM/UPM'] == 'UPM').astype(int)

    numeric_cols = [
        'WODuration', 'LaborHours', 'TotalCost', 'LaborCost',
        'FCI (facility condition index)', 'BuiltYear', 'Size',
        'MinTemp.(°C)', 'MaxTemp.(°C)', 'Humidity(%)',
        'Precipitation(mm)', 'Snow(mm)', 'Cloudness(%)',
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    print(f"  After preprocess: {len(df):,} rows")
    return df


def aggregate_descriptions(df):
    """
    Build four description columns per building x subsystem x month:
      upm_descriptions  — this month's UPM work-order descriptions (up to 5)
      ppm_descriptions  — this month's PPM work-order descriptions (up to 5)
      hist_upm_descriptions — top recurring UPM descriptions for this entity (all time)
      hist_ppm_descriptions — top recurring PPM descriptions for this entity (all time)
    Stored as '|||'-separated strings so they survive parquet serialisation.
    """
    print("Aggregating WO descriptions...")
    SEP = '|||'
    month_cols = ['BuildingID', 'SubsystemDescription', 'year', 'month']
    entity_cols = ['BuildingID', 'SubsystemDescription']

    def join_unique(series, n):
        vals = series.dropna().str.strip().str.upper()
        return SEP.join(vals.unique()[:n]) if len(vals) else ''

    def join_top(series, n):
        vals = series.dropna().str.strip().str.upper()
        return SEP.join(vals.value_counts().head(n).index.tolist()) if len(vals) else ''

    upm = df[df['is_upm'] == 1]
    ppm = df[df['is_upm'] == 0]

    monthly_upm = (upm.groupby(month_cols)['WODescription']
                   .apply(lambda x: join_unique(x, 5))
                   .reset_index(name='upm_descriptions'))

    monthly_ppm = (ppm.groupby(month_cols)['WODescription']
                   .apply(lambda x: join_unique(x, 5))
                   .reset_index(name='ppm_descriptions'))

    hist_upm = (upm.groupby(entity_cols)['WODescription']
                .apply(lambda x: join_top(x, 5))
                .reset_index(name='hist_upm_descriptions'))

    hist_ppm = (ppm.groupby(entity_cols)['WODescription']
                .apply(lambda x: join_top(x, 5))
                .reset_index(name='hist_ppm_descriptions'))

    print(f"  Monthly UPM descriptions: {len(monthly_upm):,} rows")
    print(f"  Monthly PPM descriptions: {len(monthly_ppm):,} rows")
    return monthly_upm, monthly_ppm, hist_upm, hist_ppm


def aggregate_to_monthly(df):
    print("Aggregating to building x subsystem x month...")
    group_cols = ['BuildingID', 'BuildingName', 'SubsystemDescription', 'year', 'month']

    agg = df.groupby(group_cols, dropna=False).agg(
        upm_count=('is_upm', 'sum'),
        wo_count=('WOID', 'count'),
        avg_wo_duration=('WODuration', 'mean'),
        avg_labor_hours=('LaborHours', 'mean'),
        avg_total_cost=('TotalCost', 'mean'),
        total_monthly_cost=('TotalCost', 'sum'),
        fci=('FCI (facility condition index)', 'mean'),
        built_year=('BuiltYear', 'first'),
        size=('Size', 'first'),
        min_temp=('MinTemp.(°C)', 'mean'),
        max_temp=('MaxTemp.(°C)', 'mean'),
        humidity=('Humidity(%)', 'mean'),
        precipitation=('Precipitation(mm)', 'mean'),
        snow=('Snow(mm)', 'mean'),
        cloudness=('Cloudness(%)', 'mean'),
    ).reset_index()

    agg['target_upm'] = (agg['upm_count'] > 0).astype(int)

    print(f"  Aggregated: {len(agg):,} rows | UPM rate: {agg['target_upm'].mean():.3f}")
    return agg


def create_temporal_features(df):
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['season'] = df['month'].map(
        lambda m: 0 if m in [12, 1, 2] else (1 if m in [3, 4, 5] else (2 if m in [6, 7, 8] else 3))
    )
    return df


def create_derived_features(df):
    df['building_age'] = df['year'] - df['built_year']
    df.loc[df['building_age'] < 0, 'building_age'] = 0
    df['avg_temp'] = (df['min_temp'] + df['max_temp']) / 2
    df['temp_range'] = df['max_temp'] - df['min_temp']
    return df


def create_lag_features(df):
    print("Creating lag features (sorted by entity + time)...")
    entity_cols = ['BuildingID', 'SubsystemDescription']
    df = df.sort_values(entity_cols + ['year', 'month']).reset_index(drop=True)
    grp = df.groupby(entity_cols, group_keys=False)

    df['upm_last_1m'] = grp['upm_count'].shift(1).fillna(0).astype(int)

    df['upm_last_3m'] = grp['upm_count'].transform(
        lambda x: x.rolling(4, min_periods=1).sum().shift(1).fillna(0)
    ).astype(int)

    df['upm_last_6m'] = grp['upm_count'].transform(
        lambda x: x.rolling(7, min_periods=1).sum().shift(1).fillna(0)
    ).astype(int)

    def months_since_last(series):
        # IMPORTANT: compute result BEFORE updating last_idx to avoid leaking
        # the current month's UPM event into its own feature value.
        result = []
        last_idx = None
        for idx, val in enumerate(series.values):
            result.append(idx - last_idx if last_idx is not None else 24)
            if val > 0:
                last_idx = idx
        return pd.Series(result, index=series.index)

    df['months_since_upm'] = grp['upm_count'].transform(months_since_last)
    return df


def encode_subsystems(df, top_n=20):
    print(f"One-hot encoding top {top_n} subsystems...")
    top_subs = df['SubsystemDescription'].value_counts().head(top_n).index.tolist()
    # Use _sub_cat (leading underscore) to avoid clashing with the subsystem_ feature prefix
    df['_sub_cat'] = df['SubsystemDescription'].apply(
        lambda x: x if x in top_subs else 'Other'
    )
    dummies = pd.get_dummies(df['_sub_cat'], prefix='subsystem', drop_first=False)
    df = pd.concat([df, dummies.astype(int)], axis=1)
    df.drop(columns=['_sub_cat'], inplace=True)
    print(f"  Created {len(dummies.columns)} subsystem columns")
    return df, top_subs


def handle_nulls(df, feature_cols):
    print("Imputing missing values...")
    for col in feature_cols:
        n_null = df[col].isna().sum()
        if n_null > 0:
            median = df[col].median()
            df[col] = df[col].fillna(median)
            print(f"  {col}: {n_null:,} nulls → filled with median {median:.2f}")
    return df


def save_buildings_meta(df):
    print("Saving buildings metadata for frontend...")
    building_months = (
        df.groupby(['BuildingID', 'BuildingName'])[['year', 'month']]
        .apply(lambda g: sorted(g.drop_duplicates().to_dict('records'), key=lambda r: (r['year'], r['month'])))
        .reset_index(name='available_months')
    )

    meta = []
    for _, row in building_months.iterrows():
        bname = str(row['BuildingName']) if pd.notna(row['BuildingName']) else f"Building {row['BuildingID']}"
        meta.append({
            'building_id': str(row['BuildingID']),
            'building_name': bname,
            'available_months': row['available_months'],
        })
    meta.sort(key=lambda x: x['building_name'])

    with open(OUTPUT_DIR / "buildings_meta.json", 'w') as f:
        json.dump(meta, f)
    print(f"  Saved metadata for {len(meta)} buildings")


def main():
    print("=" * 70)
    print("SHAP DATA PREPARATION")
    print("=" * 70)

    raw = load_and_filter()
    raw = preprocess(raw)

    # Collect descriptions BEFORE aggregation (needs individual WO rows)
    monthly_upm_desc, monthly_ppm_desc, hist_upm_desc, hist_ppm_desc = aggregate_descriptions(raw)

    df = aggregate_to_monthly(raw)
    df = create_temporal_features(df)
    df = create_derived_features(df)
    df = create_lag_features(df)
    df, _ = encode_subsystems(df, top_n=20)

    # Merge description columns in
    merge_cols = ['BuildingID', 'SubsystemDescription', 'year', 'month']
    df = df.merge(monthly_upm_desc, on=merge_cols, how='left')
    df = df.merge(monthly_ppm_desc, on=merge_cols, how='left')
    df = df.merge(hist_upm_desc, on=['BuildingID', 'SubsystemDescription'], how='left')
    df = df.merge(hist_ppm_desc, on=['BuildingID', 'SubsystemDescription'], how='left')
    for col in ['upm_descriptions', 'ppm_descriptions', 'hist_upm_descriptions', 'hist_ppm_descriptions']:
        df[col] = df[col].fillna('')

    subsystem_cols = [c for c in df.columns if c.startswith('subsystem_')]
    feature_cols = [
        'month_sin', 'month_cos', 'season',
        'min_temp', 'max_temp', 'avg_temp', 'temp_range',
        'humidity', 'precipitation', 'snow', 'cloudness',
        'fci', 'building_age', 'size',
        'upm_last_1m', 'upm_last_3m', 'upm_last_6m', 'months_since_upm',
        'avg_labor_hours', 'avg_wo_duration', 'wo_count',
        'avg_total_cost', 'total_monthly_cost',
    ] + subsystem_cols

    df = handle_nulls(df, feature_cols)

    # Save prepared data
    df.to_parquet(OUTPUT_DIR / "prepared_data.parquet", index=False)

    # Save feature column list for training script
    with open(MODELS_DIR / "shap_feature_columns.json", 'w') as f:
        json.dump(feature_cols, f, indent=2)

    save_buildings_meta(df)

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"  data/shap/prepared_data.parquet  — {len(df):,} rows x {len(df.columns)} cols")
    print(f"  models/shap_feature_columns.json — {len(feature_cols)} features")
    print(f"  data/shap/buildings_meta.json    — {df['BuildingID'].nunique()} buildings")
    print(f"  Target UPM rate: {df['target_upm'].mean():.3f}")
    print(f"  Date range: {df['year'].min()}-{df['month'].min():02d} → {df['year'].max()}-{df['month'].max():02d}")


if __name__ == '__main__':
    main()
