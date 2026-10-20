#!/bin/zsh
# 第二轮独立审查：仅合同与两个变异；不启动 CLI、模型、Electron 或后台。
# 沙箱内亦可执行；输出含精确命令、退出码和断言，临时副本最终全部删除。
set -euo pipefail
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
TASK_REPO=${T112_REVIEW_REPO:-/Users/luckye/Documents/Code/a2a-wt-t112}
/usr/bin/python3 -B - "$TASK_REPO" <<'PY'
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

repo = Path(sys.argv[1]).resolve()
revision = '5f19062f52154914123e3796fdff87caaa22fc1f'
root = Path(tempfile.mkdtemp(prefix='t112-review02-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', revision=revision, fixture=str(root), runs=[], model_calls=0)
env = dict(os.environ, LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')

def run(label, argv, expected=0, assertion=None, result=None):
    completed = subprocess.run(list(map(str, argv)), cwd=repo, env=env,
                               capture_output=True, text=True, timeout=45)
    row = dict(label=label, argv=list(map(str, argv)), exit=completed.returncode,
               stdout=completed.stdout, stderr=completed.stderr)
    if result is not None and result.exists():
        row['result'] = json.loads(result.read_text(encoding='utf-8'))
    report['runs'].append(row)
    assert completed.returncode == expected, row
    if assertion:
        assert assertion in completed.stdout + completed.stderr, row
    return row

try:
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, env=env, text=True).strip() == revision, '候选已变化，停止复跑'
    for name in ['test_t091_pane_ipc.mjs', 'test_t110_cleanup.py']:
        path = 'workbench/tests/' + name
        assert (repo / path).read_bytes() == subprocess.check_output(['git', 'show', revision + ':' + path], cwd=repo, env=env), '验收文件已变化，停止复跑'
    archive = subprocess.check_output(['git', 'archive', revision, 'workbench/app',
                                      'workbench/src', 'workbench/tests'], cwd=repo, env=env)
    copy = root / 'candidate'
    copy.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as archive_file:
        for member in archive_file.getmembers():
            assert member.isfile() or member.isdir(), ('拒绝链接或特殊文件', member.name)
            assert (copy / member.name).resolve().is_relative_to(copy)
        archive_file.extractall(copy)
    ipc = repo / 'workbench/tests/test_t091_pane_ipc.mjs'
    ipc_good = root / 'ipc-good.json'
    run('ipc-good', ['node', '--experimental-vm-modules', ipc, ipc_good, '--source', copy], result=ipc_good)
    for name in ['test_t110_window_sequence.mjs', 'test_t110_reconnect_view.mjs']:
        output = root / (name + '.json')
        run(name, ['node', '--experimental-vm-modules', copy / 'workbench/tests' / name, output], result=output)
    output = root / 'cleanup-good.json'
    run('cleanup-good', ['/usr/bin/python3', '-B', repo / 'workbench/tests/test_t110_cleanup.py',
                         '--summary', output], result=output)

    # 以真实 main/transport 代码为对象；模拟边界不能冒称原生 Electron。
    main = copy / 'workbench/app/main.ts'
    original = main.read_text(encoding='utf-8')
    marker = "  app.on('browser-window-focus', updateDockBadge);"
    assert original.count(marker) == 1
    main.write_text(original.replace(marker, ''), encoding='utf-8')
    output = root / 'lost-focus-recompute.json'
    run('lost-focus-recompute', ['node', '--experimental-vm-modules', ipc, output, '--source', copy],
        expected=1, assertion='Foreground clears Dock badge', result=output)
    main.write_text(original, encoding='utf-8')

    cleanup = copy / 'workbench/tests/t108_cleanup.py'
    original = cleanup.read_text(encoding='utf-8')
    marker = "for key in ['pid', 'pgid', 'started']:"
    assert original.count(marker) == 1
    cleanup.write_text(original.replace(marker, "for key in ['pid', 'pgid']:"), encoding='utf-8')
    probe = ('import pathlib,runpy,sys; '
             'test=runpy.run_path(sys.argv[1]); '
             'test["exercise"](test["load"](pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")))')
    run('lost-started-identity', ['/usr/bin/python3', '-B', '-c', probe,
        repo / 'workbench/tests/test_t110_cleanup.py', cleanup], expected=1,
        assertion='reused_started_live_claude_title')
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = str(error)
finally:
    # 只删除本脚本新建的私有目录；不接触任何既有夹具。
    shutil.rmtree(root)
    report['fixture_removed'] = not root.exists()
    print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if report['status'] == 'PASS' else 1)
PY
