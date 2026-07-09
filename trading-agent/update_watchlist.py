"""Wöchentlicher Watchlist-Update (für den Windows-Task / Cron).

Holt für die Lücken-Kandidaten aus research.CANDIDATES die aktuellen Kurse,
1-Wochen- und 1-Monats-Veränderung sowie das aktuelle Trendsignal (SMA 50/200)
und schreibt einen Snapshot nach data/watchlist_snapshot.csv. Das Dashboard
zeigt diesen Snapshot mit Zeitstempel an.

Manuell ausführbar:  .venv\\Scripts\\python.exe update_watchlist.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from trading_agent import data, research, signals

OUT_CSV = Path("data/watchlist_snapshot.csv")
OUT_STAMP = Path("data/last_update.txt")


def pct_change(close: pd.Series, bars: int) -> float | None:
    if len(close) <= bars:
        return None
    prev = close.iloc[-(bars + 1)]
    last = close.iloc[-1]
    return (last - prev) / prev * 100 if prev else None


def main() -> int:
    rows = []
    for c in research.CANDIDATES:
        t = c["ticker"]
        hist = data.get_history(t, period="1y")
        quote = data.get_quote(t)
        close = hist["Close"].dropna() if not hist.empty else pd.Series(dtype=float)

        if len(close) > 200:
            signal = "🟢 Long" if signals.sma_crossover(close.to_frame("Close")).iloc[-1] else "⚪ Flat"
        else:
            signal = "—"

        rows.append({
            "ticker": t,
            "name": c["name"],
            "gruppe": c.get("group", ""),
            "theme": c["theme"],
            "Kurs": quote.price,
            "1W %": pct_change(close, 5),
            "1M %": pct_change(close, 21),
            "Signal": signal,
            "kaufbar": c["ucits"],
            "warum": c["why"],
        })

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    OUT_STAMP.write_text(dt.datetime.now().strftime("%Y-%m-%d %H:%M"), encoding="utf-8")
    print(f"Watchlist aktualisiert: {len(df)} Kandidaten -> {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
