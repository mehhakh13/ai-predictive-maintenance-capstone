import React, { useState } from 'react';
import { X } from 'lucide-react';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Color scale for risk (0-1) - same as main heatmap
const getRiskColor = (risk) => {
  if (risk >= 0.7) return '#ef4444'; // Red - High risk
  if (risk >= 0.5) return '#f97316'; // Orange - Medium-high
  if (risk >= 0.3) return '#fbbf24'; // Yellow - Medium
  if (risk >= 0.15) return '#84cc16'; // Light green - Low-medium
  return '#22c55e'; // Green - Low risk
};

const SubsystemHeatmap = ({
  selectedSystem,
  subsystemData,
  onCellClick,
  showValues,
  onClose
}) => {
  const [hoveredCell, setHoveredCell] = useState(null);

  // Filter data for selected system
  const systemSubsystems = subsystemData.filter(
    item => item.SystemDescription === selectedSystem
  );

  // Group data by subsystem
  const groupBySubsystem = (data) => {
    const grouped = {};
    data.forEach(item => {
      if (!grouped[item.SubsystemDescription]) {
        grouped[item.SubsystemDescription] = {};
      }
      grouped[item.SubsystemDescription][item.MonthNum] = item;
    });
    return grouped;
  };

  const subsystemByMonth = groupBySubsystem(systemSubsystems);

  // Calculate average risk per subsystem for sorting
  const subsystemAverages = Object.keys(subsystemByMonth).map(subsystem => {
    const monthsData = Object.values(subsystemByMonth[subsystem]);
    const avgRisk = monthsData.reduce((sum, m) => sum + m.ml_risk, 0) / monthsData.length;
    return { subsystem, avgRisk };
  });

  // Sort subsystems by average risk (descending)
  const sortedSubsystems = subsystemAverages
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .map(s => s.subsystem);

  const handleCellClick = (subsystem, month) => {
    const cellData = subsystemByMonth[subsystem]?.[month];

    if (cellData && onCellClick) {
      onCellClick({
        subsystem,
        month,
        monthName: MONTH_NAMES[month - 1],
        ...cellData
      });
    }
  };

  const handleMouseEnter = (subsystem, month) => {
    const cellData = subsystemByMonth[subsystem]?.[month];

    if (cellData) {
      setHoveredCell({
        subsystem,
        month,
        monthName: MONTH_NAMES[month - 1],
        ...cellData
      });
    }
  };

  const handleMouseLeave = () => {
    setHoveredCell(null);
  };

  return (
    <div className="section-card" style={{ marginTop: '1rem' }}>
      <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 className="section-title">Subsystem Risk Heatmap — {selectedSystem}</h2>
          <p className="section-subtitle">
            Detailed subsystem breakdown for the selected system
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            padding: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.9rem'
          }}
        >
          <X size={18} />
          Back to Systems
        </button>
      </div>

      <div className="heatmap-container">
        <div className="heatmap-wrapper">
          {/* Header row with month names */}
          <div className="heatmap-grid">
            <div className="heatmap-header">
              <div className="heatmap-corner-cell">Subsystem / Month</div>
              {MONTH_NAMES.map((month, idx) => (
                <div key={idx} className="heatmap-header-cell">
                  {month}
                </div>
              ))}
            </div>

            {/* Data rows */}
            {sortedSubsystems.map((subsystem) => (
              <div key={subsystem} className="heatmap-row">
                <div className="heatmap-row-header">{subsystem}</div>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((month) => {
                  const cellData = subsystemByMonth[subsystem]?.[month];
                  const risk = cellData?.ml_risk || 0;
                  const isHovered = hoveredCell?.subsystem === subsystem && hoveredCell?.month === month;

                  return (
                    <div
                      key={month}
                      className={`heatmap-cell ${isHovered ? 'hovered' : ''}`}
                      style={{
                        backgroundColor: getRiskColor(risk),
                        cursor: 'pointer'
                      }}
                      onClick={() => handleCellClick(subsystem, month)}
                      onMouseEnter={() => handleMouseEnter(subsystem, month)}
                      onMouseLeave={handleMouseLeave}
                    >
                      {showValues && cellData && (
                        <span className="cell-value">
                          {(risk * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Tooltip */}
          {hoveredCell && (
            <div className="heatmap-tooltip">
              <div className="tooltip-header">
                <strong>{hoveredCell.subsystem}</strong> - {hoveredCell.monthName}
              </div>
              <div className="tooltip-content">
                <div className="tooltip-row">
                  <span>Predicted Asset Risk:</span>
                  <strong>{(hoveredCell.ml_risk * 100).toFixed(1)}%</strong>
                </div>
                <div className="tooltip-row">
                  <span>Coverage:</span>
                  <strong>{hoveredCell.coverage} entities</strong>
                </div>
                <div className="tooltip-divider" />
                <div className="tooltip-row">
                  <span>Historical Asset Rate:</span>
                  <strong>{(hoveredCell.hist_asset_rate * 100).toFixed(1)}%</strong>
                </div>
                <div className="tooltip-row">
                  <span>Historical Shock Rate:</span>
                  <strong>{(hoveredCell.hist_shock_rate * 100).toFixed(1)}%</strong>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SubsystemHeatmap;
