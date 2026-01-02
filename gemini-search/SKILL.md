---
name: gemini-search
description: Performs automatic web search using Gemini CLI with Google Search grounding. Triggers on "Gemini search:", "suche mit Gemini", "use Gemini to find". Claude writes a request file, the Watcher executes the search, Claude reads the result. FREE Gemini 2.5 Pro with 1000 requests/day.
---

# Gemini Search Skill (Automatischer Workflow)

Vollautomatische Web-Recherche mit Gemini CLI und Google Search Grounding.

## Workflow

### Schritt 1: Request-Datei schreiben

Claude schreibt eine JSON-Datei nach:
```
X:\DEVELOPMENTS\gemini_search\requests\search.request.json
```

Inhalt:
```json
{
  "id": "unique-id",
  "query": "Die Suchanfrage",
  "format": "json"
}
```

Format-Optionen: `"json"` oder `"md"`

### Schritt 2: Watcher verarbeitet automatisch

Der Watcher (muss im Hintergrund laufen!) erkennt die Datei und:
1. Führt Gemini CLI aus
2. Speichert Ergebnis in `results/gemini_result.json`
3. Schreibt `results/ready.flag` als Signal

### Schritt 3: Auf Ergebnis warten

Claude prüft `X:\DEVELOPMENTS\gemini_search\results\status.json`:
- `"status": "idle"` → Watcher bereit, kein Request
- `"status": "searching"` → Suche läuft, warten
- `"status": "complete"` → Ergebnis bereit!
- `"status": "error"` → Fehler aufgetreten

### Schritt 4: Ergebnis lesen

Wenn status = complete, lies:
```
X:\DEVELOPMENTS\gemini_search\results\gemini_result.json
```

## Wichtige Pfade

```
X:\DEVELOPMENTS\gemini_search\
├── requests\                    ← Claude schreibt hier
│   └── search.request.json
├── results\                     ← Claude liest hier
│   ├── gemini_result.json       ← Suchergebnis
│   ├── gemini_result.md         ← Markdown (falls format=md)
│   ├── status.json              ← Aktueller Status
│   └── ready.flag               ← Signal: Ergebnis bereit
├── gemini_watcher.py            ← Hintergrund-Service
├── start_watcher.bat            ← Watcher starten (sichtbar)
├── start_watcher_hidden.bat     ← Watcher starten (unsichtbar)
└── watcher.log                  ← Log-Datei
```

## Voraussetzungen

1. **Watcher muss laufen!** Starte einmalig:
   ```cmd
   X:\DEVELOPMENTS\gemini_search\start_watcher.bat
   ```
   
2. Gemini CLI installiert und eingeloggt

## Beispiel Request

```json
{
  "id": "search-20250102-143000",
  "query": "Aktuelle Entwicklungen KI in der Schulbildung Deutschland 2025",
  "format": "json"
}
```

## Status-Datei Format

```json
{
  "status": "complete",
  "query": "...",
  "completed": "2025-01-02T14:30:45",
  "request_id": "search-20250102-143000",
  "result_file": "X:\\...\\gemini_result.json"
}
```

## Timeout / Polling

- Claude sollte max 60 Sekunden auf Ergebnis warten
- Prüfe status.json alle 3-5 Sekunden
- Bei Timeout: User informieren, Watcher-Status prüfen
