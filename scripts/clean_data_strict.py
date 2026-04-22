"""
Data Cleaning Script - Strict Strategy
Filters to high-quality universities (>80%) and removes rows with critical null values
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_QUALITY_DIR = DATA_DIR / "data_quality"
OUTPUT_DIR = DATA_DIR / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load university quality scores
def load_university_quality_scores():
    """Load quality scores from all datasets"""
    quality_scores = {}

    for dataset in ['USA', 'Canada', 'California']:
        file_path = DATA_QUALITY_DIR / f"{dataset}_university_quality.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                uni_id = row['UniversityID']
                quality = row['overall_quality']
                if uni_id not in quality_scores or quality > quality_scores[uni_id]['quality']:
                    quality_scores[uni_id] = {
                        'quality': quality,
                        'dataset': dataset,
                        'total_records': row['total_records'],
                        'buildings': row['buildings']
                    }

    return quality_scores

def filter_high_quality_universities(quality_scores, threshold=80.0):
    """Get list of universities above quality threshold"""
    high_quality = {
        uni_id: data for uni_id, data in quality_scores.items()
        if data['quality'] >= threshold
    }
    return high_quality

def clean_dataset(file_path, dataset_name, high_quality_unis):
    """Clean a single dataset"""
    print(f"\n{'='*80}")
    print(f"Cleaning: {dataset_name}")
    print(f"{'='*80}")

    chunk_size = 100000
    cleaned_chunks = []

    total_rows = 0
    kept_rows = 0
    removed_bad_uni = 0
    removed_null_cost = 0
    removed_null_duration = 0
    removed_null_subsystem = 0

    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        total_rows += len(chunk)

        # Track original size
        original_size = len(chunk)

        # Filter 1: Keep only high-quality universities
        chunk_filtered = chunk[chunk['UniversityID'].isin(high_quality_unis.keys())].copy()
        removed_bad_uni += original_size - len(chunk_filtered)

        # Track size after university filter
        after_uni_filter = len(chunk_filtered)

        # Filter 2: Remove rows with null TotalCost
        chunk_filtered = chunk_filtered[chunk_filtered['TotalCost'].notna()]
        removed_null_cost += after_uni_filter - len(chunk_filtered)
        after_cost_filter = len(chunk_filtered)

        # Filter 3: Remove rows with null WODuration
        chunk_filtered = chunk_filtered[chunk_filtered['WODuration'].notna()]
        removed_null_duration += after_cost_filter - len(chunk_filtered)
        after_duration_filter = len(chunk_filtered)

        # Filter 4: Remove rows with null SubsystemDescription
        chunk_filtered = chunk_filtered[chunk_filtered['SubsystemDescription'].notna()]
        removed_null_subsystem += after_duration_filter - len(chunk_filtered)

        kept_rows += len(chunk_filtered)

        if len(chunk_filtered) > 0:
            cleaned_chunks.append(chunk_filtered)

        print(f"Processed {total_rows:,} rows, kept {kept_rows:,} ({kept_rows/total_rows*100:.1f}%)...", end='\r')

    print(f"\nProcessing complete!")
    print(f"  Total rows: {total_rows:,}")
    print(f"  Kept rows: {kept_rows:,} ({kept_rows/total_rows*100:.1f}%)")
    print(f"  Removed:")
    print(f"    Low-quality universities: {removed_bad_uni:,}")
    print(f"    Null TotalCost: {removed_null_cost:,}")
    print(f"    Null WODuration: {removed_null_duration:,}")
    print(f"    Null SubsystemDescription: {removed_null_subsystem:,}")

    # Combine chunks
    if cleaned_chunks:
        df_cleaned = pd.concat(cleaned_chunks, ignore_index=True)
        return df_cleaned, {
            'dataset': dataset_name,
            'total_rows': total_rows,
            'kept_rows': kept_rows,
            'removal_stats': {
                'low_quality_uni': removed_bad_uni,
                'null_cost': removed_null_cost,
                'null_duration': removed_null_duration,
                'null_subsystem': removed_null_subsystem
            }
        }
    else:
        return None, None

def analyze_cleaned_data(df, dataset_name):
    """Analyze the cleaned dataset"""
    print(f"\n📊 Cleaned Data Analysis: {dataset_name}")
    print(f"  Total records: {len(df):,}")
    print(f"  Universities: {df['UniversityID'].nunique()}")
    print(f"  Buildings: {df['BuildingName'].nunique()}")
    print(f"  Subsystems: {df['SubsystemDescription'].nunique()}")
    print(f"  Date range: {df['WOStartDate'].min()} to {df['WOStartDate'].max()}")
    print(f"  Total cost: ${df['TotalCost'].sum():,.2f}")
    print(f"  Average cost per WO: ${df['TotalCost'].mean():,.2f}")
    print(f"  Average duration: {df['WODuration'].mean():.2f} hours")

    # Work order type distribution
    if 'PPM/UPM' in df.columns:
        print(f"\n  Work Order Types:")
        for wo_type, count in df['PPM/UPM'].value_counts().items():
            print(f"    {wo_type}: {count:,} ({count/len(df)*100:.1f}%)")

    # Top subsystems by frequency
    print(f"\n  Top 10 Subsystems by Frequency:")
    top_subsystems = df['SubsystemDescription'].value_counts().head(10)
    for i, (subsystem, count) in enumerate(top_subsystems.items(), 1):
        print(f"    {i}. {subsystem}: {count:,}")

def save_cleaned_data(df, dataset_name):
    """Save cleaned dataset"""
    output_path = OUTPUT_DIR / f"fmucd_{dataset_name.lower()}_cleaned.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved cleaned data: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    return output_path

def main():
    print("="*80)
    print("DATA CLEANING - STRICT STRATEGY")
    print("Strategy: Keep universities with >80% quality, remove rows with critical nulls")
    print("="*80)

    # Load university quality scores
    print("\nLoading university quality scores...")
    quality_scores = load_university_quality_scores()
    print(f"Found {len(quality_scores)} universities")

    # Filter to high-quality universities
    high_quality_unis = filter_high_quality_universities(quality_scores, threshold=80.0)
    print(f"\n✅ Selected {len(high_quality_unis)} universities with >80% quality:")
    for uni_id, data in sorted(high_quality_unis.items(), key=lambda x: x[1]['quality'], reverse=True):
        print(f"   University {uni_id}: {data['quality']:.1f}% ({data['total_records']:,} records, {data['buildings']} buildings)")

    # Process each dataset
    datasets = [
        (DATA_DIR / "fmucd_usa.csv", "USA"),
        (DATA_DIR / "fmucd_canada.csv", "Canada"),
        (DATA_DIR / "fmucd_california.csv", "California")
    ]

    all_cleaned_data = []
    cleaning_stats = []

    for file_path, name in datasets:
        if file_path.exists():
            try:
                df_cleaned, stats = clean_dataset(file_path, name, high_quality_unis)
                if df_cleaned is not None:
                    analyze_cleaned_data(df_cleaned, name)
                    saved_path = save_cleaned_data(df_cleaned, name)
                    all_cleaned_data.append(df_cleaned)
                    cleaning_stats.append(stats)
            except Exception as e:
                print(f"❌ Error cleaning {name}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  File not found: {file_path}")

    # Combine all datasets
    if all_cleaned_data:
        print("\n" + "="*80)
        print("CREATING COMBINED CLEANED DATASET")
        print("="*80)

        df_combined = pd.concat(all_cleaned_data, ignore_index=True)
        print(f"\n📊 Combined Dataset Statistics:")
        print(f"  Total records: {len(df_combined):,}")
        print(f"  Universities: {df_combined['UniversityID'].nunique()}")
        print(f"  Buildings: {df_combined['BuildingName'].nunique()}")
        print(f"  Subsystems: {df_combined['SubsystemDescription'].nunique()}")
        print(f"  Date range: {df_combined['WOStartDate'].min()} to {df_combined['WOStartDate'].max()}")

        # Save combined dataset
        combined_path = OUTPUT_DIR / "fmucd_all_cleaned.csv"
        df_combined.to_csv(combined_path, index=False)
        print(f"\n✅ Saved combined cleaned data: {combined_path}")
        print(f"   File size: {combined_path.stat().st_size / 1024 / 1024:.1f} MB")

        # Save cleaning stats
        stats_path = OUTPUT_DIR / "cleaning_stats.json"
        with open(stats_path, 'w') as f:
            json.dump({
                'strategy': 'strict',
                'threshold': 80.0,
                'selected_universities': {str(k): v for k, v in high_quality_unis.items()},
                'dataset_stats': cleaning_stats,
                'combined_stats': {
                    'total_records': len(df_combined),
                    'universities': int(df_combined['UniversityID'].nunique()),
                    'buildings': int(df_combined['BuildingName'].nunique()),
                    'subsystems': int(df_combined['SubsystemDescription'].nunique())
                }
            }, f, indent=2)
        print(f"✅ Saved cleaning statistics: {stats_path}")

    print("\n" + "="*80)
    print("✅ DATA CLEANING COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Use cleaned data for defect analytics calculations")
    print("  2. Build university/building-level rankings")
    print("  3. Create dashboard visualizations")

if __name__ == "__main__":
    main()
