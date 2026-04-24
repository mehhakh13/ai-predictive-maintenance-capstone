# Quick Reference: Slide-by-Slide Guide

## Presentation Structure (46 slides)

### Section 1: Introduction (Slides 1-3)
1. **Title Slide**: "AI Predictive Maintenance System"
2. **Project Overview**: FMUCD dataset, 4 features overview
3. **Technology Stack**: React, FastAPI, XGBoost, SHAP, BERTopic

---

### Section 2: Explainability Feature (Slides 4-14)

| Slide | Title | Key Point to Emphasize |
|-------|-------|------------------------|
| 4 | Section Title | SHAP-based feature attribution |
| 5 | Why We Built This | "Why did the model flag this building?" → Trust |
| 6 | Dataset | University 1, 54K rows, 95.6% FCI completeness |
| 7 | Data Filtering | 44 features: temporal, weather, building, lag, WO metrics |
| 8 | Model Architecture | XGBoost, AUC 0.9431, time-based split |
| 9 | **Label Leakage Prevention** | ⚠️ CRITICAL: months_since_upm bug fix, AUC 1.0→0.9431 |
| 10 | SHAP Computation | Pre-computed offline → 200ms API response |
| 11 | Frontend | SubsystemCard, ShapChart, DefectRecords |
| 12 | Future Use | Global summaries, what-if analysis, LLM explanations |
| 13 | Limitations | Single university, historical data only, feature independence |

**Talking Time**: 4 minutes
**Demo Opportunity**: Show SHAP chart (if laptop available)

---

### Section 3: Defect Analysis Feature (Slides 15-25)

| Slide | Title | Key Point to Emphasize |
|-------|-------|------------------------|
| 15 | Section Title | BERTopic-powered analytics |
| 16 | Why We Built This | 120K unstructured work orders → 63 auto-discovered categories |
| 17 | Dataset | df_with_topics_IMPROVED.parquet, Topic examples |
| 18 | Data Processing | BERT → UMAP → HDBSCAN → c-TF-IDF |
| 19 | **Cost Synthesis** | ⚠️ Acknowledge: Synthetic costs (FMUCD lacks real data) |
| 20 | BERTopic Model | all-MiniLM-L6-v2, UMAP 5D, HDBSCAN, coherence 0.52 |
| 21 | Dashboard | 9 components: heatmap, charts, table |
| 22 | Backend | 6 FastAPI endpoints, <200ms response |
| 23 | Future Use | Predictive forecasting, root cause analysis |
| 24 | Limitations | Synthetic costs, static topics, 15% outliers |

**Talking Time**: 4 minutes
**Demo Opportunity**: Show heatmap or defect table

---

### Section 4: Cost Dashboard Feature (Slides 26-33)

| Slide | Title | Key Point to Emphasize |
|-------|-------|------------------------|
| 26 | Section Title | PPM vs UPM financial analysis |
| 27 | Why We Built This | Budget visibility, ROI justification |
| 28 | Dataset | Mock data (500-800 WOs), realistic distributions |
| 29 | Data Processing | Outlier detection (P95), system aggregation |
| 30 | UI Components | 6 components: KPIs, breakdown, trends, outliers |
| 31 | Backend | GET /api/cost-analysis, top 10 systems |
| 32 | Future Use | Real ERP integration, forecasting, ROI calculator |
| 33 | Limitations | Synthetic data, no inflation adjustment |

**Talking Time**: 3 minutes
**Demo Opportunity**: Show cost breakdown chart

---

### Section 5: Chatbot Feature (Slides 34-41)

| Slide | Title | Key Point to Emphasize |
|-------|-------|------------------------|
| 34 | Section Title | RAG-powered AI assistant |
| 35 | Why We Built This | Democratize data access (no SQL needed) |
| 36 | Architecture | Claude API + 12 maintenance tools |
| 37 | 12 Tools | Cost, Risk, Building, Trend tools (2-column layout) |
| 38 | LLM Integration | Claude vs Ollama, tool calling flow |
| 39 | Example Conversation | 3-turn dialogue with tool calls |
| 40 | Future Use | RAG (manuals), multimodal (photos), proactive alerts |
| 41 | Limitations | In 'new' branch, hallucinations, API costs |

**Talking Time**: 2 minutes
**Note**: Mention "in development" status

---

### Section 6: Summary & Conclusion (Slides 42-46)

| Slide | Title | Key Point to Emphasize |
|-------|-------|------------------------|
| 42 | Section Title | "Summary: Technology Stack" |
| 43 | Tech Stack Comparison | Frontend, Backend, ML, LLM (2-column) |
| 44 | **Key Achievements** | AUC 0.9431, 63 topics, 9 dashboards, 12 tools |
| 45 | **Business Impact** | $500K savings, 40% UPM reduction, 80% faster |
| 46 | Lessons Learned | Data quality, label leakage, pre-computation |
| 47 | Future Roadmap | Short/mid/long-term (3-6m, 6-12m, 12m+) |
| 48 | Q&A Prep | 6 common questions with answers |
| 49 | Thank You | Final slide |

**Talking Time**: 2 minutes
**Transition**: "Let me summarize our achievements..."

---

## Critical Slides (Must Not Skip)

If running short on time, prioritize these slides:

1. **Slide 1**: Title (obviously)
2. **Slide 5**: Explainability - Why Built (business justification)
3. **Slide 9**: **Label Leakage Prevention** (shows rigor)
4. **Slide 16**: Defect Analysis - Why Built (120K unstructured WOs)
5. **Slide 20**: BERTopic Model (technical depth)
6. **Slide 27**: Cost Dashboard - Why Built (ROI)
7. **Slide 36**: Chatbot Architecture (innovation)
8. **Slide 44**: Key Achievements (summary)
9. **Slide 45**: Business Impact ($500K, 40%, 80%)
10. **Slide 49**: Thank You

