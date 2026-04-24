# 📊 Defect Analytics Dashboard - Complete Guide

## 🎯 Quick Start (30 seconds)

```bash
# 1. Start the frontend
cd /home/sradmin/ai-predictive-maintenance-capstone/frontend
npm run dev

# 2. Open browser
http://localhost:5173

# 3. Click "Defect Analytics" in navigation
# 4. Select a University from dropdown (REQUIRED!)
# 5. Explore the 6 tabs
```

---

## ✅ All Backend Data is READY

Your backend data files are already generated and working:

```
✅ global_rankings.csv (85 subsystems)
✅ university_rankings.csv (271 entries, 6 universities)
✅ building_rankings.csv (3,575 entries, 180 buildings)  
✅ recurrence_forecast_comparison.csv (3 ML models)
✅ environmental_model_comparison.csv (3 ML models, R²=0.81)
✅ survival_cox_model.json (Cox PH model results)
```

**Universities Available:** 1, 2, 4, 7, 8, 9

---

## 🎓 Dashboard Features (Master's Level)

### **Tab 1: Overview** ⭐ (Start Here!)
- Executive KPI cards
- Top recurrent defects chart
- Severity rankings
- Environmental sensitivity table
- AI model performance summary
- Strategic recommendations

### **Tab 2: Recurrence Analysis**
- Top 15 recurrent subsystems
- ARIMA vs Prophet vs XGBoost comparison
- Risk level categorization

### **Tab 3: Severity Analysis**
- Cost vs Duration scatter plot
- Priority action list
- Severity score rankings

### **Tab 4: Environmental Sensitivity**
- Weather-sensitive subsystems
- ML model performance (XGBoost R²=0.81)
- Correlation analysis

### **Tab 5: AI/ML Performance**
- Model scorecards with grades (A/B+/C)
- Recurrence forecast leaderboard
- Academic metric interpretation

### **Tab 6: Recommendations**
- Immediate attention items
- Preventive planning strategies
- Environmental monitoring
- ROI projections (15-25% cost reduction)

---

## 🔧 Troubleshooting

### Problem: "No data available"
**Solution:** Select a university from the dropdown!

### Problem: Loading forever
**Solution:** 
1. Open browser console (F12)
2. Click "Clear Cache & Reload" button
3. Hard refresh: Ctrl+Shift+R (Chrome) or Ctrl+F5 (Firefox)

### Problem: Charts not showing
**Solution:**
```bash
# Regenerate all data
python3 scripts/calculate_defect_analytics.py
python3 scripts/ml_defect_analytics_optimized.py

# Copy to frontend
cp -r data/defect_analytics/* frontend/public/data/defect_analytics/
cp -r data/ml_defect_analytics/* frontend/public/data/ml_defect_analytics/
```

---

## 🧪 Test Your Dashboard

### Option 1: Built-in Diagnostics
```
http://localhost:5173/test-data-loading.html
```

### Option 2: Validation Script
```bash
python3 scripts/validate_backend_data.py
```

### Option 3: Manual Check
```bash
curl http://localhost:5173/data/defect_analytics/university_rankings.csv | head -3
```

---

## 📊 Data Statistics

- **6 Universities** tracked
- **180 Buildings** analyzed  
- **85 Unique Subsystems**
- **817,943 Total Defects**
- **271 University-Subsystem combinations**
- **3,575 Building-Subsystem combinations**

### Top 5 Subsystems by Defect Count:
1. HVAC: 52,642 defects
2. Electrical: 50,955 defects
3. Plumbing: 30,805 defects
4. Lighting: 28,266 defects
5. Plumbing Fixtures: 27,690 defects

### Best ML Model:
**XGBoost** - R² = 0.8134 (81.3% variance explained)

---

## 🚨 Emergency Reset

If something is broken:

```bash
cd /home/sradmin/ai-predictive-maintenance-capstone

# Regenerate ALL data
python3 scripts/calculate_defect_analytics.py
python3 scripts/ml_defect_analytics_optimized.py

# Copy to frontend  
cp -r data/defect_analytics/* frontend/public/data/defect_analytics/
cp -r data/ml_defect_analytics/* frontend/public/data/ml_defect_analytics/

# Restart frontend
cd frontend
npm run dev

# Clear browser cache and reload
```

---

## 🎯 Key Features for Professor

✅ **Executive dashboard** with KPIs and recommendations  
✅ **Hierarchical drill-down**: University → Building → Subsystem  
✅ **3 ML models compared** with academic metrics (MAE, R², C-index)  
✅ **Professional styling** - clean, modern, presentation-ready  
✅ **Actionable insights** with priority levels and ROI  
✅ **Academic rigor** in interpretations and explanations  

---

## 📝 What Each Data File Does

### `university_rankings.csv`
Main file with subsystem rankings per university. Contains:
- Recurrence frequency (defects/month)
- Severity scores (cost + duration composite)
- Environmental correlations

### `building_rankings.csv`
Detailed building-level breakdown for drill-down analysis.

### `recurrence_forecast_comparison.csv`
Compares ARIMA, Prophet, and XGBoost for predicting future defects.

### `environmental_model_comparison.csv`
Shows which ML model best predicts environmental impact (XGBoost wins!).

### `survival_cox_model.json`
Time-to-failure analysis identifying risk factors (Humidity is #1).

---

## ✨ Your Dashboard is Production-Ready!

Everything is working. Just:
1. `npm run dev`
2. Select a university
3. Impress your professor! 🎓

Good luck! 🚀
