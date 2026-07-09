"""Einmalige Google-Kalender-Einrichtung (OAuth-Consent, Scope calendar.events).

Voraussetzung: credentials.json (OAuth-Client "Desktop app") liegt neben dieser
Datei — derselbe Client wie im AI Command Center funktioniert, es wird nur ein
neues Token mit Schreibrechten auf Termine erzeugt.

Ausführen:
    .venv\\Scripts\\python setup_calendar.py
"""
from __future__ import annotations

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from booking.config import GCAL_CREDENTIALS_FILE, GCAL_SCOPES, GCAL_TOKEN_FILE


def main() -> int:
    if not GCAL_CREDENTIALS_FILE.exists():
        print(f"Fehlt: {GCAL_CREDENTIALS_FILE}")
        print("credentials.json aus der Google Cloud Console (OAuth-Client 'Desktop app') hier ablegen.")
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(str(GCAL_CREDENTIALS_FILE), GCAL_SCOPES)
    creds = flow.run_local_server(port=0)
    GCAL_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"OK — token.json gespeichert unter {GCAL_TOKEN_FILE}")
    print("Der Buchungskalender kann jetzt Termine lesen und anlegen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
