import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  // Job creation / polling calls are short; long work happens server-side.
  timeout: 30_000,
});

const apiKey = import.meta.env.VITE_API_KEY;
if (apiKey) {
  api.defaults.headers.common['X-API-Key'] = apiKey;
}

function normalizeDetail(detail) {
  if (!detail) return null;
  if (typeof detail === 'string') return detail;
  if (typeof detail === 'object') {
    if (typeof detail.message === 'string') return detail.message;
    if (typeof detail.detail === 'string') return detail.detail;
    try {
      return JSON.stringify(detail);
    } catch {
      return 'Request failed.';
    }
  }
  return String(detail);
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('The request timed out. Please retry.'));
    }
    if (!error.response) {
      return Promise.reject(
        new Error('Could not reach the analysis service. Confirm the backend is running, then retry.'),
      );
    }
    const message =
      normalizeDetail(error.response?.data?.detail) ||
      normalizeDetail(error.response?.data?.message) ||
      error.message ||
      'Analysis failed. Check your URLs and try again.';
    return Promise.reject(new Error(message));
  },
);

export default api;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Start an async analysis job and poll until completed/failed.
 * Avoids client timeouts on long Firecrawl + LLM pipelines.
 */
export async function postAnalyze(productUrl, competitorUrls, { onProgress } = {}) {
  try {
    return await postAnalyzeJob(productUrl, competitorUrls, { onProgress });
  } catch (jobError) {
    const msg = jobError?.message || '';
    const retryWithSync =
      msg.includes('Job not found') ||
      msg.includes('did not return an id') ||
      msg.includes('returned no result');
    if (!retryWithSync) throw jobError;
  }

  const { data } = await api.post(
    '/analyze',
    {
      my_product_url: productUrl,
      competitor_store_urls: competitorUrls,
    },
    { timeout: 10 * 60 * 1000 },
  );
  if (!data?.decision) {
    throw new Error('Analysis finished but returned an incomplete result.');
  }
  return data;
}

async function postAnalyzeJob(productUrl, competitorUrls, { onProgress } = {}) {
  const { data: started } = await api.post('/analyze/jobs', {
    my_product_url: productUrl,
    competitor_store_urls: competitorUrls,
  });

  const jobId = started.job_id;
  if (!jobId) {
    throw new Error('Analysis job did not return an id.');
  }

  const pollMs = 2000;
  const maxWaitMs = 10 * 60 * 1000;
  const startedAt = Date.now();

  while (Date.now() - startedAt < maxWaitMs) {
    const { data: job } = await api.get(`/analyze/jobs/${jobId}`);
    if (typeof onProgress === 'function') {
      onProgress(job);
    }
    if (job.status === 'completed') {
      if (!job.result?.decision) {
        throw new Error('Analysis finished but returned no result.');
      }
      return job.result;
    }
    if (job.status === 'failed') {
      throw new Error(job.error || 'Analysis failed.');
    }
    await sleep(pollMs);
  }

  throw new Error('Analysis is taking too long. Check run history shortly, or retry with fewer stores.');
}

export async function postDiscoverCompetitors(productUrl) {
  const { data } = await api.post(
    '/discover-competitors',
    { my_product_url: productUrl },
    { timeout: 3 * 60 * 1000 },
  );
  return data;
}

export async function getDecisions({ limit = 10, productId } = {}) {
  const { data } = await api.get('/decisions', {
    params: {
      limit,
      ...(productId ? { product_id: productId } : {}),
    },
  });
  return data;
}

export async function getDecision(decisionId) {
  const { data } = await api.get(`/decisions/${decisionId}`);
  return data;
}

export async function getHealth() {
  const { data } = await api.get('/health');
  return data;
}
