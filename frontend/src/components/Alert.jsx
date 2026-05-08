import React from 'react';
import { Info, AlertTriangle, XCircle, CheckCircle } from 'lucide-react';

/**
 * Reusable Alert Component
 *
 * Provides consistent alert styling across the Defect Analytics dashboard
 * with color-coded severity levels matching the faculty manager UX design.
 *
 * @param {Object} props
 * @param {'info' | 'warn' | 'danger' | 'success'} props.type - Alert severity type
 * @param {React.ReactNode} props.children - Alert content
 * @param {string} [props.className] - Additional CSS classes
 * @param {boolean} [props.icon=true] - Whether to show icon
 */
const Alert = ({ type = 'info', children, className = '', icon = true }) => {
  const getStyles = () => {
    const baseStyles = {
      padding: '1rem 1.25rem',
      borderRadius: '0.5rem',
      borderLeft: '4px solid',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '0.75rem',
      fontSize: '0.875rem',
      lineHeight: '1.5',
    };

    const typeStyles = {
      info: {
        background: 'var(--severity-monitor-bg)',
        borderColor: 'var(--severity-monitor)',
        color: 'var(--text-primary)',
      },
      warn: {
        background: 'var(--severity-urgent-bg)',
        borderColor: 'var(--severity-urgent)',
        color: 'var(--text-primary)',
      },
      danger: {
        background: 'var(--severity-critical-bg)',
        borderColor: 'var(--severity-critical)',
        color: 'var(--text-primary)',
      },
      success: {
        background: 'var(--severity-ok-bg)',
        borderColor: 'var(--severity-ok)',
        color: 'var(--text-primary)',
      },
    };

    return { ...baseStyles, ...typeStyles[type] };
  };

  const getIcon = () => {
    if (!icon) return null;

    const iconProps = {
      size: 20,
      style: { flexShrink: 0, marginTop: '2px' },
    };

    const iconColors = {
      info: 'var(--severity-monitor)',
      warn: 'var(--severity-urgent)',
      danger: 'var(--severity-critical)',
      success: 'var(--severity-ok)',
    };

    const icons = {
      info: <Info {...iconProps} color={iconColors.info} />,
      warn: <AlertTriangle {...iconProps} color={iconColors.warn} />,
      danger: <XCircle {...iconProps} color={iconColors.danger} />,
      success: <CheckCircle {...iconProps} color={iconColors.success} />,
    };

    return icons[type];
  };

  return (
    <div style={getStyles()} className={`alert alert-${type} ${className}`}>
      {getIcon()}
      <div style={{ flex: 1 }}>{children}</div>
    </div>
  );
};

export default Alert;
