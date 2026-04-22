import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatCurrency, formatPercent } from '../../utils/format';

/**
 * CostDistribution Component
 * Displays pie/donut charts showing cost distribution
 * Primary: PPM vs UPM
 * Secondary: Labor vs Material vs Other
 *
 * @param {Array} data - Filtered work order data
 * @param {string} view - 'ppm-upm' or 'cost-type'
 */
const CostDistribution = ({ data, view = 'ppm-upm' }) => {
  // Calculate distribution data
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    if (view === 'ppm-upm') {
      let ppmTotal = 0;
      let upmTotal = 0;

      data.forEach(item => {
        if (item.MaintenanceType === 'PPM') {
          ppmTotal += item.TotalCost;
        } else {
          upmTotal += item.TotalCost;
        }
      });

      return [
        { name: 'PPM', value: ppmTotal, color: '#10b981' },
        { name: 'UPM', value: upmTotal, color: '#f59e0b' }
      ];
    } else {
      let laborTotal = 0;
      let materialTotal = 0;
      let otherTotal = 0;

      data.forEach(item => {
        laborTotal += item.LaborCost;
        materialTotal += item.MaterialCost;
        otherTotal += item.OtherCost;
      });

      return [
        { name: 'Labor', value: laborTotal, color: '#3b82f6' },
        { name: 'Material', value: materialTotal, color: '#8b5cf6' },
        { name: 'Other', value: otherTotal, color: '#ec4899' }
      ];
    }
  }, [data, view]);

  const totalValue = chartData.reduce((sum, item) => sum + item.value, 0);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;

    const item = payload[0];
    const percentage = (item.value / totalValue) * 100;

    return (
      <div className="custom-tooltip">
        <div className="tooltip-label">{item.name}</div>
        <div className="tooltip-divider" />
        <div className="tooltip-row">
          <span>Amount:</span>
          <strong>{formatCurrency(item.value)}</strong>
        </div>
        <div className="tooltip-row">
          <span>Percentage:</span>
          <strong>{formatPercent(percentage, 1, false)}</strong>
        </div>
      </div>
    );
  };

  // Custom label
  const renderCustomLabel = (entry) => {
    const percentage = ((entry.value / totalValue) * 100).toFixed(1);
    return `${percentage}%`;
  };

  if (chartData.length === 0 || totalValue === 0) {
    return (
      <div className="chart-empty">
        <p>No data available for the selected filters.</p>
      </div>
    );
  }

  return (
    <div className="cost-distribution">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={100}
            innerRadius={60}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }}
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Summary below chart */}
      <div className="distribution-summary">
        {chartData.map((item, index) => (
          <div key={index} className="summary-item">
            <div className="summary-color" style={{ backgroundColor: item.color }} />
            <div className="summary-info">
              <div className="summary-label">{item.name}</div>
              <div className="summary-value">{formatCurrency(item.value)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CostDistribution;
