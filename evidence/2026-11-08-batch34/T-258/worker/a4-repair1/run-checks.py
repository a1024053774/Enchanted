"""运行 repair 的完成条件与同一 M5；只在隔离源码副本删除 leader 守卫。"""
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
original = '9d6883239d2757e8899d1894999837c1e0b61617'
node = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
panes = 'workbench/src/panes.ts'
e2e = 'workbench/tests/test_t258_codex_late_start_e2e.py'
module = 'workbench/tests/test_t258_codex_late_start.ts'
summary = out / 'checks-01.json'
assert not summary.exists(), '必须用新的证据目录，禁止覆盖'
for name in (panes, e2e):
    assert (root / name).read_bytes() == subprocess.check_output(['git', 'show', original + ':' + name])
subprocess.run(['git', 'diff', '--exit-code', original, '--', 'workbench/src', 'workbench/package.json',
                'acceptance', 'REVIEW.md', '.project-map',
                'workbench/tests/test_t257_codex_stop_continuation.ts',
                'workbench/tests/test_t257_codex_stop_continuation_e2e.py'], check=True)
fixture = Path(tempfile.mkdtemp(prefix='m5-source-', dir=out))
archive = subprocess.check_output(['git', 'archive', original, 'workbench/src', 'workbench/package.json'])
with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
    for member in bundle.getmembers():
        assert not member.name.startswith('/') and '..' not in Path(member.name).parts
    bundle.extractall(fixture)
anchor = '(bound.leader_pid === null || bound.leader_pid === pane.leader)'
code = (fixture / panes).read_text(encoding='utf-8')
assert code.count(anchor) == 1
(fixture / panes).write_text(code.replace(anchor, 'true'), encoding='utf-8')
report = dict(status='INCOMPLETE', original_candidate=original, repair='b4a5ce47-0612-4047-9c81-fbbc2803dddb',
              head_at_run=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              at=datetime.now(timezone.utc).isoformat(), cwd=str(root),
              node_version=subprocess.check_output([node, '--version'], text=True).strip(),
              production_and_e2e_unchanged=True, mutation=dict(path=panes, before=anchor, after='true'), runs=[], cleanup=[])
def save():
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
save()
for name, source in [('candidate', root), ('m5', fixture)]:
    raw = out / (name + '.raw.json')
    assert not raw.exists()
    command = [node, '--test', module]
    environment = dict(T258_SOURCE_ROOT=str(source), T258_SUMMARY=str(raw))
    run = subprocess.run(command, cwd=root, env=dict(os.environ, **environment), capture_output=True, text=True)
    data = json.loads(raw.read_text(encoding='utf-8'))
    rows = [{k: v for k, v in row.items() if k != 'events'} for row in data['results']]
    report['runs'].append(dict(name=name, command=command, environment=environment, exit_code=run.returncode,
                              status=data['status'], counts={s: sum(r['status'] == s for r in rows) for s in ['PASS', 'FAIL']},
                              results=rows, fixture_cleanup=data['cleanup'], output_tail=run.stdout.splitlines()[-10:], stderr=run.stderr))
    report['cleanup'].append(dict(path=str(raw), at=datetime.now(timezone.utc).isoformat(), files=1,
                                  bytes=raw.stat().st_size, removed=False))
    save()
    raw.unlink()
    report['cleanup'][-1]['removed'] = True
    save()
    print(name, data['status'], report['runs'][-1]['counts'], 'exit=' + str(run.returncode), flush=True)
files = [p for p in fixture.rglob('*') if p.is_file()]
report['cleanup'].append(dict(path=str(fixture), at=datetime.now(timezone.utc).isoformat(), files=len(files),
                              bytes=sum(p.stat().st_size for p in files), removed=False))
save()
shutil.rmtree(fixture)
report['cleanup'][-1]['removed'] = True
save()
assert report['runs'][0]['exit_code'] == 0 and report['runs'][0]['counts'] == {'PASS': 119, 'FAIL': 0}
assert report['runs'][1]['exit_code'] == 1 and report['runs'][1]['counts'] == {'PASS': 117, 'FAIL': 2}
assert {r['name'] for r in report['runs'][1]['results'] if r['status'] == 'FAIL'} == {
    'bound-leader-mismatch worker', 'bound-leader-mismatch reviewer'}
report['status'] = 'PASS'
report['meaning'] = '本 repair 的测试补充通过；候选完成条件通过，同一 M5 被新增业务断言拒绝。不是整票验收或独立审查通过。'
save()
