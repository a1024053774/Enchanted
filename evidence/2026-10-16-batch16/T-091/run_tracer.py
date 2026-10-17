#!/usr/bin/env python3
"""CONTROLLER ONLY: real single-pane main/preload/renderer/daemon Tracer bullet.

Review inventory BEFORE running; approval is for this run only.
  Starts: Node 26.5+, production daemon/zsh PTY, ONE controlled receiver derived from
    t078_native_receiver.c with one added stdout nonce (fixture copy, original unchanged),
    ONE Electron 43.4.1 using workbench/tests/electron_driver.mjs. Claude/Codex starts 0.
    Loopback reject-only HTTP server in this parent; supplier/model turns 0, POSTs 0.
  Hooks: receiver receives normal production UserPromptSubmit/Stop/PermissionRequest
    argv (timeout 10, --dangerously-bypass-hook-trust), but executes no hooks without
    marker files. This runner creates no marker and submits no model prompt.
  UI actions: focus/blur selected pane; ONE bracketed paste with a generated UTF-8
    nonce and NO Enter; one composition-start call, one bad empty-input declaration,
    one focus-observation call. Six unknown-key calls must reject. Control keys 0.
    All are fixture test-simulated input, not evidence of a real user's history.
  Capture: capture_window.py -> verified owned PID/window number -> screencapture -l.
    Missing screen-recording permission stops the run; no settings or broad capture.
  Isolation: fresh /private/tmp HOME/state/user-data; no auth.json/login/global config.
    Git only creates a fixture baseline. No submit/verify/integrate/reclaim/push.
  Cleanup: unconfirmed ready (alive OR already exited) -> stop for controller;
    no automatic SIGTERM/force quit. After ready, normal quit for exact owned PID;
    confirm UI exit before daemon_stop; confirm owned writers absent before archive.
  Raw output and copied fixture go only to the mounted external T-091 evidence root.
    New labels, no overwrite, preserve originals; repository contains text pointers.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from capture_window import process_identity
from run_red import Observer, VOLUME, archive_fixture, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--approval-ref', required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    script_dir = Path(__file__).resolve().parent
    root = (VOLUME / 'a2a-evidence/2026-10-16-batch16/T-091').resolve()
    if not os.path.ismount(VOLUME) or not output.is_relative_to(root) or output == root:
        raise RuntimeError('mounted_external_output_required')
    if not args.label or any(char not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for char in args.label):
        raise RuntimeError('invalid_summary_label')
    for suffix in ['run.json', 'archive.json']:
        if (script_dir / f'{args.label}.{suffix}').exists():
            raise RuntimeError('summary_exists; choose a new label')
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t078-2-t091-tracer-', dir='/private/tmp')).resolve()
    for name in ['repo', 'state', 'home', 'receiver-home', 'tmp', 'ui', 'bin']:
        (fixture / name).mkdir()
    credential = fixture.parent / (fixture.name + '-operator.json')
    env = {key: os.environ[key] for key in ['PATH', 'USER', 'LOGNAME'] if key in os.environ}
    env.update(HOME=str(fixture / 'home'), TMPDIR=str(fixture / 'tmp'), LANG='en_US.UTF-8', LC_ALL='C',
               A2A_OPERATOR_CREDENTIAL=str(credential), GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T091 tracer', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T091 tracer', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    sys.path.insert(0, str(source / 'workbench/tests'))
    from command_evidence import CommandLog, command_json
    commands = CommandLog(output)
    result = {'status': 'INCOMPLETE', 'phase': 'single-pane-tracer', 'task': 'T-091', 'attempt': 'a1',
              'worker': 's16-t091', 'worker_launch': 'launch-a818e11600754e8b8ad79aab63a17f83',
              'approval_ref': args.approval_ref, 'argv': sys.argv, 'fixture': str(fixture),
              'supplier_model_turns': 0, 'real_vendor_cli_starts': 0, 'control_keys': [],
              'input_origin': 'test-simulated fixture user input', 'checks': [],
              'trace_passed': False, 'cleanup_complete': False, 'archive_complete': False,
              'cleanup_policy': 'unconfirmed ready always waits for controller; no automatic Electron SIGTERM'}
    observer = None
    observer_attempted = started = False
    worker_start_attempted = worker_identity_bound = False
    owned, requests = [], []
    api = None
    cli = []

    def run(argv, timeout=60):
        value = commands.run(argv, cwd=source, env=env, timeout=timeout)
        if value.returncode:
            raise RuntimeError({'command_failed': value.evidence['id'], 'exit': value.returncode})
        return value

    def call(command, *values):
        value = command_json(run([*cli, command, *values]))
        if value.get('ok') is not True:
            raise RuntimeError({'daemon_request_failed': value})
        return value

    def wait(predicate, description, timeout=20):
        deadline = time.monotonic() + timeout
        while True:
            value = predicate()
            if value:
                return value
            if time.monotonic() >= deadline:
                raise TimeoutError(description)
            time.sleep(0.1)

    def check(name, condition):
        result['checks'].append({'name': name, 'status': 'PASS' if condition else 'INCOMPLETE'})
        if not condition:
            raise AssertionError(name)

    try:
        node = shutil.which('node', path=env.get('PATH'))
        if not node:
            raise RuntimeError('node_required')
        result['source_revision'] = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        result['node_version'] = run([node, '--version']).stdout.strip()
        product_diff = run(['git', 'diff', 'HEAD', '--', 'workbench/app/', 'workbench/src/', 'workbench/tests/']).stdout
        if product_diff:
            raise RuntimeError('freeze_product_and_test_candidate_before_running')
        if not result['node_version'].startswith('v26.') or int(result['node_version'].split('.')[1]) < 5:
            raise RuntimeError('node_26_5_or_later_26_required')
        state, repo, home = fixture / 'state', fixture / 'repo', fixture / 'receiver-home'
        cli = [node, source / 'workbench/src/gates/cli.ts', '--state', state]
        run(['git', '-C', repo, 'init', '-b', 'main'])
        (repo / 'value.txt').write_text('T091 isolated tracer\n', encoding='utf-8')
        (repo / 'criterion.py').write_text("from pathlib import Path\nassert Path('value.txt').read_text() == 'T091 isolated tracer\\n'\n", encoding='utf-8')
        run(['git', '-C', repo, 'add', 'value.txt', 'criterion.py'])
        run(['git', '-C', repo, 'commit', '-m', 'T091 tracer fixture'])
        receiver = fixture / 'bin/codex-receiver'
        output_nonce = 'T091_OUTPUT_' + uuid.uuid4().hex
        receiver_source = (source / 'workbench/tests/t078_native_receiver.c').read_text(encoding='utf-8')
        ready_line = r'printf("T078_DETERMINISTIC_RECEIVER_READY\r\n\033[?2004h"); fflush(stdout);'
        if receiver_source.count(ready_line) != 1:
            raise RuntimeError('receiver_stdout_nonce_site_changed')
        probe_source = fixture / 'receiver-probe.c'
        probe_source.write_text(receiver_source.replace(ready_line,
            ready_line.replace('fflush(stdout);', f'printf("{output_nonce}\\r\\n"); fflush(stdout);'), 1), encoding='utf-8')
        write_json(output / 'output-oracle.json', {'nonce': output_nonce, 'source': 'fixture input fixed before receiver compilation/start'})
        run(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11',
             probe_source, '-o', receiver])
        role = fixture / 'receiver-role.md'
        role.write_text('仅记录终端字节，不运行模型或工具，不触发 hook。\n', encoding='utf-8')
        config = {'codex_bin': str(receiver), 'codex_home': str(home), 'role_card': str(role),
                  'role_card_revision': 'T-091-tracer', 'code_revision': result['source_revision'],
                  'source_snapshot': str(source), 'hook_authorization': args.approval_ref,
                  'turn_limit': 1, 'turn_authorization': args.approval_ref + ': controlled receiver only, zero model turns'}
        write_json(fixture / 'launch.json', config)

        class RejectAPI(BaseHTTPRequestHandler):
            def log_message(self, *unused):
                pass

            def do_POST(self):
                requests.append({'method': 'POST', 'path': self.path})
                self.send_error(403, 'T091 zero model budget')

            def do_GET(self):
                requests.append({'method': 'GET', 'path': self.path})
                self.send_error(403, 'T091 isolated fake API')

        api = ThreadingHTTPServer(('127.0.0.1', 0), RejectAPI)
        api.daemon_threads = True
        threading.Thread(target=api.serve_forever, daemon=True).start()
        result['fake_api_url'] = f'http://127.0.0.1:{api.server_port}/'
        daemon = call('daemon_start', '--launch-config', fixture / 'launch.json')
        started = True
        owned.append(process_identity(daemon['pid']))
        task = 't091-tracer-' + uuid.uuid4().hex[:8]
        card = {'id': task, 'source': None, 'goal': '单格 pane key 输入输出读回', 'non_goals': ['不运行模型、不提交、不集成'],
                'paths': {'allow': ['value.txt'], 'deny': []}, 'oracle_paths': ['criterion.py'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', 'criterion.py']}],
                'red_commands': [], 'task_type': '前端界面', 'repair_target': None, 'complexity': 'L',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}, 'base_commit': None, 'writer': None}
        write_json(fixture / 'card.json', card)
        call('card_save', '--task', task, '--card', fixture / 'card.json', '--expected-version', '0')
        call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1',
             '--project', 't091-isolated', '--title', 'T-091 单格 Tracer bullet')
        worker_start_attempted = True
        attempt = call('dispatch', '--task', task, '--runtime-mode', 'workspace-write')['attempt']
        wait(lambda: (home / 'receiver-started.json').exists() and (home / 'received.bin').exists(), 'receiver_start_deadline')
        receiver_started = json.loads((home / 'receiver-started.json').read_text(encoding='utf-8'))
        info = wait(lambda: (value if (value := call('pane_process_info', '--thread', attempt['thread_id'])).get('leader') else None), 'receiver_identity_deadline')
        check('receiver_foreground_identity', not info.get('failed') and info['leader'] == receiver_started['pid'] and
              info['native_session'] == receiver_started['native_session'])
        owned.extend([process_identity(info['shell_pid']), process_identity(info['leader'])])
        worker_identity_bound = True
        snapshot = call('workbench_snapshot', '--task', task)
        launch = snapshot['launch']['id']
        check('authoritative_task_launch_attempt', snapshot['launch']['task'] == task and snapshot['launch']['attempt'] == attempt['attempt_id'] and
              snapshot['launch']['role'] == 'worker' and snapshot['launch']['preset'] is None)
        write_json(output / 'expected.json', {'task': task, 'launch': launch, 'thread': attempt['thread_id'], 'attempt': attempt['attempt_id']})
        write_json(output / 'snapshot-before.json', snapshot)
        write_json(output / 'process-before.json', info)
        build = command_json(run([node, source / 'workbench/app/build.mjs', '--slot', 't091-tracer-' + fixture.name.rsplit('-', 1)[-1]], timeout=180))
        write_json(output / 'build.json', build)
        window_output = output / 'window'; window_output.mkdir()
        env['A2A_ELECTRON_DIAGNOSTICS'] = str(window_output / 'stages.jsonl')
        relative = (source / 'workbench/node_modules/electron/path.txt').read_text(encoding='utf-8').strip()
        executable = (source / 'workbench/node_modules/electron/dist' / relative).resolve(strict=True)
        argv = [str(executable), str(source / 'workbench/tests/electron_driver.mjs'), '--build', build['out'], '--state', str(state),
                '--task', task, '--launch', launch, '--user-data', str(fixture / 'ui'), '--output', str(window_output)]
        write_json(output / 'electron-command.json', {'argv': argv, 'start_new_session': True})
        observer_attempted = True
        observer = Observer(argv, env, output)
        observer.identify(argv, output)
        ready = observer.receive()
        check('owned_electron_ready', ready.get('ready') is True and ready.get('pid') == observer.process.pid and ready.get('electron') == '43.4.1')
        observer.ready_confirmed = True
        source_output = call('pane_output', '--launch', launch, '--offset', '0', '--max-bytes', '65536')
        source_bytes = base64.b64decode(source_output['data_base64'])
        check('independent_output_nonce', output_nonce.encode('ascii') in source_bytes and
              source_output['next_offset'] == source_output['total_bytes'] == len(source_bytes))
        (output / 'source-output.bin').write_bytes(source_bytes)

        def bound_view():
            value = observer.call('inspect')
            return value if value.get('input_enabled') and output_nonce in value.get('terminal', '') and value.get('offset') == len(source_bytes) else None

        view = wait(bound_view, 'keyed_view_deadline')
        key, window_id = view['pane_key'], view['window_id']
        check('one_bound_pane_no_auto_focus', len(view['panes']) == 1 and bool(key and window_id) and not view['keyboard_focused'] and not view['input_target'])
        check('visible_full_identity', view['task'] == task and view['launch'] == launch and view['thread'] == attempt['thread_id'] and
              view['attempt'] == attempt['attempt_id'] and all(text in view['text'] for text in [task, launch, attempt['attempt_id']]))
        check('renderer_sandbox', view['node'] == 'undefined')
        write_json(output / 'view-initial.json', view)
        for operation, values in [('snapshot', []), ('output', [0]), ('input', ['DENIED_SENTINEL']), ('beginComposition', []),
                                  ('releaseQueue', [{'window_id': window_id}]), ('observeFocus', ['\x1b[?1004h'])]:
            denied = observer.call('bridge-call', operation=operation, pane_key='unknown-' + key, args=values)
            check('wrong_key_rejected_' + operation, denied.get('rejected') is True)
        check('wrong_keys_write_nothing', (home / 'received.bin').read_bytes() == b'')
        observer.call('focus-pane', pane_key=key)
        wait(lambda: observer.call('inspect', pane_key=key).get('input_target'), 'keyboard_focus_deadline')
        nonce = 'T091 单格输入 ' + uuid.uuid4().hex
        observer.call('terminal-input', pane_key=key, paste=nonce, submit=False)
        expected = ('\x1b[200~' + nonce + '\x1b[201~').encode('utf-8')
        wait(lambda: (home / 'received.bin').stat().st_size >= len(expected), 'pty_input_deadline')
        check('keyed_input_exact_bytes', (home / 'received.bin').read_bytes() == expected)
        write_json(output / 'input-oracle.json', {'text': nonce, 'expected_bytes': len(expected), 'source': 'fixture input created before paste'})
        for operation, values in [('beginComposition', []), ('releaseQueue', [{'window_id': 'foreign-window'}]), ('observeFocus', ['\x1b[?1004h'])]:
            response = observer.call('bridge-call', operation=operation, pane_key=key, args=values)
            check('keyed_' + operation, response.get('resolved') is True and
                  (response['value'].get('error') == 'empty_input_declaration_required' if operation == 'releaseQueue' else response['value'].get('ok') is True))
        check('non_input_methods_do_not_write', (home / 'received.bin').read_bytes() == expected)
        inputs = call('issues', '--task', task)['user_inputs']
        events = call('events', '--task', task)['events']
        orchestration = call('orchestration_events', '--task', task)['events']
        matching = [row for row in inputs if row['form'] == 'message' and row['text'] == nonce and
                    row['target']['attempt'] == attempt['attempt_id'] and row['source_ref']['window_id'] == window_id]
        check('input_record_and_intervention', len(matching) == 1 and len(inputs) == 1 and
              len([row for row in events if row['type'] == 'human_intervention' and row['details'].get('input_id') == matching[0]['id']]) == 1)
        admitted = [row['data'] for row in orchestration if row['type'] == 'window_request_admitted']
        check('independent_sequence_and_no_unknown_admission', [row['sequence'] for row in admitted] == [1, 2, 3, 4] and
              all(row['window_id'] == window_id for row in admitted))
        check('single_window_credential', len([row for row in orchestration if row['type'] == 'window_opened']) == 1)
        check('no_enter_or_dispatch_release', not any(row['type'] in ['turn_submit_intent', 'turn_submitted', 'paste_intent'] for row in orchestration))
        write_json(output / 'input-records.json', inputs); write_json(output / 'gate-events.json', events)
        write_json(output / 'orchestration-before-close.json', orchestration)
        capture = command_json(run([sys.executable, script_dir / 'capture_window.py', '--owner', output / 'electron-owner.json',
                                    '--output', output / 'tracer-original.png']))
        write_json(output / 'capture.json', capture)
        observer.call('blur-pane', pane_key=key)
        wait(lambda: not observer.call('inspect', pane_key=key).get('input_target'), 'keyboard_blur_deadline')
        result.update(trace_passed=True, fixture_task=task, pane_key=key, window_id=window_id, launch=launch,
                      screenshot=str(output / 'tracer-original.png'))
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        cleanup_errors = []
        electron_closed = not observer_attempted
        if observer is not None:
            try:
                observer.close()
            except Exception as error:
                cleanup_errors.append({'electron': repr(error), 'owned_pid': observer.process.pid})
            electron_closed = observer.exit_confirmed
        ready_confirmed = observer.ready_confirmed if observer is not None else False
        result.update(electron_exit_confirmed=electron_closed, electron_ready_confirmed=ready_confirmed)
        if started and electron_closed and (not observer_attempted or ready_confirmed):
            try:
                if result['trace_passed']:
                    try:
                        after_close = call('orchestration_events', '--task', task)['events']
                        check('window_credential_closed', len([row for row in after_close if row['type'] == 'window_closed' and row['data']['window_id'] == window_id]) == 1)
                        alive = call('pane_process_info', '--thread', attempt['thread_id'])
                        check('closing_view_keeps_agent', alive['leader'] == receiver_started['pid'] and not alive.get('failed'))
                        write_json(output / 'process-after-window.json', alive)
                        write_json(output / 'orchestration-after-window.json', after_close)
                    except Exception as error:
                        # A failed assertion is preserved; confirmed UI exit still
                        # permits the separately authorized backend shutdown.
                        result.update(trace_passed=False, post_close_error=repr(error))
                call('daemon_stop')
                for owner in owned:
                    deadline = time.monotonic() + 15
                    while True:
                        probe = commands.run(['/bin/ps', '-ww', '-p', str(owner['pid']), '-o', 'pid=,lstart=,command='], cwd=source, env=env, timeout=5)
                        if probe.returncode == 1 and not probe.stdout.strip() and not probe.stderr.strip():
                            break
                        if probe.returncode != 0 or probe.stderr.strip() or time.monotonic() >= deadline:
                            raise RuntimeError({'writer_exit_unconfirmed': owner})
                        time.sleep(0.1)
                if (fixture / 'state/control.sock').exists() or (fixture / 'state/daemon.pid').exists():
                    raise RuntimeError('daemon_endpoint_exit_unconfirmed')
                if worker_start_attempted and not worker_identity_bound:
                    raise RuntimeError('worker_exit_cannot_be_proven_without_bound_identity; retain fixture')
                result['cleanup_complete'] = not cleanup_errors
                if credential.exists():
                    credential.unlink()
            except Exception as error:
                cleanup_errors.append({'backend': repr(error)})
        elif started:
            result['backend_cleanup_deferred'] = 'unconfirmed Electron startup/exit; wait for controller; no daemon_stop or archive'
        if api is not None:
            api.shutdown(); api.server_close()
        result['fake_posts'] = sum(row['method'] == 'POST' for row in requests)
        result['cleanup_errors'] = cleanup_errors
        write_json(output / 'fake-api-requests.json', requests)
        if result['cleanup_complete']:
            try:
                archive = output / 'fixture'
                manifest = {'original': str(fixture), 'archive': str(archive), **archive_fixture(fixture, archive),
                            'original_retained': True, 'replay': shlex.join([sys.executable, str(Path(__file__).resolve()), '--source', str(source),
                              '--output', str(output) + '-replay-new', '--label', args.label + '-replay-new', '--approval-ref', '<本次新批准引用>'])}
                write_json(script_dir / f'{args.label}.archive.json', manifest)
                result.update(archive=manifest, archive_complete=True)
            except Exception as error:
                result['archive_error'] = repr(error)
        if result['trace_passed'] and result['cleanup_complete'] and result['archive_complete'] and result['fake_posts'] == 0 and not result.get('error'):
            result['status'] = 'PASS'
        write_json(output / 'run.json', result)
        write_json(script_dir / f'{args.label}.run.json', result)
    print(json.dumps({'status': result['status'], 'trace_passed': result['trace_passed'], 'cleanup_complete': result['cleanup_complete'], 'output': str(output)}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
