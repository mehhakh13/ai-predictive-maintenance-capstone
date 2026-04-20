"""
Building Analysis Tools - Functions for building-level analysis
"""
from typing import Dict, Any
from services.data_service import get_data_service


def get_top_buildings_by_cost(limit: int = 5) -> Dict[str, Any]:
    """
    Get buildings with highest maintenance costs.

    Args:
        limit: Number of buildings to return (default: 5)

    Returns:
        Dictionary with list of expensive buildings
    """
    data_service = get_data_service()
    buildings = data_service.get_top_buildings(limit, sort_by='total_cost')

    return {
        "success": True,
        "data": buildings,
        "summary": f"Found {len(buildings)} buildings with highest costs. "
                  f"Total: ${sum(b['total_cost'] for b in buildings):,.0f}"
    }


def get_top_buildings_by_risk(limit: int = 5) -> Dict[str, Any]:
    """
    Get buildings with highest average risk.

    Args:
        limit: Number of buildings to return (default: 5)

    Returns:
        Dictionary with list of high-risk buildings
    """
    data_service = get_data_service()
    buildings = data_service.get_top_buildings(limit, sort_by='avg_risk')

    return {
        "success": True,
        "data": buildings,
        "summary": f"Found {len(buildings)} buildings with highest risk levels."
    }


def get_building_details(building_name: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific building.

    Args:
        building_name: Name or partial name of the building

    Returns:
        Dictionary with building details
    """
    data_service = get_data_service()
    df_filtered = data_service.filter_by_building(building_name)

    if len(df_filtered) == 0:
        return {
            "success": False,
            "error": f"No data found for building: {building_name}"
        }

    total_cost = df_filtered['estimated_cost'].sum()
    total_events = df_filtered['UPM_total_event'].sum()
    avg_risk = df_filtered['risk_prob_asset'].mean()

    # Get top subsystems in this building
    subsystem_summary = df_filtered.groupby('SubsystemDescription').agg({
        'UPM_total_event': 'sum',
        'estimated_cost': 'sum'
    }).nlargest(5, 'estimated_cost')

    top_subsystems = [
        {
            "subsystem": idx,
            "events": int(row['UPM_total_event']),
            "cost": float(row['estimated_cost'])
        }
        for idx, row in subsystem_summary.iterrows()
    ]

    return {
        "success": True,
        "data": {
            "building_name": building_name,
            "total_cost": float(total_cost),
            "total_events": int(total_events),
            "avg_risk": float(avg_risk),
            "record_count": len(df_filtered),
            "top_problem_subsystems": top_subsystems
        },
        "summary": f"{building_name}: ${total_cost:,.0f}, {int(total_events)} events, "
                  f"{avg_risk*100:.1f}% avg risk"
    }


# Tool registry
BUILDING_TOOLS = [
    {
        "name": "get_top_buildings_by_cost",
        "description": "Get buildings with the highest maintenance costs. Use when user asks about expensive buildings or which facilities cost the most.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of buildings to return (default: 5)",
                    "default": 5
                }
            }
        },
        "function": get_top_buildings_by_cost
    },
    {
        "name": "get_top_buildings_by_risk",
        "description": "Get buildings with highest risk levels. Use when user asks about risky buildings or which facilities need attention.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of buildings to return (default: 5)",
                    "default": 5
                }
            }
        },
        "function": get_top_buildings_by_risk
    },
    {
        "name": "get_building_details",
        "description": "Get detailed analysis for a specific building. Use when user asks about a specific building by name.",
        "parameters": {
            "type": "object",
            "properties": {
                "building_name": {
                    "type": "string",
                    "description": "Name or partial name of the building"
                }
            },
            "required": ["building_name"]
        },
        "function": get_building_details
    }
]
