import React, { useState } from 'react';
import { Wrench, ClipboardCheck, Clock, History } from 'lucide-react';

const MONTH_NAMES = [
  '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

const DescriptionChip = ({ text, type }) => {
  const isUpm = type === 'upm';
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 7,
      padding: '6px 10px',
      background: isUpm ? 'rgba(239,68,68,0.07)' : 'rgba(34,197,94,0.07)',
      border: `1px solid ${isUpm ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)'}`,
      borderRadius: 6, marginBottom: 5,
    }}>
      {isUpm
        ? <Wrench size={12} color="#ef4444" style={{ marginTop: 2, flexShrink: 0 }} />
        : <ClipboardCheck size={12} color="#22c55e" style={{ marginTop: 2, flexShrink: 0 }} />}
      <span style={{
        fontSize: 12, color: '#cbd5e1', lineHeight: 1.45,
        textTransform: 'uppercase', letterSpacing: '0.01em',
      }}>
        {text}
      </span>
    </div>
  );
};

const Section = ({ icon: Icon, title, color, children }) => (
  <div style={{ marginBottom: 12 }}>
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      marginBottom: 7, color,
    }}>
      <Icon size={13} />
      <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {title}
      </span>
    </div>
    {children}
  </div>
);

const DefectRecords = ({ subsystem, year, month }) => {
  const [showHist, setShowHist] = useState(false);

  const hasThisMonth = subsystem.this_month_upm?.length > 0 || subsystem.this_month_ppm?.length > 0;
  const hasHist = subsystem.hist_upm?.length > 0 || subsystem.hist_ppm?.length > 0;

  if (!hasThisMonth && !hasHist) return null;

  return (
    <div style={{
      marginTop: 14,
      borderTop: '1px solid #1e2d45',
      paddingTop: 14,
    }}>
      {/* ── This month ── */}
      {hasThisMonth && (
        <Section icon={Clock} title={`${MONTH_NAMES[month]} ${year} — work orders`} color="#94a3b8">
          {subsystem.this_month_upm?.length > 0 && (
            <div style={{ marginBottom: 6 }}>
              <div style={{ fontSize: 10, color: '#ef4444', fontWeight: 600, marginBottom: 4, letterSpacing: '0.05em' }}>
                UNPLANNED (UPM)
              </div>
              {subsystem.this_month_upm.map((d, i) => (
                <DescriptionChip key={i} text={d} type="upm" />
              ))}
            </div>
          )}
          {subsystem.this_month_ppm?.length > 0 && (
            <div>
              <div style={{ fontSize: 10, color: '#22c55e', fontWeight: 600, marginBottom: 4, letterSpacing: '0.05em' }}>
                PLANNED (PPM)
              </div>
              {subsystem.this_month_ppm.map((d, i) => (
                <DescriptionChip key={i} text={d} type="ppm" />
              ))}
            </div>
          )}
        </Section>
      )}

      {/* ── Historical pattern ── */}
      {hasHist && (
        <div>
          <button
            onClick={() => setShowHist(h => !h)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
              color: '#64748b', fontSize: 11, fontWeight: 700,
              textTransform: 'uppercase', letterSpacing: '0.06em',
              padding: '4px 0', marginBottom: showHist ? 8 : 0,
            }}
          >
            <History size={13} />
            Common historical defects
            <span style={{ marginLeft: 2, fontSize: 10 }}>{showHist ? '▲' : '▼'}</span>
          </button>

          {showHist && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {subsystem.hist_upm?.length > 0 && (
                <div>
                  <div style={{ fontSize: 10, color: '#ef4444', fontWeight: 600, marginBottom: 5, letterSpacing: '0.05em' }}>
                    UNPLANNED (UPM)
                  </div>
                  {subsystem.hist_upm.map((d, i) => (
                    <DescriptionChip key={i} text={d} type="upm" />
                  ))}
                </div>
              )}
              {subsystem.hist_ppm?.length > 0 && (
                <div>
                  <div style={{ fontSize: 10, color: '#22c55e', fontWeight: 600, marginBottom: 5, letterSpacing: '0.05em' }}>
                    PLANNED (PPM)
                  </div>
                  {subsystem.hist_ppm.map((d, i) => (
                    <DescriptionChip key={i} text={d} type="ppm" />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DefectRecords;
