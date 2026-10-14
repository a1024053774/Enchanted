#!/usr/bin/env python3
"""沙箱内静态检查及纯任务卡校验；不启动 socket 或写 Git 元数据。"""
import ast
import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path(__file__).with_name('local-final01-checks.json'))
OUT = parser.parse_args().output
results = []
for path in (ROOT / 'workbench/tests').glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
for path in Path(__file__).parent.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
for name in ('taskCards.ts', 'core.ts'):
    argv = ['node', '--check', str(ROOT / 'workbench/src/gates' / name)]
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    results.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
code = '''
const {validateTaskCard}=await import(process.argv[1]);
const base={id:'T-080-local',source:null,goal:'independent requirement',non_goals:['no model'],
 paths:{allow:['.'],deny:[]},oracle_paths:['acceptance/criterion.py'],
 completion_conditions:[{argv:['/usr/bin/true']}],red_commands:[],task_type:'测试',repair_target:null,
 complexity:'M',executor:{cli:'Codex',model:'gpt-6.1-sol',effort:'xhigh'},base_commit:null,writer:null};
validateTaskCard(base,base.id);
const invalid=[[],['.'],['/tmp/a'],['../a'],['a/../b'],['*.py'],['a?.py'],['a[0].py'],
 ['.git/config'],['x/.Git/'],['a\\\\b'],['a//b'],['a/./b']];
let rejected=0;
for(const paths of invalid){
 const card=structuredClone(base);card.oracle_paths=paths;
 try{validateTaskCard(card,card.id);throw new Error('invalid acceptance path accepted');}
 catch(e){if(e.constructor.name!=='TaskCardError')throw e;rejected++;}
}
for(const path of ['acceptance/criterion.py','acceptance/']){
 const card=structuredClone(base);card.oracle_paths=[path];
 card.red_commands=[{argv:['/usr/bin/true'],test_paths:['acceptance/criterion.py']}];
 try{validateTaskCard(card,card.id);throw new Error('overlap accepted');}
 catch(e){if(e.constructor.name!=='TaskCardError')throw e;rejected++;}
 card.red_commands[0].test_paths=['acceptance-other/red.py'];validateTaskCard(card,card.id);
}
const missing=structuredClone(base);delete missing.oracle_paths;
try{validateTaskCard(missing,missing.id);throw new Error('missing field accepted');}
catch(e){if(e.constructor.name!=='TaskCardError')throw e;rejected++;}
process.stdout.write(JSON.stringify({valid:true,rejected,adjacent_prefix_accepted:true})+'\\n');
'''
argv = ['node', '--input-type=module', '-e', code, (ROOT / 'workbench/src/gates/taskCards.ts').as_uri()]
p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
results.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
argv = ['git', 'diff', '--check']
p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
results.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
passed = all(row['exit'] == 0 for row in results)
with OUT.open('x', encoding='utf-8') as output:
    json.dump({'status': 'PASS' if passed else 'INCOMPLETE', 'scope': '仅静态及纯任务卡校验',
               'product_status': 'INCOMPLETE', 'command': sys.argv, 'checks': results,
               'not_run': ['真实门禁绿态', '变异体', '全量回归', '提交', '独立审查']}, output, ensure_ascii=False, indent=2)
    output.write('\n')
print(json.dumps({'status': 'PASS' if passed else 'INCOMPLETE', 'report': str(OUT)}, ensure_ascii=False))
raise SystemExit(0 if passed else 1)
