import './StatCard.css';

export default function StatCard({ label, value, mono = true, highlight = false }) {
  return (
    <div className={`stat-card ${highlight ? 'stat-card--highlight' : ''}`}>
      <div className="stat-card__label">{label}</div>
      <div className={`stat-card__value ${mono ? 'stat-card__value--mono' : ''}`}>
        {value}
      </div>
    </div>
  );
}
