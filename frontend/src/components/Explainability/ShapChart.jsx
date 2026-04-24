import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, Cell, ResponsiveContainer,
} from 'recharts';

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: '#1e2533', border: '1px solid #2d3548',
      borderRadius: 6, padding: '8px 12px', fontSize: 12,
    }}>
      <div style={{ fontWeight: 600, color: '#e2e8f0', marginBottom: 4 }}>{d.label}</div>
      {d.display_value && (
        <div style={{ color: '#94a3b8' }}>Value: <span style={{ color: '#e2e8f0' }}>{d.display_value}</span></div>
      )}
      <div style={{ color: '#94a3b8', marginTop: 2 }}>
        Impact:{' '}
        <span style={{ color: d.shap_value >= 0 ? '#f87171' : '#4ade80', fontWeight: 600 }}>
          {d.shap_value >= 0 ? '+' : ''}{d.shap_value.toFixed(4)}
        </span>
      </div>
      <div style={{ color: '#64748b', marginTop: 2, fontStyle: 'italic' }}>
        {d.direction === 'increases' ? 'Increases risk ↑' : 'Reduces risk ↓'}
      </div>
    </div>
  );
};

const ShapChart = ({ contributors, baseValue }) => {
  if (!contributors?.length) return null;

  const data = contributors.map(c => ({
    ...c,
    absValue: Math.abs(c.shap_value),
    // truncate long labels
    shortLabel: c.label.length > 28 ? c.label.slice(0, 26) + '…' : c.label,
  }));

  const maxAbs = Math.max(...data.map(d => d.absValue), 0.01);
  const domain = [-maxAbs * 1.15, maxAbs * 1.15];

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 30 + 40)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3548" horizontal={false} />
        <XAxis
          type="number"
          domain={domain}
          tickCount={5}
          tickFormatter={v => v.toFixed(2)}
          tick={{ fill: '#64748b', fontSize: 10 }}
          axisLine={{ stroke: '#2d3548' }}
        />
        <YAxis
          type="category"
          dataKey="shortLabel"
          width={160}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
        <ReferenceLine x={0} stroke="#475569" strokeWidth={1.5} />
        <Bar dataKey="shap_value" radius={[0, 3, 3, 0]} maxBarSize={18}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.shap_value >= 0 ? '#ef4444' : '#22c55e'}
              fillOpacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default ShapChart;
