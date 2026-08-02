import './ConfidenceBar.css';

export default function ConfidenceBar({ score, showLabel = true }) {
  const percentage = Math.round(score * 100);
  const isHigh = percentage >= 70;

  return (
    <div className="confidence-bar">
      <div className="confidence-bar__track" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100} aria-label="Confidence">
        <div
          className={`confidence-bar__fill ${isHigh ? 'confidence-bar__fill--high' : 'confidence-bar__fill--medium'}`}
          style={{ transform: `scaleX(${Math.max(0, Math.min(percentage, 100)) / 100})` }}
        />
      </div>
      {showLabel && (
        <span className={`confidence-bar__label ${isHigh ? 'confidence-bar__label--high' : 'confidence-bar__label--medium'}`}>
          {percentage}%
        </span>
      )}
    </div>
  );
}
