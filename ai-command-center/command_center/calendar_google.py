"""Google Calendar (read-only) — kommende Termine für das Dashboard.

Zugriff über OAuth-„Installed App"-Flow: einmalig `setup_calendar.py` ausführen,
danach liest das Dashboard `token.json`. Alles ohne Konfiguration liefert einen
sauberen „Einrichtung nötig"-Zustand statt eines Fehlers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .config import (
    GCAL_CALENDAR_ID,
    GCAL_CREDENTIALS_FILE,
    GCAL_MAX_EVENTS,
    GCAL_SCOPES,
    GCAL_TOKEN_FILE,
)


@dataclass
class CalEvent:
    summary: str
    start: datetime
    all_day: bool = False
    location: str = ""


@dataclass
class CalResult:
    state: str                       # ok | needs_credentials | needs_setup | error
    events: list[CalEvent] = field(default_factory=list)
    detail: str = ""


def _load_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials.from_authorized_user_file(str(GCAL_TOKEN_FILE), GCAL_SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        GCAL_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _parse_event(item: dict) -> CalEvent:
    start = item.get("start", {})
    if "dateTime" in start:
        dt = datetime.fromisoformat(start["dateTime"])
        all_day = False
    else:  # ganztägig (nur "date")
        dt = datetime.fromisoformat(start["date"]).replace(tzinfo=timezone.utc)
        all_day = True
    return CalEvent(
        summary=item.get("summary", "(ohne Titel)"),
        start=dt,
        all_day=all_day,
        location=item.get("location", ""),
    )


def load_events(max_results: int | None = None) -> CalResult:
    if not GCAL_CREDENTIALS_FILE.exists():
        return CalResult(state="needs_credentials")
    if not GCAL_TOKEN_FILE.exists():
        return CalResult(state="needs_setup")

    try:
        from googleapiclient.discovery import build

        creds = _load_credentials()
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        now = datetime.now(timezone.utc).isoformat()
        result = (
            service.events()
            .list(
                calendarId=GCAL_CALENDAR_ID,
                timeMin=now,
                maxResults=max_results or GCAL_MAX_EVENTS,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = [_parse_event(i) for i in result.get("items", [])]
        return CalResult(state="ok", events=events)
    except Exception as exc:  # Netzwerk, Token, API — nie das Dashboard crashen
        return CalResult(state="error", detail=str(exc))
