#!/bin/bash
#
# Quick Fix and Run Script
# This script will:
# 1. Check your setup
# 2. Generate missing data
# 3. Start backend and frontend servers
#

set -e

echo "================================================================================"
echo "AI PREDICTIVE MAINTENANCE - SETUP FIX & RUN"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check current directory
echo "Checking setup..."
if [ ! -f "FMUCD.csv" ]; then
    echo -e "${RED}✗ FMUCD.csv not found. Are you in the right directory?${NC}"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo -e "${RED}✗ frontend/ directory not found${NC}"
    exit 1
fi

if [ ! -d "backend" ]; then
    echo -e "${RED}✗ backend/ directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Directory structure looks good${NC}"
echo ""

# Check if data needs to be generated
if [ ! -f "data/dashboard/building_level_heatmap.csv" ]; then
    echo -e "${YELLOW}⚠ Dashboard data not found. Need to run data pipeline.${NC}"
    echo ""
    read -p "Run full data pipeline? This will take 5-10 minutes. (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Running data pipeline..."
        ./run_full_pipeline.sh
        echo ""
        echo -e "${GREEN}✓ Data pipeline complete${NC}"
    else
        echo -e "${YELLOW}Skipping data generation. Data loading may fail.${NC}"
    fi
else
    echo -e "${GREEN}✓ Dashboard data exists${NC}"
    echo ""
    read -p "Regenerate data anyway? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./run_full_pipeline.sh
    fi
fi

echo ""
echo "================================================================================"
echo "STARTING SERVERS"
echo "================================================================================"
echo ""

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Backend already running on port 8000${NC}"
else
    echo "Starting backend server..."
    cd backend
    python3 main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
    echo "  Backend logs: tail -f backend.log"
fi

# Wait for backend to start
sleep 3

# Check if frontend is already running
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Frontend already running on port 5173${NC}"
else
    echo "Starting frontend server..."
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo "  Frontend logs: tail -f frontend.log"
fi

echo ""
echo "================================================================================"
echo "SERVERS RUNNING!"
echo "================================================================================"
echo ""
echo -e "${GREEN}Backend:${NC}  http://localhost:8000"
echo -e "${GREEN}Frontend:${NC} http://localhost:5173"
echo ""
echo "Test backend API:"
echo "  curl http://localhost:8000/api/risk-heatmap/ml?university=10"
echo ""
echo "View logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "Stop servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop this script (servers will keep running)${NC}"
echo ""
