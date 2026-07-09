"""Research-Layer: Bewertungen je Position + Lücken-Kandidaten.

Hält die Ergebnisse der Tiefenanalyse (Stand Juni 2026) maschinenlesbar, damit
das Dashboard sie neben den Live-Daten anzeigt. Bewertungen sind nach ISIN
verschlüsselt, Kandidaten sind kaufbare UCITS-Lückenfüller zur These
(Humanoide, AI-Strombedarf via Nuklear/Netz).

Quelle der Einschätzungen: eigene Recherche, keine Anlageberatung.
"""

from __future__ import annotations

# --- Bewertung je Depotposition (Schlüssel = ISIN) ------------------------
# verdict: 🟢 stark/halten · 🟡 neutral/beobachten · 🔴 schwach/abbauen
RATINGS: dict[str, dict[str, str]] = {
    "IE00BDVPNG13": {"verdict": "🟢", "label": "Halten", "fit": "AI-Infra · Hardware",
                     "note": "Bester Fit zur These: ~79 % IT, fast nur Halbleiter/AI-Infrastruktur "
                             "(AMD, Marvell, Micron, NVIDIA) — die 'Schaufeln', die die SaaSpocalypse "
                             "nicht trifft. +90 % gelaufen."},
    "IE00BKWQ0F09": {"verdict": "🟢", "label": "Halten", "fit": "Energie · fossil",
                     "note": "Reines Öl/Gas (Shell 33 %, Total 19 %, BP 18 %). Einzige Position, die "
                             "direkt vom steigenden Energiebedarf + Dividenden profitiert."},
    "FR0010315770": {"verdict": "🟢", "label": "Halten", "fit": "Core · Welt",
                     "note": "Breiter Welt-ETF — solider Kern-Baustein."},
    "IE0006WW1TQ4": {"verdict": "🟢", "label": "Halten", "fit": "Core · Welt ex-US",
                     "note": "Breiter Industrieländer-ETF ohne USA — dein Diversifizierer."},
    "FR0010524777": {"verdict": "🟡", "label": "Beobachten", "fit": "Energie · clean",
                     "note": "These richtig (Energie), Vehikel fraglich: Clean Energy hat 2026 "
                             "Policy-Gegenwind (US-Steuergutschriften laufen aus, Zölle). Zudem "
                             "23 %-Klumpen. AI-Mehrbedarf fließt eher in Nuklear/Gas/Netz."},
    "DE000A0DJ6J9": {"verdict": "🟡", "label": "Gewinn prüfen", "fit": "Energie · Solar (Aktie)",
                     "note": "+66 %, aber Kurs (63 €) über Ø-Analystenziel (55 €); 2025 erneut "
                             "Verlust, keine Dividende. Story = Hoffnung, nicht operative Stärke."},
    "IE00BYZK4552": {"verdict": "🟡", "label": "Halten", "fit": "Robotik · breit",
                     "note": "Trotz 'Robotics' Semis-/Automations-lastig (Intel, AMD, ABB; 199 Titel). "
                             "Gute Basis, aber KEIN gezieltes Humanoid-Play."},
    "IE000R8PO127": {"verdict": "🟡", "label": "Beobachten", "fit": "Verteidigung · Infra",
                     "note": "Ukraine-Wiederaufbau (Infra + Industrie + Defence), erst März 2026 "
                             "aufgelegt. Event-getrieben, hohe Unsicherheit."},
    "DE000A0H08F7": {"verdict": "🟡", "label": "Neutral", "fit": "Infra · Bau",
                     "note": "STOXX 600 Bau & Material. Schwacher Performer, These dünn."},
    "IE000YYE6WK5": {"verdict": "🟡", "label": "Halten", "fit": "Verteidigung",
                     "note": "Mini-Posten. Europ. Defence-Sektor konsolidiert 2026 (Stoxx A&D leicht negativ YTD)."},
    "GB00BLD4ZL17": {"verdict": "🟡", "label": "Neutral", "fit": "Krypto · Bitcoin",
                     "note": "Reines Bitcoin-ETP, −22 %. Außerhalb deiner Kernthesen — bewusste Risiko-Allokation."},
    "CA92539Q6040": {"verdict": "🔴", "label": "Abbauen", "fit": "KI · gescheitert",
                     "note": "VERSES AI hat 2026 die KI-Entwicklung eingestellt (~8 Mio. $ MCap, "
                             "Going-Concern-Zweifel). Faktischer Totalverlust — höchstens steuerlich relevant."},
}

