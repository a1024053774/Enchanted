#!/usr/bin/env python3
"""T-103: real daemon, SQLite, Electron, IPC and terminal replay; no model calls.

Expected projects, task titles and terminal bytes originate in this fixture.
The same no-task Electron startup rejects the baseline and accepts the candidate.
Raw runs stay on the external disk; only the summary/manifest enter the repo.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import selectors
import shutil
import sqlite3
import subprocess
import tempfile
import time
import traceback
import uuid


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class Window:
    def __init__(self, source, driver, build, state, user_data, output, env, owners, runtime, task=None, through_start=True):
        output.mkdir()
        binary = Path(runtime['executable']).resolve(strict=True)
        assert Path(env['ELECTRON_OVERRIDE_DIST_PATH']).resolve(strict=True) == Path(runtime['dist'])
        self.argv = [str(binary), str(driver), '--build', str(build), '--state', str(state),
                     '--user-data', str(user_data), '--output', str(output)]
        if task is not None:
            self.argv += ['--task', task]
        if through_start:
            # start.mjs still launches the real Electron. The manifest selects
            # an observation bootstrap which calls the unmodified product run;
            # no IPC, data or response is replaced.
            entry = output / 'start-entry'; entry.mkdir()
            bootstrap = entry / 'observe.mjs'
            bootstrap.write_text('process.argv.push(...' + json.dumps(['--build', str(build), '--output', str(output)]) + ');\n'
                                 + 'await import(' + json.dumps(driver.as_uri()) + ');\n', encoding='utf-8')
            save(entry / 'build.json', {'main': str(bootstrap)})
            self.argv = ['node', str(source / 'workbench/app/start.mjs'), '--build', str(entry),
                         '--state', str(state), '--user-data', str(user_data)]
            if task is not None:
                self.argv += ['--task', task]
        self.stderr = (output / 'stderr.txt').open('xb')
        self.raw = (output / 'stdout.txt').open('xb')
        self.proc = subprocess.Popen(self.argv, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.stderr, start_new_session=True)
        self.ready, self.closed = {}, False
        owners.append(self)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)
        self.buffer = bytearray()
        self.sequence = 0
        # Preserve ownership before the handshake; an unconfirmed startup must
        # still identify the exact wrapper and argv for controller cleanup.
        save(output / 'launch.json', {'argv': self.argv, 'pid': self.proc.pid, 'handshake': 'pending', 'electron_runtime': runtime})
        self.ready = self.receive()
        save(output / 'ready.json', {'pid': self.proc.pid, 'ready': self.ready})
        assert Path(self.ready['electron_executable']).resolve(strict=True) == binary, self.ready
        assert self.ready['electron_version'] == runtime['version'], self.ready

    def receive(self):
        deadline = time.monotonic() + 30
        while b'\n' not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError('Electron response deadline; retain owned process for controller')
            data = os.read(self.proc.stdout.fileno(), 65536)
            if not data:
                raise RuntimeError('Electron exited; inspect stdout/stderr')
            self.raw.write(data); self.raw.flush(); self.buffer.extend(data)
        line, _, self.buffer = self.buffer.partition(b'\n')
        return json.loads(line)

    def call(self, command, **fields):
        self.sequence += 1
        self.proc.stdin.write((json.dumps({'id': self.sequence, 'command': command, **fields}) + '\n').encode())
        self.proc.stdin.flush()
        value = self.receive()
        assert value.get('id') == self.sequence and value.get('ok') is True, value
        return value.get('value')

    def wait(self, predicate, expected=None):
        deadline = time.monotonic() + 20
        while True:
            value = self.call('inspect')
            if predicate(value):
                return value
            if time.monotonic() >= deadline:
                raise AssertionError({'expected': expected, 'UI condition not reached': value})
            time.sleep(.1)

    def close(self):
        if self.closed:
            return
        if not self.ready and self.proc.poll() is None:
            raise RuntimeError('Electron startup unconfirmed; preserve process and fixture for controller')
        if self.ready.get('ready') and self.proc.poll() is None:
            self.call('close')
        self.proc.wait(timeout=10)
        assert self.proc.returncode == (0 if self.ready.get('ready') else 1), self.proc.returncode
        self.selector.close(); self.proc.stdin.close(); self.proc.stdout.close()
        self.stderr.close(); self.raw.close()
        self.closed = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--electron-dist', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, baseline, out = args.source.resolve(), args.baseline.resolve(), args.output.resolve()
    disk = Path('/Volumes/WD-Elements')
    if not disk.is_mount() or not out.is_relative_to(disk):
        raise RuntimeError('真实外置盘未挂载或输出不在外置盘，停止')
    out.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='a2at103-', dir='/tmp')).resolve()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env.pop('NODE_OPTIONS', None)
    shared_dist = args.electron_dist.resolve(strict=True)
    assert not shared_dist.is_relative_to('/Volumes') and shared_dist.stat().st_dev != disk.stat().st_dev
    assert shared_dist.stat().st_dev == (source / 'workbench').stat().st_dev, 'Electron dist must be on the internal source disk'
    env['ELECTRON_OVERRIDE_DIST_PATH'] = str(shared_dist)
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT='2',
               GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T103 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T103 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
               A2A_BUILD_VOLUME=str(disk))
    (out / 'tmp').mkdir()
    env.update(TMPDIR=str(out / 'tmp'), TMP=str(out / 'tmp'), TEMP=str(out / 'tmp'))
    commands, checks, screenshots = [], [], []
    summary = {'status': 'INCOMPLETE', 'task': 'T-103', 'attempt': 'a1', 'checks': checks,
               'source': str(source), 'baseline': str(baseline), 'fixture': str(fixture),
               'model_calls': 0, 'screenshots': screenshots, 'archive': str(out)}
    active, owned_windows = [], []
    runtime = None

    def run(argv, cwd=source, call_env=env, timeout=120):
        result = subprocess.run([str(x) for x in argv], cwd=cwd, env=call_env,
                                capture_output=True, text=True, timeout=timeout)
        commands.append({'argv': [str(x) for x in argv], 'cwd': str(cwd), 'exit': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        save(out / 'commands.json', commands)
        return result

    def ok(argv, **kwargs):
        result = run(argv, **kwargs)
        if result.returncode:
            raise RuntimeError({'setup_or_command_failure': commands[-1]})
        return result

    def call(root, state, local_env, command, *fields):
        result = ok(['node', root / 'workbench/src/gates/cli.ts', '--state', state, command, *fields], call_env=local_env)
        value = json.loads(result.stdout)
        assert value.get('ok') is True, value
        return value

    def check(name):
        checks.append({'name': name, 'status': 'PASS'})

    def build(root, label):
        result = ok(['node', root / 'workbench/app/build.mjs', '--slot', 't103-' + label + '-' + uuid.uuid4().hex[:10]], cwd=root)
        value = json.loads(result.stdout.strip().splitlines()[-1])
        save(out / (label + '-build.json'), value)
        return Path(value['out'])

    def daemon(root, label):
        state = fixture / (label + '-state')
        local_env = dict(env, A2A_OPERATOR_CREDENTIAL=str(fixture / (label + '-operator.json')))
        pid = call(root, state, local_env, 'daemon_start')['pid']
        active.append((root, state, local_env, pid))
        return state, local_env

    def populate(root, state, local_env):
        nonce = uuid.uuid4().hex[:6]
        rows = []
        for p in range(2):
            repo = fixture / (state.name + '-repo-' + str(p)); repo.mkdir()
            ok(['git', 'init', '-b', 'main', repo])
            (repo / 'value.txt').write_text('原始夹具\n', encoding='utf-8')
            (repo / 'criterion.py').write_text("from pathlib import Path; assert Path('value.txt').read_text() == '原始夹具\\n'\n", encoding='utf-8')
            ok(['git', '-C', repo, 'add', 'value.txt', 'criterion.py'])
            ok(['git', '-C', repo, 'commit', '-m', 'T103 independent fixture'])
            for t in range(2):
                task = f'task-{p}-{t}-{nonce}'
                title = f'项目{p}的任务{t} · {nonce}' if t == 0 else f'校对<标签>与长中文任务标题是否完整显示 · {p}-{nonce}'
                card = {'id': task, 'source': None, 'goal': '选择现有项目中的任务',
                        'non_goals': ['不调用模型'], 'paths': {'allow': ['value.txt'], 'deny': []},
                        'oracle_paths': ['criterion.py'], 'completion_conditions': [{'argv': ['python3', 'criterion.py']}],
                        'red_commands': [], 'task_type': '前端界面', 'repair_target': None, 'complexity': 'M',
                        'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'},
                        'base_commit': None, 'writer': None}
                file = fixture / (task + '.json'); save(file, card)
                call(root, state, local_env, 'card_save', '--task', task, '--card', file, '--expected-version', '0')
                current = call(root, state, local_env, 'create', '--task', task, '--repo', repo,
                               '--branch', 'refs/heads/main', '--card-version', '1',
                               '--project', f'project-{p}-{nonce}', '--title', title)['task']
                if p == 1 and t == 1:
                    current = call(root, state, local_env, 'revoke', '--task', task, '--reason', '夹具状态反例')['task']
                # Historical traces are fixture inputs. No launch command, CLI,
                # fake API, or model is executed to manufacture terminal bytes.
                launch = 'fixture-' + uuid.uuid4().hex
                record = {'id': launch, 'task': task, 'project': current['project_id'], 'attempt': 'historical-a1',
                          'session': 'historical-session', 'fence': 1, 'spec_rev': 1, 'thread': 'thread-' + launch,
                          'role': 'worker', 'preset': None, 'cli': 'fixture-only', 'cli_version': '历史记录夹具',
                          'model_requested': '无模型', 'created_at': '2026-10-19T00:00:00Z'}
                trace = f'只读历史输出 {task} / {uuid.uuid4().hex[:8]}\r\n'
                directory = state / 'traces' / launch; directory.mkdir(parents=True)
                (directory / 'pty.raw').write_bytes(trace.encode())
                with closing(sqlite3.connect(state / 'state.sqlite3')) as db:
                    db.execute('INSERT INTO launch_records(id,task,attempt,data) VALUES (?,?,?,?)',
                               (launch, task, record['attempt'], json.dumps(record)))
                    db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)',
                               ('2026-10-19T00:00:00Z', 'pane_layout_opened', launch, task, record['attempt'],
                                json.dumps({'position': 0, 'native_session': None, 'resume_argv': None})))
                    db.commit()
                rows.append({'task_id': task, 'project_id': current['project_id'], 'title': title,
                             'state': current['state'], 'launch': launch, 'trace': trace.strip()})
        save(out / (state.name + '-expected.json'), rows)
        return rows

    def window(root, build_path, state, local_env, label, task=None):
        return Window(root, source / 'workbench/tests/t103_picker_driver.mjs', build_path, state,
                      fixture / (label + '-ui'), out / label, local_env, owned_windows, runtime, task,
                      through_start=label != 'red-no-task')

    def capture(win, label, name, **kwargs):
        value = win.call('capture', name=name, **kwargs)
        screenshots.append(str(out / label / (name + '.png')))
        save(out / label / (name + '.json'), value)

    win = None
    try:
        summary['baseline_install'] = json.loads((baseline / 'baseline-install.json').read_text(encoding='utf-8'))
        runtime = summary['baseline_install']['electron_runtime']
        assert Path(runtime['dist']).resolve(strict=True) == shared_dist
        assert runtime['baseline_package_version'] == runtime['candidate_package_version'] == runtime['version'] == runtime['binary_probe_version']
        summary['electron_runtime'] = runtime
        summary['driver_startup_check'] = json.loads((baseline / 'driver-startup.json').read_text(encoding='utf-8'))
        assert summary['driver_startup_check']['status'] == 'PASS', 'Driver entry evaluation remains blocked'
        summary['keyboard_entry_check'] = json.loads((baseline / 'keyboard-entry.json').read_text(encoding='utf-8'))
        assert summary['keyboard_entry_check']['status'] == 'PASS', 'Keyboard injection contract failed'
        summary['electron_installation'] = json.loads((baseline / 'worktree-electron/result.json').read_text(encoding='utf-8'))
        assert summary['electron_installation']['status'] == 'PASS', 'Internal Electron install preflight failed'
        assert Path(summary['electron_installation']['executable']).resolve(strict=True) == Path(runtime['executable']).resolve(strict=True)
        summary['revision'] = ok(['git', 'rev-parse', 'HEAD']).stdout.strip()
        (out / 'candidate.diff').write_text(ok(['git', 'diff', 'HEAD', '--', 'workbench']).stdout, encoding='utf-8')
        summary['source_files'] = ['workbench/' + name for name in [
            'README.md', 'app/main.ts', 'app/preload.ts', 'app/renderer.tsx', 'app/start.mjs', 'app/style.css',
            'src/daemon.ts', 'src/gates/cli.ts', 'src/gates/core.ts',
            'tests/run_t103_picker.py', 'tests/t103_picker_driver.mjs',
            'tests/test_t103_driver_startup.mjs', 'tests/test_t103_keyboard_entry.mjs']]
        summary['source_files'] += ['evidence/2026-10-19-batch17/T-103/' + name for name in
                                    ['RUN-OUTSIDE-02-E2E.sh', 'RUN-OUTSIDE-04-ELECTRON.sh']]
        for name in summary['source_files']:
            target = out / 'source-snapshot' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, target)
        red_build, green_build = build(baseline, 'red'), build(source, 'green')
        startup_red = run(['node', baseline / 'workbench/app/start.mjs', '--build', red_build])
        assert startup_red.returncode == 1 and '--build DIST --task ID are required' in startup_red.stderr
        check('已知坏版本：真实 start.mjs 无 task 入口退出 1')
        red_state, red_env = daemon(baseline, 'red')
        red_rows = populate(baseline, red_state, red_env)
        win = window(baseline, red_build, red_state, red_env, 'red-no-task')
        assert win.ready.get('startup_error') == 'Error: Absolute data paths and a task are required', win.ready
        win.close(); win = None
        check('已知坏版本：同一真实 Electron 无 task 入口按预期拒绝')
        win = window(baseline, red_build, red_state, red_env, 'red-fixed-task', red_rows[0]['task_id'])
        red_view = win.wait(lambda value: bool(value['panes']) and value['panes'][0]['offset'] > 0)
        assert red_view['projects'] == [] and red_view['tasks'] == [], red_view
        capture(win, 'red-fixed-task', 'red-missing-list')
        win.close(); win = None
        check('已知坏版本：固定任务可读取，项目与任务列表缺失')
        state, local_env = daemon(source, 'green')
        rows = populate(source, state, local_env)
        def db_bytes():
            return {path.name: path.read_bytes() for path in state.iterdir()
                    if path.name.endswith(('.sqlite3', '.sqlite3-wal'))}
        before = db_bytes()
        projects = call(source, state, local_env, 'projects_list')['projects']
        assert projects == [{'project_id': project} for project in sorted({row['project_id'] for row in rows})]
        for project in projects:
            actual = call(source, state, local_env, 'tasks_list', '--project', project['project_id'])['tasks']
            expected = [{key: row[key] for key in ['task_id', 'project_id', 'title', 'state']}
                        for row in rows if row['project_id'] == project['project_id']]
            assert actual == expected, (actual, expected)
        assert call(source, state, local_env, 'tasks_list', '--project', 'absent-project')['tasks'] == []
        invalid = run(['node', source / 'workbench/src/gates/cli.ts', '--state', state,
                       'tasks_list', '--project', '../invalid'], call_env=local_env)
        assert invalid.returncode == 1 and json.loads(invalid.stdout)['error'] == 'invalid_id'
        after = db_bytes()
        assert before == after, 'List commands changed SQLite or WAL bytes'
        save(out / 'readonly-bytes.json', {'equal': True, 'files': {name: len(data) for name, data in before.items()},
                                          'compared': 'full bytes, not hashes; excludes SQLite shared-memory lock file'})
        check('真实命令列表与夹具一致，空项目及无效项目反例，库与 WAL 全字节不变')
        win = window(source, green_build, state, local_env, 'green-no-task')
        view = win.wait(lambda value: value['busy'] == 'false' and len(value['tasks']) == 4)
        assert view['heading'] == '选择任务' and view['panes'] == [] and view['node'] == 'undefined', view
        assert set(view['projects']) == {row['project_id'] for row in rows}
        assert [item['id'] for item in view['tasks']] == [row['task_id'] for row in rows]
        for item, row in zip(view['tasks'], rows):
            assert row['title'] in item['text'], (item, row)
        capture(win, 'green-no-task', 'green-picker')
        check('真实 Electron 无 task 进入选择页，IPC 列表与两项目四任务一致')
        previous = None
        for index in [0, 2, 1, 3, 0]:
            row = rows[index]
            win.call('keyboard-select' if index == 2 else 'select', task=row['task_id'])
            view = win.wait(lambda value: len(value['panes']) == 1 and value['panes'][0].get('task') == row['task_id']
                            and row['trace'] in value['panes'][0]['terminal'],
                            expected={'task': row['task_id'], 'terminal_text': row['trace'], 'panes': 1})
            pane = view['panes'][0]
            assert pane['launch'] == row['launch'] and pane['input'] == 'false'
            assert view['heading'] == row['title'] and [item['id'] for item in view['tasks'] if item['current'] == 'page'] == [row['task_id']]
            if previous:
                assert win.call('bridge', operation='snapshot', args=[previous])['rejected'] is True
                assert win.call('bridge', operation='input', args=[previous, 'STALE'])['rejected'] is True
            previous = pane['key']
        capture(win, 'green-no-task', 'green-switched')
        capture(win, 'green-no-task', 'green-narrow', width=900, height=650)
        assert win.call('bridge', operation='selectTask', args=['absent-task'])['rejected'] is True
        assert win.call('inspect')['heading'] == rows[0]['title']
        check('跨项目往返与键盘切换，真实终端内容随任务变化，旧 key 与不存在任务被拒绝')
        # No product deletion command exists. Remove only this isolated fixture
        # row; preserve the full pre-removal row and keep historical membership.
        with closing(sqlite3.connect(state / 'state.sqlite3')) as db:
            original = db.execute('SELECT data FROM tasks WHERE id=?', (rows[0]['task_id'],)).fetchone()[0]
            save(out / 'removed-fixture-row.json', json.loads(original))
            db.execute('DELETE FROM tasks WHERE id=?', (rows[0]['task_id'],)); db.commit()
        win.call('refresh')
        view = win.wait(lambda value: value['busy'] == 'false' and len(value['tasks']) == 3 and not value['panes'])
        assert rows[0]['task_id'] not in [item['id'] for item in view['tasks']]
        assert view['heading'] == '选择任务' and not view['alerts'], view
        capture(win, 'green-no-task', 'green-removed')
        check('隔离库移除所选任务后刷新消失、清空窗格；历史归属记录不使其复活')
        win.close(); win = None
        win = window(source, green_build, state, local_env, 'green-explicit-task', rows[2]['task_id'])
        # A mounted SessionPane has no task attribute until its first snapshot.
        # Loading is not success; keep waiting for this task and its exact trace.
        view = win.wait(lambda value: len(value['panes']) == 1 and value['panes'][0].get('task') == rows[2]['task_id']
                        and rows[2]['trace'] in value['panes'][0]['terminal'],
                        expected={'task': rows[2]['task_id'], 'terminal_text': rows[2]['trace'], 'panes': 1})
        assert view['heading'] == rows[2]['title'] and view['panes'][0]['launch'] == rows[2]['launch'], view
        capture(win, 'green-explicit-task', 'green-explicit-task')
        win.close(); win = None
        check('显式 task 启动仍直接显示原任务窗格')
        empty_state, empty_env = daemon(source, 'empty')
        win = window(source, green_build, empty_state, empty_env, 'green-empty')
        view = win.wait(lambda value: value['busy'] == 'false' and '还没有项目' in value['text'])
        assert not view['tasks'] and not view['panes'] and not view['alerts'], view
        capture(win, 'green-empty', 'green-empty')
        win.close(); win = None
        check('空库显示中文空状态，无异常或窗格')
        with closing(sqlite3.connect(state / 'state.sqlite3')) as db:
            assert db.execute("SELECT count(*) FROM orchestration_events WHERE type IN ('pane_started','pane_restored','window_opened','terminal_input_written')").fetchone()[0] == 0
        assert all((source / name).read_bytes() == (out / 'source-snapshot' / name).read_bytes()
                   for name in summary['source_files']), 'Candidate changed during this run'
        summary['status'] = 'PASS'
    except Exception as error:
        summary.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            for owned in owned_windows:
                owned.close()
            for root, state, local_env, pid in reversed(active):
                call(root, state, local_env, 'daemon_stop')
                deadline = time.monotonic() + 10
                while True:
                    probe = run(['/bin/ps', '-p', str(pid), '-o', 'pid=,command='], timeout=5)
                    if probe.returncode not in (0, 1) or probe.stderr.strip():
                        raise RuntimeError('Cannot confirm fixture daemon exit')
                    if not (state / 'daemon.pid').exists() and probe.returncode == 1 and not probe.stdout.strip():
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f'Daemon stop unconfirmed: {pid}')
                    time.sleep(.1)
                Path(local_env['A2A_OPERATOR_CREDENTIAL']).unlink()
            archived = out / 'fixtures'
            shutil.copytree(fixture, archived)
            def inventory(directory):
                return sorted((str(path.relative_to(directory)), path.stat().st_size) for path in directory.rglob('*') if path.is_file())
            original_files = inventory(fixture)
            assert original_files == inventory(archived), 'Fixture archive file counts/bytes differ'
            summary['fixture_archive'] = {'original': str(fixture), 'archive': str(archived),
                                          'files': len(original_files), 'bytes': sum(size for _, size in original_files)}
            shutil.rmtree(fixture)
        except Exception as error:
            summary.update(status='INCOMPLETE', cleanup_error=repr(error), cleanup_traceback=traceback.format_exc())
        save(out / 'run.json', summary)
        destination = source / 'evidence/2026-10-19-batch17/T-103'
        save(destination / (out.name + '-summary.json'), summary)
        save(destination / (out.name + '.archive.json'), {'original': str(fixture), 'archive': str(out),
             'bytes': sum(path.stat().st_size for path in out.rglob('*') if path.is_file()),
             'replay': 'bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-02-E2E.sh'})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
