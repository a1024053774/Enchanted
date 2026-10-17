#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base = Path('evidence/2026-10-11-batch13/T-078')
before = '5b404cb91a4415d31ff2ba2aa113de7d9bea0994'
def git(*args): return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()
assert git('rev-parse', 'HEAD') == before and git('branch', '--show-current') == 'exec/t078'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK') == 'T-078-1' and os.environ.get('A2A_ROLE') == 'worker'
assert not any(k in os.environ for k in ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'])
assert not git('diff', '--cached', '--name-only'), 'Preserve existing staged work'
paths = json.loads((base / 'controller-green-handoff-paths.json').read_bytes())
for row in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode('utf-8').split('\0'):
    if row:
        name = row[3:]
        assert any(name == p or name.startswith(p + '/') for p in paths), ('Unowned work; no mutation', name)
assert all(Path(p).exists() for p in paths), 'Missing handoff path'
for p in ['controller-green-code-freeze.json', 'controller-green-outside-01', 'controller-green-preparation-run', 'p1-materials-slice1-green']:
    assert not (base / p).exists(), ('Existing output; preserve it, no retry', p)
subprocess.run(['git', 'diff', '--check'], check=True)
subprocess.run(['git', 'add', '--', *paths], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'fix(T-078): relay native controller requests with bound caller'], check=True)
revision = git('rev-parse', 'HEAD')
with (base / 'controller-green-code-freeze.json').open('x', encoding='utf-8') as f:
    json.dump({'revision': revision, 'parent_revision': before, 'root_submit_budget': 2,
               'messages_request_budget': 3, 'tool_call_budget': 1, 'real_model_turns': 0,
               'next': 'Actual transport regressions, then static material generation; no native CLI launch'}, f, indent=2); f.write('\n')
run = base / 'controller-green-preparation-run'; run.mkdir()
def execute(name):
    argv = [sys.executable, '-B', str((base / name).resolve())]
    with (run / (name + '.stdout.bin')).open('xb') as stdout, (run / (name + '.stderr.bin')).open('xb') as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr)
    with (run / (name + '.command.json')).open('x', encoding='utf-8') as f:
        json.dump({'argv': argv, 'revision': revision, 'exit_code': result.returncode}, f, indent=2); f.write('\n')
    assert result.returncode == 0, ('Stage failed; preserve commit/output/fixture, no retry or next action', name)
execute('controller-green-stage.py')
execute('prepare-slice1-green.py')
packet = base / 'p1-materials-slice1-green'
facts = json.loads((packet / 'static-check.json').read_bytes())
assert facts['status'] == 'PASS' and facts['revision'] == revision
with (base / 'RESULTS.md').open('a', encoding='utf-8') as f:
    f.write('\n## controller 入口回归与新绿态材料冻结（脚本执行读回）\n\n')
    f.write('代码提交 `' + revision + '`；[新入口阶段](controller-green-outside-01/result.json) **PASS**：controller-entry6、空框17、runtime12、input-failures11、worker-inbox14。UI 三场景 setup/cleanup 均确认，原生 spy 边界仍单列；未启动供应商 CLI。\n\n')
    f.write('[新实例静态核对](p1-materials-slice1-green/static-check.json) **PASS**：root `' + facts['root'] + '`、launch `' + facts['launch'] + '`、session `' + facts['session'] + '`；绑定上述源码，逐文件 Git/tar 字节相同，批准字段空。根2、Messages3、Bash1、模型0。真实 Claude 绿态／launch 尚未执行，独立审查、README stale、09B/09C、整票仍 **INCOMPLETE**。\n')
second = [str(packet), str(run), str(base / 'controller-green-outside-01'), str(base / 'controller-green-code-freeze.json'), str(base / 'RESULTS.md')]
subprocess.run(['git', 'add', '--', *second], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze one-controller green launch packet'], check=True)
assert not git('status', '--porcelain'), 'Preserve unexpected remaining work; no cleanup'
print(json.dumps({'status': 'PASS', 'source_revision': revision, 'materials_revision': git('rev-parse', 'HEAD'),
                  'materials': str(packet), 'root': facts['root'], 'launch': facts['launch'],
                  'next': 'Review new packet and approve launch separately; no native CLI/API started'}, ensure_ascii=False))
PY
