@echo off
REM Startet den Gemini Search Watcher im Hintergrund
REM Kann auch im Task Scheduler eingetragen werden für Autostart

echo.
echo  ========================================
echo   Gemini Search Watcher
echo  ========================================
echo.
echo  Ueberwacht: X:\DEVELOPMENTS\gemini_search\requests\
echo  Ergebnisse: X:\DEVELOPMENTS\gemini_search\results\
echo.
echo  Druecke Ctrl+C zum Beenden
echo.
echo  ========================================
echo.

python "%~dp0gemini_watcher.py"

pause
