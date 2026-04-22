import React from 'react';
import { X } from 'lucide-react';

const CellDetailModal = ({ cellData, onClose }) => {
  if (!cellData) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h2 className="modal-title">
            {cellData.system} - {cellData.monthName}
          </h2>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          {/* ML Predictions Section */}
          <div className="detail-section">
            <h3 className="section-heading">ML Prediction</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Predicted Asset Risk:</span>
                <span className="detail-value highlight">
                  {(cellData.ml_risk * 100).toFixed(1)}%
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Coverage:</span>
                <span className="detail-value">{cellData.coverage} entities</span>
              </div>
            </div>
            <div className="risk-bar-container">
              <div
                className="risk-bar"
                style={{
                  width: `${cellData.ml_risk * 100}%`,
                  backgroundColor:
                    cellData.ml_risk >= 0.7
                      ? '#ef4444'
                      : cellData.ml_risk >= 0.5
                      ? '#f97316'
                      : cellData.ml_risk >= 0.3
                      ? '#fbbf24'
                      : '#22c55e'
                }}
              >
                <span className="risk-bar-label">{(cellData.ml_risk * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div className="risk-interpretation">
              <strong>Interpretation:</strong>
              {cellData.ml_risk >= 0.7
                ? ' High risk - Immediate preventive maintenance recommended'
                : cellData.ml_risk >= 0.5
                ? ' Medium-high risk - Schedule maintenance soon'
                : cellData.ml_risk >= 0.3
                ? ' Medium risk - Monitor closely'
                : ' Low risk - Continue routine maintenance'}
            </div>
          </div>

          {/* Historical Data Section */}
          {cellData.historical && (
            <div className="detail-section">
              <h3 className="section-heading">Historical Data</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Asset-Driven Rate:</span>
                  <span className="detail-value">
                    {(cellData.historical.hist_asset_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Shock-Driven Rate:</span>
                  <span className="detail-value">
                    {(cellData.historical.hist_shock_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Total UPM Rate:</span>
                  <span className="detail-value">
                    {(cellData.historical.hist_total_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Historical Coverage:</span>
                  <span className="detail-value">{cellData.historical.coverage} entities</span>
                </div>
              </div>
            </div>
          )}

          {/* Info Section */}
          <div className="detail-section info-section">
            <h3 className="section-heading">About This Data</h3>
            <ul className="info-list">
              <li>
                <strong>ML Risk:</strong> Represents the predicted probability of an
                asset-driven UPM event occurring in this month for this system.
              </li>
              <li>
                <strong>Asset-Driven UPM:</strong> Failures due to internal degradation
                (wear, corrosion, aging) that can be predicted and prevented.
              </li>
              <li>
                <strong>Shock-Driven UPM:</strong> Failures due to external events
                (damage, accidents, weather) that are harder to predict.
              </li>
              <li>
                <strong>Coverage:</strong> Number of building-system combinations used
                to calculate this prediction. Higher coverage = more reliable estimate.
              </li>
            </ul>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default CellDetailModal;
