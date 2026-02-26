import React, { useState } from 'react';
import { useRiskHeatmapData } from '../hooks/useRiskHeatmapData';
import KpiRow from '../components/RiskHeatmap/KpiRow';
import Heatmap from '../components/RiskHeatmap/Heatmap';
import InsightsPanel from '../components/RiskHeatmap/InsightsPanel';
import RiskCharts from '../components/RiskHeatmap/RiskCharts';
import CellDetailModal from '../components/RiskHeatmap/CellDetailModal';
import { Filter, Eye, EyeOff } from 'lucide-react';

const RiskHeatmapPage = () => {
  const { mlHeatmap, historicalHeatmap, loading, error } = useRiskHeatmapData();
  const [selectedCellData, setSelectedCellData] = useState(null);
  const [showValues, setShowValues] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);

  // Filters (UI only for now)
  const [filters, setFilters] = useState({
    campus: 'All',
    building: 'All',
    year: '2024',
    systemSearch: ''
  });

  const handleCellClick = (cellData) => {
    setSelectedCellData(cellData);
  };

  const handleCloseModal = () => {
    setSelectedCellData(null);
  };

  const toggleShowValues = () => {
    setShowValues(!showValues);
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
          <div className="filter-group">
            <Filter size={16} />
            <select
              className="filter-select"
              value={filters.campus}
              onChange={(e) => setFilters({ ...filters, campus: e.target.value })}
            >
              <option value="All">All Campuses</option>
              <option value="Campus1">Campus 1</option>
              <option value="Campus2">Campus 2</option>
            </select>
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={filters.building}
              onChange={(e) => setFilters({ ...filters, building: e.target.value })}
            >
              <option value="All">All Buildings</option>
              <option value="Building1">Building 1</option>
              <option value="Building2">Building 2</option>
            </select>
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={filters.year}
              onChange={(e) => setFilters({ ...filters, year: e.target.value })}
            >
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2022">2022</option>
            </select>
          </div>

          <div className="filter-group search">
            <input
              type="text"
              className="filter-search"
              placeholder="Search systems..."
              value={filters.systemSearch}
              onChange={(e) => setFilters({ ...filters, systemSearch: e.target.value })}
            />
          </div>

          <button className="toggle-values-btn" onClick={toggleShowValues}>
            {showValues ? <EyeOff size={16} /> : <Eye size={16} />}
            {showValues ? 'Hide Values' : 'Show Values'}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <KpiRow mlHeatmap={mlHeatmap} />

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
              showValues={showValues}
            />
          </div>
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
