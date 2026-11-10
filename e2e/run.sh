#!/usr/bin/env bash
# Usage (depuis la racine du dépôt) : bash e2e/run.sh   — nécessite Node 18+ et les dépendances Python installées.
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8770}"; TMPDB="$(mktemp -d)/e2e.db"
python3 -m app.seed "$TMPDB" >/dev/null
# Faux fournisseur d'IA local (aucune clé, aucun réseau) pour tester l'assistant de bout en bout
FAKEPORT="${FAKEPORT:-8781}"
python3 tests/fake_llm.py "$FAKEPORT" >/dev/null 2>&1 &
FAKE=$!
EXAMGEN_LLM_PROVIDER=openai EXAMGEN_LLM_BASE_URL="http://127.0.0.1:$FAKEPORT/v1" EXAMGEN_LLM_MODEL=modele-demo EXAMGEN_LLM_API_KEY=cle-demo \
EXAMGEN_DB="$TMPDB" EXAMGEN_ADMIN_TOKEN=demo PORT="$PORT" python3 -m app >/dev/null 2>&1 &
SRV=$!; trap 'kill $SRV $FAKE 2>/dev/null' EXIT
for _ in $(seq 30); do curl -sf "localhost:$PORT/healthz" >/dev/null && break; sleep 0.3; done
cd e2e && [ -d node_modules ] || npm install --no-audit --no-fund
BASE="http://localhost:$PORT" node e2e.mjs
