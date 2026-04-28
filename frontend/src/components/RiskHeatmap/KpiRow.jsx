import React from 'react';
import KpiCard from '../KpiCard';
import { Activity, AlertTriangle, TrendingUp, Calendar, Database } from 'lucide-react';

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const KpiRow = ({ mlHeatmap, selectedYear }) => {
  const calculateKpis = () => {
    if (!mlHeatmap || mlHeatmap.length === 0) {
      return { avgRisk: 0, highRiskCells: 0, highestRiskSystem: 'N/A', keyMonth: 'N/A', keyMonthLabel: 'Worst Month', coverage: 0 };
    }

    const avgRisk = mlHeatmap.reduce((sum, item) => sum + item.ml_risk, 0) / mlHeatmap.length;
    const highRiskCells = mlHeatmap.filter(item => item.ml_risk >= 0.70).length;

    // Highest Risk System (by average risk across all months)
    const systemRisks = {};
    mlHeatmap.forEach(item => {
      if (!systemRisks[item.SystemDescription]) systemRisks[item.SystemDescription] = { total: 0, count: 0 };
      systemRisks[item.SystemDescription].total += item.ml_risk;
      systemRisks[item.SystemDescription].count += 1;
    });
    let highestRiskSystem = 'N/A';
    let maxAvgRisk = 0;
    Object.keys(systemRisks).forEach(sys => {
      const avg = systemRisks[sys].total / systemRisks[sys].count;
      if (avg > maxAvgRisk) { maxAvgRisk = avg; highestRiskSystem = sys; }
    });

    // Per-month averages
    const monthRisks = {};
    mlHeatmap.forEach(item => {
      if (!monthRisks[item.MonthNum]) monthRisks[item.MonthNum] = { total: 0, count: 0 };
      monthRisks[item.MonthNum].total += item.ml_risk;
      monthRisks[item.MonthNum].count += 1;
    });
    const monthAvg = m => monthRisks[m] ? monthRisks[m].total / monthRisks[m].count : 0;

    let keyMonth, keyMonthLabel;
    if (selectedYear) {
      // Specific year selected → show worst month in that year
      let worst = 1, worstRisk = 0;
      Object.keys(monthRisks).forEach(m => {
        const avg = monthAvg(parseInt(m));
        if (avg > worstRisk) { worstRisk = avg; worst = parseInt(m); }
      });
      keyMonth = MONTH_NAMES[worst - 1];
      keyMonthLabel = `Worst Month (${selectedYear})`;
    } else {
      // All years → find next upcoming high-risk month from today
      const currentMonth = new Date().getMonth() + 1; // 1-12
      let bestMonth = null, bestRisk = -1;
      for (let i = 1; i <= 12; i++) {
        const m = ((currentMonth - 1 + i) % 12) + 1; // next months wrapping around
        const avg = monthAvg(m);
        if (avg > bestRisk) { bestRisk = avg; bestMonth = m; }
      }
      keyMonth = bestMonth ? MONTH_NAMES[bestMonth - 1] : 'N/A';
      keyMonthLabel = 'Next High-Risk Month';
    }

    return { avgRisk, highRiskCells, highestRiskSystem, keyMonth, keyMonthLabel, coverage: mlHeatmap.length };
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
        title={kpis.keyMonthLabel}
        value={kpis.keyMonth}
        subtitle={selectedYear ? 'Highest avg risk in year' : 'Upcoming from today'}
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
