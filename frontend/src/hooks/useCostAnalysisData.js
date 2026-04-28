import { useState, useEffect, useMemo } from 'react';

/**
 * Mock data generator for cost analysis
 * Generates realistic work order cost data with PPM/UPM distribution
 */
const generateMockCostData = () => {
  const systems = [
    'HVAC', 'Electrical', 'Plumbing', 'Fire Protection',
    'Elevators', 'Roofing', 'Exterior Walls', 'Windows',
    'Interior Finishes', 'Site Improvements', 'Foundation',
    'Structural Frame', 'Security Systems', 'Telecommunications', 'Lighting'
  ];

  const universities = ['University A', 'University B', 'University C'];
  const buildings = ['Building 1', 'Building 2', 'Building 3', 'Building 4', 'Building 5'];
  const maintenanceTypes = ['PPM', 'UPM'];
  const priorities = ['Low', 'Medium', 'High', 'Critical'];

  const data = [];
  const startDate = new Date('2024-01-01');
  const endDate = new Date();

  // Generate 500-800 work orders
  const numOrders = 500 + Math.floor(Math.random() * 300);

  for (let i = 0; i < numOrders; i++) {
    const system = systems[Math.floor(Math.random() * systems.length)];
    const maintenanceType = Math.random() < 0.35 ? 'PPM' : 'UPM'; // 35% PPM, 65% UPM

    // Generate random date within range
    const randomTime = startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime());
    const woStartDate = new Date(randomTime);

    // Cost varies by system and maintenance type
    let baseLaborCost = 500 + Math.random() * 2000;
    let baseMaterialCost = 200 + Math.random() * 1500;
    let baseOtherCost = 50 + Math.random() * 300;

    // HVAC and Elevators tend to be more expensive
    if (system === 'HVAC') {
      baseLaborCost *= 1.5;
      baseMaterialCost *= 1.3;
    } else if (system === 'Elevators') {
      baseLaborCost *= 1.8;
      baseMaterialCost *= 1.5;
    }

    // UPM tends to be more expensive than PPM (emergency work)
    if (maintenanceType === 'UPM') {
      baseLaborCost *= 1.4;
      baseMaterialCost *= 1.2;
      baseOtherCost *= 1.3;
    }

    // Create some outliers (5% chance of 3-5x cost)
    if (Math.random() < 0.05) {
      const multiplier = 3 + Math.random() * 2;
      baseLaborCost *= multiplier;
      baseMaterialCost *= multiplier;
      baseOtherCost *= multiplier;
    }

    const laborCost = Math.round(baseLaborCost * 100) / 100;
    const materialCost = Math.round(baseMaterialCost * 100) / 100;
    const otherCost = Math.round(baseOtherCost * 100) / 100;
    const totalCost = Math.round((laborCost + materialCost + otherCost) * 100) / 100;

    data.push({
      WOId: `WO-${String(i + 1).padStart(6, '0')}`,
      WOStartDate: woStartDate.toISOString().split('T')[0],
      SystemDescription: system,
      SubsystemDescription: `${system} Subsystem ${Math.floor(Math.random() * 3) + 1}`,
      MaintenanceType: maintenanceType,
      WOPriority: priorities[Math.floor(Math.random() * priorities.length)],
      UniversityID: universities[Math.floor(Math.random() * universities.length)],
      BuildingID: buildings[Math.floor(Math.random() * buildings.length)],
      LaborCost: laborCost,
      MaterialCost: materialCost,
      OtherCost: otherCost,
      TotalCost: totalCost,
      State: 'CA',
      Country: 'USA'
    });
  }

  return data;
};

/**
 * Custom hook to load and filter cost analysis data
 * Provides mock data by default, can be easily swapped to API calls
 *
 * @param {Object} filters - Filter criteria for the data
 * @returns {Object} Filtered data, loading state, error state, and aggregations
 */