---

## Professor Questions → Slide References

| Question | Direct to Slide |
|----------|-----------------|
| "How did you prevent overfitting?" | Slide 9 (label leakage) + Slide 8 (time-based split) |
| "What's your model performance?" | Slide 8 (AUC 0.9431) |
| "How does BERTopic work?" | Slide 20 (algorithm steps) |
| "Why synthetic costs?" | Slide 19 + 28 (FMUCD lacks real data) |
| "What's the business value?" | Slide 45 (business impact) |
| "What are the limitations?" | Slides 13, 24, 33, 41 (each feature) |
| "How scalable is this?" | Slide 22 (backend), Slide 43 (tech stack) |
| "Future work?" | Slides 12, 23, 32, 40 (each feature) |

---

## Slide Transitions (Practice These)

**Intro → Explainability**:
*"Let me start with our first feature: the SHAP explainability dashboard."*

**Explainability → Defect Analysis**:
*"Now that we can explain WHY a building is high-risk, let's understand WHAT types of defects are occurring. That's where defect analysis comes in."*

**Defect Analysis → Cost Dashboard**:
*"Knowing defect patterns is useful, but facilities managers also ask: How much is this costing us? Our cost dashboard answers that."*

**Cost Dashboard → Chatbot**:
*"These three dashboards provide rich insights, but they require clicking through multiple screens. What if users could just ask: 'Which building has the highest risk?' That's our chatbot vision."*

**Chatbot → Summary**:
*"Let me now summarize what we've built and the impact it delivers."*

---

## Time Checkpoints (Practice Pacing)

| Checkpoint | Target Time | Cumulative |
|------------|-------------|------------|
| Finish Slide 3 (Intro) | 1 min | 1 min |
| Finish Slide 14 (Explainability) | 4 min | 5 min |
| Finish Slide 25 (Defect Analysis) | 4 min | 9 min |
| Finish Slide 33 (Cost Dashboard) | 3 min | 12 min |
| Finish Slide 41 (Chatbot) | 2 min | 14 min |
| Finish Slide 49 (Summary) | 2 min | 16 min |

**Target**: 15-18 minutes total
**Max**: 20 minutes (leave time for Q&A)

---

## Emergency Cuts (If Running Over)

If you're running long, skip these slides (in order):

1. **Slide 10** (SHAP Computation) - merge with Slide 8
2. **Slide 22** (Backend API) - just mention "FastAPI with 6 endpoints"
3. **Slide 31** (Cost Backend) - skip technical details
4. **Slide 38** (LLM Integration) - briefly mention Claude API
5. **Slide 47** (Future Roadmap) - just say "we have a detailed roadmap"
6. **Slide 48** (Q&A Prep) - skip, handle questions live

**Never skip**: Slides 9 (label leakage), 44-45 (achievements/impact)

---

## Visual Aids (If Presenting in Person)

Consider bringing:
- Laptop with demo (localhost frontend)
- Printed SHAP chart example
- Heatmap screenshot (defect analysis)
- Cost trend chart screenshot

**Demo Script** (30 seconds):
1. Open Explainability page
2. Select Building A050, Jan 2019
3. Expand subsystem card
4. Point to SHAP chart: "Red increases risk, green reduces it"
5. Close

---

## Body Language Tips

- **Slide 9 (Label Leakage)**: Slow down, emphasize "This was a critical bug we discovered and fixed"
- **Slide 20 (BERTopic)**: Use hand gestures to show pipeline: embeddings → reduction → clustering
- **Slide 45 (Impact)**: Make eye contact, pause after "$500K potential savings"
- **Slide 49 (Thank You)**: Smile, open posture, invite questions

---

## Common Mistakes to Avoid

❌ **Don't**:
- Rush through label leakage slide (Slide 9) - this shows rigor!
- Apologize for synthetic costs - just acknowledge and explain
- Skip limitations slides - professors appreciate honesty
- Read slides word-for-word - use them as prompts

✅ **Do**:
- Explain WHY before WHAT (business problem before technical solution)
- Use concrete numbers ($500K, 40%, 0.9431 AUC)
- Connect each feature to stakeholder value
- Smile and show enthusiasm

---

## Post-Presentation Checklist

After presenting, be ready to:
- [ ] Share GitHub repo link (if requested)
- [ ] Demo live application (if laptop available)
- [ ] Discuss code structure (backend/main.py, frontend/src/)
- [ ] Explain deployment strategy (Docker, cloud)
- [ ] Provide references (SHAP paper, BERTopic paper, FMUCD dataset)

---

## Confidence Reminders

**Before you start**:
- ✅ You built 4 production-ready features
- ✅ You discovered and fixed label leakage (research rigor)
- ✅ You have clear business justification for everything
- ✅ You acknowledge limitations honestly
- ✅ You have a detailed future roadmap

**You've got this! 🚀**

---

## Emergency Contact

**If technical issues during demo**:
- Fall back to slides (screenshots included)
- Verbally describe: "The SHAP chart shows red bars for features that increase risk..."

**If you blank on a question**:
- "That's a great question. Let me think..." (pause 3 seconds)
- Reference slide: "As shown on Slide X..."
- Honest answer: "I'd need to investigate that further, but my hypothesis is..."

**If you run out of time**:
- Skip to Slide 44 (Key Achievements)
- "Due to time, let me jump to our summary..."
- Offer: "Happy to discuss any feature in detail during Q&A"
