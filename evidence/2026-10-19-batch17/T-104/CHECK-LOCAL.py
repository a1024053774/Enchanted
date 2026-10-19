"""只运行语法、diff 和项目地图检查，不启动后台或模型。"""
import ast
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
report = dict(status='PASS', checks=[])
commands = [
    *[['node','--check',f'workbench/src/{name}.ts'] for name in ['panes','daemon','store','gates/cli']],
    *[['node','--check',f'workbench/tests/{name}.ts'] for name in ['test_pane_dispatch_state','test_conflict_panes']],
    ['bash','-n','evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-01-BACKEND.sh'],
    ['bash','-n','evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-03-COMMIT.sh'],
    ['git','diff','--check'],
    ['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'],
]
for argv in commands:
    result = subprocess.run(argv,cwd=root,capture_output=True,text=True)
    report['checks'].append(dict(argv=argv,exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
    if result.returncode:
        report['status']='INCOMPLETE'
for file in [root/'workbench/tests/test_t104_shell_e2e.py', *Path(__file__).parent.glob('*.py')]:
    ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
report['checks'].append(dict(check='Python AST',status='PASS'))
with Path(sys.argv[1]).open('x',encoding='utf-8') as output:
    json.dump(report,output,ensure_ascii=False,indent=2)
    output.write('\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
