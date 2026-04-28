#!/usr/bin/env python3
"""
NDA-safe preprocessing pipeline.
Reads the raw FMUCD CSV exactly ONCE and writes three anonymized, aggregated
Parquet files to ./derived/. These derived files contain ZERO raw work-order
text, real building names, or any other original dataset field — only
statistical aggregates keyed by anonymized building IDs.

Run:
    python3 preprocess.py           # produce derived/
    python3 preprocess.py --show-columns  # print CSV column names then exit
"""

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ─── Column name mappings (update if CSV header changes) ────────────────────
COL_BUILDING_ID   = "BuildingID"
COL_BUILDING_NAME = "BuildingName"       # never sent anywhere
COL_UNIVERSITY    = "UniversityID"
COL_SYSTEM        = "SystemDescription"
COL_SUBSYSTEM     = "SubsystemDescription"
COL_WO_DESC       = "WODescription"      # never sent anywhere — used for local theme matching only
COL_WO_PRIORITY   = "WOPriority"
COL_WO_START      = "WOStartDate"
COL_PPM_UPM       = "PPM/UPM"
COL_LABOR_COST    = "LaborCost"
COL_MATERIAL_COST = "MaterialCost"
COL_OTHER_COST    = "OtherCost"
COL_TOTAL_COST    = "TotalCost"

CSV_PATH = Path(__file__).parent / "data" / "Facility Management Unified Classification Database (FMUCD).csv"
DERIVED  = Path(__file__).parent / "derived"

# ─── Defect theme keyword matching ──────────────────────────────────────────
# Maps keywords in WODescription → a safe theme label.
# Raw WO text NEVER leaves this function; only the label is stored.
KEYWORD_THEMES = [
    (["light", "lamp", "bulb", "luminaire", "lighting"],       "Lighting Failure"),
    (["hvac", "heat", "cool", "air", "ventilat", "duct",
      "thermostat", "boiler", "chiller", "refriger"],           "HVAC / Climate Control"),
    (["plumb", "pipe", "leak", "water", "drain", "toilet",
      "flush", "faucet", "sink", "fountain", "sump"],           "Plumbing / Water Systems"),
    (["electric", "outlet", "circuit", "breaker", "power",
      "wiring", "panel", "voltage", "generator"],               "Electrical Systems"),
    (["door", "lock", "access", "card", "entry", "key"],       "Access Control / Doors"),
    (["roof", "ceiling", "tile", "wall", "floor", "paint",
      "crack", "patch", "drywall", "sheetrock"],                "Structural / Finishes"),
    (["fire", "alarm", "sprinkler", "smoke", "suppression"],   "Fire Safety"),
    (["elevator", "lift", "escalator"],                        "Vertical Transport"),
    (["pest", "mold", "odor", "smell", "insect", "rodent"],    "Environmental / Pest"),
    (["pump", "motor", "compressor", "valve", "steam"],        "Mechanical Equipment"),
    (["filter", "inspection", "preventive", "annual",
      "monthly", "weekly", "routine", "check"],                 "Planned Maintenance"),
    (["window", "glass", "blind", "shade"],                    "Windows / Glazing"),
    (["furniture", "desk", "chair", "carpet", "floor"],        "Interior Furnishings"),
]
DEFAULT_THEME = "General Maintenance"


def assign_theme(desc: str) -> str:
    if not isinstance(desc, str):
        return DEFAULT_THEME
    desc_lower = desc.lower()
    for keywords, label in KEYWORD_THEMES:
        if any(kw in desc_lower for kw in keywords):
            return label
    return DEFAULT_THEME


def anonymize(building_id) -> str:
    """SHA-256 hash of building ID → BLD_XXXXXXXX (first 8 hex chars)."""
    if pd.isna(building_id) or str(building_id).strip() == "":
        return "BLD_UNKNOWN"
    h = hashlib.sha256(str(building_id).strip().encode()).hexdigest()[:8].upper()
    return f"BLD_{h}"


def load_csv() -> pd.DataFrame:
    print(f"Reading CSV: {CSV_PATH}")
    df = pd.read_csv(
        CSV_PATH,
        usecols=[
            COL_BUILDING_ID, COL_UNIVERSITY, COL_SYSTEM, COL_SUBSYSTEM,
            COL_WO_DESC, COL_WO_PRIORITY, COL_WO_START,
            COL_PPM_UPM, COL_TOTAL_COST, COL_LABOR_COST,
            COL_MATERIAL_COST, COL_OTHER_COST,
        ],
        low_memory=False,
    )
    print(f"  Loaded {len(df):,} rows")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[COL_TOTAL_COST] = pd.to_numeric(df[COL_TOTAL_COST], errors="coerce").fillna(0.0)
    df[COL_WO_START]   = pd.to_datetime(df[COL_WO_START], errors="coerce")

    # Drop rows missing critical fields
    before = len(df)
    df = df.dropna(subset=[COL_WO_START, COL_SUBSYSTEM])
    print(f"  Dropped {before - len(df):,} rows with missing date or subsystem")

    df["year"]  = df[COL_WO_START].dt.year.astype(int)
    df["month"] = df[COL_WO_START].dt.month.astype(int)

    # Anonymize building ID — raw BuildingID/BuildingName never leave this script
    df["anon_id"] = df[COL_BUILDING_ID].apply(anonymize)
    df["is_upm"]  = (df[COL_PPM_UPM].str.upper() == "UPM").astype(int)
    df["is_ppm"]  = (df[COL_PPM_UPM].str.upper() == "PPM").astype(int)

    # Assign defect theme (uses WO text locally; theme label stored, text discarded)
    df["theme"] = df[COL_WO_DESC].apply(assign_theme)

    return df


