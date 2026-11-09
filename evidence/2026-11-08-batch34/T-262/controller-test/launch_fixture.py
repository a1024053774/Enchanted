"""Launch the exact packaged candidate with a fresh, disposable records fixture.

Only the new /private/tmp fixture database is seeded. No model CLI is started.
The independent raw inputs are the same declared fixtures used by the E2E test.
"""
from pathlib import Path
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import time

sys.dont_write_bytecode = True
source = Path('/private/tmp/a2a-t262-package-20261108')
evidence = Path(__file__).resolve().parent
app = Path(json.loads((evidence / 'package-result.json').read_text())['app'])
packaged = json.loads((app / 'Contents/Resources/app/package.json').read_text())
assert packaged['productName'] == 'Enchanted Test'
assert packaged['a2a']['revision'] == '6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5'
spec = importlib.util.spec_from_file_location('t262_fixture', source / 'workbench/tests/test_t262_records_e2e.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixture = module.Fixture({})
assert fixture.root.parent == Path('/private/tmp')
fixture.state.mkdir()
binary = app / 'Contents/MacOS/Enchanted Test'
argv = [str(binary), '--state', str(fixture.state), '--user-data', str(fixture.root / 'ui')]
env = {k: v for k, v in os.environ.items() if not k.startswith('A2A_') and k != 'ELECTRON_RUN_AS_NODE'}
with (fixture.root / 'gui.log').open('x') as log:
    process = subprocess.Popen(argv, cwd=fixture.root, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
manifest = dict(root=str(fixture.root), state=str(fixture.state), app=str(app), argv=argv,
                gui_pid=process.pid, revision=packaged['a2a']['revision'], status='STARTING')
(evidence / 'fixture-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
database = fixture.state / 'state.sqlite3'
descriptor = fixture.state.with_name(fixture.state.name + '-credentials') / 'desktop-connection.json'
deadline = time.monotonic() + 45
while not (database.exists() and descriptor.exists()) and process.poll() is None and time.monotonic() < deadline:
    time.sleep(.2)
assert process.poll() is None, 'Test GUI exited; preserve fixture and inspect gui.log'
assert database.exists() and descriptor.exists(), 'Test backend not ready; preserve fixture and inspect permissions'
with sqlite3.connect(database) as db:
    for project in ['alpha', 'beta', 'empty']:
        repo = fixture.root / project
        repo.mkdir()
        subprocess.run(['git', 'init', '-b', 'main', str(repo)], check=True, capture_output=True)
        db.execute('INSERT INTO orchestration_events(time,type,data) VALUES (?,?,?)',
                   ('2026-11-01T00:00:00Z', 'project_opened', module.J(dict(project_id=project, repo=str(repo)))))
fixture.seed_records()
manifest.update(status='READY_FOR_CUA', inputs=len(module.INPUTS), receipts=len(module.RECEIPTS),
                fixture_source='workbench/tests/test_t262_records_e2e.py at packaged revision',
                note='Controlled raw records in a fresh test database; not real agent-generated history')
(evidence / 'fixture-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest))
