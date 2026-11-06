#!/bin/bash
# Start TraceRail locally (no Cursor required). Stops when you close this window or press Ctrl+C.
cd "$(dirname "$0")" || { echo "Could not cd to script folder."; read -r -p "Press Enter to close."; exit 1; }

echo "TraceRail starter — $(date)"
echo "Folder: $(pwd)"
echo ""

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Missing .venv — run once in Terminal:"
  echo "  cd \"$(pwd)\""
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  echo ""
  read -r -p "Press Enter to close."
  exit 1
fi

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8000 is already in use. Another TraceRail or server may be running."
  echo "Try: open http://127.0.0.1:8000/"
  echo "Or stop the other process, then run this script again."
  echo ""
  read -r -p "Press Enter to close."
  exit 1
fi

echo "TraceRail: http://127.0.0.1:8000/"
echo "Leave this window open while you use the demo."
echo ""

if ! .venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000; then
  echo ""
  echo "Server stopped with an error (see lines above)."
  read -r -p "Press Enter to close."
  exit 1
fi
