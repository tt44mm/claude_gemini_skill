@echo off
REM Gemini Web Search - Quick Launcher
REM Speichert Ergebnis in X:\DEVELOPMENTS\gemini_search\results\

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo.
    echo  Gemini Web Search - Google Grounded Search
    echo  ==========================================
    echo.
    echo  Usage: gsearch "Deine Suchanfrage"
    echo         gsearch "Query" md        ^(fuer Markdown^)
    echo         gsearch "Query" json      ^(fuer JSON, default^)
    echo.
    echo  Ergebnis wird gespeichert in:
    echo  X:\DEVELOPMENTS\gemini_search\results\gemini_result.json/md
    echo.
    exit /b 1
)

set QUERY=%~1
set FORMAT=json

if /i "%~2"=="md" set FORMAT=md
if /i "%~2"=="markdown" set FORMAT=md

set SCRIPT_DIR=%~dp0
set RESULTS_DIR=X:\DEVELOPMENTS\gemini_search\results

echo.
echo  ========================================
echo   Gemini Web Search startet...
echo  ========================================
echo.

python "%SCRIPT_DIR%gemini_websearch.py" "%QUERY%" --format %FORMAT% --output gemini_result --dir "%RESULTS_DIR%" --verbose

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  ========================================
    echo   FERTIG! Sag Claude:
    echo   "lies die Gemini-Ergebnisse"
    echo  ========================================
    echo.
)

endlocal
