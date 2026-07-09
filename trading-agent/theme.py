"""Basel-AI Design für den Trading Agent — passend zum AI Command Center.

Firmen-Branding Basel-AI Consulting (Vault → 00 Kontext/Branding.md):
Deep Forest + Waldgrün, Lime als Akzent, Space Grotesk / Inter / Space Mono.
Setzt zusätzlich ein transparentes Plotly-Template, damit die Charts auf dem
Grün sitzen. `inject()` einmalig direkt nach st.set_page_config aufrufen.
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Plotly-Template global auf den Basel-AI-Look (transparent, Lime-Akzente).
# Template-Key bleibt "forest", damit bestehende Verweise weiter funktionieren.
pio.templates["forest"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAF5", family="Inter, sans-serif"),
        colorway=["#A3E635", "#FDE047", "#34D399", "#FAFAF5", "#9CA3AF", "#65A30D"],
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.14)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.14)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
)
pio.templates.default = "forest"


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500&family=Space+Mono:wght@400;700&display=swap');

.stApp { background: #0C1F15; }
.block-container { padding-top: 2.2rem; }

html, body, .stApp, .stMarkdown, p, span, div, label { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.02em; }

/* Kennzahlen (st.metric) */
[data-testid="stMetricValue"] { font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #FAFAF5; }
[data-testid="stMetricLabel"] { color: #9CA3AF !important; }
[data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace; }

/* Tabs: Lime-Akzent auf aktiv (nur der Unterstrich, nicht das Panel!) */
button[data-baseweb="tab"] { font-family: 'Space Grotesk', sans-serif; }
button[data-baseweb="tab"][aria-selected="true"] { color: #A3E635 !important; }
[data-baseweb="tab-highlight"] { background-color: #A3E635 !important; }

/* Karten/Container */
[data-testid="stMetric"], .stDataFrame, [data-testid="stExpander"] {
  background: #14532D; border-radius: 12px; }
[data-testid="stMetric"] { padding: 12px 14px; border: 1px solid rgba(255,255,255,0.06); }

/* Tabellen dunkel */
[data-testid="stTable"] { background: #14532D; }

footer, #MainMenu { visibility: hidden; }
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
