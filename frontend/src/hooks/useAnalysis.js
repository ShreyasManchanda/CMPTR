import { useCallback, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  getDecision,
  getDecisions,
  postAnalyze,
  postDiscoverCompetitors,
} from '../lib/api';

const MOCK_RESULT = {
  product_id: 'sneaker-x1-pro',
  my_price: 1499.0,
  currency: 'INR',
  status: 'success',
  decision: {
    action: 'reduce',
    suggested_price: 1249.0,
    confidence: 0.82,
    policy_reason: 'requires_human_approval',
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
    "**Market Position Summary**\n\nYour product is currently priced at ₹1,499, which places it **16.7% above** the median competitor price of ₹1,284.\n\n**Recommendation:** Reduce your price to **₹1,249** to position competitively while maintaining margin.",
};

const ACTION_LABELS = {
  reduce: 'Reduce',
  increase: 'Increase',
  no_change: 'Hold',
  hold: 'Hold',
  manual_review: 'Manual Review',
};

function labelForAction(action) {
  if (!action) return 'Complete';
  return ACTION_LABELS[action] || String(action).replace(/_/g, ' ');
}

/**
 * useAnalysis — React Query hook for pricing analysis + run history.
 * Falls back to mock data when VITE_USE_MOCK === 'true'.
 */
export function useAnalysis() {
  const useMock = import.meta.env.VITE_USE_MOCK === 'true';
  const [completedAt, setCompletedAt] = useState(null);
  const [jobProgress, setJobProgress] = useState(null);
  const queryClient = useQueryClient();

  const historyQuery = useQuery({
    queryKey: ['decisions', { limit: 12 }],
    queryFn: async () => {
      if (useMock) {
        return {
          status: 'success',
          count: 1,
          decisions: [
            {
              id: 1,
              product_id: 'sneaker-x1-pro',
              product_name: 'Sneaker X1 Pro',
              action: 'reduce',
              confidence: 0.82,
              created_at: new Date().toISOString(),
            },
          ],
        };
      }
      return getDecisions({ limit: 12 });
    },
    staleTime: 15_000,
    retry: 1,
  });

  const mutation = useMutation({
    mutationFn: async ({ myProductUrl, competitorUrls }) => {
      if (useMock) {
        setJobProgress({ status: 'running', progress: 'mock' });
        await new Promise((resolve) => setTimeout(resolve, 1800));
        return MOCK_RESULT;
      }
      return postAnalyze(myProductUrl, competitorUrls, {
        onProgress: (job) => setJobProgress(job),
      });
    },
    onSuccess: (data) => {
      setCompletedAt(new Date());
      setJobProgress(null);
      if (data?.decision?.action) {
        toast.success(`Analysis complete: ${labelForAction(data.decision.action)}`);
      } else {
        toast.error('Analysis finished without a recommendation. Please retry.');
      }
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
    },
    onError: (error) => {
      setJobProgress(null);
      toast.error(error.message || 'Analysis failed. Please try again.');
    },
  });

  const discoveryMutation = useMutation({
    mutationFn: async ({ myProductUrl }) => {
      if (useMock) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
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

  const loadHistoryMutation = useMutation({
    mutationFn: async (decisionId) => {
      if (useMock) {
        return { status: 'success', decision: MOCK_RESULT.decision, result: MOCK_RESULT };
      }
      const detail = await getDecision(decisionId);
      // Reshape history detail into the live analysis result shape the dashboard expects.
      return {
        status: 'success',
        product_id: detail.decision.product_id,
        product_name: detail.decision.product_name,
        product_url: detail.decision.product_url,
        my_price: detail.decision.my_price,
        currency: detail.decision.currency || detail.competitors?.[0]?.currency || 'USD',
        decision: {
          action: detail.decision.action,
          suggested_price: detail.decision.suggested_price,
          confidence: detail.decision.confidence,
          policy_reason: detail.decision.policy_reason,
        },
        ai_advice: detail.decision.ai_advice,
        explanation: detail.decision.explanation,
        decision_id: detail.decision.id,
        metrics: {
          competitor_stats: (detail.competitors || []).map((c) => ({
            store: c.competitor_url,
            product_name: c.competitor_url,
            price: c.price,
            original_price: c.price,
            original_currency: c.currency,
            stock_status: 'unknown',
            confidence: c.confidence,
            scraped_at: c.scraped_at,
          })),
        },
        from_history: true,
      };
    },
    onSuccess: () => {
      setCompletedAt(new Date());
      toast.success('Loaded run from history');
    },
    onError: (error) => {
      toast.error(error.message || 'Could not load that run.');
    },
  });

  const analyzeProduct = useCallback(
    (myProductUrl, competitorUrls) => {
      loadHistoryMutation.reset();
      mutation.mutate({ myProductUrl, competitorUrls });
    },
    [mutation, loadHistoryMutation],
  );

  const discoverCompetitors = useCallback(
    (myProductUrl) => discoveryMutation.mutateAsync({ myProductUrl }),
    [discoveryMutation],
  );

  const loadHistoryDecision = useCallback(
    (decisionId) => {
      mutation.reset();
      return loadHistoryMutation.mutateAsync(decisionId);
    },
    [loadHistoryMutation, mutation],
  );

  const reset = useCallback(() => {
    setCompletedAt(null);
    setJobProgress(null);
    mutation.reset();
    loadHistoryMutation.reset();
  }, [mutation, loadHistoryMutation]);

  let status = 'idle';
  if (mutation.isPending || loadHistoryMutation.isPending) status = 'running';
  else if (mutation.isSuccess || loadHistoryMutation.isSuccess) status = 'complete';
  else if (mutation.isError || loadHistoryMutation.isError) status = 'error';

  const result = loadHistoryMutation.data ?? mutation.data ?? null;
  const error =
    loadHistoryMutation.error?.message ?? mutation.error?.message ?? null;

  return {
    result,
    loading: mutation.isPending || loadHistoryMutation.isPending,
    error,
    status,
    completedAt,
    jobProgress,
    analyzeProduct,
    reset,
    discoverCompetitors,
    discoverLoading: discoveryMutation.isPending,
    discoverError: discoveryMutation.error?.message ?? null,
    discoveryResult: discoveryMutation.data ?? null,
    history: historyQuery.data?.decisions ?? [],
    historyLoading: historyQuery.isLoading,
    historyError: historyQuery.error?.message ?? null,
    refreshHistory: () => queryClient.invalidateQueries({ queryKey: ['decisions'] }),
    loadHistoryDecision,
  };
}
