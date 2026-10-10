import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
assert label and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label)
argv = ['./a2a/scripts/bun', *sys.argv[2:]]
assert len(argv) > 1
env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SHELL', 'LANG', 'LC_ALL')}
env['A2A_SYNARA_SLOT'] = 's11-t064-checks'
if 'T064_COUNTERFACTUAL' in os.environ:
    assert os.environ['T064_COUNTERFACTUAL'] in ('parent-native', 'missing-input')
    env['T064_COUNTERFACTUAL'] = os.environ['T064_COUNTERFACTUAL']
check_root = Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-checks')
for name in ('os-home', 'codex-empty', 'claude-empty'):
    (check_root / name).mkdir(parents=True, exist_ok=True, mode=0o700)
env.update(HOME=str(check_root/'os-home'), CODEX_HOME=str(check_root/'codex-empty'),
           CLAUDE_CONFIG_DIR=str(check_root/'claude-empty'))
with (out / (label + '.log')).open('x', encoding='utf-8') as log:
    result = subprocess.run(argv, cwd=fork, env=env, stdout=log, stderr=subprocess.STDOUT)
record = dict(argv=argv, cwd=str(fork), env_override={'A2A_SYNARA_SLOT': env['A2A_SYNARA_SLOT']},
    created_at=dt.datetime.now(dt.timezone.utc).isoformat(), returncode=result.returncode,
    isolated_home=str(check_root/'os-home'),
    counterfactual=env.get('T064_COUNTERFACTUAL'),
    fork_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip(),
    tracked_status=subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=fork, text=True),
    log=str((out / (label + '.log')).relative_to(out)))
with (out / (label + '.json')).open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(result.returncode)
