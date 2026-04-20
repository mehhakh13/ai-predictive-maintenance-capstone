# Defect Intelligence API Documentation

## Overview
The Defect Intelligence API serves data from your BERTopic analysis of 120,000 work orders with 78 discovered defect topics.

## Endpoint

### GET `/api/defect-intelligence`

Returns defect data with BERTopic-discovered defect types, costs, and metadata.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `universityId` | string | 'all' | Filter by university ID (10, 12, 20, or 'all') |
| `buildingId` | string | 'all' | Filter by building ID or 'all' |
| `defectType` | string | 'all' | Filter by defect type name or 'all' |
| `system` | string | 'all' | Filter by system description or 'all' |
| `startDate` | string | null | Filter by start date (YYYY-MM-DD) |
| `endDate` | string | null | Filter by end date (YYYY-MM-DD) |
| `limit` | int | 1000 | Maximum records to return |

#### Example Requests

```bash
# Get all defects (limited to 1000)
curl "http://localhost:8000/api/defect-intelligence"

# Get defects for Cornell University
curl "http://localhost:8000/api/defect-intelligence?universityId=10"

# Get HVAC defects
curl "http://localhost:8000/api/defect-intelligence?system=HVAC"

# Get lighting failures
curl "http://localhost:8000/api/defect-intelligence?defectType=Lighting%20System%20Failure"

# Get defects in date range
curl "http://localhost:8000/api/defect-intelligence?startDate=2021-01-01&endDate=2021-12-31"
```

#### Response Format

```json
{
  "data": [
    {
      "WOId": "WO-052513",
      "WODescription": "EMERGENCY: A/C IS NOT WORKING",
      "defect_type": "Thermostat Malfunction",
      "SystemDescription": "HVAC",
      "BuildingID": "261",
      "UniversityID": 11,
      "UniversityName": "Unknown University",
      "BuildingName": "Building 261",
      "TotalCost": 505.63,
      "WOStartDate": "2021-05-28",
      "WOPriority": "nan",
      "Status": "Completed",
      "topic_id": 19
    }
  ],
  "metadata": {
    "universities": [
      {"id": 10, "name": "Cornell University"},
      {"id": 12, "name": "Ohio State University"},
      {"id": 20, "name": "University of Michigan"}
    ],
    "buildings": [
      {"id": "69", "name": "Building 69"}
    ],
    "defectTypes": [
      "Actuator Issue",
      "Alarm System Malfunction",
      "HVAC Temperature Control",
      "Lighting System Failure",
      "..."
    ],
    "systems": [
      "Electrical",
      "HVAC",
      "Plumbing",
      "..."
    ]
  },
  "total_count": 1000
}
```

## Discovered Defect Types

The API discovered **63 unique defect types** from BERTopic analysis, including:

- **HVAC & Temperature** (Topics 1, 19): Temperature control, thermostat failures
- **Lighting** (Topic 0): Light fixtures, bulbs, switches
- **Doors & Locks** (Topic 2): Lock issues, key requests
- **Electrical** (Topics 3, 4): Outlets, power outages, fire alarms
- **Plumbing** (Topics 6, 8, 12, 15, 22): Toilets, drains, sinks, faucets
- **Structural** (Topics 7, 16, 33, 34): Windows, paint, roof, ceiling tiles
- **Equipment** (Topics 9, 21, 38, 46): Refrigeration, pumps, elevators
- **Safety** (Topics 4, 17, 28): Fire alarms, pest control, stairs
- And 45+ more specialized types...

## Cost Calculation

Costs are synthetically generated based on:
- **Base cost by defect complexity** (e.g., lighting: $150, elevators: $3000)
- **Priority multiplier** (high priority = +50% cost)
- **Duration multiplier** (long duration = +30% cost)
- **Random variation** (±20% for realism)

## Topic Mapping

Each defect type maps to a BERTopic topic ID:
- Topic -1: Unclassified Defect
- Topic 0: Lighting System Failure
- Topic 1: HVAC Temperature Control
- Topic 2: Door Lock & Access
- ... (78 total topics)

## Running the Server

```bash
# Start the backend server
cd /home/sradmin/ai-predictive-maintenance-capstone/backend
python3 main.py
```

Server runs on: http://localhost:8000

## Frontend Integration

The React frontend automatically calls this API via the `useDefectData` hook:

```javascript
import { useDefectData } from '../hooks/useDefectData';

const { data, summary, metadata, loading, error } = useDefectData(filters);
```

## Data Source

- **Source**: BERTopic analysis results
- **File**: `data/bertopic/df_with_topics_IMPROVED.parquet`
- **Records**: 120,000 work orders
- **Topics**: 78 discovered defect patterns
- **Outlier Rate**: 17.7% (unclassified defects)
