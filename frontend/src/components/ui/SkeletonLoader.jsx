import { useState, useEffect } from 'react';
import './SkeletonLoader.css';

const STAGES = [
  'Crawling competitor stores...',
  'Normalising pricing data...',
  'Analysing market position...',
  'Generating recommendation...',
];

export default function SkeletonLoader() {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIdx(prev => (prev + 1) % STAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="skeleton">
      <div className="skeleton__stage">
        <div className="skeleton__spinner" />
        <p className="skeleton__label" key={idx}>{STAGES[idx]}</p>
      </div>
      <div className="skeleton__grid">
        <div className="skeleton__block skeleton__block--tall" />
        <div className="skeleton__block" />
        <div className="skeleton__block" />
      </div>
      <div className="skeleton__block skeleton__block--wide" />
    </div>
  );
}
