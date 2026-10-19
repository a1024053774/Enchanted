#!/bin/bash
# T-106 第一轮独立审查：主控在沙箱外运行，不调用模型，不操作用户数据。
# 固定审查候选；所有产物写入新的 /private/tmp 目录，不改候选、不覆盖证据。
# 原生选目录已有 form-electron-01.json 的真实证明。本探针只为省去重复的人手选择，
# 在观察 driver 中替换主进程 dialog 的结果；不把它算作原生对话框的证明。
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
revision = '24cacef60f9e88103213c0bb93eecb0cb5c41cf3'
root = Path(tempfile.mkdtemp(prefix='t106-review-outside01-', dir='/private/tmp')).resolve()
tree = root / 'candidate'; tree.mkdir()
report = dict(status='INCOMPLETE', candidate=revision, model_turns=0, root=str(root),
              scope='真实 Electron/main/preload/daemon/门禁/SQLite；观察 driver 固定主进程目录对话框结果，非原生选择证明',
              commands=[], checks=[], observed={})
windows = []
state = root / 'state'
daemon_pid = None
built = None
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'OPENAI_', 'ANTHROPIC_'))
       and k not in ('NODE_OPTIONS', 'NODE_PATH', 'ELECTRON_RUN_AS_NODE')}
home = root / 'home'; home.mkdir()
env.update(HOME=str(home), TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp',
           A2A_OPERATOR_CREDENTIAL=str(root / 'operator.json'))

def run(argv, cwd=tree):
    argv = list(map(str, argv))
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    report['commands'].append(dict(argv=argv, exit=result.returncode,
                                   stdout=result.stdout[-10000:], stderr=result.stderr[-4000:]))
    assert result.returncode == 0, report['commands'][-1]
    return result.stdout

def gate(command, *fields):
    return json.loads(run(['node', tree / 'workbench/src/gates/cli.ts', '--state', state, command, *fields]))

