"""Synthetic provider boundary; all hooks and inbox commands use product entry points."""
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

root = Path(__file__).resolve().parent
turn = int(sys.argv[2])
if turn == 0:
    # A forked child inherits the CLI sandbox. Neither a source HOME read/write
    # nor a connection to the fake upstream's separate port may bypass it.
    sentinel = root / "source-home/private-sentinel"
    for mode in ("r", "a"):
        try:
            with sentinel.open(mode):
                pass
        except PermissionError:
            continue
        raise SystemExit(21)
    port = int((root / "upstream-port").read_text())
    try:
        connection = socket.create_connection(("127.0.0.1", port), timeout=1)
    except OSError:
        pass
    else:
        connection.close()
        raise SystemExit(22)
    state = json.loads((Path(os.environ["CLAUDE_CONFIG_DIR"]) / ".claude.json").read_bytes())
    if state != {"hasCompletedOnboarding": True, "projects": {str(Path.cwd()): {"hasTrustDialogAccepted": True}}}:
        raise SystemExit(23)
    print("fixture-sandbox-child-protection-PASS", flush=True)
    raise SystemExit(0)

settings = json.loads(os.environ["T093_FIXTURE_SETTINGS"])
command = shlex.split(settings["hooks"]["Stop"][0]["hooks"][0]["command"])
prompt_id = str(uuid.uuid4())


def run(argv, value=None):
    child = subprocess.run(argv, input=json.dumps(value) if value is not None else None,
                           text=True, capture_output=True, timeout=12)
    if child.returncode:
        # Status classes only; no raw terminal, hook body, auth or account data.
        print("fixture-native-command-failed", child.returncode, flush=True)
        raise SystemExit(24)
    return child.stdout


def hook(name, **extra):
    result = run(command, {"session_id": os.environ["A2A_SESSION"], "hook_event_name": name,
                          "prompt_id": prompt_id, **extra})
    if '"block"' in result:
        raise SystemExit(25)


hook("UserPromptSubmit", prompt=sys.argv[1])
if turn == 1:
    oauth = json.loads((Path(os.environ["CLAUDE_CONFIG_DIR"]) / ".credentials.json").read_bytes())["claudeAiOauth"]
    for expected in (400, 200):
        request = urllib.request.Request(os.environ["ANTHROPIC_BASE_URL"] + "/v1/messages",
            data=json.dumps({"messages": [{"role": "user", "content": sys.argv[1]}]}).encode(),
            headers={"authorization": "Bearer " + oauth["accessToken"], "content-type": "application/json"})
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            if response.status != expected:
                raise SystemExit(26)
            response.read()
    inbox = str(Path(command[1]).parent.parent.parent / "bin/inbox")
    receipt = json.loads(run([command[0], inbox, "list", "--role", "executor"]))
    if receipt.get("queued") is not True or receipt.get("delivered") is not False:
        raise SystemExit(27)
hook("Stop", stop_hook_active=False)
