"""
Risk Analysis Tools - Functions the LLM can call to analyze risk
"""
from typing import Dict, Any
from services.data_service import get_data_service


def get_highest_risk_systems(limit: int = 5) -> Dict[str, Any]:
    """
    Get the top N systems with highest failure risk probability.

    Args:
        limit: Number of top risky systems to return (default: 5)

    Returns:
        Dictionary with list of high-risk systems
    """
    data_service = get_data_service()
    systems = data_service.get_top_risk_systems(limit)

    return {
        "success": True,
        "data": systems,
        "summary": f"Found {len(systems)} highest risk systems. "
                  f"Average risk: {sum(s['risk_probability'] for s in systems)/len(systems)*100:.1f}%"
    }


def get_risk_by_subsystem(subsystem_name: str) -> Dict[str, Any]:
    """
    Get risk analysis for a specific subsystem.

    Args:
        subsystem_name: Name of the subsystem

    Returns:
        Dictionary with risk details for the subsystem
    """
    data_service = get_data_service()
    df_filtered = data_service.filter_by_subsystem(subsystem_name)

    if len(df_filtered) == 0:
        return {
            "success": False,
            "error": f"No data found for subsystem: {subsystem_name}"
        }

    avg_risk = df_filtered['risk_prob_asset'].mean()
    max_risk = df_filtered['risk_prob_asset'].max()
    min_risk = df_filtered['risk_prob_asset'].min()
    total_events = df_filtered['UPM_total_event'].sum()

    # Calculate risk level
    if avg_risk > 0.3:
        risk_level = "High"
    elif avg_risk > 0.15:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "success": True,
        "data": {
            "subsystem": subsystem_name,
            "avg_risk_probability": float(avg_risk),
            "max_risk_probability": float(max_risk),
            "min_risk_probability": float(min_risk),
            "risk_level": risk_level,
            "total_events": int(total_events),
            "record_count": len(df_filtered)
        },
        "summary": f"{subsystem_name}: {risk_level} risk ({avg_risk*100:.1f}% probability)"
    }


# Tool registry
RISK_TOOLS = [
    {
        "name": "get_highest_risk_systems",
        "description": "Get the top N systems with highest risk of failure. Use when user asks about risky systems, high-risk equipment, or failure probability.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top risky systems to return (default: 5)",
                    "default": 5
                }
            }
        },
        "function": get_highest_risk_systems
    },
    {
        "name": "get_risk_by_subsystem",
        "description": "Get risk analysis for a specific subsystem. Use when user asks about risk for a specific system like HVAC, Plumbing, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "subsystem_name": {
                    "type": "string",
                    "description": "Name of the subsystem (e.g., 'HVAC', 'Plumbing', 'Electrical')"
                }
            },
            "required": ["subsystem_name"]
        },
        "function": get_risk_by_subsystem
    }
]
