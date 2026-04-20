import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const DefectBarChart = ({ data, onBarClick }) => {
  const chartData = useMemo(() => {
    const defectCounts = {};

    data.forEach(item => {
      defectCounts[item.defect_type] = (defectCounts[item.defect_type] || 0) + 1;
    });

    return Object.entries(defectCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [data]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{payload[0].payload.name}</p>
          <p className="tooltip-value">Count: {payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

  const getBarColor = (index) => {
    const colors = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
                    '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9'];
    return colors[index % colors.length];
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">Top 10 Defects by Frequency</h3>
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
          <YAxis tick={{ fill: '#94a3b8' }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="count"
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

export default DefectBarChart;
