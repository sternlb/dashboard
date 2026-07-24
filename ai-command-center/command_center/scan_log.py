"""Scanner-Ablage — liest das Bewegungs-Logbuch des scan-workflow-Repos read-only.

Contract wie beim Trading Agent: das Command Center liest nur die vorhandene
Datei (scan_log.csv, Semikolon-CSV mit BOM), der Scanner-Workflow bleibt
unverändert. Fehlt die Datei, kommt ein sauberer „noch nichts da"-Zustand.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import SCAN_LOG_FILE, SCAN_LOG_LIMIT

_TS_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class ScanEntry:
    when: datetime | None = None
    when_raw: str = ""
    action: str = ""          # kopiert | übersprungen | fehler
    person: str = ""
    typ: str = ""
    source_name: str = ""
    source_dir: str = ""
    target_name: str = ""
    target_dir: str = ""
    absender: str = ""
    betreff: str = ""
    note: str = ""

    def short_dir(self, parts: int = 3) -> str:
        """Zielordner gekürzt auf die letzten Ebenen, z. B. Leo / Inbox / Bank."""
        if not self.target_dir:
            return ""
        chunks = [c for c in Path(self.target_dir).parts if c not in ("\\", "/")]
        return " / ".join(chunks[-parts:])


@dataclass
class ScanLogResult:
    state: str = "ok"   # ok | missing | empty | error
    detail: str = ""
    entries: list[ScanEntry] = field(default_factory=list)
    total: int = 0
    path: Path | None = None


def _parse_when(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw.strip(), _TS_FORMAT)
    except (ValueError, AttributeError):
        return None


def _to_entry(row: dict) -> ScanEntry:
    def g(key: str) -> str:
        return str(row.get(key) or "").strip()

    raw = g("zeitpunkt")
    return ScanEntry(
        when=_parse_when(raw),
        when_raw=raw,
        action=g("aktion"),
        person=g("person"),
        typ=g("typ"),
        source_name=g("quelldatei"),
        source_dir=g("quellordner"),
        target_name=g("zieldatei"),
        target_dir=g("zielordner"),
        absender=g("absender"),
        betreff=g("betreff"),
        note=g("hinweis"),
    )


def load_scan_log(path: Path | None = None, limit: int | None = None) -> ScanLogResult:
    """Die letzten `limit` Einträge, neueste zuerst."""
    path = Path(path or SCAN_LOG_FILE)
    limit = SCAN_LOG_LIMIT if limit is None else limit

    if not path.exists():
        return ScanLogResult(state="missing", detail=str(path), path=path)

    try:
        # utf-8-sig: der Workflow schreibt beim Anlegen ein BOM (Excel-tauglich).
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = [r for r in csv.DictReader(fh, delimiter=";") if any(r.values())]
    except (OSError, csv.Error, UnicodeDecodeError) as e:
        return ScanLogResult(state="error", detail=str(e), path=path)

    if not rows:
        return ScanLogResult(state="empty", path=path)

    entries = [_to_entry(r) for r in rows[-limit:]]
    entries.reverse()  # neueste zuerst
    return ScanLogResult(entries=entries, total=len(rows), path=path)
