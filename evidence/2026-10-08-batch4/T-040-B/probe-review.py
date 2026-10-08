#!/usr/bin/env python3
"""Focused known-bad probes for the two review findings; no desktop/provider."""
import argparse
import contextlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--revision", help="Read the launcher from this fork commit for a counterfactual")
args = parser.parse_args()
repo = Path('/Users/luckye/Documents/Code/synara')
sys.path.insert(0, str(repo / 'a2a/scripts'))
root = Path(tempfile.mkdtemp(prefix='t040b-probe-', dir='/Volumes/WD-Elements/dev-cache/synara/instances'))
source = repo / 'a2a/scripts/workbench'
if args.revision:
    source = root / 'workbench'
    source.write_bytes(subprocess.check_output(['git', 'show', args.revision + ':a2a/scripts/workbench'], cwd=repo))
module = importlib.machinery.SourceFileLoader('launcher_probe', str(source)).load_module()
report = {'root': str(root), 'revision': args.revision or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(), 'status': 'INCOMPLETE', 'limitations': 'Focused control-flow checks; build process and desktop spawn are test doubles. Health uses real loopback HTTP; full Electron/standard-build behavior is checked in run-e2e.py.'}

# Failure list: 200 with startupReady=false can return early; a retained stamp
# can skip the standard build even when a non-entry desktop artifact is absent.
fixture = root / 'fixture'
fixture.mkdir()
(fixture / 'apps').mkdir()
(fixture / 'packages').mkdir()
outputs = ['apps/desktop/dist-electron/main.js', 'apps/desktop/dist-electron/preload.js', 'apps/server/dist/index.mjs', 'apps/web/dist/index.html']
for name in outputs:
    path = fixture / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('stale retained artifact', encoding='utf-8')
cache = root / 'dev-cache/synara/workbench'
cache.mkdir(parents=True)
(cache / 'build.json').write_text(json.dumps({'commit': 'a'*40, 'inputs': {}}), encoding='utf-8')
calls = []
original_repo = module.runtime.REPO
original_check_output = subprocess.check_output
original_run = subprocess.run
def fake_check_output(argv, **kwargs):
    return '' if kwargs.get('text') and 'rev-parse' not in argv else ('a'*40+'\n' if kwargs.get('text') else b'')
def fake_build(argv, **kwargs):
    calls.append([str(v) for v in argv])
    for name in ['apps/desktop/dist-electron/guestPreload.js', 'apps/desktop/dist-electron/cuaDriverHostStandalone.js', 'apps/server/dist/client/index.html']:
        path = fixture / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('standard builder result', encoding='utf-8')
    return subprocess.CompletedProcess(argv, 0)
try:
    module.runtime.REPO = fixture
    subprocess.check_output = fake_check_output
    subprocess.run = fake_build
    module.build_if_needed(root)
finally:
    module.runtime.REPO = original_repo
    subprocess.check_output = original_check_output
    subprocess.run = original_run
expected = [str(fixture / 'a2a/scripts/bun'), 'run', 'build:desktop']
report['missing_or_stale_output'] = {'standard_build_called': expected in calls, 'calls': calls}

observations = []
class Health(BaseHTTPRequestHandler):
    def log_message(self, *unused):
        pass
    def do_GET(self):
        ready = len(observations) >= 2
        observations.append({'status': 200, 'startupReady': ready})
        body = json.dumps({'startupReady': ready}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
server = ThreadingHTTPServer(('127.0.0.1', 0), Health)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
data = root / 'health-data'
(data / 'a2a-gates').mkdir(parents=True)
(data / 'a2a-gates/endpoint.json').write_text(json.dumps({'desktopPid': os.getpid()}), encoding='utf-8')
owner_calls = []
def owner(unused):
    owner_calls.append(True)
    return None if len(owner_calls) == 1 else {'pid': os.getpid()}
class Child:
    def poll(self):
        return 0
module.runtime.data_directory = lambda: data
module.runtime.read_owner = owner
module.runtime.read_endpoint = lambda unused: {'origin': f'http://127.0.0.1:{server.server_port}', 'desktopPid': os.getpid()}
module.build_if_needed = lambda unused: None
original_popen = subprocess.Popen
original_argv = sys.argv
buffer = io.StringIO()
try:
    subprocess.Popen = lambda *unused, **kwargs: Child()
    sys.argv = ['workbench', 'start']
    with contextlib.redirect_stdout(buffer):
        module.main()
finally:
    subprocess.Popen = original_popen
    sys.argv = original_argv
    server.shutdown()
    server.server_close()
    thread.join()
report['http_readiness'] = {'observations': observations, 'success_after_ready': bool(observations and observations[-1]['startupReady']), 'stdout': buffer.getvalue()}
report['status'] = 'PASS' if report['missing_or_stale_output']['standard_build_called'] and report['http_readiness']['success_after_ready'] else 'FAIL'
Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(report['status'])
raise SystemExit(0 if report['status'] == 'PASS' else 1)
