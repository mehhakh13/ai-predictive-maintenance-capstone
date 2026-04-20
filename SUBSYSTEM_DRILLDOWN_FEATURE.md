# Subsystem Drill-Down Feature

## Overview

Added hierarchical drill-down capability to the Risk Heatmap page, allowing users to explore risk from System level down to Subsystem level.

## Feature Flow

1. **Main Heatmap** shows Systems (HVAC, Electrical, Plumbing, etc.) vs Months
2. **Click System Row** to drill down to subsystems for that system
3. **Subsystem Heatmap** appears below showing detailed subsystem breakdown
4. **Click "Back to Systems"** to collapse the subsystem view

## Implementation Details

### 1. Data Hook Updates (`useRiskHeatmapData.js`)

**Added:**
- System-to-Subsystem mapping for all subsystems
- System-level aggregation for main heatmap
- `subsystemData` export for drill-down

**Changes:**
- Main heatmap now shows SYSTEMS (not subsystems)
- Subsystems are aggregated to their parent systems
- Risk values are averaged across subsystems within each system
- Mock data generators include both `SystemDescription` and `SubsystemDescription`

**Example System-to-Subsystem Mapping:**
```javascript
HVAC → Distribution Systems
     → Terminal & Package Units
     → Heat Generation Systems
     → Controls and Instrumentation

Electrical → Lighting and Branch Wiring
          → Communications & Security
          → Electrical Service & Distribution

Plumbing → Plumbing Fixtures
         → Domestic Water Distribution
```

### 2. New Component (`SubsystemHeatmap.jsx`)

**Features:**
- Same visual design as main heatmap (dark theme, color scale)
- Filters subsystems by selected system
- Rows: SubsystemDescription
- Columns: Month (Jan-Dec)
- Colors: Same risk color scale (green to red)
- Tooltip: Shows risk, coverage, historical rates
- "Back to Systems" button with X icon

**Props:**
- `selectedSystem` - The system to drill down into
- `subsystemData` - Full subsystem-level data
- `onCellClick` - Handle cell clicks (opens modal)
- `showValues` - Show/hide percentage values
- `onClose` - Close subsystem view

### 3. Main Heatmap Updates (`Heatmap.jsx`)

**Added:**
- `onRowClick` prop for row header clicks
- Clickable row headers with pointer cursor
- Tooltip hint: "Click to view subsystems"

**Behavior:**
- Clicking a **row header** triggers drill-down
- Clicking a **cell** opens the detail modal (unchanged)

### 4. Page Updates (`RiskHeatmapPage.jsx`)

**Added State:**
- `selectedSystem` - Tracks which system is selected for drill-down

**Added Handlers:**
- `handleSystemRowClick(system)` - Sets selected system
- `handleCloseSubsystemView()` - Clears selected system

**Layout:**
- Subsystem heatmap renders below main heatmap when system is selected
- Hidden when no system is selected
- Same left/right layout maintained

## User Experience

### Step 1: View System Heatmap
```
System Risk Heatmap
┌────────────────────┬─────┬─────┬─────┬─────┐
│ System / Month     │ Jan │ Feb │ Mar │ ... │
├────────────────────┼─────┼─────┼─────┼─────┤
│ HVAC              ◄───────────────────────── Click row header
│ Electrical         │     │     │     │     │
│ Plumbing          │     │     │     │     │
│ Fire Protection   │     │     │     │     │
└────────────────────┴─────┴─────┴─────┴─────┘
```

### Step 2: Click "HVAC" Row Header

### Step 3: Subsystem Heatmap Appears
```
Subsystem Risk Heatmap — HVAC                    [X] Back to Systems
┌─────────────────────────────┬─────┬─────┬─────┬─────┐
│ Subsystem / Month           │ Jan │ Feb │ Mar │ ... │
├─────────────────────────────┼─────┼─────┼─────┼─────┤
│ Heat Generation Systems     │ 🟥  │ 🟥  │ 🟨  │     │
│ Terminal & Package Units    │ 🟨  │ 🟨  │ 🟩  │     │
│ Distribution Systems        │ 🟩  │ 🟩  │ 🟩  │     │
│ Controls and Instrumentation│ 🟩  │ 🟩  │ 🟩  │     │
└─────────────────────────────┴─────┴─────┴─────┴─────┘
```

### Step 4: Click "Back to Systems" or Select Another System

## Visual Consistency

✅ **Same dark theme** as main heatmap
✅ **Same color scale**:
- Green: < 15% risk
- Light Green: 15-30%
- Yellow: 30-50%
- Orange: 50-70%
- Red: ≥ 70%

✅ **Same heatmap styling**: Grid layout, tooltips, hover effects
✅ **Same month columns**: Jan through Dec

## Data Filtering

The subsystem heatmap respects all current filters:
- ✅ Selected University (10, 11)
- ✅ Selected Building (All Buildings or specific building)
- ✅ Selected System (via row click)

## Example Use Case

**Scenario:** Facility manager sees high risk in HVAC system during winter months

**Workflow:**
1. View main heatmap → HVAC shows red in Dec, Jan, Feb
2. Click "HVAC" row → Subsystem heatmap appears
3. See that "Heat Generation Systems" is the high-risk subsystem
4. Click cell → Modal shows work order details
5. Take action: Schedule preventive maintenance for heating systems

## Code Changes Summary

### Files Modified:
1. ✅ `frontend/src/hooks/useRiskHeatmapData.js`
   - Added system-subsystem mapping
   - Added system-level aggregation
   - Export `subsystemData` for drill-down

2. ✅ `frontend/src/components/RiskHeatmap/Heatmap.jsx`
   - Added `onRowClick` prop
   - Made row headers clickable

3. ✅ `frontend/src/pages/RiskHeatmapPage.jsx`
   - Import SubsystemHeatmap component
   - Add selectedSystem state
   - Add drill-down handlers
   - Render subsystem heatmap conditionally

### Files Created:
4. ✅ `frontend/src/components/RiskHeatmap/SubsystemHeatmap.jsx`
   - New component for subsystem drill-down

## Testing

To test the feature:

1. Start dev server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Navigate to Risk Heatmap page

3. Test drill-down:
   - Click on any system row header (e.g., "HVAC", "Electrical")
   - Verify subsystem heatmap appears below
   - Check that subsystems are correctly filtered
   - Click "Back to Systems" to close

4. Test filtering:
   - Change university → subsystem data updates
   - Change building → subsystem data updates
   - Click different systems → different subsystems shown

## Future Enhancements (Optional)

- Add animation when subsystem heatmap appears/disappears
- Highlight selected system row in main heatmap
- Add breadcrumb navigation (University > Building > System)
- Allow triple drill-down (System → Subsystem → Component)

## Notes

- No redesign was done - layout and styling remain exactly the same
- Subsystem heatmap uses the exact same color scale and visual design
- Feature is non-intrusive: hidden when not in use
- Compatible with existing filters and modal functionality
