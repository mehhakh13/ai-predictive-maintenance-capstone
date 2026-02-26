"""
Phase 4: Heatmap CSV Generation for Dashboard Consumption

This script:
1. Loads predictions_with_metadata.parquet (with risk_prob_asset column)
2. Creates ML heatmap: Aggregates ML risk predictions by (System, Month)
3. Creates Historical heatmap: Aggregates historical event rates by (System, Month)
4. Applies coverage filter (≥10 entities) for reliability
5. Outputs: data/dashboard/ml_heatmap.csv, data/dashboard/historical_heatmap.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path


def create_ml_heatmap(df, min_coverage=10):
    """
    Create ML-based risk heatmap.

    Aggregation:
    - Group by (SystemDescription, month)
    - ml_risk = mean(risk_prob_asset)
    - coverage = count of distinct entities

    Output columns:
    - SystemDescription, MonthNum, ml_risk, coverage
    """
    print("\n  Aggregating ML risk by (System, Month)...")

    # Create MonthNum (1-12)
    df['MonthNum'] = df['month']

    # Group by System and MonthNum
    ml_agg = df.groupby(['SystemDescription', 'MonthNum']).agg({
        'risk_prob_asset': 'mean',
        'UniversityID': 'count',  # Count as proxy for coverage
    }).reset_index()

    ml_agg.columns = ['SystemDescription', 'MonthNum', 'ml_risk', 'coverage']

    print(f"    Before filter: {len(ml_agg):,} rows")

    # Filter by coverage
    ml_agg = ml_agg[ml_agg['coverage'] >= min_coverage]

    print(f"    After filter (coverage ≥{min_coverage}): {len(ml_agg):,} rows")
    print(f"    Unique systems: {ml_agg['SystemDescription'].nunique()}")

    return ml_agg


def create_historical_heatmap(df, min_coverage=10):
    """
    Create historical event rate heatmap.

    Aggregation:
    - Group by (SystemDescription, month)
    - Sum events, count entities
    - Calculate rates: event_count / coverage

    Output columns:
    - SystemDescription, MonthNum, hist_total_rate, hist_asset_rate, hist_shock_rate, coverage
    """
    print("\n  Aggregating historical events by (System, Month)...")

    # Create MonthNum (1-12)
    df['MonthNum'] = df['month']

    # Group by System and MonthNum
    hist_agg = df.groupby(['SystemDescription', 'MonthNum']).agg({
        'UPM_total_event': 'sum',
        'UPM_asset_event': 'sum',
        'UPM_shock_event': 'sum',
        'UniversityID': 'count',  # Count as proxy for coverage
    }).reset_index()

    hist_agg.columns = ['SystemDescription', 'MonthNum', 'total_events', 'asset_events', 'shock_events', 'coverage']

    print(f"    Before filter: {len(hist_agg):,} rows")

    # Filter by coverage
    hist_agg = hist_agg[hist_agg['coverage'] >= min_coverage]

    print(f"    After filter (coverage ≥{min_coverage}): {len(hist_agg):,} rows")

    # Calculate rates (events per entity)
    hist_agg['hist_total_rate'] = hist_agg['total_events'] / hist_agg['coverage']
    hist_agg['hist_asset_rate'] = hist_agg['asset_events'] / hist_agg['coverage']
    hist_agg['hist_shock_rate'] = hist_agg['shock_events'] / hist_agg['coverage']

    # Select final columns
    hist_agg = hist_agg[[
        'SystemDescription', 'MonthNum',
        'hist_total_rate', 'hist_asset_rate', 'hist_shock_rate',
        'coverage'
    ]]

    print(f"    Unique systems: {hist_agg['SystemDescription'].nunique()}")

    return hist_agg


def print_heatmap_summary(ml_df, hist_df):
    """
    Print summary statistics for heatmaps.
    """
    print("\n" + "=" * 80)
    print("HEATMAP SUMMARY STATISTICS")
    print("=" * 80)

    # ML Heatmap
    print("\n[ML HEATMAP]")
    print(f"  Total rows: {len(ml_df):,}")
    print(f"  Unique systems: {ml_df['SystemDescription'].nunique()}")
    print(f"  Month range: {ml_df['MonthNum'].min()} - {ml_df['MonthNum'].max()}")

    print(f"\n  Risk distribution:")
    print(f"    Min:    {ml_df['ml_risk'].min():.4f}")
    print(f"    25th:   {ml_df['ml_risk'].quantile(0.25):.4f}")
    print(f"    Median: {ml_df['ml_risk'].median():.4f}")
    print(f"    75th:   {ml_df['ml_risk'].quantile(0.75):.4f}")
    print(f"    Max:    {ml_df['ml_risk'].max():.4f}")

    print(f"\n  Coverage distribution:")
    print(f"    Min:    {ml_df['coverage'].min():,}")
    print(f"    Median: {ml_df['coverage'].median():.0f}")
    print(f"    Max:    {ml_df['coverage'].max():,}")

    print(f"\n  Top 5 riskiest (System, Month):")
    top_risk = ml_df.nlargest(5, 'ml_risk')
    for idx, row in top_risk.iterrows():
        print(f"    {row['SystemDescription']:40s} Month {row['MonthNum']:2.0f}  Risk: {row['ml_risk']:.4f}  Coverage: {row['coverage']:.0f}")

    print(f"\n  Average risk by month:")
    month_avg = ml_df.groupby('MonthNum')['ml_risk'].mean().sort_values(ascending=False)
    for month, risk in month_avg.items():
        month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(month)-1]
        print(f"    Month {month:2.0f} ({month_name}): {risk:.4f}")

    # Historical Heatmap
    print("\n[HISTORICAL HEATMAP]")
    print(f"  Total rows: {len(hist_df):,}")
    print(f"  Unique systems: {hist_df['SystemDescription'].nunique()}")
    print(f"  Month range: {hist_df['MonthNum'].min()} - {hist_df['MonthNum'].max()}")

    print(f"\n  Rate distribution (total UPM):")
    print(f"    Min:    {hist_df['hist_total_rate'].min():.4f}")
    print(f"    25th:   {hist_df['hist_total_rate'].quantile(0.25):.4f}")
    print(f"    Median: {hist_df['hist_total_rate'].median():.4f}")
    print(f"    75th:   {hist_df['hist_total_rate'].quantile(0.75):.4f}")
    print(f"    Max:    {hist_df['hist_total_rate'].max():.4f}")

    print(f"\n  Top 5 systems by avg total rate:")
    system_avg = hist_df.groupby('SystemDescription')['hist_total_rate'].mean().sort_values(ascending=False).head(5)
    for system, rate in system_avg.items():
        print(f"    {system:40s} {rate:.4f}")

    print(f"\n  Average rates by month:")
    month_rates = hist_df.groupby('MonthNum')[['hist_total_rate', 'hist_asset_rate', 'hist_shock_rate']].mean()
    print(f"    Month  Total    Asset    Shock")
    for month, row in month_rates.iterrows():
        month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(month)-1]
        print(f"    {month:2.0f} ({month_name}) {row['hist_total_rate']:.4f}   {row['hist_asset_rate']:.4f}   {row['hist_shock_rate']:.4f}")


def validate_heatmaps(ml_df, hist_df):
    """
    Validation checks for heatmap outputs.
    """
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    # Check 1: Schema validation
    print(f"\n✓ Schema Validation:")

    ml_expected_cols = ['SystemDescription', 'MonthNum', 'ml_risk', 'coverage']
    ml_valid = all(col in ml_df.columns for col in ml_expected_cols)
    print(f"  ML heatmap columns: {ml_valid}")
    print(f"    Expected: {ml_expected_cols}")
    print(f"    Actual: {list(ml_df.columns)}")

    hist_expected_cols = ['SystemDescription', 'MonthNum', 'hist_total_rate', 'hist_asset_rate', 'hist_shock_rate', 'coverage']
    hist_valid = all(col in hist_df.columns for col in hist_expected_cols)
    print(f"  Historical heatmap columns: {hist_valid}")
    print(f"    Expected: {hist_expected_cols}")
    print(f"    Actual: {list(hist_df.columns)}")

    # Check 2: Risk scores in [0, 1] range
    print(f"\n✓ Risk Score Range:")
    ml_in_range = (ml_df['ml_risk'] >= 0).all() and (ml_df['ml_risk'] <= 1).all()
    print(f"  ML risk in [0, 1]: {ml_in_range}")
    if not ml_in_range:
        print(f"    Min: {ml_df['ml_risk'].min()}, Max: {ml_df['ml_risk'].max()}")

    # Check 3: Coverage ≥ min threshold
    print(f"\n✓ Coverage Check:")
    ml_coverage_valid = (ml_df['coverage'] >= 10).all()
    hist_coverage_valid = (hist_df['coverage'] >= 10).all()
    print(f"  ML heatmap all coverage ≥10: {ml_coverage_valid}")
    print(f"  Historical heatmap all coverage ≥10: {hist_coverage_valid}")

    # Check 4: No NaNs
    print(f"\n✓ NaN Check:")
    ml_nulls = ml_df.isna().sum().sum()
    hist_nulls = hist_df.isna().sum().sum()
    print(f"  ML heatmap NaNs: {ml_nulls}")
    print(f"  Historical heatmap NaNs: {hist_nulls}")

    # Check 5: Spot check - HVAC risk by season
    print(f"\n✓ Spot Check - HVAC Risk by Season:")
    hvac_ml = ml_df[ml_df['SystemDescription'].str.contains('HVAC', case=False, na=False)]
    if len(hvac_ml) > 0:
        winter_months = [1, 2, 12]
        summer_months = [6, 7, 8]

        winter_risk = hvac_ml[hvac_ml['MonthNum'].isin(winter_months)]['ml_risk'].mean()
        summer_risk = hvac_ml[hvac_ml['MonthNum'].isin(summer_months)]['ml_risk'].mean()

        print(f"  HVAC Winter risk (Jan, Feb, Dec): {winter_risk:.4f}")
        print(f"  HVAC Summer risk (Jun, Jul, Aug): {summer_risk:.4f}")
        print(f"  Winter > Summer: {winter_risk > summer_risk}")
    else:
        print(f"  No HVAC system found in data")


def main():
    print("=" * 80)
    print("PHASE 4: HEATMAP CSV GENERATION")
    print("=" * 80)

    # Load data
    print("\n[1/4] Loading predictions_with_metadata.parquet...")
    input_path = 'data/processed/predictions_with_metadata.parquet'
    df = pd.read_parquet(input_path)
    print(f"  Loaded {len(df):,} rows x {len(df.columns)} columns")
    print(f"  Columns include 'risk_prob_asset': {'risk_prob_asset' in df.columns}")

    # Create ML heatmap
    print("\n[2/4] Creating ML heatmap...")
    ml_heatmap = create_ml_heatmap(df, min_coverage=10)

    # Create Historical heatmap
    print("\n[3/4] Creating Historical heatmap...")
    hist_heatmap = create_historical_heatmap(df, min_coverage=10)

    # Print summary
    print_heatmap_summary(ml_heatmap, hist_heatmap)

    # Validate
    validate_heatmaps(ml_heatmap, hist_heatmap)

    # Save outputs
    print("\n[4/4] Saving heatmap CSVs...")

    output_dir = Path('data/dashboard')
    output_dir.mkdir(parents=True, exist_ok=True)

    ml_path = output_dir / 'ml_heatmap.csv'
    ml_heatmap.to_csv(ml_path, index=False)
    print(f"  ✓ Saved ML heatmap to {ml_path}")
    print(f"    Size: {len(ml_heatmap):,} rows x {len(ml_heatmap.columns)} columns")

    hist_path = output_dir / 'historical_heatmap.csv'
    hist_heatmap.to_csv(hist_path, index=False)
    print(f"  ✓ Saved Historical heatmap to {hist_path}")
    print(f"    Size: {len(hist_heatmap):,} rows x {len(hist_heatmap.columns)} columns")

    # Show sample data
    print("\n" + "=" * 80)
    print("SAMPLE DATA")
    print("=" * 80)

    print("\n[ML Heatmap - First 10 rows]")
    print(ml_heatmap.head(10).to_string(index=False))

    print("\n[Historical Heatmap - First 10 rows]")
    print(hist_heatmap.head(10).to_string(index=False))

    print("\n" + "=" * 80)
    print("PHASE 4 COMPLETE!")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  - ML Heatmap: {ml_path}")
    print(f"  - Historical Heatmap: {hist_path}")
    print(f"\n✓ Pipeline complete! Heatmap CSVs ready for dashboard consumption.")


if __name__ == '__main__':
    main()
