import React, { useMemo, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { formatCurrency } from '../../utils/format';

/**
 * CostBreakdownChart Component
 * Displays stacked horizontal bar chart showing cost breakdown by system
 * Can toggle between showing total costs or PPM vs UPM breakdown
 *
 * @param {Array} data - Filtered work order data
 * @param {boolean} showPPMvsUPM - Toggle to show PPM vs UPM breakdown
 */
const CostBreakdownChart = ({ data, showPPMvsUPM = false }) => {
  const [hoveredBar, setHoveredBar] = useState(null);

  // Aggregate costs by system
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const systemCosts = {};

    data.forEach(item => {
      const system = item.SystemDescription;

      if (!systemCosts[system]) {
        systemCosts[system] = {
          system,
          LaborCost: 0,
          MaterialCost: 0,
          OtherCost: 0,
          PPM_Total: 0,
          UPM_Total: 0,
          Total: 0
        };
      }

      systemCosts[system].LaborCost += item.LaborCost;
      systemCosts[system].MaterialCost += item.MaterialCost;
      systemCosts[system].OtherCost += item.OtherCost;
      systemCosts[system].Total += item.TotalCost;

      if (item.MaintenanceType === 'PPM') {
        systemCosts[system].PPM_Total += item.TotalCost;
      } else {
        systemCosts[system].UPM_Total += item.TotalCost;
      }
    });

    // Convert to array and sort by total cost descending
    return Object.values(systemCosts)
      .sort((a, b) => b.Total - a.Total)
      .slice(0, 10); // Top 10 systems
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;

    const systemData = payload[0].payload;

    return (
      <div className="custom-tooltip">
        <div className="tooltip-label">{systemData.system}</div>
        <div className="tooltip-divider" />
        {showPPMvsUPM ? (
          <>
            <div className="tooltip-row">
              <span>PPM Total:</span>
              <strong>{formatCurrency(systemData.PPM_Total)}</strong>
            </div>
            <div className="tooltip-row">
              <span>UPM Total:</span>
              <strong>{formatCurrency(systemData.UPM_Total)}</strong>
            </div>
            <div className="tooltip-divider" />
            <div className="tooltip-row">
              <span>Total Cost:</span>
              <strong>{formatCurrency(systemData.Total)}</strong>
            </div>
          </>
        ) : (
          <>
            <div className="tooltip-row">
              <span>Labor:</span>
              <strong>{formatCurrency(systemData.LaborCost)}</strong>
            </div>
            <div className="tooltip-row">
              <span>Material:</span>
              <strong>{formatCurrency(systemData.MaterialCost)}</strong>
            </div>
            <div className="tooltip-row">
              <span>Other:</span>
              <strong>{formatCurrency(systemData.OtherCost)}</strong>
            </div>
            <div className="tooltip-divider" />
            <div className="tooltip-row">
              <span>Total:</span>
              <strong>{formatCurrency(systemData.Total)}</strong>
            </div>
          </>
        )}
      </div>
    );
  };

  if (chartData.length === 0) {
    return (
      <div className="chart-empty">
        <p>No data available for the selected filters.</p>
      </div>
    );
  }

  return (
    <div className="cost-breakdown-chart">
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
          <XAxis
            type="number"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
          />
          <YAxis
            type="category"
            dataKey="system"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            width={90}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
          <Legend
            wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }}
            iconType="square"
          />

          {showPPMvsUPM ? (
            <>
              <Bar
                dataKey="PPM_Total"
                stackId="a"
                fill="#10b981"
                name="PPM Cost"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="UPM_Total"
                stackId="a"
                fill="#f59e0b"
                name="UPM Cost"
                radius={[0, 4, 4, 0]}
              />
            </>
          ) : (
            <>
              <Bar
                dataKey="LaborCost"
                stackId="a"
                fill="#3b82f6"
                name="Labor"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="MaterialCost"
                stackId="a"
                fill="#8b5cf6"
                name="Material"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="OtherCost"
                stackId="a"
                fill="#ec4899"
                name="Other"
                radius={[0, 4, 4, 0]}
              />
            </>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CostBreakdownChart;
