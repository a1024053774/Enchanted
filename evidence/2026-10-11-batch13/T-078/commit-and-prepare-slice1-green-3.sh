#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base = Path('evidence/2026-10-11-batch13/T-078')
before = '41672c9363ce5c70689f2e3a9f71d16256e9a9a7'
def git(*args): return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()
assert git('rev-parse', 'HEAD') == before and git('branch', '--show-current') == 'exec/t078'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK') == 'T-078-1' and os.environ.get('A2A_ROLE') == 'worker'
assert not any(k in os.environ for k in ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'])
assert not git('diff', '--cached', '--name-only'), 'Preserve existing staged work'
assert not git('diff', '--', 'workbench/src', 'workbench/app', 'workbench/hooks', 'workbench/bin', 'acceptance', 'scripts')
cleanup = json.loads((base / 'p1-materials-slice1-green/cleanup-184/result.json').read_bytes())
assert cleanup['status'] == 'PASS' and cleanup['owned_exits_confirmed'] == [44036, 44048, 44069, 44068]
assert cleanup['byte_readback'] == 'PASS' and cleanup['root_retained'] is True and cleanup['root_removed'] is False
assert cleanup['slots_removed'] == [] and cleanup['signals_sent'] in [[], [{'pid': 44036, 'signal': 'SIGTERM'}]]
regression = json.loads((base / 'controller-green-outside-02/result.json').read_bytes())
assert regression['status'] == 'PASS'
for name, count in [('controller-entry',6),('empty-declaration-entry',17),('runtime',12),('input-failures',11),('worker-inbox',14)]:
    facts = json.loads((base / 'controller-green-outside-02' / name / 'results.json').read_bytes())
    assert facts['status'] == 'PASS' and len(facts['checks']) == count and all(c['status'] == 'PASS' for c in facts['checks'])
    if name in ['runtime','input-failures','worker-inbox']: assert facts['setup_complete'] is True and facts['cleanup_complete'] is True
assert not git('diff', regression['revision'], 'HEAD', '--', 'workbench/src', 'workbench/app', 'workbench/hooks', 'workbench/bin', 'acceptance', 'scripts')
paths = json.loads((base / 'controller-green-3-handoff-paths.json').read_bytes())
for row in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode('utf-8').split('\0'):
    if row:
        name = row[3:]
        assert any(name == p or name.startswith(p + '/') for p in paths), ('Unowned work; no mutation', name)
assert all(Path(p).exists() for p in paths), 'Missing handoff path'
for p in ['controller-green-3-code-freeze.json', 'controller-green-3-preparation-run', 'p1-materials-slice1-green-3']:
    assert not (base / p).exists(), ('Existing output; preserve it, no retry', p)
subprocess.run(['git', 'diff', '--check'], check=True)
subprocess.run(['git', 'add', '--', *paths], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'test(T-078): compare native feedback with registered dispatch text'], check=True)
revision = git('rev-parse', 'HEAD')
with (base / 'controller-green-3-code-freeze.json').open('x', encoding='utf-8') as f:
    json.dump({'revision': revision, 'parent_revision': before, 'product_source_revision': '455696c98e99b73a118886345ab1d83de24e0bdf',
               'reused_regression_revision': regression['revision'], 'root_submit_budget': 2, 'messages_request_budget': 3,
               'tool_call_budget': 1, 'real_model_turns': 0, 'old_scene_status': 'INCOMPLETE', 'old_budget_status': 'NO_GO'}, f, indent=2); f.write('\n')
run = base / 'controller-green-3-preparation-run'; run.mkdir()
def execute(name, argv):
    argv = list(map(str, argv))
    with (run / (name + '.stdout.bin')).open('xb') as stdout, (run / (name + '.stderr.bin')).open('xb') as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr)
    with (run / (name + '.command.json')).open('x', encoding='utf-8') as f:
        json.dump({'argv': argv, 'revision': revision, 'exit_code': result.returncode}, f, indent=2); f.write('\n')
    assert result.returncode == 0, ('Failed; preserve commit/output/fixture; no retry or next action', name)
execute('project-map-status', ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
execute('prepare-slice1-green', [sys.executable, '-B', (base / 'prepare-slice1-green.py').resolve(),
        '--freeze', (base / 'controller-green-3-code-freeze.json').resolve(),
        '--regression', (base / 'controller-green-outside-02').resolve(), '--label', 'p1-materials-slice1-green-3'])
packet = base / 'p1-materials-slice1-green-3'
facts = json.loads((packet / 'static-check.json').read_bytes())
assert facts['status'] == 'PASS' and facts['revision'] == revision and facts['regression_reused'] is True
with (base / 'RESULTS.md').open('a', encoding='utf-8') as f:
    f.write('\n## 原场景清理与新文本校验材料冻结（脚本执行读回）\n\n')
    f.write('[原场景cleanup](p1-materials-slice1-green/cleanup-184/result.json) **PASS**：确认四个原进程退出、最多仅API44036一次SIGTERM、外置归档字节读回；根／slot保持，原场景仍INCOMPLETE／预算NO_GO。新source `' + revision + '`，产品沿用455696c9；相关outside-02源码未变，明确复用、不称新运行。\n\n')
    f.write('[新实例静态核对](p1-materials-slice1-green-3/static-check.json) **PASS**：root `' + facts['root'] + '`、launch `' + facts['launch'] + '`、session `' + facts['session'] + '`；新HOME/IDs/nonce，Git/tar逐文件相同、批准字段空。根2/Messages3/Bash1/模型0；未launch，真实完整绿态、独立审查、09B/09C与整票仍 **INCOMPLETE**。\n')
second = [str(packet), str(run), str(base / 'controller-green-3-code-freeze.json'), str(base / 'RESULTS.md')]
subprocess.run(['git', 'add', '--', *second], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze fresh controller green text-format materials'], check=True)
assert not git('status', '--porcelain'), 'Preserve unexpected remaining work; no cleanup'
print(json.dumps({'status': 'PASS', 'source_revision': revision, 'materials_revision': git('rev-parse', 'HEAD'),
                  'materials': str(packet), 'root': facts['root'], 'launch': facts['launch'],
                  'next': 'Read new packet and approve launch separately; no native CLI/API started'}, ensure_ascii=False))
PY
