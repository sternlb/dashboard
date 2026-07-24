"""AI Command Center — Top-Level-Dashboard (Forest/Lime Design).

Schritt 1: Projekte aus dem Vault.
Schritt 2: Tool-Launcher, Skills-Section, Kanban (aus md-File), Projekte nach
Beruflich/Privat getrennt. Token-Nutzung und Kalender folgen.
"""
from __future__ import annotations

import html
from datetime import date, datetime, timedelta

import streamlit as st

from command_center import theme
from command_center.calendar_google import CalEvent, load_events
from command_center.config import LAN_IP, TRADING_URL, VAULT_PATH, external_url
from command_center.github import load_repos
from command_center.repo_sync import sync_repos
from command_center.scan_log import ScanEntry, load_scan_log
from command_center.trading import load_trading_summary
from command_center.usage import (
    TokenState,
    load_token_state,
    load_usage,
    save_token_state,
)
from streamlit_sortables import sort_items

from command_center.vault import (
    KanbanColumn,
    KanbanItem,
    Project,
    load_kanban,
    load_projects,
    load_skills,
    load_tools,
    save_kanban,
    vault_available,
)

_WD = ["MO", "DI", "MI", "DO", "FR", "SA", "SO"]


@st.cache_data(ttl=300)
def _cached_usage():
    return load_usage()


@st.cache_data(ttl=600)
def _cached_repos():
    return load_repos()


@st.cache_data(ttl=60)
def _cached_scan_log():
    return load_scan_log()


def _fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)

st.set_page_config(page_title="AI Command Center", page_icon="🧭", layout="wide")
theme.inject()

HERO_PROJECT = "Trading Agent"  # bekommt die hervorgehobene Lime-Karte


def _esc(s: str) -> str:
    return html.escape(s or "")


def eyebrow(text: str) -> None:
    st.markdown(
        f'<span class="acc-eyebrow"><span class="acc-dot"></span> {_esc(text)}</span>',
        unsafe_allow_html=True,
    )


