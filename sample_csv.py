"""
One-time script to create a small sample of the premium universities CSV
for frontend consumption. Run once, then forget.

Usage: python sample_csv.py
"""

import pandas as pd
from pathlib import Path

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent
SOURCE_CSV = BASE_DIR / "data" / "USA_Premium_Universities_Cleaned.csv"
OUTPUT_CSV = BASE_DIR / "frontend" / "public" / "cost_data_sample.csv"

# ---- Config ----
SAMPLE_SIZE = 10000  # rows
RANDOM_SEED = 42     # reproducibility

def main():
    print(f"Reading source CSV: {SOURCE_CSV}")
    print("(This may take 30-60 seconds for a 271 MB file...)")

    # Read the full CSV
    df = pd.read_csv(SOURCE_CSV, low_memory=False)
    print(f"  Loaded {len(df):,} total rows with {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")

    # Take a random sample
    if len(df) <= SAMPLE_SIZE:
        sample = df
        print(f"  Dataset smaller than sample size, using all rows")
    else:
        sample = df.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED)
        print(f"  Sampled {SAMPLE_SIZE:,} random rows")

    # Make sure the output folder exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Write the sample
    sample.to_csv(OUTPUT_CSV, index=False)
    size_mb = OUTPUT_CSV.stat().st_size / (1024 * 1024)
    print(f"Saved sample: {OUTPUT_CSV}")
    print(f"  Output size: {size_mb:.2f} MB")
    print("Done!")

if __name__ == "__main__":
    main()
