import React, { useMemo } from 'react';
import { Building2, AlertCircle, DollarSign, Wrench } from 'lucide-react';

const BuildingRiskView = ({ data, onBuildingClick }) => {
  const rankedBuildings = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];

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

      const b = buildingMap.get(key);
      b.total_impact += item.total_impact || 0;
      b.total_cost += item.total_cost || 0;
      b.defect_count += item.count || 0;
      if (item.defect_category) b.defect_types.add(item.defect_category);
    });

    return Array.from(buildingMap.values())
      .map(b => ({ ...b, unique_defects: b.defect_types.size }))
      .sort((a, b) => b.total_impact - a.total_impact)
      .slice(0, 20);
  }, [data]);

  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);

  const formatNumber = (value) =>
    new Intl.NumberFormat('en-US').format(value);

  const getRiskLevel = (impact, maxImpact) => {
    const pct = (impact / maxImpact) * 100;
    if (pct >= 70) return { level: 'Critical', color: '#ef4444', bgColor: 'rgba(239,68,68,0.1)' };
    if (pct >= 50) return { level: 'High',     color: '#f97316', bgColor: 'rgba(249,115,22,0.1)' };
    if (pct >= 30) return { level: 'Medium',   color: '#eab308', bgColor: 'rgba(234,179,8,0.1)' };
    return             { level: 'Low',      color: '#22c55e', bgColor: 'rgba(34,197,94,0.1)' };
  };

  if (!rankedBuildings || rankedBuildings.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 20px', color: '#94a3b8', textAlign: 'center' }}>
        <Building2 size={32} color="#94a3b8" />
        <p style={{ marginTop: '12px', fontSize: '14px' }}>No building data available</p>
      </div>
    );
  }

  const maxImpact = rankedBuildings[0]?.total_impact || 1;

  return (
    <div className="building-risk-view">
      <div className="building-risk-header">
        <Building2 size={20} />
        <h3>Building Risk Analysis</h3>
        <span className="building-subtitle">Ranked by estimated impact · Top {rankedBuildings.length} buildings</span>
      </div>

      <div className="building-ranked-list">
        {rankedBuildings.map((building, index) => {
          const risk = getRiskLevel(building.total_impact, maxImpact);
          const impactPercent = (building.total_impact / maxImpact) * 100;

          return (
            <div
              key={`${building.building_id}-${index}`}
              className="building-ranked-item"
              onClick={() => onBuildingClick && onBuildingClick(building.building_id)}
              style={{ cursor: onBuildingClick ? 'pointer' : 'default' }}
            >
              <div className="building-rank" style={{ backgroundColor: risk.bgColor, color: risk.color }}>
                {index + 1}
              </div>

              <div className="building-details">
                <div className="building-name-row">
                  <span className="building-name">{building.building_name}</span>
                  <span className="building-risk-badge" style={{ backgroundColor: risk.bgColor, color: risk.color }}>
                    {risk.level}
                  </span>
                </div>
                <span className="building-university">{building.university_name}</span>

                <div className="building-impact-bar-container">
                  <div className="building-impact-bar" style={{ width: `${impactPercent}%`, backgroundColor: risk.color }} />
                </div>

                <div className="building-stats-row">
                  <span className="building-stat-item" style={{ color: '#ef4444' }}>
                    <DollarSign size={12} style={{ verticalAlign: 'middle' }} />
                    {formatCurrency(building.total_impact)}
                  </span>
                  <span className="building-stat-item" style={{ color: '#f59e0b' }}>
                    <AlertCircle size={12} style={{ verticalAlign: 'middle' }} />
                    {formatNumber(building.defect_count)} defects
                  </span>
                  {building.unique_defects > 0 && (
                    <span className="building-stat-item" style={{ color: '#3b82f6' }}>
                      <Wrench size={12} style={{ verticalAlign: 'middle' }} />
                      {building.unique_defects} types
                    </span>
                  )}
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

        .building-ranked-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          max-height: 600px;
          overflow-y: auto;
        }

        .building-ranked-item {
          display: flex;
          gap: 16px;
          padding: 14px 16px;
          background: #0f172a;
          border-radius: 8px;
          border: 1px solid #334155;
          transition: all 0.2s;
        }

        .building-ranked-item:hover {
          border-color: #475569;
          transform: translateX(4px);
        }

        .building-rank {
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

        .building-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
          min-width: 0;
        }

        .building-name-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .building-name {
          color: #f1f5f9;
          font-weight: 600;
          font-size: 15px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .building-university {
          color: #64748b;
          font-size: 12px;
          margin-top: -4px;
        }

        .building-risk-badge {
          padding: 3px 10px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
          flex-shrink: 0;
        }

        .building-impact-bar-container {
          width: 100%;
          height: 6px;
          background: #334155;
          border-radius: 3px;
          overflow: hidden;
        }

        .building-impact-bar {
          height: 100%;
          border-radius: 3px;
          transition: width 0.3s ease;
        }

        .building-stats-row {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
        }

        .building-stat-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .building-ranked-list::-webkit-scrollbar { width: 8px; }
        .building-ranked-list::-webkit-scrollbar-track { background: #1e293b; border-radius: 4px; }
        .building-ranked-list::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
        .building-ranked-list::-webkit-scrollbar-thumb:hover { background: #64748b; }
      `}</style>
    </div>
  );
};

export default BuildingRiskView;
