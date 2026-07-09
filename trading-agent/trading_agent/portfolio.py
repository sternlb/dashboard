"""Depot-/Portfolio-Analyse.

Arbeitet mit den Snapshot-Werten aus dem ING-Depotexport (Kurswert/Einstands-
wert in EUR) — die sind autoritativ und stimmen exakt mit dem Kontoauszug. Kein
fehleranfälliges ISIN→Yahoo-Mapping nötig, um die Struktur zu verstehen. Pure
pandas, keine UI-/Netz-Abhängigkeit, vom Agent wiederverwendbar.

CSV-Spalten (Pflicht):
    name, asset_class, theme, shares, cost_eur, value_eur
Optional:
    isin, buy_price, last_price, ticker
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED = ["name", "asset_class", "theme", "shares", "cost_eur", "value_eur"]


def load_holdings(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Holdings-CSV fehlen Spalten: {missing}")
    return df


def enrich(holdings: pd.DataFrame) -> pd.DataFrame:
    """G/V und Gewichtung je Position aus den Snapshot-Werten."""
    df = holdings.copy()
    df["value_eur"] = df["value_eur"].astype(float)
    df["cost_eur"] = df["cost_eur"].astype(float)
    df["pnl_eur"] = df["value_eur"] - df["cost_eur"]
    df["pnl_pct"] = (df["pnl_eur"] / df["cost_eur"] * 100).where(df["cost_eur"] != 0)
    total = df["value_eur"].sum()
    df["weight_pct"] = (df["value_eur"] / total * 100) if total else 0.0
    return df.sort_values("value_eur", ascending=False).reset_index(drop=True)


def totals(enriched: pd.DataFrame) -> dict[str, float]:
    value = float(enriched["value_eur"].sum())
    cost = float(enriched["cost_eur"].sum())
    pnl = value - cost
    return {
        "value": value,
        "cost": cost,
        "pnl": pnl,
        "pnl_pct": (pnl / cost * 100) if cost else 0.0,
        "positions": int(len(enriched)),
        "top_weight": float(enriched["weight_pct"].max()) if len(enriched) else 0.0,
    }


def allocation(enriched: pd.DataFrame, by: str = "theme") -> pd.Series:
    """Wert je Gruppe (theme / asset_class), absteigend sortiert."""
    return enriched.groupby(by)["value_eur"].sum().sort_values(ascending=False)


def concentration_flags(enriched: pd.DataFrame, pos_limit: float = 20.0,
                        theme_limit: float = 35.0) -> list[str]:
    """Klumpenrisiken auf Positions- und Themen-Ebene."""
    flags = []
    total = enriched["value_eur"].sum()
    for _, r in enriched.iterrows():
        if r["weight_pct"] > pos_limit:
            flags.append(f"Einzelposition **{r['name']}** = {r['weight_pct']:.0f} % des Depots")
    if total:
        for theme, val in allocation(enriched, "theme").items():
            share = val / total * 100
            if share > theme_limit:
                flags.append(f"Thema **{theme}** = {share:.0f} % des Depots (Klumpen)")
    return flags


def insights(enriched: pd.DataFrame) -> list[str]:
    """Automatische, lesbare Beobachtungen zur Depot-Struktur."""
    total = enriched["value_eur"].sum()
    out: list[str] = []
    if not total:
        return out

    themes = allocation(enriched, "theme")
    top_theme, top_val = themes.index[0], themes.iloc[0]
    out.append(f"Größtes Thema: **{top_theme}** mit {top_val/total*100:.0f} % "
               f"({top_val:,.0f} €).")

    broad = enriched.loc[enriched["theme"] == "Welt/Breit", "value_eur"].sum()
    out.append(f"Breit gestreutes Welt-Investment: nur **{broad/total*100:.0f} %** "
               "— der Rest ist thematisch/sektoral gewettet.")

    n_themes = enriched["theme"].nunique()
    out.append(f"Verteilt auf **{n_themes} Themen**, aber stark ungleich gewichtet.")

    losers = enriched[enriched["pnl_pct"] < -50]
    for _, r in losers.iterrows():
        out.append(f"⚠️ **{r['name']}** steht bei {r['pnl_pct']:+.0f} % "
                   f"(noch {r['value_eur']:,.0f} € von {r['cost_eur']:,.0f} € Einstand).")

    return out
