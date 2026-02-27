#!/usr/bin/env python3
"""
PredicX - Predictive Maintenance Dashboard
Explainable AI-powered maintenance risk intelligence platform
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add scripts to path
sys.path.append('/home/sradmin/ai-predictive-maintenance-capstone/scripts')

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="PredicX - Predictive Maintenance",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .risk-high {
        color: #d62728;
        font-weight: bold;
    }
    .risk-medium {
        color: #ff7f0e;
        font-weight: bold;
    }
    .risk-low {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Load trained XGBoost model"""
    model_path = "/home/sradmin/ai-predictive-maintenance-capstone/models/xgboost_upm_predictor.pkl"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None


@st.cache_data
def load_processed_data():
    """Load processed features and metadata"""
    data_dir = "/home/sradmin/ai-predictive-maintenance-capstone/data/processed"

    if not os.path.exists(data_dir):
        return None, None, None

    X = pd.read_csv(f"{data_dir}/X_features.csv")
    y = pd.read_csv(f"{data_dir}/y_target.csv").squeeze()
    metadata = pd.read_csv(f"{data_dir}/metadata.csv")

    return X, y, metadata


@st.cache_data
def load_feature_importance():
    """Load feature importance data"""
    importance_path = "/home/sradmin/ai-predictive-maintenance-capstone/models/feature_importance.csv"
    if os.path.exists(importance_path):
        return pd.read_csv(importance_path)
    return None


def get_risk_level(probability):
    """Classify risk level based on UPM probability"""
    if probability >= 0.7:
        return "High", "#d62728"
    elif probability >= 0.4:
        return "Medium", "#ff7f0e"
    else:
        return "Low", "#2ca02c"


def create_risk_heatmap(metadata, predictions):
    """
    Visualization 1: Risk Heatmap (Systems × Months)
    Shows UPM probability for each system across months
    """
    st.subheader("🔥 Risk Heatmap: Systems × Time")
    st.markdown("**Which systems are most risky during which months?**")

    # Combine metadata with predictions
    df = metadata.copy()
    df['upm_probability'] = predictions

    # Pivot table: Systems (rows) × Months (columns)
    heatmap_data = df.pivot_table(
        index='system_description',
        columns='month',
        values='upm_probability',
        aggfunc='mean'
    )

    # Sort by average risk
    heatmap_data['avg_risk'] = heatmap_data.mean(axis=1)
    heatmap_data = heatmap_data.sort_values('avg_risk', ascending=False)
    heatmap_data = heatmap_data.drop('avg_risk', axis=1)

    # Take top 15 systems
    heatmap_data = heatmap_data.head(15)

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y=heatmap_data.index,
        colorscale='RdYlGn_r',
        zmid=0.5,
        text=np.round(heatmap_data.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="UPM Risk")
    ))

    fig.update_layout(
        title="Monthly UPM Risk by System Type",
        xaxis_title="Month",
        yaxis_title="System",
        height=600,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)


