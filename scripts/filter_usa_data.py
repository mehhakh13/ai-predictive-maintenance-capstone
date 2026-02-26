"""
Filter FMUCD.csv to only USA data with specified columns and save as parquet
"""
import pandas as pd
from pathlib import Path

# Define columns needed
COLUMNS_NEEDED = [
    # Required
    "UniversityID",
    "BuildingID",
    "SystemDescription",
    "WOStartDate",
    "PPM/UPM",
    "WODescription",

    # Building / asset context (recommended)
    "BuiltYear",
    "Size",
    "Type",
    "FCI (facility condition index)",
    "DMC (deferred maintenance cost)",
    "CRV (current replacement value)",

    # Work order signals
    "WOPriority",
    "WODuration",

    # Weather (for weather-adjusted risk)
    "MinTemp.(°C)",
    "MaxTemp.(°C)",
    "Humidity(%)",
    "Precipitation(mm)",
    "Snow(mm)",
]

# File paths
input_file = Path(__file__).parent.parent / "FMUCD.csv"
output_file = Path(__file__).parent.parent / "FMUCD_USA.parquet"

print(f"Reading data from: {input_file}")

# First, read just the header to check columns
df_sample = pd.read_csv(input_file, nrows=0)
print(f"Columns available: {list(df_sample.columns)}")

# Determine country column name
country_col = None
if 'Country' in df_sample.columns:
    country_col = 'Country'
elif 'country' in df_sample.columns:
    country_col = 'country'
else:
    print("Error: No 'Country' column found.")
    exit(1)

# Select only the needed columns that exist
available_columns = [col for col in COLUMNS_NEEDED if col in df_sample.columns]
missing_columns = [col for col in COLUMNS_NEEDED if col not in df_sample.columns]

if missing_columns:
    print(f"\nWarning: The following columns are not in the dataset:")
    for col in missing_columns:
        print(f"  - {col}")

print(f"\nSelecting {len(available_columns)} columns out of {len(COLUMNS_NEEDED)} needed")

# Add country column to the columns we need to read
cols_to_read = [country_col] + available_columns

# Read in chunks and filter for USA
print("\nProcessing data in chunks...")
chunk_size = 100000
usa_chunks = []

for i, chunk in enumerate(pd.read_csv(input_file, chunksize=chunk_size, usecols=cols_to_read, low_memory=False)):
    # Filter for USA
    usa_chunk = chunk[chunk[country_col] == 'USA'].copy()

    if len(usa_chunk) > 0:
        # Drop the country column
        usa_chunk = usa_chunk[available_columns]
        usa_chunks.append(usa_chunk)

    if (i + 1) % 10 == 0:
        print(f"  Processed {(i + 1) * chunk_size:,} rows, found {sum(len(c) for c in usa_chunks):,} USA rows")

# Combine all chunks
print("\nCombining chunks...")
df_final = pd.concat(usa_chunks, ignore_index=True)

print(f"Final shape: {df_final.shape}")

# Convert object columns with mixed types to string to avoid parquet errors
print("\nConverting mixed-type columns...")
object_cols = df_final.select_dtypes(include=['object']).columns
for col in object_cols:
    df_final[col] = df_final[col].astype(str)

# Save as parquet
print(f"\nSaving to: {output_file}")
df_final.to_parquet(output_file, index=False)

print(f"✓ Successfully saved USA data to {output_file.name}")
print(f"  Rows: {len(df_final):,}")
print(f"  Columns: {len(df_final.columns)}")
