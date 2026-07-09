"""Trading Agent eingehängt — liest dessen Daten read-only für eine Depot-Kurzübersicht.

Contract: das Command Center liest nur die vorhandenen Datendateien des Trading
Agents (holdings.csv, last_update.txt, favorites.json). Der Trading Agent selbst
bleibt unverändert. Fehlt etwas, kommt ein sauberer „nicht verfügbar"-Zustand.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import TRADING_AGENT_DIR


@dataclass
class TradingSummary:
    available: bool = False
    total_value: float = 0.0
    total_cost: float = 0.0
    positions: int = 0
    updated: str = ""
    top_theme: str = ""
    top_theme_share: float = 0.0
    top_position: str = ""
    favorites: int = 0
    order_sheet: int = 0
    detail: str = ""

    @property
    def gain_eur(self) -> float:
        return self.total_value - self.total_cost

    @property
    def gain_pct(self) -> float:
        return (self.gain_eur / self.total_cost * 100) if self.total_cost else 0.0


def _read_float(v: str) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def load_trading_summary(base: Path | None = None) -> TradingSummary:
    base = base or TRADING_AGENT_DIR
    holdings = base / "data" / "holdings.csv"
    if not holdings.exists():
        return TradingSummary(detail=f"holdings.csv nicht gefunden unter {holdings}")

    try:
        s = TradingSummary(available=True)
        by_theme: dict[str, float] = {}
        top_val = 0.0
        with holdings.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                val = _read_float(row.get("value_eur", ""))
                s.total_value += val
                s.total_cost += _read_float(row.get("cost_eur", ""))
                s.positions += 1
                theme = (row.get("theme") or "—").strip()
                by_theme[theme] = by_theme.get(theme, 0.0) + val
                if val > top_val:
                    top_val = val
                    s.top_position = (row.get("name") or "").strip()

        if by_theme:
            s.top_theme, theme_val = max(by_theme.items(), key=lambda kv: kv[1])
            s.top_theme_share = (theme_val / s.total_value * 100) if s.total_value else 0.0

        upd = base / "data" / "last_update.txt"
        if upd.exists():
            s.updated = upd.read_text(encoding="utf-8").strip()

        fav = base / "data" / "favorites.json"
        if fav.exists():
            try:
                data = json.loads(fav.read_text(encoding="utf-8"))
                s.favorites = len(data.get("tickers", []))
                s.order_sheet = len(data.get("orders", {}))
            except json.JSONDecodeError:
                pass

        return s
    except OSError as exc:
        return TradingSummary(detail=str(exc))