def topbar() -> None:
    now = datetime.now()
    stamp = f"{_WD[now.weekday()]} {now.day:02d}.{now.month:02d}. · {now.hour:02d}:{now.minute:02d}"
    st.markdown(
        f"""
        <div class="acc-topbar">
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="acc-logo">◈</span>
            <span class="acc-disp" style="font-size:15px;color:#FAFAF5;">command<span style="background:#A3E635;color:#14532D;border-radius:6px;padding:1px 7px;margin-left:5px;">center</span></span>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="acc-mono acc-sub">Persönliche Kommandozentrale</span>
            <span class="acc-chip">{stamp}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _greeting() -> str:
    h = datetime.now().hour
    if 5 <= h < 11:
        return "Guten Morgen"
    if 11 <= h < 18:
        return "Guten Tag"
    return "Guten Abend"


def hero() -> None:
    st.markdown(
        f"""
        <div class="acc-hero">
          <span class="acc-eyebrow on-paper"><span class="acc-dot"></span> Kommandozentrale</span>
          <h1>{_greeting()}, Leo.<br>Alles <span class="mark">im Griff</span>.</h1>
          <p>Deine Projekte, Skills, offenen Themen und das KI-Budget — an einer Stelle, jeden Morgen aktuell.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def vitals(projects: list[Project]) -> None:
    total = len(projects)
    active = sum(1 for p in projects if p.status_norm == "aktiv")
    beruflich = sum(1 for p in projects if p.category == "Beruflich")
    privat = sum(1 for p in projects if p.category == "Privat")

    def tile(num, label, lime=False) -> str:
        c = " lime" if lime else ""
        return (
            f'<div><div class="acc-vital-num{c}">{num}</div>'
            f'<div class="acc-vital-lbl{c}">{label}</div></div>'
        )

    st.markdown(
        '<div class="acc-vitals">'
        + tile(f"{total:02d}", "Projekte gesamt", lime=True)
        + tile(f"{active:02d}", "aktiv")
        + tile(f"{beruflich:02d}", "beruflich")
        + tile(f"{privat:02d}", "privat")
        + "</div>",
        unsafe_allow_html=True,
    )


# --- Tool-Launcher -----------------------------------------------------------
def tools_section() -> None:
    tools = load_tools()
    if not tools:
        return
    eyebrow("Tools & Dashboards")
    st.markdown('<h2 class="acc-section-h">Deine Cockpits</h2>', unsafe_allow_html=True)
    tiles = ""
    for t in tools:
        geplant = " geplant" if t.status.lower() != "aktiv" else ""
        color = theme.STATUS_COLOR.get(t.status.lower(), theme.LIME)
        url = external_url(t.url)
        open_a = f'<a class="acc-tool{geplant}" href="{url}" target="_blank">' if url else f'<div class="acc-tool{geplant}">'
        close_a = "</a>" if t.url else "</div>"
        tiles += (
            f'{open_a}<div class="ic">{_esc(t.icon)}</div>'
            f'<div class="tn">{_esc(t.name)}</div>'
            f'<div class="td">{_esc(t.desc)}</div>'
            f'<span class="acc-badge" style="color:{color};margin-top:11px;display:inline-block;">● {_esc(t.status)}</span>'
            f"{close_a}"
        )
    st.markdown(f'<div class="acc-tools">{tiles}</div>', unsafe_allow_html=True)


# --- Finanzen (Trading Agent eingehängt) -------------------------------------
def _eur(v: float) -> str:
    return f"{v:,.0f} €".replace(",", ".")


def _pct(v: float) -> str:
    return f"{'+' if v >= 0 else ''}{v:.1f}%".replace(".", ",")


def _fin_date(updated: str) -> str:
    d = (updated or "").split(" ")[0].split("-")
    return f"{d[2]}.{d[1]}.{d[0]}" if len(d) == 3 else (updated or "—")


def trading_section() -> None:
    eyebrow("Finanzen · Trading Agent")
    st.markdown('<h2 class="acc-section-h">Depot auf einen Blick</h2>', unsafe_allow_html=True)

    # Depotwerte erst nach aktivem Klick zeigen (Privatsphäre am geteilten Bildschirm).
    if not st.toggle("Depot anzeigen", value=False, key="show_depot"):
        return

    s = load_trading_summary()
    if not s.available:
        st.markdown(
            placeholder_block(
                "Trading Agent — keine Daten",
                "holdings.csv nicht gefunden. Läuft der Trading Agent / stimmt der Pfad?",
            ),
            unsafe_allow_html=True,
        )
        return

    gain_lime = " lime" if s.gain_eur >= 0 else ""

    def tile(num, label, cls="") -> str:
        return (
            f'<div><div class="acc-vital-num{cls}">{num}</div>'
            f'<div class="acc-vital-lbl{cls}">{label}</div></div>'
        )

    st.markdown(
        '<div class="acc-vitals">'
        + tile(_eur(s.total_value), "Depotwert")
        + tile(f"{_pct(s.gain_pct)}", f"Rendite · {_eur(s.gain_eur)}", cls=gain_lime)
        + tile(f"{s.positions}", "Positionen")
        + tile(_fin_date(s.updated), "Stand")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="acc-subline">Größter Block: <b>{_esc(s.top_theme)} '
        f'{s.top_theme_share:.0f}%</b> · Größte Position: <b>{_esc(s.top_position)}</b> · '
        f'Favoriten: <b>{s.favorites}</b> · Order-Sheet: <b>{s.order_sheet}</b></div>'
        f'<a class="acc-cta" href="{TRADING_URL}" target="_blank">Trading Agent öffnen ↗</a>',
        unsafe_allow_html=True,
    )
    with st.expander("Live-Ansicht einbetten"):
        st.iframe(f"{TRADING_URL}/?embed=true", height=620)


# --- Projekte ----------------------------------------------------------------
def _card_html(p: Project) -> str:
    is_hero = p.name == HERO_PROJECT
    cls = "acc-card hero" if is_hero else "acc-card"
    href = f' href="{p.obsidian_url}" target="_self"' if p.obsidian_url else ""
    tag = _esc(p.tags[1]) if len(p.tags) > 1 else _esc(p.tags[0]) if p.tags else ""
    color = theme.STATUS_COLOR.get(p.status_norm, theme.SAGE)
    return (
        f'<a class="{cls}"{href}>'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<span class="name">{_esc(p.name)}</span><span class="arrow">↗</span></div>'
        f'<div class="desc">{tag}</div>'
        f'<span class="acc-badge" style="color:{color};">● {_esc(p.status_norm)}</span>'
        f"</a>"
    )


def projects_section() -> None:
    eyebrow("Deine Projekte")

    if not vault_available():
        st.error(
            f"Vault nicht gefunden unter `{VAULT_PATH}` — Pfad prüfen oder "
            "Umgebungsvariable `VAULT_PATH` setzen."
        )
        return

    projects = load_projects()
    if not projects:
        st.info("Keine Projekte gefunden.")
        return

    st.markdown(
        f'<h2 class="acc-section-h">{len(projects)} laufende Projekte</h2>',
        unsafe_allow_html=True,
    )

    for category in ("Beruflich", "Privat"):
        group = [p for p in projects if p.category == category]
        if not group:
            continue
        ordered = sorted(
            group,
            key=lambda p: (p.name != HERO_PROJECT, p.status_norm != "aktiv", p.name.lower()),
        )
        st.markdown(f'<div class="acc-cat">{category} · {len(group)}</div>', unsafe_allow_html=True)
        cards = "".join(_card_html(p) for p in ordered)
        st.markdown(f'<div class="acc-grid">{cards}</div>', unsafe_allow_html=True)


# --- GitHub-Repos --------------------------------------------------------------
def _rel_days(dt: datetime | None) -> str:
    if not dt:
        return "—"
    days = (date.today() - dt.date()).days
    if days <= 0:
        return "heute"
    if days == 1:
        return "gestern"
    if days < 7:
        return f"vor {days} Tagen"
    if days < 30:
        w = days // 7
        return "vor 1 Woche" if w == 1 else f"vor {w} Wochen"
    m = days // 30
    return "vor 1 Monat" if m == 1 else f"vor {m} Monaten"


_SYNC_BADGES = {
    "updated": ("🟢", "aktualisiert"),
    "up_to_date": ("⚪", "aktuell"),
    "skipped_dirty": ("🟡", "übersprungen"),
    "missing": ("🟡", "fehlt lokal"),
    "error": ("🔴", "Fehler"),
}


def repo_sync_button() -> None:
    """Button: git pull für die lokalen Klone (sync = true in repos.toml)."""
    if not st.button(
        "⟳ Repos aktualisieren",
        help="git pull für Unterrichts-Repos + Vault — Sub-Pages (/gdp, /datb) und Landing Page sind danach sofort aktuell.",
    ):
        return
    with st.spinner("Hole Stand von GitHub …"):
        results = sync_repos()
    _cached_repos.clear()
    lines = ""
    for r in results:
        dot, word = _SYNC_BADGES.get(r.state, ("⚪", r.state))
        lines += (
            f'<div style="display:flex;gap:8px;align-items:baseline;font-size:13px;">'
            f"<span>{dot}</span>"
            f'<span style="color:#FAFAF5;">{_esc(r.icon)} {_esc(r.label or r.name)}</span>'
            f'<span class="acc-mono" style="color:#9CA3AF;font-size:11px;">{word} · {_esc(r.detail)}</span>'
            f"</div>"
        )
    st.markdown(lines, unsafe_allow_html=True)


def github_section() -> None:
    eyebrow("GitHub · sternlb")
    st.markdown('<h2 class="acc-section-h">Deine Repos</h2>', unsafe_allow_html=True)
    repo_sync_button()
    res = _cached_repos()

    if res.state != "ok":
        hints = {
            "no_config": "repos.toml im Projektordner anlegen (owner + [[repo]]-Einträge).",
            "no_gh": "GitHub CLI (gh) nicht gefunden — installieren und 'gh auth login' ausführen.",
            "error": f"GitHub nicht erreichbar: {res.detail[:160]}",
        }
        st.markdown(
            placeholder_block("Repos — keine Daten", hints.get(res.state, res.detail)),
            unsafe_allow_html=True,
        )
        return

    tiles = ""
    for r in res.repos:
        vis = "privat" if r.visibility == "private" else "öffentlich"
        vis_color = theme.SAGE if r.visibility == "private" else theme.LIME
        lang = f'<span class="acc-badge" style="color:#FAFAF5;">{_esc(r.language)}</span>' if r.language else ""
        tiles += (
            f'<a class="acc-tool" href="{_esc(r.url)}" target="_blank">'
            f'<div class="ic">{_esc(r.icon)}</div>'
            f'<div class="tn">{_esc(r.label)}</div>'
            f'<div class="td acc-mono" style="font-size:11px;">{_esc(r.name)}</div>'
            f'<div class="td">{_esc(r.description) or "—"}</div>'
            f'<div class="meta">'
            f'<span class="acc-badge" style="color:{vis_color};">● {vis}</span>{lang}'
            f'<span class="acc-badge" style="color:#9CA3AF;">Push: {_rel_days(r.pushed_at)}</span>'
            f"</div></a>"
        )
    st.markdown(f'<div class="acc-tools">{tiles}</div>', unsafe_allow_html=True)
    st.caption("Live über die GitHub CLI · Klick öffnet das Repo · Liste in repos.toml pflegen.")


# --- Scanner-Ablage ----------------------------------------------------------
_SCAN_BADGES = {
    "kopiert": ("📄", theme.LIME, "abgelegt"),
    "übersprungen": ("⏭", theme.GELB, "übersprungen"),
    "fehler": ("⚠", theme.ROT, "Fehler"),
}


def _scan_when(e: ScanEntry) -> str:
    if not e.when:
        return e.when_raw or "—"
    d = e.when
    return f"{_WD[d.weekday()]} {d.day:02d}.{d.month:02d} · {d.hour:02d}:{d.minute:02d}"


def _scan_row(e: ScanEntry) -> str:
    icon, color, word = _SCAN_BADGES.get(e.action, ("•", theme.SAGE, e.action or "—"))
    title = e.target_name or e.source_name or "—"
    full = f"{e.target_dir}\\{e.target_name}" if e.target_dir else e.source_dir

    trail = e.short_dir()
    if trail:
        # Abgelegt: Zielordner + woher die Datei kam.
        sub = (
            f'<span style="color:{theme.LIME};">↳ {_esc(trail)}</span>'
            f'<span style="color:rgba(250,250,245,0.35);"> · aus {_esc(e.source_name)}</span>'
        )
    else:
        # Ohne Ziel (übersprungen/Fehler) steht oben schon der Quellname.
        sub = f'<span style="color:#9CA3AF;">{_esc(e.note) or "kein Ziel"}</span>'
    if e.note and trail:
        # Grund bei Fehlern trotzdem zeigen, wenn schon ein Zielpfad feststand.
        sub += f'<span style="color:{theme.ROT};"> · {_esc(e.note)}</span>'
    person = (
        f'<span class="acc-badge" style="color:#FAFAF5;">{_esc(e.person)}</span>'
        if e.person
        else ""
    )

    return (
        '<div style="display:flex;gap:14px;align-items:flex-start;padding:10px 0;'
        'border-bottom:1px solid rgba(255,255,255,0.07);">'
        f'<span class="acc-mono" style="font-size:12px;color:{color};min-width:118px;'
        f'padding-top:2px;">{icon} {_scan_when(e)}</span>'
        '<span style="flex:1;min-width:0;">'
        f'<span style="font-size:14px;color:#FAFAF5;word-break:break-word;" '
        f'title="{_esc(full)}">{_esc(title)}</span>'
        '<span style="display:block;font-size:11.5px;color:rgba(250,250,245,0.5);'
        f'margin-top:3px;word-break:break-word;">{sub}</span></span>'
        f'<span style="display:flex;gap:6px;align-items:center;flex-shrink:0;">{person}'
        f'<span class="acc-badge" style="color:{color};">{_esc(word)}</span></span>'
        "</div>"
    )


def scan_section() -> None:
    eyebrow("Scanner · Brother ADS-1700W")
    st.markdown(
        '<h2 class="acc-section-h">Zuletzt einsortiert</h2>', unsafe_allow_html=True
    )
    res = _cached_scan_log()

    if res.state != "ok":
        hints = {
            "missing": f"Noch kein Logbuch — entsteht beim ersten Scan unter {res.path}.",
            "empty": "Logbuch ist noch leer — der erste verarbeitete Scan landet hier.",
            "error": f"Logbuch nicht lesbar: {res.detail[:160]}",
        }
        st.markdown(
            placeholder_block("Scanner-Ablage — keine Einträge", hints.get(res.state, res.detail)),
            unsafe_allow_html=True,
        )
        return

    rows = "".join(_scan_row(e) for e in res.entries)
    st.markdown(f"<div>{rows}</div>", unsafe_allow_html=True)
    st.caption(
        f"Die letzten {len(res.entries)} von {res.total} Bewegungen · "
        f"Ziel = Personen-Inbox + Typ-Unterordner · Vollständiges Logbuch: {res.path}"
    )


# --- Skills ------------------------------------------------------------------
def skills_section() -> None:
    skills = load_skills()
    eyebrow("Skills")
    st.markdown('<h2 class="acc-section-h">Stärken</h2>', unsafe_allow_html=True)
    if not skills:
        st.markdown(
            '<div class="acc-placeholder"><div class="t">Noch keine Skills</div>'
            '<div class="n">Datei 00 Kontext/Skills.md füllen (Format: - Name :: Level).</div></div>',
            unsafe_allow_html=True,
        )
        return

    cats: dict[str, list] = {}
    for s in skills:
        cats.setdefault(s.category, []).append(s)

    blocks = ""
    for cat, items in cats.items():
        rows = ""
        for s in items:
            rows += (
                f'<div class="acc-skill"><div class="acc-skill-top">'
                f'<span class="acc-skill-name">{_esc(s.name)}</span>'
                f'<span class="acc-skill-lvl">{s.level}</span></div>'
                f'<div class="acc-track"><div class="acc-fill" style="width:{s.level}%"></div></div></div>'
            )
        blocks += f'<div><div class="acc-cat">{_esc(cat)}</div>{rows}</div>'
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:26px;">{blocks}</div>',
        unsafe_allow_html=True,
    )


