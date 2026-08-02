import './RecommendationCard.css';
import { motion, useReducedMotion } from 'framer-motion';

const ACTION_CONFIG = {
  REDUCE: { label: 'REDUCE' },
  INCREASE: { label: 'INCREASE' },
  MAINTAIN: { label: 'MAINTAIN' },
  NO_CHANGE: { label: 'MAINTAIN' },
  HOLD: { label: 'MAINTAIN' },
  MANUAL_REVIEW: { label: 'MANUAL REVIEW' },
};

const POLICY_LABELS = {
  requires_human_approval: 'Requires human approval',
  allowed_by_policy: 'Allowed by policy',
  confidence_below_policy_threshold: 'Confidence below threshold',
  high_volatility: 'High market volatility',
  insufficient_samples: 'Insufficient samples',
  low_average_confidence: 'Low average confidence',
  no_competitor_data: 'No competitor data',
  invalid_my_price: 'Invalid merchant price',
  invalid_median: 'Invalid market median',
};

function formatPolicyLabel(policyReason) {
  if (!policyReason) return 'Policy pending';
  if (POLICY_LABELS[policyReason]) return POLICY_LABELS[policyReason];
  if (policyReason.startsWith('median_above_by_')) return 'Above market median';
  if (policyReason.startsWith('median_below_by_')) return 'Below market median';
  if (policyReason === 'competitive') return 'Competitive — hold';
  return policyReason.replace(/_/g, ' ');
}

export default function RecommendationCard({
  action,
  suggestedPrice,
  currentPrice,
  confidence,
  policyReason,
  currency = '₹',
}) {
  const prefersReduced = useReducedMotion();
  if (!action) return null;

  const key = action.toUpperCase().replace(' ', '_');
  const config = ACTION_CONFIG[key] || { label: action.toUpperCase() };
  const isDynamicAction = ['REDUCE', 'INCREASE'].includes(key);
  const policyLabel = formatPolicyLabel(policyReason);

  return (
    <motion.div
      className={`recommendation-card ${isDynamicAction && !prefersReduced ? 'recommendation-card--enter' : ''}`}
      variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
    >
      <div className="recommendation-card__header">
        <div className="recommendation-card__badge">{config.label}</div>
        <div className="recommendation-card__policy-label">{policyLabel}</div>
      </div>

      <div className="recommendation-card__content">
        <div className="recommendation-card__price-wrapper">
          <div className="recommendation-card__price">
            {currency}{(suggestedPrice ?? currentPrice ?? 0).toLocaleString()}
          </div>
          <div className="recommendation-card__meta">
            Currently {currency}{Number(currentPrice).toLocaleString()}
            {suggestedPrice != null && currentPrice != null && Number(suggestedPrice) !== Number(currentPrice) && (
              <>
                {' '}
                · {Number(suggestedPrice) < Number(currentPrice) ? 'Save' : 'Increase'}{' '}
                {Math.abs(Math.round((1 - Number(suggestedPrice) / Number(currentPrice)) * 100))}%
              </>
            )}
          </div>
          {confidence != null && (
            <div className="recommendation-card__strategy">
              Confidence {Math.round(Number(confidence) * 100)}%
            </div>
          )}
        </div>

        {policyReason && (
          <div className="recommendation-card__reason">{policyReason.replace(/_/g, ' ')}</div>
        )}
      </div>
    </motion.div>
  );
}
