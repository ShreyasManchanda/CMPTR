import axios from 'axios';

/**
 * Centralized Axios instance.
 * All API requests should use this instance so that the base URL,
 * headers, and interceptors are configured in one place.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120_000, // 2 minutes — the pipeline can be slow
});

// ── Request interceptor (future auth token injection goes here) ──
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error),
);

// ── Response interceptor — unwrap and normalize errors ──
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Build a user-friendly error message
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred.';
    return Promise.reject(new Error(message));
  },
);

export default api;

// ── Typed API functions ──

/**
 * Trigger a full pricing analysis pipeline.
 */
export async function postAnalyze(productUrl, competitorUrls) {
  const { data } = await api.post('/analyze', {
    my_product_url: productUrl,
    competitor_store_urls: competitorUrls,
  });
  return data;
}

/**
 * Discover competitor stores based on the user's product URL.
 */
export async function postDiscoverCompetitors(productUrl) {
  const { data } = await api.post('/discover-competitors', {
    my_product_url: productUrl,
  });
  return data;
}

/**
 * Health check — useful for verifying connectivity.
 */
export async function getHealth() {
  const { data } = await api.get('/health');
  return data;
}
