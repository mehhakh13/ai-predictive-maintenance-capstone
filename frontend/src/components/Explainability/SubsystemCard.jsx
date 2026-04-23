import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, CheckCircle, AlertCircle, BarChart2 } from 'lucide-react';
import ShapChart from './ShapChart';
import DefectRecords from './DefectRecords';

const riskConfig = (prob) => {
  if (prob >= 0.65) return { label: 'High Risk', color: '#ef4444', bg: 'rgba(239,68,68,0.1)', Icon: AlertTriangle };
  if (prob >= 0.40) return { label: 'Medium Risk', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', Icon: AlertCircle };
  return { label: 'Low Risk', color: '#22c55e', bg: 'rgba(34,197,94,0.1)', Icon: CheckCircle };
};

// Convert a contributor into a plain-English phrase describing its impact
const describeContributor = (c) => {
  const v = c.feature_value;
  const isPositive = c.shap_value > 0;

  switch (c.feature) {
    case 'upm_last_1m':
      if (!isPositive) return v === 0 ? 'no failures last month' : null;
      return v === 1 ? '1 unplanned failure last month' : `${Math.round(v)} unplanned failures last month`;

    case 'upm_last_3m':
      if (!isPositive) return v === 0 ? 'no failures in the past 3 months' : null;
      return `${Math.round(v)} failure${Math.round(v) !== 1 ? 's' : ''} in the past 3 months`;

    case 'upm_last_6m':
      if (!isPositive) return v === 0 ? 'no failures in the past 6 months' : null;
      return `${Math.round(v)} failure${Math.round(v) !== 1 ? 's' : ''} in the past 6 months`;

    case 'months_since_upm':
      if (isPositive) {
        if (v <= 1) return 'failed just last month';
        if (v <= 3) return `last failure only ${Math.round(v)} months ago`;
        return `failure ${Math.round(v)} months ago`;
      }
      return v >= 12 ? `no failures in over ${Math.round(v)} months` : `stable for ${Math.round(v)} months`;

    case 'min_temp':
      if (isPositive && v < -5) return `extreme cold (${v.toFixed(1)}°C)`;
      if (isPositive && v < 0) return `freezing temperature (${v.toFixed(1)}°C)`;
      if (!isPositive && v > 5) return `mild temperature (${v.toFixed(1)}°C)`;
      return null;

    case 'avg_temp':
    case 'max_temp':
      if (isPositive && v < -3) return `cold weather (avg ${v.toFixed(1)}°C)`;
      if (!isPositive && v > 10) return `warm conditions (${v.toFixed(1)}°C)`;
      return null;

    case 'temp_range':
      if (isPositive && v > 10) return `large temperature swings (${v.toFixed(1)}°C range)`;
      return null;

    case 'humidity':
      if (isPositive && v > 85) return `high humidity (${v.toFixed(0)}%)`;
      if (!isPositive && v < 60) return `low humidity (${v.toFixed(0)}%)`;
      return null;

    case 'precipitation':
      if (isPositive && v > 5) return `heavy rainfall (${v.toFixed(1)} mm)`;
      return null;

    case 'snow':
      if (isPositive && v > 2) return `snowfall (${v.toFixed(1)} mm)`;
      return null;

    case 'fci':
      if (isPositive && v > 0.6) return `deteriorating facility (FCI ${v.toFixed(2)})`;
      if (!isPositive && v < 0.3) return `good facility condition (FCI ${v.toFixed(2)})`;
      return null;

    case 'building_age':
      if (isPositive && v > 40) return `aging building (${Math.round(v)} years old)`;
      if (!isPositive && v < 20) return `relatively new building`;
      return null;

    case 'avg_total_cost':
      if (isPositive && v > 400) return `high avg repair cost ($${Math.round(v)})`;
      return null;

    case 'wo_count':
      if (isPositive && v > 5) return `${Math.round(v)} work orders this month`;
      return null;

    case 'avg_wo_duration':
      if (isPositive && v > 30) return `long repair times (avg ${Math.round(v)} days)`;
      return null;

    default:
      if (c.feature.startsWith('subsystem_') && isPositive && c.feature_value === 1)
        return `subsystem type has elevated base risk`;
      return null;
  }
};

const generateExplanation = (subsystem) => {
  const { risk_prob, contributors } = subsystem;
  const positive = contributors.filter(c => c.shap_value > 0.05);
  const negative = contributors.filter(c => c.shap_value < -0.05);

  const posReasons = positive.map(describeContributor).filter(Boolean);
  const negReasons = negative.map(describeContributor).filter(Boolean);

  if (risk_prob >= 0.65) {
    if (posReasons.length === 0)
      return 'This subsystem is at high risk based on its historical maintenance pattern.';
    if (posReasons.length === 1)
      return `At high risk because of ${posReasons[0]}.`;
    return `At high risk mainly due to ${posReasons[0]} and ${posReasons[1]}.`;
  }

  if (risk_prob >= 0.40) {
    if (posReasons.length > 0 && negReasons.length > 0)
      return `Moderate risk — ${posReasons[0]} raises concern, partially offset by ${negReasons[0]}.`;
    if (posReasons.length > 0)
      return `Moderate risk driven by ${posReasons[0]}.`;
    return 'Moderate risk with mixed contributing factors.';
  }

  // Low risk
  if (negReasons.length === 0)
    return 'Low risk — no significant risk factors detected.';
  if (negReasons.length === 1)
    return `Low risk — ${negReasons[0]}.`;
  return `Low risk — ${negReasons[0]} and ${negReasons[1]}.`;
};

const SubsystemCard = ({ subsystem, base, year, month, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  const { label, color, bg, Icon } = riskConfig(subsystem.risk_prob);
  const explanation = generateExplanation(subsystem);

  return (
    <div style={{
      background: '#131929',
      border: `1px solid ${open ? color + '55' : '#1e2d45'}`,
      borderRadius: 10,
      marginBottom: 10,
      overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}>
      {/* ── Header row ── */}
      <div style={{ padding: '14px 16px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          {/* Risk badge */}
          <span style={{
            display: 'flex', alignItems: 'center', gap: 5,
            background: bg, color, borderRadius: 5,
            padding: '3px 9px', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
          }}>
            <Icon size={12} />
            {label}
          </span>

          {/* Subsystem name */}
          <span style={{ flex: 1, color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>
            {subsystem.subsystem}
          </span>

          {/* Risk % */}
          <span style={{ color, fontWeight: 700, fontSize: 18, minWidth: 48, textAlign: 'right' }}>
            {(subsystem.risk_prob * 100).toFixed(0)}%
          </span>
        </div>

        {/* ── Natural language explanation ── always visible */}
        <div style={{
          background: bg,
          border: `1px solid ${color}33`,
          borderRadius: 7,
          padding: '9px 13px',
          marginBottom: 12,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 8,
        }}>
          <Icon size={14} color={color} style={{ marginTop: 2, flexShrink: 0 }} />
          <span style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.55 }}>
            {explanation}
          </span>
        </div>
      </div>

      {/* ── Defect records (always shown when data exists) ── */}
      <div style={{ padding: '0 16px' }}>
        <DefectRecords subsystem={subsystem} year={year} month={month} />
      </div>

      {/* ── Toggle button ── */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', background: 'none', border: 'none',
          borderTop: '1px solid #1e2d45',
          cursor: 'pointer', padding: '8px 16px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginTop: 10,
        }}
      >
        <span style={{
          display: 'flex', alignItems: 'center', gap: 6,
          color: '#64748b', fontSize: 11, fontWeight: 500,
        }}>
          <BarChart2 size={13} />
          {open ? 'Hide feature breakdown' : 'Show feature breakdown (SHAP)'}
        </span>
        {open
          ? <ChevronUp size={15} color="#64748b" />
          : <ChevronDown size={15} color="#64748b" />}
      </button>

      {/* ── Expanded: full SHAP chart ── */}
      {open && (
        <div style={{ padding: '12px 16px 16px' }}>
          <div style={{ color: '#64748b', fontSize: 11, marginBottom: 10 }}>
            Baseline risk: <strong style={{ color: '#94a3b8' }}>{(base * 100).toFixed(1)}%</strong>
            &ensp;→&ensp;Model output: <strong style={{ color }}>
              {(subsystem.risk_prob * 100).toFixed(1)}%
            </strong>
            &ensp;|&ensp;
            <span style={{ color: '#ef4444' }}>■</span> increases risk&ensp;
            <span style={{ color: '#22c55e' }}>■</span> reduces risk
          </div>
          <ShapChart contributors={subsystem.contributors} baseValue={base} />
        </div>
      )}
    </div>
  );
};

export default SubsystemCard;
