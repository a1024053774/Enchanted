"""Reject a missing feature and focused phase/ancestry/write mutations."""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import traceback

parser = argparse.ArgumentParser()
parser.add_argument('--summary', type=Path, required=True)
parser.add_argument('--daemon', action='store_true')
args = parser.parse_args()
assert not args.summary.exists()
source = Path(__file__).resolve().parents[2]
root = Path(tempfile.mkdtemp(prefix='t111-counterfactual-', dir='/private/tmp'))
env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'A2A_'))}
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
report = dict(status='INCOMPLETE', model_calls=0, checks=[], root=str(root))
try:
    baseline = root / 'baseline'
    baseline.mkdir()
    revision = 'b1ecd6e9cba23c1bbddb331822b6500a1488e2e9'
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',revision,'workbench/src'],cwd=source,env=env))) as tar:
        tar.extractall(baseline)
    shutil.copytree(source / 'workbench/node_modules', root / 'node_modules', symlinks=False)
    cases = [('baseline', baseline, 'T-111 read-only flow projection is missing')]
    for name, before, after, expected in [
        ('missing-parent', 'agent.attempt === task.current_attempt?.attempt_id && agent.parent &&',
         'agent.attempt === task.current_attempt?.attempt_id &&', 'orphan'),
        ('old-attempt', 'agent.attempt === task.current_attempt?.attempt_id && agent.parent &&', 'agent.parent &&', 'old'),
        ('ignore-events', "case 'claimed': stage = 'implementation'", "case 'claimed': stage = 'review'", 'implementation'),
    ]:
        tree = root / name
        shutil.copytree(source / 'workbench/src', tree / 'workbench/src')
        path = tree / 'workbench/src/flow.ts'
        original = path.read_text(encoding='utf-8')
        assert original.count(before) == 1, name
        path.write_text(original.replace(before,after),encoding='utf-8')
        cases.append((name,tree,expected))
    for name, tree, expected in cases:
        output = root / (name + '.json')
        command = ['node',str(source / 'workbench/tests/test_t111_flow.mjs'),str(output),str(tree)]
        result = subprocess.run(command,cwd=source,env=env,capture_output=True,text=True,timeout=30)
        value = json.loads(output.read_text(encoding='utf-8'))
        assert result.returncode == 1 and expected in value.get('error',''), (name,value,result.stderr)
        report['checks'].append(dict(name=name,command=command,exit=result.returncode,error=value['error']))
    if args.daemon:
        tree = root / 'write-mutant'
        shutil.copytree(source / 'workbench/src',tree / 'workbench/src')
        path = tree / 'workbench/src/flow.ts'
        original = path.read_text(encoding='utf-8')
        marker = '  const sidebar = await sidebarSnapshot(gates, store, panes);'
        assert original.count(marker) == 1
        path.write_text(original.replace(marker,"  store.event('flow_read_mutant', {});\n"+marker),encoding='utf-8')
        command = ['node','--experimental-vm-modules',str(source / 'workbench/tests/test_t107_daemon_readonly.mjs'),str(root / 'write.json'),str(tree),'flow']
        result = subprocess.run(command,cwd=source,env=env,capture_output=True,text=True,timeout=120)
        value = json.loads((root / 'write.json').read_text(encoding='utf-8'))
        assert result.returncode == 1 and value.get('cleanup_complete') and 'Sidebar read changed persisted tables or traces' in value.get('error',''), (value,result.stderr)
        report['checks'].append(dict(name='flow-write-mutant',command=command,exit=result.returncode,error=value['error']))
    report['status'] = 'PASS'
except Exception as error:
    report.update(error=repr(error),traceback=traceback.format_exc())
finally:
    if report['status'] == 'PASS':
        shutil.rmtree(root)
    args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
