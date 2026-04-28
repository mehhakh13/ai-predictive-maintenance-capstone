import React, { useState, useEffect } from 'react';
import { useRiskHeatmapData } from '../hooks/useRiskHeatmapData';
import KpiRow from '../components/RiskHeatmap/KpiRow';
import Heatmap from '../components/RiskHeatmap/Heatmap';
import SubsystemHeatmap from '../components/RiskHeatmap/SubsystemHeatmap';
import InsightsPanel from '../components/RiskHeatmap/InsightsPanel';
import RiskCharts from '../components/RiskHeatmap/RiskCharts';
import CellDetailModal from '../components/RiskHeatmap/CellDetailModal';
import { Filter, Eye, EyeOff, Building2, School, CalendarDays } from 'lucide-react';
import ForecastStrip from '../components/RiskHeatmap/ForecastStrip';

const RiskHeatmapPage = () => {
  // University and Building selection state
  const [selectedUniversity, setSelectedUniversity] = useState(10);
  const [selectedBuilding, setSelectedBuilding] = useState('all');
  const [selectedYear, setSelectedYear] = useState(null); // null = all years
  const [availableBuildings, setAvailableBuildings] = useState([]);
  const [availableYears, setAvailableYears] = useState([]);

  const { mlHeatmap, historicalHeatmap, subsystemData, metadata, loading, error } = useRiskHeatmapData(
    selectedUniversity,
    selectedBuilding,
    selectedYear
  );

  const [selectedCellData, setSelectedCellData] = useState(null);
  const [showValues, setShowValues] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedSystem, setSelectedSystem] = useState(null); // For drill-down

  // Additional filters
  const [systemSearch, setSystemSearch] = useState('');

  // Update available buildings and years when university or metadata changes
  useEffect(() => {
    if (metadata && selectedUniversity) {
      const buildings = metadata.buildings_by_university[selectedUniversity] || [];
      const years = metadata.years_by_university?.[selectedUniversity] || [];
      setAvailableBuildings(buildings);
      setAvailableYears(years);
      setSelectedBuilding('all');
      setSelectedYear(null);
    }
  }, [selectedUniversity, metadata]);

  const handleCellClick = (cellData) => {
    setSelectedCellData(cellData);
  };

  const handleCloseModal = () => {
    setSelectedCellData(null);
  };

  const toggleShowValues = () => {
    setShowValues(!showValues);
  };

  const handleSystemRowClick = (system) => {
    setSelectedSystem(system);
  };

  const handleCloseSubsystemView = () => {
    setSelectedSystem(null);
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading risk heatmap data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-container">
          <p>Error loading data: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="risk-heatmap-page">
      {/* Top Bar */}
      <div className="page-header">
        <h1 className="page-title">System Risk Heatmap</h1>

        {/* Filters */}
        <div className="filters-bar">
          {/* University Filter */}
          <div className="filter-group">
            <School size={16} />
            <select
              className="filter-select"
              value={selectedUniversity || ''}
              onChange={(e) => setSelectedUniversity(Number(e.target.value))}
            >
              {metadata && metadata.universities.map(uni => (
                <option key={uni} value={uni}>University {uni}</option>
              ))}
            </select>
          </div>

          {/* Building Filter */}
          <div className="filter-group">
            <Building2 size={16} />
            <select
              className="filter-select"
              value={selectedBuilding}
              onChange={(e) => setSelectedBuilding(e.target.value === 'all' ? 'all' : e.target.value)}
            >
              <option value="all">All Buildings</option>
              {availableBuildings.map(bldg => (
                <option key={bldg} value={bldg}>
                  {metadata?.building_names?.[bldg] || `Building ${bldg}`}
                </option>
              ))}
            </select>
          </div>

          {/* Year Filter */}
          <div className="filter-group">
            <CalendarDays size={16} />
            <select
              className="filter-select"
              value={selectedYear || 'all'}
              onChange={(e) => setSelectedYear(e.target.value === 'all' ? null : Number(e.target.value))}
            >
              <option value="all">All Years</option>
              {availableYears.map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* System Search */}
          <div className="filter-group search">
            <Filter size={16} />
            <input
              type="text"
              className="filter-search"
              placeholder="Search systems..."
              value={systemSearch}
              onChange={(e) => setSystemSearch(e.target.value)}
            />
          </div>

          {/* Toggle Values Button */}
          <button className="toggle-values-btn" onClick={toggleShowValues}>
            {showValues ? <EyeOff size={16} /> : <Eye size={16} />}
            {showValues ? 'Hide Values' : 'Show Values'}
          </button>
        </div>
      </div>

      {/* Selection Info */}
      <div style={{ padding: '0 1rem', marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
        Showing data for: University {selectedUniversity} —&nbsp;
        {selectedBuilding === 'all' ? 'All Buildings' : (metadata?.building_names?.[selectedBuilding] || selectedBuilding)}
        &nbsp;—&nbsp;{selectedYear ? selectedYear : 'All Years (historical avg)'}
      </div>

      {/* KPI Cards */}
      <KpiRow mlHeatmap={mlHeatmap} selectedYear={selectedYear} />

      {/* Next 3 Months Forecast — only when viewing all-years data */}
      {!selectedYear && <ForecastStrip mlHeatmap={mlHeatmap} />}

      {/* Main Content - 2 Column Layout */}
      <div className="main-content">
        {/* Left: Heatmap */}
        <div className="content-left">
          <div className="section-card">
            <div className="section-header">
              <h2 className="section-title">Risk Heatmap</h2>
              <p className="section-subtitle">
                Predicted Asset-Driven UPM Risk by System and Month
              </p>
            </div>
            <Heatmap
              mlHeatmap={mlHeatmap}
              historicalHeatmap={historicalHeatmap}
              onCellClick={handleCellClick}
              onRowClick={handleSystemRowClick}
              showValues={showValues}
            />
          </div>

          {/* Subsystem Drill-Down Heatmap */}
          {selectedSystem && subsystemData && (
            <SubsystemHeatmap
              selectedSystem={selectedSystem}
              subsystemData={subsystemData}
              onCellClick={handleCellClick}
              showValues={showValues}
              onClose={handleCloseSubsystemView}
            />
          )}
        </div>

        {/* Right: Insights Panel */}
        <div className="content-right">
          <InsightsPanel
            mlHeatmap={mlHeatmap}
            selectedMonth={selectedMonth}
          />
        </div>
      </div>

      {/* Bottom Section: Charts */}
      <div className="bottom-section">
        <div className="section-card">
          <RiskCharts
            mlHeatmap={mlHeatmap}
            selectedMonth={selectedMonth}
          />
        </div>
      </div>

      {/* Cell Detail Modal */}
      {selectedCellData && (
        <CellDetailModal
          cellData={selectedCellData}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default RiskHeatmapPage;