DEFAULT_RATING = {"verdict": "⚪", "label": "—", "fit": "—", "note": ""}


def rating_for(isin: str) -> dict[str, str]:
    return RATINGS.get(str(isin), DEFAULT_RATING)


# --- Energie-Durchleuchtung: clean vs. fossil (Schlüssel = ISIN) -----------
ENERGY_TYPE: dict[str, str] = {
    "FR0010524777": "Clean Energy (ETF)",
    "DE000A0DJ6J9": "Solar (Einzelaktie)",
    "IE00BKWQ0F09": "Fossil Öl/Gas (ETF)",
}


# --- Lücken-Kandidaten zur These ------------------------------------------
# 'ticker' = liquides Yahoo-Symbol für Chart/Backtest (oft US-gelistet),
# 'ucits'  = an der Börse für ING kaufbares UCITS-Pendant.
CANDIDATES: list[dict[str, str]] = [
    # --- Gruppe: KI & Energie (deine Kernthese) ---
    {"ticker": "KOID", "name": "Humanoid Robotics (KraneShares)", "theme": "Humanoide", "group": "🤖 KI & Energie",
     "ucits": "KBOT.DE (Xetra) · IE000O6Z73N7", "why": "Schließt deine größte These-Lücke: gezieltes Humanoid-Play. Enthält chin. Player (Unitree)."},
    {"ticker": "NUKL.DE", "name": "Uranium & Nuclear (VanEck)", "theme": "Nuklear/Uran", "group": "🤖 KI & Energie",
     "ucits": "direkt kaufbar (Xetra, EUR)", "why": "Direkter Profiteur des AI-Strombedarfs: Uranminer + Reaktorbau + Versorger."},
    {"ticker": "URNU.L", "name": "Uranium Miners (Global X)", "theme": "Uran pur", "group": "🤖 KI & Energie",
     "ucits": "direkt kaufbar (LSE) · URNU", "why": "Reine Uran-Wette auf die Nuklear-Renaissance."},
    {"ticker": "GRID", "name": "Smart Grid / Electrification", "theme": "Netz/Strom", "group": "🤖 KI & Energie",
     "ucits": "WIRE.DE (Xtrackers Smart Grid)", "why": "Netz & Stromausrüstung — die 'Pickaxe' des AI-Energiebooms."},
    {"ticker": "BOTZ", "name": "Robotics & AI (Global X)", "theme": "Robotik/AI", "group": "🤖 KI & Energie",
     "ucits": "Global X Robotics UCITS", "why": "Vergleichsmaßstab zu deinem iShares Automation & Robotics."},
    # --- Gruppe: El Niño 2026 (Wetter-These) ---
    {"ticker": "MOO", "name": "Agribusiness (VanEck)", "theme": "Agrar/Dünger", "group": "🌊 El Niño 2026",
     "ucits": "IS0C.DE (iShares Agribusiness)", "why": "Breiter Agrar-Korb (Dünger, Saatgut, Landmaschinen) — klassischer El-Niño-Profiteur."},
    {"ticker": "DBA", "name": "Agrar-Rohstoffe Korb (Invesco)", "theme": "Soft Commodities", "group": "🌊 El Niño 2026",
     "ucits": "WisdomTree Agriculture (AIGA)", "why": "Direkte Wette auf steigende Soft-Commodity-Preise (Zucker, Kaffee, Getreide) bei El Niño."},
    {"ticker": "SDF.DE", "name": "K+S AG (Kali/Dünger)", "theme": "Dünger", "group": "🌊 El Niño 2026",
     "ucits": "direkt kaufbar (Xetra, EUR)", "why": "Deutscher Kali-/Düngerproduzent — profitiert, wenn Bauern Ernteausfälle mit mehr Input kontern."},
    {"ticker": "CTVA", "name": "Corteva (Saatgut/Pflanzenschutz)", "theme": "Agrar-Inputs", "group": "🌊 El Niño 2026",
     "ucits": "US-Aktie (bei ING handelbar)", "why": "Saatgut & Pflanzenschutz — in der Recherche explizit als El-Niño-Gewinner genannt."},
    {"ticker": "IH2O.L", "name": "iShares Global Water UCITS", "theme": "Wasser", "group": "🌊 El Niño 2026",
     "ucits": "direkt kaufbar (LSE/Xetra)", "why": "Dürren & Wasserstress durch El Niño stärken das Thema Wasserinfrastruktur."},
]


