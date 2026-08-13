# Changelog

Versionshistorie des Add-ons **Leo Dashboards**. Diese Datei liegt bewusst neben
der `config.yaml` im Add-on-Ordner — genau dort sucht der Supervisor sie und
zeigt sie im Update-Dialog an. Ohne sie meldet Home Assistant
„No changelog found for app …_leo_dashboards!".

## 0.1.4

**Die Aufruf-Adressen stehen jetzt im Add-on-Store.**

- Die Beschreibung im Store nennt die drei Links direkt:
  `http://192.168.178.150:8500` (AI Command Center), `:8501` (Trading Agent),
  `:8502` (Landing Page / Kurs-Katalog / `/gdp/` / `/datb/`). Bisher musste man
  in DOCS.md nachsehen, welcher Port zu welchem Dashboard gehört.
- Die IP ist fest eingetragen, weil die Store-Beschreibung keine Add-on-Optionen
  auflösen kann — sie zeigt auf den Pi aus der Heim-Infrastruktur. Wandert der
  HA-Host, muss sie hier mitwandern (die Option `dashboard_host` bleibt davon
  unberührt, sie steuert weiterhin die Kachel-Links *innerhalb* der Dashboards).
- Diese Datei ist neu: ab jetzt zeigt Home Assistant beim Update, was sich
  geändert hat. Kein Code-Update, kein Image-Rebuild.

## 0.1.3

- `curl` ins Image geholt (Healthcheck bzw. Diagnose im Container).
- Bessere Fehlermeldung, wenn der Clone am GitHub-Token scheitert: das Add-on
  sagt jetzt, *welches* Repo mit welchem Grund abgelehnt wurde, statt nur
  „could not read Username".

## 0.1.2

- **Secrets über `/share` einschleusen.** Das `/data` des Add-ons ist von außen
  nicht erreichbar (SSH-Add-on im Protection Mode). `run.sh` übernimmt
  `credentials.json`, `token.json` und `holdings.csv` beim Start aus
  `/share/leo-dashboards` nach `/data` und **löscht sie in `/share`** — dort ist
  alles für jedes andere Add-on lesbar.

## 0.1.1

- **`HOME` gesetzt.** Add-on-Container mit `init: false` setzen `$HOME` nicht;
  alle `git config`-Aufrufe brachen mit „fatal: $HOME not set" ab, der
  `credential.helper` wurde nie gesetzt und die drei privaten Repos ließen sich
  nicht klonen. Betrifft außer git auch `~/.streamlit` und `~/.config/gh`.
- Persönliche Werte aus dem öffentlichen Repo genommen (Beispiel-IP,
  `git_user_email`) — beide setzt Leo ohnehin in den Add-on-Optionen.

## 0.1.0

**Erste Version: die drei privaten Dashboards laufen im Dauerbetrieb auf dem Pi.**

- Ein Add-on für alle drei Apps statt drei einzelner — gemeinsamer Lebenszyklus,
  ein `git pull`, eine Version.
- Ports 8500/8501/8502 direkt am Host, **kein Ingress** (Streamlit unter dem
  zufälligen Ingress-Sub-Pfad ist wegen Websockets + `baseUrlPath` fragil).
- `boot: auto` und Watchdog auf Port 8500: fällt das Command Center aus, startet
  der Supervisor das Add-on neu.
- Der App-Code steckt **nicht** im Image, sondern wird beim Start nach
  `/share/repos` geklont — „auf dem PC pushen, Add-on neu starten" genügt.
