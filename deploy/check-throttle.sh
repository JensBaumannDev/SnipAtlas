#!/usr/bin/env bash
# Run with: bash deploy/check-throttle.sh [https://snipatlas.jensbaumann.com]
set -euo pipefail

BASE_URL="${1:-https://snipatlas.jensbaumann.com}"
JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT

curl -sf -o /dev/null -c "$JAR" "$BASE_URL/api/auth/csrf/"
TOKEN="$(awk '$6 == "csrftoken" { print $7 }' "$JAR")"

RESULTS=''
for n in 1 2 3 4 5 6; do
  STATUS="$(curl -s -o /dev/null -w '%{http_code}' -b "$JAR" -X POST "$BASE_URL/api/auth/login/" \
    -H 'Content-Type: application/json' -H "X-CSRFToken: $TOKEN" -H "Referer: $BASE_URL/" \
    -H "X-Forwarded-For: 203.0.113.$n" \
    -d '{"email":"throttle-check@example.com","password":"wrong"}')"
  echo "Login $n (X-Forwarded-For 203.0.113.$n): $STATUS"
  RESULTS="$RESULTS $STATUS"
done

if [ "$RESULTS" != ' 400 400 400 400 400 429' ]; then
  echo 'FAILED: expected five times 400, then 429 (wait a minute if all are 429)' >&2
  exit 1
fi
echo 'OK: login throttling works'