def until(read, message, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = read()
        if value:
            return value
        time.sleep(.1)
    raise AssertionError(message)

def inventory():
    with sqlite3.connect(state / 'state.sqlite3') as db:
        return {name: db.execute('SELECT count(*) FROM ' + name).fetchone()[0]
                for name in ['tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'launch_records']}

try:
    archive = root / 'candidate.tar'
    with archive.open('xb') as handle:
        subprocess.run(['git', 'archive', revision, 'workbench'], cwd=checkout, stdout=handle, check=True)
    subprocess.run(['/usr/bin/tar', '-xf', str(archive), '-C', str(tree)], check=True)
    dependencies = Path(os.environ.get('T106_REVIEW_DEPENDENCIES',
                                       '/Users/luckye/Documents/Code/a2a/workbench/node_modules')).resolve(strict=True)
    runtime = Path(os.environ.get('T106_ELECTRON_DIST', str(dependencies / 'electron/dist'))).resolve(strict=True)
    assert not runtime.is_relative_to('/Volumes')
    assert (runtime / 'version').read_text(encoding='utf-8').strip() == '43.4.1'
    shutil.copytree(dependencies, tree / 'workbench/node_modules', symlinks=True)
    helper = tree / 'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
    assert helper.is_file(); helper.chmod(0o755)
    env['ELECTRON_OVERRIDE_DIST_PATH'] = str(runtime)
    repo = root / 'repo'
    run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
    (repo / 'tests').mkdir()
    marker = root / 'completion-was-run'
    (repo / 'tests/criterion.py').write_text(
        'from pathlib import Path\nPath(' + repr(str(marker)) + ").write_text('ran', encoding='utf-8')\n", encoding='utf-8')
    run(['git', '-C', repo, 'add', '.'])
    run(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=T106 reviewer fixture',
         '-c', 'user.email=review@example.invalid', 'commit', '-m', '独立保存结果故障夹具'])
    env['T106_REVIEW_REPOSITORY'] = str(repo)
    # 只改观察 driver：产品 main、preload、renderer、daemon 与门禁保持 archive 原文。
    driver = root / 'observe.mjs'
    original = (tree / 'workbench/tests/t106_creation_driver.mjs').read_text(encoding='utf-8')
    assert original.count("import { app } from 'electron';") == 1
    original = original.replace("import { app } from 'electron';",
        "import { app, dialog } from 'electron';\n"
        "dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [process.env.T106_REVIEW_REPOSITORY] });")
    driver.write_text(original, encoding='utf-8')
    sys.path.insert(0, str(tree / 'workbench/tests'))
    from run_t103_picker import Window
    started = gate('daemon_start'); assert started['ok']
    daemon_pid = started['pid']
    until(lambda: not gate('pane_layout').get('recovering'), '后台恢复未结束')
    manifest = json.loads(run(['node', tree / 'workbench/app/build.mjs', '--slot', 't106-review-' + uuid.uuid4().hex[:12]]).splitlines()[-1])
    built = Path(manifest['out'])
    win = Window(tree, driver, built, state, root / 'ui', root / 'window', env, windows,
                 dict(executable=str(runtime / 'Electron.app/Contents/MacOS/Electron'),
                      dist=str(runtime), version='43.4.1'), through_start=False)
    win.wait(lambda view: view['busy'] == 'false')
    win.call('click', text='新建项目与任务'); win.wait(lambda view: view['form'])
    win.call('click', text='选择仓库目录…')
    view = win.wait(lambda view: view.get('repo') == str(repo) and view['fields'].get('card'))
    defaults = json.loads(view['fields']['card'])
    assert defaults['paths'] == dict(allow=['.'], deny=['.git/']) and defaults['oracle_paths'] == ['tests/']
    assert defaults['executor'] == dict(cli='Codex', model='gpt-6.1-sol', effort='xhigh')
    assert defaults['base_commit'] is None and defaults['writer'] is None
    assert all(count == 0 for count in inventory().values())
    title_marker = root / 'title-was-executed'
    title = '标题$(touch ' + str(title_marker) + ') <审查>'
    goal = '目标不是路径：../../escape；$(touch ' + str(title_marker) + ')'
    for field, value in dict(project='review-project', title=title, goal=goal).items():
        win.call('fill', field=field, value=value)
    view = win.call('inspect')
    assert not view['formValid'] and any(item['field'] == 'command' for item in view['invalidFields'])
    report['checks'].append('只填名字和目标仍缺完成条件命令，与裁定节一致')
    win.call('fill', field='command', value=json.dumps(['python3', 'tests/criterion.py']))
    missing = dict(defaults); missing.pop('non_goals')
    win.call('fill', field='card', value=json.dumps(missing, ensure_ascii=False)); win.call('submit')
    win.wait(lambda view: any('invalid_task_card' in item and 'card' in item for item in view['alerts']))
    assert all(count == 0 for count in inventory().values())
    report['checks'].append('真实格式拒收可见且保存前五表计数均为零')
    win.call('fill', field='card', value=json.dumps(defaults, ensure_ascii=False))
    # 唯一故障注入：只阻断 card_save 的结果事件，不阻断门禁事务或拒收事件。
    with sqlite3.connect(state / 'state.sqlite3') as db:
        db.execute("""CREATE TRIGGER review_fail_card_save_result BEFORE INSERT ON orchestration_events
        WHEN NEW.type='request_result' AND json_extract(NEW.data,'$.command')='card_save'
        BEGIN SELECT RAISE(ABORT,'review: failure after card_save commit'); END""")
    win.call('submit')
    def settled_error():
        value = win.call('inspect')
        if not any('orchestration_failed' in item for item in value['alerts']):
            return None
        return value if any(item['text'] == '确认并注册任务' for item in value['buttons']) else None
    view = until(settled_error, '没有显示保存结果故障')
    counts = inventory()
    assert counts == dict(tasks=0, task_card_versions=1, task_card_snapshots=0, attempts=0, launch_records=0)
    assert not marker.exists() and not title_marker.exists()
    with sqlite3.connect(state / 'state.sqlite3') as db:
        saved = json.loads(db.execute('SELECT data FROM task_card_versions').fetchone()[0])
    assert saved['goal'] == goal
    retained_button = any(item['text'] == '关闭表单（保留已保存记录）' for item in view['buttons'])
    submit_disabled = any(item['text'] == '确认并注册任务' and item['disabled'] for item in view['buttons'])
    warning = '任务卡可能已经保存' in view['text']
    report['observed'] = dict(counts=counts, alerts=view['alerts'], buttons=view['buttons'],
                              persisted_warning=warning, submit_disabled=submit_disabled,
                              retained_close_button=retained_button, completion_ran=marker.exists(),
                              title_injection_ran=title_marker.exists(), saved_goal=saved['goal'])
    win.call('click', text='关闭表单（保留已保存记录）' if retained_button else '取消')
    win.wait(lambda value: not value['form'])
    report['observed']['after_close'] = inventory()
    assert inventory() == counts
    report['checks'].append('实际门禁已持久化卡版本，后台随后返回错误；关闭后保留事实记录')
    report['status'] = 'PASS' if retained_button and submit_disabled and warning else 'NO_GO'
    if report['status'] == 'NO_GO':
        report['finding'] = '保存已生效却仍显示取消、未提示保存未知且允许重试；main.ts:192 将一般错误误当作未保存'
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
finally:
    try:
        for win in windows:
            win.close()
        if daemon_pid is not None:
            assert gate('daemon_stop')['ok']
            until(lambda: not (state / 'control.sock').exists(), '自有后台 socket 未退出')
            def process_absent():
                result = subprocess.run(['/bin/ps', '-p', str(daemon_pid), '-o', 'stat='], capture_output=True, text=True)
                assert result.returncode in (0, 1) and not result.stderr
                return not result.stdout.strip() or result.stdout.strip().startswith('Z')
            until(process_absent, '自有后台进程未退出')
        report['cleanup_complete'] = True
        # 进程退出后清理构建、依赖和缓存；SQLite 与失败原件保留在本次临时目录。
        shutil.rmtree(tree / 'workbench/node_modules', ignore_errors=False) if (tree / 'workbench/node_modules').exists() else None
        if built is not None:
            shutil.rmtree(built.parent)
    except Exception as error:
        report.update(status='INCOMPLETE', cleanup_complete=False, cleanup_error=repr(error))
    summary = root / 'summary.json'
    with summary.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(summary)), ensure_ascii=False), flush=True)
sys.exit(0 if report['status'] == 'PASS' else 1)
PY
