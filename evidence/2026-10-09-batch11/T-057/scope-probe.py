#!/usr/bin/env python3
"""Capture read-only T-057 integration locations; do not test product behavior."""
import datetime as dt
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
fork = Path("/Users/luckye/Documents/Code/synara")
commands = [
    (root, ["git", "rev-parse", "HEAD"]),
    (fork, ["git", "rev-parse", "HEAD"]),
    (fork, ["git", "status", "--short"]),
    (fork, ["rg", "-n", "a2aRaiseTool|a2aSubmitTool", "apps/server/src/agentGateway/Layers/AgentGateway.ts"]),
    (fork, ["rg", "-n", "a2a_raise|a2a_submit", "apps/server/src/agentGateway/computerToolPermission.ts"]),
    (fork, ["rg", "-n", "TaskCompletionNotifications", "apps/web/src/routes/__root.tsx"]),
    (fork, ["rg", "-n", "projectRowLabel|SIDEBAR_PROJECT_NAME_CLASS_NAME", "apps/web/src/components/Sidebar.tsx"]),
    (fork, ["rg", "-n", "enableSystemTaskCompletionNotifications", "apps/web/src/appSettings.ts", "apps/web/src/components/settings/DesktopSettingsPanels.tsx"]),
    (fork, ["rg", "-n", "silent:|suppressWhenForeground:|desktopBridge.notifications", "apps/web/src/notifications/taskCompletion.tsx"]),
    (fork, ["rg", "-n", "last.action|Date.now|readIssues", "packages/a2a-gates/src/core.ts"]),
    (root, ["rg", "-n", "def issue_state|JUDGMENT_PERIOD|SNOOZE_PERIOD", "scripts/inbox"]),
]
results = []
for cwd, argv in commands:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    results.append({"cwd": str(cwd), "argv": argv, "exit": result.returncode,
                    "stdout": result.stdout, "stderr": result.stderr})
print(json.dumps({"created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "claim": "read-only scope inspection; not red/green acceptance evidence",
                  "commands": results}, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(item["exit"] == 0 for item in results) else 1)