export const useCostAnalysisData = (filters = {}) => {
  const [rawData, setRawData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        // Load from CSV file
        const csvData = await loadCostDataFromCSV('/cost_data_sample.csv');

        // Map CSV columns to expected format
        const mappedData = csvData.map(row => ({
          WOId: row.WOID || row.WOId,
          WOStartDate: row.WOStartDate,
          SystemDescription: row.SystemDescription,
          SubsystemDescription: row.SubsystemDescription,
          MaintenanceType: row['PPM/UPM'] || row.MaintenanceType,
          WOPriority: row.WOPriority,
          UniversityID: row.UniversityID,
          BuildingID: row.BuildingID,
          LaborCost: parseFloat(row.LaborCost) || 0,
          MaterialCost: parseFloat(row.MaterialCost) || 0,
          OtherCost: parseFloat(row.OtherCost) || 0,
          TotalCost: parseFloat(row.TotalCost) || 0,
          State: row['State/Province'] || row.State,
          Country: row.Country
        }));

        setRawData(mappedData);
        setError(null);
      } catch (err) {
        console.error('Error loading cost data:', err);
        setError(err.message);

        // Fallback to mock data if CSV fails
        console.warn('Falling back to mock data');
        const data = generateMockCostData();
        setRawData(data);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Filter data based on current filters
  const filteredData = useMemo(() => {
    let filtered = [...rawData];

    // Date range filter
    if (filters.dateRange) {
      const { start, end } = filters.dateRange;
      filtered = filtered.filter(item => {
        const itemDate = new Date(item.WOStartDate);
        return itemDate >= start && itemDate <= end;
      });
    }

    // University filter
    if (filters.university && filters.university !== 'All') {
      filtered = filtered.filter(item => item.UniversityID === filters.university);
    }

    // Building filter
    if (filters.building && filters.building !== 'All') {
      filtered = filtered.filter(item => item.BuildingID === filters.building);
    }

    // System filter (search)
    if (filters.system && filters.system !== '') {
      const searchTerm = filters.system.toLowerCase();
      filtered = filtered.filter(item =>
        item.SystemDescription.toLowerCase().includes(searchTerm)
      );
    }

    // Maintenance type filter
    if (filters.maintenanceType && filters.maintenanceType !== 'All') {
      filtered = filtered.filter(item => item.MaintenanceType === filters.maintenanceType);
    }

    return filtered;
  }, [rawData, filters]);

  // Compute aggregations
  const aggregations = useMemo(() => {
    if (filteredData.length === 0) {
      return {
        totalCost: 0,
        avgCostPerWO: 0,
        ppmTotalCost: 0,
        upmTotalCost: 0,
        mostExpensiveSystem: 'N/A',
        outlierCount: 0,
        outlierThreshold: 0
      };
    }

    // Total cost
    const totalCost = filteredData.reduce((sum, item) => sum + item.TotalCost, 0);

    // Average cost per work order
    const avgCostPerWO = totalCost / filteredData.length;

    // PPM vs UPM costs
    const ppmData = filteredData.filter(item => item.MaintenanceType === 'PPM');
    const upmData = filteredData.filter(item => item.MaintenanceType === 'UPM');
    const ppmTotalCost = ppmData.reduce((sum, item) => sum + item.TotalCost, 0);
    const upmTotalCost = upmData.reduce((sum, item) => sum + item.TotalCost, 0);

    // Most expensive system
    const systemCosts = {};
    filteredData.forEach(item => {
      if (!systemCosts[item.SystemDescription]) {
        systemCosts[item.SystemDescription] = 0;
      }
      systemCosts[item.SystemDescription] += item.TotalCost;
    });
    const mostExpensiveSystem = Object.keys(systemCosts).reduce((a, b) =>
      systemCosts[a] > systemCosts[b] ? a : b
    , 'N/A');

    // Outlier detection (P95)
    const sortedCosts = filteredData.map(item => item.TotalCost).sort((a, b) => a - b);
    const p95Index = Math.floor(sortedCosts.length * 0.95);
    const outlierThreshold = sortedCosts[p95Index] || 0;
    const outlierCount = filteredData.filter(item => item.TotalCost > outlierThreshold).length;

    return {
      totalCost,
      avgCostPerWO,
      ppmTotalCost,
      upmTotalCost,
      mostExpensiveSystem,
      outlierCount,
      outlierThreshold
    };
  }, [filteredData]);

  return {
    rawData,
    filteredData,
    loading,
    error,
    aggregations
  };
};

/**
 * Load data from CSV file (for pipeline integration)
 * @param {string} csvPath - Path to CSV file
 * @returns {Promise<Array>} Parsed data array
 */
export const loadCostDataFromCSV = async (csvPath) => {
  try {
    const response = await fetch(csvPath);
    const text = await response.text();
    return parseCSV(text);
  } catch (error) {
    console.error('Error loading CSV:', error);
    throw error;
  }
};

// Robust CSV parser that handles quoted fields and commas
const parseCSV = (text) => {
  const lines = text.trim().split('\n');

  // Parse CSV line respecting quotes
  const parseLine = (line) => {
    const result = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];

      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  const headers = parseLine(lines[0]);

  return lines.slice(1).map(line => {
    if (!line.trim()) return null;

    const values = parseLine(line);
    const obj = {};

    headers.forEach((header, index) => {
      const value = values[index] || '';
      const trimmedValue = value.trim();

      // Parse numbers for cost and numeric fields
      if (header.includes('Cost') || header.includes('Hours') ||
          header.includes('Temp') || header.includes('pressure') ||
          header.includes('Humidity') || header.includes('Wind') ||
          header.includes('Precipitation') || header.includes('Snow') ||
          header.includes('Cloudness') || header.includes('UniversityID') ||
          header.includes('BuildingID')) {
        obj[header] = parseFloat(trimmedValue) || 0;
      } else {
        obj[header] = trimmedValue;
      }
    });
    return obj;
  }).filter(row => row !== null);
};
