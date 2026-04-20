import React from 'react';
import { Filter } from 'lucide-react';

const FiltersBar = ({ filters, onFilterChange, metadata }) => {
  return (
    <div className="defect-filters-bar">
      <div className="filters-header">
        <Filter size={20} />
        <span>Filters</span>
      </div>

      <div className="filters-grid">
        <div className="filter-group">
          <label>University</label>
          <select
            value={filters.universityId || 'all'}
            onChange={(e) => onFilterChange({ ...filters, universityId: e.target.value, buildingId: 'all' })}
          >
            <option value="all">All Universities</option>
            {metadata.universities.map(uni => (
              <option key={uni.id} value={uni.id}>{uni.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Building</label>
          <select
            value={filters.buildingId || 'all'}
            onChange={(e) => onFilterChange({ ...filters, buildingId: e.target.value })}
          >
            <option value="all">All Buildings</option>
            {metadata.buildings.map(building => (
              <option key={building.id} value={building.id}>{building.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Defect Type</label>
          <select
            value={filters.defectType || 'all'}
            onChange={(e) => onFilterChange({ ...filters, defectType: e.target.value })}
          >
            <option value="all">All Defects</option>
            {metadata.defectTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>System</label>
          <select
            value={filters.system || 'all'}
            onChange={(e) => onFilterChange({ ...filters, system: e.target.value })}
          >
            <option value="all">All Systems</option>
            {metadata.systems.map(system => (
              <option key={system} value={system}>{system}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Start Date</label>
          <input
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => onFilterChange({ ...filters, startDate: e.target.value })}
          />
        </div>

        <div className="filter-group">
          <label>End Date</label>
          <input
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => onFilterChange({ ...filters, endDate: e.target.value })}
          />
        </div>
      </div>

      <button
        className="reset-filters-btn"
        onClick={() => onFilterChange({
          universityId: 'all',
          buildingId: 'all',
          defectType: 'all',
          system: 'all',
          startDate: '',
          endDate: ''
        })}
      >
        Reset Filters
      </button>
    </div>
  );
};

export default FiltersBar;
