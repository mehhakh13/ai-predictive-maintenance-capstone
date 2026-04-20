"""
Phase 4: Heatmap CSV Generation for Dashboard Consumption

This script:
1. Loads predictions_with_metadata.parquet (with risk_prob_asset column)
2. Creates Building-Level heatmap: (UniversityID, BuildingID, System, Month)
3. Creates University-Level heatmap: (UniversityID, System, Month) for "All Buildings" view
4. Creates metadata files for dropdown filtering
5. Applies coverage filter (≥10 entities) for reliability
6. Outputs:
   - data/dashboard/building_level_heatmap.csv
   - data/dashboard/university_level_heatmap.csv
   - data/dashboard/metadata.json (universities and buildings for dropdowns)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


def create_building_level_heatmap(df, min_coverage=10):
    """
    Create building-level heatmap for dropdown filtering.

    Aggregation:
    - Group by (UniversityID, BuildingID, BuildingName, SubsystemDescription, month)
    - ml_risk = mean(risk_prob_asset)
    - hist_asset_rate = mean(UPM_asset_event)
    - hist_shock_rate = mean(UPM_shock_event)
    - coverage = count of rows

    Output columns:
    - UniversityID, BuildingID, BuildingName, SubsystemDescription, MonthNum,
      ml_risk, hist_asset_rate, hist_shock_rate, coverage
    """
    print("\n  Creating building-level heatmap...")

    # Create MonthNum (1-12)
    df['MonthNum'] = df['month']

    # Group by University, Building, BuildingName, Subsystem, and MonthNum
    building_agg = df.groupby(['UniversityID', 'BuildingID', 'BuildingName', 'SubsystemDescription', 'MonthNum']).agg({
        'risk_prob_asset': 'mean',
        'UPM_asset_event': 'mean',
        'UPM_shock_event': 'mean',
        'month': 'count',  # Count as proxy for coverage
    }).reset_index()

    building_agg.columns = [
        'UniversityID', 'BuildingID', 'BuildingName', 'SubsystemDescription', 'MonthNum',
        'ml_risk', 'hist_asset_rate', 'hist_shock_rate', 'coverage'
    ]

    print(f"    Before filter: {len(building_agg):,} rows")

    # Filter by coverage
    building_agg = building_agg[building_agg['coverage'] >= min_coverage]

    print(f"    After filter (coverage ≥{min_coverage}): {len(building_agg):,} rows")
    print(f"    Unique universities: {building_agg['UniversityID'].nunique()}")
    print(f"    Unique buildings: {building_agg['BuildingID'].nunique()}")
    print(f"    Unique building names: {building_agg['BuildingName'].nunique()}")
    print(f"    Unique subsystems: {building_agg['SubsystemDescription'].nunique()}")

    return building_agg


def create_university_level_heatmap(df, min_coverage=10):
    """
    Create university-level heatmap for "All Buildings" view.

    Aggregation:
    - Group by (UniversityID, SubsystemDescription, month)
    - Average across all buildings in the university
    - ml_risk = mean(risk_prob_asset)
    - hist_asset_rate = mean(UPM_asset_event)
    - hist_shock_rate = mean(UPM_shock_event)
    - coverage = count of rows

    Output columns:
    - UniversityID, SubsystemDescription, MonthNum,
      ml_risk, hist_asset_rate, hist_shock_rate, coverage
    """
    print("\n  Creating university-level heatmap (All Buildings aggregation)...")

    # Create MonthNum (1-12)
    df['MonthNum'] = df['month']

    # Group by University, Subsystem, and MonthNum
    uni_agg = df.groupby(['UniversityID', 'SubsystemDescription', 'MonthNum']).agg({
        'risk_prob_asset': 'mean',
        'UPM_asset_event': 'mean',
        'UPM_shock_event': 'mean',
        'month': 'count',  # Count as proxy for coverage
    }).reset_index()

    uni_agg.columns = [
        'UniversityID', 'SubsystemDescription', 'MonthNum',
        'ml_risk', 'hist_asset_rate', 'hist_shock_rate', 'coverage'
    ]

    print(f"    Before filter: {len(uni_agg):,} rows")

    # Filter by coverage
    uni_agg = uni_agg[uni_agg['coverage'] >= min_coverage]

    print(f"    After filter (coverage ≥{min_coverage}): {len(uni_agg):,} rows")
    print(f"    Unique universities: {uni_agg['UniversityID'].nunique()}")
    print(f"    Unique subsystems: {uni_agg['SubsystemDescription'].nunique()}")

    return uni_agg


def create_metadata(building_df):
    """
    Create metadata for frontend dropdowns.

    Returns:
    - Dictionary with universities, buildings, and building names
    """
    print("\n  Creating metadata for dropdowns...")

    metadata = {
        'universities': [],
        'buildings_by_university': {},
        'building_names': {}  # BuildingID -> BuildingName mapping
    }

    # Get unique universities
    universities = sorted(building_df['UniversityID'].unique())
    metadata['universities'] = [int(u) for u in universities]

    # Get buildings and building names for each university
    for uni in universities:
        uni_buildings = building_df[building_df['UniversityID'] == uni][['BuildingID', 'BuildingName']].drop_duplicates()

        # Store building IDs
        buildings = sorted(uni_buildings['BuildingID'].unique())
        metadata['buildings_by_university'][int(uni)] = [str(b) for b in buildings]

        # Store BuildingID -> BuildingName mapping
        for _, row in uni_buildings.iterrows():
            metadata['building_names'][str(row['BuildingID'])] = str(row['BuildingName'])

    print(f"    Universities: {metadata['universities']}")
    print(f"    Total buildings: {sum(len(v) for v in metadata['buildings_by_university'].values())}")
    print(f"    Total building names: {len(metadata['building_names'])}")

    return metadata


def print_heatmap_summary(building_df, uni_df):
    """
    Print summary statistics for heatmaps.
    """
    print("\n" + "=" * 80)
    print("HEATMAP SUMMARY STATISTICS")
    print("=" * 80)

    # Building-Level Heatmap
    print("\n[BUILDING-LEVEL HEATMAP]")
    print(f"  Total rows: {len(building_df):,}")
    print(f"  Unique universities: {building_df['UniversityID'].nunique()}")
    print(f"  Unique buildings: {building_df['BuildingID'].nunique()}")
    print(f"  Unique building names: {building_df['BuildingName'].nunique()}")
    print(f"  Unique subsystems: {building_df['SubsystemDescription'].nunique()}")
    print(f"  Month range: {building_df['MonthNum'].min()} - {building_df['MonthNum'].max()}")

    print(f"\n  ML Risk distribution:")
    print(f"    Min:    {building_df['ml_risk'].min():.4f}")
    print(f"    25th:   {building_df['ml_risk'].quantile(0.25):.4f}")
    print(f"    Median: {building_df['ml_risk'].median():.4f}")
    print(f"    75th:   {building_df['ml_risk'].quantile(0.75):.4f}")
    print(f"    Max:    {building_df['ml_risk'].max():.4f}")

    print(f"\n  Top 5 riskiest (Uni, Bldg, Subsystem, Month):")
    top_risk = building_df.nlargest(5, 'ml_risk')
    for idx, row in top_risk.iterrows():
        print(f"    Uni {row['UniversityID']} {row['BuildingName'][:20]:20s} {row['SubsystemDescription'][:30]:30s} Month {row['MonthNum']:2.0f}  Risk: {row['ml_risk']:.4f}")

    # University-Level Heatmap
    print("\n[UNIVERSITY-LEVEL HEATMAP (All Buildings)]")
    print(f"  Total rows: {len(uni_df):,}")
    print(f"  Unique universities: {uni_df['UniversityID'].nunique()}")
    print(f"  Unique subsystems: {uni_df['SubsystemDescription'].nunique()}")
    print(f"  Month range: {uni_df['MonthNum'].min()} - {uni_df['MonthNum'].max()}")

    print(f"\n  ML Risk distribution:")
    print(f"    Min:    {uni_df['ml_risk'].min():.4f}")
    print(f"    25th:   {uni_df['ml_risk'].quantile(0.25):.4f}")
    print(f"    Median: {uni_df['ml_risk'].median():.4f}")
    print(f"    75th:   {uni_df['ml_risk'].quantile(0.75):.4f}")
    print(f"    Max:    {uni_df['ml_risk'].max():.4f}")

    print(f"\n  Average risk by university:")
    for uni in sorted(uni_df['UniversityID'].unique()):
        avg_risk = uni_df[uni_df['UniversityID'] == uni]['ml_risk'].mean()
        print(f"    University {uni}: {avg_risk:.4f}")


def validate_heatmaps(building_df, uni_df):
    """
    Validation checks for heatmap outputs.
    """
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    # Check 1: Schema validation
    print(f"\n✓ Schema Validation:")

    building_expected_cols = ['UniversityID', 'BuildingID', 'BuildingName', 'SubsystemDescription', 'MonthNum',
                              'ml_risk', 'hist_asset_rate', 'hist_shock_rate', 'coverage']
    building_valid = all(col in building_df.columns for col in building_expected_cols)
    print(f"  Building-level heatmap columns: {building_valid}")
    print(f"    Expected: {building_expected_cols}")
    print(f"    Actual: {list(building_df.columns)}")

    uni_expected_cols = ['UniversityID', 'SubsystemDescription', 'MonthNum',
                        'ml_risk', 'hist_asset_rate', 'hist_shock_rate', 'coverage']
    uni_valid = all(col in uni_df.columns for col in uni_expected_cols)
    print(f"  University-level heatmap columns: {uni_valid}")
    print(f"    Expected: {uni_expected_cols}")
    print(f"    Actual: {list(uni_df.columns)}")

    # Check 2: Risk scores in [0, 1] range
    print(f"\n✓ Risk Score Range:")
    building_in_range = (building_df['ml_risk'] >= 0).all() and (building_df['ml_risk'] <= 1).all()
    print(f"  Building-level ML risk in [0, 1]: {building_in_range}")
    if not building_in_range:
        print(f"    Min: {building_df['ml_risk'].min()}, Max: {building_df['ml_risk'].max()}")

    uni_in_range = (uni_df['ml_risk'] >= 0).all() and (uni_df['ml_risk'] <= 1).all()
    print(f"  University-level ML risk in [0, 1]: {uni_in_range}")
    if not uni_in_range:
        print(f"    Min: {uni_df['ml_risk'].min()}, Max: {uni_df['ml_risk'].max()}")

    # Check 3: Coverage ≥ min threshold
    print(f"\n✓ Coverage Check:")
    building_coverage_valid = (building_df['coverage'] >= 10).all()
    uni_coverage_valid = (uni_df['coverage'] >= 10).all()
    print(f"  Building-level all coverage ≥10: {building_coverage_valid}")
    print(f"  University-level all coverage ≥10: {uni_coverage_valid}")

    # Check 4: No NaNs
    print(f"\n✓ NaN Check:")
    building_nulls = building_df.isna().sum().sum()
    uni_nulls = uni_df.isna().sum().sum()
    print(f"  Building-level NaNs: {building_nulls}")
    print(f"  University-level NaNs: {uni_nulls}")

    # Check 5: University filter check
    print(f"\n✓ University Filter Check:")
    building_unis = sorted(building_df['UniversityID'].unique())
    uni_unis = sorted(uni_df['UniversityID'].unique())
    print(f"  Building-level universities: {building_unis}")
    print(f"  University-level universities: {uni_unis}")
    print(f"  All in {10, 11, 12}: {set(building_unis).issubset({10, 11, 12})}")


def main():
    print("=" * 80)
    print("PHASE 4: HEATMAP CSV GENERATION (Building-Level)")
    print("=" * 80)

    # Load data
    print("\n[1/5] Loading predictions_with_metadata.parquet...")
    input_path = 'data/processed/predictions_with_metadata.parquet'
    df = pd.read_parquet(input_path)
    print(f"  Loaded {len(df):,} rows x {len(df.columns)} columns")
    print(f"  Columns include 'risk_prob_asset': {'risk_prob_asset' in df.columns}")

    # Verify university filter
    print(f"\n  Verifying UniversityID filter...")
    print(f"  Unique UniversityIDs: {sorted(df['UniversityID'].unique())}")
    if not set(df['UniversityID'].unique()).issubset({10, 11, 12}):
        print(f"  WARNING: Data contains universities outside {10, 11, 12}")

    # Create building-level heatmap
    print("\n[2/5] Creating building-level heatmap...")
    building_heatmap = create_building_level_heatmap(df, min_coverage=10)

    # Create university-level heatmap (All Buildings)
    print("\n[3/5] Creating university-level heatmap...")
    uni_heatmap = create_university_level_heatmap(df, min_coverage=10)

    # Create metadata for dropdowns
    print("\n[4/5] Creating metadata...")
    metadata = create_metadata(building_heatmap)

    # Print summary
    print_heatmap_summary(building_heatmap, uni_heatmap)

    # Validate
    validate_heatmaps(building_heatmap, uni_heatmap)

    # Save outputs
    print("\n[5/5] Saving outputs...")

    output_dir = Path('data/dashboard')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save building-level heatmap
    building_path = output_dir / 'building_level_heatmap.csv'
    building_heatmap.to_csv(building_path, index=False)
    print(f"  ✓ Saved Building-level heatmap to {building_path}")
    print(f"    Size: {len(building_heatmap):,} rows x {len(building_heatmap.columns)} columns")

    # Save university-level heatmap
    uni_path = output_dir / 'university_level_heatmap.csv'
    uni_heatmap.to_csv(uni_path, index=False)
    print(f"  ✓ Saved University-level heatmap to {uni_path}")
    print(f"    Size: {len(uni_heatmap):,} rows x {len(uni_heatmap.columns)} columns")

    # Save metadata
    metadata_path = output_dir / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✓ Saved Metadata to {metadata_path}")

    # Show sample data
    print("\n" + "=" * 80)
    print("SAMPLE DATA")
    print("=" * 80)

    print("\n[Building-Level Heatmap - First 10 rows]")
    print(building_heatmap.head(10).to_string(index=False))

    print("\n[University-Level Heatmap - First 10 rows]")
    print(uni_heatmap.head(10).to_string(index=False))

    print("\n[Metadata]")
    print(json.dumps(metadata, indent=2))

    print("\n" + "=" * 80)
    print("PHASE 4 COMPLETE!")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  - Building-level Heatmap: {building_path}")
    print(f"  - University-level Heatmap: {uni_path}")
    print(f"  - Metadata: {metadata_path}")
    print(f"\n✓ Pipeline complete! Heatmap CSVs ready for dashboard with dropdown filtering.")


if __name__ == '__main__':
    main()
