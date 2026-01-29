import pandas as pd
import numpy as np


# Load dataset
df = pd.read_csv("/Users/mehakxoxo/Documents/spring_2026/data_practicum/Facility Management Unified Classification Database (FMUCD)/Facility Management Unified Classification Database (FMUCD).csv")   # change name if different

# Basic info
print(df.shape)
print(df.head())
print(df.info())


# Check missing values
missing = df.isnull().sum().sort_values(ascending=False)
print(missing)

# Drop columns with too many nulls (example: >50%)
threshold = 0.5 * len(df)
df = df.dropna(thresh=threshold, axis=1)

# Fill numeric missing values with median
num_cols = df.select_dtypes(include=['float64','int64']).columns
df[num_cols] = df[num_cols].fillna(df[num_cols].median())

# Fill categorical missing values with mode
cat_cols = df.select_dtypes(include=['object']).columns
df[cat_cols] = df[cat_cols].fillna(df[cat_cols].mode().iloc[0])



# Convert dates
df['WOStartDate'] = pd.to_datetime(df['WOStartDate'])
df['WOEndDate'] = pd.to_datetime(df['WOEndDate'])

# Create new features
df['BuildingAge'] = 2025 - df['BuiltYear']
df['Month'] = df['WOStartDate'].dt.month
df['Year'] = df['WOStartDate'].dt.year
df['Season'] = df['Month'] % 12 // 3 + 1


# Convert target to binary
df['Target_UPM'] = df['PPM/UPM'].map({'PPM': 0, 'UPM': 1})


from scipy import stats

z_scores = np.abs(stats.zscore(df[['LaborCost','TotalCost','LaborHours']]))
df = df[(z_scores < 3).all(axis=1)]


df.to_csv("FMUCD_CLEANED.csv", index=False)
print("Clean dataset saved as FMUCD_CLEANED.csv")
