"""Zentrale Konfiguration: wo liegt das Vault, welche Ordner sind Projekte."""
from __future__ import annotations

import os
import socket
from pathlib import Path


# --- Multi-Device: LAN-IP statt localhost -------------------------------------
# Vom Handy/Laptop aus zeigt "localhost" auf das falsche Gerät. Deshalb ermitteln
# wir die LAN-IP dieses Rechners und schreiben sie in alle lokalen Links um.
# Per Umgebungsvariable DASHBOARD_HOST überschreibbar (z. B. fester Hostname).
def _lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # kein Traffic — nur Routing-Lookup
        return s.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        s.close()


LAN_IP = os.environ.get("DASHBOARD_HOST") or _lan_ip()


def external_url(url: str) -> str:
    """Lokale URL so umschreiben, dass sie auch von anderen Geräten erreichbar ist."""
    return (url or "").replace("localhost", LAN_IP).replace("127.0.0.1", LAN_IP)

# Dieses Projekt liegt im Monorepo …\repos\dashboard\ai-command-center.
# Vault und andere Repos werden als Geschwister von "dashboard" erwartet.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_REPOS_ROOT = _PROJECT_ROOT.parent.parent

# Pfad zum Obsidian-Vault. Per Umgebungsvariable VAULT_PATH überschreibbar,
# damit die App auch von anderen Geräten aus läuft.
# Seit Juli 2026 liegt das Vault lokal (Git-Repo), nicht mehr im Schul-OneDrive.
_DEFAULT_VAULT = _REPOS_ROOT / "SecondBrain-Leo"

VAULT_PATH = Path(os.environ.get("VAULT_PATH", _DEFAULT_VAULT))

# Name des Vaults für obsidian:// Deep-Links (= Vault-Ordnername).
VAULT_NAME = os.environ.get("VAULT_NAME", "SecondBrain-Leo")

# Projekt-Quellen: (Unterordner im Vault, Kategorie-Label).
PROJEKT_DIRS = [
    ("02 Projekte", "Beruflich"),
    ("03 Projekte (privat)", "Privat"),
]

# Weitere Datenquellen im Vault.
SKILLS_FILE = VAULT_PATH / "00 Kontext" / "Skills.md"
KANBAN_FILE = VAULT_PATH / "01 Inbox" / "Kanban.md"

# Tool-Launcher-Definition (liegt im Projekt, nicht im Vault).
TOOLS_FILE = _PROJECT_ROOT / "tools.toml"

# GitHub-Repo-Übersicht: welche Repos das Dashboard zeigt (via gh CLI).
REPOS_FILE = _PROJECT_ROOT / "repos.toml"

# --- Google Calendar ---------------------------------------------------------
# OAuth-Dateien (gitignored). credentials.json legt Leo aus der Google Cloud
# Console ab; token.json entsteht beim einmaligen setup_calendar.py.
GCAL_CREDENTIALS_FILE = _PROJECT_ROOT / "credentials.json"
GCAL_TOKEN_FILE = _PROJECT_ROOT / "token.json"
GCAL_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
GCAL_CALENDAR_ID = os.environ.get("GCAL_CALENDAR_ID", "primary")
GCAL_MAX_EVENTS = int(os.environ.get("GCAL_MAX_EVENTS", "8"))

# --- Token-Nutzung -----------------------------------------------------------
# Lokale Claude-Code-Session-Logs (JSONL).
CLAUDE_PROJECTS_DIR = Path(
    os.environ.get("CLAUDE_PROJECTS_DIR", str(Path.home() / ".claude" / "projects"))
)
# Manueller Free-Credit-Rest (gitignored) — Anthropic bietet keinen Balance-API.
TOKEN_STATE_FILE = _PROJECT_ROOT / "token_state.json"

# --- Trading Agent (eingehängtes Fachdashboard) ------------------------------
# Geschwister-Projekt im selben Monorepo (…\dashboard\trading-agent).
TRADING_AGENT_DIR = Path(
    os.environ.get("TRADING_AGENT_DIR", _PROJECT_ROOT.parent / "trading-agent")
)
TRADING_URL = external_url(os.environ.get("TRADING_URL", "http://localhost:8501"))

