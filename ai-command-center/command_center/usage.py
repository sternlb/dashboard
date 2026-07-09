"""Token-Nutzung — parst lokale Claude-Code-Session-Logs (JSONL).

Wichtig: gezählt werden **echte Input+Output-Tokens**. Cache-Reads (das ständige
Wiedereinlesen des gecachten Kontexts) werden NICHT mitgezählt — die blähen die
Summe sonst um Faktor ~100 auf und sagen nichts über die tatsächliche Nutzung.

Dedup: Claude Code schreibt bei gestreamten Antworten pro Content-Block eine
eigene JSONL-Zeile, jede mit demselben usage-Objekt — ohne Deduplizierung wird
derselbe API-Call ~2-3× gezählt. Schlüssel wie bei ccusage: message.id +
requestId; bei abweichenden Duplikaten gewinnt der höchste Wert (das ist der
finale Streaming-Stand).

Anthropic bietet keinen API-Endpunkt für das Rest-Limit (Claude Code zeigt es nur
in `/status`). Deshalb: lokale Nutzung in den zwei Limit-Fenstern (5 Std + Woche);
die Caps kann Leo optional manuell setzen, dann zeigt das Dashboard „noch frei".
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .config import CLAUDE_PROJECTS_DIR, TOKEN_STATE_FILE


@dataclass
class UsageSummary:
    tokens_5h: int = 0        # echte Input+Output-Tokens im 5-Std-Fenster
    msgs_5h: int = 0
    tokens_today: int = 0
    tokens_7d: int = 0
    tokens_total: int = 0
    sessions: int = 0
    by_day: dict[str, int] = field(default_factory=dict)  # ISO-Datum -> Input+Output
    # Ältester Eintrag im aktuellen 5-Std-Fenster — daraus schätzt das Dashboard
    # die Reset-Zeit (ältester Eintrag + 5 Std), wie Claude sie unter
    # Einstellungen → Nutzung anzeigt.
    window_start_5h: datetime | None = None


def _iter_records(root: Path):
    for f in root.rglob("*.jsonl"):
        try:
            fh = f.open("r", encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def load_usage(root: Path | None = None) -> UsageSummary:
    root = root or CLAUDE_PROJECTS_DIR
    s = UsageSummary()
    if not root.exists():
        return s

    # Pass 1: pro API-Call (message.id + requestId) genau einen Eintrag behalten.
    best: dict[tuple, tuple[int, str | None, str | None]] = {}
    for rec in _iter_records(root):
        if rec.get("type") != "assistant":
            continue
        msg = rec.get("message") or {}
        u = msg.get("usage") or {}
        io = int(u.get("input_tokens", 0) or 0) + int(u.get("output_tokens", 0) or 0)
        if io == 0:
            continue
        mid = msg.get("id")
        key = (mid, rec.get("requestId")) if mid else ("uuid", rec.get("uuid"))
        prev = best.get(key)
        if prev is None or io > prev[0]:
            best[key] = (io, rec.get("timestamp"), rec.get("sessionId"))

    # Pass 2: deduplizierte Einträge in die Zeitfenster einsortieren.
    now = datetime.now(timezone.utc).astimezone()
    h5 = now - timedelta(hours=5)
    today = date.today()
    week_start = today - timedelta(days=6)
    seen: set[str] = set()

    for io, ts, sid in best.values():
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone()
        except (ValueError, TypeError):
            continue
        d = dt.date()

        s.tokens_total += io
        s.by_day[d.isoformat()] = s.by_day.get(d.isoformat(), 0) + io
        if d == today:
            s.tokens_today += io
        if d >= week_start:
            s.tokens_7d += io
        if dt >= h5:
            s.tokens_5h += io
            s.msgs_5h += 1
            if s.window_start_5h is None or dt < s.window_start_5h:
                s.window_start_5h = dt

        if sid:
            seen.add(str(sid))

    s.sessions = len(seen)
    return s


# --- Manueller Zustand: Free-Credit + Limit-Caps -----------------------------
@dataclass
class TokenState:
    free_amount: float = 0.0
    currency: str = "USD"
    updated: str = ""
    limit_5h: int = 0     # Token-Cap 5-Std-Fenster (0 = nicht gesetzt)
    limit_week: int = 0   # Token-Cap Woche (0 = nicht gesetzt)
    week_reset: str = ""  # Anzeigetext, wann das Wochenlimit zurücksetzt (aus /status)


def load_token_state(path: Path | None = None) -> TokenState:
    path = path or TOKEN_STATE_FILE
    if not path.exists():
        return TokenState()
    try:
        # utf-8-sig: toleriert ein BOM (z. B. von Windows-Editoren/PowerShell)
        d = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return TokenState()
    return TokenState(
        free_amount=float(d.get("free_amount", d.get("amount", 0)) or 0),
        currency=str(d.get("currency", "USD")),
        updated=str(d.get("updated", "")),
        limit_5h=int(d.get("limit_5h", 0) or 0),
        limit_week=int(d.get("limit_week", 0) or 0),
        week_reset=str(d.get("week_reset", "")),
    )


def save_token_state(state: TokenState, path: Path | None = None) -> None:
    path = path or TOKEN_STATE_FILE
    path.write_text(
        json.dumps(
            {
                "free_amount": state.free_amount,
                "currency": state.currency,
                "updated": state.updated,
                "limit_5h": state.limit_5h,
                "limit_week": state.limit_week,
                "week_reset": state.week_reset,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
