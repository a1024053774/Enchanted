"""真实 CLI/daemon/PTY/Git/SQLite/Electron；本地原生接收器，不调用模型。"""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
import traceback
import uuid
from run_t103_picker import Window
from t107_persistence import persistence


def main():
    parser = argparse.ArgumentParser()
    for name in ('source', 'electron-dist', 'summary'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--baseline', default='6411bdff8482ba47da207efa6a295a12666222aa')
    args = parser.parse_args()
    source, output = args.source.resolve(), args.summary.resolve()
    assert not output.exists(), 'Use a fresh summary path'
    root = Path(tempfile.mkdtemp(prefix='t109-real-', dir='/private/tmp')).resolve()
    state, home = root / 'state', root / 'home'
    home.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
    env.pop('NODE_OPTIONS', None)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    dist = args.electron_dist.resolve(strict=True)
    binary = dist / 'Electron.app/Contents/MacOS/Electron'
    assert not str(dist).startswith('/Volumes/') and (dist / 'version').read_text().strip() == '43.4.1'
    env.update(HOME=str(home), SHELL='/bin/zsh', ELECTRON_OVERRIDE_DIST_PATH=str(dist), LC_ALL='C',
               TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp', PYTHONDONTWRITEBYTECODE='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='T109 fixture', GIT_AUTHOR_EMAIL='t109@example.invalid',
               GIT_COMMITTER_NAME='T109 fixture', GIT_COMMITTER_EMAIL='t109@example.invalid')
    report = dict(status='INCOMPLETE', task='T-109', attempt='a1', model_calls=0, baseline=args.baseline,
                  checks=[], commands=[], limitations=['CLI 为本地 C 接收器；不证明模型行为或原生提问信号。'])
    windows, builds = [], []
    active, pid, epoch = source, None, 0

    def run(argv, cwd=source):
        value = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=value.returncode))
        assert value.returncode == 0, (argv, value.stdout[-3000:], value.stderr[-3000:])
        return value.stdout

    def call(command, *fields):
        return json.loads(run(['node', active / 'workbench/src/gates/cli.ts', '--state', state, command, *fields]))

    def until(read, predicate):
        deadline = time.monotonic() + 20
        while True:
            value = read()
            if predicate(value):
                return value
            assert time.monotonic() < deadline, value
            time.sleep(.1)

    def start(tree, config=None):
        nonlocal active, pid, epoch
        active, epoch = tree, epoch + 1
        env['A2A_OPERATOR_CREDENTIAL'] = str(root / ('operator-' + str(epoch) + '.json'))
        pid = call('daemon_start', *(['--launch-config', config] if config else []))['pid']
        until(lambda: call('pane_layout'), lambda row: not row.get('recovering'))

    def stop():
        nonlocal pid
        if pid is not None:
            call('daemon_stop')
            until(lambda: (state / 'daemon.pid').exists(), lambda present: not present)
            pid = None

    def build(tree, label):
        value = json.loads(run(['node', tree / 'workbench/app/build.mjs', '--slot', 't109-' + label + '-' + uuid.uuid4().hex[:8]]).splitlines()[-1])
        builds.append(Path(value['out']).parent)
        return Path(value['out'])

    def window(tree, built, label):
        return Window(tree, source / 'workbench/tests/t107_sidebar_driver.mjs', built, state,
                      root / 'ui', root / label, env, windows,
                      dict(executable=str(binary), dist=str(dist), version='43.4.1'), through_start=False)

    try:
        assert (source / 'workbench/node_modules').is_dir() and not (source / 'workbench/node_modules').is_symlink()
        revision = run(['git', 'rev-parse', 'HEAD']).strip()
        changes = run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'workbench/src', 'workbench/app', 'scripts',
                       'workbench/tests', 'workbench/package.json', 'workbench/package-lock.json']).splitlines()
        report.update(source_head=revision, source_changes=changes, candidate_revision=revision if not changes else None)
        receiver = root / 'receiver'
        run(['cc', '-O2', source / 'workbench/tests/t096_resume_receiver.c', '-o', receiver])
        native_home = root / 'native-home'
        native_home.mkdir()
        role_file = root / 'role.md'
        role_file.write_text('本地接收器，不运行模型或工具。\n', encoding='utf-8')
        config = root / 'launch.json'
        config.write_text(json.dumps(dict(codex_bin=str(receiver), codex_home=str(native_home), role_card=str(role_file),
                          role_card_revision='T-109/fixture', code_revision=revision, hook_authorization='T-109/local-receiver', turn_limit=1,
                          controllers={preset: dict(executable=str(receiver), model='不调用模型', effort='high', settings={},
                                      role_card=str(role_file), role_card_revision='T-109/fixture') for preset in ('ideation', 'executor')})), encoding='utf-8')
        start(source, config)
        for index in range(2):
            repo = root / ('repo-' + str(index))
            run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
            (repo / 'acceptance.py').write_text('assert True\n', encoding='utf-8')
            (repo / 'src').mkdir()
            (repo / 'src/value').write_text('fixture\n', encoding='utf-8')
            run(['git', '-C', repo, 'add', '.'])
            run(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'T109 fixture'])
            task = 'task-' + str(index)
            card = call('card_template', '--task', task, '--repo', repo, '--project', 'project-' + str(index))['card']
            card.update(goal='本地派发记录验证', non_goals=['不调用模型'], paths=dict(allow=['src/'], deny=[]), oracle_paths=['acceptance.py'],
                        completion_conditions=[dict(argv=['python3', '-I', '-B', 'acceptance.py'])], task_type='后端逻辑', complexity='M',
                        executor=dict(cli='Codex', model='gpt-6.1-sol', effort='xhigh'))
            card_file = root / ('card-' + str(index) + '.json')
            card_file.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
            assert call('card_save', '--task', task, '--card', card_file, '--expected-version', '0')['ok']
            assert call('create', '--task', task, '--repo', repo, '--project', 'project-' + str(index), '--branch', 'refs/heads/main', '--card-version', '1')['ok']
        idea = call('controller_prepare', '--task', 'task-0', '--preset', 'ideation')['prepared']
        executor = call('controller_prepare', '--task', 'task-0', '--preset', 'executor', '--parent-launch', idea['id'])['prepared']
        with sqlite3.connect(state / 'state.sqlite3') as db:
            earlier = list(db.execute('SELECT id,data FROM launch_records ORDER BY rowid'))
        result = call('dispatch', '--task', 'task-0', '--runtime-mode', 'workspace-write', '--parent-launch', executor['id'])
        assert result['ok'], result
        thread = result['attempt']['thread_id']
        worker = call('launch_show', '--launch', call('pane_status', '--thread', thread)['launch'])['launch']
        assert worker['parent_launch'] == executor['id'] and executor['parent_launch'] == idea['id']
        with sqlite3.connect(state / 'state.sqlite3') as db:
            assert list(db.execute('SELECT id,data FROM launch_records ORDER BY rowid LIMIT 2')) == earlier
            dispatch = json.loads(db.execute('SELECT data FROM dispatch_records WHERE launch=? ORDER BY seq LIMIT 1', (worker['id'],)).fetchone()[0])
            assert dispatch['parent_launch'] == executor['id']
        report['checks'].append(dict(name='真实 CLI 派发及 PTY 启动追加父 launch，旧启动记录原字节不变', status='PASS'))
        stop()
        records = [idea, executor, worker]
        with sqlite3.connect(state / 'state.sqlite3') as db:
            for name, role, parent in [('second-worker', 'worker', executor['id']), ('reviewer', 'reviewer', executor['id']),
                                      ('monitor', 'monitor', executor['id']), ('legacy', 'worker', None), ('missing', 'worker', 'nonexistent')]:
                row = dict(id=name, thread='thread-' + name, role=role, preset=None, task='task-0', project='project-0',
                           attempt='a-sentinel', session='session-' + name, fence=1, spec_rev=1,
                           cli_version='codex-cli 0.163.0', model_requested='不调用模型')
                if parent is not None:
                    row['parent_launch'] = parent
                db.execute('INSERT INTO launch_records VALUES (?,?,?,?)', (row['id'], row['task'], row['attempt'], json.dumps(row)))
                records.append(row)
            for index, row in enumerate(records[:5]):
                trace = state / 'traces' / row['id'] / 'pty.raw'
                trace.parent.mkdir(parents=True, exist_ok=True)
                if not trace.exists():
                    trace.write_text('', encoding='utf-8')
                db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)',
                           ('2026-10-20', 'pane_layout_opened', row['id'], row['task'], row['attempt'],
                            json.dumps(dict(position=index, native_session=None, resume_argv=None))))
        baseline = root / 'baseline'
        baseline.mkdir()
        archive = subprocess.check_output(['git', 'archive', args.baseline, 'workbench'], cwd=source, env=env)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(baseline)
        # Ordinary private copies; no link targets any checkout or output path.
        shutil.copytree(source / 'workbench/node_modules', baseline / 'workbench/node_modules', symlinks=False)
        start(baseline)
        red = window(baseline, build(baseline, 'red'), 'red')
        red.wait(lambda row: len(row['projects']) == 2 and not any(p['disabled'] for p in row['projects']))
        red.call('project', target='project-0')
        view = red.wait(lambda row: len(row['agents']) == len(records) and not any(a['disabled'] for a in row['agents']))
        nodes = {row['id']: row for row in view['agents']}
        assert nodes[worker['id']]['parent'] == '' and nodes[worker['id']]['level'] == 0
        report['checks'].append(dict(name='真实 Electron 原版本忽略新记录中的父 launch，worker 留在未归属', status='PASS'))
        red.close()
        stop()
        start(source)
        green = window(source, build(source, 'green'), 'green')
        green.wait(lambda row: len(row['projects']) == 2 and not any(p['disabled'] for p in row['projects']))
        green.call('project', target='project-0')
        view = green.wait(lambda row: len(row['agents']) == len(records) and not any(a['disabled'] for a in row['agents']))
        nodes = {row['id']: row for row in view['agents']}
        assert [nodes[row['id']]['level'] for row in [idea, executor, worker]] == [0, 1, 2]
        assert nodes[idea['id']]['x'] < nodes[executor['id']]['x'] < nodes[worker['id']]['x']
        assert nodes['legacy']['parent'] == '' and nodes['missing']['parent'] == ''
        assert 'a-sentinel' in nodes['reviewer']['text'] and '审查员' in nodes['reviewer']['text']
        before = persistence(state)
        green.call('sidebar')
        green.call('sidebar')
        assert persistence(state) == before, 'Actual sidebar IPC changed tables/schema/traces'
        green.call('toggle', target=executor['id'])
        collapsed = green.wait(lambda row: next(a for a in row['agents'] if a['id'] == worker['id'])['visible'] is False)
        summary = next(row for row in collapsed['summaries'] if row['id'] == executor['id'])
        assert '子会话 4' in summary['text'] and summary['visible']
        assert '未恢复 3' in summary['text'] and '未知 1' in summary['text'], summary
        green.call('toggle-keyboard', target=executor['id'])
        green.wait(lambda row: next(a for a in row['agents'] if a['id'] == worker['id'])['visible'])
        green.call('toggle', target=idea['id'])
        collapsed = green.wait(lambda row: next(a for a in row['agents'] if a['id'] == executor['id'])['visible'] is False)
        summary = next(row for row in collapsed['summaries'] if row['id'] == idea['id'])
        assert '子会话 5' in summary['text'] and '未恢复 4' in summary['text'] and '未知 1' in summary['text'], summary
        green.call('toggle', target=idea['id'])
        green.wait(lambda row: next(a for a in row['agents'] if a['id'] == worker['id'])['visible'])
        green.call('agent', target=worker['id'])
        green.wait(lambda row: row.get('focusedLaunch') == worker['id'])
        green.call('resize', width=900, height=700)
        view = green.wait(lambda row: not any(a['disabled'] for a in row['agents']))
        assert not any(a['overflow'] for a in view['agents'] if a['visible'])
        report['checks'].append(dict(name='真实 Electron 三级缩进、旧记录/缺失父项、折叠汇总、键盘展开、聚焦和窄窗', status='PASS'))
        report['checks'].append(dict(name='真实 Electron sidebar IPC 全表/schema/trace 零写入', status='PASS'))
        green.close()
        stop()
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            for win in windows:
                win.close()
            stop()
            report['cleanup_complete'] = True
        except Exception as error:
            report.update(status='INCOMPLETE', cleanup_complete=False, cleanup_error=repr(error))
        if report['status'] == 'PASS':
            shutil.rmtree(root)
            for directory in builds:
                shutil.rmtree(directory)
        else:
            report.update(retained_fixture=str(root), retained_builds=list(map(str, builds)))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
