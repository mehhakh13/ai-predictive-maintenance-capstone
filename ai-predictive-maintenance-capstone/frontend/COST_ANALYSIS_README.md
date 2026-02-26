# Maintenance Cost Analysis Dashboard

## Overview

The **Maintenance Cost Analysis Dashboard** is a comprehensive financial analytics tool for facility maintenance operations. It provides actionable insights into maintenance spending, compares Planned Preventive Maintenance (PPM) vs Unplanned Maintenance (UPM) costs, and identifies cost-saving opportunities through data visualization and outlier detection.

## Features

### 1. Key Performance Indicators (KPIs)
- **Total Cost**: Aggregate maintenance spending across all work orders
- **Average Cost per Work Order**: Mean maintenance cost metric
- **PPM vs UPM Cost Breakdown**: Side-by-side comparison with percentage distribution
- **Most Expensive System**: Identifies the system with highest total maintenance cost
- **Cost Outliers**: Counts work orders exceeding the 95th percentile threshold

### 2. Interactive Visualizations

#### Cost Breakdown by System (Stacked Horizontal Bar Chart)
- **Default View**: Shows Labor, Material, and Other costs stacked by system
- **Toggle View**: Switches to PPM vs UPM cost comparison
- Top 10 systems sorted by total cost (descending)
- Interactive tooltips with detailed cost breakdowns
- Color-coded segments for easy distinction

#### Monthly Cost Trends (Line Chart)
- Dual-line chart comparing PPM and UPM costs over time
- Time-series analysis showing seasonal patterns
- Helps identify cost spikes and trending patterns
- Interactive tooltips showing monthly totals

#### Top Cost Contributors (Right Panel)
- Ranked list of top 5 systems by total cost
- Visual mini-bars showing percentage contribution
- Dollar amounts with currency formatting
- Hover effects for better UX

#### Cost Distribution (Donut Chart)
- **Primary View**: PPM vs UPM share of total costs
- **Secondary View**: Labor vs Material vs Other breakdown
- Toggle button to switch between views
- Percentage labels on chart segments
- Summary table below with exact values

### 3. Outlier Detection & Analysis
- Automatically calculates P95 (95th percentile) threshold
- Displays top 10 cost outliers in a detailed table
- Shows Work Order ID, Date, System, Type, and cost components
- Educational "Explain This" panel describing what outliers represent
- Helps identify emergency repairs and deferred maintenance

### 4. Advanced Filtering
- **Date Range**: Last 3/6/12/24 months
- **University**: Multi-campus support
- **Building**: Drill down to specific buildings
- **System Search**: Real-time text search for systems
- **Maintenance Type**: Filter by All/PPM/UPM

## Technical Architecture

### File Structure
```
frontend/src/
├── pages/
│   └── CostAnalysisPage.jsx           # Main dashboard page
├── components/CostAnalysis/
│   ├── KpiRow.jsx                     # KPI cards component
│   ├── CostBreakdownChart.jsx         # Stacked bar chart
│   ├── CostTrendChart.jsx             # Monthly trend lines
│   ├── TopContributors.jsx            # Top 5 systems panel
│   ├── CostDistribution.jsx           # Pie/donut chart
│   └── OutlierTable.jsx               # Outlier detection table
├── hooks/
│   └── useCostAnalysisData.js         # Data loading & filtering hook
└── utils/
    └── format.js                      # Currency & number formatting
```

### Component Details

#### `CostAnalysisPage.jsx`
- **Purpose**: Main container for the entire dashboard
- **State Management**:
  - Filter state (date range, university, building, system, maintenance type)
  - UI toggle states (PPM vs UPM view, distribution view, modals)
- **Layout**: 2-column responsive grid (left: charts, right: insights)
- **Features**: "Explain This" educational panel, comprehensive filter bar

#### `KpiRow.jsx`
- **Props**: `aggregations` (computed metrics), `totalWorkOrders` (count)
- **Displays**: 5 KPI cards with icons, values, and subtitles
- **Styling**: Hover effects, color-coded icons

#### `CostBreakdownChart.jsx`
- **Library**: Recharts (BarChart component)
- **Props**: `data` (filtered work orders), `showPPMvsUPM` (toggle)
- **Features**:
  - Stacked horizontal bars
  - Custom tooltips with detailed breakdowns
  - Top 10 systems by total cost
  - Dual-mode rendering (cost types vs PPM/UPM)

