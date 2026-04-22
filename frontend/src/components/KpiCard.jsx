import React from 'react';

const KpiCard = ({ title, value, subtitle, icon: Icon, trend, trendValue }) => {
  return (
    <div className="kpi-card">
      <div className="kpi-card-header">
        <span className="kpi-card-title">{title}</span>
        {Icon && <Icon className="kpi-card-icon" size={20} />}
      </div>
      <div className="kpi-card-value">{value}</div>
      {subtitle && <div className="kpi-card-subtitle">{subtitle}</div>}
      {trend && (
        <div className={`kpi-card-trend ${trend === 'up' ? 'trend-up' : trend === 'down' ? 'trend-down' : ''}`}>
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : ''}
          {trendValue && ` ${trendValue}`}
        </div>
      )}
    </div>
  );
};

export default KpiCard;
