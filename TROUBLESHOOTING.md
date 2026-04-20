# Risk Heatmap Troubleshooting Guide

## Issue: "Frontend not showing anything / not calculating"

### Quick Fix Steps

1. **Restart the dev server:**
   ```bash
   # Kill any existing processes
   pkill -f "vite"

   # Start fresh
   cd /home/sradmin/ai-predictive-maintenance-capstone/ai-predictive-maintenance-capstone/frontend
   npm run dev
   ```

2. **Open browser console (F12)** and check for:
   - ✅ "Using mock data" message
   - ✅ "Mock building data: 600 rows" (or similar)
   - ✅ "Filtered data: X rows"
   - ✅ "ML Heatmap: X rows"
   - ❌ Any red errors

3. **Clear browser cache:**
   - Press `Ctrl + Shift + R` (hard refresh)
   - Or `Ctrl + F5`

4. **Navigate to the Risk Heatmap page:**
   - URL should be: `http://localhost:XXXX/risk-heatmap`
   - Make sure you're on the right page!

---

## What Should You See

### In Browser Console:
```
Using mock data - real CSV files are in data/dashboard/
Mock building data: 600 rows
Mock university data: 168 rows
Mock metadata: {universities: Array(2), buildings_by_university: {…}, building_names: {…}}
Sample building row: {UniversityID: 10, BuildingID: '0009', BuildingName: 'STUDENT UNION PARKING GARAGE', ...}
Filtered data: 600 rows
ML Heatmap: 600 rows
Sample ML row: {SystemDescription: 'Lighting and Branch Wiring', MonthNum: 1, ml_risk: 0.4234, ...}
```

### On Screen:
- **Top Bar:**
  - University dropdown (University 10, University 11)
  - Building dropdown (All Buildings, STUDENT UNION PARKING GARAGE, Engineering Hall, ...)
  - Search box (placeholder: "Search systems...")
  - Show/Hide Values button

- **KPI Row:**
  - Average Risk card
  - High Risk Systems card
  - Coverage card

- **Heatmap:**
  - Left column: Subsystem names (10-14 rows)
    - "Lighting and Branch Wiring"
    - "Terminal & Package Units"
    - "Heat Generation Systems"
    - etc.
  - Top row: Month names (Jan, Feb, Mar, ...)
  - Cells: Colored based on risk (green = low, red = high)

---

## Common Issues & Fixes

### Issue 1: Console shows "0 rows" or empty data

**Cause:** Data not being generated

**Fix:**
```bash
# Check if the hook file was updated correctly
grep "SubsystemDescription" /home/sradmin/ai-predictive-maintenance-capstone/ai-predictive-maintenance-capstone/frontend/src/hooks/useRiskHeatmapData.js

# Should see multiple matches
```

### Issue 2: Heatmap is blank/white

**Possible causes:**
1. **CSS not loading**
   - Check browser console for CSS errors
   - Try hard refresh (Ctrl+Shift+R)

2. **Data has 0 risk values**
   - Check console logs for "Sample ML row"
   - ml_risk should be > 0 for at least some rows

3. **Component error**
   - Check browser console for React errors

**Fix:**
```bash
# Verify Heatmap component exists
ls -la /home/sradmin/ai-predictive-maintenance-capstone/ai-predictive-maintenance-capstone/frontend/src/components/RiskHeatmap/Heatmap.jsx

# Should show the file exists
```

### Issue 3: "Cannot read property of undefined"

**Cause:** Data structure mismatch

**Check console for:**
```
Sample ML row: {
  SystemDescription: "...",  // ✅ Should exist
  MonthNum: 1,               // ✅ Should be 1-12
  ml_risk: 0.42,             // ✅ Should be 0-1
  ...
}
```

**If missing fields, check:**
```bash
cat /home/sradmin/ai-predictive-maintenance-capstone/ai-predictive-maintenance-capstone/frontend/src/hooks/useRiskHeatmapData.js | grep -A 5 "SystemDescription:"
```

### Issue 4: Dropdown shows "Building undefined"

**Cause:** building_names not in metadata

**Fix:** Check console for metadata object:
```javascript
// Should see:
building_names: {
  "0009": "STUDENT UNION PARKING GARAGE",
  "0099": "Engineering Hall",
  ...
}
```

### Issue 5: Port 5173 or 5174 already in use

**Fix:**
```bash
# Kill processes on the port
lsof -ti:5173 | xargs kill -9
lsof -ti:5174 | xargs kill -9

# Or just let Vite use a different port
npm run dev
# It will auto-select next available port
```

---

## Detailed Debugging Steps

### Step 1: Verify File Changes

