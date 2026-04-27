# Project Folder Structure

## Overview
This document describes the reorganized folder structure of the AI Predictive Maintenance project, organized by feature for better clarity and maintainability.

## What Changed
1. **Removed duplicate frontend folder** - Eliminated the incomplete frontend folder at root level
2. **Consolidated frontend** - Moved the complete frontend from nested location to root level
3. **Feature-based organization** - Restructured code into feature folders instead of type-based folders

## New Frontend Structure

```
frontend/
├── src/
│   ├── features/               # All features organized here
│   │   ├── cost-analysis/      # Cost Analysis Feature
│   │   │   ├── components/     # CostBreakdownChart, CostDistribution, etc.
│   │   │   ├── hooks/          # useCostAnalysisData
│   │   │   └── pages/          # CostAnalysisPage
│   │   │
│   │   ├── risk-heatmap/       # Risk Heatmap Feature
│   │   │   ├── components/     # Heatmap, SubsystemHeatmap, etc.
│   │   │   ├── hooks/          # useRiskHeatmapData
│   │   │   └── pages/          # RiskHeatmapPage
│   │   │
│   │   ├── prediction/         # Prediction Feature
│   │   │   └── pages/          # Prediction
│   │   │
│   │   ├── risk-ranking/       # Risk Ranking Feature
│   │   │   └── pages/          # RiskRanking
│   │   │
│   │   ├── explainability/     # Explainability Feature
│   │   │   └── pages/          # Explainability
│   │   │
│   │   ├── dashboard/          # Dashboard Feature
│   │   │   └── pages/          # Dashboard
│   │   │
│   │   └── home/               # Home Page Feature
│   │       └── pages/          # HomePage
│   │
│   ├── shared/                 # Shared across all features
│   │   ├── components/         # Navbar, KpiCard
│   │   └── utils/              # format.js
│   │
│   ├── App.jsx                 # Main app component
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
│
├── public/                     # Static assets
├── package.json                # Dependencies
└── vite.config.js              # Vite configuration
```

## Root Project Structure

```
ai-predictive-maintenance-capstone/
├── frontend/                   # React frontend (feature-based)
├── backend/                    # FastAPI backend
├── scripts/                    # Python scripts for data processing
├── data/                       # Data files and outputs
├── models/                     # Trained ML models
├── notebooks/                  # Jupyter notebooks
├── schemas/                    # Database schemas
├── services/                   # Shared services
├── tools/                      # Utility tools
└── [documentation files]       # Various .md files
```

## Benefits of This Structure

### 1. **Feature Isolation**
Each feature has its own folder with all related files:
- Easy to find: "Where's the cost analysis code?" → `features/cost-analysis/`
- Self-contained: Components, hooks, and pages for each feature are together

### 2. **Clear Boundaries**
- **Feature-specific code** → `features/[feature-name]/`
- **Shared code** → `shared/`
- No confusion about where files belong

### 3. **Scalability**
- Easy to add new features: Just create a new folder in `features/`
- Easy to remove features: Delete the feature folder
- Team members can work on different features without conflicts

### 4. **Better Navigation**
Before:
```
components/
  ├── CostAnalysis/
  │   └── KpiRow.jsx
  └── RiskHeatmap/
      └── KpiRow.jsx
```

After:
```
features/
  ├── cost-analysis/components/KpiRow.jsx
  └── risk-heatmap/components/KpiRow.jsx
```

## Import Paths

All import paths have been updated to reflect the new structure:

### App.jsx
```javascript
import Navbar from './shared/components/Navbar';
import HomePage from './features/home/pages/HomePage';
import CostAnalysisPage from './features/cost-analysis/pages/CostAnalysisPage';
```

### Feature Components
```javascript
// Within a feature
import { useCostAnalysisData } from '../hooks/useCostAnalysisData';
import KpiRow from '../components/KpiRow';

// Shared utilities
import { formatCurrency } from '../../../shared/utils/format';
```

## Next Steps (Optional)

Consider organizing documentation files:
1. Create a `docs/` folder at root
2. Move all `.md` files to `docs/`
3. Keep only README.md at root

This would make the root directory cleaner and documentation easier to browse.
