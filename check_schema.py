import pandas as pd

# Load the parquet file
df = pd.read_parquet('FMUCD_USA.parquet')

print("=" * 80)
print("FMUCD_USA.parquet Schema")
print("=" * 80)
print(f"\nTotal columns: {len(df.columns)}")
print(f"Columns: {list(df.columns)}")

print("\n" + "=" * 80)
print("Column Checks")
print("=" * 80)
print(f"Has SubsystemDescription: {'SubsystemDescription' in df.columns}")
print(f"Has BuildingName: {'BuildingName' in df.columns}")

# Filter to universities 10, 11, 12
df_filtered = df[df['UniversityID'].isin([10, 11, 12])]

print("\n" + "=" * 80)
print("Sample Data (Universities 10, 11, 12)")
print("=" * 80)

# Show sample of system-related columns
system_cols = ['UniversityID', 'BuildingID', 'SystemDescription']
if 'SubsystemDescription' in df.columns:
    system_cols.append('SubsystemDescription')
if 'BuildingName' in df.columns:
    system_cols.append('BuildingName')

print(df_filtered[system_cols].head(20))

print("\n" + "=" * 80)
print("Unique Counts (Universities 10, 11, 12)")
print("=" * 80)
for col in system_cols:
    print(f"{col}: {df_filtered[col].nunique()} unique values")

if 'SubsystemDescription' in df.columns:
    print("\n" + "=" * 80)
    print("Subsystem Examples (Top 20)")
    print("=" * 80)
    print(df_filtered['SubsystemDescription'].value_counts().head(20))
