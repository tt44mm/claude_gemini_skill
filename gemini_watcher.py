#!/usr/bin/env python3
"""
Gemini Search Watcher - Simplified Version
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Konfiguration
BASE_DIR = Path(__file__).resolve().parent
REQUESTS_DIR = BASE_DIR / "requests"
RESULTS_DIR = BASE_DIR / "results"
LOG_FILE = BASE_DIR / "watcher.log"

POLL_INTERVAL = 2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def ensure_directories():
    REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def clean_response(text: str) -> str:
    """Entferne Gemini CLI Meta-Output."""
    lines = text.split('\n')
    cleaned_lines = []
    
    skip_phrases = [
        'Loaded cached credentials',
        'Error executing tool',
        'not found in registry',
        'I am ready for your command',
        'I await your first command',
        "I'm ready for your first command",
        "Okay, I'm ready",
        "Did you mean one of:",
        "YOLO mode is enabled",
        "automatically approved",
        "node.exe :",
        "gemini.ps1:",
        "CategoryInfo",
        "FullyQualifiedErrorId",
        "NativeCommandError",
        "RemoteException",
    ]
    
    for line in lines:
        # Skip lines starting with + (PowerShell error continuation)
        if line.strip().startswith('+'):
            continue
        if line.strip().startswith('In C:\\'):
            continue
            
        should_skip = False
        for phrase in skip_phrases:
            if phrase.lower() in line.lower():
                should_skip = True
                break
        
        if not should_skip:
            cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    if result.startswith('\ufeff'):
        result = result[1:]
    
    return result


def process_request(request_file: Path):
    try:
        with open(request_file, 'r', encoding='utf-8') as f:
            request = json.load(f)
        
        query = request.get('query', '')
        output_format = request.get('format', 'md')
        request_id = request.get('id', request_file.stem)
        
        if not query:
            logger.error(f"Leere Query in {request_file}")
            return
        
        logger.info(f"🔍 Starte Suche: {query[:50]}...")
        
        status_file = RESULTS_DIR / "status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "searching",
                "query": query,
                "started": datetime.now().isoformat(),
                "request_id": request_id
            }, f, indent=2, ensure_ascii=False)
        
        # Query escapen
        safe_query = query.replace('"', "'").replace('\n', ' ').replace('`', "'")
        
        output_file = RESULTS_DIR / "temp_output.txt"
        
        # Einfacher CMD Befehl ohne PowerShell
        cmd = f'gemini -p "{safe_query}" --output-format text --yolo'
        
        logger.info(f"Command: {cmd}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300,
            shell=True,
            cwd=str(BASE_DIR)  # Working directory mit GEMINI.md
        )
        
        # stdout und stderr kombinieren
        response_text = result.stdout
        if result.stderr:
            logger.info(f"Stderr: {result.stderr[:200]}")
        
        logger.info(f"Raw stdout length: {len(response_text)}")
        
        response_text = clean_response(response_text)
        
        if not response_text or len(response_text) < 50:
            raise RuntimeError(f"Zu kurze Antwort: {response_text[:100]}")
        
        logger.info(f"Cleaned response length: {len(response_text)}")
        
        # Ergebnis speichern
        if output_format == "md":
            result_file = RESULTS_DIR / "gemini_result.md"
            result_file.write_text(response_text, encoding='utf-8')
        else:
            result_file = RESULTS_DIR / "gemini_result.json"
            wrapped = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "source": "gemini-cli",
                "model": "gemini-2.5-pro",
                "response": response_text
            }
            result_file.write_text(
                json.dumps(wrapped, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        
        ready_file = RESULTS_DIR / "ready.flag"
        ready_file.write_text(json.dumps({
            "ready": True,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "query": query,
            "result_file": str(result_file),
            "format": output_format
        }, indent=2, ensure_ascii=False), encoding='utf-8')
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "complete",
                "query": query,
                "completed": datetime.now().isoformat(),
                "request_id": request_id,
                "result_file": str(result_file)
            }, f, indent=2, ensure_ascii=False)
        
        request_file.unlink()
        logger.info(f"✅ Suche abgeschlossen: {result_file}")
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        
        status_file = RESULTS_DIR / "status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        try:
            request_file.unlink()
        except:
            pass


def watch_requests():
    logger.info("=" * 50)
    logger.info("🚀 Gemini Search Watcher gestartet")
    logger.info(f"📁 Working Dir: {BASE_DIR}")
    logger.info("=" * 50)
    
    ensure_directories()
    
    gemini_md = BASE_DIR / "GEMINI.md"
    if gemini_md.exists():
        logger.info(f"✅ GEMINI.md gefunden")
    else:
        logger.warning("⚠️ Keine GEMINI.md")
    
    status_file = RESULTS_DIR / "status.json"
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump({
            "status": "idle",
            "watcher": "running",
            "started": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    while True:
        try:
            request_files = list(REQUESTS_DIR.glob("*.request.json"))
            for request_file in request_files:
                process_request(request_file)
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("⏹️ Watcher beendet")
            break
        except Exception as e:
            logger.error(f"Watcher-Fehler: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    watch_requests()
