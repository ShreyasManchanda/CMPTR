import { motion } from 'framer-motion';
import './ConfidenceRing.css';

export default function ConfidenceRing({ score = 0, size = 120 }) {
  const clampedScore = Math.max(0, Math.min(score, 1));
  const percentage = Math.round(clampedScore * 100);
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - clampedScore * circumference;

  return (
    <div className="confidence-ring" style={{ width: size, height: size + 28 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="6"
        />

        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="var(--accent)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />

        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="central"
          className="confidence-ring__svg-text"
        >
          {percentage}%
        </text>
      </svg>

      <div className="confidence-ring__label">CONFIDENCE</div>
    </div>
  );
}