# --- Kanban ------------------------------------------------------------------
def kanban_section() -> None:
    eyebrow("Kanban · offene Themen")
    st.markdown('<h2 class="acc-section-h">Board</h2>', unsafe_allow_html=True)

    # Die Sortier-Komponente bekommt pro Session UNVERÄNDERLICHE Props: einmal
    # aus der Datei geladen, danach nie neu zugewiesen. Würden wir ihr nach
    # jedem Drag den neuen Stand als Props zurückfüttern (wie ursprünglich),
    # schaukeln sich Remounts zur React-Update-Schleife hoch (Error #185).
    # Gespeichert wird trotzdem bei jedem Drag; Obsidian-seitige Änderungen
    # erscheinen beim nächsten Seiten-Reload (frische Session).
    if "kanban_board" not in st.session_state:
        columns = load_kanban()
        if not columns:
            st.markdown(
                '<div class="acc-placeholder"><div class="t">Kein Board</div>'
                '<div class="n">Datei 01 Inbox/Kanban.md anlegen.</div></div>',
                unsafe_allow_html=True,
            )
            return
        st.session_state.kanban_board = [
            {"header": c.title, "items": [i.text for i in c.items]} for c in columns
        ]
        st.session_state.kanban_done_idx = [
            i for i, c in enumerate(columns) if "erledigt" in c.title.lower()
        ]
        st.session_state.kanban_saved = st.session_state.kanban_board

    result = sort_items(
        st.session_state.kanban_board,
        multi_containers=True,
        custom_style=theme.kanban_sortable_css(st.session_state.kanban_done_idx),
        key="kanban_sort",
    )

    if result and result != st.session_state.kanban_saved:
        new_cols = [
            KanbanColumn(
                title=c["header"],
                items=[
                    KanbanItem(text=t, done="erledigt" in c["header"].lower())
                    for t in c["items"]
                ],
            )
            for c in result
        ]
        save_kanban(new_cols)
        st.session_state.kanban_saved = result

    st.caption(
        "Karten per Drag & Drop verschieben — Änderungen landen direkt in "
        "01 Inbox/Kanban.md (Obsidian sieht sie sofort)."
    )


