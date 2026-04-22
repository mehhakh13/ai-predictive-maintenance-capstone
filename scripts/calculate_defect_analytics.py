"""
Defect Analytics Calculation Script
Calculates three rankings: Recurrence, Severity, Environmental Sensitivity
At Global, University, and Building levels
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from scipy.stats import pearsonr

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "defect_analytics"
OUTPUT_DIR.mkdir(exist_ok=True)

# Weather columns
WEATHER_COLS = [
    'MinTemp.(°C)',
    'MaxTemp.(°C)',
    'Humidity(%)',
    'Precipitation(mm)',
    'Snow(mm)',
    'WindSpeed(m/s)',
    'Atmospheric pressure(hPa)'
]

def load_cleaned_data():
    """Load the cleaned combined dataset"""
    print("Loading cleaned data...")
    file_path = PROCESSED_DIR / "fmucd_all_cleaned.csv"

    # Load with low_memory=False to avoid dtype warnings
    df = pd.read_csv(file_path, low_memory=False)

    # Convert date columns explicitly
    print("Parsing dates...")
    df['WOStartDate'] = pd.to_datetime(df['WOStartDate'], errors='coerce')
    df['WOEndDate'] = pd.to_datetime(df['WOEndDate'], errors='coerce')

    # Convert numeric columns to proper numeric types
    print("Converting numeric columns...")
    numeric_cols = ['TotalCost', 'LaborCost', 'MaterialCost', 'OtherCost', 'WODuration',
                    'WOPriority', 'LaborHours', 'MinTemp.(°C)', 'MaxTemp.(°C)',
                    'Humidity(%)', 'WindSpeed(m/s)', 'Precipitation(mm)', 'Snow(mm)',
                    'Atmospheric pressure(hPa)']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate average temperature if not present
    if 'AvgTemp.(°C)' not in df.columns:
        df['AvgTemp.(°C)'] = (df['MinTemp.(°C)'] + df['MaxTemp.(°C)']) / 2

    # Extract month and year for temporal analysis
    df['Year'] = df['WOStartDate'].dt.year
    df['Month'] = df['WOStartDate'].dt.month
    df['YearMonth'] = df['WOStartDate'].dt.to_period('M')

    print(f"Loaded {len(df):,} records")
    print(f"Universities: {df['UniversityID'].nunique()}")
    print(f"Buildings: {df['BuildingName'].nunique()}")
    print(f"Subsystems: {df['SubsystemDescription'].nunique()}")

    return df

def calculate_recurrence_rankings(df, group_by_cols, level_name):
    """
    Calculate recurrence rankings for subsystems

    Args:
        df: DataFrame with work orders
        group_by_cols: List of columns to group by (e.g., ['UniversityID', 'SubsystemDescription'])
        level_name: String describing the level (e.g., 'University')

    Returns:
        DataFrame with recurrence rankings
    """
    print(f"\nCalculating recurrence rankings at {level_name} level...")

    # Group by specified columns and count
    recurrence = df.groupby(group_by_cols).agg({
        'WOID': 'count',
        'YearMonth': ['min', 'max']
    }).reset_index()

    recurrence.columns = group_by_cols + ['total_count', 'first_occurrence', 'last_occurrence']

    # Calculate time span in months
    # Convert periods to timestamps for difference calculation
    recurrence['first_ts'] = recurrence['first_occurrence'].apply(lambda x: x.to_timestamp() if pd.notna(x) else pd.NaT)
    recurrence['last_ts'] = recurrence['last_occurrence'].apply(lambda x: x.to_timestamp() if pd.notna(x) else pd.NaT)

    # Calculate months difference
    recurrence['months_observed'] = ((recurrence['last_ts'] - recurrence['first_ts']) / pd.Timedelta(days=30.44)) + 1
    recurrence['months_observed'] = recurrence['months_observed'].fillna(1).clip(lower=1)

    # Calculate frequency (occurrences per month)
    recurrence['frequency_per_month'] = recurrence['total_count'] / recurrence['months_observed']

    # Add rank
    recurrence = recurrence.sort_values('total_count', ascending=False)
    recurrence['recurrence_rank'] = range(1, len(recurrence) + 1)

    print(f"  Calculated rankings for {len(recurrence)} entries")
    print(f"  Top 3 by recurrence:")
    for i, row in recurrence.head(3).iterrows():
        subsystem = row['SubsystemDescription'] if 'SubsystemDescription' in recurrence.columns else 'N/A'
        print(f"    {row['recurrence_rank']}. {subsystem}: {row['total_count']:,} occurrences ({row['frequency_per_month']:.2f}/month)")

    return recurrence

def normalize_column(series):
    """Normalize a series to 0-1 scale"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0, index=series.index)
    return (series - min_val) / (max_val - min_val)

