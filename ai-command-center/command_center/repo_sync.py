"""Repo-Sync — zieht lokale Geschwister-Repos per git pull auf GitHub-Stand.

Welche Repos gepullt werden, steht in repos.toml (Einträge mit sync = true).
Der lokale Pfad wird als Geschwister-Ordner des Monorepos abgeleitet
(…\\repos\\<name>), wie in config.py. Sicherheitsregeln: Repos mit lokalen
Änderungen werden übersprungen, kein --force, Konflikte werden nur gemeldet.

Läuft ohne Streamlit (nur stdlib) — auch als CLI über sync_repos.py im
Projekt-Root, damit die Startskripte vor dem Serverstart pullen können.
"""
from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .config import REPOS_FILE, REPOS_ROOT

_GIT_TIMEOUT = 60


@dataclass
class SyncResult:
    name: str
    label: str = ""
    icon: str = "📦"
    state: str = "ok"   # updated | up_to_date | skipped_dirty | missing | error
    detail: str = ""


def _git(path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=_GIT_TIMEOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _load_sync_entries(path: Path) -> list[dict]:
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return [cfg for cfg in data.get("repo", []) if cfg.get("sync") is True]


def _sync_one(cfg: dict) -> SyncResult:
    res = SyncResult(
        name=str(cfg.get("name", "")).strip(),
        label=str(cfg.get("label", cfg.get("name", ""))),
        icon=str(cfg.get("icon", "📦")),
    )
    local = REPOS_ROOT / res.name
    if not (local / ".git").exists():
        res.state, res.detail = "missing", f"kein lokaler Klon unter {local}"
        return res

    # Nur getrackte Änderungen blockieren den Pull. Untracked Dateien sind
    # harmlos — git bricht selbst ab, falls eine eingehende Datei kollidiert.
    status = _git(local, "status", "--porcelain", "--untracked-files=no")
    if status.returncode != 0:
        res.state, res.detail = "error", (status.stderr or "git status fehlgeschlagen").strip()[:160]
        return res
    if status.stdout.strip():
        res.state, res.detail = "skipped_dirty", "lokale Änderungen — nicht gepullt"
        return res

    before = _git(local, "rev-parse", "HEAD").stdout.strip()
    pull = _git(local, "pull", "--rebase", "origin")
    if pull.returncode != 0:
        res.state, res.detail = "error", (pull.stderr or "git pull fehlgeschlagen").strip()[:160]
        return res
    after = _git(local, "rev-parse", "HEAD").stdout.strip()

    if before and after and before != after:
        count = _git(local, "rev-list", "--count", f"{before}..{after}").stdout.strip()
        res.state = "updated"
        res.detail = f"{count} neue Commits" if count else "aktualisiert"
    else:
        res.state, res.detail = "up_to_date", "bereits aktuell"
    return res


def sync_repos(path: Path | None = None) -> list[SyncResult]:
    path = path or REPOS_FILE
    if not path.exists():
        return [SyncResult(name="repos.toml", state="error", detail=f"{path} fehlt")]
    try:
        entries = _load_sync_entries(path)
    except (tomllib.TOMLDecodeError, OSError) as e:
        return [SyncResult(name="repos.toml", state="error", detail=str(e)[:160])]
    if not entries:
        return [SyncResult(name="repos.toml", state="error", detail="kein Eintrag mit sync = true")]

    results: list[SyncResult] = []
    for cfg in entries:
        try:
            results.append(_sync_one(cfg))
        except FileNotFoundError:
            results.append(SyncResult(
                name=str(cfg.get("name", "?")), state="error", detail="git nicht gefunden",
            ))
        except subprocess.TimeoutExpired:
            results.append(SyncResult(
                name=str(cfg.get("name", "?")), state="error",
                detail=f"Timeout nach {_GIT_TIMEOUT}s (GitHub erreichbar?)",
            ))
    return results


def main() -> int:
    print("Repo-Sync: hole Stand von GitHub ...")
    results = sync_repos()
    for r in results:
        print(f"  [{r.state:13s}] {r.name}: {r.detail}")
    # Fehler nie als Startblocker werten — die Dashboards sollen trotzdem starten.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
