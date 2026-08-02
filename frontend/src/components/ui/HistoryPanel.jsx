import './HistoryPanel.css';

function formatWhen(iso) {
  if (!iso) return '';
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function formatAction(action) {
  if (!action) return '—';
  return String(action).replace(/_/g, ' ');
}

export default function HistoryPanel({
  decisions = [],
  loading,
  error,
  onSelect,
  activeDecisionId,
}) {
  return (
    <div className="history-panel">
      <div className="history-panel__title">Run history</div>

      {loading && <p className="history-panel__muted">Loading history…</p>}
      {error && <p className="history-panel__error">{error}</p>}

      {!loading && !error && decisions.length === 0 && (
        <p className="history-panel__muted">No saved runs yet. Analyze a product to start history.</p>
      )}

      <ul className="history-panel__list">
        {decisions.map((d) => {
          const active = activeDecisionId != null && Number(activeDecisionId) === Number(d.id);
          return (
            <li key={d.id}>
              <button
                type="button"
                className={`history-panel__item${active ? ' history-panel__item--active' : ''}`}
                onClick={() => onSelect?.(d.id)}
              >
                <span className="history-panel__name">
                  {d.product_name || d.product_id || `Run #${d.id}`}
                </span>
                <span className="history-panel__meta">
                  <span className="history-panel__action">{formatAction(d.action)}</span>
                  <span>{formatWhen(d.created_at)}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
