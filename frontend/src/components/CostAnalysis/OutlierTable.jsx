import React, { useMemo, useState } from 'react';
import { AlertTriangle, X, Info } from 'lucide-react';
import { formatCurrency } from '../../utils/format';
import { calculatePercentile } from '../../utils/format';

/**
 * OutlierTable Component
 * Displays a table of cost outliers (work orders above P95 threshold)
 * Can be shown as a modal or inline table
 *
 * @param {Array} data - Filtered work order data
 * @param {number} threshold - P95 threshold value
 * @param {boolean} isModal - Whether to show as modal (default: false)
 * @param {Function} onClose - Close handler for modal
 */
const OutlierTable = ({ data, threshold, isModal = false, onClose }) => {
  const [showExplanation, setShowExplanation] = useState(false);

  // Get outliers
  const outliers = useMemo(() => {
    if (!data || data.length === 0) return [];

    return data
      .filter(item => item.TotalCost > threshold)
      .sort((a, b) => b.TotalCost - a.TotalCost)
      .slice(0, 10); // Top 10 outliers
  }, [data, threshold]);

  const content = (
    <>
      <div className="outlier-header">
        <div className="outlier-title">
          <AlertTriangle size={20} style={{ color: '#f59e0b' }} />
          <span>Cost Outliers (Top 10)</span>
          <button
            className="info-btn"
            onClick={() => setShowExplanation(!showExplanation)}
            title="What are cost outliers?"
          >
            <Info size={16} />
          </button>
        </div>
        {isModal && (
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        )}
      </div>

      {showExplanation && (
        <div className="outlier-explanation">
          <p>
            <strong>Cost Outliers</strong> are work orders with costs above the 95th percentile (P95).
            These represent unusually expensive maintenance activities that may indicate:
          </p>
          <ul>
            <li>Emergency repairs requiring urgent attention</li>
            <li>Major system failures or replacements</li>
            <li>Deferred maintenance catching up</li>
            <li>Opportunities for cost optimization</li>
          </ul>
          <p>
            Current P95 threshold: <strong>{formatCurrency(threshold)}</strong>
          </p>
        </div>
      )}

      {outliers.length === 0 ? (
        <div className="empty-message">No outliers found for the current threshold.</div>
      ) : (
        <div className="outlier-table-container">
          <table className="outlier-table">
            <thead>
              <tr>
                <th>Work Order</th>
                <th>Date</th>
                <th>System</th>
                <th>Type</th>
                <th>Labor</th>
                <th>Material</th>
                <th>Other</th>
                <th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              {outliers.map((item, index) => (
                <tr key={index}>
                  <td className="wo-id">{item.WOId}</td>
                  <td>{new Date(item.WOStartDate).toLocaleDateString()}</td>
                  <td className="system-name">{item.SystemDescription}</td>
                  <td>
                    <span className={`badge badge-${item.MaintenanceType.toLowerCase()}`}>
                      {item.MaintenanceType}
                    </span>
                  </td>
                  <td>{formatCurrency(item.LaborCost)}</td>
                  <td>{formatCurrency(item.MaterialCost)}</td>
                  <td>{formatCurrency(item.OtherCost)}</td>
                  <td className="total-cost">{formatCurrency(item.TotalCost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );

  if (isModal) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content outlier-modal" onClick={(e) => e.stopPropagation()}>
          {content}
        </div>
      </div>
    );
  }

  return <div className="outlier-table-section">{content}</div>;
};

export default OutlierTable;
