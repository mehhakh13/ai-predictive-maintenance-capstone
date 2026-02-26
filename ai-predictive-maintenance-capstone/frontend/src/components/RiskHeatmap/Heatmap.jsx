import React, { useState } from 'react';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Color scale for risk (0-1)
const getRiskColor = (risk) => {
  if (risk >= 0.7) return '#ef4444'; // Red - High risk
  if (risk >= 0.5) return '#f97316'; // Orange - Medium-high
  if (risk >= 0.3) return '#fbbf24'; // Yellow - Medium
  if (risk >= 0.15) return '#84cc16'; // Light green - Low-medium
  return '#22c55e'; // Green - Low risk
};

const Heatmap = ({ mlHeatmap, historicalHeatmap, onCellClick, showValues }) => {
  const [hoveredCell, setHoveredCell] = useState(null);

  // Group data by system
  const groupBySystem = (data) => {
    const grouped = {};
    data.forEach(item => {
      if (!grouped[item.SystemDescription]) {
        grouped[item.SystemDescription] = {};
      }
      grouped[item.SystemDescription][item.MonthNum] = item;
    });
    return grouped;
  };

  const mlBySystem = groupBySystem(mlHeatmap);
  const histBySystem = groupBySystem(historicalHeatmap);

  // Calculate average risk per system for sorting
  const systemAverages = Object.keys(mlBySystem).map(system => {
    const monthsData = Object.values(mlBySystem[system]);
    const avgRisk = monthsData.reduce((sum, m) => sum + m.ml_risk, 0) / monthsData.length;
    return { system, avgRisk };
  });

  // Sort systems by average risk (descending)
  const sortedSystems = systemAverages
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .map(s => s.system);

  const handleCellClick = (system, month) => {
    const mlData = mlBySystem[system]?.[month];
    const histData = histBySystem[system]?.[month];

    if (mlData && onCellClick) {
      onCellClick({
        system,
        month,
        monthName: MONTH_NAMES[month - 1],
        ...mlData,
        historical: histData
      });
    }
  };

  const handleMouseEnter = (system, month) => {
    const mlData = mlBySystem[system]?.[month];
    const histData = histBySystem[system]?.[month];

    if (mlData) {
      setHoveredCell({
        system,
        month,
        monthName: MONTH_NAMES[month - 1],
        ...mlData,
        historical: histData
      });
    }
  };

  const handleMouseLeave = () => {
    setHoveredCell(null);
  };

  return (
    <div className="heatmap-container">
      <div className="heatmap-wrapper">
        {/* Header row with month names */}
        <div className="heatmap-grid">
          <div className="heatmap-header">
            <div className="heatmap-corner-cell">System / Month</div>
            {MONTH_NAMES.map((month, idx) => (
              <div key={idx} className="heatmap-header-cell">
                {month}
              </div>
            ))}
          </div>

          {/* Data rows */}
          {sortedSystems.map((system) => (
            <div key={system} className="heatmap-row">
              <div className="heatmap-row-header">{system}</div>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((month) => {
                const cellData = mlBySystem[system]?.[month];
                const risk = cellData?.ml_risk || 0;
                const isHovered = hoveredCell?.system === system && hoveredCell?.month === month;

                return (
                  <div
                    key={month}
                    className={`heatmap-cell ${isHovered ? 'hovered' : ''}`}
                    style={{
                      backgroundColor: getRiskColor(risk),
                      cursor: 'pointer'
                    }}
                    onClick={() => handleCellClick(system, month)}
                    onMouseEnter={() => handleMouseEnter(system, month)}
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
              <strong>{hoveredCell.system}</strong> - {hoveredCell.monthName}
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
              {hoveredCell.historical && (
                <>
                  <div className="tooltip-divider" />
                  <div className="tooltip-row">
                    <span>Historical Asset Rate:</span>
                    <strong>{(hoveredCell.historical.hist_asset_rate * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="tooltip-row">
                    <span>Historical Shock Rate:</span>
                    <strong>{(hoveredCell.historical.hist_shock_rate * 100).toFixed(1)}%</strong>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="heatmap-legend">
        <span className="legend-title">Risk Level:</span>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#22c55e' }} />
            <span>Low (&lt;15%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#84cc16' }} />
            <span>Low-Med (15-30%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#fbbf24' }} />
            <span>Medium (30-50%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f97316' }} />
            <span>Med-High (50-70%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#ef4444' }} />
            <span>High (≥70%)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Heatmap;
