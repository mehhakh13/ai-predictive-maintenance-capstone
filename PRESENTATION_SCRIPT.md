# AI Predictive Maintenance Dashboard - Presentation Script

## Opening (30 seconds)

"Good [morning/afternoon], everyone. Today I'm excited to present **PredicX** - an AI-powered Predictive Maintenance Intelligence Platform that I've developed for my capstone project.

This system addresses a critical challenge in facilities management: **How do we predict which building systems will fail before they actually break down?** And more importantly, **how do we understand WHY certain systems are at risk?**

Traditional maintenance is reactive - you fix things when they break. This platform is **proactive and intelligent** - it predicts failures, explains the risk factors, identifies defect patterns, and even answers natural language questions about your maintenance data.

Let me walk you through three core features that make this possible."

---

## Feature 1: SHAP Explainability Dashboard (5-6 minutes)

### Introduction (30 seconds)

"Let's start with the **Explainability Dashboard** - and this is where the AI really shines.

Many predictive models are 'black boxes' - they tell you THAT something will fail, but not WHY. This dashboard uses **SHAP values** - Shapley Additive Explanations - a cutting-edge technique from interpretable machine learning to break open that black box."

### Demo Setup (Navigate to Explainability Page)

"So here we are on the Explainability page. Let me show you how this works..."

### Walkthrough - Building Selection (1 minute)

**[Select a building from dropdown]**

"I'm selecting **Building [X]** here. Each building is analyzed month-by-month because risk factors change over time - winter conditions are different from summer, recent maintenance history matters, and so on.

**[Select year and month]**

I'll select **[Year/Month]** to analyze..."

### Key Feature 1 - Subsystem Risk Cards (2 minutes)

**[Point to the subsystem cards displayed]**

"Now this is powerful. What you're seeing here are **all the critical subsystems** in this building - HVAC, electrical, plumbing, elevators, and so on.

Each card shows:
- The **subsystem name**
- A **risk probability** percentage - this is our ML model's prediction that this system will have an unplanned maintenance event this month
- A **risk badge** - High, Medium, or Low

**[Click on a high-risk subsystem card]**

Let me click on this **[subsystem name]** which shows **[X]% risk**. This is where it gets really interesting..."

### Key Feature 2 - SHAP Contributors (2 minutes)

**[Point to the SHAP contributors chart that appears]**

"This chart shows you **exactly what's driving that risk**. These are the SHAP values - they quantify how much each factor is pushing the risk UP or DOWN.

For example, you can see here:
- **[Point to top contributor]** - '[Feature name]' with a value of [X] is **increasing** the risk. This tells us that [explain what this means - e.g., 'the building age of 45 years is a significant risk factor']
- **[Point to negative contributor]** - But '[Feature name]' with a value of [X] is actually **decreasing** the risk. So [explain - e.g., 'recent preventive maintenance is helping protect this system']

The beauty of SHAP is that these values are **additive** - they literally add up to explain the final risk score. This isn't just correlation - this is **causal contribution**.

**[Point to feature values section if visible]**

And you can see the actual values - temperature, humidity, building age, recent work order history - all the real operational data that went into this prediction."

### Key Feature 3 - Work Order History (1 minute)

**[Scroll to work order section]**

"Below the SHAP analysis, you see **historical context**:
- **Previous UPM events** - Unplanned Maintenance that actually happened on this subsystem
- **Previous PPM events** - Planned Preventive Maintenance that was completed

This gives maintenance managers the full story: the prediction, the explanation, AND the historical pattern."

### Business Value Statement (30 seconds)

"Why does this matter? Because **you can act on it**.

If you see high risk driven by building age and recent UPM history, you know you need to schedule preventive maintenance NOW. If you see risk driven by extreme weather, you can prepare backup systems.

This turns AI from a mysterious oracle into a **decision support tool** that maintenance teams can actually trust and use."

---

## Feature 2: Defect Intelligence Dashboard (4-5 minutes)

### Introduction & Transition (30 seconds)

