"""Market-data access layer (Yahoo Finance via yfinance).

No Streamlit imports here on purpose: caching is applied by the caller
(the dashboard wraps these with st.cache_data). That keeps this module
usable from scripts, notebooks, backtests, and the future agent.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


# Map dashboard period -> a sensible candle interval.
PERIOD_INTERVAL = {
    "1d": "5m",
    "5d": "15m",
    "1mo": "1h",
    "6mo": "1d",
    "1y": "1d",
    "5y": "1wk",
    "max": "1wk",
}


@dataclass
class Quote:
    ticker: str
    price: float | None
    prev_close: float | None
    currency: str | None

    @property
    def change(self) -> float | None:
        if self.price is None or self.prev_close is None:
            return None
        return self.price - self.prev_close

    @property
    def change_pct(self) -> float | None:
        if self.change is None or not self.prev_close:
            return None
        return self.change / self.prev_close * 100


def get_history(ticker: str, period: str = "6mo", interval: str | None = None) -> pd.DataFrame:
    """OHLCV history for one ticker. Columns: Open/High/Low/Close/Volume.

    Fail-soft: Netz-/Rate-Limit-Fehler (Yahoo 429) liefern einen leeren Frame
    statt einer Exception — die UI zeigt dann "Keine Daten" statt zu sterben.
    """
    interval = interval or PERIOD_INTERVAL.get(period, "1d")
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df = df.rename(columns=str.title)
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")


def get_quote(ticker: str) -> Quote:
    """Latest price + previous close. Falls back to daily history if needed."""
    t = yf.Ticker(ticker)
    price = prev = currency = None
    try:
        fi = t.fast_info
        price = fi.get("lastPrice") if hasattr(fi, "get") else getattr(fi, "last_price", None)
        prev = fi.get("previousClose") if hasattr(fi, "get") else getattr(fi, "previous_close", None)
        currency = fi.get("currency") if hasattr(fi, "get") else getattr(fi, "currency", None)
    except Exception:
        pass
    if price is None or prev is None:
        try:
            hist = t.history(period="5d", interval="1d", auto_adjust=False)
        except Exception:
            hist = pd.DataFrame()
        if not hist.empty:
            closes = hist["Close"].dropna()
            if len(closes) >= 1 and price is None:
                price = float(closes.iloc[-1])
            if len(closes) >= 2 and prev is None:
                prev = float(closes.iloc[-2])
    return Quote(ticker=ticker, price=price, prev_close=prev, currency=currency)


def get_total_return_series(ticker: str, period: str = "10y") -> pd.Series:
    """Tägliche Total-Return-Kurse (auto_adjust=True: Dividenden reinvestiert).

    Grundlage für Jahresrenditen — die Fondskosten (TER) sind in diesen Kursen
    bereits verrechnet. Fail-soft: leere Series bei Netz-/Rate-Limit-Fehlern.
    """
    try:
        df = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=True)
    except Exception:
        return pd.Series(dtype=float)
    if df.empty or "Close" not in df.columns:
        return pd.Series(dtype=float)
    return df["Close"].dropna()


def get_watchlist_table(tickers: list[str]) -> pd.DataFrame:
    """One row per ticker with last price and daily change.

    Uses a single batched download for the closes, which is far faster than
    per-ticker quote calls when the list grows.
    """
    if not tickers:
        return pd.DataFrame()

    try:
        raw = yf.download(
            tickers,
            period="5d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
        )
    except Exception:
        raw = None  # Rate-Limit o. Ä. — Tabelle bleibt leer statt Absturz

    rows = []
    for t in tickers:
        try:
            closes = (raw[t]["Close"] if len(tickers) > 1 else raw["Close"]).dropna()
        except (KeyError, TypeError):
            closes = pd.Series(dtype=float)
        last = float(closes.iloc[-1]) if len(closes) >= 1 else None
        prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
        chg_pct = ((last - prev) / prev * 100) if (last is not None and prev) else None
        rows.append({"Ticker": t, "Kurs": last, "Veränderung %": chg_pct})

    return pd.DataFrame(rows)
