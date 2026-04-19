import './RecommendationCard.css';
import { motion } from 'framer-motion';

const ACTION_CONFIG = {
  REDUCE: { color: 'var(--accent)', label: 'REDUCE' },
  INCREASE: { color: 'var(--accent)', label: 'INCREASE' },
  MAINTAIN: { color: 'var(--accent)', label: 'MAINTAIN' },
  NO_CHANGE: { color: 'var(--accent)', label: 'MAINTAIN' },
  HOLD: { color: 'var(--accent)', label: 'MAINTAIN' },
  MANUAL_REVIEW: { color: 'var(--warning)', label: 'MANUAL REVIEW' },
};

export default function RecommendationCard({ action, suggestedPrice, currentPrice, confidence, policyReason, currency = '₹' }) {
  if (!action) return null;

  const key = action.toUpperCase().replace(' ', '_');
  const config = ACTION_CONFIG[key] || { color: 'var(--accent)', label: action.toUpperCase() };
  
  const isDynamicAction = ['REDUCE', 'INCREASE'].includes(key);

  return (
    <motion.div 
      className={`recommendation-card ${isDynamicAction ? 'recommendation-card--pulse' : ''}`}
      variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
    >
      <div className="recommendation-card__header">
        <div className="recommendation-card__badge">
          {config.label}
        </div>
        <div className="recommendation-card__policy-label">
          allowed_by_policy
        </div>
      </div>

      <div className="recommendation-card__content">
        <div className="recommendation-card__price-wrapper">
          <div className="recommendation-card__price">
            {currency}{(suggestedPrice ?? currentPrice ?? 0).toLocaleString()}
          </div>
          <div className="recommendation-card__meta">
            Currently {currency}{Number(currentPrice).toLocaleString()}
            {suggestedPrice != null && currentPrice != null && Number(suggestedPrice) !== Number(currentPrice) && (
              <> · {Number(suggestedPrice) < Number(currentPrice) ? 'Save' : 'Increase'} {Math.abs(Math.round((1 - Number(suggestedPrice) / Number(currentPrice)) * 100))}%</>
            )}
          </div>
          <div className="recommendation-card__strategy">
            CURRENT STRATEGY: <span className="strikethrough">{currency}{Number(currentPrice).toLocaleString()}</span>
          </div>
        </div>
        
        {policyReason && (
          <div className="recommendation-card__reason">
             {policyReason}
          </div>
        )}
      </div>
    </motion.div>
  );
}
