import './AmbiguityPanel.css';

function normalizeAdvice(advice) {
  if (!advice) return null;
  if (typeof advice === 'string') {
    return { reasoning: advice, recommended_action: null, confidence_in_advice: null };
  }
  if (typeof advice === 'object') {
    return {
      recommended_action: advice.recommended_action || advice.action || null,
      reasoning: advice.reasoning || advice.message || null,
      confidence_in_advice:
        advice.confidence_in_advice != null
          ? Number(advice.confidence_in_advice)
          : advice.confidence != null
            ? Number(advice.confidence)
            : null,
    };
  }
  return { reasoning: String(advice), recommended_action: null, confidence_in_advice: null };
}

function formatAction(action) {
  if (!action) return null;
  return String(action).replace(/_/g, ' ');
}

export default function AmbiguityPanel({ advice }) {
  const normalized = normalizeAdvice(advice);
  if (!normalized || (!normalized.reasoning && !normalized.recommended_action)) return null;

  const confidencePct =
    normalized.confidence_in_advice != null && !Number.isNaN(normalized.confidence_in_advice)
      ? Math.round(normalized.confidence_in_advice * 100)
      : null;

  return (
    <div className="ambiguity-panel">
      <h3 className="ambiguity-panel__header">Human review needed</h3>
      {normalized.recommended_action && (
        <div className="ambiguity-panel__action">
          Suggested next step: <strong>{formatAction(normalized.recommended_action)}</strong>
          {confidencePct != null && (
            <span className="ambiguity-panel__confidence"> · {confidencePct}% confidence</span>
          )}
        </div>
      )}
      {normalized.reasoning && (
        <p className="ambiguity-panel__reasoning">{normalized.reasoning}</p>
      )}
    </div>
  );
}
