import { useState, useEffect } from 'react';

// Seeded random number generator for consistent mock data
const seededRandom = (seed) => {
  let x = Math.sin(seed++) * 10000;
  return x - Math.floor(x);
};

// Mock data generator for building-level heatmap (with consistent seed)
const generateMockBuildingHeatmap = () => {
  const universities = [10, 11, 12];
  const buildings = {
    10: [1, 2, 3, 4, 5],
    11: [1, 2, 3, 4],
    12: [1, 2, 3, 4, 5, 6]
  };
  const systems = [
    'HVAC', 'Electrical', 'Plumbing', 'Fire Protection',
    'Elevators', 'Roofing', 'Exterior Walls', 'Windows',
    'Interior Finishes', 'Site Improvements'
  ];

  const data = [];
  let seed = 12345; // Fixed seed for consistent results

  universities.forEach(uni => {
    buildings[uni].forEach(bldg => {
      systems.forEach(system => {
        for (let month = 1; month <= 12; month++) {
          // HVAC higher risk in winter (12, 1, 2) and summer (6, 7, 8)
          let baseRisk = 0.15;
          if (system === 'HVAC') {
            if ([12, 1, 2].includes(month)) baseRisk = 0.65; // Winter
            else if ([6, 7, 8].includes(month)) baseRisk = 0.55; // Summer
            else baseRisk = 0.25;
          } else if (system === 'Electrical') {
            baseRisk = 0.35 + seededRandom(seed++) * 0.15;
          } else if (system === 'Plumbing') {
            if ([12, 1, 2].includes(month)) baseRisk = 0.45; // Winter freeze
            else baseRisk = 0.25 + seededRandom(seed++) * 0.1;
          } else {
            baseRisk = 0.15 + seededRandom(seed++) * 0.25;
          }

          data.push({
            UniversityID: uni,
            BuildingID: bldg,
            SystemDescription: system,
            MonthNum: month,
            ml_risk: Math.min(0.95, baseRisk + (seededRandom(seed++) - 0.5) * 0.1),
            hist_asset_rate: Math.min(0.5, baseRisk * 0.5 + seededRandom(seed++) * 0.1),
            hist_shock_rate: Math.min(0.3, baseRisk * 0.3 + seededRandom(seed++) * 0.05),
            coverage: Math.floor(50 + seededRandom(seed++) * 200)
          });
        }
      });
    });
  });

  return data;
};

// Generate mock metadata for dropdowns
const generateMockMetadata = () => {
  return {
    universities: [10, 11, 12],
    buildings_by_university: {
      10: [1, 2, 3, 4, 5],
      11: [1, 2, 3, 4],
      12: [1, 2, 3, 4, 5, 6]
    }
  };
};

// Generate university-level aggregation (All Buildings) with consistent seed
const generateMockUniversityHeatmap = () => {
  const universities = [10, 11, 12];
  const systems = [
    'HVAC', 'Electrical', 'Plumbing', 'Fire Protection',
    'Elevators', 'Roofing', 'Exterior Walls', 'Windows',
    'Interior Finishes', 'Site Improvements'
  ];

  const data = [];
  let seed = 54321; // Different seed from building-level data

  universities.forEach(uni => {
    systems.forEach(system => {
      for (let month = 1; month <= 12; month++) {
        let baseRisk = 0.15;
        if (system === 'HVAC') {
          if ([12, 1, 2].includes(month)) baseRisk = 0.60;
          else if ([6, 7, 8].includes(month)) baseRisk = 0.50;
          else baseRisk = 0.22;
        } else if (system === 'Electrical') {
          baseRisk = 0.32 + seededRandom(seed++) * 0.12;
        } else if (system === 'Plumbing') {
          if ([12, 1, 2].includes(month)) baseRisk = 0.40;
          else baseRisk = 0.22 + seededRandom(seed++) * 0.08;
        } else {
          baseRisk = 0.12 + seededRandom(seed++) * 0.20;
        }

        data.push({
          UniversityID: uni,
          SystemDescription: system,
          MonthNum: month,
          ml_risk: Math.min(0.95, baseRisk + (seededRandom(seed++) - 0.5) * 0.1),
          hist_asset_rate: Math.min(0.5, baseRisk * 0.5 + seededRandom(seed++) * 0.1),
          hist_shock_rate: Math.min(0.3, baseRisk * 0.3 + seededRandom(seed++) * 0.05),
          coverage: Math.floor(200 + seededRandom(seed++) * 500)
        });
      }
    });
  });

  return data;
};

