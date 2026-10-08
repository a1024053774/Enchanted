#!/usr/bin/env python3
"""Probe the requested membership HTTP contract without importing its implementation."""
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

root = Path(__file__).resolve().parent
label, endpoint = sys.argv[1:]
target = root / (label + ".json")
if target.exists():
    raise SystemExit("Evidence label already exists")
url = endpoint + "/api/a2a/membership"
class FirstResponse(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
opener = urllib.request.build_opener(FirstResponse)
try:
    with opener.open(url, timeout=10) as response:
        status, body = response.status, response.read().decode("utf-8")
except urllib.error.HTTPError as error:
    status, body = error.code, error.read().decode("utf-8")
try:
    payload = json.loads(body)
except json.JSONDecodeError:
    payload = None
passed = status == 200 and isinstance(payload, dict) and payload.get("ok") is True and payload.get("tasks") == []
record = {"command": sys.argv, "url": url, "redirect_policy": "record first response", "expected": {"status": 200, "ok": True, "tasks": []},
          "observed": {"status": status, "body": body}, "result": "PASS" if passed else "NO_GO"}
target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(target.read_text(encoding="utf-8"))
raise SystemExit(0 if passed else 1)
