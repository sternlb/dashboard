#!/usr/bin/env bash
# ==============================================================================
#  Leo Dashboards — Add-on-Entrypoint
#
#  Holt den App-Code zur Laufzeit per git (nicht ins Image gebacken), damit ein
#  "auf Windows pushen -> Add-on neu starten" reicht. Nur Änderungen an
#  requirements.txt erfordern einen Versions-Bump + Image-Rebuild.
#
#  Startet drei Prozesse und beendet sich, sobald einer stirbt — der Supervisor
#  startet das Add-on dann neu (boot: auto + watchdog auf 8500).
# ==============================================================================
set -o pipefail

OPTIONS=/data/options.json
REPOS=/share/repos
VENV=/opt/venv
PY="${VENV}/bin/python"

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
fail() { echo "[$(date '+%H:%M:%S')] FEHLER: $*" >&2; exit 1; }
opt()  { jq -r --arg k "$1" '.[$k] // empty' "$OPTIONS" 2>/dev/null; }

# --- Optionen ---------------------------------------------------------------
DASHBOARD_HOST=$(opt dashboard_host)
GITHUB_OWNER=$(opt github_owner)
GITHUB_TOKEN=$(opt github_token)
VAULT_WRITEBACK=$(opt vault_writeback)
GIT_USER_NAME=$(opt git_user_name)
GIT_USER_EMAIL=$(opt git_user_email)

[ -n "$DASHBOARD_HOST" ] || fail "Option 'dashboard_host' ist leer. Ohne sie ermittelt config.py die Docker-Bridge-IP (172.30.x.x) und alle Kachel-Links zeigen ins Leere. Trage die LAN-IP des HA-Hosts ein, z. B. 192.168.178.50."
[ -n "$GITHUB_TOKEN" ]   || fail "Option 'github_token' ist leer. Die Repos sind privat und lassen sich ohne Token nicht klonen."

# --- Git-Setup --------------------------------------------------------------
# HA-Add-on-Container setzen $HOME nicht (init: false). Ohne HOME brechen alle
# git-config-Aufrufe mit "fatal: $HOME not set" ab, der credential.helper wird
# nie gesetzt und private Repos scheitern mit "could not read Username".
# Betrifft ausserdem ~/.streamlit und ~/.config/gh.
export HOME=/root
mkdir -p "$HOME"

# credential.helper store statt Token in der Remote-URL: sonst landet das Token
# dauerhaft in .git/config unter /share.
printf 'https://x-access-token:%s@github.com\n' "$GITHUB_TOKEN" > "$HOME/.git-credentials"
chmod 600 "$HOME/.git-credentials"
git config --global credential.helper store
git config --global user.name  "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
# /share gehört einer anderen UID -> git verweigert sonst mit "dubious ownership".
git config --global --add safe.directory '*'

# gh CLI authentifiziert sich über die Umgebung, kein interaktives gh auth login.
export GH_TOKEN="$GITHUB_TOKEN"

# --- Repos holen ------------------------------------------------------------
mkdir -p "$REPOS"

