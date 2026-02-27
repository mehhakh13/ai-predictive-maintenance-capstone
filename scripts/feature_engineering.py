#!/usr/bin/env python3
"""
Feature Engineering Pipeline for Predictive Maintenance
Creates system-month level aggregated features for XGBoost training
"""

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def load_data_from_supabase(table_name="fmucd_canada", limit=None, batch_size=1000):
    """Load data from Supabase table with pagination"""
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    print(f"Loading data from Supabase table: {table_name}...")

    all_data = []
    offset = 0

    while True:
        # Query with pagination (Supabase default max is 1000)
        current_batch_size = batch_size
        if limit and offset + current_batch_size > limit:
            current_batch_size = limit - offset

        response = supabase.table(table_name).select("*").range(offset, offset + current_batch_size - 1).execute()

        if not response.data:
            break

        all_data.extend(response.data)
        offset += len(response.data)

        print(f"  Loaded {len(all_data):,} records so far...", end='\r')

        # Stop if we hit the limit or no more data
        if limit and len(all_data) >= limit:
            break
        if len(response.data) < current_batch_size:
            break

    df = pd.DataFrame(all_data)
    print(f"\nLoaded {len(df)} total records from {table_name}")

    # Rename columns to match expected format
    column_mapping = {
        'wostartdate': 'wo_start_date',
        'woenddate': 'wo_end_date',
        'woduration': 'wo_duration',
        'wodescription': 'wo_description',
        'wopriority': 'wo_priority',
        'systemdescription': 'system_description',
        'systemcode': 'system_code',
        'subsystemdescription': 'subsystem_description',
        'subsystemcode': 'subsystem_code',
        'componentdescription': 'component_description',
        'descriptivecode': 'descriptive_code',
        'buildingid': 'building_id',
        'buildingname': 'building_name',
        'universityid': 'university_id',
        'state_province': 'state_province',
        'builtyear': 'built_year',
        'fci_facility_condition_index': 'fci',
        'crv_current_replacement_value': 'crv',
        'dmc_deferred_maintenance_cost': 'dmc',
        'ppm_upm': 'ppm_upm',
        'laborcost': 'labor_cost',
        'materialcost': 'material_cost',
        'othercost': 'other_cost',
        'totalcost': 'total_cost',
        'laborhours': 'labor_hours',
        'mintemp_c': 'min_temp_c',
        'maxtemp_c': 'max_temp_c',
        'atmospheric_pressurehpa': 'atmospheric_pressure',
        'humidity_pct': 'humidity_pct',
        'windspeedm_s': 'wind_speed_ms',
        'winddegree': 'wind_degree',
        'precipitationmm': 'precipitation_mm',
        'snowmm': 'snow_mm',
        'cloudness_pct': 'cloudness_pct',
    }
    df = df.rename(columns=column_mapping)

    return df


def preprocess_raw_data(df):
    """Clean and preprocess raw data"""
    print("Preprocessing raw data...")

    # Convert dates
    df['wo_start_date'] = pd.to_datetime(df['wo_start_date'], errors='coerce')
    df['wo_end_date'] = pd.to_datetime(df['wo_end_date'], errors='coerce')

    # Convert numeric columns from strings
    numeric_cols = [
        'wo_duration', 'wo_priority', 'size', 'built_year', 'fci', 'crv', 'dmc',
        'labor_cost', 'material_cost', 'other_cost', 'total_cost', 'labor_hours',
        'min_temp_c', 'max_temp_c', 'humidity_pct', 'wind_speed_ms',
        'precipitation_mm', 'snow_mm', 'atmospheric_pressure', 'wind_degree', 'cloudness_pct'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows without valid start date or system description
    df = df.dropna(subset=['wo_start_date', 'system_description']).copy()

    # Create binary target: 1 for UPM, 0 for PPM
    df['target_upm'] = (df['ppm_upm'] == 'UPM').astype(int)

    # Extract temporal features
    df['year'] = df['wo_start_date'].dt.year
    df['month'] = df['wo_start_date'].dt.month
    df['quarter'] = df['wo_start_date'].dt.quarter
    df['day_of_week'] = df['wo_start_date'].dt.dayofweek
    df['week_of_year'] = df['wo_start_date'].dt.isocalendar().week

    # Create season feature
    df['season'] = df['month'].apply(lambda x:
        'Winter' if x in [12, 1, 2] else
        'Spring' if x in [3, 4, 5] else
        'Summer' if x in [6, 7, 8] else
        'Fall'
    )

    # Fill missing costs with 0
    cost_cols = ['labor_cost', 'material_cost', 'other_cost', 'total_cost']
    for col in cost_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Fill missing weather data with column median
    weather_cols = ['min_temp_c', 'max_temp_c', 'humidity_pct',
                   'wind_speed_ms', 'precipitation_mm', 'snow_mm']
    for col in weather_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].median())

    print(f"After preprocessing: {len(df)} records")
    return df


