"""运行原验收；只重定向 EVIDENCE，保留原断言、快照及全部失败现场。"""
import argparse
import contextlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import datetime

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
p = argparse.ArgumentParser()
p.add_argument('suite', choices=['coop', 'recovery', 'run'])
p.add_argument('label')
p.add_argument('--mutant', choices=['fence', 'cas', 'lock'])
p.add_argument('--mutant-dir', default='mutants')
args = p.parse_args()
out = BASE / args.label
out.mkdir(exist_ok=False)
if args.mutant:
    os.environ['COOP_SCRIPT'] = str(ROOT / 'acceptance/entry/native-entry.py')
    mutant = BASE / args.mutant_dir / args.mutant
    os.environ['A2A_MUTANT_CLI'] = str(mutant / 'cli.ts')
    os.environ['A2A_MUTANT_CORE'] = str(mutant / 'core.ts')
    os.environ['COOP_NATIVE_ENTRY'] = str(ROOT / 'acceptance/entry/native-entry.ts')
elif args.suite == 'recovery':
    os.environ['COOP_NATIVE_ENTRY'] = str(ROOT / 'workbench/src/gates/cli.ts')
sys.path.insert(0, str(ROOT / 'acceptance'))
module = importlib.import_module('test_' + args.suite + '_e2e')
module.EVIDENCE = out
record = dict(argv=sys.argv, cwd=str(ROOT), task='T-075-1',
              suite=args.suite, started=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              node=subprocess.check_output(['node', '--version'], text=True).strip(),
              entry=str(module.SCRIPT), gate=str(ROOT/'workbench/src/gates'),
              env={key: os.environ[key] for key in ['COOP_SCRIPT','COOP_NATIVE_ENTRY','A2A_MUTANT_CLI','A2A_MUTANT_CORE'] if key in os.environ})
# The original main spawns its unchanged --run-suite entry and captures stdout/stderr.
sys.argv = [str(ROOT / 'acceptance' / ('test_' + args.suite + '_e2e.py'))]
with (out/'stdout.txt').open('x',encoding='utf-8') as stdout, (out/'stderr.txt').open('x',encoding='utf-8') as stderr:
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = module.main()
record['exit_code'] = code
checks = sorted(out.glob('check-*.json'))
assert len(checks) == 1, checks
check = json.loads(checks[0].read_text(encoding='utf-8'))
record['tests_run'] = check['trace']['tests_run']
record['failures'] = check['trace']['failures']
record['errors'] = check['trace']['errors']
# Preserve nested repositories as an archive, never as gitlinks. Leave the originals.
artifact = Path(check['artifact_root'])
with tarfile.open(out/'artifacts.tar.gz', 'w:gz') as archive:
    archive.add(artifact, arcname=artifact.name)
(out/'run.json').write_text(json.dumps(record, ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
raise SystemExit(code)