# --- Steckbriefe: was steckt hinter einem Symbol (Schlüssel = Ticker) ------
INSTRUMENTS: dict[str, dict[str, str]] = {
    # --- Profil 🌱 Mittelfristig (ETF) ---
    "EXS1.DE": {"name": "iShares Core DAX UCITS ETF", "art": "ETF · Deutschland",
                "desc": "Bildet den **DAX** ab — die 40 größten börsennotierten deutschen Konzerne "
                        "(SAP, Siemens, Allianz, Mercedes …). Thesaurierend, sehr günstig. "
                        "Stellvertreter für „die deutsche Wirtschaft als Ganzes”."},
    "SPY": {"name": "SPDR S&P 500 ETF", "art": "ETF · USA",
            "desc": "Die **500 größten US-Unternehmen** in einem Korb — der meistgehandelte ETF der Welt. "
                    "Stark von Big Tech geprägt (Apple, Microsoft, Nvidia). Maßstab für „den US-Markt”."},
    "QQQ": {"name": "Invesco QQQ (Nasdaq-100)", "art": "ETF · USA Tech",
            "desc": "Die **100 größten Nicht-Finanzwerte der Nasdaq** — tech- und wachstumslastig. "
                    "Höhere Schwankung als der S&P 500, dafür der direkteste breite Tech-/AI-Hebel."},
    "^GSPC": {"name": "S&P 500 Index", "art": "Index (Referenz)",
              "desc": "Der **Referenzindex** des US-Marktes (nicht direkt kaufbar — dafür gibt’s SPY). "
                      "Dient hier als Vergleichs-/Analysegröße."},
    "^GDAXI": {"name": "DAX Index", "art": "Index (Referenz)",
               "desc": "Der **deutsche Leitindex** (40 Blue Chips). Nicht direkt handelbar — investierbar via EXS1.DE."},
    # --- Profil ⚡ Kurzfristig (Aktien) ---
    "AAPL": {"name": "Apple Inc.", "art": "Aktie · USA",
             "desc": "Weltgrößter Konzern nach Marktwert. Geld verdient mit **iPhone + Services** "
                     "(App Store, iCloud). Sehr cashstark, aber AI-Strategie gilt als Nachzügler."},
    "MSFT": {"name": "Microsoft Corp.", "art": "Aktie · USA",
             "desc": "Windows, Office und vor allem die **Azure-Cloud**. Großer **OpenAI-Partner** — "
                     "zentraler Profiteur der AI-Welle auf der Software-/Infrastrukturseite."},
    "NVDA": {"name": "NVIDIA Corp.", "art": "Aktie · USA",
             "desc": "Baut die **GPUs**, auf denen praktisch jede KI trainiert wird — der „Schaufelverkäufer” "
                     "des AI-Goldrauschs. Extrem zyklisch und schwankungsfreudig."},
    "SAP.DE": {"name": "SAP SE", "art": "Aktie · Deutschland",
               "desc": "Größter europäischer Softwarekonzern. **ERP-Standard** für Unternehmen, Umbau Richtung "
                       "Cloud. Klassisches SaaS — also im Auge behalten wegen deiner „AI-drückt-Software”-These."},
    "SIE.DE": {"name": "Siemens AG", "art": "Aktie · Deutschland",
               "desc": "Industriekonzern: **Automatisierung, Antriebe, Energietechnik, Bahn**. Profiteur von "
                       "Elektrifizierung und Fabrik-Automation — indirekter Robotik-/Energie-Hebel."},
    # --- Chancen-Kandidaten ---
    "KOID": {"name": "KraneShares Global Humanoid Robotics & Physical AI", "art": "ETF · Humanoide",
             "desc": "**Gezieltes Humanoid-Play**: Hersteller + Zulieferer humanoider Roboter (Credo, STMicro, "
                     "Harmonic Drive, Renesas). Kaufbar als UCITS **KBOT.DE**. Enthält chin. Player (Unitree)."},
    "NUKL.DE": {"name": "VanEck Uranium & Nuclear Technologies", "art": "ETF · Nuklear",
                "desc": "**Ganze Nuklear-Kette**: Uranminer, Reaktorbau, Versorger. Direkte Wette darauf, dass der "
                        "AI-Strombedarf über Kernkraft gedeckt wird. In EUR an der Xetra handelbar."},
    "URNU.L": {"name": "Global X Uranium UCITS", "art": "ETF · Uran",
               "desc": "**Reine Uran-Wette**: Minenbetreiber und Uranproduktion. Aggressiver/zyklischer als NUKL, "
                       "fokussiert auf den Rohstoffpreis statt die gesamte Kette."},
    "GRID": {"name": "First Trust NASDAQ Clean Edge Smart Grid", "art": "ETF · Netz/Strom",
             "desc": "**Stromnetz & Elektrifizierung**: Netzausrüstung, Transformatoren, Smart Grid. Der „Pickaxe” "
                     "des AI-Energiebooms — kaufbar als UCITS via WIRE.DE."},
    "BOTZ": {"name": "Global X Robotics & Artificial Intelligence", "art": "ETF · Robotik/AI",
             "desc": "Breite Robotik-/AI-Mischung (inkl. Nvidia, Intuitive Surgical, japan. Robotikbauer). "
                     "Dient hier als **Vergleichsmaßstab** zu deinem iShares Automation & Robotics."},
    # --- El Niño 2026 ---
    "MOO": {"name": "VanEck Agribusiness ETF", "art": "ETF · Agrar",
            "desc": "Weltweite **Agrar-Wertschöpfungskette**: Dünger (Nutrien, Corteva), Saatgut, Landmaschinen "
                    "(Deere). Profitiert, wenn El Niño Ernten stresst und Agrar-Inputs gefragter werden. "
                    "Kaufbar als UCITS via IS0C.DE."},
    "DBA": {"name": "Invesco DB Agriculture Fund", "art": "ETF · Soft Commodities",
            "desc": "Korb aus **Agrar-Rohstoffen** (Zucker, Kaffee, Mais, Sojabohnen, Weizen). Direkter Hebel auf "
                    "die Preise, die bei El Niño typischerweise steigen. UCITS-Pendant: WisdomTree Agriculture."},
    "SDF.DE": {"name": "K+S AG", "art": "Aktie · Deutschland",
               "desc": "Deutscher **Kali- und Düngerproduzent**. Dünger wird teurer/gefragter, wenn Wetterextreme die "
                       "Ernten bedrohen — klassischer El-Niño-Hebel, direkt an der Xetra handelbar."},
    "CTVA": {"name": "Corteva Inc.", "art": "Aktie · USA",
             "desc": "Reiner Agrar-Konzern: **Saatgut und Pflanzenschutz**. Bauern kaufen bei Wetterstress mehr "
                     "Inputs, um Ausfälle abzufedern — in der Recherche als El-Niño-Gewinner genannt."},
    "IH2O.L": {"name": "iShares Global Water UCITS ETF", "art": "ETF · Wasser",
               "desc": "Weltweite **Wasserwirtschaft** (Versorger, Aufbereitung, Infrastruktur). Dürren und "
                       "Wasserstress durch El Niño stützen das Thema langfristig."},
}


# --- Anlage-Thesen (für Info-Blöcke im Dashboard) -------------------------
EL_NINO_NOTE = (
    "**🌊 Super El Niño 2026** — NOAA gibt ~63 % für ein „sehr starkes“ Ereignis, WMO ~90 % Persistenz "
    "bis November; mehrere Modelle sehen das stärkste je gemessene. **Markt-Effekte:** Dürren/Hitze "
    "stressen Ernten → **Gewinner** sind Agrar-Inputs (Dünger, Saatgut), Soft Commodities (Zucker, Kaffee, "
    "Kakao) und Wasser. **Verlierer:** Lebensmittelverarbeiter (Margendruck), Rück-/Versicherer (Katastrophen) "
    "und tendenziell **Erdgas** (milderer Nordwinter → weniger Heizbedarf). In deinem Depot kein direktes "
    "Erdgas-Risiko — die These erschließt v. a. neue Chancen auf der Gewinner-Seite."
)


def instrument(ticker: str) -> dict[str, str] | None:
    return INSTRUMENTS.get(str(ticker))
