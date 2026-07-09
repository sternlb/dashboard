"""Trading-Agent Dashboard (Step 1 + 2).

Tabs:
  📊 Mein Depot          — Analyse der ING-Positionen inkl. Research-Ratings & Energie-Röntgen
  🎯 Strategie & Backtest — zwei geführte Profile (ETF mittelfristig, Aktien kurzfristig)
  🔭 Chancen             — Lücken-Kandidaten zur These (wöchentlich aktualisiert) + Backtest

Run with:  streamlit run app.py
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from trading_agent import (backtest, config, data, etf_returns, favorites,
                           indicators, portfolio, profiles, research, signals)

st.set_page_config(page_title="Trading Agent", page_icon="📈", layout="wide")

import theme  # Forest/Lime Look (passend zum AI Command Center)
theme.inject()

HOLDINGS_PATH = "data/holdings.csv"
HOLDINGS_FALLBACK = "data/holdings.example.csv"
SNAPSHOT_PATH = "data/watchlist_snapshot.csv"
STAMP_PATH = "data/last_update.txt"
FAV_PATH = "data/favorites.json"


# --- cached wrappers (Streamlit caching lives here, not in the data layer) ---
@st.cache_data(ttl=120, show_spinner=False)
def cached_history(ticker: str, period: str) -> pd.DataFrame:
    return data.get_history(ticker, period=period)


@st.cache_data(ttl=60, show_spinner=False)
def cached_quote(ticker: str):
    return data.get_quote(ticker)


@st.cache_data(ttl=60, show_spinner=False)
def cached_watchlist(tickers: tuple[str, ...]) -> pd.DataFrame:
    return data.get_watchlist_table(list(tickers))


@st.cache_data(ttl=3600, show_spinner=False)
def cached_tr_series(ticker: str) -> pd.Series:
    return data.get_total_return_series(ticker, period="10y")


def label(ticker: str) -> str:
    name = config.DISPLAY_NAMES.get(ticker)
    return f"{ticker} · {name}" if name else ticker


def load_holdings() -> tuple[pd.DataFrame, bool]:
    if os.path.exists(HOLDINGS_PATH):
        return portfolio.load_holdings(HOLDINGS_PATH), False
    if os.path.exists(HOLDINGS_FALLBACK):
        return portfolio.load_holdings(HOLDINGS_FALLBACK), True
    return pd.DataFrame(columns=portfolio.REQUIRED), True


def guarded(render_fn, *args, **kwargs) -> None:
    """Führt eine Render-Funktion aus, ohne dass ein Fehler die restliche Seite
    (und damit alle folgenden Tabs) mit in den Abgrund reißt. Typischer Fall:
    Yahoo-Finance-Rate-Limit wirft mitten im Chancen-Tab eine Exception —
    vorher blieb dann auch das Order Sheet komplett leer."""
    try:
        render_fn(*args, **kwargs)
    except Exception as ex:  # noqa: BLE001 — bewusst breit: UI soll weiterleben
        st.error(f"⚠️ Ansicht konnte nicht geladen werden ({type(ex).__name__}). "
                 "Meist ist das ein vorübergehendes Yahoo-Finance-Limit — kurz warten "
                 "und in der Sidebar „🔄 Daten neu laden“ klicken.")


def safe_price(ticker: str) -> float | None:
    try:
        return cached_quote(ticker).price
    except Exception:
        return None


def load_snapshot() -> tuple[pd.DataFrame | None, str]:
    if os.path.exists(SNAPSHOT_PATH):
        df = pd.read_csv(SNAPSHOT_PATH)
        stamp = open(STAMP_PATH, encoding="utf-8").read().strip() if os.path.exists(STAMP_PATH) else "unbekannt"
        return df, stamp
    return None, "—"


# ---------- wiederverwendbare Strategie-/Backtest-Ansicht --------------------
def render_strategy_view(ticker: str, profile, period: str, fee_bps: float, show_rsi: bool,
                         view_id: str = "") -> None:
    q = cached_quote(ticker)
    hist = cached_history(ticker, period)

    position = bt = entries = exits = None
    if not hist.empty:
        position = profile.strategy(hist)
        entries, exits = signals.position_changes(position)
        bt = backtest.run_backtest(hist["Close"], position, fee_bps=fee_bps)

    hcol = st.columns([6, 1])
    hcol[0].subheader(label(ticker))
    is_fav = ticker in fav["tickers"]
    if hcol[1].button("⭐ Favorit" if is_fav else "☆ Favorit", key=f"fav_{view_id}_{ticker}",
                      help="Per Klick als Favorit fürs Order Sheet markieren / entfernen"):
        if is_fav:
            fav["tickers"].remove(ticker)
        else:
            fav["tickers"].append(ticker)
        favorites.save(FAV_PATH, fav)
        st.rerun()

    info = research.instrument(ticker)
    if info:
        with st.container(border=True):
            st.markdown(f"**🏷️ Was steckt dahinter — {info['name']}**  ·  _{info['art']}_")
            st.markdown(info["desc"])

    cur = q.currency or ""
    c = st.columns(4)
    c[0].metric("Kurs", f"{q.price:,.2f} {cur}" if q.price is not None else "—",
                f"{q.change_pct:+.2f} %" if q.change_pct is not None else None)
    if not hist.empty:
        closes = hist["Close"].dropna()
        period_chg = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
                      if len(closes) >= 2 and closes.iloc[0] else None)
        c[1].metric("Zeitraum-Δ", f"{period_chg:+.2f} %" if period_chg is not None else "—")
        c[2].metric("Hoch", f"{hist['High'].max():,.2f}")
        c[3].metric("Tief", f"{hist['Low'].min():,.2f}")

    if hist.empty:
        st.warning(f"Keine Daten für {ticker} im Zeitraum {period}.")
        return

    close = hist["Close"]
    show_macd = profile.kind == "macd"
    n_extra = int(show_rsi) + int(show_macd)
    row_heights = [0.62] + [0.38 / n_extra] * n_extra if n_extra else [1.0]
    fig = make_subplots(rows=1 + n_extra, cols=1, shared_xaxes=True,
                        vertical_spacing=0.04, row_heights=row_heights)
    fig.add_trace(go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
                  low=hist["Low"], close=hist["Close"], name="Kurs"), row=1, col=1)
    if profile.kind == "sma":
        fig.add_trace(go.Scatter(x=hist.index, y=indicators.sma(close, profile.fast),
                      name=f"SMA {profile.fast}", line=dict(width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=indicators.sma(close, profile.slow),
                      name=f"SMA {profile.slow}", line=dict(width=1.4)), row=1, col=1)
    if entries is not None and len(entries):
        fig.add_trace(go.Scatter(x=entries, y=close.reindex(entries), name="Kauf", mode="markers",
                      marker=dict(symbol="triangle-up", size=11, color="#16a34a")), row=1, col=1)
    if exits is not None and len(exits):
        fig.add_trace(go.Scatter(x=exits, y=close.reindex(exits), name="Verkauf", mode="markers",
                      marker=dict(symbol="triangle-down", size=11, color="#dc2626")), row=1, col=1)
    next_row = 2
    if show_rsi:
        fig.add_trace(go.Scatter(x=hist.index, y=indicators.rsi(close), name="RSI",
                      line=dict(width=1)), row=next_row, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=next_row, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=next_row, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=next_row, col=1)
        next_row += 1
    if show_macd:
        mc = indicators.macd(close)
        fig.add_trace(go.Bar(x=hist.index, y=mc["histogram"], name="MACD-Hist"), row=next_row, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=mc["macd"], name="MACD", line=dict(width=1)), row=next_row, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=mc["signal"], name="Signal", line=dict(width=1)), row=next_row, col=1)
        fig.update_yaxes(title_text="MACD", row=next_row, col=1)
    fig.update_layout(height=320 + 150 * n_extra, margin=dict(l=0, r=0, t=10, b=0),
                      xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, width="stretch")

    if bt is None:
        return
    m = bt.metrics
    H = profiles.METRIC_HELP
    r1 = st.columns(4)
    r1[0].metric("Strategie-Rendite", f"{m['total_return']*100:+.1f} %", help=H["total_return"])
    r1[1].metric("Buy & Hold", f"{m['buy_hold_return']*100:+.1f} %", help=H["buy_hold_return"])
    r1[2].metric("Alpha", f"{m['alpha']*100:+.1f} pp", help=H["alpha"])
    r1[3].metric("Sharpe", f"{m['sharpe']:.2f}", help=H["sharpe"])
    r2 = st.columns(4)
    r2[0].metric("Max. Drawdown", f"{m['max_drawdown']*100:.1f} %", help=H["max_drawdown"])
    r2[1].metric("CAGR p.a.", f"{m['cagr']*100:+.1f} %", help=H["cagr"])
    r2[2].metric("Trefferquote", f"{m['win_rate']*100:.0f} %", help=H["win_rate"])
    r2[3].metric("Trades", f"{int(m['trades'])}", help=H["trades"])

    eq = go.Figure()
    eq.add_trace(go.Scatter(x=bt.equity.index, y=bt.equity, name="Strategie",
                 line=dict(width=2, color="#2563eb")))
    eq.add_trace(go.Scatter(x=bt.buy_hold.index, y=bt.buy_hold, name="Buy & Hold",
                 line=dict(width=1.5, color="#9ca3af", dash="dot")))
    eq.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                     yaxis_title="Kapital (Start = 1.0)",
                     legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(eq, width="stretch")
    st.caption(f"Long/Flat, Einstieg zur nächsten Kerze. Gebühr {fee_bps:.0f} bp/Trade. "
               "Vergangene Performance ≠ Zukunft. Keine Anlageberatung.")


# ---------------------------------- Sidebar ----------------------------------
st.sidebar.title("📈 Trading Agent")
st.sidebar.caption("Step 1+2 — Depot, Strategie & Chancen")

st.sidebar.markdown("### 🎯 Strategie-Profil")
st.sidebar.caption("gilt für Tabs „Strategie“ und „Chancen“")
prof_key = st.sidebar.radio(
    "Profil", list(profiles.PROFILES.keys()),
    format_func=lambda k: f"{profiles.PROFILES[k].emoji} {profiles.PROFILES[k].name}",
    label_visibility="collapsed",
)
profile = profiles.PROFILES[prof_key]
selected = st.sidebar.selectbox("Wert", profile.universe, format_func=label, key=f"asset_{prof_key}")
periods = list(data.PERIOD_INTERVAL.keys())
period = st.sidebar.select_slider("Zeitraum", options=periods, value=profile.default_period, key=f"period_{prof_key}")
fee_bps = st.sidebar.number_input("Gebühr je Trade (Basispunkte)", min_value=0.0, max_value=100.0,
                                  value=profile.fee_bps, step=1.0, key=f"fee_{prof_key}")
show_rsi = st.sidebar.checkbox("RSI (14) einblenden", value=False)
if st.sidebar.button("🔄 Daten neu laden"):
    st.cache_data.clear()
    st.rerun()


fav = favorites.load(FAV_PATH)
cand_by_ticker = {c["ticker"]: c for c in research.CANDIDATES}

holdings, is_example = load_holdings()
enr = portfolio.enrich(holdings) if not holdings.empty else holdings
pos_by_isin = {str(r["isin"]): r for _, r in enr.iterrows()} if not enr.empty else {}

tab_depot, tab_strategy, tab_chancen, tab_order = st.tabs(
    ["📊 Mein Depot", "🎯 Strategie & Backtest", "🔭 Chancen", "📝 Order Sheet"])


# ============================== TAB: MEIN DEPOT ==============================
with tab_depot:
    if is_example:
        st.warning(f"⚠️ **Beispiel-Depot** — trage deine ING-Positionen in `{HOLDINGS_PATH}` ein.")

    if holdings.empty:
        st.info("Keine Positionen vorhanden.")
    else:
        tot = portfolio.totals(enr)

        st.subheader("Überblick")
        k = st.columns(5)
        k[0].metric("Depotwert", f"{tot['value']:,.0f} €")
        k[1].metric("Einstand", f"{tot['cost']:,.0f} €")
        k[2].metric("G/V", f"{tot['pnl']:+,.0f} €", f"{tot['pnl_pct']:+.1f} %")
        k[3].metric("Positionen", f"{tot['positions']}")
        k[4].metric("Größte Position", f"{tot['top_weight']:.0f} %")

        ins = portfolio.insights(enr)
        if ins:
            st.markdown("**Was auffällt:**")
            for line in ins:
                st.markdown(f"- {line}")
        for flag in portfolio.concentration_flags(enr):
            st.warning(f"⚠️ Klumpenrisiko: {flag}")

        # ---- Struktur ----
        st.subheader("Struktur")
        col_a, col_b = st.columns(2)
        by_theme = portfolio.allocation(enr, "theme")
        pie1 = go.Figure(go.Pie(labels=by_theme.index, values=by_theme.values, hole=0.45, sort=False))
        pie1.update_layout(title="Nach Thema", height=340, margin=dict(l=0, r=0, t=40, b=0))
        col_a.plotly_chart(pie1, width="stretch")
        by_class = portfolio.allocation(enr, "asset_class")
        pie2 = go.Figure(go.Pie(labels=by_class.index, values=by_class.values, hole=0.45))
        pie2.update_layout(title="Nach Anlageklasse", height=340, margin=dict(l=0, r=0, t=40, b=0))
        col_b.plotly_chart(pie2, width="stretch")

        # ---- Positionen + Research-Ratings ----
        st.subheader("Positionen & Bewertung")
        st.caption("⭐ anklicken markiert eine Position fürs Order Sheet (z. B. nachkaufen / reduzieren).")
        rated = enr.copy()
        rated["Bewertung"] = rated["isin"].map(lambda i: f"{research.rating_for(i)['verdict']} {research.rating_for(i)['label']}")
        rated["These-Fit"] = rated["isin"].map(lambda i: research.rating_for(i)["fit"])
        order_isins = [str(i) for i in rated["isin"]]
        disp = pd.DataFrame({
            "⭐": [i in fav["depot"] for i in order_isins],
            "Name": rated["name"].values,
            "Bewertung": rated["Bewertung"].values,
            "These-Fit": rated["These-Fit"].values,
            "Thema": rated["theme"].values,
            "Wert €": rated["value_eur"].values,
            "Gewicht %": rated["weight_pct"].values,
            "G/V %": rated["pnl_pct"].values,
        })
        edited = st.data_editor(
            disp, hide_index=True, width="stretch", key="depot_editor",
            column_config={
                "⭐": st.column_config.CheckboxColumn(help="Für Order Sheet markieren", width="small"),
                "Name": st.column_config.TextColumn(disabled=True),
                "Bewertung": st.column_config.TextColumn(disabled=True),
                "These-Fit": st.column_config.TextColumn(disabled=True),
                "Thema": st.column_config.TextColumn(disabled=True),
                "Wert €": st.column_config.NumberColumn(format="%.0f", disabled=True),
                "Gewicht %": st.column_config.NumberColumn(format="%.1f %%", disabled=True),
                "G/V %": st.column_config.NumberColumn(format="%+.1f %%", disabled=True),
            },
        )
        new_depot = [isin for isin, star in zip(order_isins, edited["⭐"]) if star]
        if set(new_depot) != set(fav["depot"]):
            fav["depot"] = new_depot
            favorites.save(FAV_PATH, fav)

        with st.expander("🔬 Einzel-Einschätzungen (Research, Juni 2026)"):
            for _, r in rated.iterrows():
                rt = research.rating_for(r["isin"])
                if rt["note"]:
                    st.markdown(f"**{rt['verdict']} {r['name']}** — _{rt['label']} · {rt['fit']}_  \n{rt['note']}")
            st.caption("Eigene Recherche, keine Anlageberatung.")

        # ---- Energie-Röntgen ----
        energy = enr[enr["isin"].isin(research.ENERGY_TYPE)].copy()
        if not energy.empty:
            st.subheader("🔎 Energie-Röntgen")
            energy["Energieart"] = energy["isin"].map(research.ENERGY_TYPE)
            grp = energy.groupby("Energieart")["value_eur"].sum().sort_values(ascending=False)
            clean = energy.loc[energy["Energieart"].str.contains("Clean|Solar"), "value_eur"].sum()
            fossil = energy.loc[energy["Energieart"].str.contains("Fossil"), "value_eur"].sum()
            e_total = energy["value_eur"].sum()
            cols = st.columns([2, 3])
            ebar = go.Figure(go.Bar(x=grp.values, y=grp.index, orientation="h",
                                    marker_color=["#16a34a", "#22c55e", "#64748b"][:len(grp)],
                                    text=[f"{v:,.0f} €" for v in grp.values], textposition="auto"))
            ebar.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0),
                               yaxis=dict(autorange="reversed"))
            cols[0].plotly_chart(ebar, width="stretch")
            cols[1].markdown(
                f"- **Energie gesamt:** {e_total:,.0f} € ({e_total/tot['value']*100:.0f} % des Depots)\n"
                f"- 🌿 **Clean/Solar:** {clean:,.0f} € ({clean/e_total*100:.0f} % der Energie) — Policy-Gegenwind 2026\n"
                f"- 🛢️ **Fossil Öl/Gas:** {fossil:,.0f} € ({fossil/e_total*100:.0f} %) — direkter Bedarfs-Profiteur + Dividenden\n"
                "- **Überlappung:** SMA Solar (Einzelaktie) liegt thematisch *über* dem Clean-Energy-ETF "
                "— doppelte Solar-Wette. Der AI-getriebene Mehrbedarf fließt dagegen eher in Nuklear/Netz "
                "(siehe Tab 🔭 Chancen)."
            )

        # ---- Brücke zu den Profilen ----
        st.subheader("Zuordnung zu den Strategie-Profilen")
        etf_val = enr.loc[enr["asset_class"] == "ETF", "value_eur"].sum()
        stock_val = enr.loc[enr["asset_class"] == "Aktie", "value_eur"].sum()
        other_val = tot["value"] - etf_val - stock_val
        mcol = st.columns(3)
        mcol[0].metric("🌱 ETF-Anteil (mittelfristig)", f"{etf_val:,.0f} €", f"{etf_val/tot['value']*100:.0f} %")
        mcol[1].metric("⚡ Aktien-Anteil (kurzfristig)", f"{stock_val:,.0f} €", f"{stock_val/tot['value']*100:.0f} %")
        mcol[2].metric("Sonstiges (Krypto)", f"{other_val:,.0f} €", f"{other_val/tot['value']*100:.0f} %")

        # ---- ETF-Erträge pro Jahr (nach Kosten) ----
        st.subheader("📈 ETF-Erträge pro Jahr (nach Kosten)")
        st.caption(
            "Total-Return-Basis (Dividenden reinvestiert). Die **TER ist im Kurs bereits "
            "verrechnet** — die Kosten-Spalten machen sie sichtbar und rechnen sie auf deine "
            "Positionsgröße um. „Seit Kauf p.a.“ und „Ø Ertrag €/Jahr“ nutzen Kaufdatum "
            "(`buy_date`) und Kaufvolumen (`cost_eur`) aus `data/holdings.csv`."
        )
        etfs = enr[enr["asset_class"] == "ETF"].copy()
        if etfs.empty:
            st.info("Keine ETFs im Depot.")
        else:
            etf_rows: list[dict] = []
            etf_series: dict[str, tuple[str, pd.Series]] = {}
            for _, r in etfs.iterrows():
                isin = str(r["isin"])
                tick = r.get("ticker") if "ticker" in etfs.columns else None
                sym = str(tick).strip() if pd.notna(tick) and str(tick).strip() else isin
                closes = cached_tr_series(sym)
                etf_series[isin] = (sym, closes)
                ter = etf_returns.ter_for(isin)
                buy_date = r.get("buy_date") if "buy_date" in etfs.columns else None
                sb = etf_returns.since_buy(float(r["cost_eur"]), float(r["value_eur"]), buy_date)
                etf_rows.append({
                    "Name": r["name"],
                    "TER %": ter,
                    "Kosten €/Jahr": ter / 100 * float(r["value_eur"]) if ter is not None else None,
                    "Ø p.a. %": etf_returns.cagr_pct(closes),
                    "Letzte 12 M %": etf_returns.last_12m_pct(closes),
                    "Seit Kauf %": sb["total_pct"],
                    "Seit Kauf p.a. %": sb["pa_pct"],
                    "Ø Ertrag €/Jahr": sb["eur_year"],
                })
            st.dataframe(
                pd.DataFrame(etf_rows), hide_index=True, width="stretch",
                column_config={
                    "TER %": st.column_config.NumberColumn(format="%.2f %%",
                             help="Laufende Fondskosten p.a. — bereits im Kurs verrechnet"),
                    "Kosten €/Jahr": st.column_config.NumberColumn(format="%.0f €",
                             help="TER × aktueller Positionswert"),
                    "Ø p.a. %": st.column_config.NumberColumn(format="%+.1f %%",
                             help="Geometrischer Durchschnitt über die verfügbare Kurshistorie (bis 10 J.)"),
                    "Letzte 12 M %": st.column_config.NumberColumn(format="%+.1f %%",
                             help="Rendite der letzten 12 Monate"),
                    "Seit Kauf %": st.column_config.NumberColumn(format="%+.1f %%",
                             help="Gesamtrendite auf dein Kaufvolumen (Einstand)"),
                    "Seit Kauf p.a. %": st.column_config.NumberColumn(format="%+.1f %%",
                             help="Auf Jahre umgerechnet — braucht buy_date in holdings.csv"),
                    "Ø Ertrag €/Jahr": st.column_config.NumberColumn(format="%+.0f €",
                             help="Gewinn/Verlust geteilt durch Haltedauer — braucht buy_date"),
                },
            )
            if "buy_date" not in etfs.columns or etfs["buy_date"].isna().all():
                st.info("💡 Trage das Kaufdatum als Spalte `buy_date` (JJJJ-MM-TT) in "
                        "`data/holdings.csv` ein, dann füllen sich „Seit Kauf p.a.“ und "
                        "„Ø Ertrag €/Jahr“.")

            det = st.selectbox("Jahresrenditen im Detail", list(etfs["name"]), key="etf_detail")
            drow = etfs.loc[etfs["name"] == det].iloc[0]
            sym, closes = etf_series[str(drow["isin"])]
            yr = etf_returns.yearly_returns(closes)
            if yr.empty:
                st.info(f"Zu wenig Kurshistorie für eine Jahresdarstellung ({sym}).")
            else:
                cur_year = pd.Timestamp.now().year
                labels = [f"{y} YTD" if y == cur_year else str(y) for y in yr.index]
                bar = go.Figure(go.Bar(
                    x=labels, y=yr.values,
                    marker_color=["#A3E635" if v >= 0 else "#E0997B" for v in yr.values],
                    text=[f"{v:+.1f} %" for v in yr.values], textposition="outside"))
                avg = etf_returns.cagr_pct(closes)
                if avg is not None:
                    bar.add_hline(y=avg, line_dash="dot", line_color="#FAFAF5",
                                  annotation_text=f"Ø {avg:+.1f} % p.a.")
                bar.update_layout(height=300, margin=dict(l=0, r=0, t=24, b=0),
                                  yaxis_title="Rendite %")
                st.plotly_chart(bar, width="stretch", key="etf_year_chart")
                dter = etf_returns.ter_for(str(drow["isin"]))
                st.caption(f"Yahoo-Symbol `{sym}` · " +
                           (f"TER {dter:.2f} % p.a. ist in den Kursen bereits enthalten."
                            if dter is not None else
                            "TER unbekannt — in `trading_agent/etf_returns.py` ergänzen."))

    # ---- Watchlist Marktüberblick ----
    st.divider()
    st.subheader("Watchlist — Marktüberblick")
    for group, tickers in config.WATCHLIST.items():
        table = cached_watchlist(tuple(tickers))
        if table.empty:
            continue
        table["Name"] = table["Ticker"].map(lambda t: config.DISPLAY_NAMES.get(t, ""))
        st.markdown(f"**{group}**")
        st.dataframe(table[["Ticker", "Name", "Kurs", "Veränderung %"]], hide_index=True, width="stretch",
                     column_config={"Kurs": st.column_config.NumberColumn(format="%.2f"),
                                    "Veränderung %": st.column_config.NumberColumn(format="%+.2f %%")})
    st.caption("Datenquelle: Yahoo Finance · Kurse verzögert · keine Anlageberatung")


# ========================= TAB: STRATEGIE & BACKTEST =========================
with tab_strategy:
    st.subheader(f"{profile.emoji} {profile.name}")
    i = st.columns(4)
    i[0].markdown(f"**Horizont**\n\n{profile.horizon}")
    i[1].markdown(f"**Anlageklasse**\n\n{profile.asset_class}")
    i[2].markdown(f"**Haltedauer**\n\n{profile.holding}")
    i[3].markdown(f"**Handelsfrequenz**\n\n{profile.turnover}")
    with st.expander("ℹ️ Strategie verstehen & beurteilen", expanded=True):
        st.markdown(f"**Was sie macht** — {profile.description}")
        st.markdown(f"**Warum** — {profile.rationale}")
        st.markdown(f"**Parameter** — `{profile.param_text}`")
        st.markdown(f"✅ **Stark wenn:** {profile.best_when}")
        st.markdown(f"⚠️ **Schwach wenn:** {profile.weak_when}")
        pc = st.columns(2)
        pc[0].markdown("**Vorteile**\n" + "\n".join(f"- {x}" for x in profile.pros))
        pc[1].markdown("**Nachteile**\n" + "\n".join(f"- {x}" for x in profile.cons))
        st.info(f"**So beurteilst du es:** {profile.how_to_judge}")
    st.divider()
    guarded(render_strategy_view, selected, profile, period, fee_bps, show_rsi, view_id="strat")
    with st.expander("📖 Kennzahlen-Glossar"):
        for kk, txt in profiles.METRIC_HELP.items():
            st.markdown(f"- **{kk}** — {txt}")


# ============================== TAB: CHANCEN ================================
with tab_chancen:
    st.subheader("🔭 Lücken-Kandidaten zur These")
    st.caption("Kaufbare UCITS-Alternativen zu deinen Thesen (Humanoide, AI-Strombedarf, El Niño 2026). "
               "Analyse-Symbol = liquides Yahoo-Ticker; Kauf über das UCITS-Pendant bei ING.")

    with st.expander("🌊 These: Super El Niño 2026", expanded=True):
        st.markdown(research.EL_NINO_NOTE)

    snap, stamp = load_snapshot()
    st.markdown(f"🕒 **Watchlist-Stand:** {stamp}  ·  _automatisches Update jeden Montag (Windows-Task)_")

    if snap is not None and not snap.empty:
        cols = [c for c in ["gruppe", "name", "theme", "Kurs", "1W %", "1M %", "Signal", "kaufbar"] if c in snap.columns]
        show = snap[cols].rename(columns={"gruppe": "Gruppe", "name": "Name", "theme": "Thema"})
        st.dataframe(show, hide_index=True, width="stretch", column_config={
            "Kurs": st.column_config.NumberColumn(format="%.2f"),
            "1W %": st.column_config.NumberColumn(format="%+.1f %%"),
            "1M %": st.column_config.NumberColumn(format="%+.1f %%"),
        })
        with st.expander("💡 Warum diese Kandidaten?"):
            for _, r in snap.iterrows():
                st.markdown(f"- **{r['name']}** ({r['theme']}) — {r['warum']}  \n  _kaufbar: {r['kaufbar']}_")
    else:
        st.info("Noch kein Snapshot. Führe `update_watchlist.py` aus oder warte aufs Montags-Update.")

    st.divider()
    st.markdown("**Kandidat im Detail** — Chart + Backtest. Mit dem ☆-Stern oben als Favorit markieren.")
    cand_labels = {c["ticker"]: f"{c['ticker']} · {c['name']}" for c in research.CANDIDATES}
    chosen = st.selectbox("Kandidat", list(cand_by_ticker.keys()),
                          format_func=lambda t: cand_labels.get(t, t))
    guarded(render_strategy_view, chosen, profile, period, fee_bps, show_rsi, view_id="chance")


# ============================== TAB: ORDER SHEET ============================
with tab_order:
    st.subheader("📝 Order Sheet — deine Favoriten")
    st.caption("Planungshilfe, **kein Auftrag**. Quelle „Vorschlag“ = neue Idee (Chancen-Tab), "
               "Quelle „Depot“ = bestehende Position. Aktion & Betrag wählst du; die Order "
               "platzierst du selbst bei ING. Wird automatisch gespeichert.")

    ACTIONS = ["Kauf (neu)", "Nachkaufen", "Reduzieren", "Halten/Beobachten"]
    rows = []
    # 1) favorisierte Ticker (Chancen-Vorschläge ODER Strategie-Werte)
    for t in fav["tickers"]:
        o = fav["orders"].get(t, {})
        if t in cand_by_ticker:
            c = cand_by_ticker[t]
            name, theme, ref, quelle = c["name"], c["theme"], c["ucits"], "Vorschlag"
        else:
            inf = research.instrument(t)
            name = inf["name"] if inf else t
            theme = inf["art"] if inf else "—"
            ref, quelle = t, "Beobachtung"
        rows.append({"Key": t, "Quelle": quelle, "Name": name, "Thema": theme,
                     "Ref (kaufbar/ISIN)": ref, "Kurs": safe_price(t),
                     "Aktion": o.get("action", "Kauf (neu)"),
                     "Betrag (€)": float(o.get("amount", 0.0)), "Notiz": o.get("note", "")})
    # 2) favorisierte Depotpositionen (per ISIN)
    for isin in [x for x in fav["depot"] if x in pos_by_isin]:
        p = pos_by_isin[isin]
        o = fav["orders"].get(isin, {})
        rows.append({"Key": isin, "Quelle": "Depot", "Name": p["name"], "Thema": p["theme"],
                     "Ref (kaufbar/ISIN)": isin, "Kurs": float(p["last_price"]),
                     "Aktion": o.get("action", "Nachkaufen"),
                     "Betrag (€)": float(o.get("amount", 0.0)), "Notiz": o.get("note", "")})

    if not rows:
        st.info("Noch keine Favoriten. Markiere Vorschläge im Tab 🔭 Chancen oder Positionen im Tab 📊 Mein Depot.")
    else:
        df = pd.DataFrame(rows)
        edited = st.data_editor(
            df.drop(columns=["Key"]), hide_index=True, width="stretch", key="order_editor",
            column_config={
                "Quelle": st.column_config.TextColumn(disabled=True),
                "Name": st.column_config.TextColumn(disabled=True),
                "Thema": st.column_config.TextColumn(disabled=True),
                "Ref (kaufbar/ISIN)": st.column_config.TextColumn(disabled=True),
                "Kurs": st.column_config.NumberColumn(format="%.2f", disabled=True),
                "Aktion": st.column_config.SelectboxColumn(options=ACTIONS),
                "Betrag (€)": st.column_config.NumberColumn(format="%.0f", min_value=0.0, step=100.0),
                "Notiz": st.column_config.TextColumn(),
            },
        )

        # persistieren (Zeilenreihenfolge bleibt stabil -> per Position auf Key mappen)
        new_orders = dict(fav["orders"])
        for orig, (_, er) in zip(rows, edited.iterrows()):
            new_orders[orig["Key"]] = {"amount": float(er["Betrag (€)"] or 0.0),
                                       "note": er["Notiz"] or "", "action": er["Aktion"]}
        if new_orders != fav["orders"]:
            fav["orders"] = new_orders
            favorites.save(FAV_PATH, fav)

        # Zusammenfassung
        summ = edited.copy()
        summ["≈ Stück"] = (summ["Betrag (€)"] / summ["Kurs"].replace(0, pd.NA)).round(2)
        kauf = float(summ.loc[summ["Aktion"].isin(["Kauf (neu)", "Nachkaufen"]), "Betrag (€)"].sum())
        redu = float(summ.loc[summ["Aktion"] == "Reduzieren", "Betrag (€)"].sum())
        mc = st.columns(3)
        mc[0].metric("🟢 Geplante Käufe", f"{kauf:,.0f} €")
        mc[1].metric("🔴 Geplante Reduzierungen", f"{redu:,.0f} €")
        mc[2].metric("Netto-Einsatz", f"{kauf - redu:+,.0f} €")

        st.dataframe(
            summ[["Quelle", "Name", "Aktion", "Ref (kaufbar/ISIN)", "Kurs", "Betrag (€)", "≈ Stück", "Notiz"]],
            hide_index=True, width="stretch",
            column_config={
                "Kurs": st.column_config.NumberColumn(format="%.2f"),
                "Betrag (€)": st.column_config.NumberColumn(format="%.0f"),
                "≈ Stück": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.download_button(
            "⬇️ Order Sheet als CSV", summ.to_csv(index=False).encode("utf-8"),
            file_name="order_sheet.csv", mime="text/csv",
        )
