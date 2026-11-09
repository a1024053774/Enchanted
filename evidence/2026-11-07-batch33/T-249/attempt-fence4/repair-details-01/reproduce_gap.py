#!/usr/bin/env python3
"""一次性源码副本断开详情，复现三条旧机械条件仍全绿的验收缺口。"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
NODE = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
paths = ['acceptance/T-249/check_git_graph.py', 'workbench/app/gitHost.ts',
         'workbench/app/panels/gitGraphModel.ts', 'workbench/app/panels/gitGraphCli.ts',
         'workbench/app/panels/GitGraphPanel.tsx', 'workbench/app/renderer.tsx',
         'workbench/app/RUN-OUTSIDE-T249.sh', 'workbench/tests/test_t249_git_graph_e2e.py',
         'workbench/tests/test_t249_git_host.mjs', 'workbench/tests/test_t249_outside_safety.py']
tmp = Path(tempfile.mkdtemp(prefix='t249-details-gap-', dir=os.environ['A2A_REQUEST_DIR']))
source = tmp / 'source'
for name in paths:
    dest = source / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, dest)
target = source / 'workbench/app/panels/GitGraphPanel.tsx'
text = target.read_text(encoding='utf-8')
before, after = '{selectedCommit && <CommitDetails', '{false && selectedCommit && <CommitDetails'
assert text.count(before) == 1
target.write_text(text.replace(before, after), encoding='utf-8')
env = dict(os.environ, TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp), PYTHONDONTWRITEBYTECODE='1',
           PATH=str(Path(NODE).parent) + os.pathsep + os.environ['PATH'])
checks = [('acceptance', ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py']),
          ('host', [NODE, '--test', 'workbench/tests/test_t249_git_host.mjs']),
          ('outside-safety', ['/usr/bin/python3', 'workbench/tests/test_t249_outside_safety.py'])]
results = []
for name, argv in checks:
    with (OUT / ('gap-no-details-' + name + '.txt')).open('x', encoding='utf-8') as log:
        log.write('cwd: ' + str(source) + '\nTMPDIR: ' + str(tmp) + '\nargv: ' + json.dumps(argv) + '\n')
        log.flush()
        p = subprocess.run(argv, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
        log.write('\nexit: ' + str(p.returncode) + '\n')
        results.append(dict(name=name, exit=p.returncode))
sizes = [p.stat().st_size for p in tmp.rglob('*') if p.is_file() and not p.is_symlink()]
summary = dict(candidate=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               time=datetime.datetime.now(datetime.timezone.utc).isoformat(), mutation=dict(path=str(target.relative_to(source)), before=before, after=after),
               results=results, directory=str(tmp), files=len(sizes), bytes=sum(sizes),
               conclusion='FAIL: 详情组件不挂载，三条机械条件仍通过' if all(r['exit'] == 0 for r in results) else 'INCOMPLETE')
with (OUT / 'gap-no-details.json').open('x', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
    f.write('\n')
shutil.rmtree(tmp)
print(json.dumps(summary, ensure_ascii=False))
print('temporary_directory_removed=' + str(not tmp.exists()))
