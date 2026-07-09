"""Trading strategies → desired market exposure.

Each strategy takes an OHLCV DataFrame and returns a `position` Series aligned
to its index: 1.0 = fully long, 0.0 = flat. (Short selling can be added later
with -1.0.) Pure pandas, reuses `indicators`, no UI dependency — the backtester
and the future live agent consume the exact same functions.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from . import indicators


def sma_crossover(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.Series:
    """Long while the fast SMA is above the slow SMA (trend-following)."""
    close = df["Close"]
    f, s = indicators.sma(close, fast), indicators.sma(close, slow)
    pos = (f > s).astype(float)
    pos[f.isna() | s.isna()] = 0.0  # flat until both averages exist
    return pos


def macd_cross(df: pd.DataFrame) -> pd.Series:
    """Long while the MACD line is above its signal line (momentum)."""
    m = indicators.macd(df["Close"])
    pos = (m["macd"] > m["signal"]).astype(float)
    pos[m["signal"].isna()] = 0.0
    return pos


def rsi_reversion(df: pd.DataFrame, low: float = 30, high: float = 70) -> pd.Series:
    """Mean-reversion: buy when RSI dips below `low`, exit when it tops `high`."""
    rsi = indicators.rsi(df["Close"])
    pos = pd.Series(0.0, index=df.index)
    holding = 0.0
    for i, v in enumerate(rsi.to_numpy()):
        if not pd.isna(v):
            if holding == 0.0 and v < low:
                holding = 1.0
            elif holding == 1.0 and v > high:
                holding = 0.0
        pos.iloc[i] = holding
    return pos


# Registry the dashboard iterates over. Add new strategies here.
STRATEGIES: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "SMA Crossover (20/50)": sma_crossover,
    "MACD Cross": macd_cross,
    "RSI Reversion (30/70)": rsi_reversion,
}


def position_changes(position: pd.Series) -> tuple[pd.Index, pd.Index]:
    """Timestamps where a position is opened (entries) and closed (exits)."""
    prev = position.shift(1).fillna(0.0)
    entries = position.index[(prev == 0.0) & (position == 1.0)]
    exits = position.index[(prev == 1.0) & (position == 0.0)]
    return entries, exits
