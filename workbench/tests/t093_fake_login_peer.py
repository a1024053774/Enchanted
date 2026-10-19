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
import errno
import importlib.util

def record(pid, role, ppid=None):
    with open(os.environ['A2A_PROFILE_PROCESS_LOG'], 'a') as stream:
        stream.write(json.dumps({'pid':pid,'ppid':os.getpid() if ppid is None else ppid,'role':role,'profile':'C inherited'})+'\n')

record(os.getpid(), 'fixture peer', os.getppid())

root = Path(__file__).resolve().parent
turn = int(sys.argv[2])
if turn == 0:
    # A forked child inherits the CLI sandbox. Neither a source HOME read/write
    # nor a connection to the fake upstream's separate port may bypass it.
    sentinel = root / "source-home/private-sentinel"
    source_guard = {}
    for mode in ("r", "a"):
        try:
            with sentinel.open(mode):
                pass
        except PermissionError:
            source_guard[mode] = True
            continue
        source_guard[mode] = False
    port = int((root / "upstream-port").read_text())
    try:
        connection = socket.create_connection(("127.0.0.1", port), timeout=1)
    except OSError as error:
        bypass = {'denied':error.errno in (errno.EPERM, errno.EACCES),'errno':error.errno}
    else:
        connection.close()
        bypass = {'denied':False,'errno':None}
    spec=importlib.util.spec_from_file_location('guards',root/'probe_helpers.py')
    guards=importlib.util.module_from_spec(spec);spec.loader.exec_module(guards)
    home_guard=guards.attempt(Path((root/'host-home').read_text()))
    state = json.loads((Path(os.environ["CLAUDE_CONFIG_DIR"]) / ".claude.json").read_bytes())
    matches = state == {"hasCompletedOnboarding": True, "projects": {str(Path.cwd()): {"hasTrustDialogAccepted": True}}}
    (root/'cli-guards.json').write_text(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'profile':'C inherited','real_home_write':home_guard,'upstream_bypass':bypass,'source_home':source_guard,'config_matches':matches}))
    good=all(source_guard.values()) and bypass['denied'] and home_guard['denied'] and matches
    print("fixture-sandbox-child-protection-"+('PASS' if good else 'FAIL'), flush=True)
    raise SystemExit(0)

settings = json.loads(os.environ["T093_FIXTURE_SETTINGS"])
command = shlex.split(settings["hooks"]["Stop"][0]["hooks"][0]["command"])
prompt_id = str(uuid.uuid4())


def run(argv, value=None):
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    record(child.pid, 'native hook or inbox command')
    try:
        stdout,stderr=child.communicate(input=json.dumps(value) if value is not None else None,timeout=12)
    except subprocess.TimeoutExpired:
        child.kill();child.communicate();raise SystemExit(24)
    if child.returncode:
        # Status classes only; no raw terminal, hook body, auth or account data.
        print("fixture-native-command-failed", child.returncode, flush=True)
        raise SystemExit(24)
    return stdout


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
    receipt = json.loads(run([command[0], inbox, "list", "--role", "ideation"]))
    if receipt.get("queued") is not True or receipt.get("delivered") is not False:
        raise SystemExit(27)
hook("Stop", stop_hook_active=False)
