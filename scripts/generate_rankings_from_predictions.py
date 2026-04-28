"""
Generate defect analytics ranking CSVs from predictions_with_metadata.parquet.
Mirrors the new-branch strategy: derive everything from the predictions parquet
so all universities and their building names are preserved.

Outputs:
  data/defect_analytics/global_rankings.csv
  data/defect_analytics/university_rankings.csv
  data/defect_analytics/building_rankings.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr

DATA_DIR = Path(__file__).parent.parent / "data"
SOURCE_PATH = DATA_DIR / "processed" / "predictions_with_metadata.parquet"
OUTPUT_DIR = DATA_DIR / "defect_analytics"
OUTPUT_DIR.mkdir(exist_ok=True)

WEATHER_MAP = {
    "min_temp":    "MinTemp",
    "max_temp":    "MaxTemp",
    "avg_humidity":"Humidity",
    "precipitation":"Precipitation",
}

COST_PER_EVENT = 500  # $500 per UPM event (same estimate as new branch)


def load_data():
    df = pd.read_parquet(SOURCE_PATH)
    # Only keep rows that have at least one UPM event OR are useful for correlation
    # (keep all rows for weather correlation; filter for counts)
    df["YearMonth"] = pd.to_datetime(df["month_date"]).dt.to_period("M")
    df["estimated_cost"] = df["UPM_total_event"] * COST_PER_EVENT
    print(f"Loaded {len(df):,} rows | unis: {sorted(df['UniversityID'].unique())} | "
          f"buildings: {df['BuildingName'].nunique()} | subsystems: {df['SubsystemDescription'].nunique()}")
    return df


def normalize(s: pd.Series) -> pd.Series:
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(0.0, index=s.index)
    return (s - mn) / (mx - mn)


def recurrence(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    agg = df.groupby(group_cols).agg(
        total_count=("UPM_total_event", "sum"),
        first_occurrence=("YearMonth", "min"),
        last_occurrence=("YearMonth", "max"),
    ).reset_index()

    agg["first_ts"] = agg["first_occurrence"].apply(lambda x: x.to_timestamp())
    agg["last_ts"]  = agg["last_occurrence"].apply(lambda x: x.to_timestamp())
    agg["months_observed"] = (
        (agg["last_ts"] - agg["first_ts"]) / pd.Timedelta(days=30.44) + 1
    ).clip(lower=1)
    agg["frequency_per_month"] = agg["total_count"] / agg["months_observed"]
    agg = agg.sort_values("total_count", ascending=False)
    agg["recurrence_rank"] = range(1, len(agg) + 1)
    return agg


def severity(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    agg = df.groupby(group_cols).agg(
        total_cost=("estimated_cost", "sum"),
        avg_cost=("estimated_cost", "mean"),
        avg_duration=("WODuration", "mean"),
        avg_priority=("WOPriority", "mean"),
    ).reset_index().fillna(0)

    agg["severity_score"] = (
        normalize(agg["total_cost"]) * 0.5
        + normalize(agg["avg_duration"]) * 0.3
        + normalize(agg["avg_priority"]) * 0.2
    ) * 100

    agg = agg.sort_values("severity_score", ascending=False)
    agg["severity_rank"] = range(1, len(agg) + 1)
    return agg


def env_sensitivity(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    weather_cols = list(WEATHER_MAP.values())
    available = [c for c in weather_cols if c in df.columns]

    monthly = df.groupby(group_cols + ["YearMonth"]).agg(
        failure_count=("UPM_total_event", "sum"),
        **{c: (c, "mean") for c in available}
    ).reset_index()

    results = []
    for keys, grp in monthly.groupby(group_cols):
        if len(grp) < 3:
            continue
        row = dict(zip(group_cols, [keys] if len(group_cols) == 1 else keys))
        best_corr, best_factor, best_score = 0.0, "none", 0.0
        for col in available:
            valid = grp[["failure_count", col]].dropna()
            if len(valid) < 3:
                continue
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r, _ = pearsonr(valid["failure_count"], valid[col])
                if np.isfinite(r) and abs(r) > abs(best_corr):
                    best_corr, best_factor = r, col
            except Exception:
                pass
        row["strongest_weather_factor"] = best_factor
        row["strongest_correlation"] = round(best_corr, 4)
        row["sensitivity_score"] = round(abs(best_corr) * 100, 2)
        results.append(row)

    return pd.DataFrame(results)


def merge_rankings(rec: pd.DataFrame, sev: pd.DataFrame,
                   env: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    df = rec.merge(sev[group_cols + ["total_cost", "avg_cost", "avg_duration",
                                      "avg_priority", "severity_score", "severity_rank"]],
                   on=group_cols, how="left")
    df = df.merge(env[group_cols + ["env_sensitivity_rank", "sensitivity_score",
                                     "strongest_weather_factor", "strongest_correlation"]],
                  on=group_cols, how="left")
    return df


def add_env_rank(env_df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    env_df = env_df.sort_values("sensitivity_score", ascending=False).copy()
    env_df["env_sensitivity_rank"] = range(1, len(env_df) + 1)
    return env_df


def run_level(df: pd.DataFrame, group_cols: list, label: str, out_name: str):
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    rec = recurrence(df, group_cols)
    sev = severity(df, group_cols)
    env = add_env_rank(env_sensitivity(df, group_cols), group_cols)
    merged = merge_rankings(rec, sev, env, group_cols)
    out = OUTPUT_DIR / out_name
    merged.to_csv(out, index=False)
    print(f"✅ {out_name}: {len(merged)} rows, unis: "
          f"{sorted(merged['UniversityID'].unique().tolist()) if 'UniversityID' in merged.columns else 'global'}")
    return merged


def main():
    df = load_data()

    # Global
    rec_g = recurrence(df, ["SubsystemDescription"])
    sev_g = severity(df, ["SubsystemDescription"])
    env_g = add_env_rank(env_sensitivity(df, ["SubsystemDescription"]), ["SubsystemDescription"])
    global_merged = merge_rankings(rec_g, sev_g, env_g, ["SubsystemDescription"])
    global_merged.to_csv(OUTPUT_DIR / "global_rankings.csv", index=False)
    print(f"\n✅ global_rankings.csv: {len(global_merged)} subsystems")

    # University level
    run_level(df, ["UniversityID", "SubsystemDescription"],
              "UNIVERSITY LEVEL", "university_rankings.csv")

    # Building level — only rows that have a building name
    df_bldg = df[df["BuildingName"].notna() & (df["BuildingName"] != "")]
    print(f"\nBuilding-level source: {len(df_bldg):,} rows, "
          f"{df_bldg['BuildingName'].nunique()} buildings")
    run_level(df_bldg, ["UniversityID", "BuildingName", "SubsystemDescription"],
              "BUILDING LEVEL", "building_rankings.csv")

    print("\n✅ Done. All 3 ranking CSVs written to data/defect_analytics/")


if __name__ == "__main__":
    main()
