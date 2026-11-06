#!/usr/bin/env bash
# Usage (depuis la racine du dépôt) : bash e2e/run.sh   — nécessite Node 18+ et les dépendances Python installées.
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8770}"; TMPDB="$(mktemp -d)/e2e.db"
python3 -m app.seed "$TMPDB" >/dev/null
EXAMGEN_DB="$TMPDB" EXAMGEN_ADMIN_TOKEN=demo PORT="$PORT" python3 -m app >/dev/null 2>&1 &
SRV=$!; trap 'kill $SRV 2>/dev/null' EXIT
for _ in $(seq 30); do curl -sf "localhost:$PORT/healthz" >/dev/null && break; sleep 0.3; done
cd e2e && [ -d node_modules ] || npm install --no-audit --no-fund
BASE="http://localhost:$PORT" node e2e.mjs
