"""Collect only allowlisted usage diagnostics; never emit credential values."""
import base64
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import socket


result = {"observed_at": datetime.now(timezone.utc).isoformat()}
result["dns"] = {}
for host in ["chatgpt.com", "api.anthropic.com", "api2.cursor.sh"]:
    result["dns"][host] = sorted({row[4][0] for row in socket.getaddrinfo(host, 443)})

result["worker_environment"] = {
    "HOME": os.environ.get("HOME"),
    "present_keys": [key for key in [
        "CODEX_HOME", "CLAUDE_CONFIG_DIR", "CLAUDE_SECURESTORAGE_CONFIG_DIR",
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
    ] if key in os.environ],
    "production_environment_inspected": False,
}

result["credentials_metadata"] = []
for path in [Path.home() / ".codex/auth.json", Path.home() / ".claude/.credentials.json"]:
    metadata = {"path": str(path), "exists": path.is_file()}
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        metadata["fields"] = sorted(data)
        for key in ["tokens", "claudeAiOauth"]:
            if isinstance(data.get(key), dict):
                metadata[key + "_fields"] = sorted(data[key])
        if isinstance(data.get("tokens"), dict):
            token = data["tokens"].get("access_token", "")
            try:
                payload = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "==="))
                metadata["access_token_exp"] = payload.get("exp")
            except (ValueError, IndexError):
                metadata["access_token_exp"] = None
        if isinstance(data.get("claudeAiOauth"), dict):
            metadata["expiresAt"] = data["claudeAiOauth"].get("expiresAt")
    result["credentials_metadata"].append(metadata)

base = Path.home() / "Library/Application Support/a2a-workbench"
result["provider_status"] = {}
safe_fields = {"provider", "status", "available", "authStatus", "authType", "version", "checkedAt"}
for name in ["codex", "claudeAgent", "cursor"]:
    data = json.loads((base / f"userdata/provider-status/{name}.json").read_text(encoding="utf-8"))
    result["provider_status"][name] = {key: value for key, value in data.items() if key in safe_fields}

# Preserve only the exact, non-secret failure observed. Count other warning messages without
# copying their context, because arbitrary logs can include credentials or user content.
result["usage_log_summary"] = {}
safe_pattern = re.compile(
    r'(\d{2}:\d{2}:\d{2}\.\d{3}) WARN \[provider-usage:(codex|claude)\] '
    r'((?:codex|claude) usage endpoint unreachable) '
    r'message="(Outbound destination resolved to a private, local, reserved, or invalid address\.)"'
)
scope_pattern = re.compile(r'\[provider-usage:([^\]]+)\] ([^\n]*?)(?: message=| status=|$)')
for relative in ["userdata/logs/server.log", "workbench-launch.log"]:
    path = base / relative
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    messages = Counter()
    excerpts = []
    for index, line in enumerate(lines, 1):
        scoped = scope_pattern.search(line)
        if scoped:
            # Message summaries are classified, never copied from an unknown logging path.
            if "endpoint unreachable" in scoped[2]:
                messages[scoped[1] + ":endpoint-unreachable"] += 1
            else:
                messages[scoped[1] + ":other-message"] += 1
        match = safe_pattern.search(line)
        if match:
            excerpts.append({"line": index, "time_utc": match[1], "provider": match[2],
                             "message": match[3], "error": match[4]})
    result["usage_log_summary"][relative] = {
        "line_count": len(lines), "messages": dict(messages),
        "first_failures": excerpts[:4], "last_failures": excerpts[-4:],
    }

print(json.dumps(result, ensure_ascii=False, indent=2))
