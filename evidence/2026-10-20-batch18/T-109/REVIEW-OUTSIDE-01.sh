#!/bin/zsh
# T-109 第一轮独立审查：沙箱外复跑；只写新建的 /tmp 目录，不截图、不调用模型。
# 已知 F1 尚在，跑完仍输出 NO_GO；此命令不修复候选。
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
candidate = '0034e35ada8242c857156794c1f4996c44b9225c'
baseline = '6411bdff8482ba47da207efa6a295a12666222aa'
root = Path(tempfile.mkdtemp(prefix='t109-independent-outside01-', dir='/private/tmp')).resolve()
tree = root / 'candidate'
env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
    env.pop(key, None)
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
report = dict(status='INCOMPLETE', candidate=candidate, baseline=baseline, model_calls=0, root=str(root), checks=[], commands=[])

def run(name, argv, cwd=tree, expected=0, timeout=180):
    value = subprocess.run([str(item) for item in argv], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    (root / (name + '.stdout')).write_text(value.stdout, encoding='utf-8')
    (root / (name + '.stderr')).write_text(value.stderr, encoding='utf-8')
    report['commands'].append(dict(name=name, argv=list(map(str, argv)), cwd=str(cwd), exit=value.returncode))
    assert value.returncode == expected, (name, value.returncode, value.stdout[-2500:], value.stderr[-1500:])
    return value.stdout

def mutation(name, path, old, new, command, expected_error, first_only=False):
    text = path.read_text(encoding='utf-8')
    assert text.count(old) == (2 if first_only else 1), name
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    run(name, command, expected=1)
    value = json.loads((root / (name + '.json')).read_text(encoding='utf-8'))
    assert expected_error in value.get('error', ''), (name, value)
    report['checks'].append(dict(name=name, status='PASS', rejected_for=value['error']))

try:
    assert run('revision', ['git', 'rev-parse', candidate], cwd=repo).strip() == candidate
    assert not str(dist).startswith('/Volumes/') and (dist / 'version').read_text().strip() == '43.4.1'
    assert (dist / 'Electron.app/Contents/MacOS/Electron').is_file()
    # git archive 的既有 hook 相对链接只在本副本内解析；不创建跨副本链接。
    raw = subprocess.check_output(['git', 'archive', candidate, 'scripts', 'workbench', '.gitignore'], cwd=repo, env=env)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        members = archive.getmembers()
        for item in members:
            assert not item.name.startswith('/') and '..' not in Path(item.name).parts
            if item.issym():
                resolved = (tree / item.name).parent.joinpath(item.linkname).resolve()
                assert str(resolved).startswith(str(tree) + '/'), (item.name, item.linkname)
        archive.extractall(tree)
    shutil.copytree(repo / 'workbench/node_modules', tree / 'workbench/node_modules', symlinks=False)
    # 只给一次性副本补读取版本所需的 Git 元数据；无 worktree、commit、checkout、reset、stash。
    run('private-init', ['git', '-c', 'core.hooksPath=/dev/null', 'init', str(tree)])
    run('private-fetch', ['git', 'fetch', '--depth=1', '--no-tags', str(repo), candidate, baseline])
    run('private-head', ['git', 'update-ref', 'HEAD', candidate])
    run('private-index', ['git', 'read-tree', candidate])
    oracle = root / 'independent.mjs'
    oracle.write_text("import assert from 'node:assert/strict';\nimport { mkdtempSync,mkdirSync,writeFileSync } from 'node:fs';\nimport { join } from 'node:path';\nimport { pathToFileURL } from 'node:url';\nimport { execFileSync } from 'node:child_process';\nconst [tree,projection,output]=process.argv.slice(2);\nconst {OrchestrationStore}=await import(pathToFileURL(join(tree,'workbench/src/store.ts')));\nconst {sidebarSnapshot,aggregate}=await import(pathToFileURL(projection));\nconst root=mkdtempSync('/private/tmp/t109-review-oracle-');const store=new OrchestrationStore(root);\nconst report={status:'INCOMPLETE',checks:[],root};\ntry {\nstore.db.exec('CREATE TABLE relay_requests (key TEXT,launch TEXT,input TEXT);CREATE TABLE relay_results (key TEXT,data TEXT);');\nconst seed=(id,role,preset,parent,title)=>store.launch({id,role,preset,parent_launch:parent,title,project:'sentinel-project',task:'T-random-719',thread:id+'-thread',attempt:'a19',cli_version:'codex-cli 0.163.0'});\nseed('idea-719','controller','ideation',null,'worker');\nseed('exec-247','controller','executor','idea-719','unrelated title');\nseed('child-803','worker',null,'exec-247','构思主控');\nseed('old-627','worker',null,undefined,'执行主控派发的 worker');\nseed('dangling-511','worker',null,'absent-932','执行主控派发的 worker');\nconst saved=()=>JSON.parse(execFileSync('python3',['-B',join(tree,'workbench/tests/t107_persistence.py'),root],{encoding:'utf8'}));\nconst before=saved();let result;\nawait assert.doesNotReject(async()=>{result=await sidebarSnapshot({listProjects:()=>[{project_id:'sentinel-project'}],listTasks:()=>[{project_id:'sentinel-project',task_id:'T-random-719',title:'执行主控派发的 worker'}],call:async()=>({ok:true,task:{repo:root}})},store,{status:()=>({lifecycle:'running',state:'busy'})});},'旧记录及缺失父 launch 必须可读取且不崩溃');\nconst by=Object.fromEntries(result.agents.map(a=>[a.id,a]));\nassert.equal(by['exec-247'].parent,'idea-719');assert.equal(by['child-803'].parent,'exec-247');\nassert.equal(by['old-627'].parent,null,'标题中的主控名称不能成为父 launch 事实');\nassert.equal(by['dangling-511'].parent,null,'不存在的父 launch 必须未归属');\nassert.ok(result.agents.every(a=>a.state==='unknown'),'没有可识别信号必须保持未知');\nassert.equal(by['idea-719'].descendants.count,2);assert.equal(by['idea-719'].descendants.state,'unknown');\nassert.equal(aggregate(['idle','unknown']),'unknown');\nassert.equal(aggregate(['running','waiting_controller_answer','waiting_user_answer']),'waiting_user_answer');\nassert.deepEqual(saved(),before,'投影不得修改任一表、schema 或 trace');\nreport.status='PASS';report.checks=['显式三级关系','标题诱饵和缺父项仍未归属','未知状态不上调','后代汇总和等待用户优先级','全表/schema/trace 零写入'];\n}catch(e){report.error=String(e);report.stack=e.stack;}finally{store.close();}\nwriteFileSync(output,JSON.stringify(report,null,2)+'\\n',{flag:'wx'});console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;\n", encoding='utf-8')
    oracle_command = lambda name, projection: ['node', oracle, tree, projection, root / (name + '.json')]
    run('independent-good', oracle_command('independent-good', tree / 'workbench/src/sidebar.ts'))
    run('hierarchy-good', ['node', 'workbench/tests/test_t109_hierarchy.mjs', root / 'hierarchy-good.json'])
    run('dispatch-good', ['python3', 'workbench/tests/test_t109_dispatch.py', '--summary', root / 'dispatch-good.json'])
    run('keyboard-good', ['node', 'workbench/tests/test_t109_keyboard_entry.mjs', root / 'keyboard-good.json'], timeout=60)
    run('ipc-good', ['node', '--experimental-vm-modules', tree / 'workbench/tests/test_t091_pane_ipc.mjs', root / 'ipc-good.json', '--source', tree, '--contract', 'sidebar'], cwd=repo)
    run('readonly-good', ['node', '--experimental-vm-modules', 'workbench/tests/test_t107_daemon_readonly.mjs', root / 'readonly-good.json', tree, 'readonly'])
    report['checks'].append(dict(name='候选先通过独立事实 oracle、层级、派发、键盘、IPC 和实际 daemon 只读检查', status='PASS'))
    for name in ('title', 'missing'):
        target = tree / 'workbench' / ('review-mutant-' + name)
        shutil.copytree(tree / 'workbench/src', target)
        if name == 'title':
            old = "    if (typeof record.parent_launch === 'string') senders.add(record.parent_launch);"
            new = old + "\n    else if (record.role === 'worker' && gates.listTasks(record.project).find(task => task.task_id === record.task)?.title?.includes('执行主控')) senders.add(launches.find(row => row.preset === 'executor').id);"
            expected = '标题中的主控名称不能成为父 launch 事实'
        else:
            old, new = 'const allowed = parent?.project === agent.project', 'const allowed = parent.project === agent.project'
            expected = '旧记录及缺失父 launch 必须可读取且不崩溃'
        mutation('mutant-' + name, target / 'sidebar.ts', old, new,
                 oracle_command('mutant-' + name, target / 'sidebar.ts'), expected)
        if name == 'title':
            run('escaped-title-contract', ['node', 'workbench/tests/test_t109_hierarchy.mjs', root / 'escaped-title-contract.json', target / 'sidebar.ts'])
            report['findings'] = ['F1：按已保存任务标题推断父项的错误实现仍通过候选原层级合同；需把标题诱饵纳入正式验收。']
    history = root / 'mutant-history'
    shutil.copytree(tree / 'scripts', history / 'scripts', symlinks=False)
    run('history-init', ['git', '-c', 'core.hooksPath=/dev/null', 'init', str(history)], cwd=root)
    run('history-fetch', ['git', '-C', history, 'fetch', '--depth=1', '--no-tags', tree, candidate], cwd=root)
    run('history-head', ['git', '-C', history, 'update-ref', 'HEAD', candidate], cwd=root)
    old = '        append_record(logfile, row)'
    new = old + "\n        (root / 'records/launches.jsonl').write_bytes((root / 'records/launches.jsonl').read_bytes().replace(b'launch-sentinel-parent', b'launch-rewritten-wrong'))"
    mutation('mutant-history', history / 'scripts/dispatch', old, new,
             ['python3', 'workbench/tests/test_t109_dispatch.py', '--source', history, '--summary', root / 'mutant-history.json'],
             'Dispatch must not rewrite launch history', first_only=True)
    # 独立补强：先通过真实 Tab 逐项导航到折叠按钮，再沿候选的 Enter 路径激活。
    # 不修改按钮、tabIndex、产品代码或展开断言；只修改本副本内的测试驱动。
    driver = tree / 'workbench/tests/t107_sidebar_driver.mjs'
    original = driver.read_text(encoding='utf-8')
    marker = "          value = await window.webContents.executeJavaScript(`(()=>{\n            const n=[...document.querySelectorAll('button[data-agent-toggle]')]"
    assert original.count(marker) == 1
    tab = """          if (request.command === 'toggle-keyboard') {
            await window.webContents.executeJavaScript('document.activeElement?.blur()');
            let reached = false;
            for (let step = 0; step < 160; step++) {
              window.webContents.sendInputEvent({type:'keyDown',keyCode:'Tab'});
              window.webContents.sendInputEvent({type:'keyUp',keyCode:'Tab'});
              await new Promise(resolve => setTimeout(resolve, 20));
              const target = await window.webContents.executeJavaScript('document.activeElement?.dataset.agentToggle');
              if (target === request.target) { reached = true; log({stage:'independent-native-tab',target,steps:step+1}); break; }
            }
            if (!reached) throw new Error('Independent Tab traversal did not reach the product disclosure');
          }
"""
    driver.write_text(original.replace(marker, tab + marker), encoding='utf-8')
    run('product-source-unchanged', ['git', 'diff', '--exit-code', candidate, '--', 'workbench/src', 'workbench/app', 'scripts'])
    run('electron-tab-good', ['python3', 'workbench/tests/run_t109_hierarchy.py', '--source', tree, '--electron-dist', dist,
                             '--summary', root / 'electron-tab-good.json'], timeout=900)
    value = json.loads((root / 'electron-tab-good.json').read_text(encoding='utf-8'))
    assert value['status'] == 'PASS' and value['source_head'] == candidate and value['source_changes'] == [' M workbench/tests/t107_sidebar_driver.mjs'], value
    assert len(value['checks']) == 4
    report['checks'].append(dict(name='真实 CLI/PTY/Electron 全场景，真实 Tab 到折叠按钮后 Enter 展开', status='PASS',
                                 source_binding='产品源码为冻结候选，测试驱动仅增加 Tab 导航，完整补丁在本脚本'))
    report['status'] = 'NO_GO' if report.get('findings') else 'PASS'
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
finally:
    # 原始记录和失败现场全保留在本次 /tmp 目录，后续按项目归档规则由主控处理。
    (root / 'review-outside-01.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('本轮摘要：' + str(root / 'review-outside-01.json'))
sys.exit(0 if report['status'] == 'PASS' else 1)

PYTHON
