import ConfidenceBar from './ConfidenceBar';
import './RecommendationCard.css';
import { motion, useReducedMotion } from 'framer-motion';

const ACTION_CONFIG = {
  REDUCE: { color: 'var(--accent)', label: 'REDUCE PRICE' },
  HOLD: { color: 'var(--text-secondary)', label: 'HOLD STEADY' },
  MANUAL_REVIEW: { color: 'var(--warning)', label: 'NEEDS REVIEW' },
};

export default function RecommendationCard({ action, suggestedPrice, currentPrice, confidence, policyReason, currency = '₹' }) {
  if (!action) return null;

  const key = action.toUpperCase().replace(' ', '_');
  const config = ACTION_CONFIG[key] || ACTION_CONFIG.HOLD;
  const shouldReduce = useReducedMotion();
  const hoverProps = shouldReduce ? {} : { whileHover: { y: -4 }, whileTap: { scale: 0.985 }, transition: { type: 'spring', stiffness: 300, damping: 26 } };

  return (
    <motion.div className="rec-hero" style={{ '--action-color': config.color }} {...hoverProps} variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}>
       <div className="rec-hero__inner">
         
         <div className="rec-hero__top-row">
            <div className="rec-hero__action-text" style={{ color: config.color }}>
              {config.label.split(' ').map((word, i) => (
                <div key={i}>{word}</div>
              ))}
            </div>

            <div className="rec-hero__price-block">
               {suggestedPrice != null ? (
                 <div className="rec-hero__suggested" style={{ color: config.color }}>
                   <span className="rec-hero__currency">{currency}</span>
                   <span className="rec-hero__value">{Number(suggestedPrice).toLocaleString()}</span>
                 </div>
               ) : (
                 <div className="rec-hero__suggested" style={{ color: config.color }}>
                   <span className="rec-hero__value">Analyze</span>
                 </div>
               )}
               
               {currentPrice != null && (
                  <div className="rec-hero__current">
                     <span className="rec-hero__current-label">Current Strategy:</span>
                     <span className="rec-hero__current-val">{currency}{Number(currentPrice).toLocaleString()}</span>
                  </div>
               )}
            </div>
         </div>

         <div className="rec-hero__bottom-row">
            {policyReason ? (
              <div className="rec-hero__reason">{policyReason}</div>
            ) : <div />}
            
            <div className="rec-hero__confidence-wrap">
              <div className="rec-hero__conf-header">
                <span className="rec-hero__conf-label">Decision Confidence</span>
                <span className="rec-hero__conf-val" style={{ color: config.color }}>
                  {Math.round((confidence || 0) * 100)}%
                </span>
              </div>
              <ConfidenceBar score={confidence || 0} showLabel={false} />
            </div>
         </div>

       </div>
    </motion.div>
  );
}
