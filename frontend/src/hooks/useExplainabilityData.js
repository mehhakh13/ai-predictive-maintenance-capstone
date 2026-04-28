import { useState, useEffect } from 'react';
import { API_BASE_URL as API_BASE } from '../config';

export const useExplainabilityData = () => {
  const [buildings, setBuildings] = useState([]);
  const [loadingBuildings, setLoadingBuildings] = useState(true);
  const [buildingsError, setBuildingsError] = useState(null);

  const [explanation, setExplanation] = useState(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [explanationError, setExplanationError] = useState(null);

  useEffect(() => {
    const fetchBuildings = async () => {
      try {
        setLoadingBuildings(true);
        const res = await fetch(`${API_BASE}/api/shap/buildings`);
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        const data = await res.json();
        setBuildings(data);
      } catch (err) {
        setBuildingsError(err.message);
      } finally {
        setLoadingBuildings(false);
      }
    };
    fetchBuildings();
  }, []);

  const fetchExplanation = async (buildingId, year, month) => {
    try {
      setLoadingExplanation(true);
      setExplanationError(null);
      setExplanation(null);
      const res = await fetch(
        `${API_BASE}/api/shap/explain?building_id=${encodeURIComponent(buildingId)}&year=${year}&month=${month}`
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setExplanation(data);
    } catch (err) {
      setExplanationError(err.message);
    } finally {
      setLoadingExplanation(false);
    }
  };

  return {
    buildings,
    loadingBuildings,
    buildingsError,
    explanation,
    loadingExplanation,
    explanationError,
    fetchExplanation,
  };
};
