#!/bin/zsh
# T-111 第一轮独立审查。默认跑真实入口；--local 仅跑不需要窗口或 socket 的部分。
# 所有副本、变异、报告和构建都在内置盘 /private/tmp；不修改原仓库或全局配置。
set -euo pipefail
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
python3 - "$@" <<'PY'
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

origin = Path('/Users/luckye/Documents/Code/a2a-wt-t111')
revision = '43717b803a6f3db84cf3420921fd277aa7d13c1a'
root = Path(tempfile.mkdtemp(prefix='t111-review-01-', dir='/private/tmp'))
local = '--local' in sys.argv
env = {k:v for k,v in os.environ.items() if not k.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
report = dict(status='INCOMPLETE', candidate=revision, root=str(root), mode='local' if local else 'outside', checks=[], model_calls=0)

def run(name, argv, expected=0):
    result = subprocess.run(list(map(str,argv)), cwd=origin, env=env, capture_output=True, text=True, timeout=300)
    (root/(name+'.stdout')).write_text(result.stdout,encoding='utf-8')
    (root/(name+'.stderr')).write_text(result.stderr,encoding='utf-8')
    report['checks'].append(dict(name=name, argv=list(map(str,argv)), exit=result.returncode, expected=expected))
    (root/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert result.returncode == expected, (name,result.returncode,result.stdout[-2000:],result.stderr[-2000:])

def archive(name):
    tree = root/name
    tree.mkdir()
    raw = subprocess.check_output(['git','archive',revision,'workbench'],cwd=origin,env=env)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        tar.extractall(tree)
    return tree

def replace(tree, old, new):
    path=tree/'workbench/src/flow.ts'
    value=path.read_text(encoding='utf-8')
    assert value.count(old)==1, old
    path.write_text(value.replace(old,new),encoding='utf-8')

try:
    candidate=archive('candidate')
    # 普通文件副本，不建链接；执行位只改私有测试运行目录。
    shutil.copytree(origin/'workbench/node_modules',candidate/'workbench/node_modules',symlinks=False)
    shutil.copytree(origin/'workbench/node_modules',root/'node_modules',symlinks=False)
    test=candidate/'workbench/tests/test_t111_flow.mjs'
    run('candidate-contract',['node',test,root/'candidate-contract.json',candidate])
    run('candidate-ipc',['node','--experimental-vm-modules',candidate/'workbench/tests/test_t091_pane_ipc.mjs',root/'candidate-ipc.json','--source',candidate])
    probe=root/'two-returns.mjs'
    probe.write_text('''import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const {projectFlow}=await import(pathToFileURL(process.argv[2]+'/workbench/src/flow.ts'));
const tasks=[{task_id:'T-unseen',project_id:'p',title:'独立输入',current_attempt:{attempt_id:'now'}}];
const events=[{task:'T-unseen',attempt:'now',type:'claimed',details:{}},
 {task:'T-unseen',attempt:'old',type:'delivery_rejected',details:{repair:{check:'completion'}}},
 {task:'T-unseen',attempt:'now',type:'delivery_rejected',details:{repair:{check:'independent_review'}}},
 {task:'T-unseen',attempt:'now',type:'review_result',details:{review:{state:'needs_fix'}}}];
const lane=projectFlow(tasks,[],events).lanes[0];
assert.equal(lane.returns.length,2,'Two gate rejection facts must remain two returns');
assert.deepEqual(lane.returns.map(x=>x.from),['checks','review']);
assert.equal(projectFlow(tasks,[],events.filter(x=>x.type!=='delivery_rejected')).lanes[0].returns.length,0);
console.log('PASS: 两条门禁打回事实，跨 attempt；附属审查结果不重复计数');
''',encoding='utf-8')
    run('candidate-two-returns',['node',probe,candidate])
    count=archive('count-mutant')
    replace(count,"event.type === 'delivery_rejected')","event.type === 'delivery_rejected').slice(0, 1)")
    # 变异一：非零打回次数永远为 1。当前交付合同漏检，独立双打回输入拒绝。
    run('count-mutant-existing-contract',['node',test,root/'count-mutant-existing-contract.json',count])
    run('count-mutant-independent-probe',['node',probe,count],1)
    assert 'Two gate rejection facts must remain two returns' in (root/'count-mutant-independent-probe.stderr').read_text(encoding='utf-8')
    missing=archive('missing-attempt-mutant')
    replace(missing,"typeof task.current_attempt?.attempt_id === 'string' && task.current_attempt.attempt_id.length > 0 &&",'true &&')
    # 变异二：把两个 undefined 当成相同 attempt；现有合同应拒绝。
    run('missing-attempt-mutant',['node',test,root/'missing-attempt-mutant.json',missing],1)
    assert 'Missing attempt binding must stay unassigned' in json.loads((root/'missing-attempt-mutant.json').read_text(encoding='utf-8')).get('error','')
    if not local:
        readonly=candidate/'workbench/tests/test_t107_daemon_readonly.mjs'
        run('candidate-flow-readonly',['node','--experimental-vm-modules',readonly,root/'candidate-flow-readonly.json',candidate,'flow'])
        run('candidate-sidebar-readonly',['node','--experimental-vm-modules',readonly,root/'candidate-sidebar-readonly.json',candidate,'readonly'])
        write=archive('write-mutant')
        replace(write,'  const sidebar = await sidebarSnapshot(gates, store, panes);',"  store.event('independent_flow_read_write', {});\n  const sidebar = await sidebarSnapshot(gates, store, panes);")
        # 变异三：流程读取写事件；真实 socket/SQLite 原值比较应拒绝。
        run('write-mutant',['node','--experimental-vm-modules',readonly,root/'write-mutant.json',write,'flow'],1)
        value=json.loads((root/'write-mutant.json').read_text(encoding='utf-8'))
        assert value.get('cleanup_complete') and 'Sidebar read changed persisted tables or traces' in value.get('error',''),value
        # 归档没有 .git。只把测试驱动的 Git 溯源查询定向到原仓库只读，产品不变。
        # 不伪造 archive 的 revision，也不在任一副本创建 worktree 或提交。
        runner=candidate/'workbench/tests/run_t111_flow.py'
        text=runner.read_text(encoding='utf-8')
        text=text.replace("revision = run(['git', 'rev-parse', 'HEAD']).stdout.strip()",'revision = '+repr(revision))
        text=text.replace("report['source_changes'] = run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'workbench']).stdout.splitlines()","report['source_changes'] = [] if source.name == 'candidate' else ['reviewer count mutation']")
        text=text.replace("cwd=source, env=env)","cwd="+repr(str(origin))+", env=env)")
        runner.write_text(text,encoding='utf-8')
        dist=os.environ.get('T111_ELECTRON_DIST','/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist')
        run('candidate-electron',['python3',runner,'--source',candidate,'--electron-dist',dist,'--summary',root/'candidate-electron.json'])
        shutil.copytree(candidate/'workbench/node_modules',count/'workbench/node_modules',symlinks=False)
        # 同一真实 Electron 完成条件：确认计数错误变异是否仍会被接受。
        run('count-mutant-existing-electron',['python3',runner,'--source',count,'--electron-dist',dist,'--summary',root/'count-mutant-existing-electron.json'])
    report['status']='NO_GO'
    report['finding']='现有完成条件接受非零打回次数恒为 1 的单处错误实现；独立双打回输入拒绝。'
finally:
    (root/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
PY
