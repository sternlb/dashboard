"""Google-Calendar-Anbindung: Frei/Belegt lesen, Buchungen anlegen.

OAuth-Token mit Scope calendar.events (einmalig via setup_calendar.py).
Termindetails verlassen den Server nie — nach außen geht nur Frei/Belegt.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .config import (
    BOOKING_MARKER_KEY,
    GCAL_CALENDAR_ID,
    GCAL_SCOPES,
    GCAL_TOKEN_FILE,
    TZ,
)


def get_service():
    creds = Credentials.from_authorized_user_file(str(GCAL_TOKEN_FILE), GCAL_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        GCAL_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def get_busy(service, time_min: datetime, time_max: datetime) -> list[tuple[datetime, datetime]]:
    """Belegte Zeiträume laut freebusy (inkl. ganztägiger 'Beschäftigt'-Termine)."""
    body = {
        "timeMin": time_min.isoformat(),
        "timeMax": time_max.isoformat(),
        "timeZone": "Europe/Berlin",
        "items": [{"id": GCAL_CALENDAR_ID}],
    }
    result = service.freebusy().query(body=body).execute()
    periods = result["calendars"][GCAL_CALENDAR_ID].get("busy", [])
    return [
        (
            datetime.fromisoformat(p["start"]).astimezone(TZ),
            datetime.fromisoformat(p["end"]).astimezone(TZ),
        )
        for p in periods
    ]


def get_booked_days(service, time_min: datetime, time_max: datetime) -> set[date]:
    """Tage, an denen bereits eine Kundenbuchung (Marker-Event) liegt."""
    days: set[date] = set()
    page_token = None
    while True:
        result = (
            service.events()
            .list(
                calendarId=GCAL_CALENDAR_ID,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                privateExtendedProperty=f"{BOOKING_MARKER_KEY}=1",
                pageToken=page_token,
            )
            .execute()
        )
        for item in result.get("items", []):
            if item.get("status") == "cancelled":
                continue
            start = item.get("start", {})
            if "dateTime" in start:
                days.add(datetime.fromisoformat(start["dateTime"]).astimezone(TZ).date())
            elif "date" in start:
                days.add(date.fromisoformat(start["date"]))
        page_token = result.get("nextPageToken")
        if not page_token:
            return days


def insert_booking(
    service,
    *,
    type_key: str,
    type_label: str,
    start: datetime,
    end: datetime,
    name: str,
    email: str,
    organization: str,
    note: str,
    online: bool,
) -> dict:
    """Buchung als Kalender-Event anlegen; Google verschickt die Einladung."""
    description_lines = [
        f"Buchung über den Basel-AI Buchungskalender.",
        f"Name: {name}",
        f"E-Mail: {email}",
    ]
    if organization:
        description_lines.append(f"Einrichtung: {organization}")
    if note:
        description_lines.append(f"Anliegen: {note}")

    event = {
        "summary": f"[Buchung] {type_label} — {name}",
        "description": "\n".join(description_lines),
        "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Berlin"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Berlin"},
        "attendees": [{"email": email, "displayName": name}],
        "extendedProperties": {
            "private": {BOOKING_MARKER_KEY: "1", "baselai_type": type_key}
        },
    }
    kwargs = {"sendUpdates": "all"}
    if online:
        event["conferenceData"] = {
            "createRequest": {
                "requestId": uuid.uuid4().hex,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }
        kwargs["conferenceDataVersion"] = 1

    try:
        return (
            service.events()
            .insert(calendarId=GCAL_CALENDAR_ID, body=event, **kwargs)
            .execute()
        )
    except Exception:
        if not online:
            raise
        # Meet-Link-Erzeugung kann an Konto-Restriktionen scheitern —
        # dann ohne Konferenz buchen statt die Buchung zu verlieren.
        event.pop("conferenceData", None)
        return (
            service.events()
            .insert(calendarId=GCAL_CALENDAR_ID, body=event, sendUpdates="all")
            .execute()
        )
