import React, { useMemo } from 'react';
import { Building2, AlertCircle, DollarSign, Wrench } from 'lucide-react';

/**
 * Building Risk View Component
 * Shows top problematic buildings with defect counts and costs
 */
const BuildingRiskView = ({ data, onBuildingClick }) => {
  const topBuildings = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];

    // Aggregate by building
    const buildingMap = new Map();

    data.forEach(item => {
      const key = `${item.building_id}-${item.building_name}`;
      if (!buildingMap.has(key)) {
        buildingMap.set(key, {
          building_id: item.building_id,
          building_name: item.building_name,
          university_name: item.university_name,
          total_impact: 0,
          total_cost: 0,
          defect_count: 0,
          defect_types: new Set()
        });
      }

      const building = buildingMap.get(key);
      building.total_impact += item.total_impact || 0;
      building.total_cost += item.total_cost || 0;
      building.defect_count += item.count || 0;
      building.defect_types.add(item.defect_category);
    });

    // Convert to array and sort by impact
    return Array.from(buildingMap.values())
      .map(b => ({ ...b, unique_defects: b.defect_types.size }))
      .sort((a, b) => b.total_impact - a.total_impact)
      .slice(0, 12); // Top 12 buildings
  }, [data]);

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

  const getRiskLevel = (impact, maxImpact) => {
    const percentage = (impact / maxImpact) * 100;
    if (percentage >= 70) return { level: 'Critical', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.15)' };
    if (percentage >= 50) return { level: 'High', color: '#f97316', bgColor: 'rgba(249, 115, 22, 0.15)' };
    if (percentage >= 30) return { level: 'Medium', color: '#eab308', bgColor: 'rgba(234, 179, 8, 0.15)' };
    return { level: 'Low', color: '#22c55e', bgColor: 'rgba(34, 197, 94, 0.15)' };
  };

  if (!topBuildings || topBuildings.length === 0) {
    return (
      <div className="building-risk-empty">
        <Building2 size={32} color="#94a3b8" />
        <p>No building data available</p>
      </div>
    );
  }

  const maxImpact = topBuildings[0]?.total_impact || 1;

  return (
    <div className="building-risk-view">
      <div className="building-risk-header">
        <Building2 size={20} />
        <h3>Building Risk Analysis</h3>
        <span className="building-subtitle">Top problematic buildings</span>
      </div>

      <div className="building-grid">
        {topBuildings.map((building, index) => {
          const risk = getRiskLevel(building.total_impact, maxImpact);
          const impactPercent = (building.total_impact / maxImpact) * 100;

          return (
            <div
              key={`${building.building_id}-${index}`}
              className="building-card"
              onClick={() => onBuildingClick && onBuildingClick(building.building_id)}
              style={{
                cursor: onBuildingClick ? 'pointer' : 'default',
                borderColor: risk.color
              }}
            >
              <div className="building-card-header">
                <div className="building-icon" style={{ backgroundColor: risk.bgColor, color: risk.color }}>
                  <Building2 size={20} />
                </div>
                <div className="building-title">
                  <h4>{building.building_name}</h4>
                  <p>{building.university_name}</p>
                </div>
                <div className="building-risk-badge" style={{ backgroundColor: risk.bgColor, color: risk.color }}>
                  {risk.level}
                </div>
              </div>

              <div className="building-impact-bar-container">
                <div
                  className="building-impact-bar"
                  style={{
                    width: `${impactPercent}%`,
                    backgroundColor: risk.color
                  }}
                />
              </div>

              <div className="building-stats">
                <div className="building-stat">
                  <div className="stat-icon" style={{ color: '#ef4444' }}>
                    <DollarSign size={16} />
                  </div>
                  <div className="stat-content">
                    <span className="stat-value">{formatCurrency(building.total_impact)}</span>
                    <span className="stat-label">Total Impact</span>
                  </div>
                </div>

                <div className="building-stat">
                  <div className="stat-icon" style={{ color: '#f59e0b' }}>
                    <AlertCircle size={16} />
                  </div>
                  <div className="stat-content">
                    <span className="stat-value">{formatNumber(building.defect_count)}</span>
                    <span className="stat-label">Defects</span>
                  </div>
                </div>

                <div className="building-stat">
                  <div className="stat-icon" style={{ color: '#3b82f6' }}>
                    <Wrench size={16} />
                  </div>
                  <div className="stat-content">
                    <span className="stat-value">{building.unique_defects}</span>
                    <span className="stat-label">Types</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .building-risk-view {
          background: #1e293b;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .building-risk-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 20px;
          color: #f1f5f9;
        }

        .building-risk-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .building-subtitle {
          margin-left: auto;
          font-size: 13px;
          color: #94a3b8;
        }

        .building-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
          max-height: 600px;
          overflow-y: auto;
        }

        .building-card {
          background: #0f172a;
          border-radius: 8px;
          padding: 16px;
          border: 2px solid #334155;
          transition: all 0.2s;
        }

        .building-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        }

        .building-card-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 16px;
        }

        .building-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .building-title {
          flex: 1;
          min-width: 0;
        }

        .building-title h4 {
          margin: 0;
          color: #f1f5f9;
          font-size: 15px;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .building-title p {
          margin: 4px 0 0 0;
          color: #94a3b8;
          font-size: 12px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .building-risk-badge {
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }

        .building-impact-bar-container {
          width: 100%;
          height: 6px;
          background: #334155;
          border-radius: 3px;
          overflow: hidden;
          margin-bottom: 16px;
        }

        .building-impact-bar {
          height: 100%;
          border-radius: 3px;
          transition: width 0.3s ease;
        }

        .building-stats {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .building-stat {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .stat-icon {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          background: rgba(255, 255, 255, 0.05);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .stat-content {
          display: flex;
          flex-direction: column;
          gap: 2px;
          flex: 1;
          min-width: 0;
        }

        .stat-value {
          color: #f1f5f9;
          font-size: 14px;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .stat-label {
          color: #64748b;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .building-risk-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          color: #94a3b8;
          text-align: center;
        }

        .building-risk-empty p {
          margin-top: 12px;
          font-size: 14px;
        }

        /* Scrollbar styling */
        .building-grid::-webkit-scrollbar {
          width: 8px;
        }

        .building-grid::-webkit-scrollbar-track {
          background: #1e293b;
          border-radius: 4px;
        }

        .building-grid::-webkit-scrollbar-thumb {
          background: #475569;
          border-radius: 4px;
        }

        .building-grid::-webkit-scrollbar-thumb:hover {
          background: #64748b;
        }

        @media (max-width: 1200px) {
          .building-grid {
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          }
        }

        @media (max-width: 768px) {
          .building-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default BuildingRiskView;
