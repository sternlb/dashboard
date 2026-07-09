# Trading Agent

Privates Projekt. Ziel in drei Schritten:

1. **Dashboard** — Marktdaten, Charts, Indikatoren, Watchlist. ← *aktuell*
2. **Markt-/Zeitanalyse** — Indikatoren, Signale, Backtesting auf historischen Daten.
3. **Ausführung** — Broker-Anbindung, autonome Trades. Broker-agnostisch hinter einer
   Adapter-Schnittstelle; zuerst Paper-Trading, dann echter Broker.

> **Hinweis zu Step 3:** ING DiBa bietet keine offizielle Trading-API für Privatkunden.
> Für echte autonome Ausführung ist Interactive Brokers (IBKR) der realistische Weg.
> Die Engine wird deshalb broker-unabhängig gebaut.

## Setup

```bash
py -m venv .venv
.venv\Scripts\activate         # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Starten

```bash
streamlit run app.py
```

Dashboard läuft dann auf http://localhost:8501

## Struktur

```
app.py                    Streamlit-Dashboard (UI)
trading_agent/
  config.py               Watchlist je Anlageklasse
  data.py                 Marktdaten (yfinance) — framework-unabhängig
  indicators.py           SMA / EMA / RSI / MACD — pure pandas
requirements.txt
```

Die Module unter `trading_agent/` sind bewusst frei von Streamlit, damit
Analyse-Engine (Step 2) und Agent (Step 3) sie wiederverwenden können.
```
```

## Symbole (Yahoo Finance)

| Klasse        | Beispiel    |
|---------------|-------------|
| US-Aktie/ETF  | `AAPL`, `SPY` |
| Xetra (EUR)   | `SAP.DE`    |
| Index         | `^GDAXI` (DAX) |
| Forex         | `EURUSD=X`  |
| Krypto        | `BTC-EUR`   |
