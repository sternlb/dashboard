@echo off
REM ============================================================
REM  Startet alle persoenlichen Dashboards (sichtbar, minimiert)
REM  Pfade relativ zum Repo-Root (%~dp0) - laeuft aus jedem Klon.
REM  Neues Dashboard? Einfach einen weiteren "start"-Block kopieren
REM  und Ordner + Port anpassen.
REM ============================================================
set "ROOT=%~dp0"

REM --- AI Command Center (Port 8500) ---
start "AI Command Center" /min /d "%ROOT%ai-command-center" ".venv\Scripts\streamlit.exe" run app.py --server.port 8500 --server.headless true

REM --- Trading Agent (Port 8501) ---
start "Trading Agent" /min /d "%ROOT%trading-agent" ".venv\Scripts\streamlit.exe" run app.py --server.port 8501 --server.headless true

REM --- Landing Page Basel-AI (Port 8502, statischer HTTP-Server, stdlib) ---
start "Landing Page Basel-AI" /min /d "%ROOT%basel-ai-landing" python app.py

REM --- Buchungskalender Basel-AI (Port 8505, FastAPI) ---
start "Buchungskalender Basel-AI" /min /d "%ROOT%basel-ai-buchung" ".venv\Scripts\python.exe" app.py

echo.
echo Dashboards gestartet:
echo   AI Command Center      : http://localhost:8500
echo   Trading Agent          : http://localhost:8501
echo   Landing Page Basel-AI  : http://localhost:8502
echo   Buchungskalender       : http://localhost:8505
echo.
