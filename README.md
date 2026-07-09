# Dashboard — AI Command Center & Server

Monorepo mit allen persönlichen Dashboard-Servern von Leo. Ein `git clone` +
`setup.ps1` reicht, um alles auf einem neuen Windows-Laptop zu starten.

| Projekt | Port | Stack | Zweck |
|---|---|---|---|
| [ai-command-center](ai-command-center/) | 8500 | Streamlit | Top-Level-Dashboard: Projekte, Skills, Kanban, Token-Nutzung, Kalender, Depot, Repos |
| [trading-agent](trading-agent/) | 8501 | Streamlit | Depot-Dashboard: Charts, Signale, Backtests, Order Sheet |
| [basel-ai-landing](basel-ai-landing/) | 8502 | Python stdlib | Statischer Server: Landing Page, Kurs-Katalog, Unterrichts-Repos (/gdp, /datb) |
| [basel-ai-buchung](basel-ai-buchung/) | 8505 | FastAPI | Buchungskalender Basel-AI (Google Calendar, freie Slots + Buchung) |

## Voraussetzungen

- **Windows** mit **Python 3.11+** (entwickelt mit 3.13) und Git
- **gh CLI** eingeloggt (`gh auth login`) — nur für die Repo-Kacheln im Command Center
- **Geschwister-Repos** neben diesem Repo geklont (gleicher Parent-Ordner, z. B. `C:\Users\<du>\repos\`):
  - `SecondBrain-Leo` (Obsidian-Vault = Datenschicht: Projekte, Skills, Kanban, Basel-AI-Seiten)
  - `2526_KI1_GdP_C` und `2526_KI1_DatB` (Unterrichts-Repos für /gdp und /datb)

Liegen die Repos woanders, Pfade per Env-Variable setzen (siehe unten).

## Schnellstart (neuer Laptop)

```powershell
cd C:\Users\<du>\repos
git clone https://github.com/sternlb/dashboard
git clone https://github.com/sternlb/SecondBrain-Leo
git clone https://github.com/sternlb/2526_KI1_GdP_C
git clone https://github.com/sternlb/2526_KI1_DatB

cd dashboard
powershell -ExecutionPolicy Bypass -File setup.ps1   # venvs + pip install
# Secrets kopieren (siehe unten), dann:
start_dashboards.bat
```

Stoppen: `stop_dashboards.bat` (killt alle Prozesse auf den Ports 8500/8501/8502/8505).

## Secrets (gitignored — pro Rechner beschaffen)

| Datei | Wofür | Beschaffung |
|---|---|---|
| `ai-command-center\credentials.json` | Google-Kalender (read-only) | Vom Haupt-PC kopieren, oder eigenen OAuth-Client (Desktop app) in der Google Cloud Console anlegen |
| `ai-command-center\token.json` | dito | Einmalig `.venv\Scripts\python setup_calendar.py` ausführen (OAuth-Consent im Browser) |
| `basel-ai-buchung\credentials.json` + `token.json` | Buchungskalender (Schreibzugriff!) | Wie oben; `setup_calendar.py` liegt im Projektordner |
| `ai-command-center\token_state.json` | Manuelle Token-Caps / Free-Credit-Rest | Entsteht beim Editieren im Dashboard; ohne Datei nur Beispielwerte |
| `trading-agent\data\holdings.csv` | Echtes Depot | Vom Haupt-PC kopieren; Format siehe `data\holdings.example.csv` |

**Diese Dateien niemals committen.** Root-`.gitignore` deckt sie ab — vor jedem
Push mit `git status` gegenprüfen.

## Env-Overrides (optional)

| Variable | Default | Bedeutung |
|---|---|---|
| `VAULT_PATH` | `..\SecondBrain-Leo` (Geschwister) | Obsidian-Vault (Command Center) |
| `VAULT_NAME` | `SecondBrain-Leo` | Vault-Name für obsidian://-Links |
| `TRADING_AGENT_DIR` | `.\trading-agent` (Geschwister-Projekt) | Depot-Daten fürs Command Center |
| `TRADING_URL` | `http://localhost:8501` | Trading-Agent-URL (iframe/CTA) |
| `BASEL_AI_DIR` | `..\SecondBrain-Leo\03 Projekte (privat)\Basel-AI Consulting` | Quellordner der Landing Page |
| `GDP_DIR` / `DATB_DIR` | `..\2526_KI1_GdP_C` / `..\2526_KI1_DatB` | Unterrichts-Repos für /gdp, /datb |
| `DASHBOARD_HOST` | LAN-IP (auto) | Host für Links auf andere Geräte |
| `CLAUDE_PROJECTS_DIR` | `~\.claude\projects` | Claude-Code-Logs (Token-Sektion) |

## Autostart (Windows-Login)

Verknüpfung im Startup-Ordner anlegen: `Win+R` → `shell:startup` → Verknüpfung
auf `start_dashboards_hidden.vbs` (startet alle vier Server unsichtbar).

## Zugriff im WLAN (Handy/Laptop)

Die Server binden auf `0.0.0.0`. Firewall-Regel für eingehend TCP nötig, z. B.:

```
netsh advfirewall firewall add rule name="AI Dashboards" dir=in action=allow protocol=TCP localport=8500-8502,8505 profile=private,domain
```

(Auf dem Haupt-PC existiert die Regel bereits für 8500–8502 — **8505 ggf. ergänzen**.)
Adresse am Handy: `http://<PC-IP>:8500` — steht auch im Dashboard-Footer.
