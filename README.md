# Gemini Search Watcher & Claude Skill

Dieses Projekt stellt eine Brücke (Bridge) zwischen **Claude Desktop** und der **Google Gemini CLI** her. Da Web-Suchen und externe CLIs in isolierten AI-Umgebungen oft Timeouts verursachen oder nicht direkt verfügbar sind, nutzt dieses System einen asynchronen "File-Watcher"-Ansatz.

Das System besteht aus zwei Hauptteilen:
1. Einem Hintergrund-Skript (`gemini_watcher.py`), das auf Suchaufträge wartet und die Gemini CLI steuert.
2. Einer Dateisystem-Schnittstelle, die es Claude (oder dir manuell) erlaubt, Suchen zu beauftragen und Ergebnisse abzuholen.

---

## 📋 Voraussetzungen

1. **Python 3.x**: Muss installiert sein.
2. **Google Gemini CLI**: Das Tool `gemini` muss im System-PATH verfügbar sein und funktionieren (d.h. Authentifizierung muss bereits erfolgt sein).
3. **API Key**: Ein gültiger Google API Key muss für die CLI konfiguriert sein (Standardumgebungsvariablen).

---

## 🚀 Starten des Systems

Bevor Anfragen verarbeitet werden können, muss der "Watcher" gestartet werden. Dieser läuft permanent im Hintergrund.

### Option A: Windows Batch-Datei (Empfohlen)
Doppelklicke auf:
- `start_watcher.bat`: Öffnet ein Fenster, in dem du die Logs siehst. (Gut zum Testen)
- `start_watcher_hidden.bat`: Startet den Prozess komplett im Hintergrund.

### Option B: Direkt über Python
Öffne ein Terminal im Projektordner und führe aus:
```bash
python gemini_watcher.py
```

Du solltest die Meldung sehen: `🚀 Gemini Search Watcher gestartet`.

---

## ✍️ Manuelle Nutzung / Anfrage triggern

Du kannst das System testen oder manuell nutzen, indem du einfach eine Textdatei erstellst. Du musst dazu keine Programmierkenntisse haben, nur Textdateien speichern können.

### Schritt 1: Datei erstellen
Erstelle eine neue Textdatei im Ordner:
`requests/`

Der Dateiname muss auf `.request.json` enden, zum Beispiel `meine_suche.request.json`.

### Schritt 2: Inhalt einfügen
Der Inhalt muss valides JSON sein. Kopiere diese Vorlage:

```json
{
  "id": "manuelle_suche_01",
  "query": "Wie ist das Wetter in Berlin heute?",
  "format": "md"
}
```

**Erklärung der Felder:**
- `id`: Eine beliebige ID, um deine Anfrage wiederzufinden (optional, wird sonst generiert).
- `query`: Deine eigentliche Suchanfrage an Gemini.
- `format`: Entweder `"md"` (für Markdown-Text) oder `"json"` (für strukturierte Daten).

### Schritt 3: Speichern & Warten
Sobald du die Datei speicherst, passiert folgendes:
1. Der Watcher bemerkt die neue Datei sofort.
2. Er benennt sie um oder löscht sie, um zu zeigen, dass sie in Bearbeitung ist.
3. Er startet die Gemini CLI im Hintergrund.
4. Du siehst den Status live in der Datei `results/status.json`.

---

## 📂 Ergebnisse abrufen

Alle Ausgaben landen im Ordner `results/`.

| Datei | Beschreibung |
|-------|--------------|
| `status.json` | Zeigt den aktuellen Systemzustand (`idle`, `searching`, `complete`, `error`). Hier schaut man zuerst rein. |
| `gemini_result.md` | Das fertige Suchergebnis als lesbarer Text (wenn format="md"). |
| `gemini_result.json` | Das fertige Suchergebnis als JSON-Objekt (wenn format="json"). |
| `ready.flag` | Eine Hilfsdatei für Skripte, die signalisiert: "Fertig, du kannst lesen". |

### Fehlerbehebung
Falls etwas nicht klappt:
1. Prüfe die Datei `watcher.log` im Hauptverzeichnis.
2. Stelle sicher, dass `gemini` in deiner Konsole funktioniert (Befehl `gemini --version`).
