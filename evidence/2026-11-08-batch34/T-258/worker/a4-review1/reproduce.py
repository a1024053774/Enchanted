"""复现审查 M5：只改自身源码/诊断副本，保留逐案断言后清理。"""
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

root = Path.cwd().resolve()
out = Path(__file__).resolve().parent
candidate = '9d6883239d2757e8899d1894999837c1e0b61617'
node = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
module = 'workbench/tests/test_t258_codex_late_start.ts'
panes = 'workbench/src/panes.ts'
summary = out / 'reproduction-01.json'
assert not summary.exists(), '必须用新的证据路径，禁止覆盖'
source_bytes = subprocess.check_output(['git', 'show', candidate + ':' + panes])
test_bytes = subprocess.check_output(['git', 'show', candidate + ':' + module])
assert (root / panes).read_bytes() == source_bytes
assert (root / module).read_bytes() == test_bytes
fixture = Path(tempfile.mkdtemp(prefix='m5-source-', dir=out))
archive = subprocess.check_output(['git', 'archive', candidate, 'workbench/src', 'workbench/package.json'])
with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
    for member in bundle.getmembers():
        assert not member.name.startswith('/') and '..' not in Path(member.name).parts
    bundle.extractall(fixture)
anchor = '(bound.leader_pid === null || bound.leader_pid === pane.leader)'
code = source_bytes.decode('utf-8')
assert code.count(anchor) == 1
mutant = code.replace(anchor, 'true')
test_code = test_bytes.decode('utf-8')
assert test_code.count('after(() => {') == 1
probe = fixture / 'leader-probe.ts'
probe.write_text(test_code.replace('after(() => {', (out / 'leader-probe.inc.ts').read_text(encoding='utf-8') + '\nafter(() => {'), encoding='utf-8')
report = dict(status='INCOMPLETE', candidate=candidate, at=datetime.now(timezone.utc).isoformat(),
              cwd=str(root), mutation=dict(path=panes, before=anchor, after='true'), runs=[], cleanup=[])
def save():
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
save()
for name, source, test_file, pattern in [
    ('m5-original-tests', fixture, root / module, None),
    ('sentinel-candidate', root, probe, 'review sentinel bound-leader mismatch'),
    ('sentinel-m5', fixture, probe, 'review sentinel bound-leader mismatch'),
]:
    (fixture / panes).write_text(mutant, encoding='utf-8')
    raw = out / (name + '.raw.json')
    assert not raw.exists()
    command = [node, '--test'] + (['--test-name-pattern=' + pattern] if pattern else []) + [str(test_file)]
    environment = dict(T258_SOURCE_ROOT=str(source), T258_SUMMARY=str(raw))
    run = subprocess.run(command, cwd=root, env=dict(os.environ, **environment), capture_output=True, text=True)
    data = json.loads(raw.read_text(encoding='utf-8'))
    rows = [{k: v for k, v in row.items() if k != 'events'} for row in data['results']]
    report['runs'].append(dict(name=name, command=command, environment=environment, exit_code=run.returncode,
                              status=data['status'], counts={s: sum(r['status'] == s for r in rows) for s in ['PASS', 'FAIL']},
                              results=rows, fixture_cleanup=data['cleanup'], output_tail=run.stdout.splitlines()[-10:], stderr=run.stderr))
    report['cleanup'].append(dict(path=str(raw), files=1, bytes=raw.stat().st_size, removed=False))
    save()
    raw.unlink()
    report['cleanup'][-1]['removed'] = True
    save()
    print(name, data['status'], run.returncode, flush=True)
assert [r['exit_code'] for r in report['runs']] == [0, 0, 1]
assert [r['counts'] for r in report['runs']] == [{'PASS': 117, 'FAIL': 0}, {'PASS': 2, 'FAIL': 0}, {'PASS': 0, 'FAIL': 2}]
report['status'] = 'PASS'
report['meaning'] = '审查覆盖缺口已复现；不是完成条件或整票通过。产品与完成条件测试未修改。'
files = [p for p in fixture.rglob('*') if p.is_file()]
report['cleanup'].append(dict(path=str(fixture), at=datetime.now(timezone.utc).isoformat(), files=len(files),
                              bytes=sum(p.stat().st_size for p in files), removed=False))
save()
shutil.rmtree(fixture)
report['cleanup'][-1]['removed'] = True
assert (root / panes).read_bytes() == source_bytes and (root / module).read_bytes() == test_bytes
save()
