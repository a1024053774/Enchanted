"""T-107 real Electron/daemon/SQLite/Git, using isolated saved launch facts.

No model calls, Herdr, screenshots, or native directory dialogs. Historical pane
states are produced by real backend recovery; fixture dispatch ancestry is
controlled input, not proof that production currently records concrete senders.
"""
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


def assert_fixture_restoration(view):
    # These deliberately incomplete controller records and managed attempts
    # must fail the existing T-096 restoration rules. Require exact pane-local
    # diagnostics, read-only input, and no additional global/connection alerts.
    controller = '未恢复：restore_record_unrecognized。启动记录已保留。'
    managed = '未恢复：受管 worker 未续接；请由执行主控按中断恢复流程回收后重新认领。启动记录已保留。'
    expected = {'agent-' + str(i): controller if i < 2 else managed for i in range(5)}
    panes = {pane.get('launch'): pane for pane in view['panes']}
    assert len(panes) == len(view['panes']), 'Duplicate historical launch views'
    for launch, message in expected.items():
        assert launch in panes, 'Expected historical pane has not loaded: ' + launch
        assert panes[launch]['input'] == 'false', 'Historical restoration failure must remain read-only: ' + launch
        assert panes[launch]['alerts'] == [message], ('Unexpected restoration diagnostic', launch, panes[launch]['alerts'])
    assert sorted(view['alerts']) == sorted(expected.values()), ('Unexpected or missing page alerts', view['alerts'])


