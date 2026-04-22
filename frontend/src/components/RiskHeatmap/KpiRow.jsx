import React from 'react';
import KpiCard from '../KpiCard';
import { Activity, AlertTriangle, TrendingUp, Calendar, Database } from 'lucide-react';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const KpiRow = ({ mlHeatmap }) => {
  // Calculate KPIs from ML heatmap data
  const calculateKpis = () => {
    if (!mlHeatmap || mlHeatmap.length === 0) {
      return {
        avgRisk: 0,
        highRiskCells: 0,
        highestRiskSystem: 'N/A',
        worstMonth: 'N/A',
        coverage: 0
      };
    }

    // Average Asset UPM Risk
    const avgRisk = mlHeatmap.reduce((sum, item) => sum + item.ml_risk, 0) / mlHeatmap.length;

    // High-Risk Cells (ml_risk >= 0.70)
    const highRiskCells = mlHeatmap.filter(item => item.ml_risk >= 0.70).length;

    // Highest Risk System (by average risk)
    const systemRisks = {};
    mlHeatmap.forEach(item => {
      if (!systemRisks[item.SystemDescription]) {
        systemRisks[item.SystemDescription] = { total: 0, count: 0 };
      }
      systemRisks[item.SystemDescription].total += item.ml_risk;
      systemRisks[item.SystemDescription].count += 1;
    });

    let highestRiskSystem = 'N/A';
    let maxAvgRisk = 0;
    Object.keys(systemRisks).forEach(system => {
      const avg = systemRisks[system].total / systemRisks[system].count;
      if (avg > maxAvgRisk) {
        maxAvgRisk = avg;
        highestRiskSystem = system;
      }
    });

    // Worst Month (month with highest average risk)
    const monthRisks = {};
    mlHeatmap.forEach(item => {
      if (!monthRisks[item.MonthNum]) {
        monthRisks[item.MonthNum] = { total: 0, count: 0 };
      }
      monthRisks[item.MonthNum].total += item.ml_risk;
      monthRisks[item.MonthNum].count += 1;
    });

    let worstMonth = 1;
    let maxMonthRisk = 0;
    Object.keys(monthRisks).forEach(month => {
      const avg = monthRisks[month].total / monthRisks[month].count;
      if (avg > maxMonthRisk) {
        maxMonthRisk = avg;
        worstMonth = parseInt(month);
      }
    });

    // Coverage (number of system-months)
    const coverage = mlHeatmap.length;

    return {
      avgRisk,
      highRiskCells,
      highestRiskSystem,
      worstMonth: MONTH_NAMES[worstMonth - 1],
      coverage
    };
  };

  const kpis = calculateKpis();

  return (
    <div className="kpi-row">
      <KpiCard
        title="Avg Asset UPM Risk"
        value={`${(kpis.avgRisk * 100).toFixed(1)}%`}
        subtitle="Predicted monthly probability"
        icon={Activity}
      />
      <KpiCard
        title="High-Risk Cells"
        value={kpis.highRiskCells}
        subtitle="Risk ≥ 70%"
        icon={AlertTriangle}
        trend={kpis.highRiskCells > 20 ? 'up' : kpis.highRiskCells > 0 ? 'neutral' : 'down'}
      />
      <KpiCard
        title="Highest Risk System"
        value={kpis.highestRiskSystem}
        subtitle="By average risk"
        icon={TrendingUp}
      />
      <KpiCard
        title="Worst Month"
        value={kpis.worstMonth}
        subtitle="Highest avg risk"
        icon={Calendar}
      />
      <KpiCard
        title="Coverage"
        value={kpis.coverage}
        subtitle="System-month combinations"
        icon={Database}
      />
    </div>
  );
};

export default KpiRow;
