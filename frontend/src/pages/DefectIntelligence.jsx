import React, { useState } from 'react';
import { AlertCircle, TrendingUp, Wrench, Hash } from 'lucide-react';
import { useDefectData } from '../hooks/useDefectData';
import useAggregatedDefectData from '../hooks/useAggregatedDefectData';
import KpiCard from '../components/KpiCard';
import FiltersBar from '../components/DefectIntelligence/FiltersBar';
import DefectBarChart from '../components/DefectIntelligence/DefectBarChart';
import SystemHeatmap from '../components/DefectIntelligence/SystemHeatmap';
import DefectTable from '../components/DefectIntelligence/DefectTable';
import ImpactRanking from '../components/DefectIntelligence/ImpactRanking';
import BuildingRiskView from '../components/DefectIntelligence/BuildingRiskView';
import MonthlyTrendsChart from '../components/DefectIntelligence/MonthlyTrendsChart';

const DefectIntelligence = () => {
  const [filters, setFilters] = useState({
    universityId: 'all',
    buildingId: 'all',
    defectType: 'all',
    system: 'all',
    startDate: '',
    endDate: ''
  });

  const [selectedCell, setSelectedCell] = useState(null);

  const { data, summary, metadata, loading, error } = useDefectData(filters);
  const { data: aggData, loading: aggLoading, error: aggError } = useAggregatedDefectData(filters);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setSelectedCell(null);
  };

  const handleBarClick = (data) => {
    if (data && data.name) {
      setFilters(prev => ({ ...prev, defectType: data.name }));
    }
  };

  const handleHeatmapCellClick = (cellData) => {
    setSelectedCell(cellData);
    setFilters(prev => ({
      ...prev,
      system: cellData.system,
      defectType: cellData.defectType
    }));
  };

  const handleRowClick = (row) => {
    console.log('Row clicked:', row);
  };

  const handleDefectClick = (defectCategory) => {
    setFilters(prev => ({ ...prev, defectType: defectCategory }));
  };

  const handleBuildingClick = (buildingId) => {
    setFilters(prev => ({ ...prev, buildingId }));
  };

  if (error) {
    return (
      <div className="page-container">
        <div className="error-message">Error loading defect data: {error}</div>
      </div>
    );
  }

  return (
    <div className="page-container defect-intelligence-page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Defect Intelligence Dashboard</h1>
        <p className="page-subtitle">
          Analyze failure patterns and root causes from maintenance data
        </p>
      </div>

      {/* Filters Bar */}
      <FiltersBar
        filters={filters}
        onFilterChange={handleFilterChange}
        metadata={metadata}
      />

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KpiCard
          title="Total Defects"
          value={summary.totalDefects}
          icon={AlertCircle}
          subtitle="Identified defects"
        />
        <KpiCard
          title="Most Frequent Defect"
          value={summary.mostFrequentDefect.name}
          icon={TrendingUp}
          subtitle={`${summary.mostFrequentDefect.count} occurrences`}
        />
        <KpiCard
          title="Most Affected System"
          value={summary.mostAffectedSystem.name}
          icon={Wrench}
          subtitle={`${summary.mostAffectedSystem.count} defects`}
        />
        <KpiCard
          title="Defect Types Found"
          value={summary.uniqueDefectTypes}
          icon={Hash}
          subtitle="Distinct categories"
        />
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        <div className="section-card">
          {loading
            ? <div className="loading-spinner">Loading defect data...</div>
            : <DefectBarChart data={data} onBarClick={handleBarClick} />}
        </div>
      </div>

      {/* Impact Ranking & Building Risk - Side by Side */}
      <div className="insights-section">
        <div className="insights-grid">
          <div className="section-card">
            {aggLoading
              ? <div className="loading-spinner">Loading rankings...</div>
              : <ImpactRanking data={aggData.impactRanking} onDefectClick={handleDefectClick} />}
          </div>
          <div className="section-card">
            {aggLoading
              ? <div className="loading-spinner">Loading buildings...</div>
              : <BuildingRiskView data={aggData.buildingDefects} onBuildingClick={handleBuildingClick} />}
          </div>
        </div>
      </div>

      {/* Monthly Trends */}
      <div className="section-card trends-section">
        {aggLoading
          ? <div className="loading-spinner">Loading trends...</div>
          : <MonthlyTrendsChart
              data={aggData.monthlyTrends}
              selectedCategories={filters.defectType !== 'all' ? [filters.defectType] : []}
            />}
      </div>

      {/* Heatmap Section */}
      <div className="section-card heatmap-section">
        <div className="heatmap-header">
          <h3>System × Defect Analysis</h3>
        </div>
        {aggLoading
          ? <div className="loading-spinner">Loading heatmap...</div>
          : <SystemHeatmap
              data={aggData.systemDefects || []}
              onCellClick={handleHeatmapCellClick}
            />}
        {selectedCell && (
          <div className="selected-cell-info">
            <strong>Selected:</strong> {selectedCell.system} × {selectedCell.defectType}
            {' | '}
            Count: {selectedCell.count}
          </div>
        )}
      </div>

      {/* Drill-Down Table */}
      <div className="section-card table-section">
        <DefectTable data={data} onRowClick={handleRowClick} />
      </div>
    </div>
  );
};

export default DefectIntelligence;
