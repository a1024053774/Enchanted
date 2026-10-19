#!/usr/bin/env python3
"""Public-entry contract preflight for T-075-4.

The first checkpoint proves that the UI build and daemon read interfaces exist.
It does not claim Electron, PTY lifetime, recovery, or model acceptance. Run the
same preflight against the baseline and the candidate before the live stage.
"""
import argparse
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=['preflight', 'window'], required=True)
    parser.add_argument('--ipc-contract', choices=['legacy', 'picker', 'shell', 'panes', 'creation', 'sidebar'], default='sidebar')
    parser.add_argument('--runtime-source', type=Path,
                        help='Internal-disk source containing the Electron runtime and observation driver')
    args = parser.parse_args()
    source = args.source.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    fixture = Path(tempfile.mkdtemp(prefix='a2a4-', dir='/tmp')).resolve()
    repo, state = fixture / 'repo', fixture / 'state'
    repo.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    credential = fixture / 'operator-credential.json'
    env['A2A_OPERATOR_CREDENTIAL'] = str(credential)
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath',
               GIT_CONFIG_VALUE_0=os.devnull, GIT_CONFIG_KEY_1='commit.gpgsign',
               GIT_CONFIG_VALUE_1='false', GIT_AUTHOR_NAME='T0754 fixture',
               GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T0754 fixture',
               GIT_COMMITTER_EMAIL='fixture@example.invalid',
               A2A_BUILD_VOLUME='/Volumes/WD-Elements')
    command_log = CommandLog(output)
    commands, checks = command_log.entries, []
    cli = [shutil.which('node'), source / 'workbench/src/gates/cli.ts', '--state', state]
    task = 'fixture-' + uuid.uuid4().hex[:10]
    project = 'observed-project-' + uuid.uuid4().hex[:8]
    title = '真实任务查询-' + uuid.uuid4().hex[:8]
    started = False
    pid = None
    window = None
    window_attempted = False
    build_manifest = None
    runtime_source = args.runtime_source.resolve() if args.runtime_source else source
    verdict = {'status': 'INCOMPLETE', 'stage': args.stage, 'source': str(source),
               'ipc_contract': args.ipc_contract, 'runtime_source': str(runtime_source),
               'fixture': str(fixture), 'task': task, 'project': project, 'title': title,
               'model_turns': 0, 'electron_started': False, 'checks': checks}

    def save(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, *, timeout=60):
        try:
            return command_log.run(argv, cwd=source, env=env, timeout=timeout)
        finally:
            save('commands.json', commands)

    def ok(argv):
        result = run(argv)
        if result.returncode != 0:
            raise RuntimeError({'setup_or_cleanup_command_failed': commands[-1]})
        return result

    def call(command, *values):
        result = ok([*cli, command, *values])
        value = command_json(result)
        if value.get('ok') is not True:
            raise RuntimeError(value)
        return value

    def check(name, test):
        first = len(commands)
        try:
            test()
        except AssertionError as error:
            checks.append({'name': name, 'status': 'INCOMPLETE', 'kind': 'contract_failure',
                           'error': str(error), 'commands': [first, len(commands)]})
        else:
            checks.append({'name': name, 'status': 'PASS', 'commands': [first, len(commands)]})
        save('verdict.json', verdict)

    try:
        if cli[0] is None:
            raise RuntimeError('Node executable is unavailable')
        ok(['git', '-C', repo, 'init', '-b', 'main'])
        (repo / 'value.txt').write_text('原始夹具\n', encoding='utf-8')
        (repo / 'criterion.py').write_text("from pathlib import Path; assert Path('value.txt').read_text(encoding='utf-8') == '原始夹具\\n'\n", encoding='utf-8')
        ok(['git', '-C', repo, 'add', 'value.txt', 'criterion.py'])
        ok(['git', '-C', repo, 'commit', '-m', 'Independent UI query fixture'])
        pid = call('daemon_start')['pid']
        started = True
        card = {'id': task, 'source': None, 'goal': '查询这张真实保存的任务卡',
                'non_goals': ['不启动模型，不改工作分支'],
                'paths': {'allow': ['value.txt'], 'deny': []},
                'oracle_paths': ['criterion.py'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c',
                    "from pathlib import Path; assert Path('value.txt').read_text(encoding='utf-8') == '原始夹具\\n'"]}],
                'red_commands': [], 'task_type': '前端界面', 'repair_target': None,
                'complexity': 'L', 'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'},
                'base_commit': None, 'writer': None}
        card_file = fixture / 'card.json'
        card_file.write_text(json.dumps(card, ensure_ascii=False) + '\n', encoding='utf-8')
        call('card_save', '--task', task, '--card', card_file, '--expected-version', '0')
        call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main',
             '--card-version', '1', '--project', project, '--title', title)
        attempt = call('claim', '--task', task, '--owner', 'independent-ui-check')['attempt']
        save('attempt.json', attempt)
        current = call('status', '--task', task)['task']
        with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
            recorded = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (task,)).fetchone()[0])
        assert current == recorded
        assert recorded['project_id'] == project and recorded['title'] == title
        assert recorded['current_attempt']['attempt_id'] == attempt['attempt_id']
        save('independent-task-readback.json', recorded)
        verdict['fixture_setup'] = 'PASS'

        def build_contract():
            nonlocal build_manifest
            build = source / 'workbench/app/build.mjs'
            verdict['build_entry_exists'] = build.is_file()
            result = run([cli[0], build, '--slot', 't0754-preflight-' + fixture.name], timeout=120)
            assert result.returncode == 0, ('UI build entry must succeed with the mounted external cache volume', commands[-1])
            build_manifest = command_json(result)
            save('build.json', build_manifest)

        def snapshot_contract():
            result = run([*cli, 'workbench_snapshot', '--task', task])
            assert result.returncode == 0, ('UI snapshot must be available through the daemon CLI', commands[-1])
            value = command_json(result)
            assert value['ok'] is True
            assert value['task']['task_id'] == task
            assert value['task']['project_id'] == project
            assert value['task']['title'] == title
            assert value['task']['state'] == 'claimed'
            assert value['task']['current_attempt']['attempt_id'] == attempt['attempt_id']
            assert value['pane'] is None, 'A claim without dispatch must not invent a pane'

        def unknown_launch_contract():
            result = run([*cli, 'pane_output', '--launch', 'absent-' + uuid.uuid4().hex,
                          '--offset', '0', '--max-bytes', '4096'])
            assert result.returncode == 1, ('The output interface must reject a missing launch, not fail CLI argument parsing', commands[-1])
            value = command_json(result)
            assert value['ok'] is False and value['error'] == 'unknown_launch', value

        check('electron_build_entry', build_contract)
        check('daemon_workbench_snapshot', snapshot_contract)
        check('daemon_output_unknown_launch', unknown_launch_contract)
        if args.stage == 'window' and all(item['status'] == 'PASS' for item in checks):
            from electron_client import ElectronClient
            window_attempted = True
            window = ElectronClient(runtime_source, Path(build_manifest['out']), state, task,
                                    fixture / 'ui', output / 'window', env)
            verdict['electron_started'] = True
            def window_contract():
                value = window.wait(lambda item: title in item['text'] and item['gate'] == 'claimed')
                assert project in value['text'] and '只读' in value['text']
                assert value['state'] == 'unknown' and value['offset'] == 0
                expected_bridge = {'beginComposition', 'closePane', 'input', 'observeFocus', 'output',
                                   'paneKeys', 'releaseQueue', 'snapshot'}
                if args.ipc_contract in ('picker', 'shell', 'panes', 'creation', 'sidebar'):
                    expected_bridge |= {'projects', 'tasks', 'selection', 'selectTask'}
                if args.ipc_contract in ('shell', 'panes', 'creation', 'sidebar'):
                    expected_bridge |= {'newTerminal'}
                if args.ipc_contract in ('panes', 'creation', 'sidebar'):
                    expected_bridge |= {'paneAction', 'resize'}
                if args.ipc_contract in ('creation', 'sidebar'):
                    expected_bridge |= {'creationRepository', 'creationSubmit', 'creationCancel'}
                if args.ipc_contract == 'sidebar':
                    expected_bridge |= {'sidebar', 'selectAgent', 'notificationSetting'}
                assert set(value['bridge']) == expected_bridge, (value['bridge'], sorted(expected_bridge))
                assert len(value['bridge']) == len(expected_bridge), 'Public bridge names must not repeat'
                assert value['node'] == 'undefined'
                window.call('readonly-input')
                window.call('capture', name='claimed-no-pane')
                with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
                    assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0] == 0
                    save('readback-orchestration_events.json', [dict(type=kind, data=data) for kind, data in
                        db.execute('SELECT type,data FROM orchestration_events ORDER BY seq')])
                after = call('status', '--task', task)['task']
                assert after == recorded, 'Viewing must not mutate the gate state'
            check('electron_real_window', window_contract)
        verdict['status'] = 'PASS' if all(item['status'] == 'PASS' for item in checks) else 'INCOMPLETE'
    except Exception as error:
        # A harness/setup error is evidence, never a qualifying contract red.
        verdict.update(status='INCOMPLETE', harness_error=repr(error), traceback=traceback.format_exc())
    finally:
        if window is not None:
            try:
                window.close()
            except Exception as error:
                verdict.update(status='INCOMPLETE', window_cleanup_error=repr(error))
        try:
            if window_attempted and (window is None or not window.ready_confirmed or not window.exit_confirmed):
                raise RuntimeError('Electron ready/exit unconfirmed; backend shutdown and archive deferred to controller')
            if started:
                call('daemon_stop')
                deadline = time.monotonic() + 10
                while True:
                    result = run(['/bin/ps', '-o', 'pid=,ppid=,pgid=,command=', '-p', str(pid)])
                    if result.returncode not in (0, 1) or result.stderr.strip():
                        raise RuntimeError('Cannot confirm termination of the fixture daemon')
                    if not result.stdout.strip() and not (state / 'daemon.pid').exists():
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError('Fixture daemon did not stop within the deadline')
                    time.sleep(0.1)
                verdict['daemon_stopped'] = True
            if not started or verdict.get('daemon_stopped'):
                if credential.exists():
                    credential.unlink()
                with tarfile.open(output / 'fixture.tar.gz', 'x:gz') as archive:
                    archive.add(fixture, arcname=fixture.name)
        except Exception as error:
            verdict.update(status='INCOMPLETE', cleanup_error=repr(error), cleanup_traceback=traceback.format_exc())
        save('verdict.json', verdict)
    print(json.dumps({'status': verdict['status'], 'stage': args.stage,
                      'checks': checks, 'model_turns': 0}, ensure_ascii=False))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