def create_system_month_features(df):
    """
    Aggregate data to system-month level
    Each row = one system type in one month
    """
    print("Creating system-month level aggregations...")

    # Group by system, year, month
    grouped = df.groupby(['system_description', 'year', 'month'])

    # Aggregation logic
    features = grouped.agg({
        # Target: UPM rate
        'target_upm': ['sum', 'count', 'mean'],

        # Weather features (monthly averages)
        'min_temp_c': 'mean',
        'max_temp_c': 'mean',
        'humidity_pct': 'mean',
        'wind_speed_ms': 'mean',
        'precipitation_mm': 'mean',
        'snow_mm': 'mean',

        # Cost features
        'total_cost': ['mean', 'sum'],
        'labor_cost': 'mean',
        'material_cost': 'mean',

        # Work order characteristics
        'wo_duration': 'mean',
        'labor_hours': 'mean',
        'wo_priority': 'mean',

        # Building characteristics
        'size': 'mean',
        'built_year': 'mean',
        'fci': 'mean',
    }).reset_index()

    # Flatten column names
    features.columns = ['_'.join(col).strip('_') if col[1] else col[0]
                       for col in features.columns.values]

    # Rename for clarity
    features = features.rename(columns={
        'target_upm_sum': 'upm_count',
        'target_upm_count': 'total_wo_count',
        'target_upm_mean': 'upm_rate',
        'total_cost_mean': 'avg_cost_per_wo',
        'total_cost_sum': 'total_monthly_cost',
        'min_temp_c_mean': 'min_temp_c',
        'max_temp_c_mean': 'max_temp_c',
        'humidity_pct_mean': 'humidity_pct',
        'wind_speed_ms_mean': 'wind_speed_ms',
        'precipitation_mm_mean': 'precipitation_mm',
        'snow_mm_mean': 'snow_mm',
        'labor_cost_mean': 'labor_cost',
        'material_cost_mean': 'material_cost',
        'wo_duration_mean': 'wo_duration',
        'labor_hours_mean': 'labor_hours',
        'wo_priority_mean': 'wo_priority',
        'size_mean': 'size',
        'built_year_mean': 'built_year',
        'fci_mean': 'fci',
    })

    # Create derived features
    features['ppm_count'] = features['total_wo_count'] - features['upm_count']
    features['avg_temp'] = (features['min_temp_c'] + features['max_temp_c']) / 2
    features['temp_range'] = features['max_temp_c'] - features['min_temp_c']

    # Season mapping
    features['season'] = features['month'].apply(lambda x:
        'Winter' if x in [12, 1, 2] else
        'Spring' if x in [3, 4, 5] else
        'Summer' if x in [6, 7, 8] else
        'Fall'
    )

    # Encode season
    season_map = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
    features['season_encoded'] = features['season'].map(season_map)

    # Historical failure rate (rolling 3-month average)
    features = features.sort_values(['system_description', 'year', 'month'])
    features['historical_upm_rate'] = (
        features.groupby('system_description')['upm_rate']
        .rolling(window=3, min_periods=1)
        .mean()
        .reset_index(0, drop=True)
    )

    print(f"Created {len(features)} system-month records")
    return features


