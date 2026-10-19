"""不启动后台或模型：在隔离源码上对照基线和候选的两项旧回归。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[3]
fixture = Path(tempfile.mkdtemp(prefix='t104-regressions-', dir='/private/tmp'))
base = 'cc18d93dbbcf2ee641dc92befe68e5b0609b4807'
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_'))}
report = dict(status='INCOMPLETE', argv=sys.argv, fixture=str(fixture), base=base, runs=[])
for label in ['baseline', 'candidate']:
    source = fixture / label
    if label == 'baseline':
        files = subprocess.check_output(['git','ls-tree','-r','--name-only',base,'workbench/src'],cwd=root,text=True).splitlines()
        for name in files:
            path = source/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(subprocess.check_output(['git','show',f'{base}:{name}'],cwd=root))
    else:
        shutil.copytree(root/'workbench/src',source/'workbench/src')
    (source/'workbench/tests').mkdir()
    (source/'workbench/node_modules').symlink_to(root/'workbench/node_modules',target_is_directory=True)
    for name in ['test_pane_dispatch_state.ts','test_conflict_panes.ts']:
        shutil.copyfile(root/'workbench/tests'/name,source/'workbench/tests'/name)
    commands = [
        ['node',str(source/'workbench/tests/test_pane_dispatch_state.ts'),str(source/'worker-dispatch')],
        ['node',str(source/'workbench/tests/test_conflict_panes.ts'),'--product',str(source),'--output',str(source/'conflict-panes.json')],
    ]
    for argv in commands:
        run = subprocess.run(argv,cwd=source,env=env,capture_output=True,text=True,timeout=30)
        report['runs'].append(dict(case=label,argv=argv,exit=run.returncode,stdout=run.stdout,stderr=run.stderr))
report['status'] = 'PASS' if all(row['exit']==0 for row in report['runs']) else 'INCOMPLETE'
with Path(sys.argv[1]).open('x',encoding='utf-8') as output:
    json.dump(report,output,ensure_ascii=False,indent=2)
    output.write('\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
