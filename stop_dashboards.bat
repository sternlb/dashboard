@echo off
REM Beendet alle laufenden Dashboard-Server ueber ihre Ports
REM (8500 Command Center, 8501 Trading, 8502 Landing, 8505 Buchung).
REM Port-basiert statt Prozessname - trifft die Server unabhaengig davon,
REM mit welchem Python/Streamlit und aus welchem Ordner sie gestartet wurden.
powershell -NoProfile -Command "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 8500,8501,8502,8505 } | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
echo Dashboards gestoppt.
