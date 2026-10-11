"""通过独立 CAS 竞争场景验证候选或变异体，保留全部现场。"""
import argparse, json, os, subprocess, sys, tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--mutant',action='store_true');p.add_argument('--mutant-dir',default='mutants');args=p.parse_args()
out=BASE/args.label;out.mkdir(exist_ok=False)
artifacts=out/'retained-artifacts';artifacts.mkdir()
env=dict(os.environ,COOP_E2E_ARTIFACT_ROOT=str(artifacts),COOP_E2E_TRACE=str(out/'trace.json'))
if args.mutant:
 env.update(COOP_SCRIPT=str(ROOT/'acceptance/entry/native-entry.py'),A2A_MUTANT_CLI=str(BASE/args.mutant_dir/'cas/cli.ts'),A2A_MUTANT_CORE=str(BASE/args.mutant_dir/'cas/core.ts'))
argv=[sys.executable,'-B',str(ROOT/'workbench/tests/test_cas_race.py')]
with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
 result=subprocess.run(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
with tarfile.open(out/'artifacts.tar.gz','w:gz') as archive: archive.add(artifacts,arcname=artifacts.name)
record={'argv':argv,'exit_code':result.returncode,'env':{k:v for k,v in env.items() if k.startswith(('COOP_','A2A_MUTANT'))}}
(out/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record)
raise SystemExit(result.returncode)
