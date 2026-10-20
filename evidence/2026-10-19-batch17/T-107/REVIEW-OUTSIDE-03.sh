#!/bin/bash
# 第三轮版本核对复验；实际 HEAD 仍为第二轮候选，不能证明暂存区 F4 修复。
# 固定 f563fd518；若待审提交已更新，本脚本拒绝运行，请重新冻结候选。
# 用法：bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-03.sh [local|electron]
# electron 由执行主控在沙箱外运行，不截图、不调用模型、不操作 Herdr。
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
revision = 'f563fd5182feebfd16bee9063714e278536ddc6b'
actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
assert actual == revision, 'HEAD 已改变；本脚本只审查冻结候选，不接管新提交'
root = Path(tempfile.mkdtemp(prefix='t107-review-outside-03-', dir='/private/tmp'))
deps = Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules')
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'GIT_'))}
for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
    env.pop(key, None)
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
report = dict(candidate=revision, mode=mode, root=str(root), model_calls=0, commands=[], mutations=[], status='INCOMPLETE')
print('审查现场：' + str(root), flush=True)

def save():
    (root / 'review-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def run(name, argv, expected=0, extra=None):
    current = dict(env)
    current.update(extra or {})
    value = subprocess.run(list(map(str, argv)), cwd=repo, env=current, capture_output=True, text=True, timeout=600)
    (root / (name + '.stdout.txt')).write_text(value.stdout, encoding='utf-8')
    (root / (name + '.stderr.txt')).write_text(value.stderr, encoding='utf-8')
    report['commands'].append(dict(name=name, argv=list(map(str, argv)), exit=value.returncode, expected=expected))
    save()
    print(name + ' rc=' + str(value.returncode), flush=True)
    assert value.returncode == expected, name + '：查看保留的日志'
    return value

archive = subprocess.check_output(['git', 'archive', revision, 'workbench'], cwd=repo, env=env)
for name in ('candidate', 'unknown-idle', 'title-parent', 'read-write'):
    tree = root / name
    tree.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree)
    (tree / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
candidate = root / 'candidate'
run('candidate-projection', ['node', candidate / 'workbench/tests/test_t107_sidebar.mjs', root / 'candidate-projection.json'])
run('candidate-ipc', ['node', '--experimental-vm-modules', candidate / 'workbench/tests/test_t091_pane_ipc.mjs', root / 'candidate-ipc.json', '--source', candidate])
mutations = [
    ('unknown-idle', "  return 'unknown';\n}\n\nexport function aggregate", "  return 'idle';\n}\n\nexport function aggregate", 'Missing signal must remain unknown'),
    ('title-parent', 'parent: senders.size === 1 ? [...senders][0] : null', "parent: senders.size === 1 ? [...senders][0] : launches.find(p => p.project === record.project && p.preset === 'executor' && String(record.title ?? 'executor').includes('executor'))?.id ?? null", 'Role-only parent must be rejected'),
    ('read-write', '  const launches = store.launches()', "  store.event('sidebar_read', { source: 'sidebar' });\n  const launches = store.launches()", 'Sidebar read changed persisted tables or traces'),
]
for name, old, new, expected_error in mutations:
    path = root / name / 'workbench/src/sidebar.ts'
    text = path.read_text(encoding='utf-8')
    assert text.count(old) == 1
    path.write_text(text.replace(old, new), encoding='utf-8')
    output = root / (name + '-projection.json')
    run(name, ['node', root / name / 'workbench/tests/test_t107_sidebar.mjs', output], 1)
    observed = json.loads(output.read_text(encoding='utf-8'))
    assert expected_error in observed.get('error', ''), observed
    report['mutations'].append(dict(name=name, rejected=True, expected_error=expected_error, observed=observed))
    save()

# 独立 sentinel：真实采集器接收 rollout 文件，问题出现后必须保持未知。
# 同一内容仅改文件名，不能改变根会话问题的归属；不启动 CLI 或模型。
probe = root / 'rollout-probe.mjs'
probe.write_text(r"""
import { mkdirSync, writeFileSync, appendFileSync, mkdtempSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
const source = process.argv[2];
const load = p => import(pathToFileURL(join(source, 'workbench/src', p)));
const { OrchestrationStore } = await load('store.ts');
const { RequestRelay } = await load('relay.ts');
const { Panes } = await load('panes.ts');
const { sidebarSnapshot, gitFacts } = await load('sidebar.ts');
async function observe(prefix) {
  const root = mkdtempSync('/private/tmp/t107-review-rollout-');
  const home = join(root, 'home'), logs = join(home, 'sessions');
  mkdirSync(logs, {recursive:true}); mkdirSync(join(root,'traces','launch'), {recursive:true});
  const store = new OrchestrationStore(root); new RequestRelay(store);
  const native = 'ed2ad023-4b4d-497d-ae75-caf00d103977';
  const record = {id:'launch', thread:'thread', role:'worker', project:'p', task:'t', attempt:'a',
    cli_version:'codex-cli 0.163.0', env:{CODEX_HOME:home}};
  store.launch(record);
  const host = new Panes(root, store, {}, () => {});
  const pane = {record,attempt:{workspace:root},pty:{pid:123},state:'busy',stopped:false,archived:false,
    failed:null,native,turn:'root-turn',active:{id:'submission',nativeTurn:'root-turn'},queue:[],writing:false,
    offsets:new Map(),interrupted:false};
  host.panes.set('thread',pane);
  store.event('turn_submitted',{id:'submission'},record);
  store.event('turn_start_signal',{session_id:native,turn_id:'root-turn'},record);
  const file = join(logs,prefix + native + '.jsonl');
  writeFileSync(file,[{type:'session_meta',payload:{source:'cli',cwd:root,id:native}},
    {type:'event_msg',payload:{type:'task_started',turn_id:'root-turn'}}].map(JSON.stringify).join('\n')+'\n');
  const gates = {listProjects:()=>[],listTasks:()=>[]};
  const read = async () => (await sidebarSnapshot(gates,store,host)).agents[0].state;
  const saved = () => JSON.parse(execFileSync('python3',['-B',join(source,'workbench/tests/t107_persistence.py'),root],{encoding:'utf8'}));
  const persisted = saved(), offsets = [...pane.offsets];
  await read(); await read();
  assert.deepEqual(saved(),persisted,'Independent read changed SQLite or traces');
  assert.deepEqual([...pane.offsets],offsets,'Independent read consumed native bytes');
  host.scan(pane); const before = await read();
  assert.equal(before,'running','Positive execution before the question');
  appendFileSync(file,JSON.stringify({type:'response_item',payload:{type:'function_call',name:'request_user_input',
    call_id:'q',internal_chat_message_metadata_passthrough:{turn_id:'root-turn'}}})+'\n');
  host.scan(pane); const after = await read();
  assert.equal(pane.turn,'root-turn'); assert.equal(pane.active.nativeTurn,'root-turn');
  const error = await gitFacts(join(root,'missing-repository'));
  assert.equal(error.branch,null); assert.equal(error.ahead,null); assert.ok(error.error.includes('无法读取 Git'));
  const result = {root,file,before,after,expected_after:'unknown',unconsumed_read_zero_writes:true,question_recorded:store.db.prepare("SELECT count(*) AS n FROM orchestration_events WHERE type='native_record' AND json_extract(data,'$.record.payload.name')='request_user_input'").get().n,git_failure:error};
  store.close(); return result;
}
console.log(JSON.stringify({simple:await observe(''),rollout:await observe('rollout-2026-10-19T12-00-00-')}));
""", encoding='utf-8')
value = run('independent-rollout-probe', ['node', probe, candidate])
report['rollout_probe'] = json.loads(value.stdout)
assert report['rollout_probe']['simple']['after'] == 'unknown'
report['rollout_violation'] = report['rollout_probe']['rollout']['after'] != 'unknown'
save()

if mode == 'electron':
    # Git archive 副本只通过 GIT_DIR 读取历史对象；不建立 worktree、不写 Git 元数据。
    git_dir = subprocess.check_output(['git','rev-parse','--absolute-git-dir'], cwd=repo, env=env, text=True).strip()
    history = {'GIT_DIR':git_dir}
    run('review-fixes-counterfactual', ['python3','-B',candidate / 'workbench/tests/test_t107_review_regressions.py','--source',candidate,'--summary',root / 'review-fixes.json'], extra=history)
    dist = deps / 'electron/dist'
    assert not str(dist.resolve()).startswith('/Volumes/')
    assert (dist / 'version').read_text(encoding='utf-8').strip() == '43.4.1'
    for name, expected in [('candidate',0),('read-write',1)]:
        tree, output = root / name, root / (name + '-electron.json')
        run(name + '-electron',['python3','-B',tree / 'workbench/tests/run_t107_sidebar.py','--source',tree,'--dependencies',deps,'--electron-dist',dist,'--summary',output],expected,history)
        observed = json.loads(output.read_text(encoding='utf-8'))
        assert observed.get('cleanup_complete'), observed
        if name == 'candidate':
            assert observed.get('implemented_slice_status') == 'PASS' and observed['status'] == 'INCOMPLETE', observed
        else:
            assert 'Sidebar read changed persisted tables or traces' in observed.get('error','') or 'Sidebar read changed persisted tables or traces' in str(observed.get('commands',[])), observed
        report[name + '_electron'] = observed
        save()

report['status'] = 'NO_GO' if report['rollout_violation'] else 'INCOMPLETE'
save()
print(json.dumps(dict(status=report['status'],root=str(root),mode=mode),ensure_ascii=False))
raise SystemExit(1 if report['status'] == 'NO_GO' else 2)
PY
