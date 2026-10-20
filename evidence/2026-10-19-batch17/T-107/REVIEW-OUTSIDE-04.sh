#!/bin/bash
# T-107 第四轮独立复验：绑定提交 dc37cd6abd10bbb18fad282398924a1f041c34d1。
# 只从 git archive 建一次性副本，不建 worktree、不写候选仓库。
# 用法：bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-04.sh [local|electron]
# electron 由执行主控在沙箱外运行；不截图、不调用模型、不操作 Herdr。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t107
export LC_ALL=C
export PYTHONDONTWRITEBYTECODE=1
python3 -B - "$PWD" "${1:-electron}" <<'PY'
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

repo, mode = Path(sys.argv[1]), sys.argv[2]
assert mode in ('local', 'electron')
revision = 'dc37cd6abd10bbb18fad282398924a1f041c34d1'
actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
assert actual == revision, 'HEAD 已改变；本脚本只审查冻结候选，不接管新提交'
root = Path(tempfile.mkdtemp(prefix='t107-review-outside-04-', dir='/private/tmp'))
deps = Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules')
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'GIT_'))}
for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
    env.pop(key, None)
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', T107_DEPENDENCIES=str(deps),
           GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
report = dict(candidate=revision, mode=mode, root=str(root), model_calls=0,
              commands=[], mutations=[], checks=[], status='INCOMPLETE')
print('审查现场：' + str(root), flush=True)


