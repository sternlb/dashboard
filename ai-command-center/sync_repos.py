"""CLI-Wrapper für den Repo-Sync — wird von den Startskripten aufgerufen.

Pullt alle repos.toml-Einträge mit sync = true (Unterrichts-Repos + Vault),
damit die Sub-Pages (/gdp, /datb) und die Vault-Inhalte beim Start aktuell
sind. Braucht nur die stdlib, kein venv: python sync_repos.py
"""
import sys

from command_center.repo_sync import main

if __name__ == "__main__":
    sys.exit(main())
