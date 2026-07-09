"""Basel-AI Design-System — Farben, Fonts und CSS für das Dashboard.

Firmen-Branding Basel-AI Consulting (Single Source of Truth:
Vault → 00 Kontext/Branding.md, Teil 1): Waldgrün + Deep Forest als Basis,
Lime als Akzent (nie als Textfarbe auf hell), Gelb nur als Mikro-Akzent
(KI-Funke), flächige Farben ohne Verläufe. Space Grotesk für Headlines,
Inter für Fließtext, Space Mono für Zahlen/Labels.

Version 4 (Juli 2026): Web-Regeln der Landing Page übernommen
(Branding.md → "Web & Landing Pages"):
- Scharfe Kanten: max. 2px Border-Radius auf Boxen, Buttons, Tags, Balken.
- Scroll-/Einflug-Dynamik (Signature): Kacheln fliegen gestaffelt ein —
  Richtung/Rotation/Delay pro Element über CSS-Variablen (--fx-x/y/r/s/d),
  Easing cubic-bezier(.16,1,.3,1). In Browsern mit Scroll-Timeline-Support
  (Chrome/Edge) animieren Sektionen beim Scrollen in den Viewport, sonst
  gestaffelt beim Laden. prefers-reduced-motion wird immer respektiert.
"""
from __future__ import annotations

import streamlit as st

# --- Palette (Basel-AI) -------------------------------------------------------
FOREST = "#0C1F15"      # Deep Forest — Seitenhintergrund
FOREST_DEEP = "#081711" # Instrumentenleiste, Spalten, Tracks (abgedunkelt)
PINE = "#14532D"        # Waldgrün — Karten und Flächen
LIME = "#A3E635"        # Akzent (Kreidestrich, Hover, CTAs auf dunkel)
LIME_INK = "#14532D"    # Text auf Lime (wie die AI-Pill im Logo)
GELB = "#FDE047"        # KI-Funke — nur Mikro-Akzente
PAPER = "#FAFAF5"       # Off-White — helle Sektionen, Text auf dunkel
INK = "#0A0F0C"         # Text auf hell
SAGE = "#9CA3AF"        # gedämpfter Text auf dunkel
STONE = "#6B7280"       # gedämpfter Text auf hell
ROT = "#E24B4A"         # Limit fast/ganz ausgeschöpft

# Statusfarbe für Badges
STATUS_COLOR = {
    "aktiv": LIME,
    "pausiert": GELB,
    "abgeschlossen": SAGE,
    "geplant": "#D1D5DB",
    "unbekannt": SAGE,
}


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=Space+Mono:wght@400;700&display=swap');

/* --- Design-Token: scharfe Kanten (Branding-Regel Web, max. 2px) ----------- */
:root { --r: 2px; --fx-ease: cubic-bezier(.16, 1, .3, 1); }

