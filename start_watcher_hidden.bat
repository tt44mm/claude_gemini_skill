@echo off
REM Startet den Gemini Search Watcher UNSICHTBAR im Hintergrund
REM Ideal für Autostart (Task Scheduler bei Anmeldung)

start "" pythonw "%~dp0gemini_watcher.py"

echo Gemini Watcher im Hintergrund gestartet.
echo Log: X:\DEVELOPMENTS\gemini_search\watcher.log
