# Presentation Quick Reference Card

## 🎯 Core Message
**"PredicX uses explainable AI to predict failures, discover defect patterns, and answer questions in natural language."**

---

## 📊 Feature 1: SHAP Explainability (5-6 min)

### What to Show
1. Select building + year/month
2. Click HIGH-RISK subsystem card
3. Point to SHAP contributors (bars)
4. Scroll to work order history

### What to Say
- "SHAP explains WHY systems are risky"
- "Red bars INCREASE risk, blue bars DECREASE risk"
- "These are additive - they sum to the final prediction"
- "You can ACT on this - schedule preventive maintenance"

### Key Terms
- SHAP values (Shapley Additive Explanations)
- Interpretable ML
- Causal contribution

---

## 🔍 Feature 2: Defect Intelligence (4-5 min)

### What to Show
1. Defect summary (top categories)
2. Cost bar chart
3. System heatmap (hot spots)
4. Monthly trends (seasonality)

### What to Say
- "BERTopic discovered these patterns from 269K work orders"
- "No manual categorization - unsupervised learning"
- "Shows WHERE money goes and WHEN problems spike"
- "Enables data-driven budget planning"

### Key Terms
- BERTopic (neural language model)
- Unsupervised learning
- Pattern discovery

---

## 💬 Feature 3: AI Chat (4-5 min)

### What to Demo
**Query 1**: "What are the most expensive defects?"
- Shows natural language understanding
- Returns chart + numbers

**Query 2**: "Which buildings have the most HVAC issues?"
- Shows context memory
- Demonstrates filtering

**Query 3**: "Show me defect trends"
- Shows interpretation
- Provides insights

### What to Say
- "Claude Sonnet 4 with function calling"
- "Real-time queries, not pre-written answers"
- "Democratizes data access - no SQL needed"
- "Ask → Answer in 3 seconds"

### Key Terms
- Large Language Model (LLM)
- Function calling
- Conversational analytics

---

## 💡 Key Talking Points

### Opening Hook
"Traditional maintenance is reactive. This platform is proactive and intelligent."

### Technical Sophistication
- XGBoost ML model
- SHAP interpretability
- BERTopic clustering
- Claude API integration
- Full-stack production system

### Business Value
- ✅ Reduced downtime
- ✅ Optimized budgets
- ✅ Better planning
- ✅ Faster decisions

### Closing
"AI assists human expertise to keep buildings running smoothly."

---

## 🎬 Demo Checklist

### Before Starting
- [ ] Backend running (`python3 main.py`)
- [ ] Frontend running (port 5174)
- [ ] Chat modal tested
- [ ] Good building pre-selected for SHAP
- [ ] Browser tabs organized

### During Demo
- [ ] Speak to audience, not screen
- [ ] Pause after each feature
- [ ] Highlight the AI/ML
- [ ] Explain business impact

---

## ⚡ If Things Go Wrong

| Problem | What to Say |
|---------|-------------|
| API slow | "Hitting live Claude API in real-time..." |
| Chat unexpected | "Generative AI is probabilistic, let me rephrase..." |
| Data not loading | Switch to architecture discussion |

---

## 🔑 Anticipated Questions

**"What's your model accuracy?"**
→ "[X]% accuracy, but SHAP lets us validate predictions are sensible"

**"How scalable is this?"**
→ "FastAPI backend handles concurrency, BERTopic is pre-computed"

**"How does it integrate?"**
→ "RESTful API - works with any CMMS system"

**"What data do you need?"**
→ "Work orders with descriptions, dates, buildings, systems. More data = better predictions"

---

## 📐 Timing

| Section | Minutes |
|---------|---------|
| Opening | 0.5 |
| Explainability | 5.5 |
| Defect Intelligence | 4.5 |
| AI Chat | 4.5 |
| Closing | 1.0 |
| **TOTAL** | **16 min** |
| Q&A | 5-10 |

---

## 🎯 One-Liner for Each Feature

**Explainability**: "SHAP breaks open the black box - shows WHY systems fail"

**Defect Intelligence**: "BERTopic discovers hidden patterns in 269K work orders"

**AI Chat**: "Ask questions in English, get insights in seconds"

---

## 🚀 Enthusiasm Points

- 🔥 "This is cutting-edge ML interpretability"
- 🔥 "Unsupervised learning discovered these patterns automatically"
- 🔥 "This is the future of data access"
- 🔥 "Full-stack production-ready ML system"
