"""Liest Projekte aus dem Obsidian-Vault (read-only) über das YAML-Frontmatter."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import frontmatter

from .config import (
    KANBAN_FILE,
    PROJEKT_DIRS,
    SKILLS_FILE,
    TOOLS_FILE,
    VAULT_AUTOCOMMIT,
    VAULT_NAME,
    VAULT_PATH,
    VAULT_WRITEBACK,
)
from .repo_sync import commit_and_push


@dataclass
class Project:
    name: str
    category: str                      # "Beruflich" / "Privat"
    status: str | None = None          # aus Frontmatter: aktiv / pausiert / abgeschlossen ...
    tags: list[str] = field(default_factory=list)
    updated: str | None = None         # aus "aktualisiert" oder "date"
    rel_path: str | None = None        # Pfad relativ zum Vault (für obsidian:// Link)
    is_folder: bool = False            # True = Ordner-Projekt (z. B. Unterrichtsreihe)

    @property
    def status_norm(self) -> str:
        return (self.status or "unbekannt").strip().lower()

    @property
    def obsidian_url(self) -> str | None:
        """Deep-Link, der die Notiz direkt in Obsidian öffnet."""
        if not self.rel_path:
            return None
        return (
            f"obsidian://open?vault={quote(VAULT_NAME)}"
            f"&file={quote(self.rel_path)}"
        )


def _read_meta(md_file: Path) -> dict:
    """Frontmatter einer Markdown-Datei lesen. Fehler tolerant abfangen."""
    try:
        post = frontmatter.load(md_file, encoding="utf-8")
        return dict(post.metadata)
    except Exception:
        return {}


def _norm_tags(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [t.strip() for t in raw.replace(",", " ").split() if t.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(t).strip() for t in raw if str(t).strip()]
    return []


def _project_from_file(md_file: Path, category: str, vault: Path) -> Project:
    meta = _read_meta(md_file)
    rel = md_file.relative_to(vault).as_posix()
    return Project(
        name=md_file.stem,
        category=category,
        status=meta.get("status"),
        tags=_norm_tags(meta.get("tags")),
        updated=str(meta.get("aktualisiert") or meta.get("date") or ""),
        rel_path=rel,
        is_folder=False,
    )


def _representative_note(folder: Path) -> Path | None:
    """Hauptnotiz eines Ordner-Projekts finden (gleicher Name oder Planungsnote)."""
    same = folder / f"{folder.name}.md"
    if same.exists():
        return same
    for md in sorted(folder.glob("*.md")):
        if md.stem.lower().startswith(("unterrichtsplanung", "readme", folder.name.lower())):
            return md
    return None


def _project_from_folder(folder: Path, category: str, vault: Path) -> Project:
    rep = _representative_note(folder)
    meta = _read_meta(rep) if rep else {}
    rel = rep.relative_to(vault).as_posix() if rep else None
    return Project(
        name=folder.name,
        category=category,
        status=meta.get("status") or "aktiv",
        tags=_norm_tags(meta.get("tags")),
        updated=str(meta.get("aktualisiert") or meta.get("date") or ""),
        rel_path=rel,
        is_folder=True,
    )


def load_projects(vault: Path | None = None) -> list[Project]:
    """Alle Projekte aus den konfigurierten Projekt-Ordnern einsammeln."""
    vault = vault or VAULT_PATH
    projects: list[Project] = []

    for sub, category in PROJEKT_DIRS:
        base = vault / sub
        if not base.exists():
            continue
        # Top-Level .md-Dateien = einzelne Projekte
        for md in sorted(base.glob("*.md")):
            projects.append(_project_from_file(md, category, vault))
        # Unterordner = Ordner-Projekte (z. B. Unterrichtsreihen).
        # Nur echte Projekt-Ordner: mind. eine .md-Datei (schließt Anhang-Ordner aus).
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            if any(folder.glob("*.md")):
                projects.append(_project_from_folder(folder, category, vault))

    return projects


def vault_available(vault: Path | None = None) -> bool:
    vault = vault or VAULT_PATH
    return vault.exists() and vault.is_dir()


# --- Skills ------------------------------------------------------------------
@dataclass
class Skill:
    name: str
    level: int
    category: str


def load_skills(path: Path | None = None) -> list[Skill]:
    """Skills aus Markdown lesen. Format: `## Kategorie` + `- Name :: Level`."""
    path = path or SKILLS_FILE
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    # Frontmatter abtrennen
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]

    skills: list[Skill] = []
    category = "Allgemein"
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            category = line[3:].strip()
        elif line.startswith("- ") and "::" in line:
            name, _, level = line[2:].partition("::")
            try:
                lvl = max(0, min(100, int(re.sub(r"[^0-9]", "", level) or 0)))
            except ValueError:
                lvl = 0
            skills.append(Skill(name=name.strip(), level=lvl, category=category))
    return skills


# --- Kanban ------------------------------------------------------------------
@dataclass
class KanbanItem:
    text: str
    done: bool


@dataclass
class KanbanColumn:
    title: str
    items: list[KanbanItem] = field(default_factory=list)


def save_kanban(columns: list[KanbanColumn], path: Path | None = None) -> str:
    """Kanban-Spalten zurück in die Markdown-Datei schreiben (Obsidian-Kanban-Format).

    Einzige Schreiboperation ins Vault. Frontmatter und der
    ``%% kanban:settings %%``-Block des Obsidian-Plugins bleiben erhalten,
    nur die Spalten/Karten dazwischen werden neu aufgebaut.

    Rückgabe: "" wenn alles glatt lief, sonst eine Meldung für die UI.
    """
    path = path or KANBAN_FILE
    if not VAULT_WRITEBACK:
        return "Schreibzugriff aufs Vault ist deaktiviert (VAULT_WRITEBACK=false)."
    original = path.read_text(encoding="utf-8") if path.exists() else ""

    head = ""
    rest = original
    if original.startswith("---"):
        parts = original.split("---", 2)
        if len(parts) == 3:
            head = f"---{parts[1]}---\n"
            rest = parts[2]

    m = re.search(r"%%\s*kanban:settings.*?%%", rest, flags=re.DOTALL)
    settings = m.group(0) if m else ""

    blocks = []
    for col in columns:
        lines = [f"## {col.title}", ""]
        lines += [f"- [{'x' if it.done else ' '}] {it.text}" for it in col.items]
        blocks.append("\n".join(lines).rstrip())

    out = head + "\n" + "\n\n".join(blocks) + "\n"
    if settings:
        out += "\n" + settings + "\n"
    path.write_text(out, encoding="utf-8", newline="\n")

    if not VAULT_AUTOCOMMIT:
        return ""
    try:
        rel = path.resolve().relative_to(VAULT_PATH.resolve()).as_posix()
    except ValueError:
        # Datei liegt außerhalb des Vaults — dann gibt es nichts zu committen.
        return ""
    return commit_and_push(VAULT_PATH, rel, "Kanban: Stand aus dem Command Center")


def load_kanban(path: Path | None = None) -> list[KanbanColumn]:
    """Kanban aus dem Obsidian-Kanban-Plugin-Markdown lesen (single source of truth)."""
    path = path or KANBAN_FILE
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]

    columns: list[KanbanColumn] = []
    current: KanbanColumn | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("%% kanban:settings"):
            break
        if stripped.startswith("## "):
            current = KanbanColumn(title=stripped[3:].strip())
            columns.append(current)
        elif current is not None:
            m = re.match(r"-\s*\[([ xX])\]\s*(.+)", stripped)
            if m:
                current.items.append(
                    KanbanItem(text=m.group(2).strip(), done=m.group(1).lower() == "x")
                )
    return columns


# --- Tools / Launcher --------------------------------------------------------
@dataclass
class Tool:
    name: str
    icon: str = "🔧"
    url: str = ""
    desc: str = ""
    status: str = "aktiv"


def load_tools(path: Path | None = None) -> list[Tool]:
    """Tool-Launcher-Kacheln aus tools.toml lesen."""
    path = path or TOOLS_FILE
    if not path.exists():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return []
    return [
        Tool(
            name=str(t.get("name", "?")),
            icon=str(t.get("icon", "🔧")),
            url=str(t.get("url", "")),
            desc=str(t.get("desc", "")),
            status=str(t.get("status", "aktiv")),
        )
        for t in data.get("tool", [])
    ]
