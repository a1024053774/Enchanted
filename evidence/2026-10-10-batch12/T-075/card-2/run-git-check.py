"""运行真实门禁的 CAS/中断测试，原目录在 /tmp，完整归档在本卡。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
p = argparse.ArgumentParser()
p.add_argument('suite', choices=['cas', 'window', 'commands'])
p.add_argument('label')
p.add_argument('--baseline', action='store_true')
p.add_argument('--mutant', choices=['cas'])
p.add_argument('--mutant-manifest', type=Path, default=BASE/'mutants-01/manifest.json')
args = p.parse_args()
out = BASE / args.label
out.mkdir(exist_ok=False)
artifact = Path(tempfile.mkdtemp(prefix='a2a-card2-git-check-', dir='/tmp'))
env = dict(os.environ, COOP_E2E_ARTIFACT_ROOT=str(artifact), COOP_E2E_TRACE=str(out/'trace.json'))
for key in ('COOP_SCRIPT', 'A2A_MUTANT_CLI', 'A2A_MUTANT_CORE'):
    env.pop(key, None)
env['COOP_NATIVE_ENTRY'] = str(ROOT/'workbench/src/gates/cli.ts')
if args.baseline:
    baseline = Path(json.loads((BASE/'baseline-bindings.json').read_text())['source'])
    env['COOP_SCRIPT'] = str(baseline/'acceptance/entry/a2a_gates.py')
    env['COOP_NATIVE_ENTRY'] = str(baseline/'workbench/src/gates/cli.ts')
if args.mutant:
    manifest = json.loads(args.mutant_manifest.read_text())
    item = next(item for item in manifest['mutants'] if item['name'] == args.mutant)
    env.update(COOP_SCRIPT=str(ROOT/'acceptance/entry/native-entry.py'),
               A2A_MUTANT_CLI=item['gate'], A2A_MUTANT_CORE=item['core'],
               COOP_NATIVE_ENTRY=str(ROOT/'acceptance/entry/native-entry.ts'))
test = {'cas': 'test_cas_race.py', 'window': 'test_work_branch_recovery.py',
        'commands': 'test_completion_recovery.py'}[args.suite]
command = [sys.executable,'-B',str(ROOT/'workbench/tests'/test)]
with (out/'stdout.txt').open('x') as stdout, (out/'stderr.txt').open('x') as stderr:
    result = subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
with tarfile.open(out/'artifacts.tar.gz','w:gz') as archive:
    archive.add(artifact,arcname=artifact.name)
record = {'argv':command,'exit':result.returncode,'artifact_root':str(artifact),
          'env':{k:v for k,v in env.items() if k.startswith(('COOP_','A2A_MUTANT'))}}
(out/'run.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
raise SystemExit(result.returncode)
