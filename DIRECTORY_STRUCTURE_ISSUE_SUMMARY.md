# Directory Structure Issue - Summary

## What's the Problem?

Your teammate **preshi0024** is working in a **nested directory structure** on the `presh` branch:
```
ai-predictive-maintenance-capstone/
├── ai-predictive-maintenance-capstone/    ← WRONG (nested duplicate)
│   └── frontend/
│       └── src/
├── frontend/                               ← CORRECT
│   └── src/
└── backend/
```

## Why This Causes Issues:

1. **Different code locations**: When your teammate runs their server from the nested directory, they see different code than what's on main
2. **Outdated code**: The `presh` branch is actually **BEHIND** main - it's missing newer features
3. **Merge conflicts**: If merged as-is, it would overwrite your newer work

## What You Have (Main Branch - NEWER):

Your `frontend/src/pages/RiskHeatmapPage.jsx` includes:
- ✅ Year filter dropdown (CalendarDays icon)
- ✅ ForecastStrip component showing next high-risk month
- ✅ Updated KpiRow with `selectedYear` parameter
- ✅ Better KPI calculations for year-specific vs. forecast mode

## What Presh Branch Has (OLDER):

The `ai-predictive-maintenance-capstone/frontend/src/pages/RiskHeatmapPage.jsx`:
- ❌ No year filter
- ❌ No ForecastStrip component
- ❌ Basic KpiRow without year logic
- ❌ Missing recent improvements from commits after April 24

## The Fix:

### For Your Teammate (preshi0024):

Send them the file `FIX_FOR_PRESHI.md` which explains:
1. Pull latest from `main` branch
2. Delete the nested `ai-predictive-maintenance-capstone/` directory
3. Work directly in the root `frontend/` and `backend/` directories
4. Create new PRs from a fresh branch based on latest main

### For You:

Your setup is **already correct**! Just make sure:

1. **Always work from the root directory:**
   ```bash
   cd /home/sradmin/ai-predictive-maintenance-capstone
   ```

2. **Start frontend server:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Start backend server:**
   ```bash
   cd backend
   python main.py
   ```

4. **Before pulling from presh branch**, coordinate with your teammate to ensure they've:
   - Rebased their work on latest main
   - Fixed their directory structure
   - Tested their changes in the correct `frontend/` location

## Git Commands for You:

To see if presh branch has any unique work worth merging:
```bash
git log main..origin/presh --oneline
```

To see file differences:
```bash
git diff main origin/presh -- frontend/
```

## Communication with Teammate:

Message to send:
```
Hi! I found the issue - your code is in ai-predictive-maintenance-capstone/frontend/
but it should be in the root frontend/ directory. The main branch has newer features
that your branch doesn't have (year filter, forecast strip). Can you:

1. Pull latest from main
2. Delete the nested ai-predictive-maintenance-capstone/ folder
3. Work from the root frontend/ and backend/ directories
4. Rebase your work on top of main

I've created FIX_FOR_PRESHI.md with step-by-step instructions!
```

## Next Steps:

1. ✅ Your environment is clean and correct
2. ✅ You have the latest features on main
3. ⚠️ Communicate with preshi0024 about the directory structure issue
4. ⚠️ Wait for them to fix their branch before merging
5. ⚠️ Test together once they've rebased on main

---

**Status**: Your code is working correctly. The issue is with your teammate's branch structure, not your setup.
