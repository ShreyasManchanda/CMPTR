import { useRef, useState, Suspense, lazy, useCallback } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import BackgroundPaths from '../components/ui/BackgroundPaths';
import StatCard from '../components/ui/StatCard';
import RecommendationCard from '../components/ui/RecommendationCard';
import CompetitorRow from '../components/ui/CompetitorRow';
const TrendChart = lazy(() => import('../components/ui/TrendChart'));
import ExplanationPanel from '../components/ui/ExplanationPanel';
import AmbiguityPanel from '../components/ui/AmbiguityPanel';
import HistoryPanel from '../components/ui/HistoryPanel';
import RunStatusBadge from '../components/ui/RunStatusBadge';
import EmptyState from '../components/ui/EmptyState';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import InputForm from '../components/ui/InputForm';
import ConfidenceRing from '../components/ui/ConfidenceRing';
import { useAnalysis } from '../hooks/useAnalysis';
import './Dashboard.css';

function getMedian(arr) {
  if (!arr || arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function formatFriendlyError(message) {
  if (!message) return 'Analysis failed. Check your URLs and try again.';
  const lower = message.toLowerCase();
  if (lower.includes('network') || lower.includes('timeout') || lower.includes('econnrefused')) {
    return 'Could not reach the analysis service. Confirm the backend is running, then retry.';
  }
  return message;
}

function formatRunTime(date) {
  if (!date) return null;
  try {
    return new Intl.DateTimeFormat(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  } catch {
    return date.toLocaleTimeString();
  }
}

export default function Dashboard() {
  const {
    result,
    loading,
    error,
    status,
    analyzeProduct,
    reset,
    discoverCompetitors,
    discoverLoading,
    discoverError,
    completedAt,
    jobProgress,
    history,
    historyLoading,
    historyError,
    loadHistoryDecision,
  } = useAnalysis();
  const formRef = useRef(null);
  const prefersReduced = useReducedMotion();
  const [productUrl, setProductUrl] = useState('');
  const [competitorUrls, setCompetitorUrls] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState({});
  const lastPayload = useRef(null);

  const handleRun = useCallback((url, competitors) => {
    lastPayload.current = { url, competitors };
    analyzeProduct(url, competitors);
  }, [analyzeProduct]);

  const handleRetry = useCallback(() => {
    const payload = lastPayload.current;
    if (payload?.url) {
      analyzeProduct(payload.url, payload.competitors || []);
      return;
    }
    reset();
    formRef.current?.querySelector('input')?.focus();
  }, [analyzeProduct, reset]);

  const handleDiscover = async (url) => {
    if (!url) return;
    try {
      const data = await discoverCompetitors(url);
      const found = data?.suggestions || [];
      setSuggestions(found);
      setSelectedSuggestions(Object.fromEntries(found.map((item) => [item.url, true])));
    } catch {
      setSuggestions([]);
      setSelectedSuggestions({});
    }
  };

  const handleToggleSuggestion = (url) => {
    setSelectedSuggestions((prev) => ({
      ...prev,
      [url]: !prev[url],
    }));
  };

  const handleAddSelected = () => {
    const selected = suggestions
      .filter((item) => selectedSuggestions[item.url])
      .map((item) => item.url);

    const normalized = Array.from(
      new Set([
        ...competitorUrls.split('\n').map((u) => u.trim()).filter(Boolean),
        ...selected,
      ]),
    );

    setCompetitorUrls(normalized.join('\n'));
  };

  const scrollToForm = () => {
    formRef.current?.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth' });
    formRef.current?.querySelector('input')?.focus();
  };

  const CURRENCY_SYMBOLS = { USD: '$', EUR: '€', GBP: '£', INR: '₹', JPY: 'JP¥', CNY: 'CN¥', CAD: 'C$', AUD: 'A$', CHF: 'CHF ' };
  const cur = CURRENCY_SYMBOLS[result?.currency] || result?.currency || '$';

  const competitors = result?.metrics?.competitor_stats || [];
  const stats = {
    min: competitors.length ? Math.min(...competitors.map((c) => c.price)) : null,
    max: competitors.length ? Math.max(...competitors.map((c) => c.price)) : null,
    median: competitors.length ? getMedian(competitors.map((c) => c.price)) : null,
    yourPrice: result?.my_price,
    count: competitors.length,
    avgConf: competitors.length
      ? competitors.reduce((a, c) => a + (c.confidence || 0), 0) / competitors.length
      : null,
  };

  const showEmpty = !result && !loading;
  const showResult = result && !loading;
  const friendlyError = formatFriendlyError(error);

  const motionProps = prefersReduced
    ? {}
    : {
        initial: 'hidden',
        animate: 'visible',
        variants: {
          hidden: {},
          visible: { transition: { staggerChildren: 0.05 } },
        },
      };

  const childVariants = prefersReduced
    ? undefined
    : { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } } };

  return (
    <div className="dashboard">
      <a href="#dashboard-main" className="skip-link">Skip to content</a>
      <Navbar />
      <BackgroundPaths blur />

      {showResult && (
        <header className="dashboard__top-bar">
          <div className="dashboard__top-bar-left">
            <span className="dashboard__product-id-label">{result.product_id}</span>
          </div>
          <div className="dashboard__top-bar-right">
            <RunStatusBadge status={status} />
          </div>
        </header>
      )}

      <main id="dashboard-main" className="dashboard__main">
        <div className="dashboard__layout">
          <aside className="dashboard__sidebar" ref={formRef}>
            <div className="dashboard__sidebar-inner">
              <h2 className="dashboard__sidebar-title">Analysis Setup</h2>

              <InputForm
                productUrl={productUrl}
                competitorUrls={competitorUrls}
                onUrlChange={setProductUrl}
                onCompetitorChange={setCompetitorUrls}
                onDiscover={handleDiscover}
                discovering={discoverLoading}
                suggestions={suggestions}
                selectedSuggestions={selectedSuggestions}
                onToggleSuggestion={handleToggleSuggestion}
                onAddSelected={handleAddSelected}
                onSubmit={handleRun}
                loading={loading}
              />

              {discoverError && (
                <div className="dashboard__discover-error" role="alert">
                  <p>{formatFriendlyError(discoverError)}</p>
                </div>
              )}

              {result && (
                <div className="dashboard__run-meta">
                  <div className="dashboard__run-time">
                    Last run{completedAt ? `: ${formatRunTime(completedAt)}` : ''}
                    {result.from_history ? ' · from history' : ''}
                  </div>
                  <div className="dashboard__run-stats">
                    {competitors.length} data point{competitors.length !== 1 ? 's' : ''} processed
                  </div>
                </div>
              )}

              {loading && jobProgress?.progress && (
                <div className="dashboard__job-progress" aria-live="polite">
                  Running analysis… ({String(jobProgress.progress).replace(/_/g, ' ')})
                </div>
              )}

              <HistoryPanel
                decisions={history}
                loading={historyLoading}
                error={historyError}
                activeDecisionId={result?.decision_id}
                onSelect={(id) => loadHistoryDecision(id)}
              />

              {error && (
                <div className="dashboard__error" role="alert">
                  <p className="dashboard__error-msg">{friendlyError}</p>
                  <div className="dashboard__error-actions">
                    <button type="button" className="dashboard__retry-btn" onClick={handleRetry}>
                      Retry analysis
                    </button>
                    <button type="button" className="dashboard__dismiss-btn" onClick={() => reset()}>
                      Dismiss
                    </button>
                  </div>
                </div>
              )}
            </div>
          </aside>

          <section className="dashboard__content" aria-live="polite">
            {showEmpty && (
              <div className="dashboard__content-empty">
                <EmptyState
                  onCTA={scrollToForm}
                  title={error ? 'Analysis did not finish' : undefined}
                  text={error ? friendlyError : undefined}
                  ctaLabel={error ? 'Fix inputs and retry' : undefined}
                />
              </div>
            )}

            {loading && (
              <div className="dashboard__content-loading">
                <SkeletonLoader
                  progressLabel={
                    jobProgress?.progress
                      ? `Running analysis… (${String(jobProgress.progress).replace(/_/g, ' ')})`
                      : null
                  }
                />
              </div>
            )}

            {showResult && (
              <motion.div className="dashboard__results-wrapper" {...motionProps}>
                <div className="dashboard__results-grid">
                  <motion.div className="dashboard__upper-split" variants={childVariants}>
                    <div className="dashboard__main-zone">
                      {result.decision?.action === 'manual_review' && (
                        <AmbiguityPanel advice={result.ai_advice} />
                      )}
                      <RecommendationCard
                        action={result.decision?.action}
                        suggestedPrice={result.decision?.suggested_price}
                        currentPrice={result.my_price}
                        confidence={result.decision?.confidence}
                        policyReason={result.decision?.policy_reason}
                        currency={cur}
                      />
                    </div>

                    <div className="dashboard__side-zone">
                      <div className="dashboard__stats-grid">
                        <StatCard loading={loading} label="Min Price" value={stats.min != null ? `${cur}${stats.min.toLocaleString()}` : '—'} />
                        <StatCard loading={loading} label="Max Price" value={stats.max != null ? `${cur}${stats.max.toLocaleString()}` : '—'} />
                        <StatCard loading={loading} label="Market Median" value={stats.median != null ? `${cur}${stats.median.toLocaleString()}` : '—'} />
                        <StatCard loading={loading} label="Your Price" value={stats.yourPrice != null ? `${cur}${stats.yourPrice.toLocaleString()}` : '—'} highlight />
                        <StatCard loading={loading} label="Sample Size" value={stats.count ?? '—'} />
                        <StatCard loading={loading} label="Avg Confidence" value={stats.avgConf != null ? `${Math.round(stats.avgConf * 100)}%` : '—'} />
                      </div>

                      <div className="dashboard__ring-card">
                        <ConfidenceRing score={result.decision?.confidence || 0} />
                      </div>
                    </div>
                  </motion.div>

                  <motion.div className="dashboard__explanation-full" variants={childVariants}>
                    <ExplanationPanel content={result.explanation} />
                  </motion.div>

                  <motion.div className="dashboard__lower-zone" variants={childVariants}>
                    <div className="dashboard__lower-split">
                      <div className="dashboard__table-container">
                        <div className="dashboard__section-label">Raw Competitor Data</div>
                        <div className="dashboard__table-card">
                          <div className="dashboard__table-header">
                            <div>Store</div>
                            <div>Product</div>
                            <div style={{ textAlign: 'right' }}>Price</div>
                            <div style={{ textAlign: 'center' }}>Stock</div>
                            <div style={{ textAlign: 'center' }}>Confidence</div>
                            <div style={{ textAlign: 'right' }}>Scraped</div>
                          </div>
                          <div className="dashboard__table-rows">
                            {competitors.map((c, i) => (
                              <CompetitorRow
                                key={`${c.store}-${i}`}
                                store={c.store}
                                productName={c.product_name}
                                price={c.price}
                                stockStatus={c.stock_status}
                                confidence={c.confidence}
                                scrapedAt={c.scraped_at}
                                currency={cur}
                                ourPrice={result.my_price}
                                url={c.url}
                              />
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="dashboard__chart-container">
                        <div className="dashboard__section-label">Price Distribution</div>
                        <div className="dashboard__chart-card">
                          <Suspense fallback={<div className="dashboard__chart-fallback">Loading chart…</div>}>
                            <TrendChart competitors={competitors} ourPrice={result.my_price} currency={cur} />
                          </Suspense>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </motion.div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