def create_monthly_predictions(metadata, predictions):
    """
    Visualization 2: Monthly UPM/PPM Predictions
    Time series showing predicted UPM and PPM counts
    """
    st.subheader("📊 Monthly Maintenance Predictions")
    st.markdown("**Expected UPM and PPM work orders over time**")

    # Combine data
    df = metadata.copy()
    df['upm_probability'] = predictions
    df['predicted_upm'] = df['total_wo_count'] * df['upm_probability']
    df['predicted_ppm'] = df['total_wo_count'] * (1 - df['upm_probability'])

    # Group by year-month
    df['year_month'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    monthly = df.groupby('year_month').agg({
        'predicted_upm': 'sum',
        'predicted_ppm': 'sum',
        'upm_count': 'sum',
        'ppm_count': 'sum'
    }).reset_index()

    # Create figure
    fig = go.Figure()

    # Predicted UPM
    fig.add_trace(go.Scatter(
        x=monthly['year_month'],
        y=monthly['predicted_upm'],
        mode='lines+markers',
        name='Predicted UPM',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8)
    ))

    # Predicted PPM
    fig.add_trace(go.Scatter(
        x=monthly['year_month'],
        y=monthly['predicted_ppm'],
        mode='lines+markers',
        name='Predicted PPM',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8)
    ))

    # Actual UPM (historical)
    fig.add_trace(go.Scatter(
        x=monthly['year_month'],
        y=monthly['upm_count'],
        mode='markers',
        name='Actual UPM',
        marker=dict(color='#d62728', size=6, symbol='x'),
        opacity=0.5
    ))

    # Actual PPM (historical)
    fig.add_trace(go.Scatter(
        x=monthly['year_month'],
        y=monthly['ppm_count'],
        mode='markers',
        name='Actual PPM',
        marker=dict(color='#2ca02c', size=6, symbol='x'),
        opacity=0.5
    ))

    fig.update_layout(
        title="Monthly Maintenance Forecast",
        xaxis_title="Month",
        yaxis_title="Number of Work Orders",
        height=500,
        hovermode='x unified',
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Avg Monthly UPM", f"{monthly['predicted_upm'].mean():.0f}")
    with col2:
        st.metric("Avg Monthly PPM", f"{monthly['predicted_ppm'].mean():.0f}")
    with col3:
        upm_trend = monthly['predicted_upm'].iloc[-3:].mean() - monthly['predicted_upm'].iloc[:3].mean()
        st.metric("UPM Trend", f"{upm_trend:+.0f}", delta_color="inverse")
    with col4:
        total_predicted = monthly['predicted_upm'].sum() + monthly['predicted_ppm'].sum()
        st.metric("Total Predicted WOs", f"{total_predicted:.0f}")


def create_cost_dashboard(metadata, predictions):
    """
    Visualization 3: Projected Cost Dashboard
    Cost analysis based on UPM vs PPM predictions
    """
    st.subheader("💰 Projected Cost Analysis")
    st.markdown("**Financial impact of predicted maintenance activities**")

    # Combine data
    df = metadata.copy()
    df['upm_probability'] = predictions
    df['predicted_upm_cost'] = df['total_monthly_cost'] * df['upm_probability']
    df['predicted_ppm_cost'] = df['total_monthly_cost'] * (1 - df['upm_probability'])

    col1, col2 = st.columns(2)

    with col1:
        # Cost by system type
        system_costs = df.groupby('system_description').agg({
            'predicted_upm_cost': 'sum',
            'predicted_ppm_cost': 'sum'
        }).reset_index()

        system_costs['total_cost'] = (system_costs['predicted_upm_cost'] +
                                      system_costs['predicted_ppm_cost'])
        system_costs = system_costs.sort_values('total_cost', ascending=False).head(10)

        fig_system = go.Figure()
        fig_system.add_trace(go.Bar(
            name='UPM Cost',
            x=system_costs['system_description'],
            y=system_costs['predicted_upm_cost'],
            marker_color='#d62728'
        ))
        fig_system.add_trace(go.Bar(
            name='PPM Cost',
            x=system_costs['system_description'],
            y=system_costs['predicted_ppm_cost'],
            marker_color='#2ca02c'
        ))

        fig_system.update_layout(
            barmode='stack',
            title="Top 10 Systems by Projected Cost",
            xaxis_title="System",
            yaxis_title="Cost ($)",
            height=400,
            xaxis_tickangle=-45,
            template="plotly_white"
        )

        st.plotly_chart(fig_system, use_container_width=True)

    with col2:
        # Monthly cost trend
        df['year_month'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        monthly_cost = df.groupby('year_month').agg({
            'predicted_upm_cost': 'sum',
            'predicted_ppm_cost': 'sum'
        }).reset_index()

        fig_monthly = go.Figure()
        fig_monthly.add_trace(go.Scatter(
            x=monthly_cost['year_month'],
            y=monthly_cost['predicted_upm_cost'],
            fill='tonexty',
            name='UPM Cost',
            line=dict(color='#d62728')
        ))
        fig_monthly.add_trace(go.Scatter(
            x=monthly_cost['year_month'],
            y=monthly_cost['predicted_ppm_cost'],
            fill='tozeroy',
            name='PPM Cost',
            line=dict(color='#2ca02c')
        ))

        fig_monthly.update_layout(
            title="Monthly Cost Forecast",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            height=400,
            template="plotly_white"
        )

        st.plotly_chart(fig_monthly, use_container_width=True)

    # Cost metrics
    col1, col2, col3, col4 = st.columns(4)

    total_upm_cost = df['predicted_upm_cost'].sum()
    total_ppm_cost = df['predicted_ppm_cost'].sum()
    total_cost = total_upm_cost + total_ppm_cost

    with col1:
        st.metric("Total Projected Cost", f"${total_cost:,.0f}")
    with col2:
        st.metric("UPM Cost", f"${total_upm_cost:,.0f}",
                 delta=f"{total_upm_cost/total_cost*100:.1f}%", delta_color="inverse")
    with col3:
        st.metric("PPM Cost", f"${total_ppm_cost:,.0f}",
                 delta=f"{total_ppm_cost/total_cost*100:.1f}%")
    with col4:
        savings_potential = total_upm_cost * 0.3  # Assume 30% savings if converted to PPM
        st.metric("Potential Savings", f"${savings_potential:,.0f}")


def create_shap_explainability(feature_importance):
    """
    Visualization 4: SHAP Explainability Panel
    Show which features drive predictions
    """
    st.subheader("🔍 Model Explainability: Feature Importance")
    st.markdown("**Why does the model predict high risk? Key contributing factors**")

    if feature_importance is None:
        st.warning("Feature importance data not available. Train the model first.")
        return

    # Top 15 features
    top_features = feature_importance.head(15)

    # Create horizontal bar chart
    fig = go.Figure(go.Bar(
        x=top_features['importance'],
        y=top_features['feature'],
        orientation='h',
        marker=dict(
            color=top_features['importance'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Importance")
        )
    ))

    fig.update_layout(
        title="Top 15 Most Important Features for UPM Prediction",
        xaxis_title="Feature Importance Score",
        yaxis_title="Feature",
        height=500,
        template="plotly_white",
        yaxis={'categoryorder': 'total ascending'}
    )

    st.plotly_chart(fig, use_container_width=True)

    # Feature interpretation
    st.markdown("### 📋 Feature Impact Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Temporal Factors:**")
        temporal_features = top_features[
            top_features['feature'].str.contains('month|season', case=False, na=False)
        ]
        if not temporal_features.empty:
            for _, row in temporal_features.iterrows():
                st.markdown(f"- {row['feature']}: {row['importance']:.4f}")
        else:
            st.markdown("- No temporal features in top 15")

        st.markdown("**Weather Factors:**")
        weather_features = top_features[
            top_features['feature'].str.contains('temp|humidity|snow|wind|precipitation', case=False, na=False)
        ]
        if not weather_features.empty:
            for _, row in weather_features.iterrows():
                st.markdown(f"- {row['feature']}: {row['importance']:.4f}")
        else:
            st.markdown("- No weather features in top 15")

    with col2:
        st.markdown("**System Factors:**")
        system_features = top_features[
            top_features['feature'].str.contains('is_|system', case=False, na=False)
        ]
        if not system_features.empty:
            for _, row in system_features.iterrows():
                st.markdown(f"- {row['feature']}: {row['importance']:.4f}")
        else:
            st.markdown("- No system features in top 15")

        st.markdown("**Historical Factors:**")
        historical_features = top_features[
            top_features['feature'].str.contains('historical|count|rate', case=False, na=False)
        ]
        if not historical_features.empty:
            for _, row in historical_features.iterrows():
                st.markdown(f"- {row['feature']}: {row['importance']:.4f}")
        else:
            st.markdown("- No historical features in top 15")


def main():
    """Main Streamlit app"""

    # Header
    st.markdown('<div class="main-header">PredicX</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Explainable Predictive Maintenance & Risk Intelligence Platform</div>',
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=PredicX", width=150)
        st.markdown("---")

        st.markdown("### 🎯 About")
        st.markdown("""
        PredicX uses machine learning to predict unplanned maintenance (UPM) risks
        before they happen, helping campuses reduce costs and improve facility reliability.
        """)

        st.markdown("---")
        st.markdown("### 📊 Data Source")
        data_source = st.selectbox(
            "Select Dataset",
            ["Canada Campus", "California Campus", "Combined"]
        )

        st.markdown("---")
        st.markdown("### ⚙️ Model Info")
        st.markdown("""
        - **Algorithm**: XGBoost Classifier
        - **Granularity**: System-Month Level
        - **Features**: 30+ engineered features
        - **Target**: UPM Probability
        """)

    # Check if model and data are available
    model = load_model()
    X, y, metadata = load_processed_data()
    feature_importance = load_feature_importance()

    if model is None or X is None:
        st.error("⚠️ Model or data not found. Please run the training pipeline first.")
        st.markdown("""
        ### Setup Instructions:
        1. Run feature engineering: `python scripts/feature_engineering.py`
        2. Train model: `python scripts/train_model.py`
        3. Refresh this dashboard
        """)
        return

    # Make predictions
    predictions = model.predict_proba(X)[:, 1]

    # Overall metrics
    st.markdown("---")
    st.markdown("### 📈 Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        avg_upm_prob = predictions.mean()
        risk_level, risk_color = get_risk_level(avg_upm_prob)
        st.metric("Avg UPM Risk", f"{avg_upm_prob:.1%}",
                 delta=risk_level, delta_color="inverse")

    with col2:
        high_risk_count = (predictions >= 0.7).sum()
        st.metric("High Risk Systems", f"{high_risk_count}")

    with col3:
        total_systems = metadata['system_description'].nunique()
        st.metric("Systems Monitored", f"{total_systems}")

    with col4:
        total_months = len(metadata)
        st.metric("System-Months", f"{total_months}")

    with col5:
        total_cost = metadata['total_monthly_cost'].sum()
        st.metric("Total Cost", f"${total_cost:,.0f}")

    st.markdown("---")

    # Visualization 1: Risk Heatmap
    create_risk_heatmap(metadata, predictions)

    st.markdown("---")

    # Visualization 2: Monthly Predictions
    create_monthly_predictions(metadata, predictions)

    st.markdown("---")

    # Visualization 3: Cost Dashboard
    create_cost_dashboard(metadata, predictions)

    st.markdown("---")

    # Visualization 4: SHAP Explainability
    create_shap_explainability(feature_importance)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">PredicX Dashboard - Group 09 | '
        'Powered by XGBoost & Streamlit</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
