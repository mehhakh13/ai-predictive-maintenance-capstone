# ⚡ Quick Start Guide - Fixed Setup!

## ✅ PROBLEM SOLVED!

**Before:** Had to run `./run_full_pipeline.sh` every time (10 minutes)
**Now:** Just `git pull` and run! Data is included! ⚡

---

## 🚀 For You (Mehak):

```bash
# Push your changes + data
git push origin main
```

Done! Everyone on your team can now pull and run immediately.

---

## 👥 For Your Teammates (Including preshi0024):

### First Time Setup:

```bash
# 1. Clone or pull latest
git pull origin main

# 2. Install backend dependencies (one-time)
pip install -r requirements.txt

# 3. Install frontend dependencies (one-time)
cd frontend
npm install
cd ..
```

### Every Day Usage:

**Terminal 1 - Backend:**
```bash
cd backend
python3 main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**That's it!** No data generation needed! 🎉

---

## 📊 What's Included in Git Now:

✅ `data/dashboard/building_level_heatmap.csv` - 69,068 rows (4.6MB)
✅ `data/dashboard/university_level_heatmap.csv` - 552 rows (44KB)
✅ `data/dashboard/metadata.json` - Filter options (1.6KB)

**Total: 4.7MB** - Small enough for git!

---

## 🔄 When to Update Data:

Only when you want fresh predictions:

```bash
# Regenerate with latest model
./run_full_pipeline.sh

# Commit updated data
git add data/dashboard/
git commit -m "Update predictions with latest data"
git push
```

Your teammates will get the update on next `git pull`.

---

## ✅ What Works Now:

- ✅ Backend loads data instantly (no generation needed)
- ✅ Risk Heatmap page shows data immediately
- ✅ All filters work (university, building, year)
- ✅ Subsystem drill-down works
- ✅ Year filter + forecast strip (latest features!)

---

## 🎯 Summary:

**Like Frontend:**
```bash
cd frontend
npm run dev  # ← Just works!
```

**Backend Now:**
```bash
cd backend
python3 main.py  # ← Just works! (data included in git)
```

**No more manual data generation!** 🚀

---

## 📝 Next Steps for preshi0024:

1. **Fix directory structure** (see `FIX_FOR_PRESHI.md`)
2. **Pull latest main** (includes data + latest features)
3. **Run servers** (no data generation needed!)

---

## 🆘 Troubleshooting:

**Data not loading?**
```bash
# Verify data exists
ls -lh data/dashboard/

# Should show:
# 4.6M building_level_heatmap.csv
# 44K  university_level_heatmap.csv
# 1.6K metadata.json

# If missing:
git pull origin main --force
```

**Backend error?**
```bash
# Check dependencies
pip install -r requirements.txt

# Check if port 8000 is free
lsof -i :8000
```

**Frontend error?**
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📚 Additional Resources:

- **Full fix explanation:** `SOLUTION_SUMMARY.md`
- **For preshi0024:** `FIX_FOR_PRESHI.md`
- **Directory issue details:** `DIRECTORY_STRUCTURE_ISSUE_SUMMARY.md`
- **Complete troubleshooting:** `COMPLETE_FIX_GUIDE.md`

---

**Status: ✅ READY TO USE!**

Your backend now works exactly like frontend - no manual setup required! 🎊
