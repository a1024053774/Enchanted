#!/bin/bash
# 第二轮独立审查补测；由执行主控在沙箱外运行。固定候选，不覆盖旧证据。
# 观察 driver 固定主进程目录选择结果，避免手工操作；不声称新的原生对话框证明。
# 无模型、截图、安装、全局配置或用户数据操作。原件仅写新的 /private/tmp 目录。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t106
python3 - <<'PY'
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import uuid

sys.dont_write_bytecode = True
checkout = Path.cwd()
revision = '5036a8dc32de265dc27499028f0b938db3d1a15a'
previous = '24cacef60f9e88103213c0bb93eecb0cb5c41cf3'
root = Path(tempfile.mkdtemp(prefix='t106-review-outside02-', dir='/private/tmp')).resolve()
candidate, baseline = root / 'candidate', root / 'baseline'
report = dict(status='INCOMPLETE', candidate=revision, previous=previous, root=str(root),
              model_turns=0, commands=[], checks=[],
              scope='真实 Electron/main/preload/daemon/门禁/SQLite；固定目录结果，不证明原生目录选择')
windows, daemons, builds = [], [], []
fault_started = False
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))
       and k not in ('NODE_OPTIONS', 'NODE_PATH', 'ELECTRON_RUN_AS_NODE')}
