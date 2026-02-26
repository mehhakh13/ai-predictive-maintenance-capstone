"""
Phase 1: Data Preparation & Classification for Asset UPM Risk Prediction

This script:
1. Loads FMUCD_USA.parquet (3.3M work orders)
2. Classifies UPM events into shock/asset/unknown using keyword matching
3. Creates monthly aggregations by entity (University, Building, System)
4. Generates smart monthly grids (only for active periods, not full 227 months)
5. Zero-fills missing months within each entity's active period
6. Outputs: data/processed/monthly_asset_upm.parquet (~500K rows)
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime

# Enhanced keyword lists for shock vs asset classification
SHOCK_KEYWORDS = [
    'damage', 'damaged', 'damaging',
    'broken', 'broke', 'break', 'breaking',
    'shatter', 'shattered', 'smash', 'smashed',
    'vandal', 'vandalism', 'vandalized',
    'accident', 'accidental',
    'impact', 'impacted', 'strike', 'struck', 'hit',
    'crash', 'crashed',
    'storm', 'wind', 'lightning', 'flood', 'flooded',
    'freeze', 'frozen', 'ice',
    'spill', 'spilled', 'knocked', 'bumped', 'dropped',
]

ASSET_KEYWORDS = [
    'wear', 'worn', 'wearing',
    'deteriorat', 'deteriorated', 'deteriorating',
    'degrad', 'degraded', 'degrading',
    'aging', 'aged', 'old',
    'corros', 'corroded', 'corroding', 'rust', 'rusted', 'rusting',
    'erode', 'eroded', 'eroding',
    'fail', 'failed', 'failing', 'failure',
    'malfunc', 'malfunction', 'malfunctioning',
    'leak', 'leaking', 'leaks', 'leaked', 'leaky',
    'seep', 'seepage', 'drip', 'dripping',
    'clog', 'clogged', 'clogging', 'block', 'blocked', 'blockage',
    'obstruct', 'obstructed',
    'expired', 'exhausted', 'consumed',
]

# Contextual patterns (higher confidence)
CONTEXTUAL_PATTERNS = {
    'shock': [
        r'door.*broken', r'broken.*door', r'window.*broken', r'alarm.*false'
    ],
    'asset': [
        r'water.*leak', r'leak.*water', r'toilet.*leak', r'pipe.*leak',
        r'alarm.*fire', r'replace.*old'
    ]
}


def classify_upm_type(description):
    """
    Classify UPM work order into 'shock', 'asset', or 'unknown'.

    Expected: 70-80% will be 'unknown' - this is acceptable.

    Logic:
    1. Check contextual patterns first (most reliable)
    2. Check keywords with conflict resolution (first keyword wins)
    3. Default to 'unknown'
    """
    if pd.isna(description):
        return 'unknown'

    desc_lower = str(description).lower()

    # Check contextual patterns first (highest confidence)
    for pattern in CONTEXTUAL_PATTERNS['shock']:
        if re.search(pattern, desc_lower):
            return 'shock'

    for pattern in CONTEXTUAL_PATTERNS['asset']:
        if re.search(pattern, desc_lower):
            return 'asset'

    # Check keywords - first match wins (conflict resolution)
    shock_found = None
    asset_found = None

    for keyword in SHOCK_KEYWORDS:
        if keyword in desc_lower:
            if shock_found is None:
                shock_found = desc_lower.find(keyword)

    for keyword in ASSET_KEYWORDS:
        if keyword in desc_lower:
            if asset_found is None:
                asset_found = desc_lower.find(keyword)

    # First keyword wins
    if shock_found is not None and asset_found is not None:
        return 'shock' if shock_found < asset_found else 'asset'
    elif shock_found is not None:
        return 'shock'
    elif asset_found is not None:
        return 'asset'
    else:
        return 'unknown'


def main():
    print("=" * 80)
    print("PHASE 1: DATA PREPARATION & CLASSIFICATION")
    print("=" * 80)

    # Load data
    print("\n[1/6] Loading FMUCD_USA.parquet...")
    df = pd.read_parquet('FMUCD_USA.parquet')
    print(f"  Loaded {len(df):,} work orders")
    print(f"  Original columns: {len(df.columns)}")

    # Rename columns for easier handling
    print("  Renaming columns...")
    df.rename(columns={
        'PPM/UPM': 'PPMorUPM',
        'FCI (facility condition index)': 'FCI',
        'DMC (deferred maintenance cost)': 'DMC',
        'CRV (current replacement value)': 'CRV',
        'MinTemp.(°C)': 'MinTemp',
        'MaxTemp.(°C)': 'MaxTemp',
        'Humidity(%)': 'Humidity',
        'Precipitation(mm)': 'Precipitation',
        'Snow(mm)': 'Snow',
    }, inplace=True)
    print(f"  Renamed columns: {list(df.columns)}")

    # Parse dates and create time features
    print("\n[2/6] Parsing dates and creating time features...")
    df['WOStartDate'] = pd.to_datetime(df['WOStartDate'], errors='coerce')
    df = df.dropna(subset=['WOStartDate'])

    df['year'] = df['WOStartDate'].dt.year
    df['month'] = df['WOStartDate'].dt.month
    df['month_date'] = df['WOStartDate'].dt.to_period('M').dt.to_timestamp()

    print(f"  Date range: {df['WOStartDate'].min()} to {df['WOStartDate'].max()}")
    print(f"  Total months: {df['month_date'].nunique()}")

    # Standardize PPM/UPM values
    print("\n[3/6] Standardizing PPM/UPM values...")
    df['PPMorUPM'] = df['PPMorUPM'].str.strip().str.upper()
    print(f"  PPM/UPM distribution:")
    print(df['PPMorUPM'].value_counts())

    # Classify UPM events into shock/asset/unknown
    print("\n[4/6] Classifying UPM events (shock/asset/unknown)...")
    print("  This may take a few minutes...")

    # Only classify UPM events
    df['upm_type'] = 'N/A'
    upm_mask = df['PPMorUPM'] == 'UPM'
    df.loc[upm_mask, 'upm_type'] = df.loc[upm_mask, 'WODescription'].apply(classify_upm_type)

    # Print classification results
    print(f"\n  UPM Classification Results:")
    upm_df = df[df['PPMorUPM'] == 'UPM']
    print(upm_df['upm_type'].value_counts())
    print(f"\n  Percentages:")
    print(upm_df['upm_type'].value_counts(normalize=True) * 100)

    # Sample check
    print("\n  Sample classifications (first 20 UPM events):")
    sample = upm_df[['WODescription', 'upm_type']].head(20)
    for idx, row in sample.iterrows():
        desc = str(row['WODescription'])[:60] if pd.notna(row['WODescription']) else 'None'
        print(f"    [{row['upm_type']:8s}] {desc}")

    # Create monthly aggregations
    print("\n[5/6] Creating monthly aggregations by entity...")

    # Define grouping keys
    entity_cols = ['UniversityID', 'BuildingID', 'SystemDescription', 'year', 'month', 'month_date']

    # Create event indicators
    df['is_upm'] = (df['PPMorUPM'] == 'UPM').astype(int)
    df['is_upm_asset'] = ((df['PPMorUPM'] == 'UPM') & (df['upm_type'] == 'asset')).astype(int)
    df['is_upm_shock'] = ((df['PPMorUPM'] == 'UPM') & (df['upm_type'] == 'shock')).astype(int)

    # Aggregation
    agg_dict = {
        # Event counts
        'is_upm': 'sum',
        'is_upm_asset': 'sum',
        'is_upm_shock': 'sum',

        # Building context (first value - these don't change over time)
        'BuiltYear': 'first',
        'Size': 'first',
        'Type': 'first',
        'FCI': 'first',
        'DMC': 'first',
        'CRV': 'first',

        # Weather (monthly means)
        'MinTemp': 'mean',
        'MaxTemp': 'mean',
        'Humidity': 'mean',
        'Precipitation': 'mean',
        'Snow': 'mean',

        # WO characteristics (monthly means)
        'WOPriority': 'mean',
        'WODuration': 'mean',
    }

    monthly = df.groupby(entity_cols).agg(agg_dict).reset_index()

    # Rename event columns
    monthly.rename(columns={
        'is_upm': 'UPM_total_event',
        'is_upm_asset': 'UPM_asset_event',
        'is_upm_shock': 'UPM_shock_event',
    }, inplace=True)

    print(f"  Initial aggregated rows: {len(monthly):,}")
    print(f"  Unique entities: {monthly.groupby(['UniversityID', 'BuildingID', 'SystemDescription']).ngroups:,}")

    # Smart monthly grid generation
    print("\n[6/6] Generating smart monthly grids (only for active periods)...")

    # Get first/last appearance per entity
    entity_group_cols = ['UniversityID', 'BuildingID', 'SystemDescription']
    entity_ranges = monthly.groupby(entity_group_cols)['month_date'].agg(['min', 'max']).reset_index()
    entity_ranges.columns = ['UniversityID', 'BuildingID', 'SystemDescription', 'first_month', 'last_month']

    print(f"  Generating complete monthly grids for {len(entity_ranges):,} entities...")

    # Generate complete monthly grid for each entity
    grid_frames = []
    for idx, row in entity_ranges.iterrows():
        if idx % 1000 == 0:
            print(f"    Processing entity {idx:,}/{len(entity_ranges):,}...", end='\r')

        # Create date range from first to last appearance
        months = pd.date_range(row['first_month'], row['last_month'], freq='MS')

        # Create grid for this entity
        entity_grid = pd.DataFrame({
            'UniversityID': row['UniversityID'],
            'BuildingID': row['BuildingID'],
            'SystemDescription': row['SystemDescription'],
            'month_date': months,
        })

        grid_frames.append(entity_grid)

    print(f"\n    Generated grid frames for {len(grid_frames):,} entities")

    # Combine all grids
    complete_grid = pd.concat(grid_frames, ignore_index=True)
    complete_grid['year'] = complete_grid['month_date'].dt.year
    complete_grid['month'] = complete_grid['month_date'].dt.month

    print(f"  Complete grid size: {len(complete_grid):,} rows")

    # Merge with aggregated data (zero-fill missing months)
    print("  Merging with aggregated data (zero-filling missing months)...")
    merge_cols = ['UniversityID', 'BuildingID', 'SystemDescription', 'year', 'month', 'month_date']
    final = complete_grid.merge(monthly, on=merge_cols, how='left')

    # Fill event counts with 0 (missing months = no events)
    event_cols = ['UPM_total_event', 'UPM_asset_event', 'UPM_shock_event']
    final[event_cols] = final[event_cols].fillna(0).astype(int)

    # Forward fill building context (these don't change)
    building_cols = ['BuiltYear', 'Size', 'Type', 'FCI', 'DMC', 'CRV']
    for col in building_cols:
        if col in final.columns:
            final[col] = final.groupby(entity_group_cols)[col].ffill().bfill()

    # Interpolate weather data (linear interpolation within entity)
    weather_cols = ['MinTemp', 'MaxTemp', 'Humidity', 'Precipitation', 'Snow']
    for col in weather_cols:
        if col in final.columns:
            final[col] = final.groupby(entity_group_cols)[col].transform(
                lambda x: x.interpolate(method='linear', limit_direction='both')
            )

    # Interpolate WO characteristics
    wo_cols = ['WOPriority', 'WODuration']
    for col in wo_cols:
        if col in final.columns:
            final[col] = final.groupby(entity_group_cols)[col].transform(
                lambda x: x.interpolate(method='linear', limit_direction='both')
            )

    print(f"  Final dataset size: {len(final):,} rows")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    # Check 1: Event count preservation
    original_events = df['is_upm'].sum()
    final_events = final['UPM_total_event'].sum()
    print(f"\n✓ Event count check:")
    print(f"  Original UPM events: {original_events:,}")
    print(f"  Final UPM events: {final_events:,}")
    print(f"  Match: {original_events == final_events}")

    # Check 2: Grid completeness
    print(f"\n✓ Grid completeness:")
    print(f"  Entities with complete grids: {len(entity_ranges):,}")
    print(f"  Average months per entity: {len(final) / len(entity_ranges):.1f}")

    # Check 3: Null checks
    print(f"\n✓ Null values in critical columns:")
    critical_cols = ['UniversityID', 'BuildingID', 'SystemDescription', 'year', 'month', 'month_date'] + event_cols
    for col in critical_cols:
        null_count = final[col].isna().sum()
        print(f"  {col}: {null_count:,} nulls")

    # Check 4: Event distribution
    print(f"\n✓ Event distribution:")
    print(f"  Rows with UPM_total_event > 0: {(final['UPM_total_event'] > 0).sum():,} ({(final['UPM_total_event'] > 0).mean()*100:.1f}%)")
    print(f"  Rows with UPM_asset_event > 0: {(final['UPM_asset_event'] > 0).sum():,} ({(final['UPM_asset_event'] > 0).mean()*100:.1f}%)")
    print(f"  Rows with UPM_shock_event > 0: {(final['UPM_shock_event'] > 0).sum():,} ({(final['UPM_shock_event'] > 0).mean()*100:.1f}%)")

    # Save output
    print("\n" + "=" * 80)
    output_path = 'data/processed/monthly_asset_upm.parquet'
    print(f"Saving to {output_path}...")
    final.to_parquet(output_path, index=False)
    print(f"✓ Saved {len(final):,} rows")

    print("\n" + "=" * 80)
    print("PHASE 1 COMPLETE!")
    print("=" * 80)
    print(f"\nOutput: {output_path}")
    print(f"Size: {len(final):,} rows x {len(final.columns)} columns")
    print("\nNext step: Run scripts/engineer_asset_features.py")


if __name__ == '__main__':
    main()
