@echo off
rem Werkstattrundgang - Kiosk-Start (erst "npm run build" ausgefuehrt haben)
cd /d "%~dp0"
if not exist dist\index.html (
  echo Fehler: dist\index.html fehlt. Erst "npm run build" ausfuehren.
  pause
  exit /b 1
)
start "rundgang-server" cmd /c "npm run preview"
timeout /t 3 /nobreak >nul
rem Edge ist auf Windows 11 immer vorhanden und per App-Pfad startbar.
rem Fuer Chrome stattdessen die auskommentierte Zeile verwenden.
start "" msedge --kiosk http://localhost:4173 --edge-kiosk-type=fullscreen --no-first-run
rem start "" chrome --kiosk http://localhost:4173
