"""Guided strategy profiles — the two pillars the agent will run.

A profile bundles a strategy with its parameters, intended asset class,
timeframe, costs, and a plain-language explanation so the strategy can be
*judged* in the dashboard (and later executed autonomously per profile).

- mid_etf    : mid-term, low-turnover trend-following on broad ETFs
- short_stock: short-term momentum trading on liquid single stocks
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Callable

import pandas as pd

from . import signals


@dataclass(frozen=True)
class StrategyProfile:
    key: str
    name: str
    emoji: str
    horizon: str
    asset_class: str
    holding: str
    turnover: str
    kind: str                       # "sma" | "macd" — drives chart overlays
    strategy: Callable[[pd.DataFrame], pd.Series]
    param_text: str
    fast: int                       # SMA periods (unused for macd)
    slow: int
    description: str
    rationale: str
    best_when: str
    weak_when: str
    pros: tuple[str, ...]
    cons: tuple[str, ...]
    universe: tuple[str, ...]
    default_period: str
    fee_bps: float
    how_to_judge: str


PROFILES: dict[str, StrategyProfile] = {
    "mid_etf": StrategyProfile(
        key="mid_etf",
        name="Mittelfristig — ETF-Trendfolge",
        emoji="🌱",
        horizon="Wochen bis Monate",
        asset_class="Breite ETFs (Index)",
        holding="lang — oft Monate pro Position",
        turnover="niedrig — wenige Trades pro Jahr",
        kind="sma",
        strategy=partial(signals.sma_crossover, fast=50, slow=200),
        param_text="SMA 50 / SMA 200 (Golden Cross)",
        fast=50,
        slow=200,
        description=(
            "Klassischer Golden/Death Cross: investiert, solange der 50-Tage-"
            "Durchschnitt über dem 200-Tage-Durchschnitt liegt — geht in Cash, "
            "sobald er darunter fällt."
        ),
        rationale=(
            "Breite ETFs steigen langfristig, haben aber tiefe Bärenmärkte. Der "
            "200-Tage-Filter hält dich in Aufwärtstrends investiert und nimmt "
            "dich vor den großen Crashs heraus."
        ),
        best_when="Klare, länger laufende Trends (Bullen- wie Bärenmärkte).",
        weak_when="Seitwärtsmärkte — der Filter erzeugt teure Fehlsignale (Whipsaws).",
        pros=(
            "Wenige Trades → geringe Kosten & Steuern",
            "Begrenzt große Drawdowns deutlich",
            "Einfach nachvollziehbar und robust",
            "Passt zur ETF-Sparlogik",
        ),
        cons=(
            "Reagiert träge, verpasst exakte Tief-/Hochpunkte",
            "Underperformt Buy & Hold in starken Bullenjahren",
            "Whipsaws in langen Seitwärtsphasen",
        ),
        universe=("EXS1.DE", "SPY", "QQQ", "^GSPC", "^GDAXI"),
        default_period="5y",
        fee_bps=5.0,
        how_to_judge=(
            "Ziel ist ein klar **geringerer Max-Drawdown** als Buy & Hold bei "
            "akzeptabler Rendite. Wenige Trades sind hier ein gutes Zeichen. "
            "Schau auf Calmar (Rendite je Einheit Drawdown), nicht nur Rohrendite."
        ),
    ),
    "short_stock": StrategyProfile(
        key="short_stock",
        name="Kurzfristig — Aktien-Momentum",
        emoji="⚡",
        horizon="Tage bis Wochen",
        asset_class="Liquide Einzelaktien",
        holding="kurz — Tage bis wenige Wochen",
        turnover="hoch — viele Trades",
        kind="macd",
        strategy=signals.macd_cross,
        param_text="MACD 12 / 26 / 9",
        fast=12,
        slow=26,
        description=(
            "Momentum über MACD: long, solange die MACD-Linie über ihrer "
            "Signallinie liegt — Ausstieg, wenn sie darunter kreuzt."
        ),
        rationale=(
            "Einzelaktien bewegen sich in kürzeren Momentum-Schüben. MACD fängt "
            "die Beschleunigung früh ab und steigt aus, wenn das Momentum dreht."
        ),
        best_when="Aktien mit klaren, kurzen Trendschüben und Volatilität.",
        weak_when="Ruhige oder zickzack-Märkte — viele kleine Fehltrades, Kosten fressen die Rendite.",
        pros=(
            "Reagiert schnell auf Trendwechsel",
            "Fängt kurze Bewegungen, die Trendfolger verpassen",
            "Klares, regelbasiertes Ein-/Ausstiegssignal",
        ),
        cons=(
            "Viele Trades → Kosten & Steuern schlagen durch",
            "Anfällig für Whipsaws in Seitwärtsphasen",
            "Erfordert engere Überwachung / Disziplin",
        ),
        universe=("AAPL", "MSFT", "NVDA", "SAP.DE", "SIE.DE"),
        default_period="1y",
        fee_bps=15.0,
        how_to_judge=(
            "Entscheidend ist **netto nach Gebühren**: Trefferquote × Ø-Gewinn "
            "muss die Kosten der vielen Trades schlagen. Sharpe und Drawdown "
            "wiegen schwerer als die Rohrendite. Viele Trades sind nur ok, wenn "
            "der Ø-Trade klar positiv ist."
        ),
    ),
}


# Plain-language meaning of each backtest metric — shown as tooltips/glossary.
METRIC_HELP: dict[str, str] = {
    "total_return": "Gesamtrendite der Strategie über den Zeitraum (nach Gebühren).",
    "cagr": "Annualisierte Rendite — als wäre sie über ein Jahr geglättet.",
    "buy_hold_return": "Vergleich: einfach kaufen und halten, ohne Ein-/Ausstiege.",
    "alpha": "Mehrrendite gegenüber Buy & Hold. Positiv = Strategie schlägt Halten.",
    "max_drawdown": "Größter Verlust vom Hoch zum Tief. Wie weh es zwischendurch tat.",
    "volatility": "Annualisierte Schwankungsbreite der Renditen (Risiko).",
    "sharpe": "Rendite pro Risiko. >1 gut, >2 sehr gut, <0 schlecht.",
    "calmar": "Annualisierte Rendite geteilt durch Max-Drawdown. Höher = besser.",
    "exposure": "Anteil der Zeit, in der Kapital im Markt war (Rest: Cash).",
    "win_rate": "Anteil der Trades mit Gewinn.",
    "avg_trade": "Durchschnittliche Rendite pro Trade (nach Gebühren).",
    "trades": "Anzahl der Trades. Viele Trades = mehr Kosten & Aufwand.",
}
