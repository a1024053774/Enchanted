#!/usr/bin/env python3
"""Run bounded offline artifact checks and record results; never start a probe."""
import ast
import datetime as dt
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
checks = []
for argv in [
    ['python3', '-B', str(BASE/'analyze-rev3.py')],
    ['node', '--check', str(BASE/'rev3-host.cjs')],
    ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', str(ROOT)],
]:
    r = subprocess.run(argv, capture_output=True, text=True)
    checks.append(dict(argv=argv, exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr))
for name in ['probe-rev3.py', 'rev3-runner.py', 'race-rev3.py', 'archive-rev3.py', 'turn-hook-record.py', 'analyze-rev3.py', 'checks-rev3.py']:
    ast.parse((BASE/name).read_text(encoding='utf-8'), filename=name)
directories = sorted(p for p in BASE.glob('rev3-*-*') if p.is_dir())
count = 0
for d in directories:
    for f in d.rglob('*'):
        if f.suffix == '.json':
            json.loads(f.read_text(encoding='utf-8'))
            count += 1
        elif f.suffix == '.jsonl':
            for line in f.read_text(encoding='utf-8').splitlines():
                json.loads(line)
            count += 1
for f in [BASE/'RESULTS.md', BASE/'PLAN-rev3.md', BASE/'needs-decision-04.md',
          ROOT/'findings/native-cli-signals-injection-2026-10-10.zh-CN.md',
          ROOT/'.project-map/tickets/T-074-pane-signal-and-injection-facts.md']:
    s = f.read_text(encoding='utf-8')
    assert '\ufffd' not in s and not s.startswith('\ufeff')
prior = (BASE/'r7-injections-ready-rev1-final.jsonl').read_text().splitlines()
current = (BASE/'r7-injections.jsonl').read_text().splitlines()
assert len(prior) == 16
# The rev-2 commit is the fixed reference, unaffected by the later submission commit.
rev2 = subprocess.check_output(['git', 'show', '2fcd1d0ced591e657797727d97a1c0c8cefa0116:evidence/2026-10-10-batch12/T-074/r7-injections.jsonl'], cwd=ROOT, text=True).splitlines()
assert current[:len(rev2)] == rev2
ps = subprocess.check_output(['/bin/ps', '-axo', 'pid,ppid,pgid,command'], text=True)
live = []
for d in directories:
    m = json.loads((d/'launch.json').read_text())
    temp = Path(m['temp_root'])
    live.extend(line for line in ps.splitlines() if str(temp) in line or str(temp.resolve()) in line)
    if m['cli'] == 'codex':
        assert not temp.exists()
    else:
        assert Path(m['fixture']).exists()
assert not live
result = dict(at=dt.datetime.now(dt.timezone.utc).isoformat(), task_status='BLOCKED', commands=checks,
              python_syntax='PASS', utf8_text='PASS', json_files_checked=count,
              prior_r7_lines_preserved=len(rev2), owned_processes=live,
              codex_homes_removed=True, claude_fixtures_retained=True)
destination = BASE/'checks-rev3.json'
with destination.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k != 'commands'}, ensure_ascii=False))
for r in checks:
    print(r['argv'], 'exit', r['exit_code'])
    if r['exit_code']:
        print(r['stdout'], r['stderr'])
assert all(r['exit_code'] == 0 for r in checks)
