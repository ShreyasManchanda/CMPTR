import './EmptyState.css';

export default function EmptyState({ onCTA }) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="6" y="10" width="36" height="28" rx="4" stroke="var(--text-secondary)" strokeWidth="1.5" fill="none"/>
          <line x1="6" y1="18" x2="42" y2="18" stroke="var(--text-secondary)" strokeWidth="1.5"/>
          <circle cx="12" cy="14" r="1.5" fill="var(--accent)"/>
          <circle cx="17" cy="14" r="1.5" fill="var(--warning)"/>
          <circle cx="22" cy="14" r="1.5" fill="var(--text-secondary)"/>
          <rect x="12" y="24" width="24" height="2" rx="1" fill="var(--bg-surface-2)"/>
          <rect x="12" y="30" width="16" height="2" rx="1" fill="var(--bg-surface-2)"/>
        </svg>
      </div>
      <h3 className="empty-state__title">No analysis yet</h3>
      <p className="empty-state__text">
        Enter your product URL and competitor stores to get started.
      </p>
      {onCTA && (
        <button className="empty-state__cta" onClick={onCTA}>
          Run your first analysis
        </button>
      )}
    </div>
  );
}
