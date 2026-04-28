/**
 * API Configuration
 * Automatically detects the environment and sets the correct API URL
 */

/**
 * Detects if running in GitHub Codespaces
 * @returns {boolean}
 */
const isCodespaces = () => {
  return typeof window !== 'undefined' && window.location.hostname.includes('app.github.dev');
};

/**
 * Gets the API base URL based on the current environment
 * @returns {string}
 */
export const getApiBaseUrl = () => {
  // Check for explicit environment variable override
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Auto-detect Codespaces
  if (isCodespaces()) {
    const currentUrl = window.location.hostname;
    // Replace the frontend port with backend port (8000)
    const apiUrl = currentUrl.replace(/-\d+\.app\.github\.dev$/, '-8000.app.github.dev');
    return `https://${apiUrl}`;
  }

  // Default to localhost for local development
  return 'http://localhost:8000';
};

// Export the configured API URL
export const API_BASE_URL = getApiBaseUrl();

// Export helper for logging
export const logEnvironment = () => {
  console.log('🌍 Environment Detection:', {
    isCodespaces: isCodespaces(),
    apiBaseUrl: API_BASE_URL,
    hostname: typeof window !== 'undefined' ? window.location.hostname : 'server',
  });
};
