import React, { useState, useMemo } from 'react';
import { Filter, BarChart3, TrendingUp, Info } from 'lucide-react';
import { useCostAnalysisData } from '../hooks/useCostAnalysisData';
import KpiRow from '../components/CostAnalysis/KpiRow';
import CostBreakdownChart from '../components/CostAnalysis/CostBreakdownChart';
import CostTrendChart from '../components/CostAnalysis/CostTrendChart';
import TopContributors from '../components/CostAnalysis/TopContributors';
import CostDistribution from '../components/CostAnalysis/CostDistribution';
import OutlierTable from '../components/CostAnalysis/OutlierTable';

/**
 * CostAnalysisPage Component
 * Main dashboard for Maintenance Cost Analysis
 * Features:
 * - PPM vs UPM cost comparison
 * - System-level cost breakdown
 * - Monthly cost trends
 * - Top cost contributors
 * - Cost distribution visualization
 * - Outlier detection and analysis
 */
const CostAnalysisPage = () => {
  // State for filters
  const [filters, setFilters] = useState({
    dateRange: {
      start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)), // Last 12 months
      end: new Date()
    },
    university: 'All',
    building: 'All',
    system: '',
    maintenanceType: 'All'
  });

  // State for UI toggles
  const [showPPMvsUPM, setShowPPMvsUPM] = useState(false);
  const [distributionView, setDistributionView] = useState('ppm-upm');
  const [showOutlierModal, setShowOutlierModal] = useState(false);
  const [showExplainThis, setShowExplainThis] = useState(false);

  // Load data with current filters
  const { filteredData, loading, error, aggregations } = useCostAnalysisData(filters);

  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleDateRangeChange = (range) => {
    const now = new Date();
    let start, end = now;

    switch (range) {
      case '3m':
        start = new Date(now.setMonth(now.getMonth() - 3));
        break;
      case '6m':
        start = new Date(now.setMonth(now.getMonth() - 6));
        break;
      case '12m':
        start = new Date(now.setFullYear(now.getFullYear() - 1));
        break;
      case '24m':
        start = new Date(now.setFullYear(now.getFullYear() - 2));
        break;
      default:
        start = new Date(now.setFullYear(now.getFullYear() - 1));
    }

    setFilters(prev => ({
      ...prev,
      dateRange: { start, end }
    }));
  };

  // Get unique values for filter dropdowns
  const uniqueUniversities = useMemo(() => {
    if (!filteredData) return [];
    return ['All', ...new Set(filteredData.map(item => item.UniversityID))];
  }, [filteredData]);

  const uniqueBuildings = useMemo(() => {
    if (!filteredData) return [];
    return ['All', ...new Set(filteredData.map(item => item.BuildingID))];
  }, [filteredData]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading cost analysis data...</p>
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
    <div className="cost-analysis-page">
      {/* Top Bar */}
      <div className="page-header">
        <div className="header-title-row">
          <h1 className="page-title">Maintenance Cost Analysis</h1>
          <button
            className="explain-btn"
            onClick={() => setShowExplainThis(!showExplainThis)}
          >
            <Info size={16} />
            Explain This
          </button>
        </div>

        {showExplainThis && (
          <div className="explain-panel">
            <p>
              <strong>Maintenance Cost Analysis</strong> measures the financial impact of
              maintenance activities across labor, material, and other costs. We compare
              <strong> Planned Preventive Maintenance (PPM)</strong> vs{' '}
              <strong>Unplanned Maintenance (UPM)</strong> to identify budget risks and
              cost-saving opportunities.
            </p>
            <p>
              <strong>Key Insight:</strong> UPM typically costs 40-60% more than PPM due to
              emergency labor rates, expedited parts, and reactive scheduling. Increasing PPM
              investment often reduces total maintenance costs.
            </p>
          </div>
        )}

        {/* Filters Bar */}
        <div className="filters-bar">
          <div className="filter-group">
            <Filter size={16} />
            <select
              className="filter-select"
              value={filters.dateRange.label || '12m'}
              onChange={(e) => handleDateRangeChange(e.target.value)}
            >
              <option value="3m">Last 3 Months</option>
              <option value="6m">Last 6 Months</option>
              <option value="12m">Last 12 Months</option>
              <option value="24m">Last 24 Months</option>
            </select>
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={filters.university}
              onChange={(e) => handleFilterChange('university', e.target.value)}
            >
              {uniqueUniversities.map(uni => (
                <option key={uni} value={uni}>
                  {uni === 'All' ? 'All Universities' : uni}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={filters.building}
              onChange={(e) => handleFilterChange('building', e.target.value)}
            >
              {uniqueBuildings.map(building => (
                <option key={building} value={building}>
                  {building === 'All' ? 'All Buildings' : building}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group search">
            <input
              type="text"
              className="filter-search"
              placeholder="Search systems..."
              value={filters.system}
              onChange={(e) => handleFilterChange('system', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={filters.maintenanceType}
              onChange={(e) => handleFilterChange('maintenanceType', e.target.value)}
            >
              <option value="All">All Types</option>
              <option value="PPM">PPM Only</option>
              <option value="UPM">UPM Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <KpiRow aggregations={aggregations} totalWorkOrders={filteredData.length} />

      {/* Main Content - 2 Column Layout */}
      <div className="main-content">
        {/* Left Column */}
        <div className="content-left">
          {/* Cost Breakdown Chart */}
          <div className="section-card">
            <div className="section-header">
              <div>
                <h2 className="section-title">
                  <BarChart3 size={20} style={{ marginRight: '0.5rem' }} />
                  Cost Breakdown by System
                </h2>
                <p className="section-subtitle">
                  {showPPMvsUPM
                    ? 'PPM vs UPM cost comparison'
                    : 'Labor, Material, and Other costs'}
                </p>
              </div>
              <button
                className="toggle-btn"
                onClick={() => setShowPPMvsUPM(!showPPMvsUPM)}
              >
                {showPPMvsUPM ? 'Show Cost Types' : 'Show PPM vs UPM'}
              </button>
            </div>
            <CostBreakdownChart data={filteredData} showPPMvsUPM={showPPMvsUPM} />
          </div>

          {/* Cost Trend Chart */}
          <div className="section-card" style={{ marginTop: '1.5rem' }}>
            <div className="section-header">
              <h2 className="section-title">
                <TrendingUp size={20} style={{ marginRight: '0.5rem' }} />
                Monthly Cost Trends
              </h2>
              <p className="section-subtitle">PPM vs UPM cost over time</p>
            </div>
            <CostTrendChart data={filteredData} />
          </div>
        </div>

        {/* Right Column */}
        <div className="content-right">
          {/* Top Contributors */}
          <div className="section-card">
            <TopContributors data={filteredData} />
          </div>

          {/* Cost Distribution */}
          <div className="section-card" style={{ marginTop: '1.5rem' }}>
            <div className="section-header">
              <div>
                <h3 className="section-title">Cost Distribution</h3>
                <p className="section-subtitle">
                  {distributionView === 'ppm-upm'
                    ? 'PPM vs UPM share'
                    : 'Labor vs Material vs Other'}
                </p>
              </div>
              <button
                className="toggle-btn-small"
                onClick={() =>
                  setDistributionView(prev =>
                    prev === 'ppm-upm' ? 'cost-type' : 'ppm-upm'
                  )
                }
              >
                Switch
              </button>
            </div>
            <CostDistribution data={filteredData} view={distributionView} />
          </div>
        </div>
      </div>

      {/* Bottom Section: Outlier Table */}
      <div className="bottom-section">
        <div className="section-card">
          <OutlierTable
            data={filteredData}
            threshold={aggregations.outlierThreshold}
          />
        </div>
      </div>

      {/* Outlier Modal (if triggered) */}
      {showOutlierModal && (
        <OutlierTable
          data={filteredData}
          threshold={aggregations.outlierThreshold}
          isModal={true}
          onClose={() => setShowOutlierModal(false)}
        />
      )}
    </div>
  );
};

export default CostAnalysisPage;