def add_system_encoding(features):
    """Add one-hot encoding for system types"""
    print("Adding system type encoding...")

    # Get top 10 most common systems
    top_systems = features['system_description'].value_counts().head(10).index.tolist()

    # Create binary columns for top systems
    for system in top_systems:
        features[f'is_{system.lower().replace(" ", "_")}'] = (
            features['system_description'] == system
        ).astype(int)

    return features


def prepare_training_data(features):
    """
    Prepare final feature set for XGBoost training
    Target: UPM probability (upm_rate)
    """
    print("Preparing training data...")

    # Define feature columns
    feature_cols = [
        # Temporal
        'month', 'season_encoded',

        # Weather
        'min_temp_c', 'max_temp_c', 'avg_temp', 'temp_range',
        'humidity_pct', 'wind_speed_ms', 'precipitation_mm', 'snow_mm',

        # Historical
        'historical_upm_rate', 'total_wo_count',

        # Cost & Work Order Stats
        'avg_cost_per_wo', 'wo_duration', 'labor_hours', 'wo_priority',

        # Building Characteristics
        'size', 'built_year', 'fci',
    ]

    # Add system type binary features
    system_cols = [col for col in features.columns if col.startswith('is_')]
    feature_cols.extend(system_cols)

    # Filter to only include rows with sufficient data
    features = features.dropna(subset=feature_cols + ['upm_rate'])

    # Separate features and target
    X = features[feature_cols]
    y = features['upm_rate']

    # Store metadata for later use
    metadata = features[['system_description', 'year', 'month', 'season',
                        'upm_count', 'ppm_count', 'total_wo_count',
                        'total_monthly_cost']]

    print(f"Final training set: {len(X)} samples, {len(feature_cols)} features")
    print(f"Target (UPM rate) range: {y.min():.3f} to {y.max():.3f}")

    return X, y, metadata, feature_cols


def main(table_names=["fmucd_canada"], limit_per_table=None):
    """Main pipeline execution"""
    print("="*60)
    print("Feature Engineering Pipeline for Predictive Maintenance")
    print("="*60)

    # Step 1: Load data from Supabase
    dataframes = []

    for table_name in table_names:
        print(f"\nLoading from {table_name}...")
        df_table = load_data_from_supabase(table_name=table_name, limit=limit_per_table)
        dataframes.append(df_table)

    # Combine all dataframes
    if len(dataframes) > 1:
        df = pd.concat(dataframes, ignore_index=True)
        print(f"\nCombined {len(dataframes)} tables: {len(df)} total records")
    else:
        df = dataframes[0]

    # Step 2: Preprocess
    df = preprocess_raw_data(df)

    # Step 3: Create system-month features
    features = create_system_month_features(df)

    # Step 4: Add system encoding
    features = add_system_encoding(features)

    # Step 5: Prepare training data
    X, y, metadata, feature_cols = prepare_training_data(features)

    # Step 6: Save processed data
    output_dir = "/home/sradmin/ai-predictive-maintenance-capstone/data/processed"
    os.makedirs(output_dir, exist_ok=True)

    X.to_csv(f"{output_dir}/X_features.csv", index=False)
    y.to_csv(f"{output_dir}/y_target.csv", index=False)
    metadata.to_csv(f"{output_dir}/metadata.csv", index=False)

    # Save feature columns list
    with open(f"{output_dir}/feature_columns.txt", 'w') as f:
        f.write('\n'.join(feature_cols))

    print(f"\n✓ Saved processed data to {output_dir}/")
    print(f"  - X_features.csv: {X.shape}")
    print(f"  - y_target.csv: {y.shape}")
    print(f"  - metadata.csv: {metadata.shape}")
    print(f"  - feature_columns.txt")

    return X, y, metadata, feature_cols


if __name__ == "__main__":
    main()
