"""
Trend Analysis Tools - Functions for temporal analysis
"""
from typing import Dict, Any
from services.data_service import get_data_service


def get_monthly_trends(months: int = 12) -> Dict[str, Any]:
    """
    Get monthly maintenance trends for the last N months.

    Args:
        months: Number of recent months to analyze (default: 12)

    Returns:
        Dictionary with monthly trend data
    """
    data_service = get_data_service()
    trends = data_service.get_monthly_trends(months)

    total_cost = sum(t['total_cost'] for t in trends)
    total_events = sum(t['event_count'] for t in trends)
    avg_monthly_cost = total_cost / len(trends) if trends else 0

    return {
        "success": True,
        "data": trends,
        "summary": f"Last {months} months: ${total_cost:,.0f} total cost, "
                  f"{total_events} events, ${avg_monthly_cost:,.0f} avg per month",
        "chart_data": trends  # Can be used for line charts
    }


def get_most_frequent_defects(limit: int = 5) -> Dict[str, Any]:
    """
    Get the most frequently occurring defect types.

    Args:
        limit: Number of top defects to return (default: 5)

    Returns:
        Dictionary with most common defects
    """
    data_service = get_data_service()
    defects = data_service.get_most_frequent_defects(limit)

    return {
        "success": True,
        "data": defects,
        "summary": f"Top {len(defects)} most frequent defects. "
                  f"Total occurrences: {sum(d['event_count'] for d in defects):,}"
    }


def get_summary_statistics() -> Dict[str, Any]:
    """
    Get overall summary statistics for the entire dataset.

    Returns:
        Dictionary with summary stats
    """
    data_service = get_data_service()
    stats = data_service.get_summary_statistics()

    return {
        "success": True,
        "data": stats,
        "summary": f"Dataset: {stats['total_records']:,} records from "
                  f"{stats['total_buildings']} buildings, "
                  f"{stats['date_range']['start']} to {stats['date_range']['end']}"
    }


# Tool registry
TREND_TOOLS = [
    {
        "name": "get_monthly_trends",
        "description": "Get monthly maintenance trends over time. Use when user asks about trends, patterns over time, or historical data.",
        "parameters": {
            "type": "object",
            "properties": {
                "months": {
                    "type": "integer",
                    "description": "Number of recent months to analyze (default: 12, max: 60)",
                    "default": 12
                }
            }
        },
        "function": get_monthly_trends
    },
    {
        "name": "get_most_frequent_defects",
        "description": "Get the most frequently occurring defect types. Use when user asks about common problems or frequent issues.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top defects to return (default: 5)",
                    "default": 5
                }
            }
        },
        "function": get_most_frequent_defects
    },
    {
        "name": "get_summary_statistics",
        "description": "Get overall summary statistics for the dataset. Use when user asks about overall stats, dataset info, or general overview.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "function": get_summary_statistics
    }
]
