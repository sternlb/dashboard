@echo off
REM ============================================================
REM  Startet alle Dashboard-Server neu:
REM  erst stoppen (port-basiert), dann unsichtbar neu starten
REM  (gleiche Art wie der Autostart per VBS).
REM  Desktop-Verknuepfung "AI Dashboards neu starten" zeigt hierher.
REM ============================================================
set "ROOT=%~dp0"

echo Stoppe Dashboards...
call "%ROOT%stop_dashboards.bat"

REM Kurz warten bis die Ports wieder frei sind
REM (ping statt timeout - funktioniert auch ohne Konsolen-Eingabe)
ping -n 3 127.0.0.1 >nul

echo Starte Dashboards neu (unsichtbar, inkl. Repo-Sync)...
wscript "%ROOT%start_dashboards_hidden.vbs"

echo.
echo Neustart angestossen. In wenigen Sekunden erreichbar:
echo   AI Command Center      : http://localhost:8500
echo   Trading Agent          : http://localhost:8501
echo   Landing Page Basel-AI  : http://localhost:8502
echo   Buchungskalender       : http://localhost:8505
echo.
ping -n 6 127.0.0.1 >nul
