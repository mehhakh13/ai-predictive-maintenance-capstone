import React, { useState, useMemo } from 'react';
import { Search, Building2, Calendar, Brain, AlertTriangle, Loader2 } from 'lucide-react';
import { useExplainabilityData } from '../hooks/useExplainabilityData';
import SubsystemCard from '../components/Explainability/SubsystemCard';

const MONTH_NAMES = [
  '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

const Explainability = () => {
  const {
    buildings, loadingBuildings, buildingsError,
    explanation, loadingExplanation, explanationError,
    fetchExplanation,
  } = useExplainabilityData();

  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [buildingSearch, setBuildingSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');

  const filteredBuildings = useMemo(() =>
    buildings.filter(b =>
      b.building_name.toLowerCase().includes(buildingSearch.toLowerCase())
    ), [buildings, buildingSearch]
  );

  const availableMonths = useMemo(() => {
    if (!selectedBuilding) return [];
    return selectedBuilding.available_months || [];
  }, [selectedBuilding]);

  const availableYears = useMemo(() => {
    const years = [...new Set(availableMonths.map(m => m.year))].sort();
    return years;
  }, [availableMonths]);

  const monthsForYear = useMemo(() => {
    if (!selectedYear) return [];
    return availableMonths.filter(m => m.year === parseInt(selectedYear));
  }, [availableMonths, selectedYear]);

  const handleBuildingSelect = (b) => {
    setSelectedBuilding(b);
    setSelectedYear('');
    setSelectedMonth('');
  };

  const handleYearChange = (e) => {
    setSelectedYear(e.target.value);
    setSelectedMonth('');
  };

  const handleAnalyse = () => {
    if (!selectedBuilding || !selectedYear || !selectedMonth) return;
    fetchExplanation(selectedBuilding.building_id, parseInt(selectedYear), parseInt(selectedMonth));
  };

  const filteredSubsystems = useMemo(() => {
    if (!explanation?.subsystems) return [];
    if (riskFilter === 'high') return explanation.subsystems.filter(s => s.risk_prob >= 0.65);
    if (riskFilter === 'medium') return explanation.subsystems.filter(s => s.risk_prob >= 0.40 && s.risk_prob < 0.65);
    if (riskFilter === 'low') return explanation.subsystems.filter(s => s.risk_prob < 0.40);
    return explanation.subsystems;
  }, [explanation, riskFilter]);

  const stats = useMemo(() => {
    if (!explanation?.subsystems) return null;
    const s = explanation.subsystems;
    return {
      total: s.length,
      high: s.filter(x => x.risk_prob >= 0.65).length,
      medium: s.filter(x => x.risk_prob >= 0.40 && x.risk_prob < 0.65).length,
      low: s.filter(x => x.risk_prob < 0.40).length,
      avgRisk: s.reduce((a, b) => a + b.risk_prob, 0) / s.length,
    };
  }, [explanation]);

  return (
    <div style={{ minHeight: '100vh', background: '#0b1120', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif' }}>

      {/* Page header */}
      <div style={{ padding: '28px 32px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
          <Brain size={26} color="#6366f1" />
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>
            Explainability Panel
          </h1>
        </div>
        <p style={{ margin: 0, color: '#64748b', fontSize: 13 }}>
          SHAP-based feature attribution — understand why the model predicts high UPM risk for a specific building and month
        </p>
      </div>

      <div style={{ padding: '20px 32px', display: 'flex', gap: 24, alignItems: 'flex-start' }}>

        {/* Left: Controls */}
        <div style={{
          width: 300, flexShrink: 0,
          background: '#0f1a2e', border: '1px solid #1e2d45',
          borderRadius: 12, padding: 20,
        }}>

          {/* Building search */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>
              Building
            </label>
            <div style={{ position: 'relative', marginTop: 6 }}>
              <Search size={14} color="#64748b" style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="Search building name..."
                value={buildingSearch}
                onChange={e => setBuildingSearch(e.target.value)}
                style={{
                  width: '100%', boxSizing: 'border-box',
                  paddingLeft: 32, paddingRight: 10, paddingTop: 8, paddingBottom: 8,
                  background: '#131929', border: '1px solid #1e2d45',
                  borderRadius: 7, color: '#e2e8f0', fontSize: 12, outline: 'none',
                }}
              />
            </div>
          </div>

          {/* Building list */}
          <div style={{
            maxHeight: 220, overflowY: 'auto', marginBottom: 20,
            border: '1px solid #1e2d45', borderRadius: 7,
          }}>
            {loadingBuildings ? (
              <div style={{ padding: 16, color: '#64748b', fontSize: 12, textAlign: 'center' }}>Loading buildings…</div>
            ) : buildingsError ? (
              <div style={{ padding: 16, color: '#ef4444', fontSize: 12 }}>
                Backend not running.<br />Start it with:<br />
                <code style={{ fontSize: 11 }}>uvicorn backend.main:app --reload</code>
              </div>
            ) : (
              filteredBuildings.map(b => (
                <div
                  key={b.building_id}
                  onClick={() => handleBuildingSelect(b)}
                  style={{
                    padding: '8px 12px', cursor: 'pointer', fontSize: 12,
                    color: selectedBuilding?.building_id === b.building_id ? '#6366f1' : '#94a3b8',
                    background: selectedBuilding?.building_id === b.building_id ? 'rgba(99,102,241,0.1)' : 'transparent',
                    borderBottom: '1px solid #1a2540',
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}
                >
                  <Building2 size={13} />
                  <span>{b.building_name}</span>
                </div>
              ))
            )}
          </div>

          {/* Year selector */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>
              Year
            </label>
            <select
              value={selectedYear}
              onChange={handleYearChange}
              disabled={!selectedBuilding}
              style={{
                width: '100%', marginTop: 6,
                padding: '8px 10px',
                background: '#131929', border: '1px solid #1e2d45',
                borderRadius: 7, color: selectedBuilding ? '#e2e8f0' : '#475569', fontSize: 12, outline: 'none',
              }}
            >
              <option value="">Select year…</option>
              {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          {/* Month selector */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>
              Month
            </label>
            <select
              value={selectedMonth}
              onChange={e => setSelectedMonth(e.target.value)}
              disabled={!selectedYear}
              style={{
                width: '100%', marginTop: 6,
                padding: '8px 10px',
                background: '#131929', border: '1px solid #1e2d45',
                borderRadius: 7, color: selectedYear ? '#e2e8f0' : '#475569', fontSize: 12, outline: 'none',
              }}
            >
              <option value="">Select month…</option>
              {monthsForYear.map(m => (
                <option key={m.month} value={m.month}>
                  {MONTH_NAMES[m.month]} ({m.month})
                </option>
              ))}
            </select>
          </div>

          {/* Analyse button */}
          <button
            onClick={handleAnalyse}
            disabled={!selectedBuilding || !selectedYear || !selectedMonth || loadingExplanation}
            style={{
              width: '100%', padding: '10px 0',
              background: (!selectedBuilding || !selectedYear || !selectedMonth)
                ? '#1e2d45' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: (!selectedBuilding || !selectedYear || !selectedMonth) ? '#475569' : '#fff',
              border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 13,
              cursor: (!selectedBuilding || !selectedYear || !selectedMonth) ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            {loadingExplanation
              ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Analysing…</>
              : <><Calendar size={15} /> Analyse</>
            }
          </button>
        </div>

        {/* Right: Results */}
        <div style={{ flex: 1, minWidth: 0 }}>

          {/* Error */}
          {explanationError && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 10, padding: '14px 18px', marginBottom: 16,
              color: '#fca5a5', fontSize: 13,
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <AlertTriangle size={16} />
              {explanationError}
            </div>
          )}

          {/* Stats bar */}
          {stats && (
            <div style={{ display: 'flex', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
              {[
                { label: 'Subsystems', value: stats.total, color: '#6366f1' },
                { label: 'High Risk', value: stats.high, color: '#ef4444' },
                { label: 'Medium Risk', value: stats.medium, color: '#f59e0b' },
                { label: 'Low Risk', value: stats.low, color: '#22c55e' },
                { label: 'Avg Risk', value: `${(stats.avgRisk * 100).toFixed(0)}%`, color: '#94a3b8' },
              ].map(s => (
                <div key={s.label} style={{
                  background: '#0f1a2e', border: '1px solid #1e2d45',
                  borderRadius: 8, padding: '10px 16px', flex: '1 1 100px', minWidth: 90,
                }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{s.label}</div>
                </div>
              ))}

              {/* Filter pills */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto', flexWrap: 'wrap' }}>
                {['all', 'high', 'medium', 'low'].map(f => (
                  <button key={f} onClick={() => setRiskFilter(f)} style={{
                    padding: '5px 12px', borderRadius: 20,
                    border: `1px solid ${riskFilter === f ? '#6366f1' : '#1e2d45'}`,
                    background: riskFilter === f ? 'rgba(99,102,241,0.15)' : 'transparent',
                    color: riskFilter === f ? '#a5b4fc' : '#64748b',
                    fontSize: 11, fontWeight: 600, cursor: 'pointer', textTransform: 'capitalize',
                  }}>
                    {f === 'all' ? 'All' : `${f.charAt(0).toUpperCase() + f.slice(1)} risk`}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Title when data loaded */}
          {explanation && (
            <div style={{ marginBottom: 14 }}>
              <h2 style={{ margin: '0 0 2px', fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>
                {explanation.building_name}
              </h2>
              <span style={{ color: '#64748b', fontSize: 12 }}>
                {MONTH_NAMES[explanation.month]} {explanation.year} &nbsp;·&nbsp;
                {explanation.subsystems.length} subsystems
              </span>
            </div>
          )}

          {/* Subsystem cards */}
          {filteredSubsystems.map((s, i) => (
            <SubsystemCard
              key={`${s.subsystem}-${i}`}
              subsystem={s}
              base={s.shap_base}
              year={explanation.year}
              month={explanation.month}
              defaultOpen={i === 0}
            />
          ))}

          {/* No results */}
          {explanation && filteredSubsystems.length === 0 && (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '40px 0', fontSize: 13 }}>
              No subsystems match the current filter.
            </div>
          )}

          {/* Empty state */}
          {!explanation && !loadingExplanation && !explanationError && (
            <div style={{
              textAlign: 'center', padding: '80px 40px',
              background: '#0f1a2e', border: '1px dashed #1e2d45',
              borderRadius: 12, color: '#475569',
            }}>
              <Brain size={48} color="#1e2d45" style={{ marginBottom: 16 }} />
              <div style={{ fontSize: 15, fontWeight: 600, color: '#334155', marginBottom: 8 }}>
                No analysis yet
              </div>
              <div style={{ fontSize: 13 }}>
                Select a building, year, and month on the left,<br />then click <strong style={{ color: '#64748b' }}>Analyse</strong>.
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        select option { background: #131929; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 3px; }
      `}</style>
    </div>
  );
};

export default Explainability;
