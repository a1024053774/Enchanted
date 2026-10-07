#!/bin/sh
# managed by muster; reinstalling the integration replaces this file.
# MUSTER_INTEGRATION_ID=qodercli
# MUSTER_INTEGRATION_VERSION=3

[ "${1:-}" = "session" ] || exit 0
[ "${MUSTER_ENV:-}" = "1" ] || exit 0
[ -n "${MUSTER_SOCKET_PATH:-}" ] || exit 0
[ -n "${MUSTER_PANE_ID:-}" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

python3 -c '
import json
import os
import subprocess
import sys
import time

try:
    payload = json.load(sys.stdin)
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError
    subprocess.run(
        [
            os.environ.get("MUSTER_BIN_PATH") or "muster",
            "pane", "report-agent-session", os.environ["MUSTER_PANE_ID"],
            "--source", "muster:qodercli", "--agent", "qodercli",
            "--agent-session-id", session_id, "--seq", str(time.time_ns()),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=1,
        check=False,
    )
except Exception:
    pass
' 2>/dev/null || true
