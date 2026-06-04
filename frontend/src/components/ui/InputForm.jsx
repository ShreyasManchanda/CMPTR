import './InputForm.css';

export default function InputForm({
  productUrl,
  competitorUrls,
  onUrlChange,
  onCompetitorChange,
  onDiscover,
  discovering,
  suggestions,
  selectedSuggestions,
  onToggleSuggestion,
  onAddSelected,
  onSubmit,
  loading,
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const urls = competitorUrls.split('\n').map((u) => u.trim()).filter(Boolean);
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
          onChange={(e) => onUrlChange(e.target.value)}
        />
      </div>

      <div className="input-form__group">
        <label className="input-form__label" htmlFor="competitor-urls">Competitor store URLs</label>
        <textarea
          id="competitor-urls"
          rows={4}
          placeholder={"https://competitor1.com\nhttps://competitor2.com"}
          value={competitorUrls}
          onChange={(e) => onCompetitorChange(e.target.value)}
        />
        <span className="input-form__hint">Enter one URL per line</span>
      </div>

      <button
        type="button"
        className="input-form__secondary"
        onClick={() => onDiscover(productUrl)}
        disabled={discovering || !productUrl}
      >
        {discovering ? 'Finding competitors…' : 'Find competitors'}
      </button>

      {suggestions?.length > 0 && (
        <div className="input-form__suggestions">
          <div className="input-form__suggestions-title">Suggested competitors</div>
          {suggestions.map((suggestion) => (
            <label key={suggestion.url} className="input-form__suggestion-item">
              <input
                type="checkbox"
                checked={!!selectedSuggestions[suggestion.url]}
                onChange={() => onToggleSuggestion(suggestion.url)}
              />
              <span>{suggestion.store || suggestion.url}</span>
            </label>
          ))}
          <button
            type="button"
            className="input-form__tertiary"
            onClick={onAddSelected}
          >
            Add selected to competitor list
          </button>
        </div>
      )}

      <button type="submit" className="input-form__submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Run Analysis'}
      </button>
    </form>
  );
}
