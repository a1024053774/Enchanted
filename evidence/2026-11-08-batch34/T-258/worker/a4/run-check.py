"""运行本卡模块检查，保留逐案断言与清理状态，不复制 pane/数据库事件全文。"""
import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('kind', choices=['parent', 'candidate', 'unsafe', 't257', 'native-origin'])
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
root = Path.cwd().resolve()
summary = args.summary.resolve()
raw = summary.with_suffix('.raw.json')
output = summary.with_suffix('.raw.txt')
assert not any(p.exists() for p in (summary, raw, output)), '必须使用新证据路径'
node = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
base = '172b2f17566f923b2e0be8f7d21fc0b189b83fa2'
historical = '49c7b9a9435f68aec38a862125b8f00220b9b3af'
restored = ['workbench/src/panes.ts', 'workbench/tests/test_t258_codex_late_start.ts',
            'workbench/tests/test_t258_codex_late_start_e2e.py']
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
# 除卡内三个文件外，产品源码及包配置必须仍是新基线。
subprocess.run(['git', 'diff', '--exit-code', base, '--', 'workbench/src', 'workbench/package.json',
                ':(exclude)workbench/src/panes.ts'], check=True, capture_output=True)
for name in restored:
    if args.kind == 'parent' and name == restored[0]:
        continue  # 父版 panes.ts 由下面的固定基线快照提供，可在恢复后重放。
    assert (root / name).read_bytes() == subprocess.check_output(['git', 'show', historical + ':' + name]), name
source = root
snapshot = None
if args.kind in ('parent', 'unsafe'):
    snapshot = Path(tempfile.mkdtemp(prefix=args.kind + '-source-', dir=summary.parent))
    archive = subprocess.check_output(['git', 'archive', base, 'workbench/src', 'workbench/package.json'])
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for member in bundle.getmembers():
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
        bundle.extractall(snapshot)
    source = snapshot
    if args.kind == 'unsafe':
        path = source / restored[0]
        code = (root / restored[0]).read_text(encoding='utf-8')
        anchor = 'await this.confirmLateCodexStart(pane, value);'
        assert code.count(anchor) == 1
        path.write_text(code.replace(anchor, '{ pane.failed = null; pane.state = "busy"; }'), encoding='utf-8')
env = dict(os.environ, T258_SOURCE_ROOT=str(source), T258_SUMMARY=str(raw))
if args.kind == 't257':
    command = [node, 'workbench/tests/test_t257_codex_stop_continuation.ts', str(source), str(raw)]
elif args.kind == 'native-origin':
    command = [node, 'workbench/tests/test_t251_hook_cwd.ts', str(source), str(raw)]
else:
    command = [node, '--test', 'workbench/tests/test_t258_codex_late_start.ts']
report = dict(status='INCOMPLETE', kind=args.kind, time=datetime.now(timezone.utc).isoformat(),
              base=base, head_at_run=head, restored_from=historical, command=command, cwd=str(root),
              environment={k: env[k] for k in ('T258_SOURCE_ROOT', 'T258_SUMMARY')},
              node_version=subprocess.check_output([node, '--version'], text=True).strip(),
              dependency_path=str((root.parent / 'node_modules').resolve()))
def save():
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
save()
with output.open('x', encoding='utf-8') as log:
    run = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
report['exit_code'] = run.returncode
save()
data = json.loads(raw.read_text(encoding='utf-8'))
report['status'] = data['status']
report['results'] = [{k: v for k, v in row.items() if k in
                     ('name', 'sequence', 'seed', 'status', 'error', 'expected', 'actual', 'observed', 'failed', 'state')}
                    for row in data['results']]
for row in report['results']:
    if 'status' not in row:
        row['status'] = 'PASS' if row['actual'] == row['expected'] else 'FAIL'
report['counts'] = {s: sum(row['status'] == s for row in report['results']) for s in ('PASS', 'FAIL')}
report['fixture_cleanup'] = data.get('cleanup', {'status': 'N/A', 'reason': '原生来源检查不创建夹具'})
report['output_tail'] = output.read_text(encoding='utf-8').splitlines()[-10:]
report['cleanup'] = []
for path in [raw, output] + ([snapshot] if snapshot else []):
    files = [p for p in path.rglob('*') if p.is_file() or p.is_symlink()] if path.is_dir() else [path]
    report['cleanup'].append(dict(path=str(path), files=len(files), bytes=sum(p.lstat().st_size for p in files),
                                  at=datetime.now(timezone.utc).isoformat(), removed=False))
save()  # 必须在删除自己创建的原始大摘要/源码夹具前留下状态。
for row in report['cleanup']:
    path = Path(row['path'])
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    row['removed'] = True
save()
print(json.dumps({k: report[k] for k in ('kind', 'status', 'counts', 'exit_code')}, ensure_ascii=False))
raise SystemExit(run.returncode)
