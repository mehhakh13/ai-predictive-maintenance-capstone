# Explainability Panel — SHAP Feature

Answers the question **"why did the model predict high UPM risk for this building this month?"** using SHAP (SHapley Additive exPlanations) applied to a per-subsystem XGBoost classifier trained on University 1 (Canada) data.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Dataset Choice](#3-dataset-choice)
4. [Data Pipeline — `prepare_shap_data.py`](#4-data-pipeline)
5. [Feature Engineering](#5-feature-engineering)
6. [Label Leakage Avoidance](#6-label-leakage-avoidance)
7. [Model Training — `train_shap_model.py`](#7-model-training)
8. [Backend API](#8-backend-api)
9. [Frontend Components](#9-frontend-components)
10. [API Reference](#10-api-reference)
11. [Running the Full Pipeline](#11-running-the-full-pipeline)
12. [Project File Map](#12-project-file-map)

---

## 1. Overview

The Explainability Panel is a standalone page in the PredicX dashboard. A user selects a building, a year, and a month. The panel then shows every subsystem in that building for that month with:

- **Risk probability** — the XGBoost model's predicted probability of an Unplanned Maintenance (UPM) event
- **Natural-language explanation** — a generated sentence such as *"At high risk mainly due to 3 failures in the past 3 months and aging building (47 years old)"*
- **Work order details** — actual descriptions of UPM/PPM work orders that occurred that month, plus a collapsible list of the top historically recurring defects for the subsystem
- **SHAP chart** — a horizontal bar chart showing each feature's contribution to pushing the risk above or below the baseline, collapsible for users who want the technical detail

Risk tiers used throughout:

| Tier   | Probability |
|--------|-------------|
| High   | ≥ 65 %      |
| Medium | 40 – 64 %   |
| Low    | < 40 %      |

---

## 2. Architecture

```
Raw FMUCD CSV
     │
     ▼
scripts/prepare_shap_data.py
     │  • filters to University 1 + FCI not-null
     │  • aggregates to building × subsystem × month
     │  • engineers 44 features + lag features
     │  • collects WO descriptions (this-month + historical)
     │
     ├─► data/shap/prepared_data.parquet   (54,269 rows × 56 cols)
     ├─► models/shap_feature_columns.json  (44 feature names)
     └─► data/shap/buildings_meta.json     (building list + available months)
          │
          ▼
scripts/train_shap_model.py
     │  • time-based 80/20 split (no future leakage)
     │  • trains XGBoost binary classifier (Test AUC = 0.9431)
     │  • runs shap.TreeExplainer over all 54,269 rows offline
     │
     ├─► models/shap_model.pkl
     ├─► models/shap_expected_value.json   (base value = -0.009)
     └─► data/shap/shap_values.parquet     (54,269 rows — risk_prob + shap_* + val_* cols)
          │
          ▼
backend/main.py  (FastAPI)
     │  GET /api/shap/buildings   → building list for the UI dropdown
     │  GET /api/shap/explain     → subsystems + risk + SHAP contributors + WO descriptions
          │
          ▼
frontend/src/pages/Explainability.jsx
     │  • building search + year/month selectors
     │  • stats bar (total / high / medium / low / avg risk)
     │  • risk filter pills
     └─► SubsystemCard × N
              ├─ risk badge + % + natural-language sentence
              ├─ DefectRecords  (this month's WOs + historical defects)
              └─ ShapChart      (collapsible horizontal bar chart)
```

---

## 3. Dataset Choice

The FMUCD dataset covers multiple universities. Only **University 1 (Canada)** was used for this feature because it is the only institution with near-complete data across all three required feature families:

| Feature family   | University 1 completeness |
|------------------|--------------------------|
| FCI              | 95.6 %                   |
| Weather          | 100 %                    |
| TotalCost        | 100 %                    |
| Date range       | 2012 – 2020 (8 years)    |

A further filter removes rows where FCI is null, leaving 132,000+ raw work-order rows that aggregate to **54,269 building × subsystem × month records**.

**`WOPriority` is intentionally excluded** — cross-tab analysis showed it is 99%+ correlated with PPM/UPM labels (priority 1/2/4 = UPM, priority 3/5 = PPM), making it label leakage rather than a predictive signal.

---

## 4. Data Pipeline

**Script:** `scripts/prepare_shap_data.py`

### Steps

1. **Load & filter** — reads the raw FMUCD CSV, keeps `UniversityID == 1` and rows with non-null FCI.

2. **Preprocess** — parses `WOStartDate`, extracts `year` / `month`, creates `is_upm` flag, coerces numeric columns.

3. **Aggregate WO descriptions** — before aggregating to monthly level, collects per-row `WODescription` into four lookup tables:
   - `upm_descriptions` — up to 5 unique UPM descriptions for this building × subsystem × month
   - `ppm_descriptions` — up to 5 unique PPM descriptions for this building × subsystem × month
   - `hist_upm_descriptions` — top 5 most frequent UPM descriptions for this building × subsystem across all time
   - `hist_ppm_descriptions` — top 5 most frequent PPM descriptions for this building × subsystem across all time

   Descriptions are stored as `|||`-separated strings (safe because no description contains `|||`).

4. **Aggregate to monthly** — groups by `BuildingID × SubsystemDescription × year × month`, computing work-order counts, durations, costs, weather averages, and building attributes.

5. **Feature engineering** — adds temporal features, derived features, lag features, and one-hot subsystem dummies (see §5).

6. **Merge descriptions** — left-joins the four description tables back into the main dataframe; null values become empty strings.

7. **Null imputation** — missing values in numeric features filled with their column median.

8. **Outputs:**
   - `data/shap/prepared_data.parquet` — 54,269 rows × 56 columns
   - `models/shap_feature_columns.json` — ordered list of the 44 model input features
   - `data/shap/buildings_meta.json` — list of buildings with their available year/month combinations (used by the frontend dropdown)

---

## 5. Feature Engineering

The model uses 44 features split across five groups.

### Temporal (3)
| Feature     | Description                                      |
|-------------|--------------------------------------------------|
| `month_sin` | `sin(2π × month / 12)` — cyclical month encoding |
| `month_cos` | `cos(2π × month / 12)` — cyclical month encoding |
| `season`    | 0=Winter, 1=Spring, 2=Summer, 3=Fall             |

### Weather (7)
| Feature         | Description                          |
|-----------------|--------------------------------------|
| `min_temp`      | Monthly minimum temperature (°C)     |
| `max_temp`      | Monthly maximum temperature (°C)     |
| `avg_temp`      | Derived: `(min + max) / 2`           |
| `temp_range`    | Derived: `max − min`                 |
| `humidity`      | Average humidity (%)                 |
| `precipitation` | Total precipitation (mm)             |
| `snow`          | Total snowfall (mm)                  |
| `cloudness`     | Average cloud cover (%)              |

### Building attributes (3)
| Feature        | Description                                         |
|----------------|-----------------------------------------------------|
| `fci`          | Facility Condition Index (0 = perfect, 1 = failing) |
| `building_age` | `year − built_year`                                 |
| `size`         | Building footprint (sqm)                            |

### Maintenance history / lag features (4)
| Feature           | Description                                                                    |
|-------------------|--------------------------------------------------------------------------------|
| `upm_last_1m`     | UPM count in the previous 1 month (shifted, no leakage)                       |
| `upm_last_3m`     | UPM count in the previous 3 months                                             |
| `upm_last_6m`     | UPM count in the previous 6 months                                             |
| `months_since_upm`| Months elapsed since the last UPM event (24 if never) — computed **before** logging the current row to prevent leakage |

### Work-order cost / effort (5)
| Feature              | Description                   |
|----------------------|-------------------------------|
| `avg_labor_hours`    | Average labour hours per WO   |
| `avg_wo_duration`    | Average WO duration (days)    |
| `wo_count`           | Number of work orders         |
| `avg_total_cost`     | Average WO cost ($)           |
| `total_monthly_cost` | Sum of all WO costs that month |

### Subsystem identity — one-hot (22)
Top-20 subsystems by frequency are one-hot encoded with the `subsystem_` prefix. Subsystems outside the top 20 map to `subsystem_Other`. These encode what *type* of system is being assessed.

---

## 6. Label Leakage Avoidance

Two sources of leakage were identified and fixed during development:

### `months_since_upm` off-by-one
The naive approach updated `last_idx` before appending the result, so a row where a UPM *just occurred* always received `months_since_upm = 0` (perfectly correlated with the label). The fix computes the result first, *then* updates `last_idx`:

```python
def months_since_last(series):
    result = []
    last_idx = None
    for idx, val in enumerate(series.values):
        result.append(idx - last_idx if last_idx is not None else 24)  # result first
        if val > 0:
            last_idx = idx                                               # then update
    return pd.Series(result, index=series.index)
```

Before fix: Test AUC = **1.0000** (leak). After fix: Test AUC = **0.9431** (legitimate).

### `WOPriority`
Cross-tab analysis showed priority values map almost deterministically to UPM/PPM labels. It was never included in the feature set.

### Time-based split
Training uses chronological order — the earliest 80% of months for training, the latest 20% for testing — so the model never sees future data during training.

---

## 7. Model Training

**Script:** `scripts/train_shap_model.py`

### XGBoost hyperparameters

```python
xgb.XGBClassifier(
    objective='binary:logistic',
    max_depth=6,
    learning_rate=0.05,
    n_estimators=300,
    scale_pos_weight=n_neg / n_pos,   # handles ~36% UPM class imbalance
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='auc',
)
```

### Results

| Split | Date range            | Rows   | AUC    |
|-------|-----------------------|--------|--------|
| Train | 2012-12 → 2018-08     | 43,415 | 0.9628 |
| Test  | 2018-09 → 2020-01     | 10,854 | 0.9431 |

### SHAP computation

After training, `shap.TreeExplainer` computes SHAP values for all 54,269 rows offline. This takes ~60 seconds and produces:

- One `shap_<feature>` column per feature (raw log-odds contribution)
- One `val_<feature>` column per feature (the actual feature value used)
- `risk_prob` — model's probability output
- `shap_base` — the global expected value (−0.009 in log-odds space, ≈ 50 % in probability space after transformation)

Everything is saved to `data/shap/shap_values.parquet` so the API serves pre-computed values with zero inference latency.

---

## 8. Backend API

**File:** `backend/main.py`

SHAP data is loaded into memory on startup:

```
✓ SHAP values loaded: 54,269 rows
✓ SHAP buildings meta loaded: N buildings
✓ SHAP feature columns loaded: 44 features
```

### `GET /api/shap/buildings`

Returns the building list. Each entry includes the list of `(year, month)` pairs available in the data, used to populate the frontend dropdowns.

### `GET /api/shap/explain`

Query params: `building_id`, `year`, `month`

Filters the in-memory parquet to the requested slice, assembles contributors via `_build_contributors()`, and returns every subsystem for that building × month. Subsystem one-hot features where the value is 0 ("not this subsystem type") are skipped from the contributor list to reduce noise. `month_sin` and `month_cos` SHAP values are summed into a single "Seasonal Pattern" entry.

`|||`-separated description strings are split into arrays before returning.

Response shape:

```json
{
  "building_id": "A050",
  "building_name": "6414 Coburg Rd",
  "year": 2019,
  "month": 1,
  "subsystems": [
    {
      "subsystem": "Controls and Instrumentation",
      "risk_prob": 0.7812,
      "shap_base": -0.009,
      "contributors": [
        {
          "feature": "upm_last_3m",
          "label": "UPM Last 3 Months",
          "shap_value": 0.4123,
          "feature_value": 3.0,
          "display_value": "3.0 events",
          "direction": "increases"
        }
      ],
      "this_month_upm": ["6414 COBURG RD - INVESTIGATE SOUND - HEATING SYSTEM"],
      "this_month_ppm": [],
      "hist_upm": [
        "6414 COBURG RD RM 212 - NO HEAT",
        "6414 COBURG RD - NO HEAT FROM FURNACE",
        "6414 COBURG RD - NEST THERMOSTAT ERROR"
      ],
      "hist_ppm": []
    }
  ]
}
```

---

## 9. Frontend Components

### `frontend/src/pages/Explainability.jsx`

Two-panel layout: 300 px left sidebar (controls) + flex-1 right panel (results).

- Fetches buildings from `/api/shap/buildings` on mount via `useExplainabilityData` hook
- Building list is searchable (client-side filter on `building_name`)
- Year and month dropdowns are populated from `building.available_months` — only valid combinations appear
- **Stats bar**: total subsystems, high/medium/low counts, average risk %
- **Risk filter pills**: All / High risk / Medium risk / Low risk (client-side filter, no re-fetch)
- Subsystems sorted by risk probability descending

### `frontend/src/hooks/useExplainabilityData.js`

Manages two independent pieces of async state:

- `buildings` / `loadingBuildings` / `buildingsError` — fetched once on mount
- `explanation` / `loadingExplanation` / `explanationError` — fetched on demand via `fetchExplanation(buildingId, year, month)`

### `frontend/src/components/Explainability/SubsystemCard.jsx`

One card per subsystem. Always visible:

- **Risk badge** (colour-coded) + subsystem name + risk %
- **Natural-language explanation** — generated client-side from SHAP contributors via `generateExplanation()` + `describeContributor()`. No LLM involved; rule-based mapping of feature × value × direction → human phrase (e.g. `upm_last_3m = 4, shap > 0` → `"4 failures in the past 3 months"`).
- **DefectRecords** section (see below)

Collapsible (click "Show feature breakdown"):

- Baseline → model output annotation
- **ShapChart** — horizontal Recharts bar chart, red = increases risk, green = reduces

### `frontend/src/components/Explainability/DefectRecords.jsx`

Shows actual work-order descriptions from the data. Two sections:

1. **This month's work orders** (always expanded) — UPM chips (red Wrench icon) and PPM chips (green ClipboardCheck icon). Skipped entirely if neither this-month list has content.

2. **Common historical defects** (collapsible, toggle with "▼") — two-column grid, UPM | PPM, showing the top recurring defect descriptions across all time for this building × subsystem.

The entire component renders nothing if there are no descriptions at all.

### `frontend/src/components/Explainability/ShapChart.jsx`

Horizontal `BarChart` from Recharts. Features:

- Dynamic height: `max(180, contributors.length × 30 + 40)` px
- Symmetric x-axis domain padded to ±115 % of the maximum absolute SHAP value
- `ReferenceLine x={0}` divides positive (risk-increasing, red) from negative (risk-reducing, green)
- Custom tooltip showing feature label, raw value, SHAP impact, and direction

---

## 10. API Reference

### Buildings endpoint

```
GET /api/shap/buildings

Response: Array of building objects
[
  {
    "building_id": "A050",
    "building_name": "6414 Coburg Rd",
    "available_months": [
      { "year": 2013, "month": 1 },
      { "year": 2013, "month": 2 },
      ...
    ]
  },
  ...
]
```

### Explain endpoint

```
GET /api/shap/explain?building_id={id}&year={yyyy}&month={m}

200: explanation object (see §8)
404: no data for this building/year/month combination
503: SHAP data not loaded (pipeline hasn't been run)
```

---

## 11. Running the Full Pipeline

> Requires the `shap_env` conda environment (Python 3.11, XGBoost, SHAP, pandas, FastAPI).

### One-time setup

```bash
conda create -n shap_env python=3.11 -y
conda activate shap_env
pip install xgboost shap fastapi uvicorn[standard] pandas pyarrow scikit-learn joblib
```

### Step 1 — Prepare data

```bash
conda activate shap_env
cd /path/to/ai-predictive-maintenance-capstone
python scripts/prepare_shap_data.py
```

Outputs:
- `data/shap/prepared_data.parquet`
- `models/shap_feature_columns.json`
- `data/shap/buildings_meta.json`

### Step 2 — Train model and compute SHAP values

```bash
python scripts/train_shap_model.py
```

Expected output:
```
Train AUC: 0.9628  |  Test AUC: 0.9431
✓ Meets target (> 0.70)
Saved → models/shap_model.pkl
Saved → data/shap/shap_values.parquet (54,269 rows)
```

### Step 3 — Start backend

Run from the **project root** (not from inside `backend/`):

```bash
conda activate shap_env
uvicorn backend.main:app --port 8000
```

You should see:
```
✓ SHAP values loaded: 54,269 rows
✓ SHAP buildings meta loaded: N buildings
✓ SHAP feature columns loaded: 44 features
```

### Step 4 — Start frontend

```bash
cd frontend
npm install   # first time only
npm run dev
```

Open `http://localhost:5173`, navigate to **Explainability Panel** in the sidebar.

---

## 12. Project File Map

```
ai-predictive-maintenance-capstone/
│
├── scripts/
│   ├── prepare_shap_data.py       # Step 1: aggregate raw CSV → parquet + metadata
│   └── train_shap_model.py        # Step 2: train XGBoost + compute SHAP offline
│
├── models/
│   ├── shap_model.pkl             # Trained XGBoost classifier
│   ├── shap_feature_columns.json  # Ordered list of 44 feature names
│   └── shap_expected_value.json   # SHAP base value (expected_value = -0.009)
│
├── data/shap/
│   ├── prepared_data.parquet      # 54,269 rows × 56 cols (features + metadata)
│   ├── shap_values.parquet        # 54,269 rows (risk_prob + shap_* + val_* + descriptions)
│   └── buildings_meta.json        # Building list with available year/month combinations
│
├── backend/
│   └── main.py                    # FastAPI — /api/shap/buildings + /api/shap/explain
│
└── frontend/src/
    ├── pages/
    │   └── Explainability.jsx     # Main page — layout, filters, stats bar
    ├── hooks/
    │   └── useExplainabilityData.js  # Async state for buildings + explanation fetches
    └── components/Explainability/
        ├── SubsystemCard.jsx      # Card per subsystem: badge + NL explanation + records + chart
        ├── DefectRecords.jsx      # This-month WOs + historical recurring defects
        └── ShapChart.jsx          # Horizontal Recharts bar chart for SHAP contributors
```
