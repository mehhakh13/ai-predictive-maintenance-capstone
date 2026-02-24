import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

# Load environment variables
load_dotenv('/home/sradmin/ai-predictive-maintenance-capstone/.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Config
INPUT_FILE = '/home/sradmin/ai-predictive-maintenance-capstone/data/fmucd_canada.csv'
TABLE_NAME = 'fmucd_canada'
CHUNK_SIZE = 5000  # Read 5k rows at a time
BATCH_SIZE = 500   # Insert 500 rows per API call

def clean_columns(df):
    """Clean column names for Supabase"""
    df.columns = [
        col.replace(' ', '_')
           .replace('/', '_')
           .replace('(', '')
           .replace(')', '')
           .replace('.', '_')
           .replace('°', '')
           .replace('%', '_pct')
           .lower()
        for col in df.columns
    ]
    return df

def clean_record(record):
    """Clean NaN/inf values for JSON"""
    cleaned = {}
    for k, v in record.items():
        if v is None:
            cleaned[k] = None
        elif isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            cleaned[k] = None
        else:
            cleaned[k] = v
    return cleaned

def upload_chunk(records, table_name):
    """Upload records in batches"""
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        supabase.table(table_name).insert(batch).execute()

# Count total rows for progress bar
print("Counting rows...")
total_rows = sum(1 for _ in open(INPUT_FILE)) - 1
total_chunks = (total_rows // CHUNK_SIZE) + 1
print(f"Total rows: {total_rows:,}")

# First, clear existing data
print(f"Clearing existing data in {TABLE_NAME}...")
try:
    supabase.table(TABLE_NAME).delete().neq('id', 0).execute()
    print("Cleared existing data.")
except Exception as e:
    print(f"Note: {e}")

# Process in chunks
print(f"\nUploading {total_rows:,} rows in chunks of {CHUNK_SIZE}...")
uploaded = 0
errors = 0

for chunk in tqdm(pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE, low_memory=False),
                  total=total_chunks, desc="Uploading"):
    # Clean columns
    chunk = clean_columns(chunk)

    # Replace NaN/inf
    chunk = chunk.replace([np.inf, -np.inf], np.nan)
    chunk = chunk.where(pd.notnull(chunk), None)

    # Convert to records and clean
    records = [clean_record(r) for r in chunk.to_dict('records')]

    # Upload
    try:
        upload_chunk(records, TABLE_NAME)
        uploaded += len(records)
    except Exception as e:
        errors += 1
        if errors > 5:
            print(f"\nToo many errors. Last error: {e}")
            break
        print(f"\nError: {e}, retrying...")
        continue

print(f"\nDone! Uploaded {uploaded:,} records to {TABLE_NAME}")
