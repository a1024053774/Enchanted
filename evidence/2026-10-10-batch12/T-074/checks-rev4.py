#!/usr/bin/env python3
"""Run bounded offline artifact checks without starting a model."""
import argparse
import ast
import datetime as dt
import json
from pathlib import Path
import subprocess

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
p=argparse.ArgumentParser();p.add_argument('--output',default='checks-rev4.json');args=p.parse_args()
checks=[]
for argv in [
    ['python3','-B',str(BASE/'analyze-rev4.py')],
    ['node','--check',str(BASE/'rev4-host.cjs')],
    ['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root',str(ROOT)],
]:
    r=subprocess.run(argv,capture_output=True,text=True)
    checks.append(dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
for name in ['probe-rev4.py','rev4-runner.py','archive-rev4.py','analyze-rev4.py','checks-rev4.py']:
    ast.parse((BASE/name).read_text(encoding='utf-8'),filename=name)
count=0
for label in ['rev4-codex','rev4-claude']:
    for f in (BASE/label).rglob('*'):
        if f.suffix=='.json':json.loads(f.read_text(encoding='utf-8'));count+=1
        elif f.suffix=='.jsonl':
            for line in f.read_text(encoding='utf-8').splitlines():json.loads(line)
            count+=1
for f in [BASE/'RESULTS.md',BASE/'PLAN-rev4.md',ROOT/'findings/native-cli-signals-injection-2026-10-10.zh-CN.md',ROOT/'findings/README.md',ROOT/'.project-map/tickets/T-074-pane-signal-and-injection-facts.md']:
    s=f.read_text(encoding='utf-8');assert '\ufffd' not in s and not s.startswith('\ufeff')
prior=subprocess.check_output(['git','show','040d017b236e5131001ee31bdafcfbddd0dd5923:evidence/2026-10-10-batch12/T-074/r7-injections.jsonl'],cwd=ROOT,text=True).splitlines()
assert (BASE/'r7-injections.jsonl').read_text().splitlines()[:len(prior)]==prior
ps=subprocess.check_output(['/bin/ps','-axo','pid,ppid,pgid,command'],text=True)
live=[]
for label in ['rev4-codex','rev4-claude']:
    m=json.loads((BASE/label/'launch.json').read_text());temp=Path(m['temp_root'])
    live.extend(line for line in ps.splitlines() if str(temp) in line or str(temp.resolve()) in line)
    if m['cli']=='codex':assert not temp.exists()
    else:assert Path(m['fixture']).exists()
assert not live
result=dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),commands=checks,python_syntax='PASS',utf8_text='PASS',json_files_checked=count,prior_r7_lines_preserved=len(prior),owned_processes=live,codex_home_removed=True,claude_fixture_retained=True)
with (BASE/args.output).open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for r in checks:
    print(r['argv'],'exit',r['exit_code'])
    if r['exit_code']:print(r['stdout'],r['stderr'])
print(json.dumps({k:v for k,v in result.items() if k!='commands'},ensure_ascii=False))
assert all(r['exit_code']==0 for r in checks)
