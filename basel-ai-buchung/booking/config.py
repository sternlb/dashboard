"""Konfiguration Buchungskalender Basel-AI.

Buchungsfenster, Termin-Typen und Regeln hier anpassen — der Rest des Codes
liest ausschließlich aus dieser Datei.
"""
from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("Europe/Berlin")

# --- Google Calendar ---
GCAL_CALENDAR_ID = "primary"
GCAL_CREDENTIALS_FILE = BASE_DIR / "credentials.json"
GCAL_TOKEN_FILE = BASE_DIR / "token.json"
# events = Termine lesen/anlegen, freebusy = Frei/Belegt-Abfrage
GCAL_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]

# Marker in extendedProperties, an dem eigene Buchungen erkannt werden
# (Grundlage der 1-Termin-pro-Tag-Regel)
BOOKING_MARKER_KEY = "baselai_booking"

# --- Buchungsregeln ---
MIN_LEAD_HOURS = 48        # frühester buchbarer Slot: jetzt + 48 h
HORIZON_DAYS = 60          # Buchungen maximal 60 Tage im Voraus
SLOT_STEP_MIN = 30         # Raster der Startzeiten
BUFFER_MIN = 15            # Puffer nach jedem Termin (gegen belegte Zeiten geprüft)
MAX_BOOKINGS_PER_DAY = 1   # Kernregel: ein Kundentermin pro Tag

# Buchbare Fenster pro Wochentag (0=Montag … 6=Sonntag), lokale Uhrzeit.
# Wochentage ohne Eintrag sind nicht buchbar.
BOOKING_WINDOWS: dict[int, list[tuple[str, str]]] = {
    0: [("15:00", "19:00")],  # Montag
    1: [("15:00", "19:00")],  # Dienstag
    2: [("15:00", "19:00")],  # Mittwoch
    3: [("15:00", "19:00")],  # Donnerstag
    4: [("14:00", "18:00")],  # Freitag
}

# --- Termin-Typen (Leistungen aus Firma.md) ---
APPOINTMENT_TYPES: dict[str, dict] = {
    "erstgespraech": {
        "label": "Kostenloses Erstgespräch",
        "duration_min": 30,
        "online": True,
        "price": "kostenlos · online",
        "description": "Kennenlernen und Anliegen klären: Wo stehen Sie, was ist mit KI in Ihrer Einrichtung möglich?",
    },
    "coaching": {
        "label": "1:1-Coaching",
        "duration_min": 60,
        "online": True,
        "price": "120 € Schulen · 150 € Unternehmen (netto) · online",
        "description": "Konkrete Fragen und Workflows einer Lehrkraft — direkt am eigenen Material, per Videocall.",
    },
    "beratung": {
        "label": "Beratungsgespräch",
        "duration_min": 60,
        "online": True,
        "price": "110 €/h Schulen · 150 €/h Unternehmen (netto) · online",
        "description": "Tool-Auswahl, datenschutzbewusste Einführung, KI-Strategie für Ihre Bildungseinrichtung.",
    },
}

# --- Server & Schutz ---
HOST = "0.0.0.0"
PORT = 8505
MAX_BOOKINGS_PER_IP_PER_HOUR = 3
MAX_BOOKINGS_TOTAL_PER_DAY = 10  # Notbremse gegen Spam-Wellen
