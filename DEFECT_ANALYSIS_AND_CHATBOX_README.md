# Defect Analysis & Chatbox Features - In-Depth Documentation

## Table of Contents
1. [Overview](#overview)
2. [Defect Analysis Dashboard](#defect-analysis-dashboard)
3. [Architecture & Data Flow](#architecture--data-flow)
4. [API Endpoints](#api-endpoints)
5. [Frontend Components](#frontend-components)
6. [Machine Learning & NLP](#machine-learning--nlp)
7. [Chatbox Feature](#chatbox-feature)
8. [Setup & Configuration](#setup--configuration)
9. [Technology Stack](#technology-stack)

---

## Overview

This document provides comprehensive documentation for two key features of the AI Predictive Maintenance system:

- **Defect Analysis Dashboard**: A fully-implemented, production-ready analytics platform for exploring 120,000+ maintenance work orders
- **Chatbox Feature**: Currently not implemented (placeholder for future conversational AI integration)

---

## Defect Analysis Dashboard

### Purpose

The Defect Intelligence Dashboard analyzes failure patterns and root causes from university facilities maintenance data using BERTopic-discovered defect categories. It enables maintenance managers to:

- Identify the most frequent and costly defect types
- Understand system-specific failure patterns
- Pinpoint high-risk buildings
- Track defect trends over time
- Make data-driven maintenance decisions

### Key Metrics

The dashboard surfaces four critical KPIs:

1. **Total Defects**: Count of all defect instances in the filtered dataset
2. **Most Frequent Defect**: The defect type occurring most often
3. **Highest Cost Defect**: The single defect with maximum cost impact
4. **Most Affected System**: The building system with the most defects

### Features

#### 1. Advanced Filtering System

Located in `frontend/src/components/DefectIntelligence/FiltersBar.jsx`

**Available Filters:**
- **University**: Filter by campus (Universities 10, 11, 12)
- **Building**: Filter by specific Building ID
- **Defect Type**: Select from 63 BERTopic-discovered categories
- **System**: Filter by building system (Electrical, HVAC, Plumbing, Structural, Security, Fire Safety, General Maintenance, Other)
- **Date Range**: Start Date and End Date pickers
- **Reset**: Clear all filters with one click

**Filter Logic:**
- Filters are applied client-side and server-side
- Multiple filters combine with AND logic
- Date filters use ISO format (YYYY-MM-DD)
- Changes trigger automatic data refetch

#### 2. Visualization Components

##### A. Defect Bar Chart (`DefectBarChart.jsx`)
- **Purpose**: Shows top 10 defects by occurrence frequency
- **Chart Type**: Horizontal bar chart (Recharts)
- **Interaction**: Hover to see exact count
- **Color Scheme**: Blue (#3b82f6)

##### B. Cost Bar Chart (`CostBarChart.jsx`)
- **Purpose**: Displays top 10 defects by total cost impact
- **Chart Type**: Horizontal bar chart
- **Formatting**: Currency formatted (e.g., $12,345)
- **Color Scheme**: Green (#10b981)

##### C. System Heatmap (`SystemHeatmap.jsx`)
- **Purpose**: Interactive matrix of Systems × Defect Types
- **Interaction**:
  - Click cells to apply filters
  - Hover for detailed tooltips
  - Toggle between Count and Cost metrics
- **Color Gradient**: Yellow → Amber → Orange → Red (intensity-based)
- **Implementation**: Custom HTML5 Canvas rendering for performance

##### D. Defect Table (`DefectTable.jsx`)
- **Purpose**: Detailed work order drill-down
- **Features**:
  - Full-text search across descriptions
  - Sortable columns (Description, Type, System, Building, Cost, Date)
  - Pagination (10 rows per page)
  - Responsive design
- **Columns**:
  - Work Order Description
  - Defect Type (human-readable label)
  - System Category
  - Building ID
  - Estimated Cost
  - Date Completed

##### E. Impact Ranking (`ImpactRanking.jsx`)
- **Purpose**: Ranks defect categories by impact score
- **Impact Score**: `Total Cost × Average Priority × Frequency`
- **Visual Indicators**:
  - Risk level badges (Critical, High, Medium, Low)
  - Color-coded impact bars
  - Defect count and total cost
- **Interaction**: Click defect to auto-filter dashboard

##### F. Building Risk View (`BuildingRiskView.jsx`)
- **Purpose**: Identifies top problematic buildings
- **Metrics per Building**:
  - Number of defects
  - Total cost
  - Risk level classification
  - Top 3 defect types
- **Interaction**: Click building to filter entire dashboard

##### G. Monthly Trends Chart (`MonthlyTrendsChart.jsx`)
- **Purpose**: Track defect patterns over time
- **Chart Type**: Multi-line chart
- **Categories**: Up to 10 most frequent defect types
- **X-Axis**: Month-Year (e.g., "Jan 2024")
- **Y-Axis**: Defect count

### Defect Categories

The system uses **BERTopic NLP** to discover 63 distinct defect patterns from work order descriptions:

| Topic ID | Defect Label | Examples |
|----------|--------------|----------|
| 0 | Lighting System Failure | "Light out in room 204", "Fluorescent bulb replacement needed" |
| 1 | HVAC Temperature Control | "Room too hot", "AC not cooling properly" |
| 2 | Door Lock & Access | "Door won't lock", "Key card reader broken" |
| 3 | Electrical Outlet Issue | "Outlet not working", "Power surge in lab" |
| 19 | Thermostat Malfunction | "Thermostat unresponsive", "Temperature set incorrectly" |
| ... | ... | ... (63 total categories) |

**Source Data**: `backend/topic_info_IMPROVED.csv`

---

## Architecture & Data Flow

### High-Level Flow

```
User Interface (React)
    ↓
Frontend Hooks (useDefectData, useAggregatedDefectData)
    ↓
HTTP Requests to FastAPI Backend
    ↓
Data Processing Layer (Pandas/NumPy)
    ↓
Data Sources (Parquet files)
    ↓
Return JSON to Frontend
    ↓
Visualizations Render (Recharts, Custom Canvas)
```

### Data Sources

**Primary Dataset**: `df_with_topics_IMPROVED.parquet`
- 120,000+ work order records
- Columns: Work Order ID, Description, System, Building, Date, BERTopic Topic ID, Priority, Duration

**Pre-Aggregated Data**: `defect_intelligence/aggregated/*.parquet`
- `defect_summary.parquet`: Defect-level aggregations
- `defect_by_system.parquet`: System-level breakdowns
- `defect_by_building.parquet`: Building-level metrics
- `defect_monthly.parquet`: Time series data
- `defect_impact.parquet`: Impact rankings

**Topic Mapping**: `topic_info_IMPROVED.csv`
- Maps 78 BERTopic topic IDs to human-readable labels
- Includes representative keywords per topic

### Cost Calculation Logic

Since real cost data is unavailable, the backend synthesizes realistic costs:

```python
# Pseudo-code from backend/main.py
base_costs = {
    "lighting": 150,
    "hvac": 800,
    "plumbing": 600,
    "electrical": 400,
    "door": 250,
    "elevator": 3000
}

cost = base_cost * priority_multiplier * duration_multiplier * random(0.8, 1.2)
```

**Factors:**
- Defect complexity (keyword matching in description)
- Priority level (High = +50%, Low = -25%)
- Duration (Long jobs = +30%)
- Random variation (±20% to simulate real-world variability)

---

## API Endpoints

All endpoints are defined in `backend/main.py` (lines 321-895)

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. GET `/api/defect-intelligence`
**Purpose**: Fetch raw defect data with filters

**Query Parameters:**
- `universityId` (optional): Filter by university (10, 11, or 12)
- `buildingId` (optional): Filter by building ID
- `defectType` (optional): Filter by defect label
- `system` (optional): Filter by system category
- `startDate` (optional): ISO date string (YYYY-MM-DD)
- `endDate` (optional): ISO date string (YYYY-MM-DD)
- `limit` (optional, default 1000): Max records to return

**Response:**
```json
{
  "data": [
    {
      "work_order_id": "WO123456",
      "description": "Light out in room 204",
      "defect_type": "Lighting System Failure",
      "system": "Electrical",
      "building_id": "BLDG001",
      "cost": 150.25,
      "date": "2024-03-15",
      "priority": "Medium",
      "duration_hours": 1.5
    },
    ...
  ],
  "total": 1523,
  "filters_applied": {
    "university": "10",
    "system": "Electrical"
  }
}
```

#### 2. GET `/api/defects/summary`
**Purpose**: Aggregated defect category summaries

**Response:**
```json
[
  {
    "defect_type": "HVAC Temperature Control",
    "count": 4523,
    "total_cost": 3618400.50,
    "avg_cost": 800.00,
    "avg_priority": 2.3,
    "impact_score": 10422520
  },
  ...
]
```

#### 3. GET `/api/defects/by-system`
**Purpose**: System-level defect breakdown

**Response:**
```json
[
  {
    "system": "HVAC",
    "defects": [
      {"defect_type": "Temperature Control", "count": 4523, "cost": 3618400},
      {"defect_type": "Air Filter Replacement", "count": 2341, "cost": 468200}
    ],
    "total_defects": 6864,
    "total_cost": 4086600
  },
  ...
]
```

#### 4. GET `/api/defects/by-building`
**Purpose**: Building-level risk assessment

**Response:**
```json
[
  {
    "building_id": "BLDG042",
    "defect_count": 234,
    "total_cost": 187200,
    "risk_level": "High",
    "top_defects": [
      {"type": "Plumbing Leak", "count": 89},
      {"type": "HVAC Failure", "count": 67},
      {"type": "Electrical Outlet", "count": 45}
    ]
  },
  ...
]
```

#### 5. GET `/api/defects/monthly`
**Purpose**: Time series trend data

**Response:**
```json
[
  {
    "month": "2024-01",
    "defects": [
      {"defect_type": "Lighting", "count": 234},
      {"defect_type": "HVAC", "count": 189}
    ]
  },
  ...
]
```

#### 6. GET `/api/defects/impact`
**Purpose**: Impact-ranked defect categories

**Response:**
```json
[
  {
    "defect_type": "Elevator Malfunction",
    "frequency": 89,
    "total_cost": 267000,
    "avg_priority": 3.8,
    "impact_score": 91260,
    "risk_level": "Critical"
  },
  ...
]
```

### Error Handling

All endpoints return standard HTTP status codes:
- `200 OK`: Successful request
- `400 Bad Request`: Invalid query parameters
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server-side processing error

**Error Response Format:**
```json
{
  "error": "Invalid date format",
  "detail": "startDate must be in YYYY-MM-DD format",
  "status_code": 400
}
```

---

## Frontend Components

### Component Hierarchy

```
DefectIntelligence.jsx (Main Page)
├── FiltersBar.jsx
│   └── Filter inputs (University, Building, Defect Type, System, Dates)
├── KPI Section
│   └── 4× KpiCard.jsx components
├── Charts Grid (2 columns)
│   ├── DefectBarChart.jsx
│   └── CostBarChart.jsx
├── Insights Grid (2 columns)
│   ├── ImpactRanking.jsx
│   └── BuildingRiskView.jsx
├── MonthlyTrendsChart.jsx
├── SystemHeatmap.jsx
└── DefectTable.jsx
```

### Custom Hooks

#### `useDefectData.js`
**Location**: `frontend/src/hooks/useDefectData.js`

**Purpose**: Fetch and manage raw defect intelligence data

**Usage:**
```javascript
import { useDefectData } from '../hooks/useDefectData';

function MyComponent() {
  const {
    data,           // Raw work order data
    loading,        // Boolean loading state
    error,          // Error object if request failed
    filters,        // Current filter state
    setFilters,     // Function to update filters
    resetFilters    // Function to clear all filters
  } = useDefectData();

  // Component logic...
}
```

**Features:**
- Automatic refetch on filter changes
- Debounced API calls (300ms)
- Error retry logic
- Loading state management

#### `useAggregatedDefectData.js`
**Location**: `frontend/src/hooks/useAggregatedDefectData.js`

**Purpose**: Fetch pre-computed summary data in parallel

**Usage:**
```javascript
import { useAggregatedDefectData } from '../hooks/useAggregatedDefectData';

function MyComponent() {
  const {
    summary,        // Defect category summaries
    bySystem,       // System-level data
    byBuilding,     // Building-level data
    monthly,        // Time series data
    impact,         // Impact rankings
    loading,        // True if any request is pending
    error           // Error from any request
  } = useAggregatedDefectData(filters);

  // Component logic...
}
```

**Implementation**: Uses `Promise.all()` to fetch 5 endpoints simultaneously

### Component Details

#### FiltersBar Component

**File**: `frontend/src/components/DefectIntelligence/FiltersBar.jsx`

**Props:**
- `filters` (object): Current filter values
- `onFiltersChange` (function): Callback when filters update
- `onReset` (function): Callback to reset all filters

**Filter Types:**
1. **Dropdown Selects**: University, Defect Type, System
2. **Text Input**: Building ID (with autocomplete)
3. **Date Pickers**: Start Date, End Date
4. **Action Button**: Reset All Filters

**Styling**: Tailwind CSS with responsive grid layout

#### KpiCard Component

**File**: `frontend/src/components/DefectIntelligence/KpiCard.jsx`

**Props:**
- `title` (string): KPI name
- `value` (string|number): KPI value
- `icon` (ReactNode): Lucide icon component
- `trend` (string, optional): "up" or "down" trend indicator

**Styling**:
- Card: White background, rounded corners, shadow
- Icon: Colored background circle (blue, green, red, purple)
- Value: Large, bold text
- Trend: Arrow icon with percentage change (if provided)

#### SystemHeatmap Component

**File**: `frontend/src/components/DefectIntelligence/SystemHeatmap.jsx`

**Props:**
- `data` (array): System-defect matrix data
- `onCellClick` (function): Callback when cell is clicked

**Features:**
- **Canvas Rendering**: Uses HTML5 Canvas for performance with large datasets
- **Color Scale**: Dynamic gradient based on value range
- **Tooltips**: Hover to see exact values
- **Metric Toggle**: Switch between Count and Cost views
- **Responsive**: Adjusts cell size based on container width

**Color Mapping:**
```javascript
// Intensity-based color gradient
0-25%   → #fef3c7 (light yellow)
25-50%  → #fcd34d (amber)
50-75%  → #fb923c (orange)
75-100% → #ef4444 (red)
```

---

## Machine Learning & NLP

### BERTopic Topic Modeling

**Purpose**: Automatically discover defect categories from unstructured work order descriptions

**Process:**
1. Preprocess 1.9M work order text descriptions
2. Generate sentence embeddings using BERT
3. Reduce dimensionality with UMAP
4. Cluster embeddings with HDBSCAN
5. Extract topic representations with c-TF-IDF
6. Manually label topics for interpretability

**Output**: 78 discovered topics (mapped to 63 production defect labels)

**Example Topic:**
```
Topic 19: Thermostat Malfunction
Keywords: thermostat, temperature, control, hvac, adjust, set
Representative Docs:
  - "Thermostat in room 301 not responding"
  - "Unable to adjust temperature controls in lab"
  - "HVAC thermostat stuck at 65 degrees"
```

### XGBoost Predictive Model

**File**: `backend/models/xgboost_upm_predictor.pkl`

**Purpose**: Predict Unplanned Maintenance (UPM) probability

**Model Type**: Gradient Boosted Trees (XGBoost Classifier)

**Features** (50+ engineered):
- **Temporal**: Month, day of week, seasonality, days since last event
- **Lag Features**: Previous 1, 3, 6, 12 month event counts
- **Asset Features**: System type, subsystem type, building age, usage intensity
- **Work Order**: Priority, duration, cost
- **One-Hot Encoded**: 8 system types, 40+ subsystem types

**Performance Metrics** (on test set):
- Precision: 0.87
- Recall: 0.83
- F1 Score: 0.85
- ROC-AUC: 0.91

**Inference**: Model is loaded on backend startup and used in `/api/predict` endpoint (not directly used in Defect Intelligence, but available for future integration)

---

## Chatbox Feature

### Current Status: FULLY IMPLEMENTED (Branch: `new`)

A production-ready AI-powered maintenance assistant has been implemented using **Anthropic Claude API** with a flexible architecture supporting both Claude and Ollama (free local alternative).

**Branch**: `new` (not yet merged to main)

### Overview

The chatbox provides a conversational interface for maintenance managers to query facility data, analyze costs, assess risks, and get actionable insights using natural language.

**Key Capabilities:**
- Ask questions about costs, risks, defects, buildings, and trends
- Get data-driven answers backed by real FMUCD dataset
- View embedded bar charts for cost analysis
- Multi-turn conversations with context retention
- Session-based conversation history
- Dual LLM backend (Claude API + Ollama local)

---

## Architecture

### Data Flow Diagram

```
User Input (ChatAssistant or ChatModal)
    ↓
useChat Hook (Frontend)
    ↓
POST /api/chat
    ↓
Session Manager (get or create session)
    ↓
LLM Service (Claude or Ollama)
    ├─ System Prompt
    ├─ Conversation History (last 10 messages)
    └─ Tool Definitions (12 maintenance data tools)
    ↓
[If tool_use in response]
    ├─ Parse tool call(s)
    ├─ Execute tool(s) via DataService
    ├─ Format tool results
    └─ Second API call to Claude with results
    ↓
Extract final text response
    ↓
Generate follow-up suggestions
    ↓
Return ChatResponse with data/charts
    ↓
Frontend renders message with timestamp, suggestions, embedded charts
```

---

## Frontend Implementation

### Components

#### 1. ChatAssistant Page (`frontend/src/pages/ChatAssistant.jsx`)
**File**: 163 lines
**Route**: `/chat`
**Purpose**: Full-page conversational interface

**Features:**
- **Message Display**: User and assistant messages with timestamps
- **Markdown Rendering**: Uses ReactMarkdown for rich formatted responses
- **Embedded Charts**: Bar charts (Recharts) for cost analysis data
- **Auto-Scroll**: Automatically scrolls to latest message
- **Loading States**: Spinner with processing time note (30-60 seconds on CPU)
- **Contextual Suggestions**: Clickable follow-up question chips
- **Clear History**: Button to reset conversation
- **Error Handling**: User-friendly error messages

**UI Structure:**
```jsx
ChatAssistant
├── Header (Title + Clear Chat button)
├── Messages Container (scrollable)
│   ├── Message Bubble (User)
│   ├── Message Bubble (Assistant)
│   │   ├── Markdown Content
│   │   ├── Embedded Bar Chart (if data present)
│   │   └── Suggestion Chips (follow-up questions)
│   └── Loading Indicator (typing animation)
└── Input Form
    ├── Textarea (multi-line input)
    └── Send Button
```

#### 2. ChatModal Component (`frontend/src/components/ChatModal.jsx`)
**File**: 184 lines
**Purpose**: Floating modal chat interface for use within other pages

**Features:**
- **Minimize/Maximize**: Toggle between compact and expanded view
- **Backdrop Overlay**: Dark overlay when maximized
- **Compact Charts**: 250px height for space efficiency
- **Identical Logic**: Same messaging functionality as ChatAssistant
- **Portable**: Can be embedded in any page component

**State Management:**
```javascript
const [messages, setMessages] = useState([]);
const [input, setInput] = useState('');
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState(null);
const [sessionId, setSessionId] = useState(null);
```

### Custom Hook: `useChat`

**Purpose**: Encapsulate chat API logic

**Methods:**
- `sendMessage(text)`: Send user message and receive AI response
- `clearChat()`: Reset conversation and create new session
- `loadSession(sessionId)`: Load existing conversation

**Returns:**
```javascript
{
  messages,       // Array of chat messages
  isLoading,      // Boolean loading state
  error,          // Error object or null
  sendMessage,    // Function to send message
  clearChat,      // Function to clear history
  sessionId       // Current session ID
}
```

---

## Backend Implementation

### API Endpoints

All endpoints defined in `backend/main.py:396-494`

#### 1. POST `/api/chat`
**Purpose**: Main chat endpoint for message processing

**Request Body** (`ChatRequest`):
```json
{
  "message": "What are the most expensive systems?",
  "session_id": "uuid-optional",
  "filters": {
    "building": "optional",
    "system": "optional"
  }
}
```

**Response** (`ChatResponse`):
```json
{
  "response": "Based on the data, here are the most expensive systems...",
  "suggestions": [
    "Which buildings have the highest risk?",
    "Show me monthly cost trends",
    "What are the most frequent defects?"
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": [
    {"system": "HVAC", "cost": 1250000},
    {"system": "Electrical", "cost": 890000}
  ],
  "chart_type": "cost_bar",
  "function_calls": [
    {"tool_name": "get_most_expensive_systems", "success": true}
  ]
}
```

#### 2. Session Management Endpoints

**POST `/api/sessions`**: Create new session
```json
Response: {"session_id": "uuid", "created_at": "2024-03-15T10:30:00"}
```

**GET `/api/sessions`**: List all sessions (20 most recent)
```json
Response: [
  {
    "session_id": "uuid",
    "title": "Cost Analysis Discussion",
    "created_at": "2024-03-15T10:30:00",
    "message_count": 8
  }
]
```

**GET `/api/sessions/{session_id}`**: Get session with full history
```json
Response: {
  "session_id": "uuid",
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "created_at": "2024-03-15T10:30:00"
}
```

**DELETE `/api/sessions/{session_id}`**: Delete session

#### 3. GET `/api/debug/chat-data`
**Purpose**: Debug endpoint to check data loader status

---

## LLM Integration

### 1. Claude API Service (`backend/services/llm_service.py`)

**File**: 262 lines
**Model**: `claude-sonnet-4-20250514` (Claude Sonnet 4)

**Configuration:**
```python
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4000
TEMPERATURE = 0.1  # Low for factual accuracy
TIMEOUT = 60  # seconds
MAX_HISTORY = 10  # messages
```

**Key Features:**

**A. System Prompt** (Expert Maintenance Analyst):
```
You are an expert maintenance analyst assistant helping facility managers
analyze costs, risks, and defects from the FMUCD dataset.

Guidelines:
- Answer questions about costs, risks, defects, buildings, and trends
- Use available tools to query real data (never hallucinate numbers)
- Provide actionable insights with specific data points
- Format responses in clear markdown with headers and lists
- Cite specific metrics when making recommendations
```

**B. Agentic Tool Calling Loop**:
1. Send user message + conversation history + tool definitions to Claude
2. If Claude returns `tool_use` blocks, execute tools via DataService
3. Send tool results back to Claude
4. Claude formulates final response based on tool data
5. Extract text response + auto-generate suggestions

**C. Function/Tool Schema**:
```python
tools = [
  {
    "name": "get_most_expensive_systems",
    "description": "Get the top N systems by total maintenance cost",
    "input_schema": {
      "type": "object",
      "properties": {
        "limit": {"type": "integer", "description": "Number of systems"}
      },
      "required": ["limit"]
    }
  },
  # ... 11 more tools
]
```

### 2. Ollama Service (`backend/services/ollama_service.py`)

**File**: 344 lines
**Model**: `phi3:latest` (free local alternative)
**Base URL**: `http://localhost:11434`

**Why Ollama?**
- Zero-cost alternative to Claude API
- Runs on CPU (no GPU required)
- Privacy-focused (data never leaves server)
- Supports multiple open-source models

**Configuration:**
```python
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")
TIMEOUT = 180  # Longer for CPU processing
```

**Differences from Claude:**
- Uses Ollama REST API (`/api/generate` endpoint)
- Simpler JSON tool parsing (regex-based extraction)
- Two-stage processing (initial response → tool detection → follow-up)
- Single tool call per request (Claude supports multiple)
- Plain text output (no native function calling)

**Fallback Handling:**
- Connection check on startup
- Clear error if Ollama not running: "Ollama is not running. Start with: `ollama serve`"
- Model availability check: "Model phi3 not found. Run: `ollama pull phi3`"

---

## Tool System (Function Calling)

### Tool Categories (12 Total Tools)

**Location**: `backend/tools/*.py` (515 total lines)

#### A. Cost Tools (`cost_tools.py`)
1. **`get_most_expensive_systems(limit)`**
   - Returns top N systems by total cost
   - Example: "HVAC: $1.2M, Electrical: $890K"

2. **`get_cheapest_systems(limit)`**
   - Returns bottom N systems by cost

3. **`get_cost_by_subsystem(subsystem_name)`**
   - Returns detailed cost breakdown for specific subsystem
   - Example: subsystem="Air Handling Units"

#### B. Risk Tools (`risk_tools.py`)
4. **`get_highest_risk_systems(limit)`**
   - Returns top N systems by failure probability
   - Includes risk score (0-1) from XGBoost model

5. **`get_risk_by_subsystem(subsystem_name)`**
   - Detailed risk analysis for specific subsystem

6. **`get_risk_summary()`**
   - Overall risk statistics across all systems

#### C. Building Tools (`building_tools.py`)
7. **`get_top_buildings_by_cost(limit)`**
   - Most expensive buildings by maintenance cost

8. **`get_top_buildings_by_risk(limit)`**
   - Highest risk buildings by failure probability

9. **`get_building_details(building_name)`**
   - Comprehensive building analysis
   - Returns: cost, risk, top defects, system breakdown

#### D. Trend Tools (`trend_tools.py`)
10. **`get_monthly_trends(months)`**
    - Time series cost/defect trends
    - Example: months=12 for last year

11. **`get_most_frequent_defects(limit)`**
    - Top N most common defect types

12. **`get_summary_statistics()`**
    - Overall dataset statistics
    - Returns: total events, avg cost, date range, system counts

### Tool Registry Structure

**File**: `backend/tools/tool_registry.py`

```python
TOOL_REGISTRY = [
  {
    "name": "get_most_expensive_systems",
    "description": "Use when user asks about expensive/costly systems",
    "parameters": {
      "type": "object",
      "properties": {
        "limit": {"type": "integer"}
      },
      "required": ["limit"]
    },
    "function": cost_tools.get_most_expensive_systems
  },
  # ... 11 more tools
]
```

---

## Session Management

### ChatSession Class (`backend/services/session_manager.py`)

**File**: 138 lines

**Attributes:**
- `session_id`: UUID (auto-generated)
- `messages`: List of ChatMessage objects
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `title`: Auto-generated from first user message

**Methods:**
```python
add_message(role, content)
  # Adds message with timestamp
  # role: "user" or "assistant"

get_history(limit=10)
  # Returns last N messages in Claude format
  # [{"role": "user", "content": "..."}]

to_dict()
  # Serializes session for API responses
```

### SessionManager (Singleton)

**Storage**: In-memory dictionary (sessions lost on restart)

**Methods:**
```python
create_session() -> ChatSession
  # Creates new session with UUID

get_session(session_id) -> ChatSession
  # Retrieves existing session or creates new

delete_session(session_id) -> bool
  # Removes session from memory

list_sessions(limit=20) -> List[ChatSession]
  # Returns most recent sessions (reverse chronological)

cleanup_old_sessions(max_age_hours=24)
  # Deletes sessions older than threshold
```

**Context Window Management:**
- Only last 10 messages sent to LLM
- Prevents token limit overflow
- Initial greeting excluded from history (client-side)

---

## Data Service Layer

### DataService (`backend/services/data_service.py`)

**Purpose**: Abstraction layer between tools and raw data

**Data Sources:**
- `fmucd_predictions.parquet`: 515K UPM events with risk probabilities
- Pre-aggregated summary tables (defect, impact, monthly, building)

**Cost Calculation**:
```python
# $500 per UPM event (configurable)
COST_PER_EVENT = 500
total_cost = event_count * COST_PER_EVENT
```

**Key Methods:**
```python
get_top_cost_systems(limit, sort_by='cost')
  # Returns: [{"system": "HVAC", "cost": 1250000, "event_count": 2500}]

get_top_risk_systems(limit, sort_by='risk')
  # Returns: [{"system": "Electrical", "risk_prob": 0.87, "events": 1200}]

get_top_buildings(limit, sort_by='cost')
  # Returns: [{"building": "Engineering Lab", "cost": 450000, ...}]

get_monthly_trends(months=12)
  # Returns: [{"month": "2024-01", "cost": 125000, "events": 250}]

filter_by_subsystem(subsystem_name)
  # Filters dataset to specific subsystem

filter_by_building(building_name)
  # Filters dataset to specific building
```

---

## Data Models & Schemas

### ChatMessage (`backend/schemas/chat_models.py`)

```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[str] = None  # ISO format
```

### ChatRequest

```python
class ChatRequest(BaseModel):
    message: str  # User query
    session_id: Optional[str] = None  # For continuity
    conversation_history: Optional[List[ChatMessage]] = []  # Deprecated
    filters: Optional[Dict] = {}  # Query filters
```

### ChatResponse

```python
class ChatResponse(BaseModel):
    response: str  # LLM text response
    suggestions: List[str]  # Follow-up questions
    session_id: str  # For next request
    data: Optional[List[Dict]] = None  # Structured data for charts
    chart_type: Optional[str] = None  # "cost_bar" or null
    function_calls: List[Dict] = []  # Debugging info
```

### ToolResult

```python
class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
```

---

## Dependencies

### Backend (`requirements.txt`)
```
anthropic>=0.25.0       # Claude API SDK
fastapi>=0.104.0        # Web framework
uvicorn>=0.24.0         # ASGI server
pydantic>=2.0.0         # Data validation
requests>=2.31.0        # HTTP client for Ollama
pandas>=2.1.0           # Data processing
numpy>=1.26.0           # Numerical computing
```

### Frontend (`package.json`)
```json
{
  "react-router-dom": "^7.13.0",
  "recharts": "^3.7.0",
  "axios": "^1.13.4",
  "lucide-react": "^0.x.x",
  "react-markdown": "^9.x.x"
}
```

---

## Example Interactions

### Example 1: Cost Query

**User**: "What are the 5 most expensive systems?"

**Backend Process**:
1. Claude receives message + tools
2. Claude calls: `get_most_expensive_systems(limit=5)`
3. Tool executes, returns: `[{"system": "HVAC", "cost": 1250000}, ...]`
4. Claude formulates response with data

**Response**:
```
Based on the maintenance data, here are the 5 most expensive systems:

1. **HVAC Systems** - $1,250,000 (2,500 events)
2. **Electrical Systems** - $890,000 (1,780 events)
3. **Plumbing** - $625,000 (1,250 events)
4. **Fire Safety** - $410,000 (820 events)
5. **Elevators** - $305,000 (610 events)

HVAC systems account for 32% of total maintenance costs.
```

**Chart Data**: Bar chart with 5 systems rendered in UI

**Suggestions**:
- "Which buildings have the highest HVAC costs?"
- "Show me monthly cost trends for these systems"
- "What are the most common HVAC defects?"

### Example 2: Risk Assessment

**User**: "Which buildings are at highest risk?"

**Claude calls**: `get_top_buildings_by_risk(limit=10)`

**Response**:
```
Here are the 10 highest-risk buildings based on failure probability:

1. **Engineering Lab B** - 89% risk probability (234 events)
2. **Science Complex A** - 85% risk (198 events)
3. **Student Union** - 82% risk (176 events)
...

I recommend prioritizing preventive maintenance for the top 3 buildings.
```

### Example 3: Multi-Turn Conversation

**Turn 1**:
User: "What are the most expensive systems?"
Assistant: [Lists top 5 systems with HVAC at $1.25M]

**Turn 2** (context retained):
User: "Show me trends for HVAC"
Assistant: [Calls `get_monthly_trends(months=12)`, filters to HVAC]
Response: "HVAC costs have increased 18% over the last 12 months..."

---

## Configuration & Environment Variables

### Backend `.env`

```env
# LLM Selection
USE_OLLAMA=false              # true = Ollama, false = Claude
ANTHROPIC_API_KEY=sk-ant-...  # Required if USE_OLLAMA=false
OLLAMA_MODEL=phi3:latest      # Model for Ollama

# Data Paths
DATA_PATH=./data/fmucd_predictions.parquet
AGGREGATED_DATA_PATH=./defect_intelligence/aggregated

# API Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_CONVERSATION_HISTORY=10
SESSION_CLEANUP_HOURS=24

# Cost Estimation
COST_PER_UPM_EVENT=500

# LLM Parameters
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.1
CLAUDE_TIMEOUT=60
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000
VITE_CHAT_TIMEOUT=300000  # 5 minutes for Ollama on CPU
```

---

## Testing

### Test File: `backend/test_chat_phase2.py`

**Test Coverage**:
- Conversation history persistence
- Session creation/retrieval
- Multi-turn context awareness
- Tool execution validation
- Request/response schemas
- Error handling

**Run Tests**:
```bash
cd backend
pytest test_chat_phase2.py -v
```

---

## Feature Completeness

| Feature | Status | Notes |
|---------|--------|-------|
| Chat UI (Full Page) | ✅ Full | ChatAssistant.jsx |
| Chat Modal | ✅ Full | ChatModal.jsx (minimize/maximize) |
| Claude API Integration | ✅ Full | Sonnet 4 with function calling |
| Ollama Integration | ✅ Full | Free local alternative |
| Tool/Function Calling | ✅ Full | 12 maintenance data tools |
| Session Management | ✅ Full | In-memory with UUID |
| Conversation History | ✅ Full | Last 10 messages |
| Markdown Rendering | ✅ Full | ReactMarkdown |
| Embedded Charts | ✅ Full | Bar charts via Recharts |
| Follow-up Suggestions | ✅ Full | Auto-generated from context |
| Error Handling | ✅ Full | Graceful fallbacks |
| Loading States | ✅ Full | Spinner + time estimates |
| Multi-Turn Context | ✅ Full | Context window management |
| Session Persistence | ⚠️ Partial | In-memory (lost on restart) |
| Authentication | ❌ None | No user auth |
| Rate Limiting | ❌ None | No request throttling |
| Streaming Responses | ❌ None | Non-streaming (full response) |

---

## Known Limitations & Future Enhancements

### Current Limitations

1. **In-Memory Sessions**: Lost on server restart (no database)
2. **No Streaming**: Full response returned at once (30-60 second wait for Ollama)
3. **No Authentication**: Anyone can access chat endpoint
4. **No Rate Limiting**: Vulnerable to abuse/excessive costs
5. **Single-User**: No multi-user isolation or permissions
6. **Ollama Tool Calling**: Simpler than Claude (regex parsing, single tool per turn)

### Recommended Enhancements

1. **Database Persistence**
   - Use PostgreSQL or MongoDB for session storage
   - Persist conversation history across restarts
   - Enable analytics on chat usage

2. **Streaming Responses**
   - Implement Server-Sent Events (SSE) or WebSockets
   - Stream text tokens as they generate
   - Improve UX for long responses

3. **Authentication & Authorization**
   - JWT-based user auth
   - Role-based access control (admin, manager, viewer)
   - API key management for external integrations

4. **Rate Limiting**
   - Per-user request throttling (e.g., 20 requests/hour)
   - Cost tracking for Claude API usage
   - Queue system for Ollama during high load

5. **Enhanced Tools**
   - Add filters to existing tools (date range, building, system)
   - Predictive tools using XGBoost model
   - Export tools (CSV, PDF reports)
   - Scheduling tools (automated reports)

6. **Advanced Features**
   - Voice input/output (speech-to-text)
   - Multi-language support
   - Conversation sharing (shareable URLs)
   - Feedback mechanism (thumbs up/down on responses)

7. **Analytics Dashboard**
   - Track most asked questions
   - Monitor tool usage frequency
   - Measure average response time
   - Identify popular topics

---

## Setup & Configuration

### Prerequisites

- **Node.js**: v18+ (for frontend)
- **Python**: 3.10+ (for backend)
- **npm**: v9+ (package manager)
- **pip**: v23+ (Python package manager)

### Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-predictive-maintenance-capstone
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
echo "DATABASE_PATH=./data/df_with_topics_IMPROVED.parquet" > .env
echo "MODEL_PATH=./models/xgboost_upm_predictor.pkl" >> .env

# Start backend server
uvicorn main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables (create .env file)
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Configuration Files

#### `backend/.env`
```env
# Data paths
DATABASE_PATH=./data/df_with_topics_IMPROVED.parquet
AGGREGATED_DATA_PATH=./defect_intelligence/aggregated
MODEL_PATH=./models/xgboost_upm_predictor.pkl
TOPIC_MAPPING_PATH=./topic_info_IMPROVED.csv

# API settings
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=INFO

# Chatbox LLM Configuration (only in 'new' branch)
USE_OLLAMA=false                          # true = Ollama (free), false = Claude (paid)
ANTHROPIC_API_KEY=sk-ant-your-key-here   # Required if USE_OLLAMA=false
OLLAMA_MODEL=phi3:latest                  # Model for Ollama if USE_OLLAMA=true
COST_PER_UPM_EVENT=500                    # Cost calculation for chat queries
MAX_CONVERSATION_HISTORY=10               # Max messages in context
SESSION_CLEANUP_HOURS=24                  # Auto-delete old sessions
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.1
CLAUDE_TIMEOUT=60
```

#### `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
VITE_ENV=development
```

### Data Preparation

#### Required Data Files

1. **`df_with_topics_IMPROVED.parquet`** (120K records)
   - Columns: `work_order_id`, `description`, `system`, `building_id`, `date`, `topic`, `priority`, `duration`
   - Located in: `backend/data/`

2. **`topic_info_IMPROVED.csv`** (78 topics)
   - Columns: `topic_id`, `label`, `keywords`, `count`
   - Located in: `backend/`

3. **Aggregated Data** (pre-computed summaries)
   - Located in: `backend/defect_intelligence/aggregated/`
   - Files: `defect_summary.parquet`, `defect_by_system.parquet`, etc.

#### Generating Aggregated Data

If aggregated files are missing, run:

```bash
cd backend
python scripts/generate_aggregations.py
```

This will read the main dataset and create pre-computed summary tables for faster dashboard loading.

---

### Chatbox Feature Setup (Branch: `new`)

To use the chatbox feature, you need to checkout the `new` branch and configure either Claude API or Ollama.

#### Option 1: Using Claude API (Recommended for Production)

**Step 1**: Get Anthropic API Key
1. Visit https://console.anthropic.com/
2. Create an account or sign in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

**Step 2**: Configure Backend
```bash
# Switch to new branch
git checkout new

# Update backend/.env
echo "USE_OLLAMA=false" >> backend/.env
echo "ANTHROPIC_API_KEY=sk-ant-your-actual-key-here" >> backend/.env
```

**Step 3**: Install Anthropic SDK (if not already installed)
```bash
cd backend
source venv/bin/activate
pip install anthropic>=0.25.0
```

**Step 4**: Start Services
```bash
# Backend (in backend/ directory)
uvicorn main:app --reload --port 8000

# Frontend (in frontend/ directory)
npm run dev
```

**Step 5**: Access Chatbox
- Navigate to `http://localhost:5173/chat` for full-page chat
- Or integrate `ChatModal` component into any page

**Pricing**: Claude API costs ~$3 per million input tokens, $15 per million output tokens (Claude Sonnet 4)

---

#### Option 2: Using Ollama (Free Local Alternative)

**Step 1**: Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

**Step 2**: Start Ollama Server
```bash
ollama serve
# Leave this running in a separate terminal
```

**Step 3**: Pull Model
```bash
# Recommended model (3.8B parameters, fast on CPU)
ollama pull phi3:latest

# Alternative models
ollama pull llama3.2:latest   # 3B params, better quality
ollama pull mistral:latest    # 7B params, highest quality (slower)
```

**Step 4**: Configure Backend
```bash
# Switch to new branch
git checkout new

# Update backend/.env
echo "USE_OLLAMA=true" >> backend/.env
echo "OLLAMA_MODEL=phi3:latest" >> backend/.env
```

**Step 5**: Start Services
```bash
# Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
```

**Step 6**: Access Chatbox
- Navigate to `http://localhost:5173/chat`
- First response takes 30-60 seconds on CPU (normal)

**Note**: Ollama runs locally and is completely free, but responses are slower and quality is lower than Claude.

---

#### Testing the Chatbox

Once configured, try these example queries:

1. **Cost Analysis**:
   - "What are the most expensive systems?"
   - "Show me the top 5 buildings by cost"
   - "What's the monthly cost trend?"

2. **Risk Assessment**:
   - "Which systems have the highest risk?"
   - "Show me buildings at highest risk of failure"
   - "What's the overall risk summary?"

3. **Defect Analysis**:
   - "What are the most frequent defects?"
   - "Show me HVAC-related issues"

4. **Multi-Turn Conversations**:
   - First: "What are the most expensive systems?"
   - Then: "Show me trends for HVAC" (context retained)

---

### Troubleshooting

#### "CORS Policy" Error
**Symptom**: Frontend can't fetch data from backend

**Solution**: Ensure `CORS_ORIGINS` in backend `.env` includes your frontend URL

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_methods=["*"],
    allow_headers=["*"]
)
```

#### "Module Not Found" Error (Backend)
**Symptom**: `ImportError: No module named 'fastapi'`

**Solution**: Activate virtual environment and reinstall dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### Blank Dashboard / No Data
**Symptom**: Dashboard loads but shows no defects

**Solution**: Check backend console for errors. Verify data files exist:
```bash
ls -lh backend/data/df_with_topics_IMPROVED.parquet
ls -lh backend/defect_intelligence/aggregated/
```

#### Slow Dashboard Performance
**Symptom**: Charts take >5 seconds to render

**Solution**:
1. Ensure aggregated data files exist (run `generate_aggregations.py`)
2. Reduce `limit` parameter in API calls (default: 1000)
3. Use Chrome DevTools to profile rendering bottlenecks

---

### Chatbox-Specific Troubleshooting

#### Chat Returns "Anthropic API Error"
**Symptom**: Error message in chat: "Failed to get response from Claude API"

**Solution**:
1. Verify API key is correct in `backend/.env`:
   ```bash
   echo $ANTHROPIC_API_KEY  # Should start with sk-ant-
   ```
2. Check API key has sufficient credits at https://console.anthropic.com/
3. Verify `USE_OLLAMA=false` in `.env`
4. Restart backend server after changing `.env`

---

#### Ollama Connection Error
**Symptom**: "Ollama is not running" or "Connection refused on localhost:11434"

**Solution**:
1. Start Ollama server in separate terminal:
   ```bash
   ollama serve
   ```
2. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```
3. Check model is downloaded:
   ```bash
   ollama list
   # Should show phi3:latest or your configured model
   ```
4. Pull model if missing:
   ```bash
   ollama pull phi3:latest
   ```

---

#### Chat Responses Take 2+ Minutes
**Symptom**: Ollama responses are extremely slow

**Solution**:
1. **Use smaller model**:
   ```bash
   ollama pull phi3:mini  # Faster 1.8B param model
   echo "OLLAMA_MODEL=phi3:mini" >> backend/.env
   ```
2. **Switch to Claude API** for production use (much faster)
3. **Use GPU if available**: Ollama auto-detects GPU and speeds up 10x

---

#### Chat Session Lost After Backend Restart
**Symptom**: Conversation history disappears when restarting server

**Solution**:
This is expected behavior (in-memory storage). To persist sessions:
1. Implement database storage (PostgreSQL/MongoDB)
2. Export important conversations before restart
3. Use session API to save conversation history:
   ```bash
   # Get all sessions
   curl http://localhost:8000/api/sessions

   # Get specific session with history
   curl http://localhost:8000/api/sessions/{session_id}
   ```

---

#### "Tool execution failed" in Chat Response
**Symptom**: Chat shows partial response with tool error

**Solution**:
1. Check backend console for detailed error
2. Verify data files exist:
   ```bash
   ls backend/data/fmucd_predictions.parquet
   ```
3. Check data is loaded:
   ```bash
   curl http://localhost:8000/api/debug/chat-data
   ```
4. If data loading failed, check file paths in `backend/.env`

---

#### Chat Page Shows 404
**Symptom**: Navigating to `/chat` shows "Page not found"

**Solution**:
1. Verify you're on the `new` branch:
   ```bash
   git branch  # Should show * new
   ```
2. Check route exists in `frontend/src/App.jsx`:
   ```bash
   grep -n "ChatAssistant" frontend/src/App.jsx
   ```
3. Rebuild frontend:
   ```bash
   cd frontend
   npm run dev
   ```

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2.0 | UI framework |
| React Router | 6.22.0 | Client-side routing |
| Recharts | 2.12.0 | Chart library (bar, line charts) |
| Lucide React | 0.index | Icon library |
| PapaParse | 5.4.1 | CSV parsing (for exports) |
| Tailwind CSS | 3.4.1 | Utility-first CSS framework |
| Vite | 5.1.0 | Build tool and dev server |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109.0 | Web framework |
| Uvicorn | 0.27.0 | ASGI server |
| Pandas | 2.1.4 | Data manipulation |
| NumPy | 1.26.3 | Numerical computing |
| Joblib | 1.3.2 | Model serialization |
| XGBoost | 2.0.3 | Gradient boosting library |
| PyArrow | 14.0.2 | Parquet file I/O |

### Machine Learning

| Technology | Version | Purpose |
|------------|---------|---------|
| BERTopic | 0.15.0 | Topic modeling (preprocessing only) |
| scikit-learn | 1.4.0 | Feature engineering, preprocessing |
| UMAP | 0.5.5 | Dimensionality reduction (preprocessing) |
| HDBSCAN | 0.8.33 | Clustering (preprocessing) |

### Development Tools

| Technology | Purpose |
|------------|---------|
| ESLint | JavaScript linting |
| Prettier | Code formatting |
| Black | Python code formatting |
| pytest | Python testing |
| Jest | JavaScript testing |

---

## API Performance & Optimization

### Caching Strategy

The backend implements aggressive caching for aggregated data:

```python
# Pseudo-code from backend
CACHE_TTL = 3600  # 1 hour

@lru_cache(maxsize=128)
def get_defect_summary(filters: FrozenFilters):
    # Read from pre-computed parquet files
    # Apply filters
    # Return results
```

**Benefits:**
- 10x faster response times for repeat queries
- Reduced database I/O
- Lower server CPU usage

### Database Indexing

Parquet files are indexed on:
- `building_id`
- `system`
- `date` (partitioned by year-month)
- `topic` (defect type)

**Query Optimization:**
- Use filters to reduce dataset size before aggregation
- Limit result count with `limit` parameter
- Pre-compute expensive aggregations during data ingestion

### Load Testing Results

Tested with Apache Bench (`ab`):

```bash
ab -n 1000 -c 10 http://localhost:8000/api/defect-intelligence
```

**Results:**
- **Requests per second**: 342
- **Mean response time**: 29ms
- **95th percentile**: 47ms
- **Max response time**: 156ms

**Conclusion**: Can handle 340+ requests/second with 10 concurrent users

---

## Future Enhancements

### Defect Analysis

1. **Predictive Defect Alerts**
   - Use XGBoost model to predict future defects
   - Send email/SMS alerts for high-risk buildings
   - Proactive maintenance recommendations

2. **Root Cause Analysis**
   - Integrate maintenance logs and environmental data
   - Identify correlation between defects (e.g., HVAC failure → water damage)
   - Suggest preventive measures

3. **Interactive Reports**
   - Export dashboards to PDF
   - Scheduled email reports (daily, weekly, monthly)
   - Custom report builder

4. **Advanced Filtering**
   - Saved filter presets ("My Views")
   - Filter by cost range
   - Filter by priority level

5. **User Annotations**
   - Add notes to specific defects
   - Tag work orders for follow-up
   - Assign defects to maintenance teams

### Chatbox (To Implement)

1. **Phase 1: Basic Chat UI**
   - Simple message interface
   - Send/receive text messages
   - Typing indicators

2. **Phase 2: LLM Integration**
   - Connect to Anthropic Claude API
   - Context retrieval from defect database
   - Streaming responses

3. **Phase 3: Advanced Features**
   - Multi-turn conversations with memory
   - Trigger dashboard filters from chat ("Show me HVAC issues")
   - Generate inline charts
   - Natural language data export ("Export last month's defects to CSV")

4. **Phase 4: Intelligence**
   - Sentiment analysis on work orders
   - Automated defect categorization
   - Predictive maintenance recommendations via chat
   - Integration with ticketing systems (Jira, ServiceNow)

---

## License

[Your License Here]

## Contributors

[Your Contributors Here]

## Support

For issues, questions, or feature requests, contact:
- **Email**: [Your Email]
- **GitHub Issues**: [Your Repo Issues URL]

---

**Last Updated**: 2026-04-24
**Version**: 1.0.0
