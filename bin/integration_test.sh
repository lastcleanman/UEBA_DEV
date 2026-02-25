#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DOCKER="auto"   # auto|on|off
KEEP_STACK="false"

usage() {
  cat <<'USAGE'
Usage: bin/integration_test.sh [options]

Options:
  --docker            Force Docker-based runtime smoke tests.
  --no-docker         Skip Docker-based runtime smoke tests.
  --keep-stack        Keep docker compose stack running after tests.
  -h, --help          Show this help message.

What this script runs:
  1) Backend static check      : python3 -m compileall backend (or python fallback)
  2) (Optional) Docker smoke   : compose up, backend uvicorn, API health checks
USAGE
}

log() { printf "\n[%s] %s\n" "$1" "$2"; }
ok() { printf "[PASS] %s\n" "$1"; }
warn() { printf "[WARN] %s\n" "$1"; }
fail() { printf "[FAIL] %s\n" "$1"; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --docker) RUN_DOCKER="on" ;;
    --no-docker) RUN_DOCKER="off" ;;
    --keep-stack) KEEP_STACK="true" ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown argument: $arg" ;;
  esac
done

cd "$ROOT_DIR"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  fail "python3 (or python) is required"
fi

command -v npm >/dev/null 2>&1 || fail "npm is required"

log "STEP" "Backend static compile check (using ${PYTHON_BIN})"
"${PYTHON_BIN}" -m compileall backend
ok "Backend compileall"

has_docker_cli="false"
if command -v docker >/dev/null 2>&1; then
  has_docker_cli="true"
fi

if [[ "$RUN_DOCKER" == "auto" && "$has_docker_cli" == "false" ]]; then
  warn "Docker CLI not found, skipping runtime smoke tests"
  exit 0
fi

if [[ "$RUN_DOCKER" == "on" && "$has_docker_cli" == "false" ]]; then
  fail "--docker specified but Docker CLI is not available"
fi

if [[ "$RUN_DOCKER" == "off" ]]; then
  log "STEP" "Docker smoke tests skipped by --no-docker"
  exit 0
fi

if [[ ! -f docker-compose.yml ]]; then
  fail "docker-compose.yml not found in $ROOT_DIR"
fi

cleanup() {
  if [[ "$KEEP_STACK" == "false" ]]; then
    log "CLEANUP" "Stopping docker compose stack"
    docker compose down >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

log "STEP" "Compose config validation"
docker compose config >/dev/null
ok "docker compose config"

log "STEP" "Starting compose services"
docker compose up -d --build
ok "docker compose up"

log "STEP" "Starting backend API server inside container"
docker compose exec -T ueba-backend bash -lc \
  "pkill -f 'uvicorn backend.main:app' >/dev/null 2>&1 || true; if command -v python3 >/dev/null 2>&1; then nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 >/tmp/uvicorn.log 2>&1 & else nohup python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 >/tmp/uvicorn.log 2>&1 & fi"

log "STEP" "Waiting for backend health endpoint"
for i in {1..30}; do
  if curl -fsS http://localhost:8000/ >/dev/null 2>&1; then
    ok "Backend health endpoint ready"
    break
  fi
  sleep 2
  if [[ "$i" -eq 30 ]]; then
    docker compose exec -T ueba-backend bash -lc "tail -n 200 /tmp/uvicorn.log || true"
    fail "Backend health endpoint did not become ready in time"
  fi
done

log "STEP" "Running runtime API smoke checks"
curl -fsS http://localhost:8000/ >/dev/null
curl -fsS http://localhost:8000/api/v1/pipeline/status >/dev/null
curl -fsS http://localhost:8000/api/v1/system/license >/dev/null
curl -fsS http://localhost:8000/api/v1/roadmap/capabilities >/dev/null
ok "Runtime API smoke checks"

log "DONE" "All integrated tests passed"