#!/bin/bash
# Avengers Dev - themed status line. Claude Code pipes session JSON on stdin.
python3 -c '
import json, sys, os, random
raw = sys.stdin.read()
try:
    d = json.loads(raw) if raw.strip() else {}
except Exception:
    d = {}
model = (d.get("model") or {}).get("display_name", "Claude")
ws = d.get("workspace") or {}
cwd = ws.get("current_dir") or d.get("cwd") or os.getcwd()
cwd = os.path.basename(os.path.normpath(cwd))
verbs = ["Assembling the team", "Suiting up", "Scanning for threats", "Forging",
         "Reviewing", "Analyzing", "Calculating", "Strategizing", "Deploying",
         "Securing the perimeter"]
print(f"\U0001F9B8 Avengers • {model} • {cwd} • {random.choice(verbs)}")
'
