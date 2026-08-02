import { useState, useEffect } from 'react';
import './SkeletonLoader.css';

const STAGES = [
  'Crawl: reading competitor stores…',
  'Normalize: aligning prices and currency…',
  'Decide: scoring market position…',
  'Explain: writing the recommendation…',
];

export default function SkeletonLoader({ progressLabel = null }) {
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
        <p className="skeleton__label" key={progressLabel || idx}>
          {progressLabel || STAGES[idx]}
        </p>
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
