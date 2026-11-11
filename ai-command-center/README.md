# AI Command Center

Top-Level-Dashboard als persönliche Kommandozentrale. Hängt Fachdashboards
(z. B. den Trading Agent) als Module ein. Das Obsidian-Vault ist die Datenschicht,
diese Streamlit-App die Anzeigeschicht.

Projektnotiz im Vault: `03 Projekte (privat)/AI Command Center.md`.

## Start

```
.venv\Scripts\streamlit run app.py --server.port 8500
```

Dann http://localhost:8500 öffnen. (Port 8500, damit der Trading Agent auf 8501 frei bleibt.)

## Konfiguration

Der Vault-Pfad steht in `command_center/config.py` und ist per Umgebungsvariable
`VAULT_PATH` überschreibbar (z. B. für andere Geräte).

## Zugriff von Handy & Laptop (gleiches WLAN)

Das Dashboard läuft auf diesem Rechner und ist im Heimnetz erreichbar:

- **Adresse:** `http://<IP-dieses-Rechners>:8500` (Trading Agent: `:8501`).
  Die aktuelle Adresse steht im Dashboard-Footer.
- **Voraussetzungen** (alles eingerichtet, 02.07.2026):
  - Streamlit lauscht auf allen Interfaces (`address = "0.0.0.0"` in `.streamlit/config.toml`, bei beiden Dashboards)
  - Firewall-Regel „AI Dashboards (Streamlit 8500-8501)" — eingehend TCP 8500–8501, Profile Privat/Domäne
  - Links im Dashboard (Tool-Kacheln, Trading-CTA, iframe) werden automatisch von
    `localhost` auf die LAN-IP umgeschrieben (`command_center/config.py` → `external_url()`),
    sonst zeigen sie am Handy ins Leere
- **Android:** im Browser die Adresse öffnen → Menü → „Zum Startbildschirm hinzufügen".
  Dann verhält es sich wie eine App.
- **Tipp:** In der Fritzbox dem Rechner „immer die gleiche IPv4-Adresse zuweisen"
  aktivieren, sonst kann sich die IP nach einem Neustart ändern.
- Fester Hostname statt IP: Umgebungsvariable `DASHBOARD_HOST` setzen.
- Der PC muss dafür an sein (Autostart der Dashboards läuft beim Login).

## Stand

- [x] Schritt 1 — Gerüst + Projekte-Kachel + Forest/Lime-Design
- [x] Schritt 2 — Tool-Launcher, Skills, Kanban (md-Sync), Projekte nach Beruflich/Privat getrennt
- [x] Schritt 3 — Kalender (Google Calendar): verbunden, zeigt kommende Termine (read-only)
- [x] Schritt 4 — Token-Nutzung: lokale Claude-Code-Nutzung (Tokens/Tag, 7-Tage-Chart) + manuelles Free-Credit-Feld
- [x] Schritt 5 — Trading Agent eingehängt: Depot-Kurzübersicht (read-only aus dessen Daten) + Live-Einbettung per iframe + Launcher-Kachel
- [x] Schritt 6 — Design v2 (Ambient-Hintergrund, Animationen, Sticky-Topbar, Begrüßung) + Multi-Device: responsive CSS, LAN-Zugriff für Handy/Laptop
- [x] Schritt 7 — Kanban interaktiv: Karten per Drag & Drop verschieben (streamlit-sortables), schreibt direkt in `01 Inbox/Kanban.md` zurück (einzige Schreiboperation ins Vault; Frontmatter + Plugin-Settings bleiben erhalten)

## Gepatchte Kanban-Komponente (`streamlit_sortables/` im Projektordner)

Das Verzeichnis `streamlit_sortables/` ist eine **vendored, gepatchte Kopie**
des PyPI-Pakets `streamlit-sortables` 0.3.1. Sie liegt bewusst neben `app.py`
und schattet dadurch das pip-installierte Paket (Streamlit legt den
Skript-Ordner vorn auf den `sys.path`). **Nicht löschen** — sonst kommt der
Bug zurück:

