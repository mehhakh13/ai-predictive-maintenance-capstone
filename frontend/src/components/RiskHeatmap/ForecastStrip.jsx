import React from 'react';
import { TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

const getRiskColor = (risk) => {
  if (risk >= 0.7) return '#ef4444';
  if (risk >= 0.5) return '#f97316';
  if (risk >= 0.3) return '#fbbf24';
  if (risk >= 0.15) return '#84cc16';
  return '#22c55e';
};

const getRiskLabel = (risk) => {
  if (risk >= 0.7) return 'High';
  if (risk >= 0.5) return 'Med-High';
  if (risk >= 0.3) return 'Medium';
  if (risk >= 0.15) return 'Low-Med';
  return 'Low';
};

const getRiskIcon = (risk) => {
  if (risk >= 0.5) return AlertTriangle;
  return CheckCircle;
};

const ForecastStrip = ({ mlHeatmap }) => {
  if (!mlHeatmap || mlHeatmap.length === 0) return null;

  const currentMonth = new Date().getMonth() + 1; // 1-12

  // Next 3 months from today (wrapping Dec→Jan)
  const nextMonths = [1, 2, 3].map(i => ((currentMonth - 1 + i) % 12) + 1);

  const forecastData = nextMonths.map(month => {
    const rows = mlHeatmap.filter(r => r.MonthNum === month);
    if (!rows.length) return { month, avgRisk: 0, topSystem: 'No data', topRisk: 0, systemCount: 0 };

    const avgRisk = rows.reduce((s, r) => s + r.ml_risk, 0) / rows.length;
    const highRiskSystems = [...rows].sort((a, b) => b.ml_risk - a.ml_risk);
    const topSystem = highRiskSystems[0]?.SystemDescription || 'N/A';
    const topRisk = highRiskSystems[0]?.ml_risk || 0;
    const highRiskCount = rows.filter(r => r.ml_risk >= 0.5).length;

    return { month, avgRisk, topSystem, topRisk, highRiskCount, systemCount: rows.length };
  });

  return (
    <div style={{
      margin: '0 1rem 1rem',
      padding: '1rem 1.25rem',
      background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
      borderRadius: '12px',
      border: '1px solid #334155',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.875rem' }}>
        <TrendingUp size={16} color="#60a5fa" />
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          Next 3 Months Forecast — Based on historical seasonal patterns
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
        {forecastData.map(({ month, avgRisk, topSystem, topRisk, highRiskCount, systemCount }, idx) => {
          const color = getRiskColor(avgRisk);
          const Icon = getRiskIcon(avgRisk);
          const daysAway = (idx + 1) * 30;

          return (
            <div key={month} style={{
              background: '#1e293b',
              border: `1px solid ${color}40`,
              borderLeft: `3px solid ${color}`,
              borderRadius: '8px',
              padding: '0.875rem 1rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9' }}>
                    {MONTH_NAMES[month - 1]}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>~{daysAway} days away</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color }}>
                    {(avgRisk * 100).toFixed(0)}%
                  </div>
                  <div style={{
                    fontSize: '0.7rem', fontWeight: 600, color,
                    background: `${color}20`, padding: '1px 6px', borderRadius: '4px'
                  }}>
                    {getRiskLabel(avgRisk)}
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                <span style={{ color: '#64748b' }}>Watch: </span>
                <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{topSystem}</span>
                <span style={{ color: '#64748b' }}> ({(topRisk * 100).toFixed(0)}%)</span>
              </div>

              {highRiskCount > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.4rem' }}>
                  <Icon size={12} color={color} />
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                    {highRiskCount} of {systemCount} systems at medium-high risk
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ForecastStrip;
