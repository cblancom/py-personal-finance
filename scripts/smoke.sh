#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:${WEB_PORT:-3001}}"
RETRIES="${SMOKE_RETRIES:-30}"
DELAY="${SMOKE_DELAY:-1}"

fail() {
  echo "smoke: $*" >&2
  exit 1
}

fetch() {
  curl -fsS --max-time 10 "$1"
}

wait_for() {
  local url="$1"
  local attempt

  for attempt in $(seq 1 "$RETRIES"); do
    if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$DELAY"
  done

  return 1
}

wait_for "$BASE_URL/" ||
  fail "la web no responde en $BASE_URL"

wait_for "$BASE_URL/api/health" ||
  fail "la API no responde en $BASE_URL"

fetch "$BASE_URL/" | grep -q 'Py Personal Finance' ||
  fail "la web no devuelve la aplicación"

fetch "$BASE_URL/healthz" | grep -qx 'ok' ||
  fail "healthz no responde ok"

fetch "$BASE_URL/api/health" | grep -q '"status":"ok"' ||
  fail "la API no reporta status ok"

fetch "$BASE_URL/api/health" | grep -q '"database":"ok"' ||
  fail "la API no reporta la base disponible"

fetch "$BASE_URL/api/resumen" | grep -q '"balance"' ||
  fail "el resumen no responde"

fetch "$BASE_URL/ruta-smoke-inexistente" | grep -q 'Py Personal Finance' ||
  fail "el fallback SPA no funciona"

echo "smoke: OK en $BASE_URL"
