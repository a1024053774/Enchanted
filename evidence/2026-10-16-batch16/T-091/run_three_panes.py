#!/usr/bin/env python3
"""CONTROLLER ONLY: T-091 same-task three-pane green, refusals and UI regression.

Review BEFORE this run; do not reuse any previous approval.
  CLI/process budget: Node 26.5+, one production daemon, zsh PTYs; fixed real
    Claude Code 2.1.296: two --version probes and TWO interactive controller starts;
    THREE sequential controlled C receiver starts (foreign task, old attempt,
    current worker), NOT real Codex. clang once; fixture Git init/add/commit only.
    Initial pane_release TWO times, only the controlled foreign/old receiver;
    each consumes its queued fixture prompt (bracketed paste + CR), never a model.
    TWO synthetic Stop hooks from those receivers, then gate reclaim TWO times,
    only those exact attempts, before UI starts. Current worker is never released.
    ONE Electron 43.4.1 with production run(), repeated --launch, isolated user-data.
    One parent loopback HTTP API, reject all POSTs; provider model rounds 0, POSTs 0.
  Hooks: production per-session UserPromptSubmit/Stop/PermissionRequest command
    hooks (Claude 3s, receiver 10s) are passed; receiver has bypass-hook-trust argv.
    The two numbered Stop files above are the only synthetic hooks; no vendor
    model prompt, tools or global configuration. Receiver simulated turns: 2.
  UI/input budget: no Enter, Esc, control keys, trust/theme/login/permission answers.
    At most 120 driver RPCs (at most 360 screen reads, 3 per RPC), three captures.
    Stop before another RPC after 32 MiB stdout; one reply can cross the threshold.
    Full output stays on the external volume; terminal prints one short summary.
    Controller screens are OBSERVED ONLY: no focus, paste, keys or prompt release.
    Worker focus once, one generated Unicode bracketed paste submit=false, blur once.
    Each pane: one composition-start and one focus-observation IPC (no PTY bytes).
    One invalid cross-window empty-input declaration; six unknown-key probes.
    Two try-open refusals: third launch from another task, then same-task old attempt.
    Scroll each controller's own terminal viewport once (no keyboard/focus).
    Resize outer window to 1440x900, 1200x800, 900x650 and back; no remount/tab switching.
  Capture: three original frames (one per size), ONLY verified owned Electron window
    via capture_window.py / screencapture -l. No mosaic, cropping or editing.
  Isolation: fresh /private/tmp HOME/state/user-data; loopback fake API only;
    no auth.json, login credentials, real model rounds or global writes.
    C source is a fixture copy of T-078: unique session/diagnostic paths for each
    launch and an output nonce fixed before compile; no business behavior added.
  Cleanup: if Electron ready is unconfirmed, alive OR exited, pause for controller.
    No automatic Electron signal/force quit. After confirmed ready, normal quit;
    verify all 3 view credentials closed and agents survived, then daemon_stop.
    Confirm all registered writers absent before symlink-preserving archive copy.
    Retain originals. New external output/label; no overwrite or internal fallback.
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
from run_red import CLAUDE, Observer, VOLUME, archive_fixture, write_json


def receiver_probe(source, nonce):
    """Keep T-078's controlled receiver; separate the three launch diagnostics."""
    code = source.read_text(encoding='utf-8')
    replacements = [
        ('static const char *session = "00000000-0078-4000-8000-000000000001";',
         'static const char *session;'),
        ('if (snprintf(out, PATH_MAX, "%s/%s", home, name) >= PATH_MAX)',
         'if (snprintf(out, PATH_MAX, "%s/%s/%s", home, !strncmp(name, "sessions", 8) ? "" : getenv("A2A_LAUNCH"), name) >= PATH_MAX)'),
        ('char file[PATH_MAX]; path(file, "sessions"); if (mkdir(file, 0700)) fail("create sessions");',
         'session = getenv("A2A_SESSION"); if (!session || !getenv("A2A_LAUNCH")) return 2;\n'
         '  char file[PATH_MAX]; snprintf(file, sizeof file, "%s/%s", home, getenv("A2A_LAUNCH"));\n'
         '  if (mkdir(file, 0700)) fail("create launch diagnostics");\n'
         '  path(file, "sessions"); if (mkdir(file, 0700) && errno != EEXIST) fail("create sessions");'),
        (r'printf("T078_DETERMINISTIC_RECEIVER_READY\r\n\033[?2004h"); fflush(stdout);',
         r'printf("T078_DETERMINISTIC_RECEIVER_READY\r\n\033[?2004h"); ' +
         f'printf("{nonce} %s\\r\\n", getenv("A2A_LAUNCH")); fflush(stdout);'),
    ]
    for before, after in replacements:
        if code.count(before) != 1:
            raise RuntimeError('receiver_probe_site_changed: ' + before)
        code = code.replace(before, after, 1)
    return code


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
    fixture = Path(tempfile.mkdtemp(prefix='t078-2-t091-three-', dir='/private/tmp')).resolve()
    for name in ['repo', 'state', 'home', 'receiver-home', 'tmp', 'ui', 'bin']:
        (fixture / name).mkdir()
    credential = fixture.parent / (fixture.name + '-operator.json')
    env = {key: os.environ[key] for key in ['PATH', 'USER', 'LOGNAME'] if key in os.environ}
    env.update(HOME=str(fixture / 'home'), TMPDIR=str(fixture / 'tmp'), LANG='en_US.UTF-8', LC_ALL='C',
               A2A_OPERATOR_CREDENTIAL=str(credential), GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T091 three panes', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T091 three panes', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    sys.path.insert(0, str(source / 'workbench/tests'))
    from command_evidence import CommandLog, command_json
    commands = CommandLog(output)
    result = {'status': 'INCOMPLETE', 'phase': 'same-task-three-panes', 'task': 'T-091', 'attempt': 'a1',
              'worker': 's16-t091', 'worker_launch': 'launch-71afbd1600cb451a9d9354aa7768e72b',
              'worker_session': 'd4277ace-1dde-425b-99b8-8988f1df751f',
              'worker_native_session': '01a14a05-4472-70e1-af77-58414340c1ee',
              'approval_ref': args.approval_ref, 'argv': sys.argv, 'fixture': str(fixture),
              'supplier_model_turns': 0, 'controller_cli_starts_budget': 2, 'controller_start_attempts': 0, 'controlled_receiver_starts_budget': 3,
              'real_codex_cli_starts': 0, 'electron_starts_budget': 1, 'electron_start_attempts': 0,
              'peak_controlled_receivers': 0, 'driver_rpc_limit': 120, 'screen_read_upper_bound': 360,
              'stdout_stop_threshold_bytes': 32 * 1024 * 1024, 'capture_limit': 3,
              'control_keys': [], 'controller_screen_actions': [], 'input_origin': 'test-simulated fixture user input',
              'checks': [], 'green_observed': False, 'negatives_passed': False,
              'cleanup_complete': False, 'archive_complete': False}
    observer = None
    observer_attempted = started = False
    worker_start_attempted = 0
    worker_bound = 0
    receivers_active = 0
    owned, expected, requests, cli = [], [], [], []
    api = None
    state, repo, home = fixture / 'state', fixture / 'repo', fixture / 'receiver-home'

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

    def wait(predicate, description, timeout=30):
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

    def absent(owner):
        probe = commands.run(['/bin/ps', '-ww', '-p', str(owner['pid']), '-o', 'pid=,lstart=,command='], cwd=source, env=env, timeout=5)
        if probe.returncode == 1 and not probe.stdout.strip() and not probe.stderr.strip():
            return True
        if probe.returncode != 0 or probe.stderr.strip():
            raise RuntimeError({'cannot_confirm_writer_exit': owner})
        return False

    def create_task(task, title):
        card = {'id': task, 'source': None, 'goal': title, 'non_goals': ['不运行模型、不交付或集成'],
                'paths': {'allow': ['value.txt'], 'deny': []}, 'oracle_paths': ['criterion.py'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', 'criterion.py']}],
                'red_commands': [], 'task_type': '前端界面', 'repair_target': None, 'complexity': 'L',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}, 'base_commit': None, 'writer': None}
        path = fixture / (task + '.card.json'); write_json(path, card)
        call('card_save', '--task', task, '--card', path, '--expected-version', '0')
        call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1',
             '--project', 't091-isolated', '--title', title)

    def start_worker(task, label):
        nonlocal worker_start_attempted, worker_bound, receivers_active
        check(label + '_only_one_receiver', receivers_active == 0 and worker_start_attempted < 3)
        worker_start_attempted += 1
        attempt = call('dispatch', '--task', task, '--runtime-mode', 'workspace-write')['attempt']
        snapshot = call('workbench_snapshot', '--task', task)
        launch = snapshot['launch']['id']
        diagnostics = home / launch
        wait(lambda: (diagnostics / 'receiver-started.json').exists() and (diagnostics / 'received.bin').exists(), label + '_receiver_start')
        receiver = json.loads((diagnostics / 'receiver-started.json').read_text(encoding='utf-8'))
        info = wait(lambda: (value if (value := call('pane_process_info', '--thread', attempt['thread_id'])).get('leader') else None), label + '_identity')
        check(label + '_controlled_identity', not info.get('failed') and info['leader'] == receiver['pid'] and
              info['native_session'] == receiver['native_session'] == attempt['session_id'])
        owners = [process_identity(info['shell_pid']), process_identity(info['leader'])]
        owned.extend(owners); worker_bound += 1
        receivers_active += 1
        result['peak_controlled_receivers'] = max(result['peak_controlled_receivers'], receivers_active)
        item = {'task': task, 'role': 'worker', 'preset': None, 'launch': launch, 'thread': attempt['thread_id'],
                'session': attempt['session_id'], 'attempt': attempt['attempt_id'], 'leader': info['leader']}
        write_json(output / (label + '.initial.snapshot.json'), snapshot)
        write_json(output / (label + '.initial.process.json'), info)
        return item, diagnostics, owners

    def raw_output(item):
        chunks, cursor = [], 0
        while True:
            chunk = call('pane_output', '--launch', item['launch'], '--offset', str(cursor), '--max-bytes', '65536')
            data = base64.b64decode(chunk['data_base64'])
            check('raw_output_cursor_' + (item['preset'] or 'worker'), chunk['launch'] == item['launch'] and
                  chunk['start_offset'] == cursor and chunk['next_offset'] == cursor + len(data))
            chunks.append(data); cursor = chunk['next_offset']
            if cursor == chunk['total_bytes']:
                return b''.join(chunks)

    def finish_and_reclaim(item, diagnostics, owners):
        nonlocal receivers_active
        # Only the controlled receiver: consume the pre-existing fixture dispatch,
        # then use its actual hook CLI child to establish idle before gate reclaim.
        call('pane_release', '--thread', item['thread'], '--reason', args.approval_ref + ': controlled setup receiver only')
        wait(lambda: (diagnostics / 'turn-1.ready').exists(), 'controlled_setup_turn')
        write_json(diagnostics / 'hook-1.json', {'hook_event_name': 'Stop', 'session_id': item['session'],
                                               'turn_id': 'turn-1', 'stop_hook_active': False})
        wait(lambda: (diagnostics / 'hook-1.exit').exists(), 'controlled_stop_hook')
        check('controlled_stop_exit_' + item['launch'], (diagnostics / 'hook-1.exit').read_text().strip() == '0')
        wait(lambda: call('pane_status', '--thread', item['thread']).get('state') == 'idle', 'controlled_idle_before_reclaim')
        call('reclaim', '--task', item['task'], '--attempt', item['attempt'])
        for owner in owners:
            wait(lambda: absent(owner), 'controlled_reclaim_exit')
        receivers_active -= 1

    def visible(view, width, height):
        panes = view.get('panes', [])
        return len(panes) == 3 and all(p['bounds']['width'] > 0 and p['bounds']['height'] > 0 and
            p['bounds']['y'] >= 0 and p['bounds']['y'] + p['bounds']['height'] <= height and
            p['bounds']['x'] + p['bounds']['width'] <= width and p['terminal_bounds']['height'] > 0 for p in panes)

    try:
        node = shutil.which('node', path=env.get('PATH'))
        if not node:
            raise RuntimeError('node_required')
        result['source_revision'] = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        result['node_version'] = run([node, '--version']).stdout.strip()
        if not result['node_version'].startswith('v26.') or int(result['node_version'].split('.')[1]) < 5:
            raise RuntimeError('node_26_5_or_later_26_required')
        if run(['git', 'diff', 'HEAD', '--', 'workbench/app/', 'workbench/src/', 'workbench/tests/']).stdout:
            raise RuntimeError('freeze_product_and_tests_before_running')
        cli = [node, source / 'workbench/src/gates/cli.ts', '--state', state]
        run(['git', '-C', repo, 'init', '-b', 'main'])
        (repo / 'value.txt').write_text('T091 isolated panes\n', encoding='utf-8')
        (repo / 'criterion.py').write_text("from pathlib import Path\nassert Path('value.txt').read_text() == 'T091 isolated panes\\n'\n", encoding='utf-8')
        run(['git', '-C', repo, 'add', 'value.txt', 'criterion.py'])
        run(['git', '-C', repo, 'commit', '-m', 'T091 three-pane fixture'])
        receiver = fixture / 'bin/codex-receiver'
        output_nonce = 'T091_OUTPUT_' + uuid.uuid4().hex
        probe = fixture / 'receiver-probe.c'
        probe.write_text(receiver_probe(source / 'workbench/tests/t078_native_receiver.c', output_nonce), encoding='utf-8')
        write_json(output / 'output-oracle.json', {'nonce': output_nonce, 'fixed_before': 'compilation and all receiver starts'})
        run(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11', probe, '-o', receiver])
        role = fixture / 'receiver-role.md'; role.write_text('只收终端字节，不运行模型，不执行工具或合成 hook。\n', encoding='utf-8')
        write_json(fixture / 'launch.json', {'codex_bin': str(receiver), 'codex_home': str(home), 'role_card': str(role),
            'role_card_revision': 'T-091-three', 'code_revision': result['source_revision'], 'source_snapshot': str(source),
            'hook_authorization': args.approval_ref, 'turn_limit': 1,
            'turn_authorization': args.approval_ref + ': controlled receiver only, zero provider rounds'})

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
        api_url = f'http://127.0.0.1:{api.server_port}/'
        result['fake_api_url'] = api_url
        daemon = call('daemon_start', '--launch-config', fixture / 'launch.json'); started = True
        owned.append(process_identity(daemon['pid']))
        task = 't091-three-' + uuid.uuid4().hex[:8]
        foreign_task = 't091-other-' + uuid.uuid4().hex[:8]
        create_task(foreign_task, 'T-091 错 task 反例夹具')
        foreign, foreign_diagnostics, foreign_owners = start_worker(foreign_task, 'foreign')
        finish_and_reclaim(foreign, foreign_diagnostics, foreign_owners)
        create_task(task, 'T-091 同任务三窗格')
        old, old_diagnostics, old_owners = start_worker(task, 'old')
        finish_and_reclaim(old, old_diagnostics, old_owners)
        worker, diagnostics, _ = start_worker(task, 'worker')

        for preset in ['ideation', 'executor']:
            folder = fixture / 'roles' / preset
            for directory in ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']:
                (folder / directory).mkdir(parents=True)
            (folder / 'claude/settings.json').write_text('{"theme":"dark"}\n', encoding='utf-8')
            (folder / 'role.md').write_text('只停在隔离首屏等待主控；不输入、不运行模型或工具。\n', encoding='utf-8')
            manifest = {'schema': 1, 'root': str(fixture), 'state': str(state), 'task': task, 'preset': preset,
                'launch': str(uuid.uuid4()), 'session': str(uuid.uuid4()), 'thread': str(uuid.uuid4()),
                'executable': CLAUDE, 'role_file': str(folder / 'role.md'), 'code_revision': result['source_revision'],
                'source_snapshot': str(source), 'api_url': api_url, 'turn_limit': 1}
            write_json(folder / 'manifest.json', manifest)
            role_env = {**env, 'HOME': str(folder / 'home'), 'CLAUDE_CONFIG_DIR': str(folder / 'claude'),
                        'TMPDIR': str(folder / 'tmp'), 'DISABLE_AUTOUPDATER': '1'}
            version = commands.run([CLAUDE, '--version'], cwd=source, env=role_env, timeout=20)
            check(preset + '_fixed_version', version.returncode == 0 and version.stdout.strip() == '2.1.296 (Claude Code)')
            result['controller_start_attempts'] += 1
            launch = call('controller_start', '--task', task, '--manifest', folder / 'manifest.json')['launch']
            info = wait(lambda: (value if (value := call('pane_process_info', '--thread', manifest['thread'])).get('leader') else None), preset + '_identity')
            check(preset + '_native_identity', not info.get('failed') and info.get('native_session') == manifest['session'])
            owned.extend([process_identity(info['shell_pid']), process_identity(info['leader'])])
            expected.append({'task': task, 'role': 'controller', 'preset': preset, 'launch': manifest['launch'],
                'thread': manifest['thread'], 'session': manifest['session'], 'attempt': None, 'leader': info['leader']})
            write_json(output / (preset + '.launch.json'), launch)
        expected.append(worker)
        old_snapshot = call('workbench_snapshot', '--task', task, '--launch', old['launch'])
        check('old_launch_is_same_task_historical_attempt', old_snapshot['launch']['id'] == old['launch'] and
              old_snapshot['launch']['task'] == task and old_snapshot['launch']['attempt'] == old['attempt'] and
              old_snapshot['task']['current_attempt']['attempt_id'] == worker['attempt'] and old['attempt'] != worker['attempt'])
        write_json(output / 'old.snapshot.json', old_snapshot)
        write_json(output / 'expected.json', {'task': task, 'panes': expected, 'required_visible_count': 3,
                                            'foreign_launch': foreign, 'old_launch': old})
        for item in expected:
            label = item['preset'] or 'worker'
            snapshot = call('workbench_snapshot', '--task', task, '--launch', item['launch'])
            check(label + '_snapshot_binding', all(snapshot['launch'][field] == item[field if field != 'id' else 'launch']
                  for field in ['task', 'role', 'preset', 'thread', 'attempt', 'session', 'id']))
            write_json(output / (label + '.snapshot.json'), snapshot)
            write_json(output / (label + '.process.json'), call('pane_process_info', '--thread', item['thread']))
        write_json(output / 'owned-processes.json', owned)
        build = command_json(run([node, source / 'workbench/app/build.mjs', '--slot', 't091-three-' + fixture.name.rsplit('-', 1)[-1]], timeout=180))
        write_json(output / 'build.json', build)
        window_output = output / 'window'; window_output.mkdir()
        env['A2A_ELECTRON_DIAGNOSTICS'] = str(window_output / 'stages.jsonl')
        relative = (source / 'workbench/node_modules/electron/path.txt').read_text(encoding='utf-8').strip()
        executable = (source / 'workbench/node_modules/electron/dist' / relative).resolve(strict=True)
        argv = [str(executable), str(source / 'workbench/tests/electron_driver.mjs'), '--build', build['out'], '--state', str(state),
                '--task', task, '--user-data', str(fixture / 'ui'), '--output', str(window_output)]
        # Deliberately supply worker first; production sorts the verified role records.
        for item in [worker, *expected[:2]]:
            argv.extend(['--launch', item['launch']])
        write_json(output / 'electron-command.json', {'argv': argv, 'start_new_session': True})
        observer_attempted = True; result['electron_start_attempts'] += 1
        observer = Observer(argv, env, output); observer.identify(argv, output)
        ready = observer.receive()
        check('owned_electron_ready', ready.get('ready') is True and ready.get('pid') == observer.process.pid and ready.get('electron') == '43.4.1')
        observer.ready_confirmed = True
        view = wait(lambda: (value if len((value := observer.call('inspect-all')).get('panes', [])) == 3 and
            all(p.get('input_enabled') and p.get('window_id') and p.get('snapshot') for p in value['panes']) else None), 'three_bound_panes')
        check('exact_public_bridge', sorted(view['bridge']) == ['beginComposition', 'input', 'observeFocus', 'output', 'paneKeys', 'releaseQueue', 'snapshot'] and
              view['node'] == 'undefined' and view['pane_keys_frozen'] and view['pane_keys'] == [p['pane_key'] for p in view['panes']])
        check('three_distinct_keys_and_window_ids', len({p['pane_key'] for p in view['panes']}) == len({p['window_id'] for p in view['panes']}) == 3)
        check('no_auto_focus', not any(p['keyboard_focused'] or p['input_target'] for p in view['panes']))
        keys = {}
        for item, pane in zip(expected, view['panes']):
            label = item['preset'] or 'worker'; keys[label] = pane['pane_key']
            check(label + '_visible_full_identity', pane['launch'] == item['launch'] and pane['task'] == task and pane['role'] == item['role'] and
                  pane['preset'] == (item['preset'] or '') and pane['attempt'] == (item['attempt'] or '') and pane['thread'] == item['thread'] and
                  all(value in pane['text'] for value in [task, item['launch'], item['attempt'] or item['preset']]))
            raw = raw_output(item); (output / (label + '.first-screen.bin')).write_bytes(raw)
            if item['role'] == 'worker':
                check('worker_output_nonce', output_nonce.encode() in raw and item['launch'].encode() in raw)
            observed = wait(lambda: (v if (v := observer.call('inspect', pane_key=keys[label]))['offset'] >= len(raw) else None), label + '_output_cursor')
            chunks = [json.loads(line) for line in (window_output / 'received.ndjson').read_text(encoding='utf-8').splitlines()]
            stream = b''.join(base64.b64decode(chunk['data_base64']) for chunk in chunks if chunk['launch'] == item['launch'])
            check(label + '_own_stream_matches_raw_trace', stream.startswith(raw))
            check(label + '_output_nonce_isolation', (output_nonce in observed['terminal']) == (item['role'] == 'worker'))
        write_json(output / 'view-initial.json', view)
        before_negative = call('orchestration_events', '--task', task)['events']
        for label, invalid in [('wrong-task', foreign), ('old-launch', old)]:
            refused = observer.call('try-open', launches=[expected[0]['launch'], expected[1]['launch'], invalid['launch']])
            reason = 'launch_task_mismatch' if label == 'wrong-task' else 'Pane is not a current running session'
            check(label + '_third_pane_refused', refused.get('rejected') is True and refused.get('error') == 'Error: ' + reason and
                  refused['windows_before'] == refused['windows_after'] == [ready['browser_window']])
            write_json(output / (label + '.refusal.json'), refused)
        after_negative = call('orchestration_events', '--task', task)['events']
        check('no_refused_credentials', len([r for r in after_negative if r['type'] == 'window_opened']) ==
              len([r for r in before_negative if r['type'] == 'window_opened']) == 3)
        check('negative_inputs_empty', not call('issues', '--task', task)['user_inputs'] and (diagnostics / 'received.bin').read_bytes() == b'')
        result['negatives_passed'] = True
        for operation, values in [('snapshot', []), ('output', [0]), ('input', ['DENIED_SENTINEL']), ('beginComposition', []),
                                  ('releaseQueue', [{}]), ('observeFocus', ['\x1b[?1004h'])]:
            denied = observer.call('bridge-call', operation=operation, pane_key='absent-' + keys['worker'], args=values)
            check('unknown_key_' + operation, denied.get('rejected') is True)
        for label in ['ideation', 'executor', 'worker']:
            for operation, values in [('beginComposition', []), ('observeFocus', ['\x1b[?1004h'])]:
                response = observer.call('bridge-call', operation=operation, pane_key=keys[label], args=values)
                check(label + '_' + operation, response.get('resolved') is True and response['value']['ok'] is True)
        worker_view = observer.call('inspect', pane_key=keys['worker'])
        invalid_release = observer.call('bridge-call', operation='releaseQueue', pane_key=keys['worker'],
            args=[{'statement': '用户声明输入框已空', 'launch': worker['launch'], 'window_id': view['panes'][0]['window_id'], 'interruption': 0, 'input_generation': 0}])
        check('cross_pane_release_rejected', invalid_release.get('resolved') is True and invalid_release['value'].get('error') == 'empty_input_declaration_required')
        observer.call('focus-pane', pane_key=keys['worker'])
        def focused_worker():
            value = observer.call('inspect-all')
            return value if sum(p['input_target'] for p in value['panes']) == 1 and value['panes'][2]['input_target'] else None

        focused = wait(focused_worker, 'actual_worker_focus')
        check('blue_border_follows_worker', focused['panes'][2]['focused_border'] != 'none' and '正在输入' in focused['panes'][2]['text'])
        nonce = 'T091 三格输入 ' + uuid.uuid4().hex
        expected_bytes = ('\x1b[200~' + nonce + '\x1b[201~').encode('utf-8')
        write_json(output / 'input-oracle.json', {'text': nonce, 'expected_bytes': len(expected_bytes), 'target': worker, 'fixed_before': 'paste'})
        observer.call('terminal-input', pane_key=keys['worker'], paste=nonce, submit=False)
        wait(lambda: (diagnostics / 'received.bin').stat().st_size >= len(expected_bytes), 'worker_input_bytes')
        check('worker_exact_bytes', (diagnostics / 'received.bin').read_bytes() == expected_bytes)
        inputs = call('issues', '--task', task)['user_inputs']
        events = call('events', '--task', task)['events']
        orchestration = call('orchestration_events', '--task', task)['events']
        check('worker_input_record', len(inputs) == 1 and inputs[0]['text'] == nonce and inputs[0]['target']['attempt'] == worker['attempt'] and
              inputs[0]['target']['task'] == task and inputs[0]['target']['thread'] == worker['thread'] and inputs[0]['source_ref']['window_id'] == worker_view['window_id'])
        check('worker_intervention', len([r for r in events if r['type'] == 'human_intervention' and r['details'].get('input_id') == inputs[0]['id']]) == 1)
        for item, pane in zip(expected, view['panes']):
            admitted = [r['data'] for r in orchestration if r['type'] == 'window_request_admitted' and r['data']['window_id'] == pane['window_id']]
            check((item['preset'] or 'worker') + '_independent_sequence', [r['sequence'] for r in admitted] == list(range(1, len(admitted) + 1)) and len(admitted) >= 2)
            check((item['preset'] or 'worker') + '_composition_bound', len([r for r in admitted if r['command'] == 'window_composition']) == 1)
        written = [r for r in orchestration if r['type'] == 'terminal_input_written']
        check('one_worker_write_no_controller_write', len(written) == 1 and written[0]['launch'] == worker['launch'] and written[0]['data']['byte_length'] == len(expected_bytes))
        request_id = inputs[0]['source_ref']['command_id']
        sequence = inputs[0]['source_ref']['source_sequence']
        chain = [r for r in orchestration if r['type'] in ['window_request_admitted', 'terminal_input_write_intent', 'terminal_input_written'] and r['data'].get('request_id') == request_id]
        check('same_request_input_receipt_chain', [r['type'] for r in chain] == ['window_request_admitted', 'terminal_input_write_intent', 'terminal_input_written'] and
              all(r['launch'] == worker['launch'] and r['data']['window_id'] == worker_view['window_id'] and r['data']['sequence'] == sequence for r in chain) and
              chain[0]['data']['command'] == 'window_input' and chain[1]['data']['data'].encode('utf-8') == expected_bytes)
        check('no_enter_or_dispatch_release_in_visible_panes', not any(r['type'] in ['turn_submit_intent', 'turn_submitted', 'paste_intent'] and
              r.get('launch') in {item['launch'] for item in expected} for r in orchestration))
        write_json(output / 'input-records.json', inputs); write_json(output / 'gate-events.json', events)
        write_json(output / 'orchestration-before-close.json', orchestration)
        initial_bindings = [(p['pane_key'], p['window_id'], p['launch']) for p in view['panes']]
        before_scroll = observer.call('inspect-all')
        first_scroll = observer.call('scroll-pane', pane_key=keys['ideation'], left=100, top=20)
        after_scroll = observer.call('inspect-all')
        check('ideation_scroll_is_independent', first_scroll['scroll']['left'] == 100 and
              [p['scroll'] for p in after_scroll['panes'][1:]] == [p['scroll'] for p in before_scroll['panes'][1:]])
        second_scroll = observer.call('scroll-pane', pane_key=keys['executor'], left=150, top=30)
        after_second_scroll = observer.call('inspect-all')
        check('executor_scroll_is_independent', second_scroll['scroll']['left'] == 150 and
              after_second_scroll['panes'][0]['scroll'] == after_scroll['panes'][0]['scroll'] and
              after_second_scroll['panes'][2]['scroll'] == after_scroll['panes'][2]['scroll'])
        for width, height in [(1440, 900), (1200, 800), (900, 650), (1440, 900)]:
            resized = observer.call('resize', width=width, height=height)
            check(f'exact_window_size_{width}', resized['window_size'] == [width, height])
            def sized_view():
                value = observer.call('inspect-all')
                return value if visible(value, value['viewport']['width'], value['viewport']['height']) else None

            layout = wait(sized_view, f'visible_{width}')
            panes = layout['panes']; a, b, c = [p['bounds'] for p in panes]
            check(f'layout_{width}_{height}', (abs(a['y'] - b['y']) < 1 and b['x'] > a['x'] and c['y'] > a['y'] and abs(c['width'] - a['width'] - b['width']) < 2)
                  if width >= 1000 else (a['y'] < b['y'] < c['y'] and abs(a['x'] - b['x']) < 1 and abs(a['width'] - c['width']) < 1))
            check(f'bindings_survive_resize_{width}', [(p['pane_key'], p['window_id'], p['launch']) for p in panes] == initial_bindings)
            check(f'focus_survives_resize_{width}', [p['input_target'] for p in panes] == [False, False, True])
            filename = f'view-{width}x{height}.json'
            if not (output / filename).exists():
                write_json(output / filename, layout)
                name = 'green-original.png' if width == 1440 else f'green-{width}x{height}-original.png'
                capture = command_json(run([sys.executable, script_dir / 'capture_window.py', '--owner', output / 'electron-owner.json', '--output', output / name]))
                write_json(output / (name + '.capture.json'), capture)
        observer.call('blur-pane', pane_key=keys['worker'])
        wait(lambda: not any(p['input_target'] for p in observer.call('inspect-all')['panes']), 'worker_blurred')
        result.update(green_observed=True, fixture_task=task, panes=initial_bindings, screenshot=str(output / 'green-original.png'))
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
            result['driver_rpc_count'] = observer.number
            result['observer_stdout_bytes'] = (output / 'observer.stdout.bin').stat().st_size
        stages = window_output / 'stages.jsonl' if 'window_output' in locals() else None
        if stages is not None and stages.exists():
            try:
                rows = [json.loads(line) for line in stages.read_text(encoding='utf-8').splitlines()]
                result['screen_read_count'] = sum(row.get('stage') == 'screen_read' for row in rows)
                result['electron_windows_created'] = sum(row.get('stage') == 'window_created' for row in rows)
            except (OSError, ValueError) as error:
                result['metrics_error'] = repr(error)
        result['capture_count'] = len(list(output.glob('green-*-original.png'))) + int((output / 'green-original.png').exists())
        ready_confirmed = observer.ready_confirmed if observer is not None else False
        result.update(electron_exit_confirmed=electron_closed, electron_ready_confirmed=ready_confirmed)
        if started and electron_closed and (not observer_attempted or ready_confirmed):
            try:
                if result['green_observed']:
                    try:
                        after_close = call('orchestration_events', '--task', task)['events']
                        closed = [r['data']['window_id'] for r in after_close if r['type'] == 'window_closed']
                        check('three_credentials_closed', sorted(closed) == sorted(row[1] for row in initial_bindings))
                        for item in expected:
                            info = call('pane_process_info', '--thread', item['thread'])
                            check((item['preset'] or 'worker') + '_survives_window', info['leader'] == item['leader'] and not info.get('failed'))
                            write_json(output / ((item['preset'] or 'worker') + '.after-window.process.json'), info)
                        write_json(output / 'orchestration-after-window.json', after_close)
                    except Exception as error:
                        result.update(green_observed=False, post_close_error=repr(error))
                call('daemon_stop')
                for owner in owned:
                    wait(lambda: absent(owner), 'writer_exit_deadline', timeout=15)
                if (state / 'control.sock').exists() or (state / 'daemon.pid').exists():
                    raise RuntimeError('daemon_endpoint_exit_unconfirmed')
                if worker_start_attempted != worker_bound:
                    raise RuntimeError('worker_identity_unbound; retain fixture')
                result['cleanup_complete'] = not cleanup_errors
                if credential.exists():
                    credential.unlink()
            except Exception as error:
                cleanup_errors.append({'backend': repr(error)})
        elif started:
            result['backend_cleanup_deferred'] = 'unconfirmed Electron ready/exit; wait for controller; no daemon_stop or archive'
        if api is not None:
            api.shutdown(); api.server_close()
        result['fake_posts'] = sum(row['method'] == 'POST' for row in requests)
        result['controlled_receiver_start_attempts'] = worker_start_attempted
        write_json(output / 'fake-api-requests.json', requests)
        result['cleanup_errors'] = cleanup_errors
        if result['cleanup_complete']:
            try:
                copied = archive_fixture(fixture, output / 'fixture')
                replay = shlex.join([sys.executable, str(Path(__file__).resolve()), '--source', str(source), '--output', str(output) + '-replay-new', '--label', args.label + '-replay-new', '--approval-ref', '<本次新批准引用>'])
                manifest = {'original': str(fixture), 'archive': str(output / 'fixture'), **copied, 'original_retained': True, 'replay': replay}
                write_json(script_dir / f'{args.label}.archive.json', manifest)
                result.update(archive=manifest, archive_complete=True)
            except Exception as error:
                result['archive_error'] = repr(error)
        result['status'] = 'PASS' if result['green_observed'] and result['negatives_passed'] and result['cleanup_complete'] and result['archive_complete'] and result['fake_posts'] == 0 and not result.get('error') and not result.get('metrics_error') and result.get('screen_read_count', 361) <= 360 and result['capture_count'] == 3 and result.get('electron_windows_created') == 1 else 'INCOMPLETE'
        write_json(output / 'run.json', result); write_json(script_dir / f'{args.label}.run.json', result)
    print(json.dumps({key: result.get(key) for key in ['status', 'green_observed', 'negatives_passed', 'cleanup_complete',
        'archive_complete', 'fake_posts', 'controller_start_attempts', 'controlled_receiver_start_attempts',
        'real_codex_cli_starts', 'electron_start_attempts', 'screen_read_count', 'capture_count', 'error']}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
