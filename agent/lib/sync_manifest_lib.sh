#!/usr/bin/env bash
set -euo pipefail

CANONICAL="/Users/lute/project/Agent/Agent_hook/agent/lib/manifest.py"
TARGETS=(
  "/Users/lute/project/Agent/Agent_mcp/agent/lib/manifest.py"
  "/Users/lute/project/Agent/Agent_skills/agent/lib/manifest.py"
)

if [ ! -f "$CANONICAL" ]; then
  echo "FATAL: canonical manifest.py missing at $CANONICAL" >&2
  exit 1
fi

CHANGED=0
for t in "${TARGETS[@]}"; do
  if ! cmp -s "$CANONICAL" "$t"; then
    cp "$CANONICAL" "$t"
    echo "synced -> $t"
    CHANGED=$((CHANGED+1))
  fi
done

if [ "$CHANGED" -eq 0 ]; then
  echo "all 3 copies already byte-identical, nothing to do"
fi

echo "verify md5:"
if command -v md5sum >/dev/null 2>&1; then
  md5sum "$CANONICAL" "${TARGETS[@]}"
else
  md5 "$CANONICAL" "${TARGETS[@]}"
fi
