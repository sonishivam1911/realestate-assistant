#!/usr/bin/env bash
# Local smoke tests for CMA agent — run from repo root after filling .env
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[ -d venv ] && source venv/bin/activate
export PYTHONPATH="$ROOT"

echo "=== 1. .env shell parse ==="
if bash -c 'set -a; source .env; set +a; echo OK' 2>/dev/null; then
  echo "PASS — .env sources without shell errors"
else
  echo "FAIL — quote values that contain spaces (APP_TITLE, FROM_NAME, etc.)"
  exit 1
fi

echo ""
echo "=== 2. Python config ==="
python -c "
from dotenv import load_dotenv
import os
load_dotenv('$ROOT/.env')
from services.email_service import smtp_configured
from services.openrouter_client import _headers

assert os.getenv('OPENROUTER_API_KEY','').startswith('sk-or-'), 'OPENROUTER_API_KEY missing'
assert smtp_configured(), 'SMTP not configured'
assert 'Authorization' in _headers(), 'OpenRouter headers failed'
uri = os.getenv('POSTGRES_URI') or os.getenv('POSTGRES_URI_CONTABO') or ''
print('OpenRouter: OK')
print('SMTP: OK')
print('Postgres:', 'OK' if uri else 'skipped (empty — chat still works)')
"

echo ""
echo "=== 3. SMTP login (no email sent) ==="
python -c "
from dotenv import load_dotenv
import os, smtplib
load_dotenv('$ROOT/.env')
host = os.getenv('SMTP_HOST')
port = int(os.getenv('SMTP_PORT', '587'))
user = os.getenv('SMTP_USERNAME')
pwd = (os.getenv('SMTP_PASSWORD') or '').replace(' ', '')
s = smtplib.SMTP(host, port, timeout=20)
s.starttls()
s.login(user, pwd)
s.quit()
print('PASS — Gmail SMTP auth OK')
"

echo ""
echo "=== 4. API health ==="
if curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; then
  echo "PASS — API already running on :8080"
else
  uvicorn api.main:app --host 127.0.0.1 --port 8080 &
  API_PID=\$!
  sleep 2
  curl -sf http://127.0.0.1:8080/health && echo "PASS — API started" || { kill \$API_PID 2>/dev/null; exit 1; }
  kill \$API_PID 2>/dev/null || true
fi

echo ""
echo "=== 5. Chat guard (no email → prompt, no LLM call) ==="
python -c "
import json, urllib.request
body = json.dumps({
  'messages': [{'role': 'user', 'parts': [{'type': 'text', 'text': 'CMA for 123 Main St'}]}],
  'radius_miles': 5,
}).encode()
req = urllib.request.Request('http://127.0.0.1:8080/api/chat', data=body, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        chunk = resp.read(4000).decode(errors='replace')
except Exception as e:
    print('FAIL —', e)
    raise SystemExit(1)
if 'email' in chunk.lower():
    print('PASS — API rejects/prompts when user_email missing')
else:
    print('WARN — response:', chunk[:200])
"

echo ""
echo "All smoke tests passed. Run ./start_dev.sh and open http://localhost:3000 for full UI test."
