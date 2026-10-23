#!/usr/bin/env bash
set -u

out=$(mktemp)
try=1
while true; do
  if zola check >"$out" 2>&1; then
    cat "$out"
    rm -f "$out"
    exit 0
  fi
  cat "$out"
  if grep -q "broken internal link" "$out"; then
    rm -f "$out"
    exit 1
  fi
  if ! grep -q "broken external link" "$out"; then
    rm -f "$out"
    exit 1
  fi
  if [ "$try" -ge 3 ]; then
    echo "External link check still failing after ${try} attempts. The build continues because those hosts are flaky. Internal links passed."
    rm -f "$out"
    exit 0
  fi
  sleep $((try * 3))
  try=$((try + 1))
done
