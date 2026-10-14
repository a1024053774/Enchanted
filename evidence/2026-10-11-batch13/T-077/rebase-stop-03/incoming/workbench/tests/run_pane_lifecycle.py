"""One real Codex turn exercises the real PTY and Electron lifecycle.

Only the controller runs this script outside the sandbox. A timeout or missing
PTY output stops the run. The script never retries a turn or invents PTY bytes.
"""
import argparse
import base64
import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import uuid

from command_evidence import CommandLog, command_json
from electron_client import ElectronClient
from fixture_artifacts import archive_and_cleanup
from turn_accounting import read_main_turns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--budget', type=Path, required=True)
    args = parser.parse_args()
    source, repository = args.source.resolve(), args.repository.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    fixture = Path(tempfile.mkdtemp(prefix='a4live-', dir='/tmp')).resolve()
    repo, state, home = fixture / 'repo', fixture / 'state', fixture / 'codex-home'
    repo.mkdir(); home.mkdir(mode=0o700)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env.update(GIT_AUTHOR_NAME='T0754 lifecycle fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T0754 lifecycle fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    git_env = {**env, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
               'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'core.hooksPath', 'GIT_CONFIG_VALUE_0': os.devnull,
               'GIT_CONFIG_KEY_1': 'commit.gpgsign', 'GIT_CONFIG_VALUE_1': 'false'}
    cli = ['node', source / 'workbench/src/gates/cli.ts', '--state', state]
    task, project = 'T-075-4', 'a2a-lifecycle-' + uuid.uuid4().hex[:8]
    started = False
    cleanup_pids = set()
    windows = []
    thread = launch = attempt = request_directory = None
    verdict = {'status': 'INCOMPLETE', 'task': task, 'fixture': str(fixture), 'state': str(state),
               'real_turns_reserved': 0, 'observed_main_turns': None, 'evidence_source': 'PTY trace bytes, including Codex TUI redraws',
               'model_requested': 'gpt-6.1-sol', 'effort_requested': 'xhigh', 'service_tier_requested': None}
    commands = CommandLog(output)

    def save(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def journal(kind, **value):
        with (output / 'lifecycle.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                     'kind': kind, **value}, ensure_ascii=False) + '\n')

    def run(argv, *, check=True, command_env=None, timeout=60):
        result = commands.run(argv, cwd=source, env=command_env or env, timeout=timeout)
        if check and result.returncode:
            raise RuntimeError({'command_failed': result.evidence})
        return result

    def call(command, *values, error=None, check=True):
        result = run([*cli, command, *values], check=check and error is None)
        expected_exits = (1,) if error is not None else (0,) if check else (0, 1)
        assert result.returncode in expected_exits, result.evidence
        value = command_json(result)
        if error is not None:
            assert result.returncode == 1 and value.get('error') == error, value
        elif check:
            assert value.get('ok') is True, value
        return value

    def git(*values):
        return run(['git', '-C', repo, *values], command_env=git_env).stdout.strip()

    def gate_readback(label):
        value = call('status', '--task', task)['task']
        with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
            stored = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (task,)).fetchone()[0])
            counts = {name: db.execute('SELECT count(*) FROM ' + name).fetchone()[0]
                      for name in ['launch_records', 'dispatch_records', 'user_inputs']}
        assert stored == value
        save(label + '.json', {'gate': value, 'counts': counts})
        return value, counts

    def processes(label):
        info = call('pane_process_info', '--thread', thread)
        cleanup_pids.update(row['pid'] for row in info['processes'])
        needed = {info['shell_pid']}
        if info['leader']:
            needed.add(info['leader'])
        actual = run(['/bin/ps', '-o', 'pid=,ppid=,pgid=,command=', '-p', ','.join(map(str, sorted(needed)))])
        ids = {int(line.split()[0]) for line in actual.stdout.splitlines() if line.strip()}
        assert needed <= ids, ('advertised PIDs must exist', needed, actual.stdout)
        save(label + '.json', {'backend': info, 'independent_ps': actual.stdout})
        return info

    def close_window(window):
        window.close()
        windows.remove(window)
        journal('window_closed', pid=window.process.pid, exit=window.process.returncode)

    def trace_totals(label):
        before = trace.stat().st_size
        response = call('pane_output', '--launch', launch['id'], '--offset', '0', '--max-bytes', '1')
        after = trace.stat().st_size
        assert before <= response['total_bytes'] <= after, 'CLI and file sizes must agree within the append interval'
        with trace.open('rb') as stream:
            assert base64.b64decode(response['data_base64'], validate=True) == stream.read(response['next_offset'])
        value = {'direct_before': before, 'backend_total': response['total_bytes'], 'direct_after': after,
                 'launch': response['launch']}
        journal('trace_totals', label=label, **value)
        return value

    def observe_growth(minimum, label, timeout=30):
        deadline = time.monotonic() + timeout
        while True:
            current = call('pane_status', '--thread', thread)
            if current['failed']:
                raise RuntimeError(current)
            totals = trace_totals(label)
            if current['turn'] and totals['backend_total'] > minimum and totals['direct_before'] > minimum:
                journal('growth_observed', label=label, minimum=minimum, pane_state=current['state'], totals=totals)
                return totals
            if time.monotonic() >= deadline:
                raise RuntimeError({'no_pty_byte_growth': label, 'minimum': minimum, 'totals': totals,
                                    'action': 'stop; no alternative output channel'})
            time.sleep(0.25)

    def compare_window(window, label, minimum):
        with window.output_checkpoint(minimum) as checkpoint:
            target = checkpoint['highwater']
            inspection = checkpoint['view']
            save(label + '-checkpoint.json', checkpoint)
            expected = trace.read_bytes()[:target]
            actual = bytearray()
            for line in (window.output / 'received.ndjson').read_bytes().splitlines(keepends=True):
                assert line.endswith(b'\n'), 'Checkpoint must leave only complete output responses'
                chunk = json.loads(line)
                data = base64.b64decode(chunk['data_base64'], validate=True)
                assert chunk['launch'] == launch['id']
                assert chunk['start_offset'] == len(actual)
                assert chunk['next_offset'] == len(actual) + len(data)
                actual.extend(data)
            assert len(actual) == inspection['offset'] == target >= minimum
            with (output / (label + '-trace.bin')).open('xb') as stream:
                stream.write(expected)
            with (output / (label + '-window.bin')).open('xb') as stream:
                stream.write(actual)
            assert bytes(actual) == expected, 'Window replay must equal the trace byte for byte'
            journal('window_bytes_equal', label=label, minimum=minimum, compared_bytes=target,
                    renderer_applied_offset=inspection['offset'])
            return inspection

    def stopped_pids(label):
        deadline = time.monotonic() + 10
        while True:
            result = run(['/bin/ps', '-o', 'pid=,ppid=,pgid=,command=', '-p', ','.join(map(str, sorted(cleanup_pids)))], check=False)
            assert result.returncode in (0, 1) and not result.stderr.strip(), result
            if not result.stdout.strip() and not (state / 'daemon.pid').exists():
                save(label + '.json', {'pids': sorted(cleanup_pids), 'remaining': result.stdout, 'confirmed_exited': True})
                return
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned daemon or pane processes did not exit; retain the isolated home')
            time.sleep(0.1)

    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External build volume is not mounted')
        build = command_json(run(['node', source / 'workbench/app/build.mjs', '--slot', 't0754-live-' + fixture.name], timeout=120))
        save('build.json', build)
        git('init', '-b', 'main')
        workload = '#!/bin/zsh\nset -eu\n/bin/sleep 90\n'
        (repo / 'wait.zsh').write_text(workload, encoding='utf-8')
        git('add', 'wait.zsh')
        git('commit', '-m', 'Ordinary long-running lifecycle fixture')
        base = git('rev-parse', 'HEAD')
        shutil.copyfile(Path.home() / '.codex/auth.json', home / 'auth.json')
        (home / 'auth.json').chmod(0o600)
        (home / 'config.toml').write_text(f'[projects.{json.dumps(str(repo))}]\ntrust_level="trusted"\n', encoding='utf-8')
        (home / 'rules').mkdir()
        (home / 'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                                'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding='utf-8')
        ticket = source / '.project-map/tickets/T-075-tracer-bullet-daemon-gate-pane.md'
        ready_rev = int(next(line.split(':', 1)[1] for line in ticket.read_text(encoding='utf-8').splitlines() if line.startswith('ready_rev:')))
        assert ready_rev == 4, 'The fixture must use the approved ticket revision'
        config = {'codex_bin': str(Path(shutil.which('codex')).resolve()), 'codex_home': str(home),
                  'role_card': str(source / '.project-map/roles/worker.md'),
                  'role_card_revision': run(['git', '-C', repository, 'log', '-1', '--format=%H', '--', '.project-map/roles/worker.md']).stdout.strip(),
                  'code_revision': run(['git', '-C', repository, 'rev-parse', 'HEAD']).stdout.strip(),
                  'source_snapshot': str(output.parent / 'candidate-source.tar.gz'),
                  'hook_authorization': 'T-075-4 controller-decision-01 section 4; unchanged three hooks',
                  'turn_limit': 1, 'turn_authorization': 'T-075-4 decision02 / controller #41; one additional turn; cumulative cap 2 of 4'}
        save('launch-config.json', config)
        start = call('daemon_start', '--launch-config', output / 'launch-config.json'); started = True
        cleanup_pids.add(start['pid'])
        assert os.getpgid(start['pid']) == os.getsid(start['pid']) == start['pid']
        assert os.getsid(start['pid']) != os.getsid(0)
        card = {'id': task, 'source': {'ticket': str(ticket), 'ready_rev': ready_rev},
                'goal': '这是独立的窗口生命周期和运行中断验收夹具，不是编排产品开发任务。'
                        '只在当前 worktree 用执行工具运行 /bin/zsh -f wait.zsh。脚本已经准备好，只执行一个90秒的sleep；不读取或改写脚本。'
                        '执行工具每次等待约 1000ms；脚本未退出就继续读取同一个工具会话的输出，每次等待不超过10秒。'
                        '保持这个主回合运行，等待执行主控从外部停止后台来制造中断。'
                        '这张夹具任务不进入完成交付阶段：不 git add、不 git commit、不 submit、不写交付请求文件。'
                        '不要查看凭据、全局配置或a2a源码，不发网络请求，不启动子agent，不主动结束主回合。',
                'non_goals': ['不实现产品，不完成或提交这张中断夹具任务，不操作任何其他会话'],
                'paths': {'allow': ['scratch/'], 'deny': ['wait.zsh']},
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c', 'raise SystemExit(23)']}],
                'red_commands': [], 'task_type': '测试', 'repair_target': None, 'complexity': 'M',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}, 'base_commit': None, 'writer': None}
        save('card.json', card)
        call('card_save', '--task', task, '--card', output / 'card.json', '--expected-version', '0')
        call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1',
             '--project', project, '--title', 'T-075-4 · 真实窗格与中断验证')
        attempt = call('dispatch', '--task', task, '--runtime-mode', 'workspace-write')['attempt']
        thread = attempt['thread_id']; save('attempt.json', attempt)
        pane = call('pane_status', '--thread', thread)
        launch = call('launch_show', '--launch', pane['launch'])['launch']; save('launch-record.json', launch)
        assert launch['model_requested'] == 'gpt-6.1-sol' and launch['effort_requested'] == 'xhigh'
        assert launch['service_tier_requested'] is None and launch['turn_limit'] == 1
        assert not any(arg.startswith('service_tier=') for arg in launch['argv'])
        request_directory = Path(launch['request_dir'])
        trace = state / 'traces' / launch['id'] / 'pty.raw'
        deadline = time.monotonic() + 30
        while True:
            info = processes('initial-processes')
            if info['leader'] and not info['failed']:
                break
            if info['failed'] or time.monotonic() >= deadline:
                raise RuntimeError({'foreground_not_confirmed': info})
            time.sleep(0.2)
        shell_pid, leader_pid = info['shell_pid'], info['leader']
        before_gate, before_counts = gate_readback('before-release-gate')
        assert before_gate['state'] == 'claimed' and before_counts['launch_records'] == 1
        first = ElectronClient(source, Path(build['out']), state, task, fixture / 'ui', output / 'window-first', env, launch=launch['id'])
        windows.append(first)
        first.wait(lambda value: value['gate'] == 'claimed' and value['state'] == 'unknown')
        first.call('capture', name='initial-unknown')
        with args.budget.open('a+', encoding='utf-8') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX); stream.seek(0)
            entries = [json.loads(line) for line in stream if line.strip()]
            reserved = sum(item.get('reserved', 0) for item in entries)
            if reserved + 1 > 3:
                raise RuntimeError('Controller #43 allows one additional turn, for a cumulative reservation of three')
            stream.seek(0, 2)
            stream.write(json.dumps({'kind': 'reserve', 'reserved': 1, 'launch': launch['id'], 'output': str(output),
                                     'authorization': 'controller #43', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}) + '\n')
            stream.flush(); os.fsync(stream.fileno())
        verdict['real_turns_reserved'] = 1; save('verdict.json', verdict)
        initial_bytes = trace.stat().st_size
        call('pane_release', '--thread', thread, '--reason', '主控 #43：最多增加一个回合，以PTY字节增长取证')
        initial_growth = observe_growth(initial_bytes, 'turn-active', timeout=60)
        highwater = initial_growth['backend_total']
        view = compare_window(first, 'before-close', highwater)
        assert view['gate'] == 'claimed'
        assert view['terminal'].strip(), 'The real Codex TUI must appear in xterm'
        first.call('capture', name='live-before-close')
        before_process = processes('before-close-processes')
        before_close = trace_totals('before-close')
        close_window(first)
        closed_start = trace_totals('electron-exited')
        time.sleep(2)
        before_reopen = observe_growth(closed_start['direct_after'], 'before-reopen')
        closed_size = before_reopen['backend_total']
        assert closed_size > closed_start['direct_after'] >= before_close['backend_total']
        after_process = processes('while-closed-processes')
        assert (after_process['shell_pid'], after_process['leader']) == (shell_pid, leader_pid)
        delta = call('pane_output', '--launch', launch['id'], '--offset', str(closed_start['direct_after']), '--max-bytes', '65536')
        bytes_delta = base64.b64decode(delta['data_base64'], validate=True)
        assert bytes_delta and bytes_delta == trace.read_bytes()[closed_start['direct_after']:delta['next_offset']]
        save('closed-output-readback.json', {'before_close': before_close, 'electron_exited': closed_start,
                                           'before_reopen': before_reopen, 'delta': delta,
                                           'before_process': before_process, 'after_process': after_process})
        second = ElectronClient(source, Path(build['out']), state, task, fixture / 'ui', output / 'window-reopened', env, launch=launch['id'])
        windows.append(second)
        backfill_view = compare_window(second, 'reopened-backfill', closed_size)
        assert backfill_view['terminal'].strip(), 'Replayed Codex TUI content must be visible'
        second.call('capture', name='reopened-backfill')
        following_totals = observe_growth(closed_size, 'after-reopen')
        following_size = following_totals['backend_total']
        view = compare_window(second, 'reopened-live', following_size)
        assert view['terminal'].strip() and view['gate'] == 'claimed'
        assert (call('pane_status', '--thread', thread)['launch']) == launch['id']
        second.call('readonly-input')
        second.call('capture', name='live-after-reopen')
        call('pane_output', '--launch', launch['id'], '--offset=-1', error='invalid_output_offset')
        call('pane_output', '--launch', launch['id'], '--offset', '0', '--max-bytes', '65537', error='invalid_output_limit')
        call('pane_output', '--launch', launch['id'], '--offset', str(2**52), error='output_offset_past_end')
        pre_stop_gate, pre_stop_counts = gate_readback('before-restart-gate')
        assert pre_stop_gate == before_gate and pre_stop_counts == before_counts
        assert not pre_stop_counts['user_inputs'], 'Read-only keyboard and paste must not create user input'
        assert b'READ_ONLY_SENTINEL' not in trace.read_bytes()
        assert Path(attempt['workspace'], 'wait.zsh').read_text(encoding='utf-8') == workload
        assert not list(request_directory.glob('*.json')), 'The interruption fixture must not request delivery'
        close_window(second)
        processes('before-daemon-stop-processes')
        save('stop-first-daemon.json', call('daemon_stop')); started = False
        stopped_pids('stopped-original-processes')
        stopped_trace = trace.read_bytes()
        with (output / 'pty-before-restart.raw').open('xb') as stream:
            stream.write(stopped_trace)
        third = ElectronClient(source, Path(build['out']), state, task, fixture / 'ui', output / 'window-restart', env, launch=launch['id'])
        windows.append(third)
        third.wait(lambda value: '后台未连接' in value['text'])
        third.call('capture', name='daemon-offline')
        restart = call('daemon_start'); started = True; cleanup_pids.add(restart['pid'])
        assert restart['pid'] != start['pid']
        snapshot = call('workbench_snapshot', '--task', task, '--launch', launch['id'])
        status = call('pane_status', '--thread', thread)
        recorded_launch = call('launch_show', '--launch', launch['id'])
        save('restart-readback.json', {'snapshot': snapshot, 'pane_status': status, 'launch_show': recorded_launch})
        assert status['state'] == 'unknown' and status['lifecycle'] == 'interrupted' and status['historical'] is True
        assert status['launch'] == launch['id'] and status['queued'] == [] and status['active'] is None
        assert recorded_launch['launch'] == launch
        after_gate, after_counts = gate_readback('after-restart-gate')
        assert after_gate == pre_stop_gate and after_counts == pre_stop_counts
        assert trace.read_bytes() == stopped_trace, 'Restart must not append automatic worker output'
        events = call('orchestration_events')['events']; save('orchestration-events.json', events)
        restored = [item for item in events if item['type'] == 'pane_recovered' and item['launch'] == launch['id']]
        assert len(restored) == 1 and restored[0]['data']['lifecycle'] == 'interrupted'
        assert len([item for item in events if item['type'] == 'pane_started']) == 1
        assert len([item for item in events if item['type'] == 'turn_submit_intent']) == 1
        with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
            stored_recovery = [json.loads(row[0]) for row in db.execute(
                "SELECT data FROM orchestration_events WHERE type='pane_recovered' AND launch=?", (launch['id'],))]
        assert stored_recovery == [restored[0]['data']]
        children = run(['pgrep', '-P', str(restart['pid'])], check=False)
        assert children.returncode == 1 and not children.stdout.strip() and not children.stderr.strip(), 'Restart must not create a worker child'
        third.call('reconnect')
        third.wait(lambda value: value['lifecycle'] == 'interrupted' and value['state'] == 'unknown' and value['gate'] == 'claimed')
        compare_window(third, 'after-restart-history', len(stopped_trace))
        third.call('capture', name='interrupted-original-attempt')
        time.sleep(1)
        assert trace.read_bytes() == stopped_trace
        # The launch ID and native session ID are different identities.
        native_file = state / 'traces' / launch['id'] / 'native.jsonl'
        native = [json.loads(line) for line in native_file.read_text(encoding='utf-8').splitlines()]
        native_id = next(item['payload']['id'] for item in native if item['type'] == 'session_meta' and item['payload']['source'] == 'cli')
        primary = [item['data']['record'] for item in events if item['type'] == 'native_record'
                   and item['data']['file'].endswith(native_id + '.jsonl')]
        turns = {item['payload']['turn_id'] for item in primary if item['type'] == 'event_msg' and item['payload']['type'] == 'task_started'}
        verdict['observed_main_turns'] = len(turns)
        assert len(turns) == 1
        contexts = [item['payload'] for item in primary if item['type'] == 'turn_context']
        assert contexts and all(item['model'] == 'gpt-6.1-sol' and item['approval_policy'] == 'never'
                                and item['sandbox_policy'].get('network_access') is False for item in contexts)
        assert not any(item['type'] == 'permission_wait' for item in events)
        assert git('rev-parse', 'HEAD') == base
        save('native-turn-readback.json', {'native_session': native_id, 'turns': sorted(turns), 'contexts': contexts})
        verdict.update(status='PASS', launch=launch['id'], attempt=attempt['attempt_id'], thread=thread,
                       compared_history_bytes=len(stopped_trace), closed_interval=[closed_start['direct_after'], closed_size],
                       pty_bytes_grew_while_closed=True, restart='interrupted; gate state unchanged; no resume')
    except (OSError, ValueError, KeyError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        verdict.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc(),
                       last_command_before_cleanup=commands.entries[-1] if commands.entries else None)
        journal('failure', error=repr(error))
    finally:
        for window in list(windows):
            try:
                close_window(window)
            except Exception as error:
                verdict.update(status='INCOMPLETE', window_cleanup_error=repr(error))
        if started:
            try:
                if thread and call('pane_status', '--thread', thread).get('historical') is not True:
                    processes('final-owned-processes')
                save('final-orchestration-events.json', call('orchestration_events'))
            except Exception as error:
                verdict.update(status='INCOMPLETE', final_observation_error=repr(error))
            finally:
                try:
                    save('stop-final-daemon.json', call('daemon_stop', check=False))
                except Exception as error:
                    verdict.update(status='INCOMPLETE', stop_error=repr(error))
        archive_and_cleanup(state, output, home, cleanup_pids, run, save, verdict)
        if launch is not None and verdict.get('database_archive', {}).get('integrity') == 'ok':
            try:
                accounting = read_main_turns(verdict['database_archive']['path'], launch['id'])
                save('archived-turn-accounting.json', accounting)
                verdict['observed_main_turns'] = accounting['main_turns']
                if verdict['real_turns_reserved'] and accounting['main_turns'] != 1:
                    raise RuntimeError('The reserved turn must have exactly one observed root CLI turn')
                with args.budget.open('a', encoding='utf-8') as stream:
                    fcntl.flock(stream, fcntl.LOCK_EX)
                    stream.write(json.dumps({'kind': 'observed', 'launch': launch['id'], 'output': str(output),
                                             'main_turns': verdict['observed_main_turns']}) + '\n')
                    stream.flush(); os.fsync(stream.fileno())
            except Exception as error:
                verdict.update(status='INCOMPLETE', turn_accounting_error=repr(error))
        if verdict.get('isolated_home_removed'):
            try:
                with tarfile.open(output / 'fixture-artifacts.tar.gz', 'x:gz') as archive:
                    for path, name in [(repo, 'repo'), (state, 'state')]:
                        if path.exists(): archive.add(path, arcname=name)
                    if request_directory is not None:
                        archive.add(request_directory, arcname='request-files')
            except (OSError, tarfile.TarError) as error:
                verdict.update(status='INCOMPLETE', fixture_archive_error=repr(error))
        save('verdict.json', verdict)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
