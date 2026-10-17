#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base = Path('evidence/2026-10-11-batch13/T-078')
before = '455696c98e99b73a118886345ab1d83de24e0bdf'
def git(*args): return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()
assert git('rev-parse', 'HEAD') == before and git('branch', '--show-current') == 'exec/t078'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK') == 'T-078-1' and os.environ.get('A2A_ROLE') == 'worker'
assert not any(k in os.environ for k in ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'])
assert not git('diff', '--cached', '--name-only'), 'Preserve existing staged work'
assert not git('diff', '--', 'workbench/src', 'workbench/app', 'workbench/hooks', 'workbench/bin', 'acceptance', 'scripts'), 'This is a fixture/document repair, not a product change'
prior = json.loads((base / 'controller-green-outside-01/result.json').read_bytes())
entry = json.loads((base / 'controller-green-outside-01/controller-entry/results.json').read_bytes())
assert prior['status'] == entry['status'] == 'INCOMPLETE' and prior['revision'] == before
assert len(entry['checks']) == 5 and all(c['status'] == 'PASS' for c in entry['checks'][:4])
assert entry['checks'][4]['name'] == 'real-Stop-transfers-as-ideation-and-queues-feedback'
assert "undefined !== '\\r'" in entry['checks'][4]['error']
paths = json.loads((base / 'controller-green-2-handoff-paths.json').read_bytes())
for row in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode('utf-8').split('\0'):
    if row:
        name = row[3:]
        assert any(name == p or name.startswith(p + '/') for p in paths), ('Unowned work; no mutation', name)
assert all(Path(p).exists() for p in paths), 'Missing handoff path'
for p in ['controller-green-2-code-freeze.json', 'controller-green-outside-02', 'controller-green-2-preparation-run', 'p1-materials-slice1-green']:
    assert not (base / p).exists(), ('Existing output; preserve it, no retry', p)
subprocess.run(['git', 'diff', '--check'], check=True)
subprocess.run(['git', 'add', '--', *paths], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'test(T-078): wait for feedback submission before entry assertions'], check=True)
revision = git('rev-parse', 'HEAD')
with (base / 'controller-green-2-code-freeze.json').open('x', encoding='utf-8') as f:
    json.dump({'revision': revision, 'parent_revision': before, 'product_source_revision': before,
               'root_submit_budget': 2, 'messages_request_budget': 3, 'tool_call_budget': 1,
               'real_model_turns': 0, 'prior_failure_preserved': 'controller-green-outside-01'}, f, indent=2); f.write('\n')
run = base / 'controller-green-2-preparation-run'; run.mkdir()
def execute(name, argv):
    argv = list(map(str, argv))
    with (run / (name + '.stdout.bin')).open('xb') as stdout, (run / (name + '.stderr.bin')).open('xb') as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr)
    with (run / (name + '.command.json')).open('x', encoding='utf-8') as f:
        json.dump({'argv': argv, 'revision': revision, 'exit_code': result.returncode}, f, indent=2); f.write('\n')
    assert result.returncode == 0, ('Failed; preserve commit/output/fixture; no retry or next action', name)
execute('project-map-status', ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
freeze = (base / 'controller-green-2-code-freeze.json').resolve()
regression = (base / 'controller-green-outside-02').resolve()
execute('controller-green-stage', [sys.executable, '-B', (base / 'controller-green-stage.py').resolve(), '--output', regression, '--freeze', freeze])
execute('prepare-slice1-green', [sys.executable, '-B', (base / 'prepare-slice1-green.py').resolve(), '--regression', regression, '--freeze', freeze])
packet = base / 'p1-materials-slice1-green'
facts = json.loads((packet / 'static-check.json').read_bytes())
assert facts['status'] == 'PASS' and facts['revision'] == revision
with (base / 'RESULTS.md').open('a', encoding='utf-8') as f:
    f.write('\n## controller 入口续跑与新材料冻结（脚本执行读回）\n\n')
    f.write('夹具／README 提交 `' + revision + '`，产品源码沿用 `455696c98e99b73a118886345ab1d83de24e0bdf`；提交后 project_map status **PASS**。新 [outside-02](controller-green-outside-02/result.json) **PASS**：controller-entry6、空框17、runtime12、input-failures11、worker-inbox14；UI 三组 setup/cleanup 均确认，原 outside-01 失败与原数据库归档保持原样。\n\n')
    f.write('[新实例静态核对](p1-materials-slice1-green/static-check.json) **PASS**：root `' + facts['root'] + '`、launch `' + facts['launch'] + '`、session `' + facts['session'] + '`；绑定本次 source，逐文件 Git/tar 字节相同，批准字段空。根2、Messages3、Bash1、模型0。实际 Claude 绿态／launch 尚未执行，独立审查、09B/09C、整票仍 **INCOMPLETE**。\n')
second = [str(packet), str(run), str(regression), str(base / 'controller-green-2-code-freeze.json'), str(base / 'RESULTS.md')]
subprocess.run(['git', 'add', '--', *second], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze controller green materials after entry timing repair'], check=True)
assert not git('status', '--porcelain'), 'Preserve unexpected remaining work; no cleanup'
print(json.dumps({'status': 'PASS', 'source_revision': revision, 'materials_revision': git('rev-parse', 'HEAD'),
                  'materials': str(packet), 'root': facts['root'], 'launch': facts['launch'],
                  'next': 'Read actual new packet; approve launch separately; no native CLI/API started'}, ensure_ascii=False))
PY
