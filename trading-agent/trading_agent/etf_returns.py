"""Jährliche ETF-Erträge nach Kosten + Seit-Kauf-Betrachtung.

Grundlage sind die Total-Return-Kurse der ETFs selbst (Dividenden reinvestiert).
Die laufenden Fondskosten (TER) werden **im Fonds** verrechnet und stecken damit
bereits in diesen Kursen — die TER-Spalte macht sie sichtbar und rechnet sie in
€/Jahr auf die aktuelle Positionsgröße um (kein Doppelabzug).

Kaufdatum (`buy_date`) und Kaufvolumen (`cost_eur`) aus holdings.csv fließen in
die Seit-Kauf-Kennzahlen ein: Rendite p.a. seit Kauf und Ø-Ertrag in €/Jahr.
Pure pandas, keine UI-/Netz-Abhängigkeit (Kursdaten liefert der Aufrufer).
"""

from __future__ import annotations

import pandas as pd

# --- TER in % p.a. je ISIN — manuell gepflegt (Stand 07/2026) ---------------
# Neue Position? ISIN + TER (Factsheet des Anbieters) hier ergänzen.
TER_PCT: dict[str, float] = {
    "FR0010315770": 0.38,  # Amundi MSCI World Swap Dist
    "IE000R8PO127": 0.75,  # HANetf Defence & Ukraine Reconstruction
    "DE000A0H08F7": 0.46,  # iShares STOXX Europe 600 Construction & Materials
    "IE00BYZK4552": 0.40,  # iShares Automation & Robotics
    "FR0010524777": 0.60,  # Amundi MSCI New Energy
    "IE00BKWQ0F09": 0.18,  # SPDR MSCI Europe Energy
    "IE000YYE6WK5": 0.55,  # VanEck Defense
    "IE00BDVPNG13": 0.40,  # WisdomTree Artificial Intelligence
    "IE0006WW1TQ4": 0.15,  # Xtrackers MSCI World ex USA
}


def ter_for(isin: str) -> float | None:
    return TER_PCT.get(str(isin))


def yearly_returns(closes: pd.Series) -> pd.Series:
    """Kalenderjahres-Renditen in %, Index = Jahr (int).

    Rechnet Jahresschluss zu Jahresschluss — dadurch sind alle Werte volle
    Kalenderjahre, auch wenn die Historie mitten im Jahr beginnt (das
    angebrochene erste Jahr fällt automatisch weg). Das laufende Jahr ist
    als YTD enthalten — Beschriftung übernimmt der Aufrufer.
    """
    if closes.empty:
        return pd.Series(dtype=float)
    year_end = closes.resample("YE").last().dropna()
    if len(year_end) < 2:
        return pd.Series(dtype=float)
    rets = year_end.pct_change().dropna() * 100
    rets.index = rets.index.year
    return rets


def cagr_pct(closes: pd.Series) -> float | None:
    """Durchschnittliche Rendite p.a. (geometrisch) über die verfügbare Historie."""
    if len(closes) < 2:
        return None
    days = (closes.index[-1] - closes.index[0]).days
    if days < 200:  # unter ~1 Jahr ist "p.a." irreführend
        return None
    return (float(closes.iloc[-1] / closes.iloc[0]) ** (365.25 / days) - 1) * 100


def last_12m_pct(closes: pd.Series) -> float | None:
    """Rendite der letzten 12 Monate in %."""
    if len(closes) < 2:
        return None
    cutoff = closes.index[-1] - pd.Timedelta(days=365)
    past = closes[closes.index <= cutoff]
    if past.empty:
        return None
    return (float(closes.iloc[-1] / past.iloc[-1]) - 1) * 100


def since_buy(cost_eur: float, value_eur: float, buy_date) -> dict:
    """Seit-Kauf-Kennzahlen aus Kaufvolumen + Kaufdatum.

    total_pct  — Gesamtrendite seit Kauf (braucht nur das Kaufvolumen)
    pa_pct     — Rendite p.a. seit Kauf (braucht das Kaufdatum)
    eur_year   — Ø Ertrag in €/Jahr seit Kauf (braucht das Kaufdatum)
    years      — Haltedauer in Jahren
    """
    out = {"total_pct": None, "pa_pct": None, "eur_year": None, "years": None}
    if cost_eur:
        out["total_pct"] = (value_eur / cost_eur - 1) * 100
    if buy_date is None or pd.isna(buy_date):
        return out
    bd = pd.Timestamp(buy_date)
    years = (pd.Timestamp.now() - bd).days / 365.25
    if years <= 0:
        return out
    out["years"] = years
    if cost_eur:
        out["pa_pct"] = (float(value_eur / cost_eur) ** (1 / years) - 1) * 100
        out["eur_year"] = (value_eur - cost_eur) / years
    return out
