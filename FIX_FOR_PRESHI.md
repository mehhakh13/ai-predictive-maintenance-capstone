# Fix for Directory Structure Issue - For Preshi

## Problem
You're working in a nested directory structure that doesn't match the main branch. Your code is in:
- `ai-predictive-maintenance-capstone/frontend/` (wrong location)

But it should be in:
- `frontend/` (correct location)

## Steps to Fix:

### 1. Switch to main branch and pull latest:
```bash
git checkout main
git pull origin main
```

### 2. Delete the nested directory if it exists:
```bash
rm -rf ai-predictive-maintenance-capstone/
```

### 3. Create a new branch from the latest main:
```bash
git checkout -b presh-updated
```

### 4. Now work directly in `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```

### 5. For backend:
```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

## Your Server Configuration

Make sure your development server is pointing to:
- Frontend: `./frontend` (not `./ai-predictive-maintenance-capstone/frontend`)
- Backend: `./backend`

## When Making Changes:

1. Always work in the root `frontend/` directory
2. Create PRs from your branch to `main`
3. Make sure to test that data loads correctly before committing

## Current Main Branch Features:

The main branch now has:
- Year filter for risk heatmap
- Forecast strip showing next 3 months high-risk prediction
- Updated KPI calculations with year-specific logic
- All your previous subsystem drill-down work

These features are more recent than what's on the `presh` branch, so start from main!