def save():
    (root / 'review-summary.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(name, argv, expected=0, extra=None):
    current = dict(env)
    current.update(extra or {})
    value = subprocess.run(list(map(str, argv)), cwd=repo, env=current,
                           capture_output=True, text=True, timeout=900)
    (root / (name + '.stdout.txt')).write_text(value.stdout, encoding='utf-8')
    (root / (name + '.stderr.txt')).write_text(value.stderr, encoding='utf-8')
    row = dict(name=name, argv=list(map(str, argv)), exit=value.returncode,
               expected=expected)
    report['commands'].append(row)
    save()
    print(name + ' rc=' + str(value.returncode), flush=True)
    assert value.returncode == expected, name + '：查看保留的日志'
    return value


archive = subprocess.check_output(['git', 'archive', revision, 'workbench'], cwd=repo, env=env)
git_dir = subprocess.check_output(
    ['git', 'rev-parse', '--absolute-git-dir'], cwd=repo, env=env, text=True).strip()
for name in ('candidate', 'unknown-idle', 'title-parent', 'read-write'):
    tree = root / name
    tree.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree)
    # 仅供真实 Electron runner 读取已冻结历史对象；不是 worktree，不写 Git 元数据。
    # 不放 GIT_DIR 进子进程环境，避免夹具 git init 被继承的 GIT_DIR 劫持。
    (tree / '.git').write_text('gitdir: ' + git_dir + '\n', encoding='utf-8')
    (tree / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
candidate = root / 'candidate'

# 先确认候选本身通过投影、IPC、实际 daemon 和作者反事实重放。
projection = root / 'candidate-projection.json'
run('candidate-projection',
    ['node', candidate / 'workbench/tests/test_t107_sidebar.mjs', projection])
assert json.loads(projection.read_text(encoding='utf-8'))['status'] == 'PASS'
report['checks'].append('candidate_projection_git_sqlite_unknown_rollout_and_ancestry')

ipc = root / 'candidate-ipc.json'
run('candidate-ipc',
    ['node', '--experimental-vm-modules', candidate / 'workbench/tests/test_t091_pane_ipc.mjs',
     ipc, '--source', candidate])
assert json.loads(ipc.read_text(encoding='utf-8'))['status'] == 'PASS'
report['checks'].append('candidate_ipc_20_handlers_21_bridge_and_known_bad_sidebar')

for daemon_mode in ('readonly', 'identity', 'filename', 'rollout'):
    output = root / ('daemon-' + daemon_mode + '.json')
    run('candidate-daemon-' + daemon_mode,
        ['node', '--experimental-vm-modules',
         candidate / 'workbench/tests/test_t107_daemon_readonly.mjs',
         output, candidate, daemon_mode])
    observed = json.loads(output.read_text(encoding='utf-8'))
    assert observed['status'] == 'PASS' and observed.get('cleanup_complete'), observed
    if daemon_mode in ('filename', 'rollout'):
        assert observed['before_question'] == 'running', observed
        assert observed['observed'] == 'unknown', observed
        assert observed['filename'].endswith('root-session.jsonl'), observed
report['rollout_probe'] = {
    'filename': json.loads((root / 'daemon-filename.json').read_text(encoding='utf-8')),
    'rollout': json.loads((root / 'daemon-rollout.json').read_text(encoding='utf-8')),
}
report['checks'].append('independent_rollout_filename_sentinel_before_running_after_unknown')
report['checks'].append('actual_daemon_socket_sqlite_trace_read_zero_writes')

counterexamples = root / 'candidate-counterexamples.json'
run('candidate-counterexamples',
    ['python3', '-B', candidate / 'workbench/tests/test_t107_counterexamples.py',
     counterexamples])
assert json.loads(counterexamples.read_text(encoding='utf-8'))['status'] == 'PASS'
report['checks'].append('candidate_single_fault_counterexamples_rejected')

# T-096 原恢复契约与五条拒绝提示仍通过；这不是 T-107 新造的全页错误。
t096 = root / 'candidate-t096.json'
run('candidate-t096-restore',
    ['node', '--experimental-vm-modules', candidate / 'workbench/tests/test_t096_restore.mjs',
     t096])
assert json.loads(t096.read_text(encoding='utf-8'))['status'] == 'PASS'
report['checks'].append('t096_restoration_and_precise_refusals_unchanged')

# F4 单一红绿对照：旧候选的精确文件名通过，rollout 前缀在同一未答问题后
# 被同一 submission 的 start 钩子上调成 running；当前候选两种名称都保持 unknown。
f4_revision = 'f563fd5182feebfd16bee9063714e278536ddc6b'
f4_tree = root / 'f4-baseline'
f4_tree.mkdir()
f4_archive = subprocess.check_output(['git', 'archive', f4_revision, 'workbench'],
                                     cwd=repo, env=env)
with tarfile.open(fileobj=io.BytesIO(f4_archive)) as tar:
    tar.extractall(f4_tree)
(f4_tree / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
old_filename = root / 'old-f4-filename.json'
run('old-f4-filename',
    ['node', '--experimental-vm-modules',
     candidate / 'workbench/tests/test_t107_daemon_readonly.mjs',
     old_filename, f4_tree, 'filename'])
old_rollout = root / 'old-f4-rollout.json'
old_rollout_run = run('old-f4-rollout',
    ['node', '--experimental-vm-modules',
     candidate / 'workbench/tests/test_t107_daemon_readonly.mjs',
     old_rollout, f4_tree, 'rollout'], 1)
old_rollout_report = json.loads(old_rollout.read_text(encoding='utf-8'))
assert 'Unanswered root question must stay unknown under either native filename' in \
    old_rollout_report.get('error', ''), old_rollout_report
report['f4_counterfactual'] = {
    'baseline': f4_revision,
    'filename_status': json.loads(old_filename.read_text(encoding='utf-8'))['status'],
    'rollout_status': old_rollout_report['status'],
    'rollout_error': old_rollout_report.get('error'),
}
report['checks'].append('f4_old_rollout_red_and_current_filename_rollout_green')

# 独立 Git 失败输入：返回 null 与具体原因，不把缺上游或读取失败猜成 0。
git_probe = root / 'git-failure-probe.mjs'
git_probe.write_text(r"""
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const source = process.argv[2];
const { gitFacts } = await import(pathToFileURL(join(source, 'workbench/src/sidebar.ts')));
const value = await gitFacts(join(source, 'does-not-exist-' + process.pid));
assert.equal(value.branch, null);
assert.equal(value.upstream, null);
assert.equal(value.ahead, null);
assert.equal(value.behind, null);
assert.match(value.error, /^无法读取 Git：/);
console.log(JSON.stringify(value));
""", encoding='utf-8')
git_output = run('candidate-git-failure', ['node', git_probe, candidate])
report['git_failure'] = json.loads(git_output.stdout)
report['checks'].append('git_read_failure_returns_null_facts_and_reason')

# “按窗格标题猜父层级”的反例。候选只接受成功 assign 与已派发目标的事实；
# 这里给两条启动记录写入相同的伪标题，但没有派发事实，worker 必须未归属。
hierarchy_probe = root / 'hierarchy-probe.mjs'
hierarchy_probe.write_text(r"""
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const source = process.argv[2], root = mkdtempSync('/private/tmp/t107-title-parent-');
const { OrchestrationStore } = await import(pathToFileURL(join(source, 'workbench/src/store.ts')));
const { sidebarSnapshot } = await import(pathToFileURL(join(source, 'workbench/src/sidebar.ts')));
const store = new OrchestrationStore(root);
store.db.exec(`CREATE TABLE relay_requests (key TEXT PRIMARY KEY,launch TEXT,task TEXT,attempt TEXT,request_id TEXT,input TEXT,created_at TEXT);
  CREATE TABLE relay_results (key TEXT PRIMARY KEY,data TEXT,created_at TEXT);`);
const common = { project: 'project', task: 'task', cli_version: 'codex-cli 0.163.0', title: '执行主控' };
store.launch({ ...common, id: 'exec', thread: 'exec-thread', role: 'controller',
  preset: 'executor', attempt: null });
store.launch({ ...common, id: 'worker', thread: 'worker-thread', role: 'worker',
  preset: null, attempt: 'attempt' });
const gates = { listProjects: () => [], listTasks: () => [] };
const panes = { status: () => ({ lifecycle: 'running', state: 'unknown', active: null }) };
const value = await sidebarSnapshot(gates, store, panes);
const worker = value.agents.find(row => row.id === 'worker');
assert.equal(worker.parent, null, 'Pane title or role alone must not infer a parent');
store.close();
console.log(JSON.stringify({ worker_parent: worker.parent }));
""", encoding='utf-8')
title_candidate = run('candidate-title-parent-probe', ['node', hierarchy_probe, candidate])
report['title_parent_candidate'] = json.loads(title_candidate.stdout)

mutations = [
    ('unknown-idle',
     "  return 'unknown';\n}\n\nexport function aggregate",
     "  return 'idle';\n}\n\nexport function aggregate",
     'Missing signal must remain unknown'),
    ('title-parent',
     "parent: senders.size === 1 ? [...senders][0] : null",
     "parent: senders.size === 1 ? [...senders][0] : record.title === '执行主控' ? launches.find(p => p.project === record.project && p.preset === 'executor')?.id ?? null : null",
     'Pane title or role alone must not infer a parent'),
    ('read-write',
     '  const launches = store.launches()',
     "  store.event('sidebar_read', { source: 'sidebar' });\n  const launches = store.launches()",
     'Sidebar read changed persisted tables or traces'),
]
for name, old, new, expected_error in mutations:
    path = root / name / 'workbench/src/sidebar.ts'
    text = path.read_text(encoding='utf-8')
    assert text.count(old) == 1, (name, text.count(old))
    path.write_text(text.replace(old, new), encoding='utf-8')
    if name == 'title-parent':
        value = run(name, ['node', hierarchy_probe, root / name], 1)
        observed_error = value.stderr
    else:
        output = root / (name + '-projection.json')
        value = run(name, ['node', root / name / 'workbench/tests/test_t107_sidebar.mjs',
                           output], 1)
        observed = json.loads(output.read_text(encoding='utf-8'))
        observed_error = observed.get('error', '')
        assert expected_error in observed_error, observed
    if name == 'title-parent':
        assert expected_error in observed_error, observed_error
    report['mutations'].append(dict(name=name, rejected=True, expected_error=expected_error,
                                    observed_error=observed_error[-2000:]))
    save()

if mode == 'electron':
    # 内置盘 Electron 43.4.1；使用 guard 的真实入口副本来复核候选旅程。
    # 写库变异必须在侧栏读取前后的全表、schema 与 trace 比较上被业务断言拒绝。
    dist = deps / 'electron/dist'
    assert not str(dist.resolve()).startswith('/Volumes/')
    assert (dist / 'version').read_text(encoding='utf-8').strip() == '43.4.1'
    for name, expected in [('candidate', 0), ('read-write', 1)]:
        tree = root / name
        output = root / (name + '-electron.json')
        run(name + '-electron',
            ['python3', '-B', tree / 'workbench/tests/run_t107_sidebar.py',
             '--source', tree, '--dependencies', deps, '--electron-dist', dist,
             '--summary', output], expected)
        observed = json.loads(output.read_text(encoding='utf-8'))
        assert observed.get('cleanup_complete'), observed
        if name == 'candidate':
            assert observed.get('implemented_slice_status') == 'PASS', observed
            assert observed.get('status') == 'INCOMPLETE', observed
        else:
            combined = observed.get('error', '') + str(observed.get('commands', []))
            assert 'Sidebar read changed persisted tables or traces' in combined, observed
        report[name + '_electron'] = observed
        save()

report['status'] = 'INCOMPLETE'
save()
print(json.dumps(dict(status=report['status'], root=str(root), mode=mode),
                 ensure_ascii=False))
# 本轮没有新增产品红态；整票仍因作者声明且本轮核实的三个信号缺口为 INCOMPLETE。
raise SystemExit(2)
PY