"Now let's shift from prediction to **pattern discovery**. The second feature is the **Defect Intelligence Dashboard**.

This uses **BERTopic** - a neural language model - to automatically discover what types of defects occur most often, where they happen, how much they cost, and how they trend over time.

No manual categorization - the AI learned these patterns from **269,000 work order descriptions**."

### Demo Setup (Navigate to Defect Intelligence Page)

**[Switch to Defect Intelligence page]**

"Here's what that looks like..."

### Key Feature 1 - Defect Summary (1 minute)

**[Point to top defect categories chart/table]**

"At the top, we have the **Defect Summary** - the most expensive and frequent defect categories discovered by the AI.

You can see:
- **[Point to #1 defect]** - '[Defect type]' is the top issue with **[X] occurrences** and **$[Y] in total costs**
- The AI grouped together similar work orders - things like 'light not working', 'bulb out', 'fixture broken' all got clustered into 'Lighting System Failure'

This is **unsupervised learning** - I didn't tell the model these categories exist. It discovered them from the language patterns in maintenance descriptions."

### Key Feature 2 - Cost Analysis (1 minute)

**[Point to cost bar chart]**

"This cost breakdown is crucial for **budget planning**.

You can immediately see where money is going - HVAC systems, electrical issues, plumbing failures - and prioritize accordingly.

**[Point to specific high-cost category]**

For example, '[Category]' is costing **$[X]** - that might warrant a capital improvement project rather than continuous repairs."

### Key Feature 3 - System Heatmap (1 minute)

**[Point to system heatmap]**

"The **System Heatmap** shows which building systems have which defect types.

**[Point to a hot spot]**

See this darker cell? That's telling us **[System X]** has a high concentration of **[Defect Y]**. This could indicate:
- A systemic issue with that system type across buildings
- Aging equipment that needs replacement
- A training issue for maintenance staff

This view helps you spot patterns that would be invisible in raw work order lists."

### Key Feature 4 - Monthly Trends (1 minute)

**[Point to monthly trends chart]**

"Time series analysis is critical. This chart shows **how defects trend month-over-month**.

**[Point to trends]**

- You can see seasonal patterns - HVAC issues spike in summer and winter
- You can spot anomalies - sudden spikes that might indicate a failing asset
- You can measure the impact of interventions - did that preventive maintenance program reduce failures?

This enables **data-driven maintenance scheduling** instead of guessing."

### Filters Demo (30 seconds)

**[Demo filters if time allows]**

"And of course, everything is filterable - by university, building, defect type, date range - so maintenance managers can drill down to exactly what they need to see."

---

## Feature 3: AI Chat Assistant (4-5 minutes)

### Introduction & Transition (30 seconds)

"Now, both of those dashboards are powerful, but they require you to click around and explore. What if you could just **ask questions in plain English**?

That's where the **AI Chat Assistant** comes in. This uses **Claude Sonnet 4** - one of the most advanced large language models available - with function calling to query your maintenance data conversationally."

### Demo Setup (Open Chat Modal)

**[Click chat button to open modal]**

"Let me open the chat assistant..."

### Technical Architecture (30 seconds)

"Quick technical note: This isn't just a chatbot reading static text. It's powered by:
- **Claude Sonnet 4 API** for natural language understanding
- **Function calling** - the AI can actually execute queries against the database
- **Session management** - it remembers conversation context
- **Real-time data** - every response is based on current data, not pre-written answers

Essentially, I've given the AI access to analytical tools, and it decides when and how to use them."

### Demo 1 - Simple Query (1 minute)

**[Type: "What are the most expensive defects?"]**

"Let me start simple: 'What are the most expensive defects?'

**[Wait for response]**

Notice a few things:
1. **It answered in natural language** - not just dumping data
2. **It's showing actual numbers** - total costs, categories
3. **It provided a chart** - the AI decided a visualization would help
4. **It gave suggestions** - 'Try asking...' to guide follow-up questions

This is **intelligent data exploration** - the AI understood my intent, queried the right data, and presented it clearly."

### Demo 2 - Complex/Follow-up Query (1.5 minutes)

**[Type a follow-up like: "Which buildings have the most HVAC issues?"]**

"Now a follow-up: 'Which buildings have the most HVAC issues?'

**[Wait for response]**

The AI:
- **Remembered context** - it knows we're talking about maintenance data
- **Filtered correctly** - it understood 'HVAC issues' meant defects in HVAC systems
- **Aggregated by building** - it knew I wanted a building-level breakdown
- **Ranked the results** - showing me the top problem buildings first

**[If it shows a list]**

You can see Building [X] has [Y] HVAC issues - a maintenance manager could use this to prioritize inspections."

### Demo 3 - Trend/Insight Query (1 minute)

**[Type: "Are defects trending up or down?" or "Show me defect trends"]**

"One more: 'Show me defect trends'

**[Wait for response]**

This is where the AI really shines. It:
- **Understood a vague question** - 'trends' could mean many things
- **Made smart assumptions** - probably means over time
- **Generated the right query** - monthly aggregation
- **Interpreted the result** - telling me if things are improving or getting worse

This is **conversational analytics** - no SQL, no dashboards, just questions and answers."

### Business Value Statement (1 minute)

"Why is this transformative?

**Traditional way**: 'I need to know X' → Ask data team → Wait days → Get spreadsheet → Manually analyze

**With AI Assistant**: 'I need to know X' → Ask in chat → Get answer in 3 seconds → Ask follow-up → Get deeper insight

This **democratizes data access**. You don't need to be a data analyst. You don't need to know SQL. You just ask.

Imagine a maintenance director during a budget meeting: 'Alexa, what's our UPM trend?' - and getting an instant, accurate answer. That's what this enables."

### Technical Challenge Highlight (30 seconds - optional)

"From a technical standpoint, the challenge here was:
- Designing the **function calling architecture** - giving Claude the right tools to query complex maintenance data
- **Prompt engineering** - making sure the AI stays focused on maintenance insights, not generic responses
- **Session management** - keeping conversation context without leaking memory
- **Error handling** - gracefully handling ambiguous questions

This is **applied AI engineering** - not just using an API, but architecting an intelligent system."

---

## Integration & Architecture (1-2 minutes - optional)

### System Overview

"Let me tie this together with a quick architecture overview.

**Backend**:
- **FastAPI** serving REST APIs
- **XGBoost ML model** for risk prediction (trained on historical UPM/PPM data)
- **SHAP library** for explainability
- **BERTopic** for defect clustering
- **Claude API** for conversational AI
- All running on **real-world university facilities data** - 269,000 work orders across multiple buildings

**Frontend**:
- **React** with modern component architecture
- **Recharts** for interactive visualizations
- **Real-time API integration** - everything updates live

**Data Pipeline**:
- Feature engineering from raw work orders
- Weather data integration
- Building metadata enrichment
- Monthly aggregation for time-series analysis

This is a **full-stack ML system** - not just a model, but a complete production-ready application."

---

## Closing & Impact (1 minute)

### Summary

"So in summary, what we've built here is:

1. **Explainability Dashboard** - Predict failures AND understand why using SHAP
2. **Defect Intelligence** - Discover cost patterns and trends using neural language models
3. **AI Chat Assistant** - Ask questions in natural language and get instant insights

Together, these features transform maintenance from **reactive firefighting** to **proactive, data-driven strategy**."

### Real-World Impact

"The real-world impact potential is significant:

- **Reduced downtime** - Predict failures before they happen
- **Optimized budgets** - Focus spending on high-risk, high-cost areas
- **Better planning** - Understand seasonal patterns and long-term trends
- **Faster decisions** - Get answers in seconds, not days

This is the future of facilities management - where **AI assists human expertise** to keep buildings running smoothly."

### Thank You

"Thank you for your time. I'm happy to answer any questions or demo any features in more detail."

---

## Q&A Preparation - Anticipated Questions

### Technical Questions

**Q: What accuracy does your predictive model achieve?**
A: "Our XGBoost model achieves [X]% accuracy on UPM prediction. More importantly, the SHAP explainability lets us validate predictions - we can see if the model is using sensible features or just overfitting noise."

**Q: How did you handle imbalanced data?**
A: "Great question. UPM events are rare - about [X]% of work orders. I used class weighting in XGBoost and focused on precision/recall rather than just accuracy. The goal is catching high-risk systems while minimizing false alarms."

**Q: How scalable is this system?**
A: "The backend is built on FastAPI which handles concurrent requests well. BERTopic clustering is pre-computed, not real-time, so it scales. The main constraint is the Claude API cost for chat - but we also support Ollama for free local inference."

**Q: How did you train BERTopic?**
A: "BERTopic uses sentence transformers to embed work order descriptions, then UMAP for dimensionality reduction and HDBSCAN for clustering. I fine-tuned the min_cluster_size parameter to get meaningful defect categories - not too granular, not too broad."

### Business/Application Questions

**Q: How would this integrate with existing systems?**
A: "The API is RESTful, so it can integrate with any CMMS (Computerized Maintenance Management System). You could embed these dashboards in existing tools or consume the predictions via API to trigger work orders automatically."

**Q: What data do you need to deploy this?**
A: "Minimum: Work order history with descriptions, dates, building IDs, and system types. Ideally: Weather data, building metadata (age, size, FCI), and maintenance costs. The more data, the better the predictions."

**Q: How do you handle data privacy?**
A: "All data is anonymized - no personal information. Building IDs are masked. For the Claude API, we could use local Ollama deployment for sensitive environments, keeping all data on-premises."

### Demo Questions

**Q: Can you show [specific feature]?**
A: "Absolutely! Let me navigate to..." [Be ready to demo any feature on demand]

**Q: What happens if the AI gives a wrong answer?**
A: "Good question. The chat includes suggestions to help guide users, and we could add feedback mechanisms. The key is the AI shows its work - it returns data and explains its reasoning, so users can validate answers."

---

## Timing Guide

| Section | Time | Total |
|---------|------|-------|
| Opening | 0:30 | 0:30 |
| Explainability Dashboard | 5:30 | 6:00 |
| Defect Intelligence | 4:30 | 10:30 |
| AI Chat Assistant | 4:30 | 15:00 |
| Architecture (optional) | 1:30 | 16:30 |
| Closing | 1:00 | 17:30 |
| Q&A | 5:00 | 22:30 |

**Target: 15-20 minutes presentation + 5-10 minutes Q&A**

---

## Presentation Tips

### Before You Start
- ✅ Have both tabs open: Explainability and Defect Intelligence
- ✅ Pre-select a good building with high-risk subsystems for demo
- ✅ Test chat assistant with sample questions
- ✅ Check that backend is running (should see "✓ Using Claude API")
- ✅ Prepare a backup plan if API is slow (mention it's hitting real AI, not cached)

### During Presentation
- 🎯 **Speak to the audience**, not the screen
- 🎯 **Pause after showing a feature** - let it sink in
- 🎯 **Use storytelling** - "Imagine you're a facilities director..."
- 🎯 **Highlight ML/AI** - This is a capstone, showcase the intelligence
- 🎯 **Explain business value** - Not just "cool tech", but "solves real problems"

### If Things Go Wrong
- **If API is slow**: "As you can see, this is hitting the live Claude API in real-time..."
- **If chat gives unexpected response**: "The beauty of generative AI is it's probabilistic - let me rephrase..."
- **If data doesn't load**: Switch to architecture discussion or Q&A

### Enthusiasm Points
- When showing SHAP: "This is cutting-edge ML interpretability"
- When showing BERTopic: "Unsupervised learning discovered these patterns"
- When showing Chat: "This is the future of data access"

---

## One-Liner Summary

"PredicX uses explainable AI, neural language models, and conversational interfaces to transform predictive maintenance from reactive firefighting to proactive intelligence."

