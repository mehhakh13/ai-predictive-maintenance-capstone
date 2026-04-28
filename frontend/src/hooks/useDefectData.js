import { useState, useEffect, useMemo } from 'react';
import { API_BASE_URL } from '../config';

export const useDefectData = (filters = {}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [apiMetadata, setApiMetadata] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Build query parameters
        const params = new URLSearchParams();

        if (filters.universityId && filters.universityId !== 'all') {
          params.append('universityId', filters.universityId);
        }

        if (filters.buildingId && filters.buildingId !== 'all') {
          params.append('buildingId', filters.buildingId);
        }

        if (filters.defectType && filters.defectType !== 'all') {
          params.append('defectType', filters.defectType);
        }

        if (filters.system && filters.system !== 'all') {
          params.append('system', filters.system);
        }

        if (filters.startDate) {
          params.append('startDate', filters.startDate);
        }

        if (filters.endDate) {
          params.append('endDate', filters.endDate);
        }

        params.append('limit', '100');

        const url = `${API_BASE_URL}/api/defect-intelligence?${params.toString()}`;

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        setRawData(result.data || []);
        setApiMetadata(result.metadata || null);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching defect data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [
    filters.universityId,
    filters.buildingId,
    filters.defectType,
    filters.system,
    filters.startDate,
    filters.endDate
  ]);

  // Calculate summary statistics from fetched data
  const summary = useMemo(() => {
    if (rawData.length === 0) {
      return {
        totalDefects: 0,
        mostFrequentDefect: { name: 'N/A', count: 0 },
        highestCostDefect: { name: 'N/A', cost: 0 },
        mostAffectedSystem: { name: 'N/A', count: 0 },
        totalCost: 0
      };
    }

    // Group by defect type
    const defectCounts = {};
    const defectCosts = {};
    const systemCounts = {};

    rawData.forEach(item => {
      // Defect counts
      defectCounts[item.defect_type] = (defectCounts[item.defect_type] || 0) + 1;

      // Defect costs
      defectCosts[item.defect_type] = (defectCosts[item.defect_type] || 0) + item.TotalCost;

      // System counts
      systemCounts[item.SystemDescription] = (systemCounts[item.SystemDescription] || 0) + 1;
    });

    // Find most frequent defect
    const mostFrequent = Object.entries(defectCounts).sort((a, b) => b[1] - a[1])[0];

    // Find highest cost defect
    const highestCost = Object.entries(defectCosts).sort((a, b) => b[1] - a[1])[0];

    // Find most affected system
    const mostAffected = Object.entries(systemCounts).sort((a, b) => b[1] - a[1])[0];

    // Total cost
    const totalCost = rawData.reduce((sum, item) => sum + item.TotalCost, 0);

    return {
      totalDefects: rawData.length,
      mostFrequentDefect: { name: mostFrequent[0], count: mostFrequent[1] },
      highestCostDefect: { name: highestCost[0], cost: highestCost[1] },
      mostAffectedSystem: { name: mostAffected[0], count: mostAffected[1] },
      totalCost
    };
  }, [rawData]);

  // Use metadata from API response
  const metadata = useMemo(() => {
    if (apiMetadata) {
      return apiMetadata;
    }

    // Fallback: compute from rawData if API didn't provide metadata
    const universities = [...new Set(rawData.map(item => ({ id: item.UniversityID, name: item.UniversityName })))];
    const buildings = [...new Set(rawData.map(item => ({ id: item.BuildingID, name: item.BuildingName })))];
    const defectTypes = [...new Set(rawData.map(item => item.defect_type))].sort();
    const systems = [...new Set(rawData.map(item => item.SystemDescription))].sort();

    // Remove duplicates
    const uniqueUniversities = Array.from(new Map(universities.map(u => [u.id, u])).values());
    const uniqueBuildings = Array.from(new Map(buildings.map(b => [b.id, b])).values());

    return {
      universities: uniqueUniversities,
      buildings: uniqueBuildings,
      defectTypes,
      systems
    };
  }, [rawData, apiMetadata]);

  return {
    data: rawData,
    summary,
    metadata,
    loading,
    error
  };
};
