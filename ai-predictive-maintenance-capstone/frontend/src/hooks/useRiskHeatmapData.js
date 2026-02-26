import { useState, useEffect } from 'react';

// Mock data generator based on pipeline CSV schema
const generateMockMLHeatmap = () => {
  const systems = [
    'HVAC', 'Electrical', 'Plumbing', 'Fire Protection',
    'Elevators', 'Roofing', 'Exterior Walls', 'Windows',
    'Interior Finishes', 'Site Improvements', 'Foundation',
    'Structural Frame', 'Security Systems', 'Telecommunications', 'Other'
  ];

  const data = [];
  systems.forEach(system => {
    for (let month = 1; month <= 12; month++) {
      // HVAC higher risk in winter (12, 1, 2) and summer (6, 7, 8)
      let baseRisk = 0.15;
      if (system === 'HVAC') {
        if ([12, 1, 2].includes(month)) baseRisk = 0.65; // Winter
        else if ([6, 7, 8].includes(month)) baseRisk = 0.55; // Summer
        else baseRisk = 0.25;
      } else if (system === 'Electrical') {
        baseRisk = 0.35 + Math.random() * 0.15;
      } else if (system === 'Plumbing') {
        if ([12, 1, 2].includes(month)) baseRisk = 0.45; // Winter freeze
        else baseRisk = 0.25 + Math.random() * 0.1;
      } else {
        baseRisk = 0.15 + Math.random() * 0.25;
      }

      data.push({
        SystemDescription: system,
        MonthNum: month,
        ml_risk: Math.min(0.95, baseRisk + (Math.random() - 0.5) * 0.1),
        coverage: Math.floor(50 + Math.random() * 200)
      });
    }
  });

  return data;
};

const generateMockHistoricalHeatmap = () => {
  const systems = [
    'HVAC', 'Electrical', 'Plumbing', 'Fire Protection',
    'Elevators', 'Roofing', 'Exterior Walls', 'Windows',
    'Interior Finishes', 'Site Improvements', 'Foundation',
    'Structural Frame', 'Security Systems', 'Telecommunications', 'Other'
  ];

  const data = [];
  systems.forEach(system => {
    for (let month = 1; month <= 12; month++) {
      let totalRate = 0.12;
      let assetRate = 0.08;
      let shockRate = 0.04;

      if (system === 'HVAC') {
        if ([12, 1, 2, 6, 7, 8].includes(month)) {
          totalRate = 0.18;
          assetRate = 0.13;
          shockRate = 0.05;
        }
      } else if (system === 'Plumbing') {
        if ([12, 1, 2].includes(month)) {
          totalRate = 0.15;
          assetRate = 0.10;
          shockRate = 0.05;
        }
      }

      data.push({
        SystemDescription: system,
        MonthNum: month,
        hist_total_rate: totalRate + (Math.random() - 0.5) * 0.02,
        hist_asset_rate: assetRate + (Math.random() - 0.5) * 0.02,
        hist_shock_rate: shockRate + (Math.random() - 0.5) * 0.01,
        coverage: Math.floor(100 + Math.random() * 400)
      });
    }
  });

  return data;
};

/**
 * Hook to load Risk Heatmap data
 * Can be easily switched to API calls when backend is ready
 */
export const useRiskHeatmapData = () => {
  const [mlHeatmap, setMlHeatmap] = useState([]);
  const [historicalHeatmap, setHistoricalHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        // TODO: Replace with actual API calls when backend is ready
        // const mlResponse = await fetch('/api/heatmap/ml');
        // const mlData = await mlResponse.json();
        // const histResponse = await fetch('/api/heatmap/historical');
        // const histData = await histResponse.json();

        // For now, use mock data
        const mlData = generateMockMLHeatmap();
        const histData = generateMockHistoricalHeatmap();

        setMlHeatmap(mlData);
        setHistoricalHeatmap(histData);
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

  return { mlHeatmap, historicalHeatmap, loading, error };
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
