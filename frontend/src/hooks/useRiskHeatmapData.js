import { useState, useEffect, useRef, useMemo } from 'react';

const API = '/api/risk-heatmap';

export const useRiskHeatmapData = (selectedUniversity, selectedBuilding) => {
  const [universityData, setUniversityData] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Per-building cache so we don't re-fetch on every re-render
  const buildingCache = useRef({});
  const [buildingData, setBuildingData] = useState([]);

  // Load university-level data + metadata once on mount
  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const [uniRes, metaRes] = await Promise.all([
          fetch(`${API}/university?universityId=${selectedUniversity}`),
          fetch(`${API}/metadata`),
        ]);

        if (!uniRes.ok) throw new Error(`University heatmap: ${uniRes.status}`);
        if (!metaRes.ok) throw new Error(`Metadata: ${metaRes.status}`);

        const [uniRows, meta] = await Promise.all([uniRes.json(), metaRes.json()]);
        setUniversityData(uniRows);
        setMetadata(meta);
      } catch (err) {
        console.error('Failed to load heatmap data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [selectedUniversity]);

  // Lazily fetch building-level data when a specific building is selected
  useEffect(() => {
    if (!selectedBuilding || selectedBuilding === 'all') {
      setBuildingData([]);
      return;
    }

    if (buildingCache.current[selectedBuilding]) {
      setBuildingData(buildingCache.current[selectedBuilding]);
      return;
    }

    const fetchBuilding = async () => {
      try {
        const res = await fetch(
          `${API}/building?buildingId=${encodeURIComponent(selectedBuilding)}&universityId=${selectedUniversity}`
        );
        if (!res.ok) throw new Error(`Building heatmap: ${res.status}`);
        const rows = await res.json();
        buildingCache.current[selectedBuilding] = rows;
        setBuildingData(rows);
      } catch (err) {
        console.error('Failed to load building data:', err);
        setError(err.message);
      }
    };

    fetchBuilding();
  }, [selectedBuilding, selectedUniversity]);

  // Aggregate to system-level for the main heatmap
  const filteredData = useMemo(() => {
    if (!universityData.length && !buildingData.length) {
      return { mlHeatmap: [], historicalHeatmap: [], subsystemData: [], metadata };
    }

    const source = selectedBuilding === 'all' ? universityData : buildingData;

    const subsystemData = source.map(row => ({
      SystemDescription: row.SystemDescription,
      SubsystemDescription: row.SubsystemDescription,
      MonthNum: row.MonthNum,
      ml_risk: row.ml_risk,
      hist_asset_rate: row.hist_asset_rate,
      hist_shock_rate: row.hist_shock_rate,
      BuildingName: row.BuildingName || 'All Buildings',
      coverage: row.coverage,
    }));

    // Roll up subsystems → systems
    const bySystemMonth = {};
    source.forEach(row => {
      const key = `${row.SystemDescription}_${row.MonthNum}`;
      if (!bySystemMonth[key]) {
        bySystemMonth[key] = {
          SystemDescription: row.SystemDescription,
          MonthNum: row.MonthNum,
          ml_risk_sum: 0,
          hist_asset_sum: 0,
          hist_shock_sum: 0,
          coverage_sum: 0,
          count: 0,
        };
      }
      const agg = bySystemMonth[key];
      agg.ml_risk_sum += row.ml_risk || 0;
      agg.hist_asset_sum += row.hist_asset_rate || 0;
      agg.hist_shock_sum += row.hist_shock_rate || 0;
      agg.coverage_sum += row.coverage || 0;
      agg.count += 1;
    });

    const mlHeatmap = Object.values(bySystemMonth).map(agg => ({
      SystemDescription: agg.SystemDescription,
      MonthNum: agg.MonthNum,
      ml_risk: agg.ml_risk_sum / agg.count,
      coverage: agg.coverage_sum,
    }));

    const historicalHeatmap = Object.values(bySystemMonth).map(agg => ({
      SystemDescription: agg.SystemDescription,
      MonthNum: agg.MonthNum,
      hist_asset_rate: agg.hist_asset_sum / agg.count,
      hist_shock_rate: agg.hist_shock_sum / agg.count,
    }));

    return { mlHeatmap, historicalHeatmap, subsystemData, metadata };
  }, [universityData, buildingData, selectedBuilding, metadata]);

  return { ...filteredData, loading, error };
};
