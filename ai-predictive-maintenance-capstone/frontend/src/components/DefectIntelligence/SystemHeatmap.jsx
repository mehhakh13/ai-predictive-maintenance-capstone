import React, { useMemo, useState } from 'react';
import { formatCompactNumber } from '../../utils/format';

const SystemHeatmap = ({ data, onCellClick, metric = 'count' }) => {
  const [hoveredCell, setHoveredCell] = useState(null);

  const { heatmapData, systems, defectTypes, maxValue } = useMemo(() => {
    const matrix = {};
    const systemSet = new Set();
    const defectTypeSet = new Set();

    data.forEach(item => {
      const key = `${item.SystemDescription}|${item.defect_type}`;

      if (!matrix[key]) {
        matrix[key] = { count: 0, cost: 0, items: [] };
      }

      matrix[key].count += 1;
      matrix[key].cost += item.TotalCost;
      matrix[key].items.push(item);

      systemSet.add(item.SystemDescription);
      defectTypeSet.add(item.defect_type);
    });

    const systems = Array.from(systemSet).sort();
    const defectTypes = Array.from(defectTypeSet).sort();

    // Find max value for color scaling
    const values = Object.values(matrix).map(v => metric === 'count' ? v.count : v.cost);
    const maxValue = Math.max(...values, 1);

    return { heatmapData: matrix, systems, defectTypes, maxValue };
  }, [data, metric]);

  const getCellValue = (system, defectType) => {
    const key = `${system}|${defectType}`;
    const cell = heatmapData[key];
    return cell ? (metric === 'count' ? cell.count : cell.cost) : 0;
  };

  const getCellColor = (value) => {
    if (value === 0) return '#1a1a1a';

    const intensity = value / maxValue;

    if (intensity > 0.75) return '#dc2626'; // Red
    if (intensity > 0.5) return '#ea580c';  // Orange
    if (intensity > 0.25) return '#f59e0b'; // Amber
    return '#eab308'; // Yellow
  };

  const handleCellClick = (system, defectType) => {
    const key = `${system}|${defectType}`;
    const cellData = heatmapData[key];

    if (cellData && onCellClick) {
      onCellClick({
        system,
        defectType,
        count: cellData.count,
        cost: cellData.cost,
        items: cellData.items
      });
    }
  };

  return (
    <div className="heatmap-container">
      <div className="heatmap-wrapper">
        <div className="heatmap-grid-container">
          {/* Row headers (Systems) */}
          <div className="heatmap-row-headers">
            <div className="heatmap-corner-cell"></div>
            {systems.map(system => (
              <div key={system} className="heatmap-row-header">
                {system}
              </div>
            ))}
          </div>

          {/* Column headers and cells */}
          <div className="heatmap-columns">
            {defectTypes.map(defectType => (
              <div key={defectType} className="heatmap-column">
                <div className="heatmap-column-header">
                  <span>{defectType}</span>
                </div>
                {systems.map(system => {
                  const value = getCellValue(system, defectType);
                  const cellKey = `${system}|${defectType}`;

                  return (
                    <div
                      key={cellKey}
                      className={`heatmap-cell ${hoveredCell === cellKey ? 'hovered' : ''}`}
                      style={{ backgroundColor: getCellColor(value) }}
                      onClick={() => handleCellClick(system, defectType)}
                      onMouseEnter={() => setHoveredCell(cellKey)}
                      onMouseLeave={() => setHoveredCell(null)}
                    >
                      {value > 0 && (
                        <span className="heatmap-cell-value">
                          {metric === 'count' ? value : formatCompactNumber(value)}
                        </span>
                      )}

                      {hoveredCell === cellKey && value > 0 && (
                        <div className="heatmap-tooltip">
                          <div><strong>{system}</strong></div>
                          <div><strong>{defectType}</strong></div>
                          <div>Count: {heatmapData[cellKey].count}</div>
                          <div>Cost: ${formatCompactNumber(heatmapData[cellKey].cost)}</div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="heatmap-legend">
        <div className="legend-title">
          {metric === 'count' ? 'Defect Count' : 'Total Cost'}
        </div>
        <div className="legend-gradient">
          <div className="legend-color" style={{ backgroundColor: '#eab308' }}></div>
          <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
          <div className="legend-color" style={{ backgroundColor: '#ea580c' }}></div>
          <div className="legend-color" style={{ backgroundColor: '#dc2626' }}></div>
        </div>
        <div className="legend-labels">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>
    </div>
  );
};

export default SystemHeatmap;
