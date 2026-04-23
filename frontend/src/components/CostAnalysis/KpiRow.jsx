import React from 'react';
import { DollarSign, TrendingUp, AlertTriangle, Layers } from 'lucide-react';
import { formatCurrency, formatNumber } from '../../utils/format';

/**
 * KpiRow Component
 * Displays key performance indicators for cost analysis
 *
 * @param {Object} aggregations - Computed aggregations from the data hook
 * @param {number} totalWorkOrders - Total number of work orders in filtered dataset
 */
const KpiRow = ({ aggregations, totalWorkOrders }) => {
  const {
    totalCost,
    avgCostPerWO,
    ppmTotalCost,
    upmTotalCost,
    mostExpensiveSystem,
    outlierCount
  } = aggregations;

  // Calculate PPM vs UPM ratio
  const ppmPercent = totalCost > 0 ? (ppmTotalCost / totalCost) * 100 : 0;
  const upmPercent = totalCost > 0 ? (upmTotalCost / totalCost) * 100 : 0;

  const kpis = [
    {
      title: 'Total Cost',
      value: formatCurrency(totalCost),
      subtitle: `Across ${formatNumber(totalWorkOrders)} work orders`,
      icon: DollarSign,
      color: '#3b82f6'
    },
    {
      title: 'Avg Cost per WO',
      value: formatCurrency(avgCostPerWO),
      subtitle: 'Mean maintenance cost',
      icon: TrendingUp,
      color: '#10b981'
    },
    {
      title: 'PPM vs UPM Cost',
      value: formatCurrency(ppmTotalCost),
      subtitle: `PPM: ${ppmPercent.toFixed(1)}% | UPM: ${upmPercent.toFixed(1)}%`,
      secondaryValue: formatCurrency(upmTotalCost),
      icon: Layers,
      color: '#f59e0b'
    },
    {
      title: 'Most Expensive System',
      value: mostExpensiveSystem,
      subtitle: 'Highest total maintenance cost',
      icon: AlertTriangle,
      color: '#ef4444',
      isText: true
    },
    {
      title: 'Cost Outliers',
      value: formatNumber(outlierCount),
      subtitle: 'Work orders above P95 threshold',
      icon: AlertTriangle,
      color: '#8b5cf6'
    }
  ];

  return (
    <div className="kpi-row">
      {kpis.map((kpi, index) => (
        <div key={index} className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-title">{kpi.title}</span>
            <kpi.icon className="kpi-card-icon" size={20} style={{ color: kpi.color }} />
          </div>
          <div className="kpi-card-value" style={kpi.isText ? { fontSize: '1.25rem' } : {}}>
            {kpi.value}
          </div>
          {kpi.secondaryValue && (
            <div className="kpi-card-value" style={{ fontSize: '1.25rem', marginTop: '0.25rem' }}>
              {kpi.secondaryValue}
            </div>
          )}
          <div className="kpi-card-subtitle">{kpi.subtitle}</div>
        </div>
      ))}
    </div>
  );
};

export default KpiRow;
