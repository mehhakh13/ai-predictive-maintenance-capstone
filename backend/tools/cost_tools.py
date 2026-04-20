"""
Cost Analysis Tools - Functions the LLM can call to analyze costs
"""
from typing import Dict, Any, List
from services.data_service import get_data_service


def get_most_expensive_systems(limit: int = 5) -> Dict[str, Any]:
    """
    Get the top N most expensive systems/subsystems by total cost.

    Args:
        limit: Number of top systems to return (default: 5)

    Returns:
        Dictionary with list of expensive systems and chart data
    """
    data_service = get_data_service()
    systems = data_service.get_top_cost_systems(limit)

    return {
        "success": True,
        "data": systems,
        "chart_data": [
            {
                "category": s['subsystem'][:30],
                "total_cost": s['total_cost'],
                "count": s['event_count']
            }
            for s in systems
        ],
        "summary": f"Found {len(systems)} most expensive systems. "
                  f"Total cost: ${sum(s['total_cost'] for s in systems):,.0f}"
    }


def get_cheapest_systems(limit: int = 5) -> Dict[str, Any]:
    """
    Get the top N least expensive systems/subsystems.

    Args:
        limit: Number of systems to return (default: 5)

    Returns:
        Dictionary with list of cheapest systems
    """
    data_service = get_data_service()
    # Get all systems and sort by cost ascending
    all_systems = data_service.get_top_cost_systems(100)
    cheapest = sorted(all_systems, key=lambda x: x['total_cost'])[:limit]

    return {
        "success": True,
        "data": cheapest,
        "summary": f"Found {len(cheapest)} least expensive systems."
    }


def get_cost_by_subsystem(subsystem_name: str) -> Dict[str, Any]:
    """
    Get cost details for a specific subsystem.

    Args:
        subsystem_name: Name of the subsystem (e.g., "HVAC", "Plumbing")

    Returns:
        Dictionary with cost breakdown for the subsystem
    """
    data_service = get_data_service()
    df_filtered = data_service.filter_by_subsystem(subsystem_name)

    if len(df_filtered) == 0:
        return {
            "success": False,
            "error": f"No data found for subsystem: {subsystem_name}"
        }

    total_cost = df_filtered['estimated_cost'].sum()
    event_count = df_filtered['UPM_total_event'].sum()
    avg_risk = df_filtered['risk_prob_asset'].mean()

    return {
        "success": True,
        "data": {
            "subsystem": subsystem_name,
            "total_cost": float(total_cost),
            "event_count": int(event_count),
            "avg_cost_per_event": float(total_cost / event_count) if event_count > 0 else 0,
            "avg_risk": float(avg_risk),
            "record_count": len(df_filtered)
        },
        "summary": f"{subsystem_name}: ${total_cost:,.0f} total cost, {int(event_count)} events"
    }


# Tool registry for LLM
COST_TOOLS = [
    {
        "name": "get_most_expensive_systems",
        "description": "Get the top N most expensive systems or subsystems by total maintenance cost. Use this when user asks about expensive systems, highest costs, or which systems cost the most money.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top systems to return (default: 5, max: 20)",
                    "default": 5
                }
            }
        },
        "function": get_most_expensive_systems
    },
    {
        "name": "get_cheapest_systems",
        "description": "Get the top N least expensive systems. Use when user asks about cheapest systems or lowest cost systems.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of systems to return (default: 5)",
                    "default": 5
                }
            }
        },
        "function": get_cheapest_systems
    },
    {
        "name": "get_cost_by_subsystem",
        "description": "Get detailed cost information for a specific subsystem like HVAC, Plumbing, Electrical, etc. Use when user asks about costs for a specific system.",
        "parameters": {
            "type": "object",
            "properties": {
                "subsystem_name": {
                    "type": "string",
                    "description": "Name of the subsystem (e.g., 'HVAC', 'Plumbing', 'Electrical', 'Lighting')"
                }
            },
            "required": ["subsystem_name"]
        },
        "function": get_cost_by_subsystem
    }
]
