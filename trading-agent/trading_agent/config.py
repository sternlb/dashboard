"""Default watchlist, grouped by asset class.

Tickers use Yahoo Finance symbology:
- US stocks/ETFs:   AAPL, SPY
- Xetra (EUR):       suffix .DE   (e.g. SAP.DE)
- Indices:           prefix ^     (e.g. ^GDAXI = DAX)
- Forex:             pair=X       (e.g. EURUSD=X)
- Crypto:            COIN-CUR     (e.g. BTC-EUR)
"""

WATCHLIST: dict[str, list[str]] = {
    "EU Aktien & ETFs": ["SAP.DE", "SIE.DE", "ALV.DE", "EXS1.DE"],
    "US Aktien & ETFs": ["AAPL", "MSFT", "NVDA", "SPY"],
    "Indizes": ["^GDAXI", "^GSPC", "^IXIC"],
    "Forex": ["EURUSD=X", "EURGBP=X"],
    "Krypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"],
}


def all_tickers() -> list[str]:
    """Flat, de-duplicated list of every ticker across all groups."""
    seen: dict[str, None] = {}
    for group in WATCHLIST.values():
        for t in group:
            seen.setdefault(t, None)
    return list(seen)


# Friendly display names for tickers that aren't self-explanatory.
DISPLAY_NAMES: dict[str, str] = {
    "^GDAXI": "DAX",
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq Composite",
    "EXS1.DE": "iShares DAX ETF",
    "EURUSD=X": "EUR/USD",
    "EURGBP=X": "EUR/GBP",
}