# Sagt bei einem fehlgeschlagenen Clone, woran es wirklich liegt. GitHub
# antwortet auf einen Clone ohne Repo-Zugriff mit "Write access to repository
# not granted" — das klingt nach fehlendem Schreibrecht, meint aber meistens,
# dass das Repo gar nicht in der Repository-Auswahl des Tokens steht.
diagnose_token() {
    local who code
    log "Token-Diagnose:"
    who=$(curl -sS -H "Authorization: Bearer ${GITHUB_TOKEN}" \
          https://api.github.com/user 2>/dev/null | jq -r '.login // "unbekannt"')
    log "  Token gehoert zum Konto: ${who}"
    for r in dashboard SecondBrain-Leo 2526_KI1_GdP_C 2526_KI1_DatB; do
        code=$(curl -sS -o /dev/null -w '%{http_code}' \
               -H "Authorization: Bearer ${GITHUB_TOKEN}" \
               "https://api.github.com/repos/${GITHUB_OWNER}/${r}" 2>/dev/null)
        log "  ${r}: HTTP ${code}"
    done
    log "  200 = ok | 404 = Repo steht nicht in der Repository-Auswahl des Tokens"
    log "  403 = Repository permissions zu niedrig | 401 = Token ungueltig/zurueckgezogen"
}

sync_repo() {
    local name="$1" dir="${REPOS}/$1"
    if [ -d "${dir}/.git" ]; then
        log "pull  ${name}"
        if ! git -C "$dir" pull --ff-only 2>&1 | sed 's/^/        /'; then
            log "WARN  ${name}: pull fehlgeschlagen, arbeite mit lokalem Stand weiter"
        fi
    else
        log "clone ${name}"
        if ! git clone "https://github.com/${GITHUB_OWNER}/${name}.git" "$dir" 2>&1 | sed 's/^/        /'; then
            diagnose_token
            fail "${name} konnte nicht geklont werden — siehe Token-Diagnose oben."
        fi
    fi
}

sync_repo dashboard
sync_repo SecondBrain-Leo
sync_repo 2526_KI1_GdP_C
sync_repo 2526_KI1_DatB

DASH="${REPOS}/dashboard"
CC="${DASH}/ai-command-center"
TA="${DASH}/trading-agent"
LP="${DASH}/basel-ai-landing"

# --- Secrets aus /share uebernehmen (Erstbefuellung) ------------------------
# Das /data dieses Add-ons ist von aussen nicht erreichbar: das SSH-Add-on
# laeuft im Protection Mode und bekommt /mnt/data nicht gemountet. Deshalb
# duerfen die Secrets nach /share/leo-dashboards gelegt werden. Hier werden sie
# einmalig nach /data verschoben und aus /share entfernt — /share ist fuer jedes
# Add-on lesbar, dort haben sie dauerhaft nichts verloren.
INBOX=/share/leo-dashboards
for f in credentials.json token.json token_state.json holdings.csv; do
    [ -f "${INBOX}/${f}" ] || continue
    if mv "${INBOX}/${f}" "/data/${f}"; then
        chmod 600 "/data/${f}"
        log "Secret uebernommen: ${f} (aus ${INBOX} entfernt)"
    else
        log "WARN  ${f} konnte nicht nach /data uebernommen werden"
    fi
done

# --- Secrets aus /data verlinken --------------------------------------------
# /data ist persistent und liegt im HA-Backup; die Dateien sind gitignored,
# die Repo-Arbeitskopie bleibt dadurch sauber (wichtig für repo_sync).
link_secret() {
    local src="/data/$1" dst="$2"
    if [ -f "$src" ]; then
        mkdir -p "$(dirname "$dst")"
        ln -sf "$src" "$dst"
    else
        log "WARN  /data/$1 fehlt — abhängige Kachel bleibt leer"
    fi
}

link_secret credentials.json "${CC}/credentials.json"
link_secret token.json       "${CC}/token.json"
link_secret token_state.json "${CC}/token_state.json"
link_secret holdings.csv     "${TA}/data/holdings.csv"

# --- Drift-Sicherung --------------------------------------------------------
# Die Deps stecken im Image. Falls eine App-requirements.txt seit dem letzten
# Image-Build gewachsen ist, hier nachziehen statt beim Import abzustürzen.
for req in "${CC}/requirements.txt" "${TA}/requirements.txt"; do
    [ -f "$req" ] || continue
    "${VENV}/bin/pip" install --quiet --disable-pip-version-check -r "$req" 2>&1 | sed 's/^/        /' \
        || log "WARN  pip-Nachinstallation aus ${req} fehlgeschlagen"
done

# --- Umgebung für die Apps --------------------------------------------------
export DASHBOARD_HOST                      # sonst Docker-Bridge-IP in allen Links
export VAULT_PATH="${REPOS}/SecondBrain-Leo"
export TRADING_AGENT_DIR="${TA}"
export TRADING_URL="http://${DASHBOARD_HOST}:8501"
# Von Windows gespiegelt (siehe DOCS.md); fehlen sie, bleiben die Kacheln leer.
export CLAUDE_PROJECTS_DIR=/share/claude-logs
export SCAN_LOG_PATH=/share/scan/scan_log.csv
# Kanban-Rückschreiben. AUTOCOMMIT ist auf dem Dev-PC aus und hier an: ohne
# commit+push bliebe dieser Klon dirty und repo_sync würde ihn ab dem ersten
# Kanban-Klick dauerhaft überspringen.
export VAULT_WRITEBACK="${VAULT_WRITEBACK}"
export VAULT_AUTOCOMMIT="${VAULT_WRITEBACK}"

log "Host ${DASHBOARD_HOST} · Vault ${VAULT_PATH} · Writeback ${VAULT_WRITEBACK}"

# --- Dienste starten --------------------------------------------------------
declare -a PIDS=()

log "start Landing Page      :8502"
( cd "$LP" && exec "$PY" app.py ) &
PIDS+=($!)

log "start Trading Agent     :8501"
( cd "$TA" && exec "${VENV}/bin/streamlit" run app.py \
    --server.port 8501 --server.address 0.0.0.0 --server.headless true ) &
PIDS+=($!)

log "start AI Command Center :8500"
( cd "$CC" && exec "${VENV}/bin/streamlit" run app.py \
    --server.port 8500 --server.address 0.0.0.0 --server.headless true ) &
PIDS+=($!)

# Ersetzt den Windows-Task "TradingAgent_WatchlistUpdate" (montags 09:00).
# Marker in /data macht den Lauf idempotent über Neustarts hinweg.
watchlist_loop() {
    while true; do
        if [ "$(date +%u)" = "1" ] && [ "$(date +%H)" = "09" ]; then
            local marker="/data/.watchlist-$(date +%F)"
            if [ ! -f "$marker" ]; then
                log "Watchlist-Update"
                ( cd "$TA" && "$PY" update_watchlist.py ) && touch "$marker"
            fi
        fi
        sleep 600
    done
}
watchlist_loop &
PIDS+=($!)

cleanup() {
    log "stoppe Dienste"
    kill "${PIDS[@]}" 2>/dev/null
    wait 2>/dev/null
}
trap cleanup EXIT INT TERM

log "alle Dienste laufen"

# Sobald ein Dienst stirbt, geht das ganze Add-on runter — der Supervisor
# startet es neu. Besser ein sichtbarer Neustart als ein stilles Teil-Dashboard.
wait -n "${PIDS[@]}"
fail "ein Dienst hat sich beendet — Add-on wird neu gestartet"
