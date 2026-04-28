#!/usr/bin/env python3
"""
Rebuilds df_with_topics_IMPROVED.parquet from the raw FMUCD CSV.

Uses keyword matching against topic_info_IMPROVED.csv topic representations
to assign topic_id to each work order — no need to re-train BERTopic.
"""

import pandas as pd
import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FMUCD_CSV   = PROJECT_ROOT / "data" / "Facility Management Unified Classification Database (FMUCD).csv"
TOPIC_INFO  = PROJECT_ROOT / "data" / "bertopic" / "topic_info_IMPROVED.csv"
OUTPUT      = PROJECT_ROOT / "data" / "bertopic" / "df_with_topics_IMPROVED.parquet"

# --------------------------------------------------------------------------
# 1. Load topic keywords
# --------------------------------------------------------------------------
print("Loading topic info...")
topic_info = pd.read_csv(TOPIC_INFO)

# Build ordered list: [(topic_id, [kw1, kw2, ...]), ...]
# Skip topic -1 (catch-all); we assign it when nothing else matches.
topics_kw = []
for _, row in topic_info.iterrows():
    tid = int(row["Topic"])
    if tid == -1:
        continue
    try:
        kws = ast.literal_eval(row["Representation"])
    except Exception:
        kws = [k.strip() for k in str(row["Representation"]).split(",")]
    # Keep only non-empty, lowercase keywords; prioritise multi-word ones first
    kws = sorted([k.lower().strip() for k in kws if k.strip()], key=lambda x: -len(x))
    topics_kw.append((tid, kws))

print(f"  Loaded {len(topics_kw)} topics")

# --------------------------------------------------------------------------
# 2. Build a fast lookup: for each keyword, which topic_id does it map to?
#    First topic (by Topic ID ascending) that contains the keyword wins.
# --------------------------------------------------------------------------
topics_kw.sort(key=lambda x: x[0])   # sort by topic_id ascending

kw_to_topic = {}
for tid, kws in topics_kw:
    for kw in kws:
        if kw not in kw_to_topic:
            kw_to_topic[kw] = tid

# Sort by keyword length descending so longer phrases match first
sorted_kws = sorted(kw_to_topic.keys(), key=lambda x: -len(x))

def assign_topic(desc: str) -> int:
    if not isinstance(desc, str) or not desc.strip():
        return -1
    desc_lower = desc.lower()
    for kw in sorted_kws:
        if kw in desc_lower:
            return kw_to_topic[kw]
    return -1

# --------------------------------------------------------------------------
# 3. Load FMUCD CSV — only the columns the backend needs
# --------------------------------------------------------------------------
UNIVERSITIES = [10, 11, 12]   # match original filtered dataset

print("Loading FMUCD CSV (this may take ~30s for 3.7M rows)...")
USECOLS = [
    "UniversityID", "BuildingID", "BuildingName",
    "SystemDescription", "SubsystemDescription",
    "WOID", "WODescription", "WOPriority",
    "WOStartDate", "WOEndDate", "WODuration",
    "PPM/UPM", "TotalCost", "LaborCost", "MaterialCost",
]
df = pd.read_csv(FMUCD_CSV, usecols=USECOLS, low_memory=False)
df = df[df["UniversityID"].isin(UNIVERSITIES)].copy()
print(f"  Loaded {len(df):,} rows (universities {UNIVERSITIES})")

# Rename WOID -> WOId to match what the backend expects
df = df.rename(columns={"WOID": "WOId"})

# --------------------------------------------------------------------------
# 4. Assign topic_id via keyword matching
# --------------------------------------------------------------------------
print("Assigning topic IDs via keyword matching...")
df["topic_id"] = df["WODescription"].map(assign_topic)
print(f"  topic_id distribution (top 10):\n{df['topic_id'].value_counts().head(10).to_string()}")

# --------------------------------------------------------------------------
# 5. Save
# --------------------------------------------------------------------------
print(f"Saving to {OUTPUT} ...")
df.to_parquet(OUTPUT, index=False)
print(f"Done — {len(df):,} rows saved to {OUTPUT}")
print("\nNext step: run scripts/generate_defect_aggregates.py to build the aggregated parquets.")
