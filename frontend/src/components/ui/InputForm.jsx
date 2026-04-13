import { useState } from 'react';
import './InputForm.css';

export default function InputForm({ onSubmit, loading }) {
  const [productUrl, setProductUrl] = useState('');
  const [competitorUrls, setCompetitorUrls] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const urls = competitorUrls.split('\n').map(u => u.trim()).filter(Boolean);
    onSubmit(productUrl, urls);
  };

  return (
    <form className="input-form" onSubmit={handleSubmit}>
      <div className="input-form__group">
        <label className="input-form__label" htmlFor="product-url">My product URL</label>
        <input
          id="product-url"
          type="url"
          required
          placeholder="https://yourstore.com/products/my-product"
          value={productUrl}
          onChange={(e) => setProductUrl(e.target.value)}
        />
      </div>

      <div className="input-form__group">
        <label className="input-form__label" htmlFor="competitor-urls">Competitor store URLs</label>
        <textarea
          id="competitor-urls"
          rows={4}
          placeholder={"https://competitor1.com\nhttps://competitor2.com"}
          value={competitorUrls}
          onChange={(e) => setCompetitorUrls(e.target.value)}
        />
        <span className="input-form__hint">Enter one URL per line</span>
      </div>

      <button type="submit" className="input-form__submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Run Analysis'}
      </button>
    </form>
  );
}