```bash
cd /home/sradmin/ai-predictive-maintenance-capstone/ai-predictive-maintenance-capstone/frontend

# Check hook file was updated
grep "SubsystemDescription" src/hooks/useRiskHeatmapData.js | wc -l
# Should show 10+ matches

# Check page file was updated
grep "building_names" src/pages/RiskHeatmapPage.jsx | wc -l
# Should show 2+ matches
```

### Step 2: Check Mock Data Generation

Open browser console and run:
```javascript
// This should match what you see in console logs
// Universities: [10, 11]
// Buildings per university: 5 and 4
// Subsystems: 10-14 unique
// Months: 1-12
// Total rows: Universities × Buildings × Subsystems × Months
// = 2 unis × avg 4.5 buildings × 10 subsystems × 12 months = ~1,080 rows
```

### Step 3: Test Data Flow

1. Select **University 10** → Should see ~600 rows in console
2. Select **All Buildings** → Should show university-level data
3. Select **Specific Building** → Should show that building's data
4. Change university → Building dropdown should reset to "All Buildings"

### Step 4: Verify Heatmap Rendering

1. **Check if data reaches component:**
   - Open React DevTools
   - Find `<Heatmap>` component
   - Check props: `mlHeatmap` should have 100-600 items

2. **Check if grouping works:**
   - Console should NOT show errors about `groupBySystem`
   - Heatmap should show 10-14 subsystem rows

3. **Check colors:**
   - Cells with ml_risk > 0.7 → Red
   - Cells with ml_risk 0.5-0.7 → Orange
   - Cells with ml_risk 0.3-0.5 → Yellow
   - Cells with ml_risk 0.15-0.3 → Light green
   - Cells with ml_risk < 0.15 → Green

---

## Expected Console Output

```
Using mock data - real CSV files are in data/dashboard/
Mock building data: 600 rows
Mock university data: 168 rows
Mock metadata: {
  universities: [10, 11],
  buildings_by_university: {
    10: ['0009', '0099', '0106', '0113', '0132'],
    11: ['0001', '0002', '0003', '0004']
  },
  building_names: {
    '0009': 'STUDENT UNION PARKING GARAGE',
    ...
  }
}
Sample building row: {
  UniversityID: 10,
  BuildingID: '0009',
  BuildingName: 'STUDENT UNION PARKING GARAGE',
  SubsystemDescription: 'Lighting and Branch Wiring',
  MonthNum: 1,
  ml_risk: 0.4234,
  hist_asset_rate: 0.2117,
  hist_shock_rate: 0.1270,
  coverage: 187
}
Filtered data: 600 rows  # For University 10, All Buildings
ML Heatmap: 600 rows
Sample ML row: {
  SystemDescription: 'Lighting and Branch Wiring',
  MonthNum: 1,
  ml_risk: 0.4234,
  BuildingName: 'STUDENT UNION PARKING GARAGE',
  coverage: 187
}
```

---

## If Still Not Working

### 1. Check Git Status
```bash
cd /home/sradmin/ai-predictive-maintenance-capstone/ai-predictive-maintenance-capstone/frontend
git status
git diff src/hooks/useRiskHeatmapData.js
git diff src/pages/RiskHeatmapPage.jsx
```

### 2. Verify Node Modules
```bash
npm install  # Reinstall dependencies
npm run dev  # Try again
```

### 3. Check for Syntax Errors
```bash
npm run lint  # Check for linting errors
```

### 4. Test with Simple Data
Open browser console and paste:
```javascript
// Test if Heatmap component works with minimal data
const testData = [{
  SystemDescription: 'Test System',
  MonthNum: 1,
  ml_risk: 0.5
}];
console.log('Test data:', testData);
```

---

## Success Checklist

When everything is working, you should see:

- [ ] Dev server running on port 5173 or 5174
- [ ] No red errors in browser console
- [ ] Console shows "Mock building data: 600 rows"
- [ ] Console shows "Filtered data: X rows" where X > 0
- [ ] University dropdown has 2 options (10, 11)
- [ ] Building dropdown shows names (not just IDs)
- [ ] Heatmap shows 10-14 subsystem rows
- [ ] Heatmap cells are colored (not all white/gray)
- [ ] Hovering over cells shows tooltips
- [ ] Clicking cells opens a modal
- [ ] KPI cards show numbers
- [ ] Charts at bottom show data

---

## Get Help

If still stuck, send me:

1. **Screenshot** of the browser window
2. **Console output** (copy all text from console)
3. **Network tab** (check if any requests are failing)
4. **React DevTools** screenshot showing Heatmap component props

---

**Last Updated:** 2026-03-07
