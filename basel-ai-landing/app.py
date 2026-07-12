"""Basel-AI Web — statischer HTTP-Server für Landing Page, Kurs-Katalog
und die Unterrichts-Repos (GdP, DatB).

Serviert HTML/Assets direkt aus dem Vault-Ordner
`03 Projekte (privat)/Basel-AI Consulting/` (Single Source of Truth) sowie
die geclonten Unterrichts-Repos unter eigenen Mount-Pfaden. Kein Streamlit,
keine externen Pakete — reiner stdlib-HTTP-Server. Jede Anfrage liest die
Datei neu ein, Aenderungen sind also sofort per Reload sichtbar, ganz ohne
Server-Neustart.

Routen:
  /            -> Landing Page Basel-AI.html
  /kurse       -> Kurs-Katalog Basel-AI.html
  /gdp/        -> index.html aus dem Geschwister-Repo 2526_KI1_GdP_C
  /datb/       -> index.html aus dem Geschwister-Repo 2526_KI1_DatB
  /gdp/<pfad>, /datb/<pfad> -> Dateien rekursiv aus dem jeweiligen Repo
                  (nur erlaubte Endungen, kein Pfad-Traversal). Die Repos
                  nutzen nur relative Links, daher funktionieren dieselben
                  Dateien unveraendert auch direkt per file:// im Klon.
  /02 Projekte/…, /10 Anhang/Podcasts/… -> Vault-Ordner fuer die
                  "../../"-Links der User Stories (Lektionen + Lern-Podcast).
  /<Pfad>      -> beliebige Datei aus dem Basel-AI-Ordner inkl. Unterordner
                  (nur erlaubte Endungen, kein Pfad-Traversal) — damit
                  funktionieren die relativen Links des Kurs-Katalogs auf
                  Foliensets & ZIPs sowie die Screenshots der User Stories
                  (Unterordner "User Story Assets").
"""
from __future__ import annotations

import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8502
# Vault und Unterrichts-Repos werden als Geschwister-Repos neben dem
# dashboard-Repo erwartet (…\repos\), überschreibbar per Env-Variable.
_REPOS = Path(__file__).resolve().parents[2]
BASE_DIR = Path(
    os.environ.get(
        "BASEL_AI_DIR",
        _REPOS / "SecondBrain-Leo" / "03 Projekte (privat)" / "Basel-AI Consulting",
    )
)
ROUTES = {
    "/": "Landing Page Basel-AI.html",
    "/kurse": "Kurs-Katalog Basel-AI.html",
}
# Unterrichts-Repos: Mount-Pfad -> Wurzelordner, rekursiv serviert.
# Dazu die Vault-Ordner, auf die die User Stories relativ verweisen
# ("../../02 Projekte/…", "../../10 Anhang/Podcasts/…"): der Browser
# normalisiert diese Pfade zu "/02 Projekte/…" bzw. "/10 Anhang/…",
# daher funktionieren dieselben relativen Links per HTTP und file://.
# Bewusst nur diese beiden Ordner (Unterrichtsmaterial + Podcasts),
# nicht der ganze Vault — private Projekte bleiben unerreichbar.
_VAULT = BASE_DIR.parents[1]
MOUNTS = {
    "/gdp": Path(os.environ.get("GDP_DIR", _REPOS / "2526_KI1_GdP_C")),
    "/datb": Path(os.environ.get("DATB_DIR", _REPOS / "2526_KI1_DatB")),
    "/02 Projekte": _VAULT / "02 Projekte",
    "/10 Anhang/Podcasts": _VAULT / "10 Anhang" / "Podcasts",
}
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".mp3": "audio/mpeg",
    ".c": "text/plain; charset=utf-8",
    ".h": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


class LandingHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urllib.parse.unquote(self.path.split("?", 1)[0])
        if path.startswith("/favicon.ico"):
            self.send_response(204)
            self.end_headers()
            return

        # Unterrichts-Repos (rekursiv, mit Traversal-Schutz).
        for prefix, base in MOUNTS.items():
            if path == prefix:
                # Ohne Slash wuerden relative Links der index.html ins Leere
                # zeigen -> auf /gdp/ bzw. /datb/ umleiten.
                self.send_response(301)
                self.send_header("Location", prefix + "/")
                self.end_headers()
                return
            if path.startswith(prefix + "/"):
                rel = path[len(prefix) + 1 :]
                if not rel or rel.endswith("/"):
                    rel += "index.html"
                target = (base / rel).resolve()
                base_resolved = base.resolve()
                if base_resolved not in target.parents:
                    self._not_found()
                    return
                self._serve_file(target)
                return

        name = ROUTES.get(path.rstrip("/") or "/")
        if name is None:
            name = path.lstrip("/")
        target = (BASE_DIR / name).resolve()

        # Nur Dateien innerhalb des Basel-AI-Ordners (inkl. Unterordner
        # wie "User Story Assets", kein Pfad-Traversal).
        if BASE_DIR.resolve() not in target.parents:
            self._not_found()
            return
        self._serve_file(target)

    def _serve_file(self, target: Path) -> None:
        ctype = CONTENT_TYPES.get(target.suffix.lower())
        if ctype is None:
            self._not_found()
            return
        try:
            body = target.read_bytes()
        except OSError:
            self._not_found()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self) -> None:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Nicht gefunden.")

    def log_message(self, format: str, *args) -> None:  # ruhiger, kein Konsolen-Spam
        pass


def main() -> None:
    if not BASE_DIR.is_dir():
        print(f"WARNUNG: Basel-AI-Ordner fehlt: {BASE_DIR} (Env BASEL_AI_DIR setzen?)")
    for prefix, base in MOUNTS.items():
        if not base.is_dir():
            print(f"WARNUNG: Mount {prefix} zeigt ins Leere: {base}")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), LandingHandler)
    print(f"Basel-AI Web läuft auf http://localhost:{PORT} (/ = Landing, /kurse = Katalog)")
    server.serve_forever()


if __name__ == "__main__":
    main()
