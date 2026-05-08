import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

/**
 * Monthly Trends Chart Component
 * Shows defect occurrences over time with line chart
 */
const MonthlyTrendsChart = ({ data, selectedCategories = [] }) => {
  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];

    const DISPLAY_START = '2015-01';

    // Group by month
    const monthlyMap = new Map();

    data.forEach(item => {
      const month = item.month;
      if (month < DISPLAY_START) return;
      if (!monthlyMap.has(month)) {
        monthlyMap.set(month, { month, total: 0, categories: {} });
      }

      const monthData = monthlyMap.get(month);
      monthData.total += item.count || 0;

      // Track individual categories
      if (item.defect_category) {
        if (!monthData.categories[item.defect_category]) {
          monthData.categories[item.defect_category] = 0;
        }
        monthData.categories[item.defect_category] += item.count || 0;
      }
    });

    // Convert to array and sort by month
    const result = Array.from(monthlyMap.values())
      .sort((a, b) => a.month.localeCompare(b.month))
      .map(item => {
        // Flatten categories into the main object
        const flattened = { ...item, ...item.categories };
        delete flattened.categories;
        return flattened;
      });

    return result;
  }, [data]);

  // Get top categories for lines
  const topCategories = useMemo(() => {
    if (selectedCategories && selectedCategories.length > 0) {
      return selectedCategories.slice(0, 5);
    }

    if (!data || !Array.isArray(data)) return [];

    const categoryTotals = new Map();

    data.forEach(item => {
      const cat = item.defect_category;
      if (!cat) return;
      categoryTotals.set(cat, (categoryTotals.get(cat) || 0) + (item.count || 0));
    });

    return Array.from(categoryTotals.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([cat]) => cat);
  }, [data, selectedCategories]);

  const colors = [
    '#ef4444', // red
    '#f97316', // orange
    '#eab308', // yellow
    '#22c55e', // green
    '#3b82f6', // blue
    '#8b5cf6', // purple
  ];

  const formatMonth = (monthStr) => {
    try {
      // Convert "2021-05" to "May '21"
      const [year, month] = monthStr.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1);
      const monthName = date.toLocaleDateString('en-US', { month: 'short' });
      const shortYear = year.slice(-2);
      return `${monthName} '${shortYear}`;
    } catch {
      return monthStr;
    }
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="monthly-tooltip">
        <p className="tooltip-label">{formatMonth(label)}</p>
        {payload
          .sort((a, b) => b.value - a.value)
          .map((entry, index) => (
            <div key={index} className="tooltip-row" style={{ color: entry.color }}>
              <span className="tooltip-name">{entry.name}:</span>
              <span className="tooltip-value">{formatNumber(entry.value)}</span>
            </div>
          ))}
      </div>
    );
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className="monthly-trends-empty">
        <TrendingUp size={32} color="#94a3b8" />
        <p>No trend data available</p>
      </div>
    );
  }

  return (
    <div className="monthly-trends-chart">
      <div className="monthly-trends-header">
        <TrendingUp size={20} />
        <h3>Monthly Defect Trends</h3>
        <span className="monthly-subtitle">
          {topCategories.length > 0 ? `Top ${topCategories.length} defect categories` : 'All defects over time'}
          {' · '}
          <span style={{ color: '#64748b', fontSize: '11px' }}>2015–present (data sparse before 2015)</span>
        </span>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="month"
              tickFormatter={formatMonth}
              stroke="#94a3b8"
              angle={-45}
              textAnchor="end"
              height={80}
              tick={{ fontSize: 12 }}
            />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
              formatter={(value) => (
                <span style={{ color: '#f1f5f9', fontSize: '13px' }}>{value}</span>
              )}
            />

            {/* Total line */}
            <Line
              type="monotone"
              dataKey="total"
              name="Total Defects"
              stroke="#94a3b8"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />

            {/* Individual category lines */}
            {topCategories.map((category, index) => (
              <Line
                key={category}
                type="monotone"
                dataKey={category}
                name={category}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <style jsx>{`
        .monthly-trends-chart {
          background: #1e293b;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .monthly-trends-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 20px;
          color: #f1f5f9;
        }

        .monthly-trends-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .monthly-subtitle {
          margin-left: auto;
          font-size: 13px;
          color: #94a3b8;
        }

        .chart-container {
          width: 100%;
          min-height: 400px;
        }

        .monthly-tooltip {
          background: rgba(15, 23, 42, 0.95);
          border: 1px solid #475569;
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }

        .tooltip-label {
          color: #f1f5f9;
          font-weight: 600;
          font-size: 14px;
          margin: 0 0 8px 0;
          padding-bottom: 8px;
          border-bottom: 1px solid #334155;
        }

        .tooltip-row {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          margin: 6px 0;
          font-size: 13px;
        }

        .tooltip-name {
          font-weight: 500;
        }

        .tooltip-value {
          font-weight: 700;
        }

        .monthly-trends-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          color: #94a3b8;
          text-align: center;
          background: #1e293b;
          border-radius: 12px;
        }

        .monthly-trends-empty p {
          margin-top: 12px;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
};

export default MonthlyTrendsChart;
