"""Drive-Links für abgelegte Scans — löst lokale Drive-for-Desktop-Pfade
(z. B. G:\\Meine Ablage\\Leo\\Inbox\\Bank\\x.pdf) in Google-Drive-Web-Links auf.

Quelle ist die lokale Metadaten-DB von Google Drive für Desktop
(%LOCALAPPDATA%\\Google\\DriveFS\\<konto>\\metadata_sqlite_db), **read-only**.
Der Pfad wird ab dem Drive-Root Ebene für Ebene über den Ordnernamen aufgelöst.
Kein API-Zugang, kein OAuth. Findet sich nichts (Datei verschoben/umbenannt,
noch nicht hochgeladen, DriveFS fehlt), gibt es einfach keinen Link.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path, PureWindowsPath

_DB_GLOB = "Google/DriveFS/*/metadata_sqlite_db"
_CLOUD_ID = re.compile(r"[A-Za-z0-9_-]{10,}")

FILE_URL = "https://drive.google.com/file/d/{}/view"
FOLDER_URL = "https://drive.google.com/drive/folders/{}"


def _databases() -> list[Path]:
    base = Path(os.environ.get("LOCALAPPDATA", ""))
    return sorted(base.glob(_DB_GLOB)) if base.parts else []


def _resolve(con: sqlite3.Connection, parts: list[str]) -> list[str | None]:
    """Cloud-IDs für jede Ebene unterhalb des Roots (None ab der ersten Lücke)."""
    root = con.execute(
        "SELECT stable_id FROM items WHERE local_title = ? AND is_folder "
        "AND stable_id NOT IN (SELECT item_stable_id FROM stable_parents)",
        (parts[0],),
    ).fetchone()
    ids: list[str | None] = [None] * (len(parts) - 1)
    if not root:
        return ids
    cur = root[0]
    for i, name in enumerate(parts[1:]):
        hit = con.execute(
            "SELECT i.stable_id, i.id FROM items i JOIN stable_parents p "
            "ON p.item_stable_id = i.stable_id "
            "WHERE p.parent_stable_id = ? AND i.local_title = ? AND NOT i.trashed",
            (cur, name),
        ).fetchone()
        if not hit:
            break
        cur = hit[0]
        ids[i] = hit[1] if _CLOUD_ID.fullmatch(hit[1] or "") else None
    return ids


def drive_links(folder: str, filename: str) -> tuple[str, str]:
    """(Datei-URL, Ordner-URL) — jeweils "" wenn nicht auflösbar."""
    if not folder:
        return "", ""
    # Drive-Root ("Meine Ablage") + Unterordner, ohne Laufwerksbuchstaben.
    dirs = list(PureWindowsPath(folder).parts[1:])
    if len(dirs) < 2:  # Root selbst oder kein Drive-Pfad
        return "", ""
    parts = dirs + ([filename] if filename else [])
    for db in _databases():
        try:
            con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=1)
            try:
                ids = _resolve(con, parts)
            finally:
                con.close()
        except sqlite3.Error:
            continue
        folder_id = ids[len(dirs) - 2]
        file_id = ids[-1] if filename else None
        if file_id or folder_id:
            return (
                FILE_URL.format(file_id) if file_id else "",
                FOLDER_URL.format(folder_id) if folder_id else "",
            )
    return "", ""