/**
 * Hook to load Risk Heatmap data with University and Building filtering
 *
 * @param {number|null} selectedUniversity - Selected UniversityID (10, 11, or 12)
 * @param {number|string|null} selectedBuilding - Selected BuildingID or 'all' for all buildings
 */
export const useRiskHeatmapData = (selectedUniversity = null, selectedBuilding = null) => {
  const [buildingData, setBuildingData] = useState([]);
  const [universityData, setUniversityData] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load raw data once on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        // TODO: Replace with actual API calls when backend is ready
        // const buildingResponse = await fetch('/api/heatmap/building');
        // const buildingData = await buildingResponse.json();
        // const uniResponse = await fetch('/api/heatmap/university');
        // const uniData = await uniResponse.json();
        // const metaResponse = await fetch('/api/heatmap/metadata');
        // const metaData = await metaResponse.json();

        // For now, use mock data
        const buildingData = generateMockBuildingHeatmap();
        const uniData = generateMockUniversityHeatmap();
        const metaData = generateMockMetadata();

        setBuildingData(buildingData);
        setUniversityData(uniData);
        setMetadata(metaData);
        setError(null);
      } catch (err) {
        console.error('Error loading heatmap data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Filter data based on selections
  const getFilteredData = () => {
    if (!selectedUniversity) {
      // No university selected - return empty
      return { mlHeatmap: [], historicalHeatmap: [] };
    }

    if (selectedBuilding === 'all' || !selectedBuilding) {
      // All buildings - use university-level aggregation
      const filtered = universityData.filter(row => row.UniversityID === selectedUniversity);

      return {
        mlHeatmap: filtered.map(row => ({
          SystemDescription: row.SystemDescription,
          MonthNum: row.MonthNum,
          ml_risk: row.ml_risk,
          coverage: row.coverage
        })),
        historicalHeatmap: filtered.map(row => ({
          SystemDescription: row.SystemDescription,
          MonthNum: row.MonthNum,
          hist_total_rate: row.hist_asset_rate + row.hist_shock_rate,
          hist_asset_rate: row.hist_asset_rate,
          hist_shock_rate: row.hist_shock_rate,
          coverage: row.coverage
        }))
      };
    } else {
      // Specific building selected
      const filtered = buildingData.filter(
        row => row.UniversityID === selectedUniversity && row.BuildingID === selectedBuilding
      );

      return {
        mlHeatmap: filtered.map(row => ({
          SystemDescription: row.SystemDescription,
          MonthNum: row.MonthNum,
          ml_risk: row.ml_risk,
          coverage: row.coverage
        })),
        historicalHeatmap: filtered.map(row => ({
          SystemDescription: row.SystemDescription,
          MonthNum: row.MonthNum,
          hist_total_rate: row.hist_asset_rate + row.hist_shock_rate,
          hist_asset_rate: row.hist_asset_rate,
          hist_shock_rate: row.hist_shock_rate,
          coverage: row.coverage
        }))
      };
    }
  };

  const { mlHeatmap, historicalHeatmap } = getFilteredData();

  return {
    mlHeatmap,
    historicalHeatmap,
    metadata,
    loading,
    error
  };
};

/**
 * Load data from CSV files (when pipeline outputs are available)
 */
export const loadDataFromCSV = async (mlPath, histPath) => {
  try {
    // Parse CSV manually or use a library like papaparse
    const mlResponse = await fetch(mlPath);
    const mlText = await mlResponse.text();
    const mlData = parseCSV(mlText);

    const histResponse = await fetch(histPath);
    const histText = await histResponse.text();
    const histData = parseCSV(histText);

    return { mlData, histData };
  } catch (error) {
    console.error('Error loading CSV:', error);
    throw error;
  }
};

// Simple CSV parser
const parseCSV = (text) => {
  const lines = text.trim().split('\n');
  const headers = lines[0].split(',');

  return lines.slice(1).map(line => {
    const values = line.split(',');
    const obj = {};
    headers.forEach((header, index) => {
      const value = values[index];
      // Try to parse as number
      obj[header] = isNaN(value) ? value : parseFloat(value);
    });
    return obj;
  });
};
