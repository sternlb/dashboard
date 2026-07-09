"""Verfügbarkeitslogik: Buchungsfenster minus belegte Zeiten, 1 Termin pro Tag.

Reine Logik ohne Google-API — testbar mit beliebigen Busy-Listen.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .config import (
    BOOKING_WINDOWS,
    BUFFER_MIN,
    HORIZON_DAYS,
    MIN_LEAD_HOURS,
    SLOT_STEP_MIN,
    TZ,
)


def booking_range(now: datetime) -> tuple[datetime, datetime]:
    """Erlaubter Buchungszeitraum [jetzt+Vorlauf, jetzt+Horizont]."""
    return now + timedelta(hours=MIN_LEAD_HOURS), now + timedelta(days=HORIZON_DAYS)


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def day_slots(
    day: date,
    duration_min: int,
    busy: list[tuple[datetime, datetime]],
    booked_days: set[date],
    now: datetime,
) -> list[datetime]:
    """Freie Startzeiten eines Tages. Leere Liste, wenn der Tag gesperrt ist."""
    if day in booked_days:
        return []
    windows = BOOKING_WINDOWS.get(day.weekday(), [])
    if not windows:
        return []

    earliest, latest = booking_range(now)
    duration = timedelta(minutes=duration_min)
    buffer = timedelta(minutes=BUFFER_MIN)
    step = timedelta(minutes=SLOT_STEP_MIN)

    slots: list[datetime] = []
    for win_start, win_end in windows:
        cursor = datetime.combine(day, _parse_hhmm(win_start), tzinfo=TZ)
        window_end = datetime.combine(day, _parse_hhmm(win_end), tzinfo=TZ)
        while cursor + duration <= window_end:
            slot_end = cursor + duration + buffer
            if (
                cursor >= earliest
                and cursor <= latest
                and not any(b_start < slot_end and b_end > cursor for b_start, b_end in busy)
            ):
                slots.append(cursor)
            cursor += step
    return slots


def month_availability(
    year: int,
    month: int,
    duration_min: int,
    busy: list[tuple[datetime, datetime]],
    booked_days: set[date],
    now: datetime,
) -> dict[str, list[str]]:
    """{ISO-Datum: ["15:00", "15:30", …]} für alle buchbaren Tage des Monats."""
    result: dict[str, list[str]] = {}
    day = date(year, month, 1)
    while day.month == month:
        slots = day_slots(day, duration_min, busy, booked_days, now)
        if slots:
            result[day.isoformat()] = [s.strftime("%H:%M") for s in slots]
        day += timedelta(days=1)
    return result
