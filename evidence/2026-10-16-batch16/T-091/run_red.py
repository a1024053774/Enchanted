#!/usr/bin/env python3
"""T-091 red readback. CONTROLLER EXECUTION ONLY; product code must remain unchanged.

Review this inventory before running (current approval only; no T-078 approval reuse):
  CLI: Node >=26.5 <27; fixed Claude 2.1.296 --version plus TWO interactive starts;
       one compiled t078_native_receiver.c (NOT Codex); production daemon + zsh PTYs;
       one Electron 43.4.1 process with production built run(); git in a NEW fixture;
       clang; /bin/ps readbacks; screencapture for the verified owned window only.
  Hooks: production per-launch UserPromptSubmit/Stop/PermissionRequest command hooks
       are passed in Claude settings (3s) and receiver argv (10s). Hook command:
       NODE SOURCE/workbench/src/gates/cli.ts --state ISOLATED_STATE signal --launch UUID.
       Receiver argv includes --dangerously-bypass-hook-trust; it is a controlled
       C receiver, never Codex. No global hooks/settings.
       No synthetic hook is triggered. Receiver does not invoke hooks without marker files.
       Fixture Git uses /dev/null hooks. No submit, verify, integrate, reclaim or push.
  Keys: ZERO; no Enter/Escape/trust/theme/permission keys, no paste, focus or queue release.
       Only terminal protocol replies already owned by the daemon are allowed.
  Budget: supplier model turns 0; fake Messages roots 0; fake Messages POSTs 0;
       worker model turns 0; Claude starts 2, worker receiver starts 1, Electron starts 1.
       Product turn_limit must be 1 (schema minimum); this runner never releases a prompt.
  Isolation: NEW /private/tmp/t078-2-t091-red-* HOME/state/user-data; loopback API
       rejects every POST; no auth.json or login credential is read/copied.
  End: close owned Electron; daemon_stop only this state; confirm registered PIDs exit;
       copy the stopped fixture to the mounted external evidence volume, compare counts
       and bytes, retain the original. Only text summaries/manifests go into the repo.
       Electron normal quit uses NSRunningApplication.terminate() for its verified PID;
       no close RPC, signal, force quit, or process-group kill. If exit is unconfirmed,
       do NOT stop the daemon or archive the live fixture; stop and report.
       A process stuck before ready cannot accept normal quit (red-01 observation).
       Without a confirmed ready handshake, do not attempt normal quit: wait for
       the controller. This script NEVER sends SIGTERM, including this failure.
  Missing permission / setup or cleanup failure => INCOMPLETE. Preserve first-screen
       bytes for controller review; no screen is treated as ready or approved for keys.
       No permission request, retry, fallback, real login, or substitute model run.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import selectors
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from capture_window import process_identity
from owned_electron import normal_quit

BASELINE = '44bbb7828459d81fab0d46069a19d3dd515a7732'
CLAUDE = '/Users/luckye/.local/share/claude/versions/2.1.296'
VOLUME = Path('/Volumes/WD-Elements')


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def inventory(root):
    root = Path(os.path.abspath(root))
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise RuntimeError('fixture_archive_root_must_be_directory')
    entries, links, pending = [], [], [root]
    regular_files = regular_bytes = link_bytes = directories = 0
    while pending:
        with os.scandir(pending.pop()) as children:
            for child in children:
                path = Path(child.path)
                relative = path.relative_to(root).as_posix()
                info = child.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    target = os.readlink(path)
                    size = len(os.fsencode(target))
                    # Classify the target text lexically. Do not resolve, stat,
                    # open or descend through the target, including link chains.
                    lexical = os.path.abspath(os.path.join(path.parent, target))
                    outside = os.path.commonpath([str(root), lexical]) != str(root)
                    links.append({'path': relative, 'target': target, 'bytes': size,
                                  'outside_fixture': outside, 'lexical_target': lexical})
                    entries.append({'path': relative, 'kind': 'symlink', 'bytes': size, 'target': target})
                    link_bytes += size
                elif stat.S_ISDIR(info.st_mode):
                    entries.append({'path': relative, 'kind': 'directory'})
                    directories += 1
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    entries.append({'path': relative, 'kind': 'file', 'bytes': info.st_size})
                    regular_files += 1
                    regular_bytes += info.st_size
                else:
                    raise RuntimeError('fixture_archive_contains_live_special_file: ' + relative)
    return {'files': regular_files + len(links), 'bytes': regular_bytes + link_bytes,
            'regular_files': regular_files, 'regular_bytes': regular_bytes,
            'symlink_count': len(links), 'symlink_bytes': link_bytes, 'directories': directories,
            'entries': sorted(entries, key=lambda row: row['path']),
            'symlinks': sorted(links, key=lambda row: row['path'])}


def archive_fixture(source, destination):
    before = inventory(source)
    shutil.copytree(source, destination, symlinks=True)
    after = inventory(destination)
    compared = [key for key in before if key != 'symlinks']
    if any(before[key] != after[key] for key in compared):
        raise RuntimeError('archive_file_count_bytes_or_link_target_mismatch')
    archived_links = {row['path']: row for row in after['symlinks']}
    return {**{key: before[key] for key in compared if key != 'entries'},
            'symlinks': [{**row, 'outside_archive_fixture': archived_links[row['path']]['outside_fixture'],
                          'archive_lexical_target': archived_links[row['path']]['lexical_target']}
                         for row in before['symlinks']],
            'symlink_policy': 'copy link itself; compare exact target text; never follow targets',
            'bytes_definition': 'regular file bytes plus filesystem-encoded link target bytes; directories excluded',
            'comparison': True}


class Observer:
    def __init__(self, argv, env, output):
        self.log = (output / 'observer-protocol.jsonl').open('x', encoding='utf-8')
        self.stderr = (output / 'observer.stderr.txt').open('xb')
        self.stdout = (output / 'observer.stdout.bin').open('xb')
        self.process = subprocess.Popen(argv, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.stderr, start_new_session=True, bufsize=0)
        self.selector = selectors.DefaultSelector()
        os.set_blocking(self.process.stdout.fileno(), False)
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer = bytearray()
        self.number = 0
        self.owner = None
        self.exit_confirmed = False
        self.ready_confirmed = False

    def identify(self, argv, output):
        # Save ownership before waiting for any ready/protocol response.
        self.owner = {**process_identity(self.process.pid), 'driver': argv[1], 'executable': argv[0]}
        write_json(output / 'electron-owner.json', self.owner)

    def receive(self, timeout=40):
        deadline = time.monotonic() + timeout
        while True:
            end = self.buffer.find(b'\n')
            if end >= 0:
                line = bytes(self.buffer[:end + 1]); del self.buffer[:end + 1]
                self.log.write(line.decode('utf-8')); self.log.flush()
                return json.loads(line)
            if not self.selector.select(max(0, deadline - time.monotonic())):
                raise TimeoutError('observer_response_deadline')
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('observer_exited_before_response')
            self.stdout.write(chunk); self.stdout.flush(); self.buffer.extend(chunk)

    def call(self, command):
        self.number += 1
        self.process.stdin.write((json.dumps({'id': self.number, 'command': command}) + '\n').encode())
        self.process.stdin.flush()
        result = self.receive()
        if result.get('id') != self.number or result.get('ok') is not True:
            raise RuntimeError({'observer_request_failed': result})
        return result['value']

    def close(self):
        # Normal quit is independent of the observer's stdin/ready protocol.
        try:
            if self.process.poll() is None:
                if self.owner is None:
                    raise RuntimeError('electron_owner_unconfirmed; stop without closing another process')
                if not self.ready_confirmed:
                    raise RuntimeError('electron_startup_unconfirmed_wait_for_controller; normal_quit_not_attempted; automatic_sigterm_disabled')
                def observe(value):
                    self.log.write(json.dumps(value) + '\n'); self.log.flush()
                normal_quit(self.owner, observe=observe, child=self.process)
            self.exit_confirmed = self.process.poll() is not None
            if not self.exit_confirmed:
                raise RuntimeError('electron_exit_unconfirmed')
            if self.process.returncode != 0:
                raise RuntimeError('observer_exit_nonzero')
        finally:
            # Preserve available bytes even if normal exit was not confirmed.
            # The child records a detached protocol in its file, without exiting.
            while self.selector.select(0):
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    self.selector.unregister(self.process.stdout)
                    break
                self.stdout.write(chunk)
            self.stdout.flush()
            self.selector.close()
            self.log.close(); self.stderr.close(); self.stdout.close()
            self.process.stdin.close(); self.process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='NEW directory under the mounted external T-091 evidence directory')
    parser.add_argument('--label', required=True, help='New text summary prefix, e.g. red-02')
    parser.add_argument('--approval-ref', required=True, help='Current controller approval for this exact inventory')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    script_dir = Path(__file__).resolve().parent
    allowed_output = (VOLUME / 'a2a-evidence/2026-10-16-batch16/T-091').resolve()
    output = args.output.resolve()
    if not os.path.ismount(VOLUME) or not output.is_relative_to(allowed_output) or output == allowed_output:
        raise RuntimeError('mounted_external_evidence_directory_required')
    if not args.label or any(char not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for char in args.label):
        raise RuntimeError('invalid_summary_label')
    for suffix in ['run.json', 'archive.json', 'RESULTS.md']:
        if (script_dir / f'{args.label}.{suffix}').exists():
            raise RuntimeError('summary_already_exists; choose a new label')
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t078-2-t091-red-', dir='/private/tmp')).resolve()
    for name in ['repo', 'state', 'home', 'receiver-home', 'tmp', 'ui', 'bin']:
        (fixture / name).mkdir()
    credential = fixture.parent / (fixture.name + '-operator.json')  # Outside archived fixture.
    env = {key: os.environ[key] for key in ['PATH', 'USER', 'LOGNAME'] if key in os.environ}
    env.update(HOME=str(fixture / 'home'), TMPDIR=str(fixture / 'tmp'), LANG='en_US.UTF-8', LC_ALL='C',
               A2A_OPERATOR_CREDENTIAL=str(credential), GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T091 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T091 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    sys.path.insert(0, str(source / 'workbench/tests'))
    from command_evidence import CommandLog, command_json
    commands = CommandLog(output)
    result = {'status': 'INCOMPLETE', 'phase': 'red-readback', 'task': 'T-091', 'attempt': 'a1',
              'worker': 's16-t091', 'worker_launch': 'launch-a818e11600754e8b8ad79aab63a17f83',
              'baseline': BASELINE, 'approval_ref': args.approval_ref, 'argv': sys.argv,
              'fixture': str(fixture), 'output': str(output), 'supplier_model_turns': 0,
              'keys': [], 'synthetic_hooks': [], 'red_observed': False, 'cleanup_complete': False,
              'cleanup_policy': {'before_ready': 'stop_wait_for_controller; no normal quit request',
                                 'after_ready': 'owner-verified normal quit, then confirm exit',
                                 'signals': 'no automatic SIGTERM or force quit'}}
    started = False
    observer = None
    observer_attempted = False
    api = None
    owned = []
    requests = []
    requests_lock = threading.Lock()
    cli = []

    def run(argv, timeout=60):
        value = commands.run(argv, cwd=source, env=env, timeout=timeout)
        if value.returncode != 0:
            raise RuntimeError({'command_id': value.evidence['id'], 'exit': value.returncode})
        return value

    def call(command, *values):
        value = command_json(run([*cli, command, *values]))
        if value.get('ok') is not True:
            raise RuntimeError({'daemon_request_rejected': value})
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

    try:
        node = shutil.which('node', path=env.get('PATH'))
        if not node:
            raise RuntimeError('node_required')
        version = run([node, '--version']).stdout.strip()
        if not version.startswith('v26.') or int(version.split('.')[1]) < 5:
            raise RuntimeError('node_26_5_or_later_26_required')
        result['node_version'] = version
        result['source_revision'] = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        product_diff = run(['git', 'diff', BASELINE, '--', 'workbench/app/', 'workbench/src/', 'workbench/tests/']).stdout
        if product_diff:
            raise RuntimeError('red_requires_unchanged_baseline_product_and_tests')
        write_json(output / 'source.json', {'revision': result['source_revision'], 'baseline': BASELINE,
                                          'product_diff': product_diff, 'source': str(source)})
        state, repo = fixture / 'state', fixture / 'repo'
        cli = [node, source / 'workbench/src/gates/cli.ts', '--state', state]
        run(['git', '-C', repo, 'init', '-b', 'main'])
        (repo / 'value.txt').write_text('T091 isolated red fixture\n', encoding='utf-8')
        run(['git', '-C', repo, 'add', 'value.txt'])
        run(['git', '-C', repo, 'commit', '-m', 'T091 independent three-pane fixture'])
        receiver = fixture / 'bin/codex-receiver'
        run(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11',
             source / 'workbench/tests/t078_native_receiver.c', '-o', receiver])
        role = fixture / 'receiver-role.md'
        role.write_text('仅收集终端字节；不运行模型，不执行任务，不触发合成 hook。\n', encoding='utf-8')
        config = {'codex_bin': str(receiver), 'codex_home': str(fixture / 'receiver-home'),
                  'role_card': str(role), 'role_card_revision': 'T-091-red',
                  'code_revision': result['source_revision'], 'source_snapshot': str(source),
                  'hook_authorization': args.approval_ref, 'turn_limit': 1,
                  'turn_authorization': args.approval_ref + ': zero model turns; no release or input'}
        write_json(fixture / 'launch.json', config)

        class RejectAPI(BaseHTTPRequestHandler):
            def log_message(self, *unused):
                pass

            def do_GET(self):
                self.answer()

            def do_POST(self):
                self.answer()

            def answer(self):
                length = int(self.headers.get('Content-Length', '0'))
                if length > 1024 * 1024:
                    self.send_error(413)
                    return
                self.rfile.read(length)
                row = {'method': self.command, 'path': self.path, 'bytes': length,
                       'public_fixture_bearer': self.headers.get('Authorization') == 'Bearer a2a-fixture-key-not-a-secret'}
                with requests_lock:
                    requests.append(row)
                    with (output / 'fake-api-requests.jsonl').open('a', encoding='utf-8') as stream:
                        stream.write(json.dumps(row) + '\n')
                body = b'{"type":"error","error":{"type":"permission_error","message":"T091 zero root budget"}}'
                self.send_response(403); self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

        api = ThreadingHTTPServer(('127.0.0.1', 0), RejectAPI)
        api.daemon_threads = True
        threading.Thread(target=api.serve_forever, daemon=True).start()
        api_url = f'http://127.0.0.1:{api.server_port}/'
        result['fake_api_url'] = api_url
        (fixture / 'api-identity.json').write_text(json.dumps({'pid': os.getpid(), 'url': api_url}), encoding='utf-8')
        daemon = call('daemon_start', '--launch-config', fixture / 'launch.json')
        started = True
        owned.append(process_identity(daemon['pid']))
        task = 't091-red-' + uuid.uuid4().hex[:8]
        card = {'id': task, 'source': None, 'goal': '核对同一任务三窗格的基线现状',
                'non_goals': ['不输入、不运行模型、不交付或集成'],
                'paths': {'allow': ['value.txt'], 'deny': []}, 'oracle_paths': ['value.txt'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c', 'raise SystemExit(0)']}],
                'red_commands': [], 'task_type': '前端界面', 'repair_target': None, 'complexity': 'L',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'},
                'base_commit': None, 'writer': None}
        write_json(fixture / 'card.json', card)
        call('card_save', '--task', task, '--card', fixture / 'card.json', '--expected-version', '0')
        call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main',
             '--card-version', '1', '--project', 't091-isolated', '--title', 'T-091 同任务三窗格基线')
        expected = []
        for preset in ['ideation', 'executor']:
            root = fixture / 'roles' / preset
            for directory in ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']:
                (root / directory).mkdir(parents=True)
            (root / 'claude/settings.json').write_text('{"theme":"dark"}\n', encoding='utf-8')
            (root / 'role.md').write_text('本次只停在隔离首屏，等待主控；不得发送任务或使用工具。\n', encoding='utf-8')
            manifest = {'schema': 1, 'root': str(fixture), 'state': str(state), 'task': task, 'preset': preset,
                        'launch': str(uuid.uuid4()), 'session': str(uuid.uuid4()), 'thread': str(uuid.uuid4()),
                        'executable': CLAUDE, 'role_file': str(root / 'role.md'),
                        'code_revision': result['source_revision'], 'source_snapshot': str(source),
                        'api_url': api_url, 'turn_limit': 1}
            write_json(root / 'manifest.json', manifest)
            # Preflight has the same isolated HOME/config/tmp as the actual role.
            role_env = {**env, 'HOME': str(root / 'home'), 'CLAUDE_CONFIG_DIR': str(root / 'claude'),
                        'TMPDIR': str(root / 'tmp'), 'DISABLE_AUTOUPDATER': '1'}
            preflight = commands.run([CLAUDE, '--version'], cwd=source, env=role_env, timeout=20)
            if preflight.returncode != 0 or preflight.stdout.strip() != '2.1.296 (Claude Code)':
                raise RuntimeError('fixed_claude_version_mismatch')
            launch = call('controller_start', '--task', task, '--manifest', root / 'manifest.json')['launch']
            expected.append({'task': task, 'role': 'controller', 'preset': preset, 'launch': manifest['launch'],
                             'thread': manifest['thread'], 'session': manifest['session'], 'attempt': None})
            write_json(output / f'{preset}.launch.json', launch)

        attempt = call('dispatch', '--task', task, '--runtime-mode', 'workspace-write')['attempt']
        wait(lambda: (fixture / 'receiver-home/receiver-started.json').exists(), 'receiver_start_deadline')
        worker = call('workbench_snapshot', '--task', task)['launch']
        expected.append({'task': task, 'role': 'worker', 'preset': None, 'launch': worker['id'],
                         'thread': attempt['thread_id'], 'session': attempt['session_id'], 'attempt': attempt['attempt_id']})
        write_json(output / 'expected.json', {'task': task, 'panes': expected, 'required_visible_count': 3})
        for item in expected:
            info = None

            def observed():
                nonlocal info
                info = call('pane_process_info', '--thread', item['thread'])
                if info.get('failed'):
                    raise RuntimeError({'pane_identity_failed': info})
                if item['role'] == 'controller':
                    return info.get('leader') is not None and info.get('native_session') == item['session']
                receiver_started = json.loads((fixture / 'receiver-home/receiver-started.json').read_text(encoding='utf-8'))
                return info.get('leader') == receiver_started['pid'] and info.get('native_session') == receiver_started['native_session']

            wait(observed, 'foreground_identity_deadline')
            owned.extend([process_identity(info['shell_pid']), process_identity(info['leader'])])
            snapshot = call('workbench_snapshot', '--task', task, '--launch', item['launch'])
            if snapshot['launch']['id'] != item['launch'] or snapshot['launch']['task'] != task or \
                    snapshot['launch']['role'] != item['role'] or snapshot['launch']['thread'] != item['thread']:
                raise RuntimeError('snapshot_binding_mismatch')
            label = item['preset'] or 'worker'
            write_json(output / (label + '.snapshot.json'), snapshot)
            write_json(output / (label + '.process.json'), info)
            chunk = call('pane_output', '--launch', item['launch'], '--offset', '0', '--max-bytes', '65536')
            (output / ((item['preset'] or 'worker') + '.first-screen.bin')).write_bytes(base64.b64decode(chunk['data_base64']))
        write_json(output / 'owned-processes.json', owned)
        slot = 't091-red-' + fixture.name.rsplit('-', 1)[-1]
        build = command_json(run([node, source / 'workbench/app/build.mjs', '--slot', slot], timeout=180))
        write_json(output / 'build.json', build)
        plan = {'build': build['out'], 'state': str(state), 'task': task, 'userData': str(fixture / 'ui'),
                'launches': [item['launch'] for item in expected]}
        write_json(output / 'window-plan.json', plan)
        relative = (source / 'workbench/node_modules/electron/path.txt').read_text(encoding='utf-8').strip()
        executable = (source / 'workbench/node_modules/electron/dist' / relative).resolve(strict=True)
        argv = [str(executable), str(script_dir / 'red_window.mjs'), str(output / 'window-plan.json'),
                str(output / 'observer-events.jsonl')]
        write_json(output / 'electron-command.json', {'argv': argv, 'start_new_session': True})
        observer_attempted = True
        observer = Observer(argv, env, output)
        observer.identify(argv, output)
        ready = observer.receive()
        if ready.get('ready') is not True or ready.get('pid') != observer.process.pid or ready.get('electron') != '43.4.1':
            raise RuntimeError('electron_owner_not_confirmed')
        observer.ready_confirmed = True
        result['electron_version'] = ready['electron']
        owner = observer.owner
        if process_identity(observer.process.pid) != {key: owner[key] for key in ['pid', 'started', 'command']}:
            raise RuntimeError('electron_owner_changed_during_startup')
        view = None

        def view_ready():
            nonlocal view
            view = observer.call('inspect')
            return any(region['launch'] == worker['id'] and region['terminal'] and region['offset'] > 0
                       for region in view['regions'])

        wait(view_ready, 'baseline_terminal_readback_deadline')
        write_json(output / 'view.json', view)
        capture = command_json(run([sys.executable, script_dir / 'capture_window.py', '--owner', output / 'electron-owner.json',
                                    '--output', output / 'baseline-original.png']))
        write_json(output / 'capture.json', capture)
        events = call('orchestration_events', '--task', task)['events']
        write_json(output / 'events-before-close.json', events)
        forbidden = {'terminal_input_write_intent', 'terminal_input_written', 'paste_intent', 'paste_written', 'turn_submitted'}
        if any(event['type'] in forbidden for event in events):
            raise RuntimeError('zero_input_budget_exceeded')
        with requests_lock:
            posts = [row for row in requests if row['method'] == 'POST' and row['path'].split('?')[0].rstrip('/') == '/v1/messages']
        if posts:
            raise RuntimeError('fake_messages_post_budget_exceeded')
        visible = [region for region in view['regions'] if region['visible'] and region['terminal']]
        result.update(fixture_task=task, expected_visible_launches=plan['launches'],
                      observed_visible_launches=[region['launch'] for region in visible],
                      browser_window=view['browser_window'], fake_messages_posts=len(posts),
                      screenshot=str(output / 'baseline-original.png'))
        if view['windows'] != [view['browser_window']] or len(visible) != 1 or visible[0]['launch'] != worker['id']:
            raise RuntimeError('baseline_readback_did_not_match_the_expected_single_pane_limitation')
        # Independent contract: one BrowserWindow must show all THREE expected launches.
        result.update(red_observed=True, contract='three simultaneous session panes under one task',
                      expected=3, observed=len(visible), failure='required_three_visible_panes_observed_one')
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
        result['electron_exit_confirmed'] = electron_closed
        result['electron_ready_confirmed'] = observer.ready_confirmed if observer is not None else False
        if started and not electron_closed:
            result['backend_cleanup_deferred'] = 'Electron exit unconfirmed; daemon_stop and fixture archive were not attempted'
        if started and electron_closed:
            try:
                call('daemon_stop')
                # Only observations here; the daemon owns stopping its registered PTYs.
                for identity in owned:
                    deadline = time.monotonic() + 15
                    while True:
                        process = commands.run(['/bin/ps', '-ww', '-p', str(identity['pid']), '-o', 'pid=,lstart=,command='],
                                               cwd=source, env={**env, 'LC_ALL': 'C'}, timeout=5)
                        if process.returncode == 1 and not process.stdout.strip() and not process.stderr.strip():
                            break
                        if process.returncode != 0 or process.stderr.strip() or time.monotonic() >= deadline:
                            raise RuntimeError({'owned_process_exit_unconfirmed': identity})
                        time.sleep(0.1)
                if (fixture / 'state/control.sock').exists() or (fixture / 'state/daemon.pid').exists():
                    raise RuntimeError('daemon_endpoint_exit_unconfirmed')
                result['cleanup_complete'] = not cleanup_errors
                if credential.exists():
                    credential.unlink()
            except Exception as error:
                cleanup_errors.append({'daemon': repr(error)})
        if api is not None:
            api.shutdown(); api.server_close()
        result['fake_api_stopped'] = True
        with requests_lock:
            result['fake_messages_posts_final'] = sum(row['method'] == 'POST' and
                row['path'].split('?')[0].rstrip('/') == '/v1/messages' for row in requests)
        result['cleanup_errors'] = cleanup_errors
        if result['cleanup_complete']:
            try:
                archive = output / 'fixture'
                copied = archive_fixture(fixture, archive)
                replay = shlex.join([sys.executable, str(Path(__file__).resolve()), '--source', str(source),
                                   '--output', str(output) + '-replay-new', '--label', args.label + '-replay-new',
                                   '--approval-ref', '<本次新批准引用>'])
                manifest = {'original': str(fixture), 'archive': str(archive), **copied,
                            'replay': replay, 'original_retained': True}
                write_json(script_dir / f'{args.label}.archive.json', manifest)
                result['archive'] = manifest
            except Exception as error:
                result['archive_error'] = repr(error)
        write_json(output / 'run.json', result)
        write_json(script_dir / f'{args.label}.run.json', result)
        text = ('# T-091 红态读回\n\n状态：INCOMPLETE（产品尚未实现）。\n\n'
                f"预期红态已观察：{result['red_observed']}；收尾已核对：{result['cleanup_complete']}。\n\n"
                f"完整命令与原件：`{output}`；本轮批准：{args.approval_ref}。\n\n"
                '未执行输入、绿态或回归；未运行真实供应商模型。环境、启动、截图或收尾错误不算产品红态。\n')
        with (script_dir / f'{args.label}.RESULTS.md').open('x', encoding='utf-8') as stream:
            stream.write(text)
    print(json.dumps({'status': 'INCOMPLETE', 'red_observed': result['red_observed'],
                      'cleanup_complete': result['cleanup_complete'], 'output': str(output)}, ensure_ascii=False))
    # Expected red is a contract failure, never a green product verdict.
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
