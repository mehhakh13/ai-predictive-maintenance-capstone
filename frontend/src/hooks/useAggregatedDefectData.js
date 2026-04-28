import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Hook to fetch aggregated defect intelligence data
 * Fetches pre-computed summary tables from backend
 */
const useAggregatedDefectData = (filters = {}) => {
  const [data, setData] = useState({
    summary: null,
    systemDefects: null,
    buildingDefects: null,
    monthlyTrends: null,
    impactRanking: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAggregatedData = async () => {
      setLoading(true);
      setError(null);

      try {
        const { universityId, buildingId, defectCategory, startDate, endDate } = filters;

        // Build query parameters
        const buildQueryParams = (params) => {
          const query = new URLSearchParams();
          Object.entries(params).forEach(([key, value]) => {
            if (value && value !== 'all') {
              query.append(key, value);
            }
          });
          return query.toString();
        };

        // Fetch all aggregated endpoints in parallel
        const [summaryRes, systemRes, buildingRes, monthlyRes, impactRes] = await Promise.all([
          // 1. Defect Summary
          fetch(`${API_BASE_URL}/api/defects/summary?${buildQueryParams({
            universityId,
            limit: 50
          })}`),

          // 2. System-Defect breakdown
          fetch(`${API_BASE_URL}/api/defects/by-system?${buildQueryParams({
            universityId,
            limit: 200
          })}`),

          // 3. Building-Defect breakdown
          fetch(`${API_BASE_URL}/api/defects/by-building?${buildQueryParams({
            universityId,
            buildingId,
            sortBy: 'total_impact',
            limit: 200
          })}`),

          // 4. Monthly Trends
          fetch(`${API_BASE_URL}/api/defects/monthly?${buildQueryParams({
            defectCategory,
            startDate,
            endDate,
            limit: 1000
          })}`),

          // 5. Impact Ranking
          fetch(`${API_BASE_URL}/api/defects/impact?${buildQueryParams({
            universityId,
            limit: 50
          })}`)
        ]);

        // Check for errors
        if (!summaryRes.ok || !systemRes.ok || !buildingRes.ok || !monthlyRes.ok || !impactRes.ok) {
          throw new Error('Failed to fetch aggregated data');
        }

        // Parse responses
        const [summaryData, systemData, buildingData, monthlyData, impactData] = await Promise.all([
          summaryRes.json(),
          systemRes.json(),
          buildingRes.json(),
          monthlyRes.json(),
          impactRes.json()
        ]);

        setData({
          summary: summaryData.data || [],
          systemDefects: systemData.data || [],
          buildingDefects: buildingData.data || buildingData.top_buildings || [],
          monthlyTrends: monthlyData.data || [],
          impactRanking: impactData.data || [],
          metadata: {
            summary: summaryData,
            system: systemData,
            building: buildingData,
            monthly: monthlyData,
            impact: impactData
          }
        });

      } catch (err) {
        console.error('Error fetching aggregated defect data:', err);
        setError(err.message || 'Failed to load aggregated data');
        setData({
          summary: [],
          systemDefects: [],
          buildingDefects: [],
          monthlyTrends: [],
          impactRanking: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAggregatedData();
  }, [
    filters.universityId,
    filters.buildingId,
    filters.defectCategory,
    filters.startDate,
    filters.endDate
  ]);

  return { data, loading, error };
};

export default useAggregatedDefectData;
