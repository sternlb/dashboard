# Buchungskalender Basel-AI Consulting

Kunden sehen freie Zeiten aus Leos Google Kalender und buchen direkt einen Termin.
Kernregel: **maximal 1 Termin pro Tag**. FastAPI-Server auf Port **8505**.

## Setup (einmalig)

```
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
# credentials.json (OAuth-Client "Desktop app") hierher kopieren, dann:
.venv\Scripts\python setup_calendar.py   # Browser-Consent, erzeugt token.json
```

## Start

```
.venv\Scripts\python app.py    # http://localhost:8505
```

## Wie es funktioniert

- `booking/config.py` — **alle Regeln**: Buchungsfenster je Wochentag, Vorlauf (48 h),
  Horizont (60 Tage), Slot-Raster (30 min), Puffer (15 min), Termin-Typen mit Dauer/Preis.
- `GET /api/availability` — Google `freebusy` (belegte Zeiten, Details bleiben privat)
  minus Buchungsfenster; Tage mit bestehender Buchung (Marker
  `extendedProperties.private.baselai_booking=1`) sind komplett gesperrt.
- `POST /api/book` — prüft den Slot serverseitig erneut (Race Condition), legt das Event
  mit dem Kunden als Attendee an (`sendUpdates=all` → Google verschickt die Einladung)
  und erzeugt für Online-Formate einen Meet-Link.
- Spam-Schutz: Honeypot-Feld + Rate-Limit (3 Buchungen/IP/Stunde, 10/Tag gesamt).

## Deployment (offen)

Läuft aktuell nur lokal/LAN. Für echte Kundenbuchungen: VPS (z. B. Hetzner) oder
Google Cloud Run + Domain `buchung.basel-ai.de` + HTTPS. `token.json` mit umziehen.
Vor Go-Live: Impressum/Datenschutzerklärung verlinken, E-Mail-Double-Opt-in erwägen.
