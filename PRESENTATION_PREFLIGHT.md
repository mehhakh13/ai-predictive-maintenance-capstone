# Presentation Pre-Flight Checklist

## 🎯 Complete This 10 Minutes Before Your Presentation

---

## 1️⃣ Backend Setup

### Start Backend Server
```bash
cd /home/sradmin/ai-predictive-maintenance-capstone
source shap_env/bin/activate
cd backend
python3 main.py
```

### ✅ Verify Backend is Running
You should see:
```
✓ Using Claude API
✓ Model loaded
✓ Data loaded: 27 records
✓ Feature importance loaded
✓ Predictions data loaded: 269094 records
✓ Defect summary created: 60 categories
✓ Impact summary created
✓ Monthly defect data created
✓ Building defect data created
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**❌ If you see "Using Ollama" instead**: Check that `USE_OLLAMA=false` in `/backend/.env`

---

## 2️⃣ Frontend Setup

### Start Frontend (New Terminal)
```bash
cd /home/sradmin/ai-predictive-maintenance-capstone/frontend
npm run dev
```

### ✅ Verify Frontend is Running
You should see:
```
VITE v7.3.1  ready in XXX ms

➜  Local:   http://localhost:5174/
```

**✅ Open in browser**: http://localhost:5174/

---

## 3️⃣ Branch Selection

### Choose Your Branch

**For Defect Analytics + SHAP only (no chat):**
```bash
git checkout main
# Restart backend after switching
```

**For All Features including AI Chat:**
```bash
git checkout new
# Restart backend after switching
```

**Recommended**: Use `new` branch to show all capabilities

---

## 4️⃣ Test Each Feature (CRITICAL!)

### Test 1: Explainability Dashboard
- [ ] Navigate to "Explainability" page
- [ ] Building dropdown has options
- [ ] Select a building (e.g., "Building 1")
- [ ] Select year and month
- [ ] Subsystem cards appear
- [ ] Click a HIGH RISK card (red badge)
- [ ] SHAP chart appears with bars
- [ ] Work order history shows below

**📝 Note which building/date has good data for demo**

---

### Test 2: Defect Intelligence Dashboard
- [ ] Navigate to "Defect Intelligence" page
- [ ] Defect summary table loads
- [ ] Cost bar chart visible
- [ ] System heatmap shows colored cells
- [ ] Monthly trends chart displays
- [ ] Filters work (try selecting a university)

**📝 Note any interesting patterns to highlight**

---

### Test 3: AI Chat Assistant (if on `new` branch)
- [ ] Click chat button (bottom right or in nav)
- [ ] Chat modal opens
- [ ] Type: "What are the most expensive defects?"
- [ ] Response appears in 3-5 seconds (not 30-60s)
- [ ] Chart/data shows in response
- [ ] Suggestions appear
- [ ] Test a follow-up question

**❌ If taking 30+ seconds**: You're on Ollama, not Claude API
**❌ If getting errors**: Check backend console for error messages

---

## 5️⃣ Browser Setup

### Organize Tabs
1. **Tab 1**: Home page (http://localhost:5174/)
2. **Tab 2**: Explainability page
3. **Tab 3**: Defect Intelligence page
4. Keep chat closed until demo time

### Browser Settings
- [ ] Zoom at 100% (or 90% if projector/share screen)
- [ ] Full screen mode ready (F11)
- [ ] Close unnecessary tabs
- [ ] Disable notifications
- [ ] Ensure stable internet (for Claude API)

---

## 6️⃣ Screen Share / Projector Setup

### If Presenting Via Screen Share
- [ ] Close personal tabs/windows
- [ ] Mute notifications (Do Not Disturb mode)
- [ ] Test screen share in meeting platform
- [ ] Share ONLY the browser window, not full screen

### If Using Projector
- [ ] Test connection to projector
- [ ] Verify resolution is readable
- [ ] Have HDMI/adapter ready
- [ ] Backup plan: present on laptop if projector fails

---

## 7️⃣ Backup Plan

### If Claude API Fails
**Option 1**: Switch to Ollama (free but slower)
```bash
# In backend/.env
USE_OLLAMA=true
# Restart backend
```
Say: "Running local AI model for data privacy"

**Option 2**: Skip chat demo
Focus on SHAP and Defect Intelligence

### If Data Doesn't Load
Have architecture diagram ready to discuss
Talk through the pipeline instead

### If Internet Dies
- Explain the system architecture
- Show code structure
- Discuss ML methodology

---

## 8️⃣ Materials Ready

### Beside You During Presentation
- [ ] `PRESENTATION_CHEATSHEET.md` printed or on second screen
- [ ] Water/coffee
- [ ] Phone on silent
- [ ] Backup notes with key statistics

### Key Numbers to Remember
- **269,094** work orders analyzed
- **60** defect categories discovered by AI
- **3 universities** worth of data
- **SHAP** for explainability
- **BERTopic** for defect clustering
- **Claude Sonnet 4** for chat

---

## 9️⃣ Final Checks (2 Minutes Before)

- [ ] Backend running with no errors
- [ ] Frontend loaded successfully
- [ ] All three features tested
- [ ] Browser ready with tabs organized
- [ ] Cheatsheet accessible
- [ ] Deep breath taken 😊

---

## 🎬 Ready to Present!

### Opening Line
"Good [morning/afternoon], everyone. Today I'm excited to present PredicX - an AI-powered Predictive Maintenance Intelligence Platform..."

### If Asked to Introduce Yourself First
"I'm [Your Name], and for my capstone project, I've built an AI system that predicts building failures before they happen and explains why in plain English."

---

## 🆘 Emergency Contacts (Just in Case)

**If you need to restart everything quickly:**

```bash
# Kill all processes
pkill -f "python3 main.py"
pkill -f "vite"

# Restart backend
cd ~/ai-predictive-maintenance-capstone/backend
source ../shap_env/bin/activate
python3 main.py &

# Restart frontend
cd ~/ai-predictive-maintenance-capstone/frontend
npm run dev &

# Wait 10 seconds, then open http://localhost:5174/
```

---

## ✅ Checklist Complete!

**When all items are checked, you're ready to present with confidence.**

**Good luck! You've built something impressive - now show it off! 🚀**