def calculate_severity_rankings(df, group_by_cols, level_name):
    """
    Calculate severity rankings using composite score
    Severity = Cost×0.5 + Duration×0.3 + Priority×0.2

    Args:
        df: DataFrame with work orders
        group_by_cols: List of columns to group by
        level_name: String describing the level

    Returns:
        DataFrame with severity rankings
    """
    print(f"\nCalculating severity rankings at {level_name} level...")

    # Group and aggregate
    severity = df.groupby(group_by_cols).agg({
        'TotalCost': ['sum', 'mean', 'std'],
        'WODuration': ['mean', 'std'],
        'WOPriority': ['mean', 'std'],
        'WOID': 'count'
    }).reset_index()

    # Flatten column names
    severity.columns = group_by_cols + [
        'total_cost', 'avg_cost', 'std_cost',
        'avg_duration', 'std_duration',
        'avg_priority', 'std_priority',
        'count'
    ]

    # Fill NaN std with 0
    severity = severity.fillna(0)

    # Normalize each component to 0-1 scale
    severity['norm_cost'] = normalize_column(severity['total_cost'])
    severity['norm_duration'] = normalize_column(severity['avg_duration'])
    severity['norm_priority'] = normalize_column(severity['avg_priority'])

    # Calculate composite severity score (0-100 scale)
    severity['severity_score'] = (
        severity['norm_cost'] * 0.5 +
        severity['norm_duration'] * 0.3 +
        severity['norm_priority'] * 0.2
    ) * 100

    # Add rank
    severity = severity.sort_values('severity_score', ascending=False)
    severity['severity_rank'] = range(1, len(severity) + 1)

    print(f"  Calculated rankings for {len(severity)} entries")
    print(f"  Top 3 by severity:")
    for i, row in severity.head(3).iterrows():
        subsystem = row['SubsystemDescription'] if 'SubsystemDescription' in severity.columns else 'N/A'
        print(f"    {row['severity_rank']}. {subsystem}: Score={row['severity_score']:.1f}, Cost=${row['avg_cost']:,.0f}, Duration={row['avg_duration']:.1f}h")

    return severity

