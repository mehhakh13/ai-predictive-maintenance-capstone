#!/usr/bin/env python3
"""
Generate aggregated defect intelligence data for fast API responses
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
BERTOPIC_DATA = PROJECT_ROOT / "data" / "bertopic" / "df_with_topics_IMPROVED.parquet"
TOPIC_INFO = PROJECT_ROOT / "data" / "bertopic" / "topic_info_IMPROVED.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "defect_intelligence" / "aggregated"

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading BERTopic data...")
df = pd.read_parquet(BERTOPIC_DATA)
topic_info = pd.read_csv(TOPIC_INFO)

# Create topic to name mapping
topic_to_name = dict(zip(topic_info['Topic'], topic_info['Name']))

# Map defect categories
def create_defect_label(topic_name, topic_id):
    """Convert BERTopic topic name to human-readable defect label"""
    if topic_id == -1:
        return "Mixed/Administrative Tasks"

    keyword_mappings = {
        'light': 'Lighting System Failure',
        'cold': 'HVAC Temperature Control',
        'warm': 'HVAC Temperature Control',
        'heat': 'HVAC Temperature Control',
        'lock': 'Door Lock & Access',
        'outlet': 'Electrical Outlet Issue',
        'power': 'Power Outage',
        'fire alarm': 'Fire Alarm System',
        'alarm': 'Alarm System Malfunction',
        'toilet': 'Toilet System Failure',
        'flush': 'Toilet Flushing Issue',
        'window': 'Window & Glass Damage',
        'broken': 'Structural Damage',
        'drain': 'Drainage System Clog',
        'clogged': 'Drainage System Clog',
        'sink': 'Sink Plumbing Issue',
        'thermostat': 'Thermostat Malfunction',
    }

    parts = topic_name.split('_')
    if len(parts) > 1:
        for keyword in parts[1:]:
            if keyword in keyword_mappings:
                return keyword_mappings[keyword]

    if len(parts) > 1:
        return parts[1].replace('_', ' ').title() + " Issue"

    return f"Defect Type {topic_id}"

# Add defect category
df['defect_category'] = df['topic_id'].apply(
    lambda tid: create_defect_label(topic_to_name.get(tid, f'topic_{tid}'), tid)
)

# Add WOId if not present
if 'WOId' not in df.columns:
    df['WOId'] = [f'WO-{str(i+1).zfill(6)}' for i in range(len(df))]

# Generate synthetic costs
def calculate_defect_cost(row, topic_id):
    """Calculate synthetic cost based on defect type"""
    base_costs = {
        -1: 500, 0: 150, 1: 800, 2: 300, 3: 400, 4: 600, 5: 700,
        6: 350, 7: 250, 8: 300, 9: 1200, 10: 200, 11: 800, 12: 250,
        15: 400, 16: 350, 19: 800, 21: 2000, 33: 1500, 38: 1800,
        45: 1500, 46: 3000, 54: 2500, 57: 2200,
    }

    base_cost = base_costs.get(topic_id, 500)

    priority_multiplier = 1.0
    if pd.notna(row.get('WOPriority')):
        try:
            priority = float(row['WOPriority'])
            if priority >= 50:
                priority_multiplier = 1.5
            elif priority >= 40:
                priority_multiplier = 1.2
            elif priority <= 20:
                priority_multiplier = 0.8
        except:
            pass

    duration_multiplier = 1.0
    if pd.notna(row.get('WODuration')):
        try:
            duration = float(row['WODuration'])
            if duration > 100:
                duration_multiplier = 1.3
            elif duration > 50:
                duration_multiplier = 1.1
        except:
            pass

    final_cost = base_cost * priority_multiplier * duration_multiplier * np.random.uniform(0.8, 1.2)
    return round(final_cost, 2)

np.random.seed(42)
df['TotalCost'] = df.apply(lambda row: calculate_defect_cost(row, row['topic_id']), axis=1)

# Add university names
university_mapping = {10: 'University 10', 11: 'University 11', 12: 'University 12'}
df['university_name'] = df['UniversityID'].map(university_mapping).fillna('Unknown University')

# Convert WOStartDate to datetime
df['WOStartDate'] = pd.to_datetime(df['WOStartDate'], errors='coerce')
df['month'] = df['WOStartDate'].dt.to_period('M').astype(str)

print(f"Loaded {len(df)} defect records")

# ============================================================================
# 1. DEFECT SUMMARY - Aggregate by defect category
# ============================================================================
print("\nGenerating defect summary...")
defect_summary = df.groupby('defect_category').agg({
    'WOId': 'count',
    'TotalCost': ['sum', 'mean']
}).reset_index()

defect_summary.columns = ['defect_category', 'count', 'total_cost', 'avg_cost']
defect_summary['avg_impact'] = defect_summary['total_cost'] / defect_summary['count']
defect_summary = defect_summary.sort_values('count', ascending=False)

defect_summary.to_parquet(OUTPUT_DIR / "defect_summary.parquet", index=False)
print(f"✓ Saved defect_summary.parquet ({len(defect_summary)} categories)")

# ============================================================================
# 2. SYSTEM-DEFECT BREAKDOWN
# ============================================================================
print("\nGenerating system-defect breakdown...")
system_defect = df.groupby(['SystemDescription', 'defect_category']).agg({
    'WOId': 'count',
    'TotalCost': ['sum', 'mean']
}).reset_index()

system_defect.columns = ['system', 'defect_category', 'count', 'total_cost', 'avg_cost']
system_defect = system_defect.sort_values('count', ascending=False)

system_defect.to_parquet(OUTPUT_DIR / "system_defect.parquet", index=False)
print(f"✓ Saved system_defect.parquet ({len(system_defect)} combinations)")

# ============================================================================
# 3. BUILDING-DEFECT BREAKDOWN
# ============================================================================
print("\nGenerating building-defect breakdown...")
building_defect = df.groupby(['UniversityID', 'university_name', 'BuildingID', 'defect_category']).agg({
    'WOId': 'count',
    'TotalCost': ['sum', 'mean']
}).reset_index()

building_defect.columns = ['university_id', 'university_name', 'building_id', 'defect_category', 'count', 'total_cost', 'avg_cost']
building_defect['building_name'] = building_defect['building_id'].astype(str)
building_defect['total_impact'] = building_defect['total_cost'] * building_defect['count']
building_defect = building_defect.sort_values('total_impact', ascending=False)

building_defect.to_parquet(OUTPUT_DIR / "building_defect.parquet", index=False)
print(f"✓ Saved building_defect.parquet ({len(building_defect)} combinations)")

# ============================================================================
# 4. MONTHLY TRENDS
# ============================================================================
print("\nGenerating monthly trends...")
monthly_defect = df.groupby(['month', 'defect_category']).agg({
    'WOId': 'count',
    'TotalCost': ['sum', 'mean']
}).reset_index()

monthly_defect.columns = ['month', 'defect_category', 'count', 'total_cost', 'avg_cost']
monthly_defect = monthly_defect.sort_values(['month', 'count'], ascending=[True, False])

monthly_defect.to_parquet(OUTPUT_DIR / "monthly_defect.parquet", index=False)
print(f"✓ Saved monthly_defect.parquet ({len(monthly_defect)} records)")

# ============================================================================
# 5. IMPACT RANKING
# ============================================================================
print("\nGenerating impact ranking...")
impact_summary = defect_summary.copy()
impact_summary['total_impact'] = impact_summary['total_cost'] * impact_summary['count']

# Assign risk levels
impact_summary['risk_level'] = pd.cut(
    impact_summary['total_impact'],
    bins=[0, 50000, 100000, 200000, float('inf')],
    labels=['Low', 'Medium', 'High', 'Critical']
)

impact_summary = impact_summary.sort_values('total_impact', ascending=False)

impact_summary.to_parquet(OUTPUT_DIR / "impact_summary.parquet", index=False)
print(f"✓ Saved impact_summary.parquet ({len(impact_summary)} categories)")

print("\n" + "="*60)
print("✓ All aggregated data files generated successfully!")
print(f"Output directory: {OUTPUT_DIR}")
print("="*60)
