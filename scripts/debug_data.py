#!/usr/bin/env python3
"""
Debug script to identify where data is being lost in the pipeline
"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def debug_pipeline():
    """Debug data loading and preprocessing"""

    print("="*60)
    print("Debug: Data Pipeline")
    print("="*60)

    # Step 1: Load raw data
    print("\n[Step 1] Loading from Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    response = supabase.table("fmucd_canada").select("*").limit(1000).execute()
    df = pd.DataFrame(response.data)

    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)[:10]}...")

    # Step 2: Check column names
    print("\n[Step 2] Column Analysis")
    print("Available columns:")
    for col in df.columns:
        print(f"  - {col}")

    # Step 3: Check critical columns
    print("\n[Step 3] Critical Column Check")

    critical_cols = {
        'wo_start_date': ['wo_start_date', 'wostartdate', 'WOStartDate'],
        'system_description': ['system_description', 'systemdescription', 'SystemDescription'],
        'ppm_upm': ['ppm_upm', 'PPM/UPM', 'ppmupm'],
    }

    for expected, variants in critical_cols.items():
        found = None
        for variant in variants:
            if variant in df.columns:
                found = variant
                break

        if found:
            print(f"✓ {expected}: found as '{found}'")
            print(f"  Sample values: {df[found].head(3).tolist()}")
        else:
            print(f"✗ {expected}: NOT FOUND")

    # Step 4: Check data types
    print("\n[Step 4] Data Types")
    print(df.dtypes.head(20))

    # Step 5: Check for nulls
    print("\n[Step 5] Null Values")
    null_counts = df.isnull().sum()
    print(null_counts[null_counts > 0].head(10))

    return df


if __name__ == "__main__":
    df = debug_pipeline()

    print("\n" + "="*60)
    print("Debug complete! Check output above to identify issues.")
    print("="*60)
