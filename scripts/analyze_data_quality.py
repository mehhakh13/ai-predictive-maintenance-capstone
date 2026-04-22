"""
Data Quality Analysis Script
Analyzes null values and data completeness across universities and buildings
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "data_quality"
OUTPUT_DIR.mkdir(exist_ok=True)

# Critical fields for analysis
CRITICAL_FIELDS = {
    'cost': ['TotalCost', 'LaborCost', 'MaterialCost'],
    'time': ['WOStartDate', 'WOEndDate', 'WODuration'],
    'priority': ['WOPriority'],
    'weather': ['MinTemp.(°C)', 'MaxTemp.(°C)', 'Humidity(%)', 'Precipitation(mm)', 'Snow(mm)', 'WindSpeed(m/s)', 'Atmospheric pressure(hPa)'],
    'location': ['UniversityID', 'BuildingName', 'BuildingID'],
    'defect': ['SubsystemDescription', 'SystemClassification', 'WODescription']
}

def analyze_dataset(file_path, dataset_name):
    """Analyze a single dataset for data quality"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {dataset_name}")
    print(f"{'='*80}")

    # Read in chunks to handle large files
    chunk_size = 100000
    first_chunk = True

    total_rows = 0
    null_counts = {}
    university_stats = {}
    building_stats = {}

    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        total_rows += len(chunk)

        # Initialize null counts on first chunk
        if first_chunk:
            null_counts = {col: 0 for col in chunk.columns}
            first_chunk = False

        # Count nulls
        for col in chunk.columns:
            null_counts[col] += chunk[col].isna().sum()

        # Analyze by university
        if 'UniversityID' in chunk.columns and 'BuildingName' in chunk.columns:
            for uni in chunk['UniversityID'].dropna().unique():
                if uni not in university_stats:
                    university_stats[uni] = {
                        'total_records': 0,
                        'buildings': set(),
                        'null_cost': 0,
                        'null_weather': 0,
                        'null_duration': 0,
                        'null_priority': 0
                    }

                uni_data = chunk[chunk['UniversityID'] == uni]
                university_stats[uni]['total_records'] += len(uni_data)
                university_stats[uni]['buildings'].update(uni_data['BuildingName'].dropna().unique())
                university_stats[uni]['null_cost'] += uni_data['TotalCost'].isna().sum()
                university_stats[uni]['null_weather'] += uni_data[['MinTemp.(°C)', 'MaxTemp.(°C)', 'Humidity(%)']].isna().all(axis=1).sum()
                university_stats[uni]['null_duration'] += uni_data['WODuration'].isna().sum()
                university_stats[uni]['null_priority'] += uni_data['WOPriority'].isna().sum()

        # Analyze by building
        if 'BuildingName' in chunk.columns:
            for building in chunk['BuildingName'].dropna().unique():
                if building not in building_stats:
                    building_stats[building] = {
                        'total_records': 0,
                        'university': None,
                        'null_cost': 0,
                        'null_weather': 0,
                        'null_duration': 0
                    }

                bldg_data = chunk[chunk['BuildingName'] == building]
                building_stats[building]['total_records'] += len(bldg_data)
                if building_stats[building]['university'] is None and 'UniversityID' in chunk.columns:
                    building_stats[building]['university'] = bldg_data['UniversityID'].iloc[0] if len(bldg_data) > 0 else None
                building_stats[building]['null_cost'] += bldg_data['TotalCost'].isna().sum()
                building_stats[building]['null_weather'] += bldg_data[['MinTemp.(°C)', 'MaxTemp.(°C)', 'Humidity(%)']].isna().all(axis=1).sum()
                building_stats[building]['null_duration'] += bldg_data['WODuration'].isna().sum()

        print(f"Processed {total_rows:,} rows...", end='\r')

    print(f"\nTotal rows processed: {total_rows:,}")

    # Calculate percentages
    null_percentages = {col: (count / total_rows * 100) for col, count in null_counts.items()}

    # Calculate university data quality scores
    for uni, stats in university_stats.items():
        stats['buildings'] = len(stats['buildings'])
        stats['cost_completeness'] = (1 - stats['null_cost'] / stats['total_records']) * 100
        stats['weather_completeness'] = (1 - stats['null_weather'] / stats['total_records']) * 100
        stats['duration_completeness'] = (1 - stats['null_duration'] / stats['total_records']) * 100
        stats['priority_completeness'] = (1 - stats['null_priority'] / stats['total_records']) * 100
        stats['overall_quality'] = (
            stats['cost_completeness'] * 0.3 +
            stats['weather_completeness'] * 0.3 +
            stats['duration_completeness'] * 0.2 +
            stats['priority_completeness'] * 0.2
        )

    # Calculate building data quality scores
    for building, stats in building_stats.items():
        stats['cost_completeness'] = (1 - stats['null_cost'] / stats['total_records']) * 100
        stats['weather_completeness'] = (1 - stats['null_weather'] / stats['total_records']) * 100
        stats['duration_completeness'] = (1 - stats['null_duration'] / stats['total_records']) * 100
        stats['overall_quality'] = (
            stats['cost_completeness'] * 0.4 +
            stats['weather_completeness'] * 0.4 +
            stats['duration_completeness'] * 0.2
        )

    return {
        'dataset': dataset_name,
        'total_rows': total_rows,
        'null_counts': null_counts,
        'null_percentages': null_percentages,
        'university_stats': university_stats,
        'building_stats': building_stats
    }

