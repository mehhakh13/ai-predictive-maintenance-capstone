import pandas as pd

# Load data
df = pd.read_csv('FMUCD.csv', low_memory=False)
df_filtered = df[df['UniversityID'].isin([10, 11, 12])]

print('After university filter:', len(df_filtered))
print('\nNull counts in key columns:')
print(f"  SubsystemDescription nulls: {df_filtered['SubsystemDescription'].isna().sum()} ({df_filtered['SubsystemDescription'].isna().mean()*100:.1f}%)")
print(f"  BuildingName nulls: {df_filtered['BuildingName'].isna().sum()} ({df_filtered['BuildingName'].isna().mean()*100:.1f}%)")
print(f"  WOStartDate nulls (before parsing): {df_filtered['WOStartDate'].isna().sum()} ({df_filtered['WOStartDate'].isna().mean()*100:.1f}%)")

# Parse dates
df_filtered['WOStartDate'] = pd.to_datetime(df_filtered['WOStartDate'], errors='coerce')
print(f"\nAfter date parsing:")
print(f"  WOStartDate nulls: {df_filtered['WOStartDate'].isna().sum()} ({df_filtered['WOStartDate'].isna().mean()*100:.1f}%)")

# Drop null dates
df_no_nulldates = df_filtered.dropna(subset=['WOStartDate'])
print(f"\nAfter dropping null dates: {len(df_no_nulldates)} rows ({len(df_no_nulldates)/len(df_filtered)*100:.1f}%)")

# Check remaining nulls
print(f"\nRemaining nulls after date drop:")
print(f"  SubsystemDescription: {df_no_nulldates['SubsystemDescription'].isna().sum()} ({df_no_nulldates['SubsystemDescription'].isna().mean()*100:.1f}%)")
print(f"  BuildingName: {df_no_nulldates['BuildingName'].isna().sum()} ({df_no_nulldates['BuildingName'].isna().mean()*100:.1f}%)")

# Drop null subsystems and building names
df_complete = df_no_nulldates.dropna(subset=['SubsystemDescription', 'BuildingName'])
print(f"\nAfter dropping null SubsystemDescription and BuildingName: {len(df_complete)} rows ({len(df_complete)/len(df_filtered)*100:.1f}%)")

# Check PPM/UPM distribution
print(f"\nPPM/UPM distribution in complete data:")
print(df_complete['PPM/UPM'].value_counts())
