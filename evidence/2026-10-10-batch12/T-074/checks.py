#!/usr/bin/env python3
"""Run the task card's read-only commands and record unmet coverage explicitly."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
destination = BASE / 'checks.json'
if destination.exists():
    raise SystemExit('Check evidence exists; refuse overwrite')
counter = "import json,collections;c=collections.Counter((r['cli'],r['state'],r['outcome']) for r in map(json.loads,open('evidence/2026-10-10-batch12/T-074/r7-injections.jsonl')));[print(*k,v) for k,v in sorted(c.items())]"
commands = [
    ['python3', '-c', counter],
    ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', str(ROOT)],
    ['codex', '--version'], ['codex', '--help'], ['claude', '--version'], ['claude', '--help'],
]
records = []
with tempfile.TemporaryDirectory(prefix='a2a-t074-help-', dir='/tmp') as directory:
    env = dict(os.environ)
    env.update(HOME=directory, CODEX_HOME=directory + '/codex', CLAUDE_CONFIG_DIR=directory + '/claude',
               CLAUDE_SECURESTORAGE_CONFIG_DIR=directory + '/claude', PYTHONDONTWRITEBYTECODE='1')
    for argv in commands:
        process = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True)
        records.append(dict(argv=argv, cwd=str(ROOT), exit_code=process.returncode,
                            stdout=process.stdout, stderr=process.stderr,
                            finished_at=dt.datetime.now(dt.timezone.utc).isoformat()))
    generated = sorted(str(p.relative_to(directory)) for p in Path(directory).rglob('*'))
rows = [json.loads(line) for line in (BASE / 'r7-injections.jsonl').read_text(encoding='utf-8').splitlines()]
codex = [r for r in rows if r['cli'] == 'codex']
summary = dict(status='BLOCKED', commands=records, help_isolated_home_generated_paths=generated,
               task_card_coverage=dict(codex_injections=len(codex), required_codex_injections=10,
                                      states_observed=sorted({r['state'] for r in codex}),
                                      required_states=['idle', 'running', 'awaiting_approval'],
                                      codex_approval_trigger=False, claude_probe=False),
               command_success_is_not_acceptance_pass=True)
destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for record in records:
    print(json.dumps(dict(argv=record['argv'], exit_code=record['exit_code']), ensure_ascii=False))
print(json.dumps(summary['task_card_coverage'], ensure_ascii=False))