def print_summary_report(results):
    """Print comprehensive summary report"""
    print("\n" + "="*100)
    print("DATA QUALITY SUMMARY REPORT")
    print("="*100)

    for result in results:
        dataset = result['dataset']
        total_rows = result['total_rows']
        null_pct = result['null_percentages']
        uni_stats = result['university_stats']
        bldg_stats = result['building_stats']

        print(f"\n📊 {dataset}")
        print(f"   Total Records: {total_rows:,}")
        print(f"   Universities: {len(uni_stats)}")
        print(f"   Buildings: {len(bldg_stats)}")

        print(f"\n   🔍 Null Percentages (Key Fields):")
        print(f"      Cost Fields:")
        print(f"         TotalCost: {null_pct.get('TotalCost', 0):.1f}%")
        print(f"         LaborCost: {null_pct.get('LaborCost', 0):.1f}%")
        print(f"         MaterialCost: {null_pct.get('MaterialCost', 0):.1f}%")

        print(f"      Time Fields:")
        print(f"         WODuration: {null_pct.get('WODuration', 0):.1f}%")
        print(f"         WOPriority: {null_pct.get('WOPriority', 0):.1f}%")

        print(f"      Weather Fields:")
        print(f"         MinTemp: {null_pct.get('MinTemp.(°C)', 0):.1f}%")
        print(f"         MaxTemp: {null_pct.get('MaxTemp.(°C)', 0):.1f}%")
        print(f"         Humidity: {null_pct.get('Humidity(%)', 0):.1f}%")
        print(f"         Precipitation: {null_pct.get('Precipitation(mm)', 0):.1f}%")

        # University quality distribution
        if uni_stats:
            quality_scores = [s['overall_quality'] for s in uni_stats.values()]
            print(f"\n   🎓 University Data Quality Distribution:")
            print(f"      Excellent (>90%): {sum(1 for s in quality_scores if s > 90)} universities")
            print(f"      Good (70-90%): {sum(1 for s in quality_scores if 70 <= s <= 90)} universities")
            print(f"      Fair (50-70%): {sum(1 for s in quality_scores if 50 <= s < 70)} universities")
            print(f"      Poor (<50%): {sum(1 for s in quality_scores if s < 50)} universities")

            # Top 5 best universities
            sorted_unis = sorted(uni_stats.items(), key=lambda x: x[1]['overall_quality'], reverse=True)[:5]
            print(f"\n      Top 5 Universities by Data Quality:")
            for i, (uni, stats) in enumerate(sorted_unis, 1):
                print(f"         {i}. {uni}: {stats['overall_quality']:.1f}% ({stats['total_records']:,} records, {stats['buildings']} buildings)")

            # Bottom 5 worst universities
            worst_unis = sorted(uni_stats.items(), key=lambda x: x[1]['overall_quality'])[:5]
            print(f"\n      Bottom 5 Universities by Data Quality:")
            for i, (uni, stats) in enumerate(worst_unis, 1):
                print(f"         {i}. {uni}: {stats['overall_quality']:.1f}% ({stats['total_records']:,} records)")

        # Building quality distribution
        if bldg_stats:
            quality_scores = [s['overall_quality'] for s in bldg_stats.values()]
            print(f"\n   🏛️  Building Data Quality Distribution:")
            print(f"      Excellent (>90%): {sum(1 for s in quality_scores if s > 90)} buildings")
            print(f"      Good (70-90%): {sum(1 for s in quality_scores if 70 <= s <= 90)} buildings")
            print(f"      Fair (50-70%): {sum(1 for s in quality_scores if 50 <= s < 70)} buildings")
            print(f"      Poor (<50%): {sum(1 for s in quality_scores if s < 50)} buildings")

