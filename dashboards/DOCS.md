# Leo Dashboards

Fährt die drei privaten Dashboards im Dauerbetrieb auf dem HA-Host, damit sie
nicht mehr am eingeschalteten Windows-PC hängen.

| Port | Dashboard |
|---|---|
| 8500 | AI Command Center |
| 8501 | Trading Agent |
| 8502 | Landing Page, Kurs-Katalog, `/gdp/`, `/datb/` |

Erreichbar unter `http://<HA-Host-IP>:<Port>` — kein Ingress, kein Sidebar-Eintrag.

## Wie es arbeitet

Der App-Code steckt **nicht** im Image. Beim Start klont bzw. pullt das Add-on
vier Repos nach `/share/repos`:

```
/share/repos/
├── dashboard/          App-Code
├── SecondBrain-Leo/    Vault = Datenschicht
├── 2526_KI1_GdP_C/     für /gdp/
└── 2526_KI1_DatB/      für /datb/
```

Die Apps erwarten genau dieses Geschwister-Layout (`config.py` leitet
`REPOS_ROOT` daraus ab) — deshalb sind dafür keine Env-Variablen nötig.

**Code ändern:** auf dem PC committen und pushen, dann das Add-on neu starten.
Kein Image-Rebuild.
**`requirements.txt` ändern:** zusätzlich `dashboards/requirements.txt` pflegen
und die Version in `config.yaml` hochzählen.

## Optionen

| Option | Bedeutung |
|---|---|
| `dashboard_host` | **Pflicht.** LAN-IP des HA-Hosts, z. B. `192.168.178.50`. Ohne sie ermittelt `config.py` die Docker-Bridge-IP (`172.30.x.x`) und schreibt damit *alle* Kachel-Links kaputt. |
| `github_owner` | GitHub-Account (`sternlb`) |
| `github_token` | Fine-grained PAT. `Contents: read` auf `dashboard`, `2526_KI1_GdP_C`, `2526_KI1_DatB`; auf `SecondBrain-Leo` `Contents: write`, falls `vault_writeback` an ist. Dient gleichzeitig als `GH_TOKEN` für die Repo-Kacheln. |
| `vault_writeback` | `true` = Kanban-Drag&Drop schreibt in den Vault und pusht. `false` = Kanban nur lesen, dann genügt ein Read-Token. |
| `git_user_name` / `git_user_email` | Autor der Kanban-Commits |

## Einmalige Einrichtung

### 1. Secrets nach `/data`

Diese Dateien sind gitignored und müssen einmalig vom PC kopiert werden — per
Advanced SSH & Web Terminal Add-on nach `/addon_configs/…` bzw. direkt ins
`/data` des Add-ons:

| Datei | Wofür |
|---|---|
| `credentials.json` | Google-Kalender (read-only) |
| `token.json` | dito, entsteht durch `setup_calendar.py` |
| `token_state.json` | manuelle Token-Caps; wird vom Dashboard beschrieben |
| `holdings.csv` | echtes Depot des Trading Agent |

Fehlt eine Datei, startet das Add-on trotzdem — die betroffene Kachel bleibt leer
und es steht eine `WARN`-Zeile im Log.

### 2. Windows-Sync für zwei Kacheln

Zwei Datenquellen entstehen weiterhin auf dem PC und werden nicht mitgeklont:

- **Token-Nutzung** liest die Claude-Code-Logs aus `~/.claude/projects`
- **Scanner-Logbuch** liest `scan-workflow/scan_log.csv` (läuft mit lokalem Ollama)

Geplanter Task auf Windows, der beides nächtlich zum Pi spiegelt:

```bash
scp -r "$HOME/.claude/projects/." root@<HA-Host-IP>:/share/claude-logs/ && scp "$HOME/repos/scan-workflow/scan_log.csv" root@<HA-Host-IP>:/share/scan/scan_log.csv
```

Ohne diesen Job bleiben nur diese beiden Kacheln leer, alles andere läuft.

## Abnahme

1. Add-on-Log: `alle Dienste laufen`, keine `WARN`-Zeilen.
2. Vom Handy im WLAN alle drei Ports öffnen.
3. Eine Kachel im Command Center anklicken — die Ziel-URL muss die LAN-IP
   enthalten, **nicht** `172.30.x.x`.
4. Kanban-Karte verschieben, danach auf dem PC `git pull` im Vault: Änderung da?
5. HA neu starten — alle drei Dashboards kommen ohne Handgriff wieder.
