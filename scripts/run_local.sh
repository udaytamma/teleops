#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv. Run: /opt/homebrew/bin/python3.12 -m venv .venv" >&2
  exit 1
fi

source .venv/bin/activate

python -m teleops.init_db

API_LOG="$ROOT_DIR/storage/api.log"
UI_LOG="$ROOT_DIR/storage/ui.log"
API_PID="$ROOT_DIR/storage/api.pid"
UI_PID="$ROOT_DIR/storage/ui.pid"

nohup uvicorn teleops.api.app:app --host 127.0.0.1 --port 8000 >"$API_LOG" 2>&1 &
echo $! > "$API_PID"
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
nohup streamlit run ui/streamlit_app/app.py \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.headless true \
  --browser.gatherUsageStats false \
  >"$UI_LOG" 2>&1 &
echo $! > "$UI_PID"

echo "API running on http://127.0.0.1:8000"
echo "UI running on http://127.0.0.1:8501"
echo "Logs: $API_LOG and $UI_LOG"
echo "PIDs: $API_PID and $UI_PID"
