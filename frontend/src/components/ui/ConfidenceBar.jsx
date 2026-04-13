import './ConfidenceBar.css';

export default function ConfidenceBar({ score, showLabel = true }) {
  const percentage = Math.round(score * 100);
  const isHigh = percentage >= 70;

  return (
    <div className="confidence-bar">
      <div className="confidence-bar__track">
        <div
          className={`confidence-bar__fill ${isHigh ? 'confidence-bar__fill--high' : 'confidence-bar__fill--medium'}`}
          style={{ width: `${percentage}%` }}
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
