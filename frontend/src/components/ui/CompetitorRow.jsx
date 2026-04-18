import './CompetitorRow.css';

function timeAgo(isoString) {
  if (!isoString) return '—';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function useCompetitorData(confidence, stockStatus) {
  const confPct = Math.round((confidence || 0) * 100);
  const confClass = confPct >= 80 ? 'high' : confPct >= 50 ? 'medium' : 'low';
  const inStock = stockStatus !== 'out_of_stock';
  return { confPct, confClass, inStock };
}

export default function CompetitorRow({ store, productName, price, stockStatus, confidence, scrapedAt, currency = '₹' }) {
  const { confPct, confClass, inStock } = useCompetitorData(confidence, stockStatus);

  return (
    <div className="comp-row">
      <div className="comp-row__store">{store}</div>
      <div className="comp-row__product">{productName}</div>
      <div className="comp-row__price">{currency} {Number(price).toLocaleString()}</div>
      <div className="comp-row__stock">
        <span className={`comp-row__stock-badge ${inStock ? 'comp-row__stock-badge--in' : 'comp-row__stock-badge--out'}`}>
          {inStock ? 'In stock' : 'Out of stock'}
        </span>
      </div>
      <div className="comp-row__confidence">
        <span className={`comp-row__conf-pill comp-row__conf-pill--${confClass}`}>{confPct}%</span>
      </div>
      <div className="comp-row__scraped">{timeAgo(scrapedAt)}</div>
    </div>
  );
}

export function CompetitorCard({ store, productName, price, stockStatus, confidence, scrapedAt, currency = '₹' }) {
  const { confPct, confClass, inStock } = useCompetitorData(confidence, stockStatus);

  return (
    <div className="comp-card">
      <div className="comp-card__header">
        <span className="comp-card__store">{store}</span>
        <span className={`comp-row__conf-pill comp-row__conf-pill--${confClass}`}>{confPct}%</span>
      </div>
      <div className="comp-card__product">{productName}</div>
      <div className="comp-card__footer">
        <span className="comp-card__price">{currency} {Number(price).toLocaleString()}</span>
        <span className={`comp-row__stock-badge ${inStock ? 'comp-row__stock-badge--in' : 'comp-row__stock-badge--out'}`}>
          {inStock ? 'In stock' : 'Out'}
        </span>
        <span className="comp-card__time">{timeAgo(scrapedAt)}</span>
      </div>
    </div>
  );
}
