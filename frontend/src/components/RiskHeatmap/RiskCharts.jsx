import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const RiskCharts = ({ mlHeatmap, selectedMonth = new Date().getMonth() + 1 }) => {
  // Calculate average risk by month
  const calculateMonthlyRisk = () => {
    if (!mlHeatmap || mlHeatmap.length === 0) return [];

    const monthlyData = {};
    mlHeatmap.forEach(item => {
      if (!monthlyData[item.MonthNum]) {
        monthlyData[item.MonthNum] = { total: 0, count: 0 };
      }
      monthlyData[item.MonthNum].total += item.ml_risk;
      monthlyData[item.MonthNum].count += 1;
    });

    return Object.keys(monthlyData)
      .sort((a, b) => parseInt(a) - parseInt(b))
      .map(month => ({
        month: MONTH_NAMES[parseInt(month) - 1],
        monthNum: parseInt(month),
        risk: (monthlyData[month].total / monthlyData[month].count) * 100
      }));
  };

  // Calculate top risky systems for selected month
  const calculateTopSystemsForMonth = () => {
    if (!mlHeatmap || mlHeatmap.length === 0) return [];

    const monthData = mlHeatmap
      .filter(item => item.MonthNum === selectedMonth)
      .sort((a, b) => b.ml_risk - a.ml_risk)
      .slice(0, 8) // Top 8 systems
      .map(item => ({
        system: item.SystemDescription.length > 15
          ? item.SystemDescription.substring(0, 15) + '...'
          : item.SystemDescription,
        risk: (item.ml_risk * 100).toFixed(1),
        fullName: item.SystemDescription
      }));

    return monthData;
  };

  const monthlyRiskData = calculateMonthlyRisk();
  const topSystemsData = calculateTopSystemsForMonth();

  // Custom tooltip for line chart
  const CustomLineTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{payload[0].payload.month}</p>
          <p className="tooltip-value">
            Avg Risk: <strong>{payload[0].value.toFixed(1)}%</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  // Custom tooltip for bar chart
  const CustomBarTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{payload[0].payload.fullName}</p>
          <p className="tooltip-value">
            Risk: <strong>{payload[0].value}%</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="risk-charts">
      {/* Line Chart: Average Risk by Month */}
      <div className="chart-container">
        <h3 className="chart-title">Average Asset Risk by Month</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={monthlyRiskData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="month"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
              label={{ value: 'Risk (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
            />
            <Tooltip content={<CustomLineTooltip />} />
            <Legend wrapperStyle={{ color: '#9ca3af' }} />
            <Line
              type="monotone"
              dataKey="risk"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
              name="Avg Risk (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart: Top Risky Systems for Selected Month */}
      <div className="chart-container">
        <h3 className="chart-title">
          Top Risky Systems - {MONTH_NAMES[selectedMonth - 1]}
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={topSystemsData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              type="number"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
              label={{ value: 'Risk (%)', position: 'insideBottom', fill: '#9ca3af' }}
            />
            <YAxis
              type="category"
              dataKey="system"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
              width={120}
            />
            <Tooltip content={<CustomBarTooltip />} />
            <Bar
              dataKey="risk"
              fill="#f59e0b"
              name="Risk (%)"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RiskCharts;