# --- Placeholder (Token / Kalender) ------------------------------------------
def placeholder_block(title: str, note: str) -> str:
    return (
        f'<div class="acc-placeholder"><div class="t">{_esc(title)}</div>'
        f'<div class="n">{_esc(note)}</div></div>'
    )


def _fmt_when(ev: CalEvent) -> str:
    d = ev.start
    base = f"{_WD[d.weekday()]} {d.day:02d}.{d.month:02d}"
    return base if ev.all_day else f"{base} · {d.hour:02d}:{d.minute:02d}"


def calendar_section() -> None:
    eyebrow("Kalender · Google")
    st.markdown('<h2 class="acc-section-h">Kommende Termine</h2>', unsafe_allow_html=True)
    res = load_events()

    if res.state == "ok":
        if not res.events:
            st.markdown(
                '<div class="acc-placeholder"><div class="n">Keine anstehenden Termine.</div></div>',
                unsafe_allow_html=True,
            )
            return
        rows = ""
        for i, ev in enumerate(res.events):
            color = "#A3E635" if i == 0 else "#9CA3AF"
            loc = f' <span style="color:rgba(250,250,245,0.5);">· {_esc(ev.location)}</span>' if ev.location else ""
            rows += (
                '<div style="display:flex;gap:16px;align-items:center;padding:10px 0;'
                'border-bottom:1px solid rgba(255,255,255,0.07);">'
                f'<span class="acc-mono" style="font-size:12px;color:{color};min-width:96px;">{_fmt_when(ev)}</span>'
                f'<span style="font-size:14px;color:#FAFAF5;">{_esc(ev.summary)}{loc}</span></div>'
            )
        st.markdown(f"<div>{rows}</div>", unsafe_allow_html=True)
        return

    hints = {
        "needs_credentials": "Einrichtung nötig: credentials.json (OAuth-Client Typ Desktop app) ins Projekt legen.",
        "needs_setup": "Fast fertig: einmalig 'python setup_calendar.py' ausführen und Zugriff freigeben.",
        "error": f"Kalender nicht erreichbar: {res.detail[:120]}",
    }
    st.markdown(
        placeholder_block("Kalender — noch nicht verbunden", hints.get(res.state, "")),
        unsafe_allow_html=True,
    )


