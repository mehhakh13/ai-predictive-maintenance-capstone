# 🎯 How to Make Backend Work Like Frontend (No Manual Data Generation)

You asked: *"What if we don't want to generate data manually by running pipeline every time?"*

## ✅ SOLUTION 1: Commit Dashboard Data to Git (ALREADY DONE!)

**Status:** ✅ **COMPLETE!**

I've already fixed this for you! Here's what I did:

### What Changed:
1. **Modified `.gitignore`** to allow `data/dashboard/` files
2. **Committed dashboard data** (only 4.7MB - small enough for git)
   - `building_level_heatmap.csv` (4.6MB)
   - `university_level_heatmap.csv` (44KB)
   - `metadata.json` (1.6KB)

### How It Works Now:

**For you:**
```bash
git push origin main
```

**For your teammates:**
```bash
git pull origin main
cd backend
python3 main.py  # ← JUST WORKS! No data generation needed!
```

**Exactly like frontend:**
- Frontend: `npm run dev` → just works
- Backend: `python3 main.py` → just works ✨

### When to Regenerate Data:

Only regenerate when you want to update the model/predictions:
```bash
./run_full_pipeline.sh
git add data/dashboard/
git commit -m "Update dashboard data with latest predictions"
git push
```

---

## 🔄 SOLUTION 2: Use Supabase (Alternative - For Large Datasets)

If dashboard data gets too big for git, use Supabase instead.

**I've created a script for you:** `backend/load_dashboard_to_supabase.py`

### Setup (One-time):

1. **Upload data to Supabase:**
   ```bash
   cd backend
   python3 load_dashboard_to_supabase.py
   ```

2. **Create Supabase tables:**
   ```sql
   -- Run in Supabase SQL Editor:

   CREATE TABLE heatmap_building (
     id SERIAL PRIMARY KEY,
     "UniversityID" INT,
     "BuildingID" TEXT,
     "BuildingName" TEXT,
     "SystemDescription" TEXT,
     "SubsystemDescription" TEXT,
     "MonthNum" INT,
     "Year" INT,
     "ml_risk" FLOAT,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE heatmap_university (
     id SERIAL PRIMARY KEY,
     "UniversityID" INT,
     "SystemDescription" TEXT,
     "MonthNum" INT,
     "ml_risk" FLOAT,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE heatmap_metadata (
     id SERIAL PRIMARY KEY,
     data JSONB,
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Modify `backend/main.py`** to fetch from Supabase:
   ```python
   # In backend/main.py, add at top:
   from supabase import create_client
   import os

   supabase = create_client(
       os.getenv("SUPABASE_URL"),
       os.getenv("SUPABASE_ANON_KEY")
   )

   # Replace file loading with:
   @app.get("/api/risk-heatmap/ml")
   async def get_ml_heatmap(university: int = None, building: str = None):
       query = supabase.table("heatmap_building").select("*")
       if university:
           query = query.eq("UniversityID", university)
       if building and building != "all":
           query = query.eq("BuildingID", building)
       result = query.execute()
       return result.data
   ```

### Pros:
- ✅ No data in git (keeps repo small)
- ✅ Everyone uses same data source
- ✅ Easy to update centrally

### Cons:
- ⚠️ Requires internet connection
- ⚠️ More setup required

---

## 📦 SOLUTION 3: One-Time Setup Script (Simplest Alternative)

Create a `setup.sh` script that downloads data on first run:

```bash
#!/bin/bash
# setup.sh

if [ ! -d "data/dashboard" ]; then
    echo "Downloading dashboard data..."
    # Option A: From Google Drive
    gdown https://drive.google.com/uc?id=YOUR_FILE_ID -O data.zip
    unzip data.zip -d data/

    # Option B: From GitHub Release
    curl -L https://github.com/USER/REPO/releases/download/v1.0/data.zip -o data.zip
    unzip data.zip -d data/
fi

echo "✓ Data ready!"
```

Teammates run once:
```bash
./setup.sh
```

---

## 🏆 RECOMMENDED SOLUTION:

**Use Solution 1** (already done!) because:
- ✅ Dashboard data is only 4.7MB (small)
- ✅ Works offline
- ✅ Zero setup for teammates
- ✅ Exactly like `npm run dev` - just works!

Only switch to Solution 2 (Supabase) if:
- Dashboard data grows beyond 50MB
- You need real-time data updates
- Multiple teams need different data views

---

## 🚀 CURRENT STATUS:

**You're all set!** Here's the workflow now:

### For You (Mehak):
```bash
# Make changes, commit
git add .
git commit -m "Update feature"
git push origin main
```

### For Teammates:
```bash
# Pull latest code + data
git pull origin main

# Start backend (data already there!)
cd backend
python3 main.py

# Start frontend
cd frontend
npm run dev
```

**No data generation needed!** 🎉

---

## 📝 Summary:

| Solution | Complexity | Speed | Offline | Status |
|----------|-----------|-------|---------|--------|
| **Git (Solution 1)** | ⭐ Easy | ⚡ Instant | ✅ Yes | ✅ **DONE** |
| Supabase (Solution 2) | ⭐⭐⭐ Medium | ⚡⚡ Fast | ❌ No | Script ready |
| Setup Script (Solution 3) | ⭐⭐ Simple | ⚡⚡ Fast | Depends | Not needed |

**Recommendation:** Keep using Solution 1. It's perfect for your use case!

---

## 🔧 Troubleshooting:

If teammates still don't see data after pulling:

```bash
# Verify data exists
ls -lh data/dashboard/

# If missing, try:
git pull origin main --force

# Or re-clone repo:
git clone https://github.com/mehhakh13/ai-predictive-maintenance-capstone.git
cd ai-predictive-maintenance-capstone
cd backend && python3 main.py
```

Done! Your backend now works exactly like frontend - no manual setup! 🎉
