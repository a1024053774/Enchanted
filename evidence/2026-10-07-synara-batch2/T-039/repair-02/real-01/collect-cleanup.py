import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import tarfile
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / 'runtime.json').read_text(encoding='utf-8'))
s = json.loads((HERE / 'server-start.json').read_text(encoding='utf-8'))
root = Path(r['root']).resolve()
assert root.parent == Path('/private/tmp') and root.name.startswith('a2a-t039-')
assert not (HERE / 'cleanup.json').exists()
home = Path(r['codex_home'])
overlay = Path(r['synara_home'], 'codex-home-overlay')
token = (root / 'bootstrap-token').read_text().encode()
auth = json.loads((home / 'auth.json').read_text())

def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)

secrets = [token] + [x.encode() for x in strings(auth) if len(x) > 40]
def safe_copy(source, target):
    data = source.read_bytes()
    assert not any(secret in data for secret in secrets), f'Credential found in excluded source: {source.name}'
    with target.open('xb') as out:
        out.write(data)

ps = subprocess.run(['ps', '-p', str(s['pid']), '-o', 'pid=,pgid=,command='], capture_output=True, text=True)
assert ps.returncode == 0 and str(HERE / 'launch.mjs') in ps.stdout and r['root'] in ps.stdout
assert int(ps.stdout.split()[1]) == s['pgid']
os.kill(s['pid'], signal.SIGTERM)
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    state = subprocess.run(['ps', '-p', str(s['pid']), '-o', 'state='], capture_output=True, text=True)
    if state.returncode != 0 or state.stdout.strip().startswith('Z'):
        break
    time.sleep(0.2)
else:
    raise RuntimeError('Own server did not stop; no credential deletion performed')
all_processes = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,pgid=,command='], text=True)
survivors = [line for line in all_processes.splitlines() if len(line.split(None,3)) == 4
             and line.split(None,3)[2] == str(s['pgid']) and not line.split(None,3)[3].startswith('(bun)')]
assert not survivors, 'Own process group still has a live child'
copied = []
for source in home.rglob('rollout-*.jsonl'):
    safe_copy(source, HERE / source.name)
    copied.append(str(source))
for source in Path(r['synara_home'], 'userdata/logs/provider').glob('*.log'):
    safe_copy(source, HERE / ('provider-' + source.name))
    copied.append(str(source))
safe_copy(root / 'instructions.txt', HERE / 'instructions.txt')
gate_root = Path(r['synara_home'], 'userdata/a2a-gates')
db_files = list(gate_root.glob('*.sqlite*'))
for source in db_files:
    if source.name.endswith(('-wal', '-shm')):
        continue
    safe_copy(source, HERE / source.name)
    copied.append(str(source))
with tarfile.open(HERE / 'retained-fixture.tar.gz', 'x:gz') as archive:
    archive.add(Path(r['repo']), arcname='fixture')
    archive.add(gate_root, arcname='a2a-gates')
git = []
for command in (['git','-C',r['repo'],'rev-parse','refs/a2a/integration'],
                ['git','-C',r['repo'],'worktree','list','--porcelain']):
    p = subprocess.run(command, capture_output=True, text=True)
    git.append(dict(argv=command, stdout=p.stdout, stderr=p.stderr, exit=p.returncode))
final_task = json.loads(json.loads((HERE / 'status-final.json').read_text())['stdout'])['task']
worker_head = subprocess.check_output(['git','-C',final_task['current_attempt']['workspace'],'rev-parse','HEAD'],text=True).strip()
assert git[0]['exit'] == 0 and git[0]['stdout'].strip() == worker_head == final_task['candidate_commit']
for p in (home, overlay):
    assert p.resolve().is_relative_to(root) and not p.is_symlink()
    shutil.rmtree(p)
(root / 'bootstrap-token').unlink()
result = dict(time=datetime.now(timezone.utc).isoformat(), stopped_server_pid=s['pid'],
              pid_check=ps.stdout, stop_signal='SIGTERM', surviving_group_processes=survivors,
              deleted_homes=[str(home),str(overlay)], home_exists=[home.exists(),overlay.exists()],
              deleted_bootstrap_token=True, credential_files_in_evidence=False, copied_sources=copied,
              retained_original_fixture=True, retained_original_synara_state=True,
              synara_private_state_excluded_from_git=True, git_readbacks=git)
with (HERE / 'cleanup.json').open('x', encoding='utf-8') as out:
    json.dump(result, out, ensure_ascii=False, indent=2)
    out.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
