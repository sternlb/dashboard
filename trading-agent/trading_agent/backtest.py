"""Vectorized backtester.

Takes a close-price series and a position series (from `signals`) and returns
an equity curve, a per-trade log, and headline metrics. Deliberately simple
and honest:

- Positions are entered on the *next* bar (`shift(1)`) — no look-ahead bias.
- A trading cost (basis points) is charged whenever exposure changes.
- Metrics are time-based, so it works for daily, intraday, or 24/7 crypto data.

This is a long/flat, single-asset backtest — enough to compare strategies and
sanity-check ideas before any real money is involved. Not a portfolio engine.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    equity: pd.Series          # strategy equity curve, starts at 1.0
    buy_hold: pd.Series        # benchmark: buy and hold the asset
    returns: pd.Series         # per-bar strategy returns (after costs)
    trade_log: pd.DataFrame    # one row per closed/holding trade
    metrics: dict[str, float]
    trades: int


def periods_per_year(index: pd.Index) -> float:
    """Annualization factor inferred from the median bar spacing."""
    if len(index) < 3:
        return 252.0
    deltas = pd.Series(pd.to_datetime(index)).diff().dropna()
    secs = deltas.dt.total_seconds().median()
    if not secs or secs <= 0:
        return 252.0
    return (365.25 * 24 * 3600) / secs


def _years(index: pd.Index) -> float:
    if len(index) < 2:
        return 0.0
    span = pd.Timestamp(index[-1]) - pd.Timestamp(index[0])
    return max(span.total_seconds() / (365.25 * 24 * 3600), 1e-9)


def _trade_log(exposure: pd.Series, net: pd.Series) -> pd.DataFrame:
    """Compound the after-cost return of each contiguous holding period."""
    in_pos = exposure > 0
    cols = ["Einstieg", "Ausstieg", "Bars", "Rendite %"]
    if not in_pos.any():
        return pd.DataFrame(columns=cols)
    trade_id = (in_pos & ~in_pos.shift(1, fill_value=False)).cumsum()
    rows = []
    for tid in trade_id[in_pos].unique():
        mask = (trade_id == tid) & in_pos
        seg = net[mask]
        rows.append({
            "Einstieg": seg.index[0],
            "Ausstieg": seg.index[-1],
            "Bars": int(mask.sum()),
            "Rendite %": float((1 + seg).prod() - 1) * 100,
        })
    return pd.DataFrame(rows, columns=cols)


def run_backtest(
    close: pd.Series,
    position: pd.Series,
    fee_bps: float = 10.0,
    ppy: float | None = None,
) -> BacktestResult:
    close = close.astype(float)
    rets = close.pct_change().fillna(0.0)
    if ppy is None:
        ppy = periods_per_year(close.index)

    pos = position.reindex(close.index).fillna(0.0)
    exposure = pos.shift(1).fillna(0.0)            # act on next bar
    gross = exposure * rets

    turns = pos.diff().abs().fillna(pos.abs())     # 0->1 or 1->0 costs once
    cost = turns * (fee_bps / 10_000.0)
    net = gross - cost

    equity = (1 + net).cumprod()
    buy_hold = (1 + rets).cumprod()

    log = _trade_log(exposure, net)
    n_trades = len(log)
    trade_rets = log["Rendite %"].to_numpy() if n_trades else np.array([])

    years = _years(close.index)
    final = float(equity.iloc[-1]) if len(equity) else 1.0
    bh_final = float(buy_hold.iloc[-1]) if len(buy_hold) else 1.0
    drawdown = equity / equity.cummax() - 1.0
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0

    std = net.std()
    sharpe = float(net.mean() / std * np.sqrt(ppy)) if std > 0 else 0.0
    cagr = final ** (1 / years) - 1.0 if years > 0 else 0.0

    metrics = {
        "total_return": final - 1.0,
        "cagr": cagr,
        "buy_hold_return": bh_final - 1.0,
        "alpha": (final - 1.0) - (bh_final - 1.0),
        "max_drawdown": max_dd,
        "volatility": float(std * np.sqrt(ppy)),
        "sharpe": sharpe,
        "calmar": cagr / abs(max_dd) if max_dd < 0 else 0.0,
        "exposure": float((exposure > 0).mean()),
        "win_rate": float((trade_rets > 0).mean()) if n_trades else 0.0,
        "avg_trade": float(trade_rets.mean()) if n_trades else 0.0,
        "best_trade": float(trade_rets.max()) if n_trades else 0.0,
        "worst_trade": float(trade_rets.min()) if n_trades else 0.0,
        "avg_bars": float(log["Bars"].mean()) if n_trades else 0.0,
        "trades": float(n_trades),
    }
    return BacktestResult(equity, buy_hold, net, log, metrics, n_trades)