isolated_home = root / 'home'; isolated_home.mkdir()
env.update(HOME=str(isolated_home), TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp')

def run(argv, local_env=env):
    argv = list(map(str, argv))
    result = subprocess.run(argv, cwd=candidate, env=local_env, capture_output=True, text=True, timeout=180)
    report['commands'].append(dict(argv=argv, exit=result.returncode,
                                   stdout=result.stdout[-12000:], stderr=result.stderr[-4000:]))
    assert result.returncode == 0, report['commands'][-1]
    return result.stdout

def gate(state, local_env, command, *fields):
    return json.loads(run(['node', candidate / 'workbench/src/gates/cli.ts', '--state', state, command, *fields], local_env))

def until(read, message):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if read():
            return
        time.sleep(.1)
    raise AssertionError(message)

def inventory(state):
    with sqlite3.connect(state / 'state.sqlite3') as db:
        return {table: db.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                for table in ['tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'launch_records']}

def stop_owned():
    for win in windows:
        win.close()
    for state, local_env, pid in reversed(daemons):
        assert gate(state, local_env, 'daemon_stop')['ok']
        until(lambda: not (state / 'control.sock').exists(), '自有后台 socket 未退出')
        def absent():
            value = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True)
            assert value.returncode in (0, 1) and not value.stderr
            return not value.stdout.strip() or value.stdout.strip().startswith('Z')
        until(absent, '自有后台进程未退出')
    daemons.clear()

try:
    for tree, commit in [(candidate, revision), (baseline, previous)]:
        tree.mkdir()
        archive = root / (tree.name + '.tar')
        with archive.open('xb') as handle:
            subprocess.run(['git', 'archive', commit, 'workbench'], cwd=checkout, stdout=handle, check=True)
        subprocess.run(['/usr/bin/tar', '-xf', str(archive), '-C', str(tree)], check=True)
    dependencies = Path(os.environ.get('T106_REVIEW_DEPENDENCIES',
                                       '/Users/luckye/Documents/Code/a2a/workbench/node_modules')).resolve(strict=True)
    runtime = Path(os.environ.get('T106_ELECTRON_DIST', str(dependencies / 'electron/dist'))).resolve(strict=True)
    assert not runtime.is_relative_to('/Volumes') and (runtime / 'version').read_text(encoding='utf-8').strip() == '43.4.1'
    env['ELECTRON_OVERRIDE_DIST_PATH'] = str(runtime)
    for tree in [candidate, baseline]:
        shutil.copytree(dependencies, tree / 'workbench/node_modules', symlinks=True)
        (tree / 'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper').chmod(0o755)
    repo = root / 'repo'
    run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
    (repo / 'tests').mkdir()
    completion_marker, title_marker = root / 'completion-ran', root / 'title-ran'
    (repo / 'tests/check.py').write_text('from pathlib import Path\nPath(' + repr(str(completion_marker))
                                        + ").write_text('ran')\n", encoding='utf-8')
    run(['git', '-C', repo, 'add', '.'])
    run(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=T106 review fixture',
         '-c', 'user.email=review@example.invalid', 'commit', '-m', '独立表单默认值与拒收夹具'])
    state = root / 'state'; local_env = dict(env, A2A_OPERATOR_CREDENTIAL=str(root / 'operator.json'))
    started = gate(state, local_env, 'daemon_start'); assert started['ok']
    daemons.append((state, local_env, started['pid']))
    until(lambda: not gate(state, local_env, 'pane_layout').get('recovering'), '后台未就绪')
    driver = root / 'observe.mjs'
    code = (candidate / 'workbench/tests/t106_creation_driver.mjs').read_text(encoding='utf-8')
    before = "import { app } from 'electron';"; assert code.count(before) == 1
    driver.write_text(code.replace(before, "import { app, dialog } from 'electron';\n"
                                  + 'dialog.showOpenDialog=async()=>({canceled:false,filePaths:['
                                  + json.dumps(str(repo)) + ']});'), encoding='utf-8')
    sys.path.insert(0, str(candidate / 'workbench/tests'))
    from run_t103_picker import Window
    manifest = json.loads(run(['node', candidate / 'workbench/app/build.mjs', '--slot', 't106-review02-' + uuid.uuid4().hex[:8]]).splitlines()[-1])
    built = Path(manifest['out']); builds.append(built.parent)
    win = Window(candidate, driver, built, state, root / 'ui', root / 'window', local_env, windows,
                 dict(executable=str(runtime / 'Electron.app/Contents/MacOS/Electron'), dist=str(runtime), version='43.4.1'), through_start=False)
    win.wait(lambda view: view['busy'] == 'false')

    def form():
        win.call('click', text='新建项目与任务'); win.wait(lambda view: view['form'])
        win.call('click', text='选择仓库目录…')
        return win.wait(lambda view: view.get('repo') == str(repo) and view['fields'].get('card'))

    view = form(); defaults = json.loads(view['fields']['card'])
    assert defaults['paths'] == dict(allow=['.'], deny=['.git/']) and defaults['oracle_paths'] == ['tests/']
    assert defaults['executor'] == dict(cli='Codex', model='gpt-6.1-sol', effort='xhigh')
    assert defaults['base_commit'] is None and defaults['writer'] is None and defaults['source'] is None
    title = '标题$(touch ' + str(title_marker) + ') <独立审查>'
    goal = '目标 ../../escape $(touch ' + str(title_marker) + ')'
    project = 'review-' + uuid.uuid4().hex[:8]
    for field, value in dict(project=project, title=title, goal=goal).items():
        win.call('fill', field=field, value=value)
    view = win.call('inspect')
    assert not view['formValid'] and any(item['field'] == 'command' for item in view['invalidFields'])
    assert all(count == 0 for count in inventory(state).values())
    win.call('fill', field='command', value=json.dumps(['python3', 'tests/check.py']))
    missing = dict(defaults); missing.pop('non_goals')
    win.call('fill', field='card', value=json.dumps(missing, ensure_ascii=False)); win.call('submit')
    win.wait(lambda view: any('invalid_task_card' in alert and 'card' in alert for alert in view['alerts']))
    assert all(count == 0 for count in inventory(state).values())
    win.call('click', text='取消'); win.wait(lambda view: not view['form'])
    assert all(count == 0 for count in inventory(state).values())
    report['checks'].append('缺完成条件时不能提交；缺字段拒收原因可见；取消前后五表零增长')
    view = form(); defaults = json.loads(view['fields']['card'])
    for field, value in dict(project=project, title=title, goal=goal, command=json.dumps(['python3', 'tests/check.py'])).items():
        win.call('fill', field=field, value=value)
    expected = dict(defaults, goal=goal, completion_conditions=[dict(argv=[str(Path(shutil.which('python3', path=env['PATH'])).resolve()), 'tests/check.py'])])
    injected = win.call('bridge', operation='creationSubmit', input=dict(task=defaults['id'], project=project,
                        title=title, branch='refs/heads/main', card=json.dumps(expected), repo='/renderer/injected'))
    assert injected.get('rejected') and all(count == 0 for count in inventory(state).values())
    win.call('submit')
    view = win.wait(lambda view: not view['form'] and any(item['id'] == defaults['id'] for item in view['tasks']))
    record = gate(state, local_env, 'status', '--task', defaults['id'])['task']
    assert record['state'] == 'ready' and record['repo'] == str(repo) and record['project_id'] == project
    assert record['title'] == title and record['card'] == expected and project in view['projects']
    assert inventory(state) == dict(tasks=1, task_card_versions=1, task_card_snapshots=1, attempts=0, launch_records=0)
    assert not title_marker.exists() and not completion_marker.exists()
    report['checks'].append('保留默认卡即可注册；完整卡、标题与目标按外部输入保存；路径注入拒绝；命令与标题未执行')
    # required 不会拦住非空的空白标题；main 的 trim 检查已确定发生在所有门禁调用前。
    # 此类拒收必须允许修正或取消，不能因 IPC 抛错被 renderer 当成未知提交。
    form()
    for field, value in dict(project=project, title='   ', goal='只验证提交前拒收', command=json.dumps(['python3', 'tests/check.py'])).items():
        win.call('fill', field=field, value=value)
    view = win.wait(lambda view: view['fields'].get('title') == '   ' and view['fields'].get('command') == json.dumps(['python3', 'tests/check.py']))
    assert view['formValid']
    before = inventory(state)
    win.call('submit')
    view = win.wait(lambda view: any('Invalid creation fields' in alert for alert in view['alerts'])
                    and any(item['text'] == '确认并注册任务' for item in view['buttons']))
    assert inventory(state) == before
    editable = any(item['text'] == '取消' and not item['disabled'] for item in view['buttons'])
    report['preflight'] = dict(title='   ', counts=inventory(state), alerts=view['alerts'], buttons=view['buttons'], editable=editable)
    if not editable:
        report.update(status='NO_GO', finding='P2：确定提交前的标题拒收被 renderer 当成未知，不能取消或修正')
        raise AssertionError(report['finding'])
    win.call('click', text='取消'); win.wait(lambda view: not view['form'])
    assert inventory(state) == before
    report['checks'].append('空白标题在提交前拒收，仍可修正或取消且五表无增长')
    stop_owned()
    # 当前候选真实 GUI 五种提交后故障，并在旧候选重现 P1。与上面的独立正常/取消旅程分开保存。
    fault_summary = root / 'postcommit.json'
    fault_started = True
    run(['python3', candidate / 'workbench/tests/run_t106_postcommit_electron.py', '--source', candidate,
         '--baseline', baseline, '--electron-dist', runtime, '--summary', fault_summary])
    fault = json.loads(fault_summary.read_text(encoding='utf-8'))
    assert fault['status'] == 'PASS' and fault.get('cleanup_complete')
    report['fault_summary'] = str(fault_summary)
    report['checks'].append('旧候选 P1 红态，当前候选保存/注册提交后故障与未知时按钮状态通过')
    report['status'] = 'PASS'
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
finally:
    try:
        stop_owned()
        # 子 runner 无法确认清理时，保留其源码、依赖与现场，交主控处理，不自动终止未知进程。
        fault_summary = root / 'postcommit.json'
        if fault_summary.exists():
            assert json.loads(fault_summary.read_text(encoding='utf-8')).get('cleanup_complete'), '子 runner 清理未确认'
        elif fault_started:
            raise RuntimeError('子 runner 未产生清理收据，保留现场')
        for path in builds:
            shutil.rmtree(path)
        for tree in [candidate, baseline]:
            if (tree / 'workbench/node_modules').exists():
                shutil.rmtree(tree / 'workbench/node_modules')
        report['cleanup_complete'] = True
    except Exception as error:
        report.update(status='INCOMPLETE', cleanup_complete=False, cleanup_error=repr(error))
    summary = root / 'summary.json'
    with summary.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(summary)), ensure_ascii=False), flush=True)
sys.exit(0 if report['status'] == 'PASS' else 1)
PY
