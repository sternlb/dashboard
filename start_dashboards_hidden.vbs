' Startet alle Dashboards komplett unsichtbar (fuer den Autostart).
' Kein Konsolenfenster. Manuell/sichtbar starten: start_dashboards.bat
' Pfade werden aus dem Skript-Ort abgeleitet - laeuft aus jedem Klon.
Dim sh, fso, root
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)

' --- Repo-Sync: Unterrichts-Repos + Vault von GitHub ziehen (wartet auf Ende) ---
sh.Run "python """ & root & "\ai-command-center\sync_repos.py""", 0, True

' --- AI Command Center (Port 8500) ---
sh.CurrentDirectory = root & "\ai-command-center"
sh.Run """" & root & "\ai-command-center\.venv\Scripts\streamlit.exe"" run app.py --server.port 8500 --server.headless true", 0, False

' --- Trading Agent (Port 8501) ---
sh.CurrentDirectory = root & "\trading-agent"
sh.Run """" & root & "\trading-agent\.venv\Scripts\streamlit.exe"" run app.py --server.port 8501 --server.headless true", 0, False

' --- Landing Page Basel-AI (Port 8502, statischer HTTP-Server) ---
sh.CurrentDirectory = root & "\basel-ai-landing"
sh.Run "python app.py", 0, False

' --- Buchungskalender Basel-AI (Port 8505, FastAPI) ---
sh.CurrentDirectory = root & "\basel-ai-buchung"
sh.Run """" & root & "\basel-ai-buchung\.venv\Scripts\python.exe"" app.py", 0, False