- **Bug:** React error #185 („Maximum update depth exceeded") beim Drag & Drop,
  wenn eine Karte genau auf der Grenze zwischen zwei Spalten schwebt. dnd-kit
  flippt dann schnell zwischen den Spalten hin und her, jedes Flip ruft
  `setItems` in `onDragOver` auf → Endlosschleife → „Component Error" im Board.
  Bekanntes Upstream-Problem (dnd-kit issue #1678), kein Fix in
  streamlit-sortables ≤ 0.3.1.
- **Patch (11.07.2026):** Move-Lock in `onDragOver` — maximal ein
  Spaltenwechsel pro 150 ms, direkt im gebauten Bundle
  `frontend/build/static/js/main.4a88f4bb.js` (umbenannt von `…4a88f4ba.js`
  als Cache-Buster; `index.html`/`asset-manifest.json` angepasst). Außerdem
  Debug-`console.log`s entfernt.
- Bei einem künftigen Upstream-Release: neue Version testen und, falls dort
  gefixt, die vendored Kopie entfernen und `requirements.txt` anheben.

## Autostart (alle Dashboards beim Login)

- `start_dashboards.bat` — startet AI Command Center (8500) + Trading Agent (8501), sichtbar-minimiert. Für manuellen Start.
- `start_dashboards_hidden.vbs` — dasselbe komplett unsichtbar (für Autostart).
- `stop_dashboards.bat` — beendet beide Server.
- Autostart ist eingerichtet: Verknüpfung „AI Dashboards" im Windows-Startup-Ordner
  (`shell:startup`) zeigt auf die VBS. Entfernen = Verknüpfung dort löschen.
- Weiteres Dashboard ergänzen: in beiden Startdateien einen Block kopieren, Pfad + Port anpassen.

## Google Kalender einrichten

1. Google Cloud Console → neues Projekt, Google Calendar API aktivieren.
2. OAuth-Consent-Screen (External), eigenes Google-Konto als Test-User hinzufügen.
3. OAuth-Client-ID Typ „Desktop app" erstellen, JSON als `credentials.json` ins Projekt legen.
4. `.venv\Scripts\python setup_calendar.py` ausführen → Browser-Consent → `token.json` entsteht.
5. Dashboard neu laden: kommende Termine erscheinen. (`credentials.json`/`token.json` sind gitignored.)

## Datenquellen

- Projekte: `02 Projekte/` + `03 Projekte (privat)/` (Frontmatter)
- Skills: `00 Kontext/Skills.md` (Format `- Name :: Level`)
- Kanban: `01 Inbox/Kanban.md` (Obsidian-Kanban-Format, single source of truth) —
  **read/write**: Drag & Drop im Dashboard schreibt die Datei um; Karten in der
  Erledigt-Spalte werden `- [x]`, alle anderen `- [ ]`
- Tools: `tools.toml` (im Projekt, für den Launcher)
- Scanner-Ablage: `..\..\scan-workflow\scan_log.csv` (Geschwister-Repo, read-only) —
  Bewegungs-Logbuch des Scanner-Workflows, Section „Zuletzt einsortiert" zeigt die
  letzten 10 Einträge. Pfad per `SCAN_LOG_PATH` überschreibbar, Anzahl per
  `SCAN_LOG_LIMIT`. Fehlt die Datei, erscheint ein Hinweis-Platzhalter.
  Dateiname und Zielordner sind Links in Google Drive (neuer Tab, auch am Handy).
  Die Drive-IDs kommen read-only aus der lokalen DB von Drive für Desktop
  (`%LOCALAPPDATA%\Google\DriveFS\*\metadata_sqlite_db`). Liegt eine Datei nicht
  mehr am geloggten Pfad (später umbenannt/verschoben), fehlt nur ihr Link.

## Architektur

```
app.py                 Streamlit-UI (Sections)
tools.toml             Tool-Launcher-Kacheln
command_center/
  config.py            Vault-Pfad, Datenquellen, Pfade
  theme.py             Forest/Lime Design-System (CSS)
  vault.py             Reader: Projekte, Skills, Kanban, Tools
  calendar_google.py   Google-Kalender (read-only)
  usage.py             Token-Nutzung (Claude-Code-Logs) + Free-Credit
  trading.py           Trading-Agent-Depot (read-only aus dessen Daten)
  github.py            Repo-Übersicht über die gh CLI
  repo_sync.py         git pull für die lokalen Klone
  scan_log.py          Scanner-Bewegungslog (read-only aus scan-workflow)
  drive_links.py       Drive-Pfad → Google-Drive-Link (read-only, DriveFS-DB)
```
Alle Reader sind Streamlit-frei und fangen fehlende Quellen sauber ab.
