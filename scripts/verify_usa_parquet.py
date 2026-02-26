"""
Verify the USA parquet file
"""
import pandas as pd

# Read the parquet file
df = pd.read_parquet('FMUCD_USA.parquet')

print(f"Shape: {df.shape}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nData types:")
print(df.dtypes)
print(f"\nFirst few rows:")
print(df.head())
print(f"\nBasic statistics:")
print(df.describe())
