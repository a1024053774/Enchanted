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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=['preflight'], required=True)
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
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath',
               GIT_CONFIG_VALUE_0=os.devnull, GIT_CONFIG_KEY_1='commit.gpgsign',
               GIT_CONFIG_VALUE_1='false', GIT_AUTHOR_NAME='T0754 fixture',
               GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T0754 fixture',
               GIT_COMMITTER_EMAIL='fixture@example.invalid',
               A2A_BUILD_VOLUME='/Volumes/WD-Elements')
    commands, checks = [], []
    cli = [shutil.which('node'), source / 'workbench/src/gates/cli.ts', '--state', state]
    task = 'fixture-' + uuid.uuid4().hex[:10]
    project = 'observed-project-' + uuid.uuid4().hex[:8]
    title = '真实任务查询-' + uuid.uuid4().hex[:8]
    started = False
    pid = None
    verdict = {'status': 'INCOMPLETE', 'stage': args.stage, 'source': str(source),
               'fixture': str(fixture), 'task': task, 'project': project, 'title': title,
               'model_turns': 0, 'electron_started': False, 'checks': checks}

    def save(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, *, timeout=60):
        argv = [str(item) for item in argv]
        try:
            result = subprocess.run(argv, cwd=source, env=env, capture_output=True,
                                    text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            commands.append({'argv': argv, 'cwd': str(source), 'timeout': timeout,
                             'stdout': (error.stdout or b'').decode('utf-8', errors='replace'),
                             'stderr': (error.stderr or b'').decode('utf-8', errors='replace')})
            save('commands.json', commands)
            raise
        commands.append({'argv': argv, 'cwd': str(source), 'exit': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        save('commands.json', commands)
        return result

    def ok(argv):
        result = run(argv)
        if result.returncode != 0:
            raise RuntimeError({'setup_or_cleanup_command_failed': commands[-1]})
        return result

    def call(command, *values):
        result = ok([*cli, command, *values])
        value = json.loads(result.stdout)
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
        ok(['git', '-C', repo, 'add', 'value.txt'])
        ok(['git', '-C', repo, 'commit', '-m', 'Independent UI query fixture'])
        pid = call('daemon_start')['pid']
        started = True
        card = {'id': task, 'source': None, 'goal': '查询这张真实保存的任务卡',
                'non_goals': ['不启动模型，不改工作分支'],
                'paths': {'allow': ['value.txt'], 'deny': []},
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
            build = source / 'workbench/app/build.mjs'
            verdict['build_entry_exists'] = build.is_file()
            result = run([cli[0], build, '--slot', 't0754-preflight-' + fixture.name], timeout=120)
            assert result.returncode == 0, ('UI build entry must succeed with the mounted external cache volume', commands[-1])

        def snapshot_contract():
            result = run([*cli, 'workbench_snapshot', '--task', task])
            assert result.returncode == 0, ('UI snapshot must be available through the daemon CLI', commands[-1])
            value = json.loads(result.stdout)
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
            value = json.loads(result.stdout)
            assert value['ok'] is False and value['error'] == 'unknown_launch', value

        check('electron_build_entry', build_contract)
        check('daemon_workbench_snapshot', snapshot_contract)
        check('daemon_output_unknown_launch', unknown_launch_contract)
        verdict['status'] = 'PASS' if all(item['status'] == 'PASS' for item in checks) else 'INCOMPLETE'
    except Exception as error:
        # A harness/setup error is evidence, never a qualifying contract red.
        verdict.update(status='INCOMPLETE', harness_error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
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
