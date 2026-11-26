"""Read the canonical contract and expose inert capability metadata."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def contract():
    return (ROOT / 'HARNESS.md').read_bytes()

def worker_contract():
    text = contract().decode('utf-8')
    return text.split('<!-- BEGIN WORKER -->', 1)[1].split('<!-- END WORKER -->', 1)[0].strip()

def registry():
    return json.loads((ROOT / 'CAPABILITIES.json').read_text(encoding='utf-8'))

def suggest(target):
    text = target.casefold()
    return [r for r in registry()['routes'] if not r['keywords'] or
            any(k in text for k in r['keywords'])]
