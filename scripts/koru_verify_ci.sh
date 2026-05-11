#!/usr/bin/env bash
set -euo pipefail

echo "=== Universal Quality Gates (strict) ==="

echo "1. Running project tests..."
if command -v task >/dev/null 2>&1; then
  task test
elif command -v pytest >/dev/null 2>&1; then
  pytest -q
elif [ -f "package.json" ] && command -v npm >/dev/null 2>&1; then
  npm test
elif [ -f "Makefile" ]; then
  make test
else
  echo "No supported test runner found"
  exit 1
fi
echo "✅ tests passed"

echo "2. Running TestQL scenarios (optional)..."
if command -v testql >/dev/null 2>&1; then
  if rg --files -g "*.testql.toon.yaml" >/dev/null 2>&1; then
    testql suite --pattern "*.testql.toon.yaml" --output console --fail-fast
    echo "✅ testql passed"
  else
    echo "ℹ️ no testql scenarios"
  fi
else
  echo "ℹ️ testql not installed"
fi

echo "3. Running WUP status (optional)..."
if command -v wup >/dev/null 2>&1 && [ -f "wup.yaml" ]; then
  wup status
  echo "✅ wup status ok"
else
  echo "ℹ️ wup not configured"
fi

echo "4. Running Regix gates (required when configured)..."
if command -v regix >/dev/null 2>&1 && [ -f "regix.yaml" ]; then
  regix gates
  echo "✅ regix gates passed"
else
  echo "ℹ️ regix not configured"
fi

echo "=== Quality Gates Complete (strict) ==="