def _usage_bars(by_day: dict[str, int]) -> str:
    days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    vals = [by_day.get(d.isoformat(), 0) for d in days]
    peak = max(vals) or 1
    cols = ""
    for d, v in zip(days, vals):
        h = max(3, round(v / peak * 60))
        cols += (
            '<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">'
            f'<div style="width:100%;height:60px;display:flex;align-items:flex-end;">'
            f'<div class="acc-ubar" title="{_fmt_tok(v)}" style="height:{h}px;"></div></div>'
            f'<span class="acc-mono" style="font-size:10px;color:rgba(250,250,245,0.45);">{_WD[d.weekday()]}</span></div>'
        )
    return f'<div style="display:flex;gap:8px;align-items:flex-end;margin-top:4px;">{cols}</div>'


def _limit_row(label: str, used: int, cap: int, sub: str = "") -> str:
    """Limit-Zeile wie in Claude → Einstellungen → Nutzung: % genutzt + % frei."""
    if cap <= 0:
        return ""
    pct = min(100.0, used / cap * 100)
    free_pct = max(0.0, 100.0 - pct)
    color = theme.LIME if pct < 80 else (theme.GELB if pct < 100 else theme.ROT)
    sub_html = f'<div class="sub">{_esc(sub)}</div>' if sub else ""
    return (
        '<div class="acc-limit">'
        '<div class="row">'
        f'<span class="lbl">{_esc(label)}</span>'
        f'<span class="pct">{pct:.0f} % genutzt · <b>{free_pct:.0f} % frei</b> · '
        f'{_fmt_tok(max(0, cap - used))} übrig</span></div>'
        f'<div class="bar"><div style="width:{pct:.0f}%;background:{color};"></div></div>'
        f"{sub_html}</div>"
    )


