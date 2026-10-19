"""真实 Electron 表单与门禁；主控操作两次原生目录对话框，不调用模型。"""
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
    for name in ['source', 'baseline', 'electron-dist', 'summary']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    source, baseline = args.source.resolve(), args.baseline.resolve()
    output = args.summary.resolve()
    assert not output.exists(), '保留既有摘要，请换新编号'
    root = Path(tempfile.mkdtemp(prefix='t106-run-', dir='/private/tmp')).resolve()
    home = root / 'home'; home.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_', 'GIT_'))
           and key not in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
    runtime = args.electron_dist.resolve(strict=True)
    assert not runtime.is_relative_to('/Volumes') and (runtime / 'version').read_text().strip() == '43.4.1'
    binary = runtime / 'Electron.app/Contents/MacOS/Electron'
    env.update(HOME=str(home), TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp',
               ELECTRON_OVERRIDE_DIST_PATH=str(runtime))
    report = dict(status='INCOMPLETE', task='T-106', attempt='a1', model_turns=0, fake_api_requests=0,
                  argv=list(map(str, __import__('sys').argv)), checks=[], commands=[], native_dialogs=[])
    daemons, windows, builds = [], [], []

    def run(argv, cwd=source, local_env=env):
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=local_env, capture_output=True, text=True, timeout=180)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=result.returncode,
                                       stdout=result.stdout[-10000:], stderr=result.stderr[-4000:]))
        assert result.returncode == 0, report['commands'][-1]
        return result.stdout

    def call(tree, state, local_env, command, *fields):
        return json.loads(run(['node', tree / 'workbench/src/gates/cli.ts', '--state', state, command, *fields], local_env=local_env))

    def until(read, description, seconds=20):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            value = read()
            if value:
                return value
            time.sleep(.15)
        raise AssertionError(description)

    def start(tree, name):
        state = root / (name + '-state')
        local_env = dict(env, A2A_OPERATOR_CREDENTIAL=str(root / (name + '-operator.json')))
        pid = call(tree, state, local_env, 'daemon_start')['pid']
        daemons.append((tree, state, local_env, pid))
        until(lambda: not call(tree, state, local_env, 'pane_layout').get('recovering'), '后台恢复未结束')
        return state, local_env

    def build(tree, name):
        value = json.loads(run(['node', tree / 'workbench/app/build.mjs', '--slot', 't106-' + name + '-' + uuid.uuid4().hex[:8]]).splitlines()[-1])
        builds.append(Path(value['out']).parent)
        return Path(value['out'])

    def window(tree, built, state, local_env, name):
        return Window(tree, source / 'workbench/tests/t106_creation_driver.mjs', built, state,
                      root / (name + '-ui'), root / name, local_env, windows,
                      dict(executable=str(binary), dist=str(runtime), version='43.4.1'), through_start=False)

    def check(text):
        report['checks'].append(text)

    def inventory(state):
        with sqlite3.connect(state / 'state.sqlite3') as db:
            return {name: db.execute('SELECT count(*) FROM ' + name).fetchone()[0]
                    for name in ['tasks', 'task_card_versions', 'task_card_snapshots', 'attempts', 'launch_records']}

    def open_form(win):
        win.call('click', text='新建项目与任务')
        win.wait(lambda view: view['form'])
        win.call('click', text='选择仓库目录…')
        print('NATIVE_DIALOG: 请主控在本测试 Electron 的原生目录对话框中选择：' + str(repo), flush=True)
        print('可用“前往文件夹”输入该路径；此处不替换对话框结果。等待 180 秒。', flush=True)
        def chosen():
            view = win.call('inspect')
            if view.get('alerts'):
                raise AssertionError(view['alerts'])
            return view if view.get('repo') == str(repo) and view['fields'].get('card') else None
        view = until(chosen, '原生目录选择未完成，保留本次现场', 180)
        report['native_dialogs'].append(dict(pid=win.proc.pid, selected=view['repo'], expected=str(repo)))
        assert view['fields']['branch'] == 'refs/heads/main'
        assert '项目随首个任务一起注册' in view['text']
        return view

    def fill(win, card, command):
        remaining = {key: value for key, value in card.items() if key not in ('goal', 'completion_conditions')}
        fields = dict(project=project, title=title, goal=card['goal'], command=command,
                      card=json.dumps(remaining, ensure_ascii=False), branch='refs/heads/main')
        for field, value in fields.items():
            win.call('fill', field=field, value=value)
        view = win.wait(lambda view: all(view['fields'].get(key) == value for key, value in fields.items()))
        assert view['formValid'], view['invalidFields']

    try:
        # Independent input includes a title/goal sentinel and real test file.
        nonce = uuid.uuid4().hex[:10]
        repo = root / 'repo'; repo.mkdir()
        run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
        (repo / 'src').mkdir(); (repo / 'tests').mkdir()
        (repo / 'src/value.txt').write_text('原始输入\n', encoding='utf-8')
        marker = root / 'completion-was-run'
        (repo / 'tests/criterion.py').write_text(
            "from pathlib import Path\nassert Path('src/value.txt').read_text(encoding='utf-8') == '原始输入\\n'\n"
            + 'Path(' + repr(str(marker)) + ").write_text('ran', encoding='utf-8')\n", encoding='utf-8')
        run(['git', '-C', repo, 'add', '.'])
        run(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=T106 fixture',
             '-c', 'user.email=t106@example.invalid', 'commit', '-m', 'Independent registration fixture'])
        project, title = 'project-' + nonce, '注册<独立标题> · ' + nonce
        card = dict(id='task-' + nonce, source=None, goal='保留原始输入并创建可验收任务 · ' + nonce,
                    non_goals=['不派 worker、不运行模型'], paths=dict(allow=['src/'], deny=[]),
                    oracle_paths=['tests/criterion.py'], completion_conditions=[dict(argv=['python3', 'tests/criterion.py'])],
                    red_commands=[], task_type='前端界面', repair_target=None, complexity='S',
                    executor=dict(cli='Codex', model='gpt-6.1-sol', effort='xhigh'), base_commit=None, writer=None)
        command = json.dumps(card['completion_conditions'][0]['argv'])
        red_state, red_env = start(baseline, 'red')
        red = window(baseline, build(baseline, 'red'), red_state, red_env, 'red')
        view = red.wait(lambda view: view['busy'] == 'false')
        assert not any(button['text'] == '新建项目与任务' for button in view['buttons'])
        assert 'creationSubmit' not in view['bridge'] and not view['projects'] and not view['tasks']
        red.close(); check('已知坏版本真实 Electron：空库没有创建表单入口，预期红态')
        state, local_env = start(source, 'green')
        green = window(source, build(source, 'green'), state, local_env, 'green')
        view = green.wait(lambda view: view['busy'] == 'false')
        assert view['node'] == 'undefined' and not view['tasks'] and not view['projects']
        open_form(green)
        assert all(value == 0 for value in inventory(state).values())
        # Renderer cannot add a repository path to the operator request.
        injected = green.call('bridge', operation='creationSubmit', input=dict(
            task=card['id'], project=project, title=title, branch='refs/heads/main',
            card=json.dumps(card), repo='/renderer/injected'))
        assert injected.get('rejected') and all(value == 0 for value in inventory(state).values())
        missing = dict(card); missing.pop('non_goals')
        fill(green, missing, command); green.call('submit')
        denied = green.wait(lambda view: any('invalid_task_card' in alert and 'card' in alert for alert in view['alerts']))
        assert all(value == 0 for value in inventory(state).values())
        fill(green, card, json.dumps('请完成任务'))
        green.call('submit')
        green.wait(lambda view: any('invalid_task_card' in alert and 'Command argv required' in alert for alert in view['alerts']))
        assert all(value == 0 for value in inventory(state).values())
        fill(green, card, json.dumps(['t106-command-does-not-exist-' + nonce]))
        green.call('submit')
        green.wait(lambda view: any('Executable is unavailable' in alert for alert in view['alerts']))
        assert all(value == 0 for value in inventory(state).values())
        green.call('click', text='取消'); green.wait(lambda view: not view['form'])
        assert all(value == 0 for value in inventory(state).values())
        assert call(source, state, local_env, 'projects_list')['projects'] == []
        check('确认前无任务/卡版本；路径注入拒绝；缺字段、非 argv、不可执行命令显示门禁原因；取消后任务、卡版本、快照、attempt、启动记录均未增加')
        open_form(green); fill(green, card, command)
        green.call('resize', width=1000, height=700)
        assert all(value == 0 for value in inventory(state).values())
        green.call('submit')
        view = green.wait(lambda view: not view['form'] and any(task['id'] == card['id'] for task in view['tasks']))
        assert project in view['projects'] and any(title in task['text'] for task in view['tasks'])
        registered = call(source, state, local_env, 'status', '--task', card['id'])['task']
        assert registered['state'] == 'ready' and registered['title'] == title and registered['project_id'] == project
        expected = json.loads(json.dumps(card))
        expected['completion_conditions'][0]['argv'][0] = str(Path(shutil.which('python3', path=env['PATH'])).resolve())
        assert registered['card'] == expected and not marker.exists(), '注册应保留用户输入，且不能提前执行完成条件'
        check('真实 Electron 确认后任务及隐含项目出现在列表；标题/目标 sentinel 保留；完成条件未提前执行')
        cli_state, cli_env = start(source, 'cli')
        card_file = root / 'cli-card.json'; card_file.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
        call(source, cli_state, cli_env, 'card_template', '--task', card['id'], '--repo', repo)
        call(source, cli_state, cli_env, 'card_validate', '--task', card['id'], '--card', card_file)
        call(source, cli_state, cli_env, 'card_save', '--task', card['id'], '--card', card_file, '--expected-version', '0')
        direct = call(source, cli_state, cli_env, 'create', '--task', card['id'], '--repo', repo,
                      '--branch', 'refs/heads/main', '--card-version', '1', '--project', project, '--title', title)['task']
        with sqlite3.connect(state / 'state.sqlite3') as db:
            stored = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (card['id'],)).fetchone()[0])
            snapshot = json.loads(db.execute('SELECT data FROM task_card_snapshots WHERE id=?', (stored['card_snapshot_id'],)).fetchone()[0])
        with sqlite3.connect(cli_state / 'state.sqlite3') as db:
            cli_stored = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (card['id'],)).fetchone()[0])
            cli_snapshot = json.loads(db.execute('SELECT data FROM task_card_snapshots WHERE id=?', (cli_stored['card_snapshot_id'],)).fetchone()[0])
        assert stored == registered and cli_stored == direct
        assert snapshot == cli_snapshot == expected
        stored.pop('card_snapshot_id'); cli_stored.pop('card_snapshot_id')
        assert stored == cli_stored, 'UI 和直接 CLI 的整条任务记录应一致，只排除独立生成的 snapshot UUID'
        check('两份独立门禁库的整条任务记录一致（只排除随机 snapshot UUID），任务卡快照内容一致')
        green.call('click', text='新建任务')
        view = green.wait(lambda view: view['form'])
        assert view['fields']['project'] == project
        green.call('click', text='取消'); green.wait(lambda view: not view['form'])
        assert inventory(state)['tasks'] == 1 and inventory(state)['task_card_versions'] == 1
        check('现有项目的新建任务入口预填项目号；取消不增加记录')
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            for win in windows:
                win.close()
            for tree, state, local_env, pid in reversed(daemons):
                call(tree, state, local_env, 'daemon_stop')
                until(lambda: not (state / 'control.sock').exists(), '后台 socket 未退出')
                def absent():
                    result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True)
                    assert result.returncode in (0, 1) and not result.stderr
                    return not result.stdout.strip() or result.stdout.strip().startswith('Z')
                until(absent, '后台进程未退出')
            report['cleanup_complete'] = True
        except Exception as error:
            report.update(status='INCOMPLETE', cleanup_error=repr(error), cleanup_complete=False)
        if report['status'] == 'PASS' and report.get('cleanup_complete'):
            shutil.rmtree(root)
            for built in builds:
                shutil.rmtree(built)
        else:
            report['retained_fixture'] = str(root)
            report['retained_builds'] = list(map(str, builds))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
