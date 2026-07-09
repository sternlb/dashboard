"""GitHub-Repo-Übersicht — Metadaten über die gh CLI (read-only).

Welche Repos gezeigt werden, steht in repos.toml (Projekt-Root). Die Daten
kommen aus einem einzigen `gh repo list`-Aufruf (authentifiziert über die
lokal eingerichtete GitHub CLI) — kein eigenes Token, kein Web-Scraping.
"""
from __future__ import annotations

import json
import subprocess
import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import REPOS_FILE

_GH_FIELDS = "name,description,visibility,pushedAt,url,primaryLanguage"


@dataclass
class Repo:
    name: str
    label: str = ""
    icon: str = "📦"
    url: str = ""
    description: str = ""
    visibility: str = ""
    language: str = ""
    pushed_at: datetime | None = None


@dataclass
class RepoResult:
    state: str = "ok"   # ok | no_config | no_gh | error
    detail: str = ""
    repos: list[Repo] = field(default_factory=list)


def _load_config(path: Path) -> tuple[str, list[dict]]:
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return str(data.get("owner", "")), list(data.get("repo", []))


def _gh_repo_list(owner: str) -> list[dict]:
    proc = subprocess.run(
        ["gh", "repo", "list", owner, "--limit", "100", "--json", _GH_FIELDS],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "gh repo list fehlgeschlagen").strip())
    return json.loads(proc.stdout or "[]")


def load_repos(path: Path | None = None) -> RepoResult:
    path = path or REPOS_FILE
    if not path.exists():
        return RepoResult(state="no_config", detail=f"{path.name} fehlt")
    try:
        owner, wanted = _load_config(path)
    except (tomllib.TOMLDecodeError, OSError) as e:
        return RepoResult(state="error", detail=f"repos.toml: {e}")
    if not owner or not wanted:
        return RepoResult(state="no_config", detail="owner/repo-Einträge fehlen")

    try:
        listed = {r["name"]: r for r in _gh_repo_list(owner)}
    except FileNotFoundError:
        return RepoResult(state="no_gh", detail="GitHub CLI (gh) nicht gefunden")
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return RepoResult(state="error", detail=str(e))

    repos: list[Repo] = []
    for cfg in wanted:
        name = str(cfg.get("name", "")).strip()
        if not name:
            continue
        meta = listed.get(name, {})
        pushed = None
        try:
            pushed = datetime.fromisoformat(
                str(meta.get("pushedAt", "")).replace("Z", "+00:00")
            ).astimezone()
        except (ValueError, TypeError):
            pass
        repos.append(
            Repo(
                name=name,
                label=str(cfg.get("label", name)),
                icon=str(cfg.get("icon", "📦")),
                url=str(meta.get("url", f"https://github.com/{owner}/{name}")),
                description=str(meta.get("description", "") or ""),
                visibility=str(meta.get("visibility", "") or "").lower(),
                language=str((meta.get("primaryLanguage") or {}).get("name", "") or ""),
                pushed_at=pushed,
            )
        )
    return RepoResult(repos=repos)
