"""Einmalige Google-Kalender-Einrichtung (OAuth-Consent).

Voraussetzung: `credentials.json` (OAuth-Client „Desktop app" aus der Google
Cloud Console) liegt neben dieser Datei.

Ausführen:
    .venv\\Scripts\\python setup_calendar.py

Es öffnet sich der Browser, du meldest dich mit deinem Google-Konto an und
gibst Lesezugriff auf den Kalender frei. Danach wird `token.json` gespeichert
und das Dashboard kann Termine anzeigen.
"""
from __future__ import annotations

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from command_center.config import (
    GCAL_CREDENTIALS_FILE,
    GCAL_SCOPES,
    GCAL_TOKEN_FILE,
)


def main() -> int:
    if not GCAL_CREDENTIALS_FILE.exists():
        print(f"Fehlt: {GCAL_CREDENTIALS_FILE}")
        print("Erst credentials.json aus der Google Cloud Console (OAuth-Client")
        print("'Desktop app') herunterladen und hier ablegen.")
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(
        str(GCAL_CREDENTIALS_FILE), GCAL_SCOPES
    )
    creds = flow.run_local_server(port=0)
    GCAL_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"OK — token.json gespeichert unter {GCAL_TOKEN_FILE}")
    print("Das Dashboard zeigt jetzt kommende Termine.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
