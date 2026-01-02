#!/usr/bin/env python3
"""
Gemini CLI Web Search Wrapper
Startet Gemini CLI mit Google Web Search und speichert Ergebnis als JSON/MD.

Usage:
    python gemini_websearch.py "Deine Suchanfrage"
    python gemini_websearch.py "Query" --format md
    python gemini_websearch.py "Query" --output ergebnis.json
"""

import argparse
import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Standard Output-Verzeichnis
DEFAULT_OUTPUT_DIR = Path(os.environ.get("GEMINI_OUTPUT_DIR", "."))
DEFAULT_OUTPUT_NAME = "gemini_result"


def run_gemini_search(
    query: str,
    output_format: str = "json",
    output_file: str = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    verbose: bool = False
) -> Path:
    """
    Führt Gemini CLI Web Search aus und speichert Ergebnis.
    
    Args:
        query: Suchanfrage
        output_format: "json" oder "md"
        output_file: Optionaler Dateiname (ohne Extension)
        output_dir: Ausgabe-Verzeichnis
        verbose: Zeige Gemini CLI Output
    
    Returns:
        Path zur Ergebnis-Datei
    """
    
    # Dateiname generieren
    if output_file:
        filename = output_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DEFAULT_OUTPUT_NAME}_{timestamp}"
    
    # Extension basierend auf Format
    ext = ".json" if output_format == "json" else ".md"
    output_path = output_dir / f"{filename}{ext}"
    
    # Gemini CLI Befehl zusammenstellen
    # Anführungszeichen escapen für shell=True auf Windows
    escaped_query = query.replace('"', '\\"')
    
    if output_format == "json":
        # JSON Output direkt von Gemini CLI
        cmd = f'gemini -p "{escaped_query}" --output-format json'
    else:
        # Für Markdown: Prompt anpassen damit Gemini MD formatiert
        md_prompt = f"""Recherchiere mit Google Web Search und erstelle einen gut strukturierten Markdown-Bericht zu: {escaped_query}

Formatiere die Antwort als Markdown mit Überschriften, Bullet Points, Links zu Quellen und einem Fazit."""
        escaped_md_prompt = md_prompt.replace('"', '\\"').replace('\n', ' ')
        
        cmd = f'gemini -p "{escaped_md_prompt}" --output-format text'
    
    if verbose:
        print(f"🔍 Starte Gemini Web Search...", file=sys.stderr)
        print(f"📝 Query: {query}", file=sys.stderr)
        print(f"📁 Output: {output_path}", file=sys.stderr)
    
    try:
        # Gemini CLI ausführen
        # shell=True nötig für Windows (.cmd Dateien)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,  # 5 Minuten Timeout
            shell=True
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            raise RuntimeError(f"Gemini CLI failed: {error_msg}")
        
        output_content = result.stdout
        
        # Bei JSON: Validieren und formatieren
        if output_format == "json":
            try:
                # Parse und re-format für bessere Lesbarkeit
                data = json.loads(output_content)
                
                # Metadaten hinzufügen
                wrapped_result = {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "source": "gemini-cli",
                    "model": "gemini-2.5-pro",
                    "result": data
                }
                output_content = json.dumps(wrapped_result, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # Falls kein valides JSON, als Text wrappen
                wrapped_result = {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "source": "gemini-cli",
                    "raw_response": output_content
                }
                output_content = json.dumps(wrapped_result, indent=2, ensure_ascii=False)
        
        # In Datei schreiben
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_content, encoding="utf-8")
        
        if verbose:
            print(f"✅ Ergebnis gespeichert: {output_path}", file=sys.stderr)
        
        return output_path
        
    except subprocess.TimeoutExpired:
        raise TimeoutError("Gemini CLI Timeout nach 5 Minuten")
    except FileNotFoundError:
        raise RuntimeError(
            "Gemini CLI nicht gefunden. Installiere mit:\n"
            "npm install -g @google/gemini-cli"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Gemini CLI Web Search Wrapper - Speichert Ergebnisse als JSON/MD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python gemini_websearch.py "Aktuelle KI Entwicklungen"
  python gemini_websearch.py "PHIDIAS Features" --format md
  python gemini_websearch.py "Query" --output meine_recherche
  python gemini_websearch.py "Query" --dir C:\\Results
"""
    )
    
    parser.add_argument("query", help="Suchanfrage")
    parser.add_argument(
        "--format", "-f",
        choices=["json", "md"],
        default="json",
        help="Output-Format (default: json)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Dateiname ohne Extension (default: gemini_result_TIMESTAMP)"
    )
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output-Verzeichnis (default: aktuelles Verzeichnis)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Zeige Fortschritt"
    )
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Gib nur den Dateipfad aus (für Scripting)"
    )
    
    args = parser.parse_args()
    
    try:
        output_path = run_gemini_search(
            query=args.query,
            output_format=args.format,
            output_file=args.output,
            output_dir=args.dir,
            verbose=args.verbose or not args.print_path
        )
        
        if args.print_path:
            print(output_path)
        else:
            print(f"\n📄 Ergebnis: {output_path}")
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