def build_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    risk_scores.parquet — building × subsystem × month rolling UPM rate.
    Fields: anon_id, subsystem, system, year, month,
            upm_count, ppm_count, total_wo, upm_rate, risk_tier
    """
    g = (
        df.groupby(["anon_id", COL_SUBSYSTEM, COL_SYSTEM, "year", "month"])
        .agg(
            upm_count=("is_upm", "sum"),
            ppm_count=("is_ppm", "sum"),
            total_wo=("is_upm", "count"),
        )
        .reset_index()
        .rename(columns={COL_SUBSYSTEM: "subsystem", COL_SYSTEM: "system"})
    )
    g["upm_rate"] = (g["upm_count"] / g["total_wo"].clip(lower=1)).round(4)

    def tier(r):
        if r < 0.34:
            return "low"
        elif r < 0.67:
            return "moderate"
        return "high"

    g["risk_tier"] = g["upm_rate"].apply(tier)
    return g


def build_cost_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    cost_summary.parquet — planned vs. unplanned cost by building × subsystem × month.
    Fields: anon_id, subsystem, system, year, month,
            planned_cost, unplanned_cost, total_cost, upm_cost_pct
    """
    df2 = df.copy()
    df2["ppm_cost"] = df2[COL_TOTAL_COST] * df2["is_ppm"]
    df2["upm_cost"] = df2[COL_TOTAL_COST] * df2["is_upm"]

    g = (
        df2.groupby(["anon_id", COL_SUBSYSTEM, COL_SYSTEM, "year", "month"])
        .agg(
            planned_cost=("ppm_cost", "sum"),
            unplanned_cost=("upm_cost", "sum"),
            total_cost=(COL_TOTAL_COST, "sum"),
        )
        .reset_index()
        .rename(columns={COL_SUBSYSTEM: "subsystem", COL_SYSTEM: "system"})
    )
    g["upm_cost_pct"] = (
        g["unplanned_cost"] / g["total_cost"].clip(lower=1e-6)
    ).clip(0, 1).round(4)
    return g


def build_defect_themes(df: pd.DataFrame) -> pd.DataFrame:
    """
    defect_themes.parquet — theme frequency and avg cost per subsystem.
    Fields: subsystem, system, theme, count, avg_cost
    NOTE: raw WODescription is NOT stored here — only the pre-mapped theme label.
    """
    g = (
        df.groupby([COL_SUBSYSTEM, COL_SYSTEM, "theme"])
        .agg(
            count=(COL_TOTAL_COST, "count"),
            avg_cost=(COL_TOTAL_COST, "mean"),
        )
        .reset_index()
        .rename(columns={COL_SUBSYSTEM: "subsystem", COL_SYSTEM: "system"})
    )
    g["avg_cost"] = g["avg_cost"].round(2)
    return g.sort_values("count", ascending=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-columns", action="store_true",
                        help="Print CSV column names then exit")
    args = parser.parse_args()

    if args.show_columns:
        row = pd.read_csv(CSV_PATH, nrows=0)
        print("CSV columns:")
        for c in row.columns:
            print(f"  {c!r}")
        return

    if not CSV_PATH.exists():
        sys.exit(f"ERROR: CSV not found at {CSV_PATH}")

    DERIVED.mkdir(exist_ok=True)

    df_raw   = load_csv()
    df_clean = clean(df_raw)
    del df_raw   # free ~1 GB

    print("Building risk_scores …")
    risk = build_risk_scores(df_clean)
    risk.to_parquet(DERIVED / "risk_scores.parquet", index=False)
    print(f"  Written {len(risk):,} rows → derived/risk_scores.parquet")

    print("Building cost_summary …")
    cost = build_cost_summary(df_clean)
    cost.to_parquet(DERIVED / "cost_summary.parquet", index=False)
    print(f"  Written {len(cost):,} rows → derived/cost_summary.parquet")

    print("Building defect_themes …")
    themes = build_defect_themes(df_clean)
    themes.to_parquet(DERIVED / "defect_themes.parquet", index=False)
    print(f"  Written {len(themes):,} rows → derived/defect_themes.parquet")

    print("\nDone. Verify no raw text leaked:")
    for name, frame in [("risk", risk), ("cost", cost), ("themes", themes)]:
        print(f"  {name} columns: {list(frame.columns)}")


if __name__ == "__main__":
    main()
