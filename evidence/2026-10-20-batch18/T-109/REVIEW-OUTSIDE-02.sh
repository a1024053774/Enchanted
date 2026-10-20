#!/bin/zsh
# T-109 第二轮独立复验。仅写新建的 /tmp 副本；不截图、不调用模型。
# 默认含真实 Electron；T109_REVIEW_LOCAL_ONLY=1 只跑沙箱内检查并标记未运行项。
set -euo pipefail
TASK_ROOT=/Users/luckye/Documents/Code/a2a-wt-t109
TASK_DIST=${T109_ELECTRON_DIST:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
python3 - "$TASK_ROOT" "$TASK_DIST" <<'PYTHON'
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback

repo, dist = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
candidate = 'a13908c04dd5f3a73c456cb173caefab0d5ef3f6'
baseline = '6411bdff8482ba47da207efa6a295a12666222aa'
root = Path(tempfile.mkdtemp(prefix='t109-review02-', dir='/private/tmp')).resolve()
tree = root / 'candidate'
env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
    env.pop(key, None)
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
report = dict(status='INCOMPLETE', task='T-109', attempt='a1', candidate=candidate, baseline=baseline,
              model_calls=0, root=str(root), commands=[], checks=[], mutations=[], not_run=[])

def run(name, argv, cwd=tree, expected=0, timeout=180):
    command = list(map(str, argv))
    try:
        value = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        (root / (name + '.stdout')).write_bytes(error.stdout or b'')
        (root / (name + '.stderr')).write_bytes(error.stderr or b'')
        report['commands'].append(dict(name=name, argv=command, cwd=str(cwd), exit=None, timeout=timeout))
        raise
    (root / (name + '.stdout')).write_text(value.stdout, encoding='utf-8')
    (root / (name + '.stderr')).write_text(value.stderr, encoding='utf-8')
    report['commands'].append(dict(name=name, argv=command, cwd=str(cwd), exit=value.returncode))
    assert value.returncode == expected, (name, value.returncode, value.stdout[-2000:], value.stderr[-1500:])
    return value.stdout

def extract(paths):
    raw = subprocess.check_output(['git', 'archive', candidate, *paths], cwd=repo, env=env)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive.getmembers():
            assert not item.name.startswith('/') and '..' not in Path(item.name).parts
            assert not item.islnk(), item.name
            if item.issym():
                target = (tree / item.name).parent.joinpath(item.linkname).resolve()
                assert str(target).startswith(str(tree) + '/'), (item.name, item.linkname)
        archive.extractall(tree)

def load(name):
    return json.loads((root / (name + '.json')).read_text(encoding='utf-8'))

def patch(path, old, new, occurrences=1):
    text = path.read_text(encoding='utf-8')
    assert text.count(old) == occurrences, (path, text.count(old))
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

def reject(name, command, expected_error):
    run(name, command, expected=1)
    observed = load(name)
    assert expected_error in observed.get('error', ''), observed
    report['mutations'].append(dict(name=name, status='PASS', rejected_for=observed['error']))

try:
    assert run('revision', ['git', 'rev-parse', candidate], cwd=repo).strip() == candidate
    extract(['scripts', 'workbench', '.gitignore', '.project-map', 'findings', '.grilling', 'CONTEXT.md', 'intent.md', 'AGENTS.md', 'README.md', 'acceptance/entry/a2a_gates.py'])
    shutil.copytree(repo / 'workbench/node_modules', tree / 'workbench/node_modules', symlinks=False)
    run('private-init', ['git', '-c', 'core.hooksPath=/dev/null', 'init', str(tree)], cwd=root)
    # archive 冻结文件；私有 Git 仅只读借用对象以核对完整历史，不创建符号链接。
    # 不使用 shallow 历史，避免地图漏判 stale；所有 refs/index 仅写本副本。
    objects = run('source-object-path', ['git', 'rev-parse', '--path-format=absolute', '--git-path', 'objects'], cwd=repo).strip()
    (tree / '.git/objects/info/alternates').write_text(objects + '\n', encoding='utf-8')
    run('private-head', ['git', 'update-ref', 'HEAD', candidate])
    run('private-index', ['git', 'read-tree', candidate])
    run('map-status', ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', tree])
    report['checks'].append('完整候选的地图检查：0 问题、0 stale')
    # 独立给定身份、任务标题与状态预期；不从生产 helper 计算答案。
    oracle = root / 'independent.mjs'
    oracle.write_text(r'''
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
const [tree, projection, output] = process.argv.slice(2);
const {OrchestrationStore} = await import(pathToFileURL(join(tree,'workbench/src/store.ts')));
const {sidebarSnapshot,aggregate} = await import(pathToFileURL(projection));
const root=mkdtempSync('/private/tmp/t109-review02-oracle-'), store=new OrchestrationStore(root);
const report={status:'INCOMPLETE',root,checks:[]};
try {
 store.db.exec('CREATE TABLE relay_requests(key TEXT,launch TEXT,input TEXT);CREATE TABLE relay_results(key TEXT,data TEXT);CREATE TABLE tasks(id TEXT,data TEXT)');
 const task='T-sentinel-563';
 store.db.prepare('INSERT INTO tasks VALUES (?,?)').run(task,JSON.stringify({task_id:task,project_id:'p-new-41',title:'执行主控派发的 worker'}));
 const seed=(id,role,preset,parent,project='p-new-41')=>store.launch({id,role,preset,parent_launch:parent,project,task,thread:id,attempt:'a83',cli_version:'codex-cli sentinel'});
 seed('i-839','controller','ideation',null);seed('e-173','controller','executor','i-839');
 seed('w-912','worker',null,'e-173');seed('r-531','reviewer',null,'e-173');seed('m-254','monitor',null,'e-173');
 seed('old-733','worker',null,undefined);seed('lost-104','worker',null,'absent-202');seed('alien-198','worker',null,'e-173','other-project');
 const gates={listProjects:()=>[{project_id:'p-new-41'}],listTasks:()=>store.db.prepare('SELECT data FROM tasks').all().map(r=>JSON.parse(r.data)),call:async()=>({ok:true,task:{repo:root}})};
 const panes={status:id=>({lifecycle:'running',state:id==='w-912'?'idle':'busy'})};
 const saved=()=>JSON.parse(execFileSync('python3',['-B',join(tree,'workbench/tests/t107_persistence.py'),root],{encoding:'utf8'}));
 const before=saved();let result;
 await assert.doesNotReject(async()=>{result=await sidebarSnapshot(gates,store,panes)},'缺失父 launch 和旧会话不得导致读取崩溃');
 const by=Object.fromEntries(result.agents.map(a=>[a.id,a]));
 assert.equal(by['e-173'].parent,'i-839');
 for(const id of ['w-912','r-531','m-254']) assert.equal(by[id].parent,'e-173');
 for(const id of ['old-733','lost-104','alien-198']) assert.equal(by[id].parent,null,'诱导标题、缺父项和跨项目不得推断归属');
 assert.equal(by['i-839'].descendants.count,4);assert.equal(by['e-173'].descendants.count,3);
 assert.equal(by['e-173'].descendants.state,'unknown');
 assert.deepEqual(by['e-173'].descendants.counts,[{state:'idle',label:'空闲',count:1},{state:'unknown',label:'未知',count:2}]);
 assert.equal(aggregate(['idle','unknown']),'unknown');assert.equal(aggregate(['running','unknown']),'running');
 assert.equal(aggregate(['running','waiting_controller_answer','waiting_user_answer']),'waiting_user_answer');
 assert.deepEqual(saved(),before,'侧栏不得改变表、schema 或 trace');
 report.status='PASS';report.checks=['给定事实三级关系','标题诱饵及未归属','孙代计数','未知不上调','等待用户优先','全持久化零写入'];
}catch(e){report.error=String(e);report.stack=e.stack}finally{store.close()}
writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;
''', encoding='utf-8')
    oracle_command = lambda name, projection: ['node', oracle, tree, projection, root / (name + '.json')]
    run('independent-good', oracle_command('independent-good', tree / 'workbench/src/sidebar.ts'))
    run('hierarchy-good', ['node', 'workbench/tests/test_t109_hierarchy.mjs', root / 'hierarchy-good.json'])
    run('dispatch-good', ['python3', 'workbench/tests/test_t109_dispatch.py', '--summary', root / 'dispatch-good.json'])
    run('keyboard-good', ['node', 'workbench/tests/test_t109_keyboard_entry.mjs', root / 'keyboard-good.json'])
    run('ipc-good', ['node', '--experimental-vm-modules', 'workbench/tests/test_t091_pane_ipc.mjs', root / 'ipc-good.json', '--source', tree, '--contract', 'sidebar'])
    run('t107-projection-good', ['node', 'workbench/tests/test_t107_sidebar.mjs', root / 't107-projection-good.json'])
    report['checks'].append('候选先通过独立 oracle、正式层级、真实 Python 命令、键盘驱动和 IPC 合同')
    for name in ('title', 'missing'):
        target = tree / 'workbench' / ('review02-mutant-' + name)
        shutil.copytree(tree / 'workbench/src', target)
        if name == 'title':
            old = "    if (typeof record.parent_launch === 'string') senders.add(record.parent_launch);"
            new = old + "\n    else if (record.role === 'worker' && gates.listTasks(record.project).find(task => task.task_id === record.task)?.title?.includes('执行主控')) senders.add(launches.find(row => row.preset === 'executor').id);"
            patch(target / 'sidebar.ts', old, new)
            reject('mutant-title-formal', ['node', 'workbench/tests/test_t109_hierarchy.mjs', root / 'mutant-title-formal.json', target / 'sidebar.ts'],
                   'Task titles must not supply parent launch facts for legacy sessions')
            run('mutant-title-independent', oracle_command('mutant-title-independent', target / 'sidebar.ts'), expected=1)
            assert '诱导标题、缺父项和跨项目不得推断归属' in load('mutant-title-independent').get('error','')
        else:
            patch(target / 'sidebar.ts', 'const allowed = parent?.project === agent.project', 'const allowed = parent.project === agent.project')
            reject('mutant-missing', oracle_command('mutant-missing', target / 'sidebar.ts'), '缺失父 launch 和旧会话不得导致读取崩溃')
    history = root / 'mutant-history'
    shutil.copytree(tree / 'scripts', history / 'scripts', symlinks=False)
    run('history-init', ['git', '-c', 'core.hooksPath=/dev/null', 'init', str(history)], cwd=root)
    run('history-fetch', ['git', 'fetch', '--depth=1', '--no-tags', str(repo), candidate], cwd=history)
    run('history-head', ['git', 'update-ref', 'HEAD', candidate], cwd=history)
    old = '        append_record(logfile, row)'
    new = old + "\n        (root / 'records/launches.jsonl').write_bytes((root / 'records/launches.jsonl').read_bytes().replace(b'launch-sentinel-parent', b'launch-rewritten-wrong'))"
    patch(history / 'scripts/dispatch', old, new, occurrences=2)
    reject('mutant-history', ['python3', 'workbench/tests/test_t109_dispatch.py', '--source', history, '--summary', root / 'mutant-history.json'],
           'Dispatch must not rewrite launch history')
    report['checks'].append('三个单处错误实现均由合同业务断言拒绝；F1 原变异已被正式验收拒绝')
    run('readonly-good', ['node', '--experimental-vm-modules', 'workbench/tests/test_t107_daemon_readonly.mjs', root / 'readonly-good.json', tree, 'readonly'])
    assert load('readonly-good')['cleanup_complete']
    if os.environ.get('T109_REVIEW_LOCAL_ONLY') == '1':
        report['not_run'] = ['真实 CLI/PTY/Electron 与 Tab 导航']
    else:
        assert not str(dist).startswith('/Volumes/') and (dist / 'version').read_text().strip() == '43.4.1'
        assert (dist / 'Electron.app/Contents/MacOS/Electron').is_file()
        driver = tree / 'workbench/tests/t107_sidebar_driver.mjs'
        marker = "          value = await window.webContents.executeJavaScript(`(()=>{\n            const n=[...document.querySelectorAll('button[data-agent-toggle]')]"
        tab = """          if (request.command === 'toggle-keyboard') {
            await window.webContents.executeJavaScript('document.activeElement?.blur()');
            let reached = false;
            for (let step = 0; step < 160; step++) {
              window.webContents.sendInputEvent({type:'keyDown',keyCode:'Tab'});
              window.webContents.sendInputEvent({type:'keyUp',keyCode:'Tab'});
              await new Promise(resolve => setTimeout(resolve, 20));
              const target = await window.webContents.executeJavaScript('document.activeElement?.dataset.agentToggle');
              if (target === request.target) { reached = true; log({stage:'review02-native-tab',target,steps:step+1}); break; }
            }
            if (!reached) throw new Error('Native Tab traversal did not reach the product disclosure');
          }
"""
        patch(driver, marker, tab + marker)
        run('product-unchanged', ['git', 'diff', '--exit-code', candidate, '--', 'scripts', 'workbench/src', 'workbench/app'])
        run('electron-tab-good', ['python3', 'workbench/tests/run_t109_hierarchy.py', '--source', tree, '--electron-dist', dist,
                                 '--summary', root / 'electron-tab-good.json'], timeout=900)
        value = load('electron-tab-good')
        assert value['status'] == 'PASS' and value['title_invariance']['status'] == 'PASS'
        assert value['source_head'] == candidate and value['source_changes'] == [' M workbench/tests/t107_sidebar_driver.mjs'], value
        assert len(value['checks']) == 4 and value['cleanup_complete']
        report['checks'].append('真实 daemon 零写入；冻结产品的真实派发/PTY/Electron、标题不变性和 Tab/Enter 全场景')
        report['status'] = 'PASS'
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
finally:
    # 不覆盖任何前轮现场；本次摘要与原始命令输出保留在独立目录。
    (root / 'review-outside-02.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('本轮摘要：' + str(root / 'review-outside-02.json'))
sys.exit(0 if report['status'] == 'PASS' else 1)
PYTHON
