import React, { useMemo } from 'react';
import { AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';

/**
 * Impact Ranking Component
 * Displays defect categories ranked by impact score (cost × priority)
 * with risk level indicators
 */
const ImpactRanking = ({ data, onDefectClick }) => {
  const sortedData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data
      .sort((a, b) => b.total_impact - a.total_impact)
      .slice(0, 15); // Top 15
  }, [data]);

  const getRiskColor = (riskLevel) => {
    const colors = {
      Critical: '#ef4444',
      High: '#f97316',
      Medium: '#eab308',
      Low: '#22c55e'
    };
    return colors[riskLevel] || '#6b7280';
  };

  const getRiskBgColor = (riskLevel) => {
    const colors = {
      Critical: 'rgba(239, 68, 68, 0.1)',
      High: 'rgba(249, 115, 22, 0.1)',
      Medium: 'rgba(234, 179, 8, 0.1)',
      Low: 'rgba(34, 197, 94, 0.1)'
    };
    return colors[riskLevel] || 'rgba(107, 114, 128, 0.1)';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  if (!sortedData || sortedData.length === 0) {
    return (
      <div className="impact-ranking-empty">
        <AlertTriangle size={32} color="#94a3b8" />
        <p>No impact data available</p>
      </div>
    );
  }

  const maxImpact = sortedData[0]?.total_impact || 1;

  return (
    <div className="impact-ranking">
      <div className="impact-ranking-header">
        <TrendingUp size={20} />
        <h3>Defect Impact Ranking</h3>
        <span className="impact-subtitle">Ranked by impact score (cost × priority)</span>
      </div>

      <div className="impact-list">
        {sortedData.map((defect, index) => {
          const impactPercent = (defect.total_impact / maxImpact) * 100;
          const riskColor = getRiskColor(defect.risk_level);
          const riskBgColor = getRiskBgColor(defect.risk_level);

          return (
            <div
              key={index}
              className="impact-item"
              onClick={() => onDefectClick && onDefectClick(defect.defect_category)}
              style={{ cursor: onDefectClick ? 'pointer' : 'default' }}
            >
              <div className="impact-rank" style={{ backgroundColor: riskBgColor, color: riskColor }}>
                {index + 1}
              </div>

              <div className="impact-details">
                <div className="impact-name-row">
                  <span className="impact-name">{defect.defect_category}</span>
                  <span className="impact-risk-badge" style={{ backgroundColor: riskBgColor, color: riskColor }}>
                    {defect.risk_level}
                  </span>
                </div>

                <div className="impact-bar-container">
                  <div
                    className="impact-bar"
                    style={{
                      width: `${impactPercent}%`,
                      backgroundColor: riskColor
                    }}
                  />
                </div>

                <div className="impact-stats">
                  <div className="impact-stat">
                    <DollarSign size={14} />
                    <span>{formatCurrency(defect.total_impact)} impact</span>
                  </div>
                  <div className="impact-stat">
                    <span>{formatNumber(defect.count)} occurrences</span>
                  </div>
                  <div className="impact-stat">
                    <span>{formatCurrency(defect.total_cost)} total cost</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .impact-ranking {
          background: #1e293b;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .impact-ranking-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 20px;
          color: #f1f5f9;
        }

        .impact-ranking-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .impact-subtitle {
          margin-left: auto;
          font-size: 13px;
          color: #94a3b8;
        }

        .impact-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
          max-height: 600px;
          overflow-y: auto;
        }

        .impact-item {
          display: flex;
          gap: 16px;
          padding: 16px;
          background: #0f172a;
          border-radius: 8px;
          border: 1px solid #334155;
          transition: all 0.2s;
        }

        .impact-item:hover {
          border-color: #475569;
          transform: translateX(4px);
        }

        .impact-rank {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          border-radius: 8px;
          font-weight: 700;
          font-size: 18px;
          flex-shrink: 0;
        }

        .impact-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .impact-name-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .impact-name {
          color: #f1f5f9;
          font-weight: 500;
          font-size: 15px;
        }

        .impact-risk-badge {
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          white-space: nowrap;
        }

        .impact-bar-container {
          width: 100%;
          height: 8px;
          background: #334155;
          border-radius: 4px;
          overflow: hidden;
        }

        .impact-bar {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .impact-stats {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
        }

        .impact-stat {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #94a3b8;
          font-size: 13px;
        }

        .impact-ranking-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          color: #94a3b8;
          text-align: center;
        }

        .impact-ranking-empty p {
          margin-top: 12px;
          font-size: 14px;
        }

        /* Scrollbar styling */
        .impact-list::-webkit-scrollbar {
          width: 8px;
        }

        .impact-list::-webkit-scrollbar-track {
          background: #1e293b;
          border-radius: 4px;
        }

        .impact-list::-webkit-scrollbar-thumb {
          background: #475569;
          border-radius: 4px;
        }

        .impact-list::-webkit-scrollbar-thumb:hover {
          background: #64748b;
        }
      `}</style>
    </div>
  );
};

export default ImpactRanking;
