#!/usr/bin/env python3
"""
Upload dashboard heatmap data to Supabase for team sharing.
This allows backend to fetch data from Supabase instead of local files.
"""

import os
import json
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Data file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
BUILDING_CSV = os.path.join(PROJECT_ROOT, "data/dashboard/building_level_heatmap.csv")
UNIVERSITY_CSV = os.path.join(PROJECT_ROOT, "data/dashboard/university_level_heatmap.csv")
METADATA_JSON = os.path.join(PROJECT_ROOT, "data/dashboard/metadata.json")

# Table names
BUILDING_TABLE = "heatmap_building"
UNIVERSITY_TABLE = "heatmap_university"
METADATA_TABLE = "heatmap_metadata"


def upload_csv_to_supabase(supabase: Client, csv_path: str, table_name: str):
    """Upload CSV data to Supabase table."""
    print(f"\nLoading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  Rows: {len(df)}")

    # Convert DataFrame to list of dicts
    records = df.to_dict('records')

    # Clear existing data
    print(f"  Clearing existing data in {table_name}...")
    try:
        supabase.table(table_name).delete().neq('id', 0).execute()
    except Exception as e:
        print(f"  Note: {e}")

    # Insert in batches
    batch_size = 1000
    total = len(records)

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            supabase.table(table_name).insert(batch).execute()
            print(f"  Inserted {min(i+batch_size, total)}/{total} rows...")
        except Exception as e:
            print(f"  Error inserting batch: {e}")

    print(f"✓ Uploaded {total} rows to {table_name}")


def upload_metadata_to_supabase(supabase: Client, json_path: str, table_name: str):
    """Upload metadata JSON to Supabase."""
    print(f"\nLoading {json_path}...")
    with open(json_path, 'r') as f:
        metadata = json.load(f)

    # Clear existing metadata
    print(f"  Clearing existing data in {table_name}...")
    try:
        supabase.table(table_name).delete().neq('id', 0).execute()
    except Exception as e:
        print(f"  Note: {e}")

    # Store as single record with JSON field
    record = {
        "data": metadata,
        "updated_at": "now()"
    }

    try:
        supabase.table(table_name).insert(record).execute()
        print(f"✓ Uploaded metadata to {table_name}")
    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("=" * 70)
    print("UPLOADING DASHBOARD DATA TO SUPABASE")
    print("=" * 70)

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print(f"Connected to Supabase: {SUPABASE_URL}")

    # Upload building-level heatmap
    upload_csv_to_supabase(supabase, BUILDING_CSV, BUILDING_TABLE)

    # Upload university-level heatmap
    upload_csv_to_supabase(supabase, UNIVERSITY_CSV, UNIVERSITY_TABLE)

    # Upload metadata
    upload_metadata_to_supabase(supabase, METADATA_JSON, METADATA_TABLE)

    print("\n" + "=" * 70)
    print("✓ ALL DATA UPLOADED TO SUPABASE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update backend/main.py to fetch from Supabase instead of local files")
    print("2. Teammates can now run backend without generating data locally")
    print("")


if __name__ == "__main__":
    main()
