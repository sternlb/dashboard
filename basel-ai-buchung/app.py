"""Buchungskalender Basel-AI Consulting — FastAPI-Server (Port 8505).

Zeigt freie Zeiten aus dem Google Kalender und nimmt Buchungen entgegen.
Regeln (Fenster, Vorlauf, 1 Termin/Tag) in booking/config.py.

Start:  .venv\\Scripts\\python app.py
Setup:  einmalig .venv\\Scripts\\python setup_calendar.py (OAuth-Consent)
"""
from __future__ import annotations

import re
import time as time_mod
from collections import defaultdict, deque
from datetime import date, datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from booking import availability, gcal
from booking.config import (
    APPOINTMENT_TYPES,
    BASE_DIR,
    GCAL_TOKEN_FILE,
    HOST,
    MAX_BOOKINGS_PER_IP_PER_HOUR,
    MAX_BOOKINGS_TOTAL_PER_DAY,
    PORT,
    TZ,
)

app = FastAPI(title="Basel-AI Buchungskalender", docs_url=None, redoc_url=None)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

# In-Memory-Rate-Limit (bei Neustart leer — für den Zweck ausreichend)
_bookings_by_ip: dict[str, deque[float]] = defaultdict(deque)
_bookings_today: deque[float] = deque()


class BookingRequest(BaseModel):
    type: str
    start: str                     # ISO, z. B. "2026-07-10T15:00"
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=200)
    organization: str = Field(default="", max_length=200)
    note: str = Field(default="", max_length=2000)
    website: str = ""              # Honeypot — Menschen lassen das Feld leer


def _check_rate_limit(ip: str) -> None:
    now = time_mod.time()
    per_ip = _bookings_by_ip[ip]
    while per_ip and per_ip[0] < now - 3600:
        per_ip.popleft()
    while _bookings_today and _bookings_today[0] < now - 86400:
        _bookings_today.popleft()
    if len(per_ip) >= MAX_BOOKINGS_PER_IP_PER_HOUR or len(_bookings_today) >= MAX_BOOKINGS_TOTAL_PER_DAY:
        raise HTTPException(429, "Zu viele Anfragen — bitte später erneut versuchen.")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "calendar_ready": GCAL_TOKEN_FILE.exists()}


@app.get("/api/types")
def types():
    return {
        key: {k: v for k, v in cfg.items() if k != "online"}
        for key, cfg in APPOINTMENT_TYPES.items()
    }


@app.get("/api/availability")
def get_availability(type: str, year: int, month: int):
    cfg = APPOINTMENT_TYPES.get(type)
    if not cfg:
        raise HTTPException(404, "Unbekannter Termin-Typ.")
    if not (1 <= month <= 12):
        raise HTTPException(422, "Ungültiger Monat.")

    now = datetime.now(TZ)
    earliest, latest = availability.booking_range(now)
    month_start = datetime(year, month, 1, tzinfo=TZ)
    next_month = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=TZ)
    if next_month < earliest or month_start > latest:
        return {"days": {}}

    service = gcal.get_service()
    busy = gcal.get_busy(service, month_start - timedelta(days=1), next_month + timedelta(days=1))
    booked = gcal.get_booked_days(service, month_start - timedelta(days=1), next_month + timedelta(days=1))
    days = availability.month_availability(year, month, cfg["duration_min"], busy, booked, now)
    return {"days": days}


@app.post("/api/book")
def book(req: BookingRequest, request: Request):
    if req.website:  # Honeypot ausgefüllt → Bot
        raise HTTPException(400, "Anfrage abgelehnt.")
    cfg = APPOINTMENT_TYPES.get(req.type)
    if not cfg:
        raise HTTPException(404, "Unbekannter Termin-Typ.")
    if not EMAIL_RE.match(req.email.strip()):
        raise HTTPException(422, "Bitte eine gültige E-Mail-Adresse angeben.")

    try:
        start = datetime.fromisoformat(req.start)
    except ValueError:
        raise HTTPException(422, "Ungültige Startzeit.")
    start = start.replace(tzinfo=TZ) if start.tzinfo is None else start.astimezone(TZ)

    ip = request.client.host if request.client else "?"
    _check_rate_limit(ip)

    # Verfügbarkeit serverseitig erneut prüfen (Slot kann inzwischen weg sein)
    now = datetime.now(TZ)
    service = gcal.get_service()
    day_start = datetime.combine(start.date(), datetime.min.time(), tzinfo=TZ)
    day_end = day_start + timedelta(days=1)
    busy = gcal.get_busy(service, day_start, day_end)
    booked = gcal.get_booked_days(service, day_start, day_end)
    free_slots = availability.day_slots(start.date(), cfg["duration_min"], busy, booked, now)
    if start not in free_slots:
        raise HTTPException(409, "Dieser Termin ist leider nicht mehr verfügbar. Bitte einen anderen Slot wählen.")

    event = gcal.insert_booking(
        service,
        type_key=req.type,
        type_label=cfg["label"],
        start=start,
        end=start + timedelta(minutes=cfg["duration_min"]),
        name=req.name.strip(),
        email=req.email.strip(),
        organization=req.organization.strip(),
        note=req.note.strip(),
        online=cfg.get("online", False),
    )

    stamp = time_mod.time()
    _bookings_by_ip[ip].append(stamp)
    _bookings_today.append(stamp)

    return {
        "ok": True,
        "label": cfg["label"],
        "start": start.isoformat(),
        "duration_min": cfg["duration_min"],
        "meet_link": event.get("hangoutLink", ""),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
