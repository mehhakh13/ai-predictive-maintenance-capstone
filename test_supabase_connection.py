#!/usr/bin/env python3
"""
Quick test script to verify Supabase connection and table structure
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def test_connection():
    """Test Supabase connection and show table info"""

    print("="*60)
    print("Supabase Connection Test")
    print("="*60)

    # Check environment variables
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ ERROR: Missing Supabase credentials in .env file")
        print("\nPlease create a .env file with:")
        print("SUPABASE_URL=your_url")
        print("SUPABASE_SERVICE_ROLE_KEY=your_key")
        return False

    print(f"\n✓ Supabase URL: {SUPABASE_URL}")
    print(f"✓ Service key: {SUPABASE_SERVICE_ROLE_KEY[:20]}...")

    # Create client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("\n✓ Supabase client created successfully")
    except Exception as e:
        print(f"\n❌ Failed to create Supabase client: {e}")
        return False

    # Test tables
    tables = ["fmucd_canada", "fmucd_california"]

    for table_name in tables:
        print(f"\n--- Testing table: {table_name} ---")

        try:
            # Get row count
            response = supabase.table(table_name).select("*", count='exact').limit(1).execute()

            if hasattr(response, 'count') and response.count is not None:
                print(f"✓ Table exists")
                print(f"  Total rows: {response.count:,}")
            else:
                print(f"✓ Table exists")
                print(f"  (Row count not available)")

            # Get sample row
            if response.data and len(response.data) > 0:
                sample = response.data[0]
                print(f"\n  Sample columns ({len(sample)} total):")
                for key in list(sample.keys())[:10]:
                    value = sample[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"    - {key}: {value}")

                if len(sample) > 10:
                    print(f"    ... and {len(sample) - 10} more columns")
            else:
                print("  ⚠ Table is empty")

        except Exception as e:
            print(f"❌ Error accessing table {table_name}: {e}")
            print(f"   Make sure the table exists and is populated")

    print("\n" + "="*60)
    print("✓ Connection test complete!")
    print("="*60)
    print("\nYou can now run the feature engineering pipeline:")
    print("  python scripts/feature_engineering.py")

    return True


if __name__ == "__main__":
    test_connection()
