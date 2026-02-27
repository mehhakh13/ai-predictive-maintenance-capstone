import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCurrency } from '../../utils/format';

/**
 * CostTrendChart Component
 * Displays line chart showing monthly cost trends for PPM vs UPM
 *
 * @param {Array} data - Filtered work order data
 */
const CostTrendChart = ({ data }) => {
  // Aggregate costs by month and maintenance type
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const monthlyData = {};

    data.forEach(item => {
      const date = new Date(item.WOStartDate);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const monthLabel = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });

      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = {
          month: monthLabel,
          monthKey,
          PPM_Cost: 0,
          UPM_Cost: 0,
          Total_Cost: 0
        };
      }

      if (item.MaintenanceType === 'PPM') {
        monthlyData[monthKey].PPM_Cost += item.TotalCost;
      } else {
        monthlyData[monthKey].UPM_Cost += item.TotalCost;
      }
      monthlyData[monthKey].Total_Cost += item.TotalCost;
    });

    // Convert to array and sort by month
    return Object.values(monthlyData).sort((a, b) => a.monthKey.localeCompare(b.monthKey));
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    const ppmCost = payload.find(p => p.dataKey === 'PPM_Cost')?.value || 0;
    const upmCost = payload.find(p => p.dataKey === 'UPM_Cost')?.value || 0;
    const totalCost = ppmCost + upmCost;

    return (
      <div className="custom-tooltip">
        <div className="tooltip-label">{label}</div>
        <div className="tooltip-divider" />
        <div className="tooltip-row">
          <span style={{ color: '#10b981' }}>PPM Cost:</span>
          <strong>{formatCurrency(ppmCost)}</strong>
        </div>
        <div className="tooltip-row">
          <span style={{ color: '#f59e0b' }}>UPM Cost:</span>
          <strong>{formatCurrency(upmCost)}</strong>
        </div>
        <div className="tooltip-divider" />
        <div className="tooltip-row">
          <span>Total:</span>
          <strong>{formatCurrency(totalCost)}</strong>
        </div>
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
    <div className="cost-trend-chart">
      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
          <XAxis
            dataKey="month"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="PPM_Cost"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
            name="PPM Cost"
          />
          <Line
            type="monotone"
            dataKey="UPM_Cost"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: '#f59e0b', r: 4 }}
            activeDot={{ r: 6 }}
            name="UPM Cost"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CostTrendChart;
