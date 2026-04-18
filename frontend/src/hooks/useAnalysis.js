import { useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { postAnalyze, postDiscoverCompetitors } from '../lib/api';

const MOCK_RESULT = {
  product_id: 'sneaker-x1-pro',
  my_price: 1499.0,
  currency: 'INR',
  status: 'success',
  decision: {
    action: 'reduce',
    suggested_price: 1249.0,
    confidence: 0.82,
    policy_reason:
      'Your price is 16.7% above the market median. Reducing to ₹1,249 aligns you competitively without undercutting.',
  },
  metrics: {
    competitor_stats: [
      {
        store: 'competitor1.com',
        product_name: 'Sneaker X1 Pro — Black',
        price: 1199.0,
        stock_status: 'in_stock',
        confidence: 0.91,
        scraped_at: new Date(Date.now() - 120000).toISOString(),
      },
      {
        store: 'competitor2.com',
        product_name: 'Sneaker X1 Pro',
        price: 1299.0,
        stock_status: 'in_stock',
        confidence: 0.85,
        scraped_at: new Date(Date.now() - 240000).toISOString(),
      },
      {
        store: 'competitor3.com',
        product_name: 'X1 Pro Running Shoe',
        price: 1349.0,
        stock_status: 'out_of_stock',
        confidence: 0.72,
        scraped_at: new Date(Date.now() - 600000).toISOString(),
      },
    ],
  },
  ai_advice: null,
  explanation:
    "**Market Position Summary**\n\nYour product is currently priced at ₹1,499, which places it **16.7% above** the median competitor price of ₹1,284.\n\nAll three competitors are offering the same product at lower price points, with the lowest at ₹1,199. The data confidence across sources is strong (average 0.83), and price volatility is low — suggesting these are stable, established prices rather than temporary promotions.\n\n**Recommendation:** Reduce your price to **₹1,249** to position competitively while maintaining margin. This places you slightly below the median without matching the lowest available price.",
};

/**
 * useAnalysis — React Query–powered hook for pricing analysis.
 *
 * Uses `useMutation` because the /analyze endpoint is a POST action.
 * Falls back to mock data when VITE_USE_MOCK !== 'false'.
 */
export function useAnalysis() {
  const useMock = import.meta.env.VITE_USE_MOCK !== 'false';

  const mutation = useMutation({
    mutationFn: async ({ myProductUrl, competitorUrls }) => {
      if (useMock) {
        await new Promise((resolve) => setTimeout(resolve, 5000));
        return MOCK_RESULT;
      }
      return postAnalyze(myProductUrl, competitorUrls);
    },
    onSuccess: (data) => {
      const action = data?.decision?.action;
      const actionLabel =
        action === 'reduce'
          ? '↓ Reduce'
          : action === 'no_change'
            ? '✓ Hold'
            : '⚠ Manual Review';
      toast.success(`Analysis complete — ${actionLabel}`);
    },
    onError: (error) => {
      toast.error(error.message || 'Analysis failed. Please try again.');
    },
  });

  const discoveryMutation = useMutation({
    mutationFn: async ({ myProductUrl }) => {
      if (useMock) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        return {
          status: 'success',
          product_name: 'Mock Product',
          suggestions: [
            { store: 'competitor1.com', url: 'https://competitor1.com' },
            { store: 'competitor2.com', url: 'https://competitor2.com' },
          ],
        };
      }
      return postDiscoverCompetitors(myProductUrl);
    },
    onError: (error) => {
      toast.error(error.message || 'Could not discover competitors.');
    },
  });

  const analyzeProduct = useCallback(
    (myProductUrl, competitorUrls) => {
      mutation.mutate({ myProductUrl, competitorUrls });
    },
    [mutation],
  );

  const discoverCompetitors = useCallback(
    (myProductUrl) => {
      return discoveryMutation.mutateAsync({ myProductUrl });
    },
    [discoveryMutation],
  );

  const reset = useCallback(() => {
    mutation.reset();
  }, [mutation]);

  let status = 'idle';
  if (mutation.isPending) status = 'running';
  else if (mutation.isSuccess) status = 'complete';
  else if (mutation.isError) status = 'error';

  return {
    result: mutation.data ?? null,
    loading: mutation.isPending,
    error: mutation.error?.message ?? null,
    status,
    analyzeProduct,
    reset,
    discoverCompetitors,
    discoverLoading: discoveryMutation.isPending,
    discoverError: discoveryMutation.error?.message ?? null,
  };
}
