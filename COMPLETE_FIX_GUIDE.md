# Complete Fix Guide - Data Loading Issue

## ROOT CAUSE IDENTIFIED:

You have **TWO separate issues**:

### Issue 1: Directory Structure Mismatch
- Your teammate works in: `ai-predictive-maintenance-capstone/frontend/`
- Correct location: `frontend/` (root level)
- **Status**: Explained in `DIRECTORY_STRUCTURE_ISSUE_SUMMARY.md`

### Issue 2: Missing Data Files (THIS IS WHY DATA WON'T LOAD!)
- The `data/` directory is in `.gitignore` (line 65)
- **Data files are NOT shared via git**
- Each person must **generate data locally** by running the pipeline
- Your teammate has generated data on their machine
- You DON'T have the generated data, so backend API returns empty!

## THE SOLUTION:

### Step 1: Generate the Dashboard Data

The backend needs these files to load data:
- `data/dashboard/building_level_heatmap.csv`
- `data/dashboard/university_level_heatmap.csv`
- `data/dashboard/metadata.json`

You already have some of these files, but you might need to regenerate them.

Run the full data pipeline:

```bash
cd /home/sradmin/ai-predictive-maintenance-capstone

# This will take a few minutes
./run_full_pipeline.sh
```

**What this does:**
1. Phase 1: Prepares data from FMUCD.csv
2. Phase 2: Engineers features
3. Phase 3: Trains ML model
4. Phase 4: Generates heatmap CSVs for dashboard

**Expected output files:**
```
✓ data/processed/monthly_asset_upm.parquet
✓ data/processed/asset_features.parquet
✓ data/processed/predictions_with_metadata.parquet
✓ models/asset_upm_predictor.pkl
✓ data/dashboard/building_level_heatmap.csv
✓ data/dashboard/university_level_heatmap.csv
✓ data/dashboard/metadata.json
```

### Step 2: Start the Backend Server

```bash
cd backend
python3 main.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test the API:
```bash
curl http://localhost:8000/api/risk-heatmap/ml?university=10
```

If you see JSON data, the backend is working!

### Step 3: Start the Frontend Server

In a new terminal:

```bash
cd frontend
npm install  # if you haven't already
npm run dev
```

You should see:
```
VITE v5.x.x ready in XXX ms
➜ Local: http://localhost:5173/
```

### Step 4: Verify Data Loads

1. Open browser to http://localhost:5173
2. Navigate to Risk Heatmap page
3. Data should now load properly!

## For Your Teammate (preshi0024):

They need to do **BOTH**:

### A. Fix Directory Structure

Send them `FIX_FOR_PRESHI.md` - they need to:
1. Pull latest from main
2. Delete nested `ai-predictive-maintenance-capstone/` directory
3. Work from root `frontend/` and `backend/`

### B. Generate Data Locally

They also need to run:
```bash
./run_full_pipeline.sh
```

Because `data/` is gitignored, everyone must generate data locally!

## Alternative: Share Data Files

If you want to avoid running the pipeline every time, you have options:

### Option 1: Commit Essential Data Files

Edit `.gitignore` to allow dashboard data:

```gitignore
# In .gitignore, change line 65:
data/
# To:
data/processed/
# (Keep the data/dashboard/ folder tracked)
```

Then commit:
```bash
git add -f data/dashboard/
git commit -m "Add generated dashboard data for team sharing"
git push
```

### Option 2: Use Shared Storage

- Upload data files to Google Drive / Dropbox
- Share link with team
- Each person downloads to their local `data/` folder

### Option 3: Use Supabase (You Already Have This!)

Looking at your scripts, you have `load_to_supabase.py` - you could:
1. Load data to Supabase database
2. Modify backend to fetch from Supabase instead of local files
3. Everyone uses same remote data source

## Quick Health Check:

Run these commands to verify your setup:

```bash
# Check Python works
python3 --version

# Check data files exist
ls -lh data/dashboard/

# Check backend dependencies
cd backend && python3 -c "from fastapi import FastAPI; print('OK')"

# Check frontend dependencies
cd frontend && npm list react

# Check FMUCD.csv exists (required for pipeline)
ls -lh FMUCD.csv
```

## Summary:

**For YOU (mehak):**
1. ✅ Your code structure is correct
2. ⚠️ Run `./run_full_pipeline.sh` to generate data
3. ✅ Start backend: `cd backend && python3 main.py`
4. ✅ Start frontend: `cd frontend && npm run dev`

**For preshi0024:**
1. ⚠️ Fix directory structure (use `FIX_FOR_PRESHI.md`)
2. ⚠️ Run `./run_full_pipeline.sh` to generate data
3. ✅ Start servers from correct directories

**Root Cause:**
- Directory mismatch + missing local data files (gitignored)

**Solution:**
- Fix directory structure + run data pipeline
