"""
Data Service Layer - Handles all data access and queries for FMUCD dataset
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import config


class DataService:
    """Service for accessing and querying FMUCD maintenance data"""

    def __init__(self):
        self.df_predictions = None
        self.df_defect_summary = None
        self.df_impact_summary = None
        self.df_monthly_summary = None
        self.df_building_summary = None
        self._load_data()

    def _load_data(self):
        """Load and prepare all datasets"""
        try:
            print("Loading FMUCD predictions data...")
            self.df_predictions = pd.read_parquet(config.PREDICTIONS_DATA_PATH)

            # Add estimated costs
            self.df_predictions['estimated_cost'] = (
                self.df_predictions['UPM_total_event'] * config.COST_PER_UPM_EVENT
            )

            # Create summary tables
            self._create_summaries()

            print(f"✓ Data loaded: {len(self.df_predictions):,} records")
            print(f"✓ Buildings: {self.df_predictions['BuildingName'].nunique()}")
            print(f"✓ Subsystems: {self.df_predictions['SubsystemDescription'].nunique()}")

        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def _create_summaries(self):
        """Create pre-aggregated summary tables"""

        # Defect/Subsystem summary
        self.df_defect_summary = self.df_predictions.groupby('SubsystemDescription').agg({
            'estimated_cost': ['sum', 'mean'],
            'UPM_total_event': 'sum',
            'risk_prob_asset': 'mean'
        }).reset_index()
        self.df_defect_summary.columns = [
            'subsystem', 'total_cost', 'avg_cost', 'event_count', 'avg_risk'
        ]
        self.df_defect_summary['event_count'] = self.df_defect_summary['event_count'].astype(int)

        # Risk/Impact summary
        self.df_impact_summary = self.df_defect_summary.copy()
        self.df_impact_summary['total_impact'] = (
            self.df_impact_summary['avg_risk'] * self.df_impact_summary['event_count']
        )

        # Monthly summary
        self.df_monthly_summary = self.df_predictions.groupby('month_date').agg({
            'estimated_cost': 'sum',
            'UPM_total_event': 'sum',
            'risk_prob_asset': 'mean'
        }).reset_index()
        self.df_monthly_summary.columns = ['month', 'total_cost', 'event_count', 'avg_risk']
        self.df_monthly_summary = self.df_monthly_summary.sort_values('month')

        # Building summary
        group_cols = ['BuildingID', 'BuildingName']
        if 'UniversityID' in self.df_predictions.columns:
            group_cols.append('UniversityID')

        self.df_building_summary = self.df_predictions.groupby(group_cols).agg({
            'UPM_total_event': 'sum',
            'estimated_cost': 'sum',
            'risk_prob_asset': 'mean'
        }).reset_index()
        self.df_building_summary.columns = [
            *group_cols, 'event_count', 'total_cost', 'avg_risk'
        ]
        self.df_building_summary['event_count'] = self.df_building_summary['event_count'].astype(int)

    # ==================== QUERY METHODS ====================

    def get_top_cost_systems(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top N systems by total cost"""
        top_systems = self.df_defect_summary.nlargest(limit, 'total_cost')

        return [
            {
                'subsystem': row['subsystem'],
                'total_cost': float(row['total_cost']),
                'avg_cost': float(row['avg_cost']),
                'event_count': int(row['event_count'])
            }
            for _, row in top_systems.iterrows()
        ]

    def get_top_risk_systems(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top N systems by risk probability"""
        top_risk = self.df_impact_summary.nlargest(limit, 'avg_risk')

        return [
            {
                'subsystem': row['subsystem'],
                'risk_probability': float(row['avg_risk']),
                'event_count': int(row['event_count']),
                'total_cost': float(row['total_cost'])
            }
            for _, row in top_risk.iterrows()
        ]

    def get_top_buildings(self, limit: int = 5, sort_by: str = 'total_cost') -> List[Dict[str, Any]]:
        """Get top N buildings by specified metric"""
        top_buildings = self.df_building_summary.nlargest(limit, sort_by)

        return [
            {
                'building_id': row['BuildingID'],
                'building_name': row['BuildingName'],
                'university_id': row.get('UniversityID', 'Unknown'),
                'event_count': int(row['event_count']),
                'total_cost': float(row['total_cost']),
                'avg_risk': float(row['avg_risk'])
            }
            for _, row in top_buildings.iterrows()
        ]

    def get_monthly_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly trend data for last N months"""
        recent = self.df_monthly_summary.tail(months)

        return [
            {
                'month': row['month'].strftime('%Y-%m'),
                'total_cost': float(row['total_cost']),
                'event_count': int(row['event_count']),
                'avg_risk': float(row['avg_risk'])
            }
            for _, row in recent.iterrows()
        ]

    def get_most_frequent_defects(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently occurring defect types"""
        top_frequent = self.df_defect_summary.nlargest(limit, 'event_count')

        total_events = self.df_defect_summary['event_count'].sum()

        return [
            {
                'subsystem': row['subsystem'],
                'event_count': int(row['event_count']),
                'percentage': float((row['event_count'] / total_events) * 100),
                'avg_cost': float(row['avg_cost'])
            }
            for _, row in top_frequent.iterrows()
        ]

    def filter_by_subsystem(self, subsystem: str) -> pd.DataFrame:
        """Filter data by subsystem name (fuzzy match)"""
        mask = self.df_predictions['SubsystemDescription'].str.contains(
            subsystem, case=False, na=False
        )
        return self.df_predictions[mask]

    def filter_by_building(self, building_name: str) -> pd.DataFrame:
        """Filter data by building name (fuzzy match)"""
        mask = self.df_predictions['BuildingName'].str.contains(
            building_name, case=False, na=False
        )
        return self.df_predictions[mask]

    def filter_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Filter data by date range"""
        mask = (
            (self.df_predictions['month_date'] >= start_date) &
            (self.df_predictions['month_date'] <= end_date)
        )
        return self.df_predictions[mask]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get overall summary statistics"""
        return {
            'total_records': len(self.df_predictions),
            'total_buildings': self.df_predictions['BuildingName'].nunique(),
            'total_subsystems': self.df_predictions['SubsystemDescription'].nunique(),
            'date_range': {
                'start': self.df_predictions['month_date'].min().strftime('%Y-%m-%d'),
                'end': self.df_predictions['month_date'].max().strftime('%Y-%m-%d')
            },
            'total_cost': float(self.df_predictions['estimated_cost'].sum()),
            'total_events': int(self.df_predictions['UPM_total_event'].sum()),
            'avg_risk': float(self.df_predictions['risk_prob_asset'].mean())
        }


# Singleton instance
_data_service = None

def get_data_service() -> DataService:
    """Get or create the data service singleton"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