def calculate_environmental_sensitivity(df, group_by_cols, level_name):
    """
    Calculate environmental sensitivity by correlating failures with weather

    Args:
        df: DataFrame with work orders
        group_by_cols: List of columns to group by
        level_name: String describing the level

    Returns:
        DataFrame with environmental sensitivity rankings
    """
    print(f"\nCalculating environmental sensitivity at {level_name} level...")

    # Aggregate to monthly level
    monthly_cols = group_by_cols + ['YearMonth']
    monthly_data = df.groupby(monthly_cols).agg({
        'WOID': 'count',
        'MinTemp.(°C)': 'mean',
        'MaxTemp.(°C)': 'mean',
        'AvgTemp.(°C)': 'mean',
        'Humidity(%)': 'mean',
        'Precipitation(mm)': 'sum',
        'Snow(mm)': 'sum',
        'WindSpeed(m/s)': 'mean',
        'Atmospheric pressure(hPa)': 'mean'
    }).reset_index()

    monthly_data.columns = group_by_cols + ['YearMonth', 'failure_count'] + [
        'avg_min_temp', 'avg_max_temp', 'avg_temp', 'avg_humidity',
        'total_precipitation', 'total_snow', 'avg_wind_speed', 'avg_pressure'
    ]

    # Calculate temperature range
    monthly_data['temp_range'] = monthly_data['avg_max_temp'] - monthly_data['avg_min_temp']

    # Weather features to correlate
    weather_features = [
        'avg_min_temp', 'avg_max_temp', 'avg_temp', 'temp_range',
        'avg_humidity', 'total_precipitation', 'total_snow',
        'avg_wind_speed', 'avg_pressure'
    ]

    # Calculate correlations for each group
    results = []

    for group_vals, group_df in monthly_data.groupby(group_by_cols):
        if len(group_df) < 3:  # Need at least 3 data points for correlation
            continue

        correlations = {}
        for feature in weather_features:
            if group_df[feature].std() > 0:  # Check for variance
                try:
                    corr, p_value = pearsonr(group_df['failure_count'], group_df[feature])
                    correlations[feature] = {
                        'correlation': corr,
                        'abs_correlation': abs(corr),
                        'p_value': p_value
                    }
                except:
                    correlations[feature] = {
                        'correlation': 0,
                        'abs_correlation': 0,
                        'p_value': 1.0
                    }
            else:
                correlations[feature] = {
                    'correlation': 0,
                    'abs_correlation': 0,
                    'p_value': 1.0
                }

        # Calculate average absolute correlation (sensitivity score)
        avg_abs_corr = np.mean([c['abs_correlation'] for c in correlations.values()])

        # Find strongest correlation
        strongest = max(correlations.items(), key=lambda x: x[1]['abs_correlation'])
        strongest_feature = strongest[0]
        strongest_corr = strongest[1]['correlation']

        # Build result
        result = {
            'sensitivity_score': avg_abs_corr * 100,  # Scale to 0-100
            'strongest_weather_factor': strongest_feature,
            'strongest_correlation': strongest_corr,
            'months_analyzed': len(group_df),
            'avg_monthly_failures': group_df['failure_count'].mean()
        }

        # Add group columns
        if isinstance(group_vals, tuple):
            for col, val in zip(group_by_cols, group_vals):
                result[col] = val
        else:
            result[group_by_cols[0]] = group_vals

        # Add all correlations as separate columns
        for feature, corr_data in correlations.items():
            result[f'corr_{feature}'] = corr_data['correlation']

        results.append(result)

    # Create DataFrame
    sensitivity = pd.DataFrame(results)

    # Add rank
    sensitivity = sensitivity.sort_values('sensitivity_score', ascending=False)
    sensitivity['env_sensitivity_rank'] = range(1, len(sensitivity) + 1)

    print(f"  Calculated rankings for {len(sensitivity)} entries")
    print(f"  Top 3 by environmental sensitivity:")
    for i, row in sensitivity.head(3).iterrows():
        subsystem = row['SubsystemDescription'] if 'SubsystemDescription' in sensitivity.columns else 'N/A'
        print(f"    {row['env_sensitivity_rank']}. {subsystem}: Score={row['sensitivity_score']:.1f}, Factor={row['strongest_weather_factor']}, Corr={row['strongest_correlation']:.3f}")

    return sensitivity

def merge_rankings(recurrence, severity, sensitivity, group_by_cols):
    """Merge all three rankings into a single dataframe"""
    print("\nMerging rankings...")

    # Start with recurrence (most complete)
    merged = recurrence.copy()

    # Merge severity
    severity_cols = ['severity_rank', 'severity_score', 'avg_cost', 'avg_duration', 'avg_priority', 'total_cost']
    merged = merged.merge(
        severity[group_by_cols + severity_cols],
        on=group_by_cols,
        how='left'
    )

    # Merge environmental sensitivity
    env_cols = ['env_sensitivity_rank', 'sensitivity_score', 'strongest_weather_factor', 'strongest_correlation']
    merged = merged.merge(
        sensitivity[group_by_cols + env_cols],
        on=group_by_cols,
        how='left'
    )

    print(f"  Merged {len(merged)} records")
    return merged

