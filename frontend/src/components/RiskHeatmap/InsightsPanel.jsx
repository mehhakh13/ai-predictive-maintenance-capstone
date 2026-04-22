import React from 'react';
import { AlertCircle, TrendingUp, Lightbulb } from 'lucide-react';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const InsightsPanel = ({ mlHeatmap, selectedMonth = new Date().getMonth() + 1 }) => {
  // Calculate insights
  const calculateInsights = () => {
    if (!mlHeatmap || mlHeatmap.length === 0) {
      return {
        topRiskySystemsThisMonth: [],
        biggestIncrease: [],
        recommendations: []
      };
    }

    // Filter data for selected month
    const currentMonthData = mlHeatmap.filter(item => item.MonthNum === selectedMonth);

    // Top 5 risky systems this month
    const topRiskySystemsThisMonth = currentMonthData
      .sort((a, b) => b.ml_risk - a.ml_risk)
      .slice(0, 5)
      .map(item => ({
        system: item.SystemDescription,
        risk: item.ml_risk,
        coverage: item.coverage
      }));

    // Calculate biggest increase vs previous month
    const prevMonth = selectedMonth === 1 ? 12 : selectedMonth - 1;
    const prevMonthData = mlHeatmap.filter(item => item.MonthNum === prevMonth);

    const increases = [];
    currentMonthData.forEach(current => {
      const prev = prevMonthData.find(p => p.SystemDescription === current.SystemDescription);
      if (prev) {
        const delta = current.ml_risk - prev.ml_risk;
        if (delta > 0.05) { // Only include significant increases (>5%)
          increases.push({
            system: current.SystemDescription,
            delta: delta,
            currentRisk: current.ml_risk,
            prevRisk: prev.ml_risk
          });
        }
      }
    });

    const biggestIncrease = increases
      .sort((a, b) => b.delta - a.delta)
      .slice(0, 3);

    // Generate recommendations based on data
    const recommendations = generateRecommendations(topRiskySystemsThisMonth, selectedMonth);

    return {
      topRiskySystemsThisMonth,
      biggestIncrease,
      recommendations
    };
  };

  const generateRecommendations = (topSystems, month) => {
    const recommendations = [];

    if (topSystems.length > 0 && topSystems[0].risk > 0.7) {
      recommendations.push({
        type: 'urgent',
        title: 'Immediate Action Required',
        text: `${topSystems[0].system} shows high risk (${(topSystems[0].risk * 100).toFixed(0)}%). Schedule preventive maintenance immediately.`
      });
    }

    // Seasonal recommendations
    if ([12, 1, 2].includes(month)) { // Winter
      recommendations.push({
        type: 'seasonal',
        title: 'Winter Season Alert',
        text: 'Monitor HVAC and Plumbing systems closely. Cold weather increases asset failure risk.'
      });
    } else if ([6, 7, 8].includes(month)) { // Summer
      recommendations.push({
        type: 'seasonal',
        title: 'Summer Season Alert',
        text: 'HVAC systems operate at peak load. Increase inspection frequency.'
      });
    }

    // Coverage-based recommendation
    const lowCoverageSystems = topSystems.filter(s => s.coverage < 50);
    if (lowCoverageSystems.length > 0) {
      recommendations.push({
        type: 'info',
        title: 'Limited Data Coverage',
        text: `Some high-risk systems have limited data. Consider these predictions with caution.`
      });
    }

    // General best practice
    recommendations.push({
      type: 'info',
      title: 'Proactive Maintenance',
      text: 'Focus on asset-driven failures with predictive maintenance. Shock-driven UPM is handled separately.'
      });

    return recommendations;
  };

  const insights = calculateInsights();

  return (
    <div className="insights-panel">
      <h3 className="insights-title">
        <Lightbulb size={20} />
        What should I do now?
      </h3>

      {/* Top Risky Systems This Month */}
      <div className="insights-section">
        <h4 className="section-title">
          <AlertCircle size={16} />
          Top 5 Risky Systems ({MONTH_NAMES[selectedMonth - 1]})
        </h4>
        <div className="risky-systems-list">
          {insights.topRiskySystemsThisMonth.length > 0 ? (
            insights.topRiskySystemsThisMonth.map((item, idx) => (
              <div key={idx} className="risky-system-item">
                <div className="system-rank">#{idx + 1}</div>
                <div className="system-info">
                  <div className="system-name">{item.system}</div>
                  <div className="system-risk">
                    Risk: <strong>{(item.risk * 100).toFixed(1)}%</strong>
                  </div>
                </div>
                <div
                  className="system-risk-bar"
                  style={{
                    width: `${item.risk * 100}%`,
                    backgroundColor: item.risk >= 0.7 ? '#ef4444' : item.risk >= 0.5 ? '#f97316' : '#fbbf24'
                  }}
                />
              </div>
            ))
          ) : (
            <p className="empty-message">No data available for this month</p>
          )}
        </div>
      </div>

      {/* Biggest Increase vs Previous Month */}
      {insights.biggestIncrease.length > 0 && (
        <div className="insights-section">
          <h4 className="section-title">
            <TrendingUp size={16} />
            Biggest Risk Increases
          </h4>
          <div className="increase-list">
            {insights.biggestIncrease.map((item, idx) => (
              <div key={idx} className="increase-item">
                <div className="increase-system">{item.system}</div>
                <div className="increase-delta">
                  +{(item.delta * 100).toFixed(1)}%
                  <span className="increase-detail">
                    ({(item.prevRisk * 100).toFixed(0)}% → {(item.currentRisk * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="insights-section">
        <h4 className="section-title">Recommended Actions</h4>
        <div className="recommendations-list">
          {insights.recommendations.map((rec, idx) => (
            <div key={idx} className={`recommendation-item ${rec.type}`}>
              <div className="recommendation-title">{rec.title}</div>
              <div className="recommendation-text">{rec.text}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InsightsPanel;
