#!/bin/bash
# T-104 第一轮独立审查：只在一次性源码副本运行后台；不调用模型或 Electron。
# 在沙箱外运行：bash evidence/2026-10-19-batch17/T-104/REVIEW-OUTSIDE-01.sh 新编号
# 本脚本不修改候选、依赖原件、全局配置或既有证据；不提交、不建 worktree。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
LABEL=${1:?请提供未使用的编号，例如 review-outside-01}
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
revision = 'd54826223194b56ca057b8ab3213729c9e53a29a'
disk = Path('/Volumes/WD-Elements')
assert disk.is_mount(), '外置盘未挂载，不回退到内置盘归档'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == revision, '候选改变，停止'
out = disk / 'a2a-evidence/2026-10-19-batch17/T-104' / sys.argv[1]
out.mkdir(exist_ok=False)
scratch = Path(tempfile.mkdtemp(prefix='t104-review-outside-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', target=revision, scratch=str(scratch), archive=str(out), runs=[], model_calls=0,
              note='这是补充验收证据；即使脚本通过，也不覆盖审查报告的记录范围发现。')

def save():
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

try:
    # 仅复制 node-pty，修复测试副本的执行位；其他依赖只读引用已有安装。
    deps = scratch / 'dependencies'
    deps.mkdir()
    original = repo / 'workbench/node_modules'
    for entry in original.iterdir():
        dest = deps / entry.name
        if entry.name == 'node-pty':
            shutil.copytree(entry, dest, symlinks=True)
        else:
            dest.symlink_to(entry, target_is_directory=entry.is_dir())
    for helper in (deps / 'node-pty/prebuilds').glob('darwin-*/spawn-helper'):
        helper.chmod(0o755)
    (out / 'source-archive-command.txt').write_text('git archive ' + revision + ' workbench\n', encoding='utf-8')
    archived = subprocess.check_output(['git', 'archive', revision, 'workbench'])
    sources = {}
    for name in ['candidate', 'restart-mutant']:
        source = scratch / name
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
            archive.extractall(source)
        (source / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
        sources[name] = source
    mutant = sources['restart-mutant'] / 'workbench/src/panes.ts'
    old = "// A user's terminal is never resumed or turned into an agent session."
    body = mutant.read_text(encoding='utf-8')
    assert body.count(old) == 1
    mutant.write_text(body.replace(old, old + '\n        this.startShell(record.project, record.worktree);'), encoding='utf-8')
    (out / 'restart-mutant-change.txt').write_text(
        'workbench/src/panes.ts 的 recover shell 分支仅新增一行：\n'
        'this.startShell(record.project, record.worktree);\n'
        '要求：重启不能启动任何新的普通 shell。\n', encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'CLAUDE_', 'ANTHROPIC_'))}
    env.pop('NODE_OPTIONS', None)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env.update(PYTHONDONTWRITEBYTECODE='1', npm_config_cache=str(disk / 'a2a-t075-npm-cache'),
               electron_config_cache=str(disk / 'a2a-electron-cache'))
    for name, source in sources.items():
        summary = out / (name + '.json')
        raw = out / name
        argv = ['python3', '-B', str(source / 'workbench/tests/test_t104_shell_e2e.py'),
                '--archive', str(raw), '--summary', str(summary)]
        with (out / (name + '.log')).open('x', encoding='utf-8') as log:
            result = subprocess.run(argv, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        data = json.loads(summary.read_text(encoding='utf-8'))
        row = dict(case=name, argv=argv, exit=result.returncode, status=data.get('status'),
                   checkpoint=data.get('checkpoint'), error=data.get('error'), cleanup_complete=data.get('cleanup_complete'))
        report['runs'].append(row)
        save()
        assert data.get('cleanup_complete') is True, '进程清理未确认；保留现场并停止，不运行后续副本'
        assert raw.is_dir(), '原始现场未归档'
        dbpath = raw / 'state/state.sqlite3'
        with sqlite3.connect('file:' + str(dbpath) + '?mode=ro', uri=True) as db:
            first_stop = db.execute("SELECT min(seq) FROM orchestration_events WHERE type='daemon_stopped'").fetchone()[0]
            assert first_stop is not None, '没有第一次后台停止边界'
            created = db.execute("SELECT seq,launch,data FROM orchestration_events WHERE type='shell_created' AND seq>? ORDER BY seq",
                                 (first_stop,)).fetchall()
        row['shells_created_after_first_stop'] = [dict(seq=s, launch=l, data=json.loads(d)) for s, l, d in created]
        if name == 'candidate':
            assert result.returncode == 0 and data['status'] == 'PASS', '好候选必须先通过相同完成条件'
            assert not created, '好候选在后台重启时新建了普通 shell'
        else:
            # 独立查库确认坏行为实际发生；环境失败或变异没有生效不能算抓住反例。
            assert created, '重启变异没有启动额外 shell，不能作为有效反例'
            if result.returncode == 0 and data['status'] == 'PASS':
                report.update(status='NO_GO', finding='重启变异实际新建 shell，但候选新增的完整后台验收仍通过；完成条件不足')
            elif data.get('checkpoint') == 'restart' and result.returncode == 1:
                report.update(status='PASS', finding='好候选通过，重启变异在重启业务断言处被拒绝')
            else:
                report.update(status='INCOMPLETE', finding='坏版本未在预期重启业务断言处失败；请检查原始错误，不计为有效拒绝')
        save()
    # 保存本轮本地审查原件；不删除 /tmp 原件。按文件数与字节数核对，不计算校验值。
    local = Path('/private/tmp/t104-review-01-u7yc31m9')
    if local.is_dir():
        target = out / 'reviewer-local'
        shutil.copytree(local, target, symlinks=True)
        def inventory(folder):
            paths = [p for p in folder.rglob('*') if p.is_file() or p.is_symlink()]
            return len(paths), sum(p.lstat().st_size for p in paths)
        assert inventory(local) == inventory(target), '本地证据复制不完整，保留原件'
        count, size = inventory(local)
        report['local_archive'] = dict(original=str(local), archive=str(target), files=count, bytes=size,
                                       replay='bash evidence/2026-10-19-batch17/T-104/REVIEW-OUTSIDE-01.sh 新编号')
except Exception as error:
    report.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
finally:
    save()
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
PY