def main():
    print("="*80)
    print("DEFECT ANALYTICS CALCULATION")
    print("="*80)

    # Load data
    df = load_cleaned_data()

    # ========================================================================
    # GLOBAL LEVEL (All data, grouped by Subsystem only)
    # ========================================================================
    print("\n" + "="*80)
    print("GLOBAL LEVEL ANALYSIS")
    print("="*80)

    recurrence_global = calculate_recurrence_rankings(
        df, ['SubsystemDescription'], 'Global'
    )

    severity_global = calculate_severity_rankings(
        df, ['SubsystemDescription'], 'Global'
    )

    sensitivity_global = calculate_environmental_sensitivity(
        df, ['SubsystemDescription'], 'Global'
    )

    global_rankings = merge_rankings(
        recurrence_global, severity_global, sensitivity_global,
        ['SubsystemDescription']
    )

    # Save
    output_path = OUTPUT_DIR / "global_rankings.csv"
    global_rankings.to_csv(output_path, index=False)
    print(f"\n✅ Saved global rankings: {output_path}")

    # ========================================================================
    # UNIVERSITY LEVEL
    # ========================================================================
    print("\n" + "="*80)
    print("UNIVERSITY LEVEL ANALYSIS")
    print("="*80)

    recurrence_uni = calculate_recurrence_rankings(
        df, ['UniversityID', 'SubsystemDescription'], 'University'
    )

    severity_uni = calculate_severity_rankings(
        df, ['UniversityID', 'SubsystemDescription'], 'University'
    )

    sensitivity_uni = calculate_environmental_sensitivity(
        df, ['UniversityID', 'SubsystemDescription'], 'University'
    )

    university_rankings = merge_rankings(
        recurrence_uni, severity_uni, sensitivity_uni,
        ['UniversityID', 'SubsystemDescription']
    )

    # Save
    output_path = OUTPUT_DIR / "university_rankings.csv"
    university_rankings.to_csv(output_path, index=False)
    print(f"\n✅ Saved university rankings: {output_path}")

    # ========================================================================
    # BUILDING LEVEL (only for buildings with data)
    # ========================================================================
    print("\n" + "="*80)
    print("BUILDING LEVEL ANALYSIS")
    print("="*80)

    # Filter to buildings with names
    df_with_buildings = df[df['BuildingName'].notna() & (df['BuildingName'] != '')]

    if len(df_with_buildings) > 0:
        recurrence_bldg = calculate_recurrence_rankings(
            df_with_buildings, ['UniversityID', 'BuildingName', 'SubsystemDescription'], 'Building'
        )

        severity_bldg = calculate_severity_rankings(
            df_with_buildings, ['UniversityID', 'BuildingName', 'SubsystemDescription'], 'Building'
        )

        sensitivity_bldg = calculate_environmental_sensitivity(
            df_with_buildings, ['UniversityID', 'BuildingName', 'SubsystemDescription'], 'Building'
        )

        building_rankings = merge_rankings(
            recurrence_bldg, severity_bldg, sensitivity_bldg,
            ['UniversityID', 'BuildingName', 'SubsystemDescription']
        )

        # Save
        output_path = OUTPUT_DIR / "building_rankings.csv"
        building_rankings.to_csv(output_path, index=False)
        print(f"\n✅ Saved building rankings: {output_path}")
    else:
        print("⚠️  No buildings with names found, skipping building-level analysis")

    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    summary = {
        'total_records': len(df),
        'universities': int(df['UniversityID'].nunique()),
        'buildings': int(df['BuildingName'].nunique()),
        'subsystems': int(df['SubsystemDescription'].nunique()),
        'date_range': {
            'start': str(df['WOStartDate'].min()),
            'end': str(df['WOStartDate'].max())
        },
        'top_recurrence': global_rankings.nlargest(10, 'total_count')[
            ['SubsystemDescription', 'total_count', 'frequency_per_month']
        ].to_dict('records'),
        'top_severity': global_rankings.nlargest(10, 'severity_score')[
            ['SubsystemDescription', 'severity_score', 'avg_cost', 'avg_duration']
        ].to_dict('records'),
        'top_environmental': global_rankings.nlargest(10, 'sensitivity_score')[
            ['SubsystemDescription', 'sensitivity_score', 'strongest_weather_factor', 'strongest_correlation']
        ].to_dict('records')
    }

    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✅ Saved summary: {summary_path}")

    print("\n" + "="*80)
    print("✅ DEFECT ANALYTICS CALCULATION COMPLETE!")
    print("="*80)
    print(f"\nOutput files saved to: {OUTPUT_DIR}")
    print("  - global_rankings.csv (subsystem rankings across all data)")
    print("  - university_rankings.csv (subsystem rankings per university)")
    print("  - building_rankings.csv (subsystem rankings per building)")
    print("  - summary.json (top 10 lists for each category)")

if __name__ == "__main__":
    main()
