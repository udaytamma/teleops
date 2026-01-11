#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PID="$ROOT_DIR/storage/api.pid"
UI_PID="$ROOT_DIR/storage/ui.pid"

stop_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      echo "Stopped PID $pid"
    else
      echo "No running process for $pid_file"
    fi
    rm -f "$pid_file"
  else
    echo "Missing $pid_file"
  fi
}

stop_pid "$API_PID"
stop_pid "$UI_PID"
