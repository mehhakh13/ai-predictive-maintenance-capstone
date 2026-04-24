import React, { useMemo } from 'react';
import { TrendingUp } from 'lucide-react';
import { formatCurrency, formatPercent } from '../../utils/format';

/**
 * TopContributors Component
 * Displays the top 5 systems by total cost with mini bars showing contribution percentage
 *
 * @param {Array} data - Filtered work order data
 */
const TopContributors = ({ data }) => {
  // Calculate top contributors
  const topSystems = useMemo(() => {
    if (!data || data.length === 0) return [];

    const systemCosts = {};
    let totalCost = 0;

    data.forEach(item => {
      const system = item.SystemDescription;
      if (!systemCosts[system]) {
        systemCosts[system] = 0;
      }
      systemCosts[system] += item.TotalCost;
      totalCost += item.TotalCost;
    });

    // Convert to array and sort
    const sorted = Object.entries(systemCosts)
      .map(([system, cost]) => ({
        system,
        cost,
        percentage: (cost / totalCost) * 100
      }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 5);

    return sorted;
  }, [data]);

  // Color scale for bars
  const colors = ['#ef4444', '#f59e0b', '#f59e0b', '#10b981', '#10b981'];

  if (topSystems.length === 0) {
    return (
      <div className="top-contributors">
        <div className="section-header">
          <h3 className="section-title">
            <TrendingUp size={18} style={{ marginRight: '0.5rem' }} />
            Top Cost Contributors
          </h3>
          <p className="section-subtitle">Highest cost systems</p>
        </div>
        <div className="empty-message">No data available</div>
      </div>
    );
  }

  return (
    <div className="top-contributors">
      <div className="section-header">
        <h3 className="section-title">
          <TrendingUp size={18} style={{ marginRight: '0.5rem' }} />
          Top Cost Contributors
        </h3>
        <p className="section-subtitle">Top 5 systems by total cost</p>
      </div>

      <div className="contributors-list">
        {topSystems.map((item, index) => (
          <div key={item.system} className="contributor-item">
            <div className="contributor-rank">{index + 1}</div>
            <div className="contributor-info">
              <div className="contributor-name">{item.system}</div>
              <div className="contributor-cost">{formatCurrency(item.cost)}</div>
              <div className="contributor-bar-container">
                <div
                  className="contributor-bar"
                  style={{
                    width: `${item.percentage}%`,
                    backgroundColor: colors[index]
                  }}
                />
              </div>
              <div className="contributor-percentage">
                {formatPercent(item.percentage, 1, false)} of total
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopContributors;
