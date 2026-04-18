"""Shared constants used across the CMPT backend."""

# Scrape confidence label → numeric score mapping.
# Used by pricing_engine.aggregate_competitors and orchestrator result serialization.
CONFIDENCE_MAP: dict[str, float] = {
    "high": 0.9,
    "medium": 0.6,
    "low": 0.3,
}

# ISO 4217 currency code → display symbol, used for API response formatting.
CURRENCY_DISPLAY: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "JPY": "JP¥",
    "CNY": "CN¥",
    "CAD": "C$",
    "AUD": "A$",
    "CHF": "CHF",
}

# Symbol/abbreviation → ISO 4217 code, used by the normalizer for currency detection.
CURRENCY_SYMBOLS: dict[str, str] = {
    "$": "USD",
    "₹": "INR",
    "Rs": "INR",
    "£": "GBP",
    "€": "EUR",
    "¥": "JPY",
    "RMB": "CNY",
    "元": "CNY",
    "CN¥": "CNY",
    "JP¥": "JPY",
    "A$": "AUD",
    "AUD$": "AUD",
    "C$": "CAD",
    "CAD$": "CAD",
    "CHF": "CHF",
}
