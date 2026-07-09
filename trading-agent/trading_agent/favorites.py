"""Favoriten + Order-Sheet-Persistenz.

Speichert die markierten Favoriten (Ticker) und die geplanten Orders
(Betrag, Notiz je Ticker) in einer kleinen JSON-Datei, damit die Auswahl
Sessions überlebt. Bewusst simpel — eine Planungshilfe, kein Orderrouting.
"""

from __future__ import annotations

import json
from pathlib import Path


def load(path: str | Path) -> dict:
    p = Path(path)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data.setdefault("tickers", [])   # favorisierte Vorschläge (Ticker)
            data.setdefault("depot", [])     # favorisierte Depotpositionen (ISIN)
            data.setdefault("orders", {})    # key (Ticker|ISIN) -> {amount, note, action}
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"tickers": [], "depot": [], "orders": {}}


def save(path: str | Path, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
