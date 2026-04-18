import './StatCard.css';
import { motion, useReducedMotion } from 'framer-motion';

export default function StatCard({ label, value, mono = true, highlight = false }) {
  const shouldReduce = useReducedMotion();
  const hoverProps = shouldReduce ? {} : { whileHover: { y: -4 }, whileTap: { scale: 0.995 }, transition: { type: 'spring', stiffness: 280, damping: 22 } };

  return (
    <motion.div className={`stat-card ${highlight ? 'stat-card--highlight' : ''}`} {...hoverProps} variants={{ hidden: { opacity: 0, y: 8 }, visible: { opacity: 1, y: 0 } }}>
      <div className="stat-card__label">{label}</div>
      <div className={`stat-card__value ${mono ? 'stat-card__value--mono' : ''}`}>
        {value}
      </div>
    </motion.div>
  );
}
