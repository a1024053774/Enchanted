#!/bin/bash
# T-104 第二轮独立审查的可选真实后台复验；不启动 Electron 或模型。
# 已有真实原件经过本轮核对；本脚本尚未执行，不把它计入通过证据。
# 用法：bash evidence/2026-10-19-batch17/T-104/REVIEW-OUTSIDE-02.sh 未使用的编号
# 只写新 /tmp 副本和外置盘新目录；不修改候选、依赖原件或全局配置。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
LABEL=${1:?请提供未使用的编号，例如 reviewer-02-replay-01}
case "$LABEL" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
python3 - "$LABEL" <<'PY'
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import traceback

repo = Path.cwd()
revision = '45c127b5af03bfdc50802579bda50b88a98dc2c7'
disk = Path('/Volumes/WD-Elements')
assert disk.is_mount(), '外置盘未挂载，停止，不回退到内置盘归档'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == revision, '候选改变，停止'
out = disk / 'a2a-evidence/2026-10-19-batch17/T-104' / sys.argv[1]
out.mkdir(exist_ok=False)
scratch = Path(tempfile.mkdtemp(prefix='t104-review-02-replay-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', target=revision, scratch=str(scratch), archive=str(out), runs=[], model_calls=0,
              command='bash evidence/2026-10-19-batch17/T-104/REVIEW-OUTSIDE-02.sh ' + sys.argv[1])

def save():
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

try:
    # 只复制 node-pty 并修改副本执行位；不安装依赖，不链接构建输出目录。
    deps = scratch / 'dependencies'
    deps.mkdir()
    for entry in (repo / 'workbench/node_modules').iterdir():
        if entry.name == 'node-pty':
            shutil.copytree(entry, deps / entry.name, symlinks=True)
        else:
            (deps / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
    for helper in (deps / 'node-pty/prebuilds').glob('darwin-*/spawn-helper'):
        helper.chmod(0o755)
    archived = subprocess.check_output(['git', 'archive', revision, 'workbench'])
    changes = {
        'privacy': ('daemon.ts', 'shellInput = isShellInput(envelope);',
                    'shellInput = isShellInput(envelope);\n        if (shellInput) store.event("request_received", { id: envelope.id, input: envelope.input });'),
        'metadata': ('daemon.ts', 'if (record.role !== "shell") store.event("window_request_admitted", { ...receipt, command: input.command }, record as any);',
                     'store.event("window_request_admitted", { ...receipt, command: input.command }, record as any);'),
        'restart': ('panes.ts', "// A user's terminal is never resumed or turned into an agent session.",
                    "// A user's terminal is never resumed or turned into an agent session.\n        this.startShell(record.project, record.worktree);")}
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
    env.pop('NODE_OPTIONS', None)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    for case in ['candidate', 'privacy', 'metadata', 'restart']:
        source = scratch / case
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
            archive.extractall(source)
        (source / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
        if case in changes:
            filename, old, new = changes[case]
            path = source / 'workbench/src' / filename
            body = path.read_text(encoding='utf-8')
            assert body.count(old) == 1, '变异必须只有一处'
            path.write_text(body.replace(old, new), encoding='utf-8')
            (out / (case + '-change.txt')).write_text(filename + '\n原文：' + old + '\n变异：' + new + '\n', encoding='utf-8')
        summary = out / (case + '.json')
        raw = out / case
        argv = ['python3', '-B', str(source / 'workbench/tests/test_t104_shell_e2e.py'),
                '--archive', str(raw), '--summary', str(summary)]
        with (out / (case + '.log')).open('x', encoding='utf-8') as log:
            result = subprocess.run(argv, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        data = json.loads(summary.read_text(encoding='utf-8'))
        row = dict(case=case, argv=argv, exit=result.returncode, status=data.get('status'),
                   checkpoint=data.get('checkpoint'), error=data.get('error'), cleanup_complete=data.get('cleanup_complete'))
        report['runs'].append(row)
        save()
        assert data.get('cleanup_complete') is True, '清理未确认；保留现场并停止'
        # 主库与 WAL 一起复制后读，避免 immutable 忽略 WAL，也不写归档原件。
        copied = scratch / (case + '-db')
        copied.mkdir()
        for path in (raw / 'state').glob('state.sqlite3*'):
            shutil.copyfile(path, copied / path.name)
        with sqlite3.connect('file:' + str(copied / 'state.sqlite3') + '?mode=ro', uri=True) as db:
            admitted = db.execute("SELECT count(*) FROM orchestration_events WHERE type='window_request_admitted'").fetchone()[0]
            first_stop = db.execute("SELECT min(seq) FROM orchestration_events WHERE type='daemon_stopped'").fetchone()[0]
            restarted = db.execute("SELECT seq,launch FROM orchestration_events WHERE type='shell_created' AND seq>?", (first_stop,)).fetchall()
        row.update(input_metadata_events=admitted, new_shells_after_first_stop=restarted)
        if case == 'candidate':
            assert result.returncode == 0 and data['status'] == 'PASS' and admitted == 0 and not restarted, '好候选必须先通过'
        else:
            if result.returncode == 0 and data.get('status') == 'PASS':
                report.update(status='NO_GO', finding='错误实现通过相同完成条件，验收不足')
                raise AssertionError(report['finding'])
            expected = {'privacy': ('privacy', 'shell 输入内容泄漏进事件流'),
                        'metadata': ('privacy', 'shell 逐次输入事件进入事件流'),
                        'restart': ('restart', '后台重启新增了 shell launch 或创建事件')}[case]
            assert result.returncode == 1 and data.get('checkpoint') == expected[0] and expected[1] in data.get('error', ''), '未在指定业务断言处失败，不算有效拒绝'
            if case == 'metadata':
                assert admitted > 0, '元数据错误未实际发生'
            if case == 'restart':
                assert restarted, '自动启动错误未实际发生'
        save()
    report['status'] = 'PASS'
except Exception as error:
    report.update(status='NO_GO' if report['status'] == 'NO_GO' else 'INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
finally:
    save()
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
PY
