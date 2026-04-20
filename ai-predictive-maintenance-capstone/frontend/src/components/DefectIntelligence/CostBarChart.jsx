import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { formatCurrency, formatCompactNumber } from '../../utils/format';

const CostBarChart = ({ data, onBarClick }) => {
  const chartData = useMemo(() => {
    const defectCosts = {};

    data.forEach(item => {
      defectCosts[item.defect_type] = (defectCosts[item.defect_type] || 0) + item.TotalCost;
    });

    return Object.entries(defectCosts)
      .map(([name, cost]) => ({ name, cost: parseFloat(cost.toFixed(2)) }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 10);
  }, [data]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{payload[0].payload.name}</p>
          <p className="tooltip-value">{formatCurrency(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  const getBarColor = (index) => {
    const colors = ['#dc2626', '#ea580c', '#d97706', '#ca8a04', '#65a30d',
                    '#16a34a', '#059669', '#0d9488', '#0891b2', '#0284c7'];
    return colors[index % colors.length];
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">Top 10 Defects by Total Cost</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis
            tick={{ fill: '#94a3b8' }}
            tickFormatter={(value) => formatCompactNumber(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="cost"
            onClick={onBarClick}
            cursor="pointer"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(index)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CostBarChart;
