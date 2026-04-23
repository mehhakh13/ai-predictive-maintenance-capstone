/**
 * Utility functions for formatting currency, percentages, and numbers
 * Used across the Cost Analysis dashboard for consistent formatting
 */

/**
 * Format a number as USD currency with commas and decimal places
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 0)
 * @returns {string} Formatted currency string (e.g., "$1,234.56")
 */
export const formatCurrency = (value, decimals = 0) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '$0';
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * Format a number as a percentage
 * @param {number} value - The number to format (0-1 range or 0-100)
 * @param {number} decimals - Number of decimal places (default: 1)
 * @param {boolean} isDecimal - If true, value is 0-1 range; if false, value is 0-100
 * @returns {string} Formatted percentage string (e.g., "45.2%")
 */
export const formatPercent = (value, decimals = 1, isDecimal = true) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0%';
  }

  const percentValue = isDecimal ? value * 100 : value;
  return `${percentValue.toFixed(decimals)}%`;
};

/**
 * Format a large number with K, M, B suffixes
 * @param {number} value - The number to format
 * @returns {string} Formatted string (e.g., "1.2K", "3.5M")
 */
export const formatCompactNumber = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0';
  }

  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`;
  }
  if (value >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`;
  }
  if (value >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`;
  }
  return value.toFixed(0);
};

/**
 * Format a number with commas (no currency symbol)
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 0)
 * @returns {string} Formatted number string (e.g., "1,234.56")
 */
export const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0';
  }

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * Calculate the percentile value from an array of numbers
 * @param {number[]} arr - Array of numbers
 * @param {number} percentile - Percentile to calculate (0-100)
 * @returns {number} The percentile value
 */
export const calculatePercentile = (arr, percentile) => {
  if (!arr || arr.length === 0) return 0;

  const sorted = [...arr].sort((a, b) => a - b);
  const index = (percentile / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index - lower;

  if (lower === upper) return sorted[lower];
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
};