#### `CostTrendChart.jsx`
- **Library**: Recharts (LineChart component)
- **Props**: `data` (filtered work orders)
- **Features**:
  - Monthly aggregation from WOStartDate
  - Dual lines (PPM green, UPM orange)
  - Custom tooltips
  - Responsive X-axis with angled labels

#### `TopContributors.jsx`
- **Props**: `data` (filtered work orders)
- **Computation**: Aggregates costs by system, calculates percentages
- **UI**: Ranked list with visual progress bars and dollar amounts

#### `CostDistribution.jsx`
- **Library**: Recharts (PieChart component)
- **Props**: `data`, `view` ('ppm-upm' or 'cost-type')
- **Features**:
  - Donut chart with percentage labels
  - Dual-view support
  - Summary table below chart

#### `OutlierTable.jsx`
- **Props**: `data`, `threshold` (P95 value), `isModal` (optional)
- **Features**:
  - P95 threshold calculation
  - Top 10 outliers sorted by cost
  - Educational explanation panel
  - Can render inline or as modal
  - Badge styling for PPM/UPM types

### Data Hook: `useCostAnalysisData.js`

**Purpose**: Centralized data management with filtering and aggregations

**Mock Data Generator**:
- Generates 500-800 realistic work orders
- 15 different system types (HVAC, Electrical, Plumbing, etc.)
- 35% PPM, 65% UPM distribution
- Cost variation by system type
- 5% outlier injection (3-5x normal cost)
- Date range: 2023-01-01 to 2024-12-31

**Filtering Logic**:
- Date range filtering
- University/Building filtering
- System search (case-insensitive)
- Maintenance type filtering
- Reactive filtering with useMemo

**Aggregations**:
- Total cost
- Average cost per WO
- PPM total cost
- UPM total cost
- Most expensive system
- Outlier count (P95)

**API Integration Ready**:
```javascript
// TODO: Replace mock data with:
const response = await fetch('/api/cost-analysis');
const data = await response.json();
```

### Utility Functions: `format.js`

**Exported Functions**:
- `formatCurrency(value, decimals)` → "$1,234.56"
- `formatPercent(value, decimals, isDecimal)` → "45.2%"
- `formatCompactNumber(value)` → "1.2K", "3.5M"
- `formatNumber(value, decimals)` → "1,234.56"
- `calculatePercentile(arr, percentile)` → percentile value

**Usage**: Ensures consistent formatting across all components

## Styling (Dark Theme)

### Color Palette
- **Background**: `#000000` (page), `#1a1a1a` (cards)
- **Text**: `#e2e8f0` (primary), `#94a3b8` (secondary)
- **Borders**: `#333333` (standard), `#666666` (highlighted)
- **Accents**:
  - PPM: `#10b981` (green)
  - UPM: `#f59e0b` (orange)
  - Labor: `#3b82f6` (blue)
  - Material: `#8b5cf6` (purple)
  - Other: `#ec4899` (pink)

### Responsive Design
- **Desktop (>1200px)**: 2-column layout
- **Tablet (768px-1200px)**: Stacked single column
- **Mobile (<768px)**: Optimized filters, smaller fonts

## Routing

### Route Configuration
```javascript
// App.jsx
<Route path="/cost-analysis" element={<CostAnalysisPage />} />
```

### Home Page Integration
```javascript
// HomePage.jsx - dashboards array
{
  title: 'Maintenance Cost Analysis',
  description: 'PPM vs UPM cost impact, top expensive systems, cost trends, and outlier detection.',
  icon: DollarSign,
  path: '/cost-analysis',
  color: '#10b981',
  featured: true
}
```

## Data Schema (CSV/API)

### Required Columns
```
WOId                  : string  - Work order identifier
WOStartDate           : date    - Work order start date (YYYY-MM-DD)
SystemDescription     : string  - System name (e.g., "HVAC")
MaintenanceType       : string  - "PPM" or "UPM"
LaborCost            : number  - Labor cost in dollars
MaterialCost         : number  - Material cost in dollars
OtherCost            : number  - Other costs in dollars
TotalCost            : number  - Total cost (sum of above)
```