def token_section() -> None:
    eyebrow("Token-Nutzung")
    st.markdown('<h2 class="acc-section-h">Claude Code — Nutzung & offene Limits</h2>', unsafe_allow_html=True)
    u = _cached_usage()
    ts = load_token_state()

    def tile(num, label, lime=False) -> str:
        c = " lime" if lime else ""
        return f'<div><div class="acc-vital-num{c}">{num}</div><div class="acc-vital-lbl{c}">{label}</div></div>'

    st.markdown(
        '<div class="acc-vitals">'
        + tile(_fmt_tok(u.tokens_5h), "5-Std-Fenster", lime=True)
        + tile(_fmt_tok(u.tokens_7d), "diese Woche")
        + tile(_fmt_tok(u.tokens_today), "heute")
        + tile(f"{u.msgs_5h}", "Nachrichten 5 Std")
        + "</div>",
        unsafe_allow_html=True,
    )

    # Offene Limits in % — wie Claude unter Einstellungen → Nutzung.
    reset_5h = ""
    if u.window_start_5h and u.tokens_5h:
        r = u.window_start_5h + timedelta(hours=5)
        reset_5h = f"Setzt sich zurück ca. {r.hour:02d}:{r.minute:02d} Uhr"
    rows = _limit_row("Aktuelle Sitzung · 5-Std-Fenster", u.tokens_5h, ts.limit_5h, reset_5h) + _limit_row(
        "Wochenlimit · alle Modelle",
        u.tokens_7d,
        ts.limit_week,
        f"Setzt sich zurück: {ts.week_reset}" if ts.week_reset else "",
    )
    if rows:
        st.markdown(f'<div class="acc-limits">{rows}</div>', unsafe_allow_html=True)
    else:
        st.caption(
            "Offene Limits in %: setze deine Caps unten (aus Claude Code /status "
            "bzw. Claude → Einstellungen → Nutzung). Ein offizieller API-Wert existiert nicht."
        )

    st.markdown(_usage_bars(u.by_day), unsafe_allow_html=True)
    st.caption(
        "Echte Input+Output-Tokens (7-Tage-Verlauf), pro API-Call dedupliziert. "
        "Cache-Reads nicht gezählt."
    )

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    if ts.free_amount:
        st.markdown(
            f'<div class="acc-placeholder" style="border-style:solid;">'
            f'<div class="t">Free-Credit-Rest: {ts.free_amount:,.2f} {_esc(ts.currency)}</div>'
            f'<div class="n">manuell · Stand {_esc(ts.updated) or "—"}</div></div>',
            unsafe_allow_html=True,
        )

    with st.expander("Einstellungen: Free-Credit & Limits"):
        st.caption("Caps in Tokens (Input+Output). 0 = nicht anzeigen.")
        c = st.columns(3)
        limit_5h = c[0].number_input("Cap 5-Std-Fenster", min_value=0, value=ts.limit_5h, step=100_000)
        limit_week = c[1].number_input("Cap Woche", min_value=0, value=ts.limit_week, step=1_000_000)
        week_reset = c[2].text_input(
            "Wochen-Reset (Anzeige)", value=ts.week_reset, placeholder="z. B. Di 08:00"
        )
        d = st.columns([0.5, 0.3, 0.2])
        amount = d[0].number_input("Free-Credit-Rest", min_value=0.0, value=float(ts.free_amount), step=1.0)
        currency = d[1].selectbox("Währung", ["USD", "EUR"], index=0 if ts.currency == "USD" else 1)
        if d[2].button("Speichern", use_container_width=True):
            save_token_state(
                TokenState(
                    free_amount=amount,
                    currency=currency,
                    updated=date.today().isoformat(),
                    limit_5h=int(limit_5h),
                    limit_week=int(limit_week),
                    week_reset=week_reset.strip(),
                )
            )
            st.rerun()


def section_gap() -> None:
    st.markdown('<div style="height:26px;"></div>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        f'<div class="acc-footer">'
        f'<span>◈ commandcenter</span>'
        f'<span>im WLAN: http://{LAN_IP}:8500 · Trading Agent: http://{LAN_IP}:8501</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    topbar()
    hero()
    projects = load_projects() if vault_available() else []
    if projects:
        vitals(projects)

    token_section()
    section_gap()
    tools_section()
    section_gap()
    trading_section()
    section_gap()
    projects_section()
    section_gap()
    github_section()
    section_gap()
    scan_section()
    section_gap()
    skills_section()
    section_gap()
    kanban_section()
    section_gap()
    calendar_section()
    footer()


if __name__ == "__main__":
    main()
