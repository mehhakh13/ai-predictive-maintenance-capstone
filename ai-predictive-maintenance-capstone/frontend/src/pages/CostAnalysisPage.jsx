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
 */
const CostAnalysisPage = () => {
  // State for filters — defaults to "All Time" so real historical data shows
  const [filters, setFilters] = useState({
    dateRange: {
      start: new Date('2000-01-01'),
      end: new Date()
    },
    university: 'All',
    building: 'All',
    system: '',
    maintenanceType: 'All'
  });

  const [showPPMvsUPM, setShowPPMvsUPM] = useState(false);
  const [distributionView, setDistributionView] = useState('ppm-upm');
  const [showOutlierModal, setShowOutlierModal] = useState(false);
  const [showExplainThis, setShowExplainThis] = useState(false);

  const { filteredData, loading, error, aggregations } = useCostAnalysisData(filters);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

const handleDateRangeChange = (range) => {
    const end = new Date();  // today
    let start;

    switch (range) {
      case '3m':
        start = new Date();
        start.setMonth(start.getMonth() - 3);
        break;
      case '6m':
        start = new Date();
        start.setMonth(start.getMonth() - 6);
        break;
      case '12m':
        start = new Date();
        start.setFullYear(start.getFullYear() - 1);
        break;
      case '24m':
        start = new Date();
        start.setFullYear(start.getFullYear() - 2);
        break;
      case '5y':
        start = new Date();
        start.setFullYear(start.getFullYear() - 5);
        break;
      case '10y':
        start = new Date();
        start.setFullYear(start.getFullYear() - 10);
        break;
      case 'all':
        start = new Date('2000-01-01');
        break;
      default:
        start = new Date('2000-01-01');
    }

    setFilters(prev => ({
      ...prev,
      dateRange: { start, end }
    }));
  };

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

        <div className="filters-bar">
          <div className="filter-group">
            <Filter size={16} />
            <select
              className="filter-select"
              value={filters.dateRange.label || 'all'}
              onChange={(e) => handleDateRangeChange(e.target.value)}
            >
              <option value="all">All Time</option>
              <option value="10y">Last 10 Years</option>
              <option value="5y">Last 5 Years</option>
              <option value="24m">Last 24 Months</option>
              <option value="12m">Last 12 Months</option>
              <option value="6m">Last 6 Months</option>
              <option value="3m">Last 3 Months</option>
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

      <KpiRow aggregations={aggregations} totalWorkOrders={filteredData.length} />

      <div className="main-content">
        <div className="content-left">
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

        <div className="content-right">
          <div className="section-card">
            <TopContributors data={filteredData} />
          </div>

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

      <div className="bottom-section">
        <div className="section-card">
          <OutlierTable
            data={filteredData}
            threshold={aggregations.outlierThreshold}
          />
        </div>
      </div>

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