### Optional Columns
```
SubsystemDescription  : string  - Subsystem detail
WOPriority           : string  - Low/Medium/High/Critical
UniversityID         : string  - Campus identifier
BuildingID           : string  - Building identifier
State                : string  - State/Province
Country              : string  - Country code
```

### CSV Loading Function
```javascript
import { loadCostDataFromCSV } from './hooks/useCostAnalysisData';

const data = await loadCostDataFromCSV('/path/to/cost_data.csv');
```

## Key Insights for Presentation

### Business Value
1. **Cost Transparency**: See exactly where maintenance dollars are spent
2. **PPM vs UPM Comparison**: Quantify the cost difference (UPM typically 40-60% more expensive)
3. **System Prioritization**: Identify which systems consume the most budget
4. **Outlier Detection**: Flag unusual spending for investigation
5. **Trend Analysis**: Identify seasonal patterns and cost escalation

### Technical Highlights
- **Modular Architecture**: Reusable components, clean separation of concerns
- **Performance Optimized**: useMemo for expensive calculations, prevent unnecessary re-renders
- **User Experience**: Tooltips, hover effects, responsive design, educational content
- **Mock Data Fallback**: Works immediately without backend
- **API Ready**: Easy swap from mock to real data
- **Accessibility**: Clear labels, semantic HTML, keyboard navigation

### Future Enhancements
- Export data to CSV/PDF
- Budget vs actual comparison
- Predictive cost modeling
- Custom date range picker
- Multi-year trend analysis
- Cost benchmarking across buildings/campuses

## Usage Instructions

### Running the Dashboard

1. **Start Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Navigate to Cost Analysis**:
   - Go to http://localhost:5173
   - Click "Maintenance Cost Analysis" card
   - Or navigate directly to http://localhost:5173/cost-analysis

3. **Explore Features**:
   - Use filters to slice data
   - Toggle between PPM vs UPM views
   - Click "Explain This" for educational content
   - Hover over charts for detailed tooltips
   - View outlier table at bottom

### Integrating Real Data

**Option 1: API Endpoint**
```javascript
// In useCostAnalysisData.js, replace mock data:
const response = await fetch('/api/cost-analysis');
const data = await response.json();
```

**Option 2: CSV File**
```javascript
import { loadCostDataFromCSV } from '../hooks/useCostAnalysisData';

const data = await loadCostDataFromCSV('/data/maintenance_costs.csv');
```

## Capstone Presentation Talking Points

1. **Problem Statement**:
   - Maintenance costs are often opaque and reactive
   - UPM costs significantly more than PPM due to emergency labor and expedited parts
   - Need visibility into spending patterns to optimize budget allocation

2. **Solution**:
   - Built a comprehensive cost analytics dashboard
   - Compares PPM vs UPM to quantify the value of preventive maintenance
   - Identifies top cost drivers and outliers for targeted improvement

3. **Technical Implementation**:
   - React-based SPA with modular component architecture
   - Custom React hooks for data management
   - Recharts library for interactive visualizations
   - Responsive dark theme design
   - Mock data generator for demonstration purposes

4. **Key Features Demo**:
   - Show KPI cards → "At a glance, see total spending and outliers"
   - Show cost breakdown chart → "Identify which systems cost the most"
   - Toggle PPM vs UPM → "Compare planned vs unplanned costs"
   - Show trend chart → "Seasonal patterns emerge"
   - Show outlier table → "Flag unusual expenses for investigation"

5. **Business Impact**:
   - Transparent cost visibility enables data-driven decisions
   - Quantifies the ROI of preventive maintenance programs
   - Helps justify budget for PPM activities
   - Reduces total maintenance costs through outlier investigation

## Code Quality & Best Practices

- ✅ **Modular Components**: Each component has a single responsibility
- ✅ **Performance**: useMemo for expensive calculations
- ✅ **Readability**: Clear naming, comprehensive comments
- ✅ **Maintainability**: Easy to extend with new charts or KPIs
- ✅ **Responsive**: Works on desktop, tablet, and mobile
- ✅ **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation
- ✅ **Dark Theme**: Consistent styling matching existing app
- ✅ **Error Handling**: Loading and error states
- ✅ **Documentation**: Inline comments and this README

---

**Built with**: React 19, Recharts, Lucide Icons, Vite
**Author**: Claude Sonnet 4.5
**Date**: February 2026
**License**: MIT
