#!/usr/bin/env python3
"""
Backend Data Validation Script for Defect Analytics Dashboard

This script validates that all required data files exist and have the correct structure
for the master's-level Defect Analytics frontend.

Usage:
    python3 scripts/validate_backend_data.py
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ️  {text}{RESET}")

# Define expected file structures
EXPECTED_FILES = {
    'defect_analytics': {
        'global_rankings.csv': {
            'required_columns': [
                'SubsystemDescription', 'total_count', 'frequency_per_month',
                'severity_score', 'avg_cost', 'avg_duration', 'strongest_weather_factor',
                'strongest_correlation'
            ],
            'min_rows': 10
        },
        'university_rankings.csv': {
            'required_columns': [
                'UniversityID', 'SubsystemDescription', 'total_count',
                'frequency_per_month', 'severity_score', 'avg_cost', 'avg_duration',
                'strongest_weather_factor', 'strongest_correlation'
            ],
            'min_rows': 50
        },
        'building_rankings.csv': {
            'required_columns': [
                'UniversityID', 'BuildingName', 'SubsystemDescription',
                'total_count', 'frequency_per_month', 'severity_score'
            ],
            'min_rows': 100
        }
    },
    'ml_defect_analytics': {
        'recurrence_forecast_comparison.csv': {
            'required_columns': ['subsystem', 'arima_mae', 'prophet_mae', 'xgb_mae', 'best_model'],
            'min_rows': 3
        },
        'environmental_model_comparison.csv': {
            'required_columns': ['model', 'train_mae', 'test_mae', 'train_r2', 'test_r2'],
            'min_rows': 2
        },
        'survival_cox_model.json': {
            'required_fields': ['model', 'c_index', 'n_samples', 'coefficients']
        }
    }
}

def validate_csv_file(filepath: Path, expected_structure: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a CSV file structure

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    if not filepath.exists():
        issues.append(f"File not found: {filepath}")
        return False, issues

    try:
        df = pd.read_csv(filepath)

        # Check minimum rows
        min_rows = expected_structure.get('min_rows', 1)
        if len(df) < min_rows:
            issues.append(f"Insufficient data: {len(df)} rows (expected ≥{min_rows})")

        # Check required columns
        required_cols = expected_structure.get('required_columns', [])
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            issues.append(f"Missing columns: {', '.join(missing_cols)}")

        # Check for empty columns
        for col in required_cols:
            if col in df.columns:
                null_pct = (df[col].isnull().sum() / len(df)) * 100
                if null_pct > 50:
                    issues.append(f"Column '{col}' has {null_pct:.1f}% null values")

        return len(issues) == 0, issues

    except Exception as e:
        issues.append(f"Error reading file: {str(e)}")
        return False, issues

def validate_json_file(filepath: Path, expected_structure: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a JSON file structure

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    if not filepath.exists():
        issues.append(f"File not found: {filepath}")
        return False, issues

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Check required fields
        required_fields = expected_structure.get('required_fields', [])
        missing_fields = set(required_fields) - set(data.keys())
        if missing_fields:
            issues.append(f"Missing fields: {', '.join(missing_fields)}")

        return len(issues) == 0, issues

    except Exception as e:
        issues.append(f"Error reading file: {str(e)}")
        return False, issues

def validate_data_statistics(frontend_dir: Path):
    """Validate and display data statistics"""
    print_header("DATA STATISTICS")

    # Load university data
    uni_file = frontend_dir / 'public/data/defect_analytics/university_rankings.csv'
    if uni_file.exists():
        df_uni = pd.read_csv(uni_file)

        universities = df_uni['UniversityID'].unique()
        subsystems = df_uni['SubsystemDescription'].nunique()
        total_defects = df_uni['total_count'].sum()

        print(f"  📊 Universities in dataset: {len(universities)}")
        print(f"     IDs: {sorted(universities)}")
        print(f"  📊 Unique subsystems: {subsystems}")
        print(f"  📊 Total defects tracked: {int(total_defects):,}")

        # Top subsystems
        top_5 = df_uni.nlargest(5, 'total_count')
        print(f"\n  🏆 Top 5 Subsystems by Total Count:")
        for idx, row in top_5.iterrows():
            print(f"     {row['SubsystemDescription']}: {int(row['total_count']):,} defects")

    # Load building data
    bldg_file = frontend_dir / 'public/data/defect_analytics/building_rankings.csv'
    if bldg_file.exists():
        df_bldg = pd.read_csv(bldg_file)
        buildings = df_bldg['BuildingName'].nunique()
        print(f"\n  🏢 Buildings tracked: {buildings}")

    # ML Model performance
    env_file = frontend_dir / 'public/data/ml_defect_analytics/environmental_model_comparison.csv'
    if env_file.exists():
        df_env = pd.read_csv(env_file)
        best_model = df_env.loc[df_env['test_r2'].idxmax()]
        print(f"\n  🤖 Best Environmental Model: {best_model['model']}")
        print(f"     R² Score: {best_model['test_r2']:.4f} ({best_model['test_r2']*100:.1f}% variance explained)")
        print(f"     Test MAE: {best_model['test_mae']:.2f}")

def main():
    """Main validation function"""
    print_header("DEFECT ANALYTICS BACKEND DATA VALIDATION")

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    frontend_dir = project_root / 'frontend'

    print(f"Project root: {project_root}")
    print(f"Frontend dir: {frontend_dir}")

    total_files = 0
    valid_files = 0
    invalid_files = 0

    # Validate each category
    for category, files in EXPECTED_FILES.items():
        print_header(f"VALIDATING: {category.replace('_', ' ').upper()}")

        category_path = frontend_dir / f'public/data/{category}'

        for filename, expected_structure in files.items():
            total_files += 1
            filepath = category_path / filename

            print(f"\n📄 {filename}")
            print(f"   Path: {filepath}")

            # Validate based on file type
            if filename.endswith('.csv'):
                is_valid, issues = validate_csv_file(filepath, expected_structure)
            elif filename.endswith('.json'):
                is_valid, issues = validate_json_file(filepath, expected_structure)
            else:
                print_warning(f"Unknown file type: {filename}")
                continue

            if is_valid:
                print_success(f"Valid ✓")
                valid_files += 1

                # Show file size
                if filepath.exists():
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    if size_mb < 1:
                        size_str = f"{filepath.stat().st_size / 1024:.1f} KB"
                    else:
                        size_str = f"{size_mb:.2f} MB"
                    print(f"   Size: {size_str}")

                    # Show row count for CSV
                    if filename.endswith('.csv'):
                        df = pd.read_csv(filepath)
                        print(f"   Rows: {len(df):,}")
            else:
                print_error(f"Invalid ✗")
                invalid_files += 1
                for issue in issues:
                    print(f"     • {issue}")

    # Data statistics
    validate_data_statistics(frontend_dir)

    # Final summary
    print_header("VALIDATION SUMMARY")

    print(f"Total files checked: {total_files}")
    print(f"{GREEN}Valid files: {valid_files}{RESET}")
    if invalid_files > 0:
        print(f"{RED}Invalid files: {invalid_files}{RESET}")
    else:
        print(f"Invalid files: {invalid_files}")

    if invalid_files == 0:
        print_success("\n✨ ALL DATA FILES ARE VALID AND READY FOR FRONTEND! ✨\n")
        print_info("Next steps:")
        print("  1. Start the frontend: cd frontend && npm run dev")
        print("  2. Open browser: http://localhost:5173")
        print("  3. Navigate to Defect Analytics page")
        print("  4. Test with diagnostic page: http://localhost:5173/test-data-loading.html")
        return 0
    else:
        print_error("\n⚠️  SOME DATA FILES HAVE ISSUES - FIX BEFORE RUNNING FRONTEND ⚠️\n")
        print_info("To regenerate data files:")
        print("  1. python3 scripts/calculate_defect_analytics.py")
        print("  2. python3 scripts/ml_defect_analytics_optimized.py")
        print("  3. python3 scripts/validate_backend_data.py")
        return 1

if __name__ == '__main__':
    exit(main())
