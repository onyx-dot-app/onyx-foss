#!/usr/bin/env bash
set -Eeuo pipefail

# QYBE development launcher.
# Starts Docker infrastructure, applies DB migrations, then runs:
#   - FastAPI backend with hot reload
#   - Next.js frontend with hot reload
#
# No Git commands are executed.

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/.dev-logs"

API_URL="${API_URL:-http://127.0.0.1:8080}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"
INTERNAL_URL="${INTERNAL_URL:-$API_URL}"
OPEN_BROWSER="${OPEN_BROWSER:-0}"
STOP_INFRA_ON_EXIT="${STOP_INFRA_ON_EXIT:-0}"

API_PID=""
WEB_PID=""

log() {
  printf '\n\033[1;36m[QYBE]\033[0m %s\n' "$*"
}

fail() {
  printf '\n\033[1;31m[QYBE ERROR]\033[0m %s\n' "$*" >&2
  exit 1
}

# shellcheck disable=SC2329
cleanup() {
  local exit_code=$?

  trap - EXIT INT TERM

  log "Stopping frontend and API processes..."

  if [[ -n "$WEB_PID" ]] && kill -0 "$WEB_PID" 2>/dev/null; then
    kill "$WEB_PID" 2>/dev/null || true
  fi

  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi

  if [[ -n "$WEB_PID" ]]; then
    wait "$WEB_PID" 2>/dev/null || true
  fi

  if [[ -n "$API_PID" ]]; then
    wait "$API_PID" 2>/dev/null || true
  fi

  if [[ "$STOP_INFRA_ON_EXIT" == "1" ]]; then
    log "Stopping Docker development infrastructure..."
    (
      cd "$ROOT_DIR"
      ods compose dev --down
    ) || true
  else
    log "Docker infrastructure remains running."
    printf 'To stop it later, run:\n  cd %q && source .venv/bin/activate && ods compose dev --down\n' "$ROOT_DIR"
  fi

  exit "$exit_code"
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

# shellcheck disable=SC1091
[[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
export PATH="$HOME/.bun/bin:$PATH"

[[ -d "$VENV_DIR" ]] || fail "Missing virtual environment: $VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

command -v ods >/dev/null 2>&1 || fail "'ods' was not found in the virtual environment."
command -v bun >/dev/null 2>&1 || fail "'bun' was not found. Expected: $HOME/.bun/bin/bun"
command -v docker >/dev/null 2>&1 || fail "'docker' was not found."
docker info >/dev/null 2>&1 || fail "Docker is not running or the current user cannot access it."

mkdir -p "$LOG_DIR"

log "Starting QYBE Docker infrastructure..."
ods compose dev --infra --no-ee

log "Writing infrastructure ports to .vscode/.env..."
ods env

log "Applying database migrations..."
ods db upgrade

log "Starting backend API..."
ods backend api --no-ee > >(tee "$LOG_DIR/api.log") 2>&1 &
API_PID=$!

log "Starting frontend..."
INTERNAL_URL="$INTERNAL_URL" ods web dev > >(tee "$LOG_DIR/frontend.log") 2>&1 &
WEB_PID=$!

printf '\n\033[1;32mQYBE development environment is starting.\033[0m\n'
printf 'Frontend: %s\n' "$FRONTEND_URL"
printf 'API:      %s\n' "$API_URL"
printf 'ReDoc:    %s/redoc\n' "$API_URL"
printf 'API log:  %s/api.log\n' "$LOG_DIR"
printf 'Web log:  %s/frontend.log\n' "$LOG_DIR"
printf '\nPress Ctrl+C to stop the frontend and API.\n'

if [[ "$OPEN_BROWSER" == "1" ]] && command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$FRONTEND_URL" >/dev/null 2>&1 || true
  xdg-open "$API_URL/redoc" >/dev/null 2>&1 || true
fi

# Exit when either development service stops unexpectedly.
wait -n "$API_PID" "$WEB_PID"
fail "The frontend or API process stopped unexpectedly. Check .dev-logs/."
