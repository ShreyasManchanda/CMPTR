import { useEffect, useMemo, useState } from 'react';
import { motion, animate } from 'framer-motion';
import './StatCard.css';

const CARD_VARIANTS = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: 'easeOut' },
  },
};

function parseAnimatedValue(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return { numeric: value, prefix: '', suffix: '', decimals: 0 };
  }

  if (typeof value !== 'string') return null;

  const match = value.match(/-?\d[\d,]*(?:\.\d+)?/);
  if (!match) return null;

  const rawNumber = match[0];
  const numeric = Number.parseFloat(rawNumber.replace(/,/g, ''));
  if (!Number.isFinite(numeric)) return null;

  const decimalPart = rawNumber.split('.')[1];
  const decimals = decimalPart ? decimalPart.length : 0;

  return {
    numeric,
    prefix: value.slice(0, match.index),
    suffix: value.slice((match.index || 0) + rawNumber.length),
    decimals,
  };
}

function AnimatedNumber({ value }) {
  const parsed = useMemo(() => parseAnimatedValue(value), [value]);
  const [displayValue, setDisplayValue] = useState(parsed?.numeric ?? value);

  useEffect(() => {
    if (!parsed) {
      setDisplayValue(value);
      return;
    }

    const controls = animate(0, parsed.numeric, {
      duration: 0.8,
      ease: 'easeOut',
      onUpdate(latest) {
        setDisplayValue(latest);
      },
    });

    return () => controls.stop();
  }, [parsed, value]);

  if (!parsed) return <span>{String(value)}</span>;

  const roundedValue = Number(displayValue);
  const formatted = roundedValue.toLocaleString(undefined, {
    minimumFractionDigits: parsed.decimals,
    maximumFractionDigits: parsed.decimals,
  });

  return (
    <span>
      {parsed.prefix}
      {formatted}
      {parsed.suffix}
    </span>
  );
}

export default function StatCard({ label, value, highlight = false, loading = false }) {
  return (
    <motion.div
      className={`stat-card ${highlight ? 'stat-card--highlight' : ''}`}
      variants={CARD_VARIANTS}
    >
      <div className="stat-card__label">{label}</div>
      <div className="stat-card__value">
        {loading || value === null ? <div className="stat-card__skeleton" /> : <AnimatedNumber value={value} />}
      </div>
    </motion.div>
  );
}