def generate_recommendations(results):
    """Generate data cleaning recommendations"""
    print("\n" + "="*100)
    print("📋 RECOMMENDATIONS")
    print("="*100)

    all_uni_stats = {}
    all_bldg_stats = {}

    for result in results:
        all_uni_stats.update(result['university_stats'])
        all_bldg_stats.update(result['building_stats'])

    # Calculate thresholds
    quality_scores = [s['overall_quality'] for s in all_uni_stats.values()]
    avg_quality = np.mean(quality_scores)
    median_quality = np.median(quality_scores)

    print(f"\n1. DATA QUALITY STATISTICS:")
    print(f"   Average university quality score: {avg_quality:.1f}%")
    print(f"   Median university quality score: {median_quality:.1f}%")
    print(f"   Total universities: {len(all_uni_stats)}")
    print(f"   Total buildings: {len(all_bldg_stats)}")

    # Recommend thresholds
    high_quality_count = sum(1 for s in quality_scores if s >= 80)
    medium_quality_count = sum(1 for s in quality_scores if 60 <= s < 80)

    print(f"\n2. RECOMMENDED FILTERING STRATEGY:")
    print(f"   Option A (Strict): Use universities with >80% quality")
    print(f"              → Keeps {high_quality_count} universities ({high_quality_count/len(all_uni_stats)*100:.1f}%)")
    print(f"              → Highest accuracy, but loses some data")

    print(f"   Option B (Moderate): Use universities with >60% quality")
    print(f"              → Keeps {high_quality_count + medium_quality_count} universities ({(high_quality_count + medium_quality_count)/len(all_uni_stats)*100:.1f}%)")
    print(f"              → Good balance of accuracy and coverage")

    print(f"   Option C (Lenient): Use universities with >40% quality")
    print(f"              → Keeps most universities")
    print(f"              → More data but lower accuracy")

    # Check weather data availability
    has_weather = sum(1 for s in all_uni_stats.values() if s['weather_completeness'] > 50)
    print(f"\n3. WEATHER DATA AVAILABILITY:")
    print(f"   Universities with >50% weather data: {has_weather} ({has_weather/len(all_uni_stats)*100:.1f}%)")
    print(f"   → For Environmental Sensitivity analysis, only include these {has_weather} universities")

    # Row-level filtering recommendation
    total_rows = sum(r['total_rows'] for r in results)
    print(f"\n4. ROW-LEVEL FILTERING RECOMMENDATION:")
    print(f"   Strategy: Remove rows where:")
    print(f"      - TotalCost IS NULL (can't calculate severity)")
    print(f"      - WODuration IS NULL (can't calculate severity)")
    print(f"      - SubsystemDescription IS NULL (can't categorize)")
    print(f"   This will ensure clean data for Recurrence and Severity rankings.")
    print(f"   For Environmental rankings, additionally require weather data.")

    return {
        'avg_quality': avg_quality,
        'median_quality': median_quality,
        'recommended_threshold': 60 if median_quality < 70 else 70,
        'universities_with_weather': has_weather
    }

def save_detailed_reports(results):
    """Save detailed CSV reports"""
    for result in results:
        dataset = result['dataset']

        # Save university report
        uni_df = pd.DataFrame.from_dict(result['university_stats'], orient='index')
        uni_df.index.name = 'UniversityID'
        uni_df = uni_df.sort_values('overall_quality', ascending=False)
        uni_output = OUTPUT_DIR / f"{dataset}_university_quality.csv"
        uni_df.to_csv(uni_output)
        print(f"\n✅ Saved: {uni_output}")

        # Save building report
        bldg_df = pd.DataFrame.from_dict(result['building_stats'], orient='index')
        bldg_df.index.name = 'BuildingName'
        bldg_df = bldg_df.sort_values('overall_quality', ascending=False)
        bldg_output = OUTPUT_DIR / f"{dataset}_building_quality.csv"
        bldg_df.to_csv(bldg_output)
        print(f"✅ Saved: {bldg_output}")

        # Save null percentages
        null_df = pd.DataFrame.from_dict(result['null_percentages'], orient='index', columns=['null_percentage'])
        null_df.index.name = 'field'
        null_df = null_df.sort_values('null_percentage', ascending=False)
        null_output = OUTPUT_DIR / f"{dataset}_null_analysis.csv"
        null_df.to_csv(null_output)
        print(f"✅ Saved: {null_output}")

def main():
    print("Starting Data Quality Analysis...")
    print("This may take 10-30 minutes depending on dataset size...")

    datasets = [
        (DATA_DIR / "fmucd_usa.csv", "USA"),
        (DATA_DIR / "fmucd_canada.csv", "Canada"),
        (DATA_DIR / "fmucd_california.csv", "California")
    ]

    results = []

    for file_path, name in datasets:
        if file_path.exists():
            try:
                result = analyze_dataset(file_path, name)
                results.append(result)
            except Exception as e:
                print(f"❌ Error analyzing {name}: {e}")
        else:
            print(f"⚠️  File not found: {file_path}")

    if results:
        print_summary_report(results)
        recommendations = generate_recommendations(results)
        save_detailed_reports(results)

        # Save recommendations
        rec_output = OUTPUT_DIR / "recommendations.json"
        with open(rec_output, 'w') as f:
            json.dump(recommendations, f, indent=2)
        print(f"\n✅ Saved recommendations: {rec_output}")

        print("\n" + "="*100)
        print("✅ ANALYSIS COMPLETE!")
        print(f"📁 Detailed reports saved to: {OUTPUT_DIR}")
        print("="*100)
    else:
        print("\n❌ No datasets found to analyze!")

if __name__ == "__main__":
    main()
