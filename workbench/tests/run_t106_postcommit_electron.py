"""实际 Electron 与 SQLite 提交后故障；观察 driver 固定目录，不证明原生选择。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time
import traceback
import uuid
from run_t103_picker import Window


def main():
    parser = argparse.ArgumentParser()
    for key in ['source', 'baseline', 'electron-dist', 'summary']:
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    output = args.summary.resolve(); assert not output.exists(), '保留旧摘要，请换编号'
    root = Path(tempfile.mkdtemp(prefix='t106-postcommit-gui-', dir='/private/tmp')).resolve()
    home = root / 'home'; home.mkdir()
    runtime = args.electron_dist.resolve(strict=True)
    assert not runtime.is_relative_to('/Volumes') and (runtime / 'version').read_text(encoding='utf-8').strip() == '43.4.1'
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_', 'CLAUDE_', 'CODEX_', 'ANTHROPIC_', 'OPENAI_'))
           and k not in ('NODE_OPTIONS', 'NODE_PATH', 'ELECTRON_RUN_AS_NODE')}
    env.update(HOME=str(home), TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp', ELECTRON_OVERRIDE_DIST_PATH=str(runtime))
    report = dict(status='INCOMPLETE', model_turns=0, argv=list(map(str, __import__('sys').argv)), cases=[], commands=[],
                  scope='实际 Electron/main/preload/daemon/门禁/SQLite；观察 driver 固定主进程目录选择结果，无原生选择证明、无截图')
    windows, daemons, builds = [], [], []

    def run(argv, cwd=source, local_env=env):
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=local_env, capture_output=True, text=True, timeout=180)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=result.returncode, stdout=result.stdout[-8000:], stderr=result.stderr[-3000:]))
        assert result.returncode == 0, report['commands'][-1]
        return result.stdout

    def gate(tree, state, local_env, command):
        return json.loads(run(['node', tree / 'workbench/src/gates/cli.ts', '--state', state, command], local_env=local_env))

    def until(read, description):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            value = read()
            if value:
                return value
            time.sleep(.1)
        raise AssertionError(description)

    def inventory(state):
        with sqlite3.connect(state / 'state.sqlite3') as db:
            return {table: db.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                    for table in ['tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'launch_records']}

    def build(tree, label):
        data = json.loads(run(['node', tree / 'workbench/app/build.mjs', '--slot', 't106-postcommit-' + label + '-' + uuid.uuid4().hex[:8]]).splitlines()[-1])
        builds.append(Path(data['out']).parent); return Path(data['out'])

    try:
        repo = root / 'repo'
        run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
        (repo / 'tests').mkdir()
        marker = root / 'completion-was-run'
        (repo / 'tests/check.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ").write_text('ran')\n", encoding='utf-8')
        run(['git', '-C', repo, 'add', '.'])
        run(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=T106 fixture', '-c', 'user.email=t106@example.invalid', 'commit', '-m', 'Postcommit GUI fixture'])
        driver = root / 'observe.mjs'
        code = (source / 'workbench/tests/t106_creation_driver.mjs').read_text(encoding='utf-8')
        assert code.count("import { app } from 'electron';") == 1
        code = code.replace("import { app } from 'electron';", "import { app, dialog } from 'electron';\n"
                            + 'dialog.showOpenDialog=async()=>({canceled:false,filePaths:[' + json.dumps(str(repo)) + ']});')
        driver.write_text(code, encoding='utf-8')
        jobs = [(baseline, build(baseline, 'red'), 'save-result', True)]
        green = build(source, 'green')
        jobs += [(source, green, name, False) for name in ['save-result', 'save-event-failure', 'save-readback-failure', 'create-result', 'create-readback-failure']]
        for index, (tree, built, name, red) in enumerate(jobs):
            state = root / ('state-' + str(index))
            local_env = dict(env, A2A_OPERATOR_CREDENTIAL=str(root / ('operator-' + str(index) + '.json')))
            pid = gate(tree, state, local_env, 'daemon_start')['pid']
            daemons.append((tree, state, local_env, pid))
            until(lambda: not gate(tree, state, local_env, 'pane_layout').get('recovering'), '后台未就绪')
            win = Window(tree, driver, built, state, root / ('ui-' + str(index)), root / ('window-' + str(index)),
                         local_env, windows, dict(executable=str(runtime / 'Electron.app/Contents/MacOS/Electron'), dist=str(runtime), version='43.4.1'), through_start=False)
            win.wait(lambda view: view['busy'] == 'false')
            win.call('click', text='新建项目与任务'); win.wait(lambda view: view['form'])
            win.call('click', text='选择仓库目录…')
            view = win.wait(lambda view: view.get('repo') == str(repo) and view['fields'].get('card'))
            defaults = json.loads(view['fields']['card'])
            assert defaults['paths'] == dict(allow=['.'], deny=['.git/']) and defaults['oracle_paths'] == ['tests/']
            assert defaults['executor'] == dict(cli='Codex', model='gpt-6.1-sol', effort='xhigh')
            title = '结果核对<独立标题>-' + str(index) + '-' + uuid.uuid4().hex[:6]
            fields = dict(project='postcommit-project', title=title, goal='提交后结果事件失败 ' + name,
                          command=json.dumps(['python3', 'tests/check.py']))
            for field, value in fields.items():
                win.call('fill', field=field, value=value)
            view = win.wait(lambda view: all(view['fields'].get(k) == v for k, v in fields.items()))
            assert view['formValid'] and all(n == 0 for n in inventory(state).values())
            mutation = 'card_save' if name.startswith('save') else 'create'
            readback = 'card_show' if mutation == 'card_save' else 'status'
            condition = "NEW.type='request_result' AND json_extract(NEW.data,'$.command')='" + mutation + "'"
            if name == 'save-event-failure':
                condition += " OR NEW.type='request_rejected' AND json_extract(NEW.data,'$.input.command')='card_save'"
            if name.endswith('readback-failure'):
                condition += " OR NEW.type='request_received' AND json_extract(NEW.data,'$.input.command')='" + readback + "'"
            with sqlite3.connect(state / 'state.sqlite3') as db:
                db.execute("CREATE TRIGGER fail_after_commit BEFORE INSERT ON orchestration_events WHEN " + condition + " BEGIN SELECT RAISE(ABORT,'T106 postcommit fault'); END")
            win.call('submit')
            if name == 'create-result':
                view = win.wait(lambda view: not view['form'] and any(title in item['text'] for item in view['tasks']))
                assert view['projects'] == ['postcommit-project']
            else:
                error = 'event_write_failed' if name == 'save-event-failure' else 'orchestration_failed'
                view = win.wait(lambda view: any(error in alert for alert in view['alerts'])
                                and any(item['text'] == '确认并注册任务' for item in view['buttons']))
            counts = inventory(state)
            assert counts == dict(tasks=1 if mutation == 'create' else 0, task_card_versions=1,
                                  task_card_snapshots=1 if mutation == 'create' else 0, attempts=0, launch_records=0)
            assert not marker.exists()
            row = dict(name=name, known_bad=red, counts=counts, alerts=view['alerts'], buttons=view['buttons'])
            report['cases'].append(row)
            with sqlite3.connect(state / 'state.sqlite3') as db:
                saved = json.loads(db.execute('SELECT data FROM task_card_versions').fetchone()[0])
                assert saved['goal'] == fields['goal']
                if mutation == 'create':
                    task = json.loads(db.execute('SELECT data FROM tasks').fetchone()[0])
                    assert task['title'] == title and task['state'] == 'ready'
                commands = [r[0] for r in db.execute("SELECT json_extract(data,'$.input.command') FROM orchestration_events WHERE type='request_received'")]
            assert commands.count(mutation) == 1, '不允许自动重放写命令'
            if red:
                assert any(button['text'] == '取消' and not button['disabled'] for button in view['buttons'])
                assert any(button['text'] == '确认并注册任务' and not button['disabled'] for button in view['buttons'])
                row['status'] = 'NO_GO'; row['red_reproduced'] = True
            elif name == 'save-result':
                assert readback in commands and '已核实任务卡已保存' in view['text']
                assert any(button['text'] == '确认并注册任务' and button['disabled'] for button in view['buttons'])
                win.call('click', text='关闭表单（保留已保存记录）'); win.wait(lambda view: not view['form'])
                assert inventory(state) == counts; row['status'] = 'PASS'
            elif name == 'create-result':
                assert 'status' in commands; row['status'] = 'PASS'
            else:
                assert '结果未知' in view['text']
                assert any(button['text'] == '结果未知，暂不能取消' and button['disabled'] for button in view['buttons'])
                assert any(button['text'] == '确认并注册任务' and button['disabled'] for button in view['buttons'])
                # The backend cancellation/replay checks are also exercised by
                # test_t106_postcommit.mjs through the actual daemon handler.
                assert win.call('inspect')['form']; row['status'] = 'PASS'
            win.close()
        assert report['cases'][0]['red_reproduced'] and all(row['status'] == 'PASS' for row in report['cases'][1:])
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            for win in windows:
                win.close()
            for tree, state, local_env, pid in reversed(daemons):
                assert gate(tree, state, local_env, 'daemon_stop')['ok']
                until(lambda: not (state / 'control.sock').exists(), '后台 socket 未退出')
                def absent():
                    result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True)
                    assert result.returncode in (0, 1) and not result.stderr
                    return not result.stdout.strip() or result.stdout.strip().startswith('Z')
                until(absent, '自有后台未退出')
            report['cleanup_complete'] = True
            for path in builds:
                shutil.rmtree(path)
        except Exception as error:
            report.update(status='INCOMPLETE', cleanup_complete=False, cleanup_error=repr(error))
        if report['status'] == 'PASS' and report.get('cleanup_complete'):
            shutil.rmtree(root)
        else:
            report['retained_fixture'] = str(root)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(output)), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