def main():
    parser = argparse.ArgumentParser()
    for name in ['source', 'dependencies', 'electron-dist', 'summary']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--baseline', default='0967cd465ce20c01b0a6ee29b2931ecbf4032caf')
    args = parser.parse_args()
    source, output = args.source.resolve(), args.summary.resolve()
    assert not output.exists(), 'Summary exists; preserve it and use a new name'
    root = Path(tempfile.mkdtemp(prefix='t107-real-', dir='/private/tmp')).resolve()
    state, home = root / 'state', root / 'home'
    home.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'GIT_'))}
    for key in ['NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE']:
        env.pop(key, None)
    dist = args.electron_dist.resolve(strict=True)
    binary = dist / 'Electron.app/Contents/MacOS/Electron'
    assert not str(dist).startswith('/Volumes/') and (dist / 'version').read_text().strip() == '43.4.1'
    env.update(HOME=str(home), SHELL='/bin/zsh', ELECTRON_OVERRIDE_DIST_PATH=str(dist),
               LC_ALL='C',
               TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='T107 fixture', GIT_AUTHOR_EMAIL='t107@example.invalid',
               GIT_COMMITTER_NAME='T107 fixture', GIT_COMMITTER_EMAIL='t107@example.invalid')
    report = dict(status='INCOMPLETE', task='T-107', attempt='a1', model_calls=0,
                  argv=list(map(str, __import__('sys').argv)), baseline=args.baseline,
                  checks=[], commands=[], limitations=[
                      '等待用户回答、等待主控回答的真实信号缺口未解决；七状态验收 INCOMPLETE。',
                      '现有 worker 派发无具体父 launch 绑定，worker/reviewer 在未归属的任务下；完整层级验收 INCOMPLETE。',
                      '真实系统通知未触发；转换和开关只由 IPC 合同验证。'])
    windows, builds = [], []
    active, pid, epoch = None, None, 0

    def run(argv, cwd=source):
        value = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=value.returncode, stdout=value.stdout[-6000:], stderr=value.stderr[-3000:]))
        assert value.returncode == 0, report['commands'][-1]
        return value.stdout

    def call(command, *fields):
        return json.loads(run(['node', active / 'workbench/src/gates/cli.ts', '--state', state, command, *fields]))

    def until(read, message):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            value = read()
            if value:
                return value
            time.sleep(.1)
        raise AssertionError(message)

    def start(tree):
        nonlocal active, pid, epoch
        active, epoch = tree, epoch + 1
        env['A2A_OPERATOR_CREDENTIAL'] = str(root / ('operator-' + str(epoch) + '.json'))
        pid = call('daemon_start')['pid']
        until(lambda: not call('pane_layout').get('recovering'), 'Recovery pending')

    def stop():
        nonlocal pid
        if pid is None:
            return
        call('daemon_stop')
        until(lambda: not (state / 'daemon.pid').exists(), 'Daemon has not confirmed shutdown')
        pid = None

    def build(tree, label):
        value = json.loads(run(['node', tree / 'workbench/app/build.mjs', '--slot', 't107-' + label + '-' + uuid.uuid4().hex[:8]]).splitlines()[-1])
        builds.append(Path(value['out']).parent)
        return Path(value['out'])

    def window(tree, build_dir, label):
        return Window(tree, source / 'workbench/tests/t107_sidebar_driver.mjs', build_dir, state,
                      root / 'ui', root / label, env, windows,
                      dict(executable=str(binary), dist=str(dist), version='43.4.1'), through_start=False)

    try:
        baseline, candidate = root / 'baseline', root / 'candidate'
        baseline.mkdir()
        archive = subprocess.run(['git', 'archive', args.baseline, 'workbench'], cwd=source, capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(baseline)
        shutil.copytree(source / 'workbench', candidate / 'workbench', ignore=shutil.ignore_patterns('node_modules', '__pycache__'))
        for tree in [baseline, candidate]:
            (tree / 'workbench/node_modules').symlink_to(args.dependencies.resolve(strict=True), target_is_directory=True)
        # The baseline creates the real schema. Test inputs enter its isolated
        # database only while the backend is stopped, following T-105 fixtures.
        start(baseline)
        stop()
        repos = [root / 'repo-one', root / 'repo-two']
        for repo in repos:
            run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
            (repo / 'content').write_text('base\n', encoding='utf-8')
            run(['git', '-C', repo, 'add', '.'])
            run(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fixture base'])
        head = run(['git', '-C', repos[0], 'rev-parse', 'HEAD']).strip()
        run(['git', '-C', repos[0], 'config', 'remote.origin.url', str(root / 'unused-origin')])
        run(['git', '-C', repos[0], 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'])
        run(['git', '-C', repos[0], 'update-ref', 'refs/remotes/origin/main', head])
        run(['git', '-C', repos[0], 'branch', '--set-upstream-to=origin/main', 'main'])
        (repos[0] / 'content').write_text('ahead\n', encoding='utf-8')
        run(['git', '-C', repos[0], '-c', 'core.hooksPath=/dev/null', 'commit', '-am', 'fixture ahead'])
        git_status = run(['git', '-C', repos[0], 'status', '-sb'])
        assert '[ahead 1]' in git_status
        now = '2026-10-19T00:00:00Z'
        launches = []
        with sqlite3.connect(state / 'state.sqlite3') as db:
            def event(kind, record, data):
                db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)',
                           (now, kind, record['id'], record['task'], record['attempt'], json.dumps(data)))
            for index in range(2):
                task = dict(task_id='task-' + str(index), title='独立项目任务 ' + str(index), project_id='project-' + str(index),
                            repo=str(repos[index]), state='ready', spec_rev=1, current_attempt=None,
                            candidate_commit=None, verification=None, integration_intent=None)
                db.execute('INSERT INTO tasks VALUES (?,?)', (task['task_id'], json.dumps(task)))
            for index, role in enumerate(['controller', 'controller', 'worker', 'worker', 'reviewer', 'monitor', 'worker']):
                record = dict(id='agent-' + str(index), thread='thread-' + str(index), task='task-0', project='project-0', role=role,
                              preset='ideation' if index == 0 else 'executor' if index == 1 else None,
                              attempt=None if role == 'controller' else 'attempt-' + str(index),
                              session='session-' + str(index), fence=1, spec_rev=1, authentication='normal-login',
                              created_at=now, cli_version='codex-cli 0.163.0', model_requested='不调用模型')
                launches.append(record)
                db.execute('INSERT INTO launch_records VALUES (?,?,?,?)', (record['id'], record['task'], record['attempt'], json.dumps(record)))
                trace = state / 'traces' / record['id']
                trace.mkdir(parents=True)
                (trace / 'pty.raw').write_text('独立历史启动记录\r\n', encoding='utf-8')
                if index < 5:
                    event('pane_layout_opened', record, dict(position=index, native_session=None, resume_argv=None))
                if index == 6:
                    event('pane_archived', record, dict(reason='fixture ended'))
                if index == 1:
                    sender = 'ideation'
                    db.execute('INSERT INTO dispatch_records(id,launch,data) VALUES (?,?,?)',
                               ('dispatch-' + str(index), record['id'], json.dumps(dict(source='inbox', text='已保存关系夹具', sender=sender, inbox_entry='assign-1', registered_at=now))))
            relay_input = dict(command='inbox_send', kind='assign', launch='agent-0', project='project-0', task='task-0', preset='ideation')
            relay_result = dict(ok=True, entry=dict(id='assign-1', kind='assign', **{'from': 'ideation'}, to='executor'))
            db.execute('INSERT INTO relay_requests VALUES (?,?,?,?,?,?,?)', ('assign-key', 'agent-0', 'task-0', None, 'assign-request', json.dumps(relay_input), now))
            db.execute('INSERT INTO relay_results VALUES (?,?,?)', ('assign-key', json.dumps(relay_result), now))
            before = list(db.execute('SELECT id,data FROM tasks ORDER BY id'))
        start(baseline)
        red = window(baseline, build(baseline, 'red'), 'red')
        view = red.wait(lambda row: len(row['projects']) == 2)
        assert 'sidebar' not in view['bridge'] and not view['agents']
        report['checks'].append(dict(name='真实 Electron 已知坏基线', status='PASS', observed='无侧栏 IPC、agent 树与 Git 摘要，符合预期红态'))
        red.close()
        stop()
        for mode in ['identity', 'readonly', 'filename', 'rollout']:
            probe = root / ('daemon-' + mode + '.json')
            run(['node', '--experimental-vm-modules', source / 'workbench/tests/test_t107_daemon_readonly.mjs', probe, candidate, mode])
            result = json.loads(probe.read_text(encoding='utf-8'))
            assert result['status'] == 'PASS' and result['cleanup_complete'], result
        report['checks'].append(dict(name='实际 daemon：根／辅助会话隔离、未消费日志下全部表与 trace 零写入', status='PASS'))
        start(candidate)
        green_build = build(candidate, 'green')
        green = window(candidate, green_build, 'green')
        green.wait(lambda row: len(row['projects']) == 2 and 'sidebar' in row['bridge'] and not any(project['disabled'] for project in row['projects']))
        green.call('project', target='project-0')
        # Since the workspace pages, choosing a project opens no pane by itself; each pane opens from its sidebar row below.
        expected_panes = set()
        view = green.wait(lambda row: len(row['agents']) == 7 and 'task-0' in row['task'] and not any(agent['disabled'] for agent in row['agents']))
        before_sidebar = persistence(state)
        green.call('sidebar')
        green.call('sidebar')
        assert persistence(state) == before_sidebar, 'Sidebar read changed persisted tables or traces'
        report['checks'].append(dict(name='真实 Electron 侧栏 IPC：所有 SQLite 表、schema 和 trace 原值不变', status='PASS'))
        assert_fixture_restoration(view)
        nodes = {row['id']: row for row in view['agents']}
        assert [nodes['agent-' + str(i)]['level'] for i in range(5)] == [0, 1, 0, 0, 0]
        assert nodes['agent-0']['x'] < nodes['agent-1']['x']
        assert all(nodes['agent-' + str(i)]['parent'] == '' for i in [2, 3, 4])
        assert 'worker' in view['unassigned'] and '审查员' in view['unassigned']
        assert nodes['agent-5']['state'] == 'unknown' and '监视器' in view['unassigned']
        assert nodes['agent-6']['state'] == 'ended'
        assert all(nodes['agent-' + str(i)]['state'] == 'unrestored' for i in range(5))
        assert 'attempt attempt-3' in nodes['agent-3']['text']
        project = next(row for row in view['projects'] if row['id'] == 'project-0')
        # The branch line under the project name (T-107 #5, user 2026-10-22 "显示出来吧"): branch · ↑ahead ↓behind, or 无上游.
        assert 'main · ↑1 ↓0' in project['text'] and project['state'] == 'unknown'
        assert 'main · 无上游' in next(row for row in view['projects'] if row['id'] == 'project-1')['text']
        report['checks'].append(dict(name='项目与 agent 层级、角色、attempt、Git 与三种历史状态', status='PASS', git_status=git_status))
        for index in range(7):
            launch = 'agent-' + str(index)
            green.call('agent', target=launch)
            expected_panes.add(launch)
            view = green.wait(lambda row: row.get('focusedLaunch') == launch and not any(agent['disabled'] for agent in row['agents'])
                              and {pane.get('launch') for pane in row['panes']} == expected_panes)
            assert_fixture_restoration(view)
            assert not next(p for p in view['panes'] if p.get('launch') == launch)['input'] == 'true'
        assert green.call('bridge', target='not-a-launch')['rejected']
        report['checks'].append(dict(name='点击逐个聚焦原窗格与临时历史窗格，均只读，未知身份拒收', status='PASS'))
        green.call('resize', width=900, height=700)
        view = green.wait(lambda row: len(row['agents']) == 7 and not any(agent['disabled'] for agent in row['agents']))
        assert not any(row['overflow'] for row in view['agents'])
        green.call('project', target='project-1')
        green.wait(lambda row: not row['agents'] and 'task-1' in row['task'] and not any(project['disabled'] for project in row['projects']))
        green.call('project', target='project-0')
        green.wait(lambda row: len(row['agents']) == 7 and 'task-0' in row['task'] and not any(agent['disabled'] for agent in row['agents']))
        green.call('notifications')
        green.wait(lambda row: row['notificationChecked'] is False)
        green.close()
        reopened = window(candidate, green_build, 'reopened')
        reopened.wait(lambda row: row['notificationChecked'] is False)
        reopened.close()
        stop()
        with sqlite3.connect(state / 'state.sqlite3') as db:
            assert list(db.execute('SELECT id,data FROM tasks ORDER BY id')) == before
            assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0] == 0
        report['checks'].append(dict(name='窄窗不溢出、跨项目往返、通知设置重开保留、任务原值与用户输入零写入', status='PASS'))
        report['implemented_slice_status'] = 'PASS'
        report['status'] = 'INCOMPLETE'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            for win in windows:
                win.close()
            stop()
            report['cleanup_complete'] = True
        except Exception as error:
            report.update(cleanup_complete=False, cleanup_error=repr(error))
        # Preserve a failed run; a completed slice keeps only its summary.
        if report.get('implemented_slice_status') == 'PASS' and report.get('cleanup_complete'):
            shutil.rmtree(root)
            for build_root in builds:
                shutil.rmtree(build_root)
        else:
            report['retained_fixture'] = str(root)
            report['retained_builds'] = list(map(str, builds))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get('implemented_slice_status') == 'PASS' and report.get('cleanup_complete') else 1


if __name__ == '__main__':
    raise SystemExit(main())
