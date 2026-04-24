import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, AlertCircle, BarChart3, DollarSign } from 'lucide-react';

const HomePage = () => {
  const dashboards = [
    {
      title: 'System Risk Heatmap',
      description: 'View predicted asset-driven UPM risk by system and month. Identify high-risk systems proactively.',
      icon: LayoutDashboard,
      path: '/risk-heatmap',
      color: '#3b82f6',
      featured: true
    },
    {
      title: 'Maintenance Cost Analysis',
      description: 'PPM vs UPM cost impact, top expensive systems, cost trends, and outlier detection.',
      icon: DollarSign,
      path: '/cost-analysis',
      color: '#10b981',
      featured: true
    },
    {
      title: 'Prediction Dashboard',
      description: 'Make predictions for individual assets and work orders.',
      icon: TrendingUp,
      path: '/prediction',
      color: '#8b5cf6'
    },
    {
      title: 'Risk Ranking',
      description: 'Rank buildings and systems by overall risk score.',
      icon: AlertCircle,
      path: '/risk-ranking',
      color: '#f59e0b'
    },
    {
      title: 'Explainability',
      description: 'Understand why the model makes specific predictions.',
      icon: BarChart3,
      path: '/explainability',
      color: '#8b5cf6'
    }
  ];

  return (
    <div className="home-page">
      <div className="home-header">
        <h1 className="home-title">Predictive Maintenance Dashboard</h1>
        <p className="home-subtitle">
          Intelligent asset management and risk prediction for facility maintenance
        </p>
      </div>

      <div className="dashboard-grid">
        {dashboards.map((dashboard, index) => (
          <Link
            key={index}
            to={dashboard.path}
            className={`dashboard-card ${dashboard.featured ? 'featured' : ''}`}
          >
            <div className="card-icon" style={{ backgroundColor: dashboard.color }}>
              <dashboard.icon size={32} color="white" />
            </div>
            <h3 className="card-title">{dashboard.title}</h3>
            <p className="card-description">{dashboard.description}</p>
            <div className="card-footer">
              <span className="card-link">View Dashboard →</span>
            </div>
          </Link>
        ))}
      </div>

      <div className="info-section">
        <div className="info-card">
          <h3>About This System</h3>
          <p>
            This predictive maintenance platform uses machine learning to forecast
            asset-driven UPM (Unscheduled Preventive Maintenance) events. By analyzing
            historical work orders, building characteristics, and weather patterns,
            we can identify high-risk systems before failures occur.
          </p>
        </div>

        <div className="info-card">
          <h3>Key Features</h3>
          <ul>
            <li>Predict asset failure risk by system and month</li>
            <li>Separate shock-driven vs asset-driven failures</li>
            <li>Identify seasonal risk patterns</li>
            <li>Prioritize preventive maintenance activities</li>
            <li>Reduce downtime and repair costs</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
