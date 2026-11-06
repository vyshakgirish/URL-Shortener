#!/usr/bin/env bash
# Quick smoke test. Usage: ./test.sh [base_url]
BASE="${1:-http://localhost}"
echo "== Health check =="
curl -s "$BASE/healthz"; echo
echo "== Shorten https://www.redhat.com =="
RESP=$(curl -s -X POST "$BASE/api/shorten" -H 'Content-Type: application/json' -d '{"url":"https://www.redhat.com"}')
echo "$RESP"
CODE=$(echo "$RESP" | sed -n 's/.*"code":"\([^"]*\)".*/\1/p')
echo "== Follow short link (expect 302) =="
curl -sI "$BASE/$CODE" | head -n 5
echo "== Stats =="
curl -s "$BASE/api/stats/$CODE"; echo