/* --- Hintergrund: flächiges Deep Forest (Branding: keine Verläufe) --------- */
.stApp { background: #0C1F15; }
.block-container { max-width: 1120px; padding-top: 1.6rem; padding-bottom: 3rem; }

html, body, .stApp, .stMarkdown, p, span, div, label { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.02em; }

::selection { background: #A3E635; color: #14532D; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #081711; }
::-webkit-scrollbar-thumb { background: #1E5C36; border-radius: var(--r); }
::-webkit-scrollbar-thumb:hover { background: #2A7A4B; }

/* --- Einflug-Dynamik (Landing-Page-Signature) ------------------------------- */
@keyframes accFly {
  from { opacity: 0;
         transform: translate3d(var(--fx-x, 0px), var(--fx-y, 56px), 0)
                    rotate(var(--fx-r, 0deg)) scale(var(--fx-s, 1)); }
  to   { opacity: 1; transform: none; }
}
@keyframes accPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(163,230,53,0.45); } 50% { box-shadow: 0 0 0 6px rgba(163,230,53,0); } }
@keyframes accGrowX { from { width: 0; } }
@keyframes accGrowY { from { transform: scaleY(0); } }

.acc-hero, .acc-vitals, .acc-placeholder, .acc-fin, .acc-limits,
.acc-tools .acc-tool, .acc-grid .acc-card {
  animation: accFly 0.9s var(--fx-ease) both;
  animation-delay: var(--fx-d, 0s);
}
/* Kacheln fliegen gestaffelt und aus wechselnden Richtungen ein */
.acc-grid .acc-card:nth-child(odd)  { --fx-x: -60px; --fx-y: 36px; --fx-r: -1.5deg; --fx-s: .96; }
.acc-grid .acc-card:nth-child(even) { --fx-x: 60px;  --fx-y: 36px; --fx-r: 1.5deg;  --fx-s: .96; }
.acc-tools .acc-tool:nth-child(odd)  { --fx-y: 64px; --fx-s: .95; }
.acc-tools .acc-tool:nth-child(even) { --fx-y: 40px; --fx-s: .95; }
.acc-grid > :nth-child(2), .acc-tools > :nth-child(2) { --fx-d: .08s; }
.acc-grid > :nth-child(3), .acc-tools > :nth-child(3) { --fx-d: .16s; }
.acc-grid > :nth-child(4), .acc-tools > :nth-child(4) { --fx-d: .24s; }
.acc-grid > :nth-child(n+5), .acc-tools > :nth-child(n+5) { --fx-d: .32s; }

/* Wo der Browser Scroll-Timelines kann, animieren Kacheln beim Scrollen in
   den Viewport (statt alle beim Laden) — exakt wie die Landing Page. */
@supports (animation-timeline: view()) {
  .acc-tools .acc-tool, .acc-grid .acc-card, .acc-fin, .acc-limits {
    animation-duration: auto; animation-delay: 0s;
    animation-timeline: view(); animation-range: entry 0% entry 80%;
  }
}

.acc-mono { font-family: 'Space Mono', monospace; }
.acc-disp { font-family: 'Space Grotesk', sans-serif; font-weight: 700; letter-spacing: -0.02em; }

.acc-eyebrow {
  font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 0.14em;
  text-transform: uppercase; display: inline-flex; align-items: center; gap: 7px; color: #A3E635;
}
.acc-eyebrow.on-paper { color: #14532D; }
.acc-dot { width: 7px; height: 7px; background: #A3E635; border-radius: var(--r); display: inline-block;
  animation: accPulse 2.6s ease-in-out infinite; }

/* --- Topbar: sticky mit Blur ---------------------------------------------- */
.acc-topbar {
  position: sticky; top: 8px; z-index: 99;
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 12px 20px; border: 1px solid rgba(255,255,255,0.10); border-radius: var(--r);
  margin-bottom: 20px;
  background: rgba(8,23,17,0.72);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.acc-logo { width: 24px; height: 24px; background: #A3E635; border-radius: var(--r);
  display: inline-flex; align-items: center; justify-content: center; color: #14532D; font-weight: 700; }
.acc-topbar .acc-sub { font-size: 12px; color: #9CA3AF; }
.acc-chip { font-family: 'Space Mono', monospace; font-size: 11px; color: #A3E635;
  background: rgba(163,230,53,0.10); border: 1px solid rgba(163,230,53,0.25);
  padding: 4px 10px; border-radius: var(--r); white-space: nowrap; }

/* --- Hero: Off-White mit Lime-Kreidestrich + gelbem KI-Funke --------------- */
.acc-hero { background: #FAFAF5; color: #0A0F0C; border-radius: var(--r); padding: 30px 26px;
  margin-bottom: 14px; position: relative; overflow: hidden; }
.acc-hero::after { content: ""; position: absolute; right: -30px; top: 40px; width: 210px; height: 12px;
  background: #A3E635; border-radius: var(--r); transform: rotate(-18deg); pointer-events: none; }
.acc-hero::before { content: ""; position: absolute; right: 42px; top: 22px; width: 9px; height: 9px;
  background: #FDE047; border-radius: var(--r); transform: rotate(12deg); pointer-events: none; }
.acc-hero h1 { color: #0A0F0C !important; font-size: 34px; line-height: 1.06; margin: 12px 0 0; }
.acc-hero h1 .mark { background: linear-gradient(transparent 60%, #A3E635 60%); padding: 0 2px; }
.acc-hero p { color: #6B7280; font-size: 15px; margin: 12px 0 0; max-width: 520px; }

/* --- Vitals ---------------------------------------------------------------- */
.acc-vitals { background: #081711; border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r); padding: 18px 24px; margin-bottom: 26px;
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.acc-vital-num { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 28px; color: #FAFAF5; line-height: 1; }
.acc-vital-num.lime { color: #A3E635; }
.acc-vital-lbl { font-size: 11px; color: #9CA3AF; padding-top: 6px; margin-top: 4px;
  border-top: 2px solid rgba(255,255,255,0.14); }
.acc-vital-lbl.lime { border-top-color: #A3E635; }

/* --- Projekt-Karten -------------------------------------------------------- */
.acc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.acc-card { background: #14532D; border: 1px solid rgba(255,255,255,0.06); border-radius: var(--r);
  padding: 16px 17px; text-decoration: none !important; display: block;
  transition: transform 0.25s var(--fx-ease), box-shadow 0.25s, border-color 0.25s; }
.acc-card, .acc-card * { text-decoration: none !important; }
.acc-card:hover { border-color: rgba(163,230,53,0.55); transform: translateY(-3px);
  box-shadow: 0 14px 30px rgba(0,0,0,0.32); }
.acc-card .name { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 16px; color: #FAFAF5; }
.acc-card .desc { font-size: 12px; color: #9CA3AF; margin: 8px 0 12px; }
.acc-card .arrow { color: #9CA3AF; transition: transform 0.18s ease, color 0.18s ease; }
.acc-card:hover .arrow { transform: translate(2px, -2px); color: #A3E635; }
.acc-card.hero { background: #A3E635; border: none; }
.acc-card.hero:hover { box-shadow: 0 14px 34px rgba(163,230,53,0.28); }
.acc-card.hero .name { color: #14532D; }
.acc-card.hero .desc { color: rgba(20,83,45,0.85); }
.acc-card.hero .arrow { color: #14532D; }
.acc-card.hero:hover .arrow { color: #14532D; }

.acc-badge { font-family: 'Space Mono', monospace; font-size: 11px; padding: 3px 10px;
  border-radius: var(--r); background: #081711; }
.acc-card.hero .acc-badge { background: #14532D; }

.acc-section-h { font-size: 22px; color: #FAFAF5; margin: 10px 0 16px; }

.acc-placeholder { background: #14532D; border: 1px dashed rgba(255,255,255,0.14);
  border-radius: var(--r); padding: 16px 18px; margin-bottom: 12px; }
.acc-placeholder .t { font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: #FAFAF5; }
.acc-placeholder .n { font-size: 12px; color: #9CA3AF; margin-top: 4px; }

/* --- Tool-Launcher / Repo-Kacheln (USP-Look: Lime-Oberkante) ---------------- */
.acc-tools { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr)); gap: 12px; }
.acc-tool { background: #14532D; border: 1px solid rgba(255,255,255,0.06);
  border-top: 3px solid #A3E635; border-radius: var(--r);
  padding: 16px 17px; text-decoration: none !important; display: block;
  transition: transform 0.25s var(--fx-ease), box-shadow 0.25s, border-color 0.25s; }
.acc-tool, .acc-tool * { text-decoration: none !important; }
.acc-tool:hover { border-color: rgba(163,230,53,0.55); border-top-color: #A3E635;
  transform: translateY(-3px); box-shadow: 0 14px 30px rgba(0,0,0,0.32); }
.acc-tool .ic { font-size: 26px; line-height: 1; }
.acc-tool .tn { font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: #FAFAF5; margin-top: 10px; }
.acc-tool .td { font-size: 12px; color: #9CA3AF; margin-top: 4px; }
.acc-tool .meta { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 11px; align-items: center; }
.acc-tool .meta .acc-badge { display: inline-block; }
.acc-tool.geplant { border-style: dashed; border-top-style: solid; opacity: 0.65; }
.acc-tool.geplant:hover { transform: none; box-shadow: none; }

/* --- Skills ----------------------------------------------------------------- */
.acc-skill { margin-bottom: 11px; }
.acc-skill-top { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }
.acc-skill-name { font-size: 13px; color: #FAFAF5; }
.acc-skill-lvl { font-family: 'Space Mono', monospace; font-size: 12px; color: #9CA3AF; }
.acc-track { height: 7px; background: #081711; border-radius: var(--r); overflow: hidden; }
.acc-fill { height: 100%; background: #A3E635; border-radius: var(--r);
  animation: accGrowX 1.1s var(--fx-ease) both; }
.acc-cat { font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 0.12em;
  text-transform: uppercase; color: rgba(250,250,245,0.4); margin: 14px 0 8px; }

/* --- Token: Limit-Zeilen (wie Claude → Einstellungen → Nutzung) ------------- */
.acc-limits { background: #081711; border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r); padding: 18px 20px 8px; margin-bottom: 14px; }
.acc-limit { margin-bottom: 16px; }
.acc-limit .row { display: flex; justify-content: space-between; align-items: baseline;
  gap: 10px; margin-bottom: 7px; flex-wrap: wrap; }
.acc-limit .lbl { font-size: 14px; color: #FAFAF5; font-weight: 500; }
.acc-limit .pct { font-family: 'Space Mono', monospace; font-size: 13px; color: #FAFAF5; }
.acc-limit .pct b { color: #A3E635; font-weight: 700; }
.acc-limit .bar { height: 9px; background: #14281D; border-radius: var(--r); overflow: hidden; }
.acc-limit .bar > div { height: 100%; border-radius: var(--r);
  animation: accGrowX 1.1s var(--fx-ease) both; }
.acc-limit .sub { font-size: 11.5px; color: #9CA3AF; margin-top: 6px; }

/* --- Token-Chart ------------------------------------------------------------ */
.acc-ubar { width: 100%; background: #A3E635;
  border-radius: var(--r) var(--r) 0 0; transform-origin: bottom;
  animation: accGrowY 0.9s var(--fx-ease) both; }

/* --- Finanzen / CTA ---------------------------------------------------------- */
.acc-fin { background: #081711; border-radius: var(--r); padding: 18px 20px; }
.acc-cta { display: inline-flex; align-items: center; gap: 6px; background: #A3E635; color: #14532D !important;
  font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 14px; padding: 9px 16px;
  border-radius: var(--r); text-decoration: none !important; margin-top: 14px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease; }
.acc-cta:hover { background: #FDE047; transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(163,230,53,0.25); }
.acc-subline { margin-top: 14px; font-size: 13px; color: #9CA3AF; }
.acc-subline b { color: #FAFAF5; font-weight: 500; }

/* --- Kanban ------------------------------------------------------------------ */
.acc-kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.acc-kcol { background: #081711; border-radius: var(--r); padding: 12px 12px 6px; }
.acc-kcol-h { font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 0.1em;
  text-transform: uppercase; color: #9CA3AF; margin-bottom: 10px; display: flex; justify-content: space-between; }
.acc-kitem { background: #14532D; border-radius: var(--r); padding: 8px 11px; font-size: 12.5px;
  color: #FAFAF5; margin-bottom: 7px; border-left: 3px solid rgba(255,255,255,0.14);
  transition: transform 0.15s ease, background 0.15s ease; }
.acc-kitem:hover { transform: translateX(3px); background: #1A6437; }
.acc-kitem.act { border-left-color: #A3E635; }
.acc-kitem.done { color: rgba(250,250,245,0.45); text-decoration: line-through; border-left-color: rgba(255,255,255,0.25); }

/* --- Footer ------------------------------------------------------------------ */
.acc-footer { margin-top: 30px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08);
  display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap;
  font-family: 'Space Mono', monospace; font-size: 11px; color: rgba(250,250,245,0.45); }

/* Custom-Component-iframes (z. B. Kanban) immer auf Containerbreite */
iframe[data-testid="stCustomComponentV1"] { width: 100% !important; }

footer, #MainMenu, header { visibility: hidden; }

/* --- Responsive: Laptop ------------------------------------------------------ */
@media (max-width: 1000px) {
  .block-container { padding-left: 1.2rem; padding-right: 1.2rem; }
}

/* --- Responsive: Handy ------------------------------------------------------- */
@media (max-width: 760px) {
  .block-container { padding: 0.8rem 0.9rem 3rem; }
  .acc-topbar { top: 4px; padding: 10px 14px; }
  .acc-topbar .acc-sub { display: none; }
  .acc-hero { padding: 24px 20px; }
  .acc-hero h1 { font-size: 27px; }
  .acc-hero p { font-size: 14px; }
  .acc-vitals { grid-template-columns: repeat(2, 1fr); padding: 16px 18px; gap: 14px; }
  .acc-vital-num { font-size: 23px; }
  .acc-grid { grid-template-columns: 1fr; }
  .acc-tools { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .acc-kanban { grid-template-columns: 1fr; }
  .acc-section-h { font-size: 19px; }
  /* Hover gibt es am Handy nicht — Karten bleiben ruhig */
  .acc-card:hover, .acc-tool:hover { transform: none; }
}

@media (max-width: 400px) {
  .acc-tools { grid-template-columns: 1fr; }
}

/* --- Barrierefreiheit --------------------------------------------------------- */
a:focus-visible, button:focus-visible { outline: 2px solid #A3E635; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def kanban_sortable_css(done_indices: list[int] | None = None) -> str:
    """CSS für die streamlit-sortables-Komponente (läuft im eigenen iframe).

    done_indices: Spalten (0-basiert), deren Karten als erledigt dargestellt
    werden (durchgestrichen, gedimmt) — typischerweise die Erledigt-Spalte.
    """
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Space+Mono:wght@400;700&display=swap');
    body { margin: 0; font-family: 'Inter', sans-serif; }
    .sortable-component { display: flex !important; gap: 12px; align-items: stretch;
      border: none !important; padding: 0 !important; background: transparent !important; }
    .sortable-container { flex: 1 1 0; min-width: 0; width: 100%; background: #081711 !important;
      border: none !important; border-radius: 2px; padding: 12px 12px 6px !important;
      box-sizing: border-box; }
    .sortable-container-header { background: transparent !important; color: #9CA3AF !important;
      font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 0.1em;
      text-transform: uppercase; padding: 0 0 10px 2px !important; }
    .sortable-container-body { background: transparent !important; min-height: 44px; padding: 0 !important; }
    .sortable-item, .sortable-item:hover { background: #14532D !important; color: #FAFAF5 !important;
      border: none !important; border-left: 3px solid rgba(255,255,255,0.14) !important;
      border-radius: 2px; padding: 8px 11px !important; font-size: 12.5px; margin-bottom: 7px;
      cursor: grab; transition: transform 0.15s ease, background 0.15s ease, box-shadow 0.15s ease; }
    .sortable-item:hover { background: #1A6437 !important; transform: translateX(3px);
      border-left-color: #A3E635 !important; }
    .sortable-item.dragging { opacity: 0.9; transform: rotate(1.5deg) scale(1.02);
      box-shadow: 0 14px 30px rgba(0,0,0,0.4); cursor: grabbing;
      border-left-color: #A3E635 !important; }
    @media (max-width: 700px) { .sortable-component { flex-direction: column; } }
    """
    # nth-of-type statt nth-child: die Komponente rendert das Custom-CSS als
    # <style>-Tag als ERSTES Kind neben den Spalten-Divs — nth-child wäre
    # dadurch um eins verschoben und würde die falsche Spalte durchstreichen.
    for i in done_indices or []:
        css += (
            f"\n    .sortable-container:nth-of-type({i + 1}) .sortable-item"
            " { opacity: 0.55; text-decoration: line-through; }"
            f"\n    .sortable-container:nth-of-type({i + 1}) .sortable-item:hover"
            " { opacity: 0.8; }"
        )
    return css
