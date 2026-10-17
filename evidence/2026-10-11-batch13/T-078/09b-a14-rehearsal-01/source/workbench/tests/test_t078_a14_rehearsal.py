"""Real daemon/relay/PTY/HTTP/Electron rehearsal; deterministic roles, no model."""
import argparse
import ast
import importlib.util
import json
import os
import base64
import shutil
import signal
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
from contextlib import closing
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
TESTS = SOURCE / 'workbench/tests'
STRUCTURE = BASE / '09b-a14-rehearsal-fixture-01/request-structure.json'
NODE = Path('/opt/homebrew/bin/node').resolve()
CLI = SOURCE / 'workbench/src/gates/cli.ts'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def require(condition, step, observed=None, expected=None):
    if not condition:
        raise AssertionError({'step': step, 'observed': observed, 'expected': expected})


def wait_for(step, observe, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = observe()
        if value:
            return value
        time.sleep(.05)
    raise TimeoutError({'step': step, 'deadline_seconds': seconds})


def preflight():
    paths = [NODE, CLI, Path('/usr/bin/clang'), TESTS / 't078_native_receiver.c',
             TESTS / 't078_09b_rehearsal_host.ts', TESTS / 't078_09b_rehearsal_peer.py',
             TESTS / 't078_09b_fake_api.py', TESTS / 't078_09b_phase_registry.py', TESTS / 't078_09b_phase_driver.py',
             TESTS / 't078_09b_i1_driver.py', TESTS / 't078_09b_i1_permission.py', TESTS / 'electron_driver.mjs',
             BASE / 'prepare-a14.py', STRUCTURE]
    for path in paths:
        require(path.is_file(), 'command_path', str(path), 'existing file')
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    structure = json.loads(STRUCTURE.read_bytes())
    schema = structure['request']['tools'][0]['input_schema']
    require(schema['required'] == ['command'] and 'argv' not in schema['properties'], 'captured_bash_schema', schema)
    require(not structure['redaction']['credentials_copied'], 'redaction_credentials', structure['redaction'])
    require(all(not key.lower().startswith(('authorization', 'api_key', 'token', 'metadata')) for key in structure['request']),
            'request_structure_whitelist', list(structure['request']))
    # Exercise the actual peer's pure request/SSE/command functions before any
    # external-stage execution. No process, socket, scratch or model is started.
    spec = importlib.util.spec_from_file_location('rehearsal_peer_preflight', TESTS / 't078_09b_rehearsal_peer.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    messages = module.initial_messages(structure, '⟦主控 #37⟧\n中文  scratch')
    require(any(block.get('text') == '⟦主控 #37⟧\n中文  scratch' for item in messages for block in item['content']),
            'captured_shape_injection')
    result = module.tool_result_message(structure, {'id': 'fixture-tool'},
             {'ok': True, 'queued': True, 'delivered': False, 'request_id': 'fixture-request', 'path': '/fixture/fixture-request.json'})
    require(json.loads(result['content'][0]['content'])['delivered'] is False, 'recorded_queued_shape')
    return {'status': 'PASS', 'scope': 'file/AST/sanitized request construction only', 'paths': list(map(str, paths)),
            'no_runtime_started': True, 'sources': [structure['source_initial'], structure['source_tool_result']],
            'real_timeout_seconds': 180, 'hard_timeout_seconds': 500}


class Scene:
    def __init__(self, output, kind):
        self.output = output; output.mkdir()
        self.kind = kind; self.root = Path(tempfile.mkdtemp(prefix='t078-2-a14-rehearsal-', dir='/private/tmp')).resolve()
        self.state = self.root / 'state'; self.children = []; self.commands = []; self.number = 0
        self.ready = None; self.request_dir = None
        self.env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
        for name in ['state', 'repo', 'repo/oracle', 'oracle', 'manager-home', 'tmp', 'target/home', 'target/bin']:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.env.update(HOME=str(self.root / 'manager-home'), TMPDIR=str(self.root / 'tmp'),
                        A2A_OPERATOR_CREDENTIAL=str(self.root / 'operator.json'),
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
                        GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false', PYTHONDONTWRITEBYTECODE='1',
                        GIT_AUTHOR_NAME='T078 rehearsal', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                        GIT_COMMITTER_NAME='T078 rehearsal', GIT_COMMITTER_EMAIL='fixture@example.invalid')
        save(output / 'owner.json', {'root': str(self.root), 'kind': kind, 'harness_pid': os.getpid(), 'no_vendor_process': True})

    def command(self, argv, timeout=30):
        self.number += 1; name = f'command-{self.number:03d}'
        argv = list(map(str, argv)); started = time.monotonic()
        try:
            result = subprocess.run(argv, cwd=SOURCE, env=self.env, capture_output=True, text=True,
                                    timeout=timeout, start_new_session=True)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode('utf-8', 'replace') if isinstance(value, bytes) else value
            save(self.output / (name + '.json'), {'argv': argv, 'status': 'INCOMPLETE', 'step': 'native_command_deadline',
                 'timeout_seconds': timeout, 'stdout': decoded(error.stdout), 'stderr': decoded(error.stderr),
                 'elapsed_seconds': time.monotonic() - started})
            raise
        value = {'argv': argv, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
                 'elapsed_seconds': time.monotonic() - started}
        save(self.output / (name + '.json'), value); self.commands.append(value)
        require(result.returncode == 0, 'native_command_exit', value, 0)
        return result.stdout

    def gate(self, command, *args):
        result = self.command([NODE, CLI, '--state', self.state, command, *args], timeout=35)
        value = json.loads(result.strip().splitlines()[-1])
        require(value.get('ok') is True, 'gate_' + command, value, 'ok=true')
        return value

    def spawn(self, name, argv):
        with (self.output / (name + '.stdout.bin')).open('xb') as stdout, (self.output / (name + '.stderr.bin')).open('xb') as stderr:
            child = subprocess.Popen(list(map(str, argv)), cwd=SOURCE, env=self.env, stdout=stdout, stderr=stderr, start_new_session=True)
        item = {'name': name, 'pid': child.pid, 'argv': list(map(str, argv)), 'child': child}
        self.children.append(item)
        save(self.output / (name + '.owner.json'), {key: value for key, value in item.items() if key != 'child'})
        return child

    def rows(self, table):
        require(table in ['launch_records', 'orchestration_events', 'relay_requests', 'relay_results', 'inbox_records', 'inbox_deliveries'], 'read_table', table)
        with closing(sqlite3.connect((self.state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM ' + table)]

    def events(self):
        return [{**row, 'data': json.loads(row['data'])} for row in self.rows('orchestration_events')]

    def setup(self):
        (self.root / 'repo/value.txt').write_text('09B rehearsal baseline\n', encoding='utf-8')
        (self.root / 'repo/oracle/contract.json').write_text('{"no_model":true}\n', encoding='utf-8')
        for argv in [['git', '-C', self.root / 'repo', 'init', '-b', 'main'],
                     ['git', '-C', self.root / 'repo', 'add', 'value.txt', 'oracle/contract.json'],
                     ['git', '-C', self.root / 'repo', 'commit', '-m', 'T078 scratch only']]:
            self.command(argv)
        receiver = self.root / 'target/bin/codex-receiver'
        self.command(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11', TESTS / 't078_native_receiver.c', '-o', receiver])
        (self.root / 'target/role.md').write_text('Deterministic rehearsal target. No model.\n', encoding='utf-8')
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
        snapshot = self.root / 'snapshot.tar.gz'
        with tarfile.open(snapshot, 'x:gz') as archive:
            for path in ([SOURCE / 'workbench/src' / name for name in ['daemon.ts', 'panes.ts', 'relay.ts', 'claudeLaunch.ts', 'gates/core.ts']]
                + [TESTS / name for name in ['t078_09b_protocol_core.py', 't078_09b_phase_registry.py', 't078_09b_fake_api.py',
                                            't078_09b_phase_driver.py', 't078_09b_rehearsal_host.ts', 't078_09b_rehearsal_peer.py']]):
                archive.add(path, arcname=str(path.relative_to(SOURCE)))
        config = {'codex_bin': str(receiver), 'codex_home': str(self.root / 'target/home'), 'role_card': str(self.root / 'target/role.md'),
                  'role_card_revision': 'T078-A14-rehearsal', 'code_revision': revision, 'source_snapshot': str(snapshot),
                  'hook_authorization': 'Main #304 scratch rehearsal; no model', 'turn_limit': 10}
        save(self.root / 'launch-config.json', config)
        apis = []
        for role in ['ideation', 'executor']:
            api_root = self.root / 'roles' / role; api_root.mkdir(parents=True)
            argv = [sys.executable, '-B', TESTS / 't078_09b_fake_api.py', '--root', api_root, '--role', role, '--port', '0', '--protocol']
            process = self.spawn(role + '-api', argv)
            path = api_root / 'api-ready.json'
            wait_for('api-ready-' + role, lambda: path.is_file() and path.stat().st_size > 0)
            ready = json.loads(path.read_bytes())
            require(ready['pid'] == process.pid and ready['fixture_profile'] == 'a14-approved-gate-history-v1', 'api_identity', ready)
            apis.append({'role': role, 'pid': process.pid, 'argv': list(map(str, argv)), 'ready': ready})
        self.host = self.spawn('daemon', [NODE, TESTS / 't078_09b_rehearsal_host.ts', self.root, self.root / 'launch-config.json', STRUCTURE])
        wait_for('daemon-ready', lambda: (self.root / 'host-ready.json').is_file())
        task = 't078-a14-rehearsal-' + self.root.name.rsplit('-', 1)[-1]
        card = {'id': task, 'source': None, 'goal': 'No-model A14 rehearsal', 'non_goals': ['vendor model', 'candidate submission'],
                'paths': {'allow': ['value.txt'], 'deny': []}, 'oracle_paths': ['oracle/contract.json'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c', "raise SystemExit('no candidate')"]}],
                'red_commands': [], 'task_type': '后端逻辑', 'repair_target': None, 'complexity': 'L',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}, 'base_commit': None, 'writer': None}
        save(self.root / 'card.json', card)
        self.gate('card_save', '--task', task, '--card', self.root / 'card.json', '--expected-version', '0')
        self.gate('create', '--task', task, '--repo', self.root / 'repo', '--branch', 'refs/heads/main', '--card-version', '1', '--project', 't078-a14-rehearsal')
        attempt = self.gate('dispatch', '--task', task, '--runtime-mode', 'workspace-write')['attempt']
        require(all(attempt.get(field) for field in ['task_id', 'attempt_id', 'session_id', 'fence', 'thread_id', 'workspace']), 'actual_claim', attempt)
        wait_for('target-received', lambda: (self.root / 'target/home/received.bin').is_file())
        target = wait_for('target-native-leader', lambda: self.target_info(attempt['thread_id']))
        self.request_dir = Path(next(json.loads(row['data'])['request_dir'] for row in self.rows('launch_records')
                                    if json.loads(row['data']).get('role') == 'worker'))
        self.ready = {'status': 'READY_FOR_APPROVAL', 'root': str(self.root), 'task': task, 'source_revision': revision,
                      'target_binding': attempt, 'target_process': target, 'api_processes': apis, 'daemon': {'pid': self.host.pid, 'root': str(self.state)}}
        self.stage_a = self.output / 'stage-a'; self.stage_a.mkdir(); save(self.stage_a / 'readiness.json', self.ready)
        self.packet = self.output / 'packet'; self.packet.mkdir()
        save(self.packet / 'static-check.json', {'status': 'PASS', 'revision': revision, 'protocol': True})
        shutil.copyfile(snapshot, self.packet / 'sources.tar.gz')

    def target_info(self, thread):
        info = self.gate('pane_process_info', '--thread', thread)
        return info if info.get('leader') and not info.get('failed') else None

    def role(self, role, i1_result=None):
        p1 = self.output / (role + '-p1')
        argv = [sys.executable, '-B', BASE / 'prepare-a14.py', '--mode', 'role', '--role', role,
                '--stage-a', self.stage_a, '--packet', self.packet, '--output', p1]
        if i1_result:
            argv += ['--result', i1_result]
        self.command(argv)
        inp = json.loads((p1 / 'input.json').read_bytes())
        api = next(item for item in self.ready['api_processes'] if item['role'] == role)
        bound = {**inp, 'api_url': api['ready']['api_url']}; save(p1 / 'runtime-input.json', bound)
        self.gate('controller_start', '--task', inp['task'], '--manifest', p1 / 'runtime-input.json')
        peer_ready = self.root / 'peer' / role / 'ready.json'
        wait_for('peer-ready-' + role, lambda: peer_ready.is_file())
        status = self.gate('pane_status', '--thread', inp['thread'])
        require(status['state'] == 'unknown', 'initial_unknown_' + role, status)
        received = self.root / 'peer' / role / 'received.bin'
        require(not received.exists() or received.stat().st_size == 0, 'unknown_zero_business_bytes_' + role)
        save(p1 / 'readiness.json', {'launch': inp['launch'], 'session': inp['session'], 'confirmed_by': 'executor',
             'readiness': 'confirmed', 'basis': 'Main #304 preapproved deterministic empty prompt; no Claude onboarding claim'})
        return p1, inp, json.loads(peer_ready.read_bytes())

    def approve(self, p1, stage):
        path = p1 / 'phases' / stage / 'approval.json'; value = json.loads(path.read_bytes())
        value.update(approved_by='executor', approval_ref='主控 #304 no-model scratch rehearsal ' + stage)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return path

    def phase(self, p1, stage, action, label):
        folder = p1 / 'phases' / stage
        self.command([sys.executable, '-B', TESTS / 't078_09b_i1_driver.py', '--mode', 'execute', '--protocol', '--stage', stage,
                      '--materials', p1, '--stage-a', self.stage_a, '--approval', folder / 'approval.json', '--protocol-phase', action,
                      '--output', folder / label], timeout=65)
        return folder / label / 'result.json'

    def inject_unarmed(self, p1, inp):
        plan = json.loads((self.root / 'protocol-plan.json').read_bytes())
        save(self.root / 'roles/ideation/stop-body.txt', {'source': 'test-simulated-user',
             'action_id': plan['synthetic_input_id'], 'approval_ref': '主控 #304 scratch rehearsal'})
        dispatch = self.gate('pane_dispatch', '--thread', inp['thread'], '--body-file', p1 / 'i1-prompt.txt')
        save(self.output / 'injected-dispatch.json', dispatch)
        self.gate('pane_release', '--thread', inp['thread'], '--reason', 'Main #304 deterministic empty prompt reviewed')
        waiting = self.root / 'roles/ideation/waiting-phase.json'
        wait_for('real_HTTP_awaits_approval', lambda: waiting.is_file())
        require(not (self.root / 'roles/ideation/stage-approvals/I1.json').exists(), 'approval_initially_absent')
        require(not (self.root / 'roles/ideation/responses.ndjson').exists(), 'no_SSE_before_approval')
        require(not any(event['type'] == 'permission_wait' for event in self.events()), 'no_tool_before_approval')
        return time.monotonic()

    def review_permission(self, inp, stage):
        number = 0
        def observe():
            nonlocal number
            events = [event for event in self.events() if event['launch'] == inp['launch'] and event['type'] == 'permission_wait']
            if not events:
                return None
            command = events[-1]['data']['tool_input']['command']
            value = self.gate('pane_output', '--launch', inp['launch'], '--offset', '0')
            raw = base64.b64decode(value['data_base64']); number += 1
            path = self.output / f'{stage}-review-screen-{number:02d}.bin'; path.write_bytes(raw)
            if command in raw.decode('utf-8') and '❯ 1. Yes' in raw.decode('utf-8'):
                return str(path)
            # Another read is an observation, never another POST/key/dispatch.
            return None
        return wait_for(stage + '_actual_permission_display', observe, seconds=15)

    def flow(self):
        self.setup(); p1, inp, peer = self.role('ideation')
        self.approve(p1, 'I1')
        waiting_at = self.inject_unarmed(p1, inp)
        time.sleep(.2)
        self.phase(p1, 'I1', 'arm', 'armed-01')
        approval_at = time.monotonic()
        self.review_permission(inp, 'I1')
        dispatch_path = self.phase(p1, 'I1', 'observe', 'dispatch-01')
        save(self.output / 'approval-arrival.json', {'status': 'PASS', 'missing_approval_produced_no_SSE_or_tool': True,
             'observed_hold_seconds': approval_at - waiting_at, 'after_actual_approval': 'READY_FOR_PERMISSION'})
        permission = p1 / 'phases/I1/permission-approval.json'
        self.command([sys.executable, '-B', BASE / 'prepare-a14.py', '--mode', 'permission', '--p1', p1, '--result', dispatch_path, '--output', permission])
        permitted = json.loads(permission.read_bytes()); permitted.update(approved_by='executor', approval_ref='主控 #304 scratch I1 once-only Electron Yes')
        permission.write_text(json.dumps(permitted, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest = p1 / 'actual-peer-manifest.json'; save(manifest, {'launch': inp['launch'], 'session': inp['session'],
             'cli': {'pid': peer['pid']}, 'scope': 'actual deterministic peer, not Claude'})
        i1_result = p1 / 'phases/I1/execute-02/result.json'
        self.command([sys.executable, '-B', TESTS / 't078_09b_i1_permission.py', '--materials', p1, '--p1', p1,
             '--stage', 'I1', '--stage-a', self.stage_a, '--dispatch-result', dispatch_path, '--process-manifest', manifest,
             '--approval', permission, '--output', i1_result.parent], timeout=180)
        result = json.loads(i1_result.read_bytes())
        require(result['status'] == 'READY_FOR_EXECUTOR' and result['pending'] and result['feedback_count'] == 0,
                'I1_pending_no_feedback', result)
        stop = result['stop_entry']; request_id = result['request_id']
        executor, einp, _ = self.role('executor', i1_result)
        before = self.gate('pane_status', '--thread', einp['thread'])
        require(len(before['queued']) == 1, 'executor_one_queued_stop', before)
        require(not any(event['type'] == 'relay_feedback_registered' for event in self.events()), 'no_I2_before_release')
        self.approve(p1, 'I2'); self.phase(p1, 'I2', 'arm', 'armed-01')
        self.approve(executor, 'E1'); e1_path = self.phase(executor, 'E1', 'release', 'dispatch-01')
        e1 = json.loads(e1_path.read_bytes())
        require(e1['status'] == 'READY_FOR_PERMISSION', 'E1_permission_stop', e1)
        e1_screen = self.review_permission(einp, 'E1')
        # No E1 permission action is ever sent by this scene.
        i2_path = self.phase(p1, 'I2', 'collect', 'collect-01'); i2 = json.loads(i2_path.read_bytes())
        require(i2['original_request_id'] == request_id and i2['stop_entry']['id'] == stop['id'], 'I2_original_request_entry', i2)
        feedback = [event for event in self.events() if event['type'] == 'relay_feedback_registered' and event['data'].get('request_id') == request_id]
        require(len(feedback) == 1, 'I2_exactly_once', feedback)
        delivered = json.loads(self.rows('inbox_deliveries')[-1]['data'])
        require(delivered['state'] == 'delivered' and delivered['entry_id'] == stop['id'], 'actual_delivery', delivered)
        inbox = [json.loads(row['data']) for row in self.rows('inbox_records')]
        require(len(inbox) == 1 and inbox[0]['created_at'] == stop['created_at'], 'single_stop_original_created_at', inbox)
        counts = self.counts()
        require(counts == {'ideation': 3, 'executor': 1}, 'actual_POST_counts', counts, {'ideation': 3, 'executor': 1})
        phase_counts = {}
        for role in ['ideation', 'executor']:
            for line in (self.root / 'roles' / role / 'requests.ndjson').read_text(encoding='utf-8').splitlines():
                call = json.loads(line)
                require(not call.get('error'), 'positive_HTTP_no_409', call.get('error'))
                stage = call['phase']; phase_counts[stage] = phase_counts.get(stage, 0) + 1
        require(phase_counts == {'I1': 2, 'I2': 1, 'E1': 1}, 'actual_POST_counts_per_stage', phase_counts)
        roots = {role: len([event for event in self.events() if event['type'] == 'turn_submit_intent'
                          and event['launch'] == data['launch']]) for role, data in [('ideation', inp), ('executor', einp)]}
        require(roots == {'ideation': 2, 'executor': 1}, 'actual_root_counts', roots)
        require(not list((self.root / 'peer/executor').glob('permission-key-*')), 'E1_zero_keypresses')
        require(not (self.root / 'peer/executor/tool-execution.json').exists(), 'E1_no_Bash_execution')
        save(self.output / 'flow-readback.json', {'status': 'PASS', 'stop': stop, 'request_id': request_id, 'I2': i2,
             'delivery': delivered, 'feedback': feedback, 'E1': e1, 'E1_reviewed_screen': e1_screen,
             'POST_counts': counts, 'per_stage_POSTs': phase_counts, 'roots': roots,
             'budget': {'I1': 2, 'I2': 1, 'E1_until_permission': 1, 'executor_full_limit': 11, 'ideation_full_limit': 6},
             'stopped_at': 'E1 native PermissionRequest; no Enter, no E1 tool_result/Stop'})
        return {'status': 'PASS', 'POST_counts': counts, 'I1': 'pending/zero feedback', 'I2': 'delivered/original IDs/exactly once', 'E1': 'READY_FOR_PERMISSION'}

    def counts(self):
        return {role: len(list((self.root / 'roles' / role / 'http-exchanges').glob('*.request.bin')))
                for role in ['ideation', 'executor']}

    def timeout(self):
        self.setup(); p1, inp, _ = self.role('ideation')
        # Deliberately do not sign/arm I1. Use the actual gate injection path;
        # the actual phase-plan HTTP handler must wait a real 180 seconds.
        start = time.monotonic(); self.inject_unarmed(p1, inp)
        time.sleep(.2)
        require(not (self.root / 'roles/ideation/responses.ndjson').exists(), 'no_SSE_before_approval')
        stopped_path = self.root / 'peer/ideation/stopped.json'
        wait_for('real_180_second_deadline', lambda: stopped_path.is_file(), seconds=205)
        stopped = json.loads(stopped_path.read_bytes()); http = json.loads((self.root / 'peer/ideation/http-01.json').read_bytes())
        require(stopped['status'] == 'INCOMPLETE' and stopped['http'] == 409 and stopped['error'] == 'phase_approval_deadline', 'timeout_refusal', stopped)
        require(http['elapsed_seconds'] >= 180, 'real_clock_180_seconds', http['elapsed_seconds'], '>=180')
        require(self.counts() == {'ideation': 1, 'executor': 0}, 'timeout_no_retry', self.counts())
        require(not self.rows('inbox_records') and not self.rows('relay_requests'), 'timeout_no_business_entries')
        require(not any(event['type'] in ['permission_wait', 'turn_end_signal'] for event in self.events()), 'timeout_no_permission_or_Stop')
        save(self.output / 'timeout-readback.json', {'status': 'INCOMPLETE', 'expected_counterexample': True,
             'verdict': 'PASS', 'http': http, 'elapsed_seconds': time.monotonic() - start, 'no_retry': True,
             'POST_counts': self.counts(), 'inbox_count': 0, 'relay_count': 0})
        return {'status': 'PASS', 'observed_scene_status': 'INCOMPLETE', 'http': http, 'no_retry': True}

    def cleanup(self):
        details = {'status': 'INCOMPLETE', 'root': str(self.root), 'exited': [], 'scratch_removed': False}
        if self.request_dir is None and (self.state / 'state.sqlite3').exists():
            workers = [json.loads(row['data']) for row in self.rows('launch_records') if json.loads(row['data']).get('role') == 'worker']
            if workers:
                self.request_dir = Path(workers[0]['request_dir'])
        if getattr(self, 'host', None) and self.host.poll() is None:
            self.gate('daemon_stop')
            self.host.wait(timeout=15)
        for item in self.children:
            if item['name'].endswith('-api') and item['child'].poll() is None:
                # These are unreaped Popen children created by this harness.
                # An exited child cannot have its PID reused before wait().
                item['child'].terminate()
                item['child'].wait(timeout=2)
            require(item['child'].poll() is not None, 'owned_child_exited', item['name'])
            details['exited'].append({'name': item['name'], 'pid': item['pid'], 'exit_code': item['child'].returncode})
        identities = self.root / 'peer-identities.json'
        if identities.is_file():
            for item in json.loads(identities.read_bytes()):
                wait_for('peer_exit_' + item['role'], lambda pid=item['pid']: not process_exists(pid), seconds=5)
        if self.ready:
            for pid in [self.ready['target_process']['shell_pid'], self.ready['target_process']['leader']]:
                wait_for('target_exit', lambda pid=pid: not process_exists(pid), seconds=5)
        for path in self.output.rglob('*-driver.jsonl'):
            for line in path.read_text(encoding='utf-8').splitlines():
                value = json.loads(line)
                if value.get('pid') and value.get('argv'):
                    wait_for('owned_Electron_exit', lambda pid=value['pid']: not process_exists(pid), seconds=5)
        database = self.state / 'state.sqlite3'
        if database.exists():
            snapshot = self.output / 'sqlite'; snapshot.mkdir()
            with closing(sqlite3.connect(database)) as src:
                checkpoint = src.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
                require(checkpoint[0] == 0, 'sqlite_checkpoint', checkpoint, 'not busy')
                with closing(sqlite3.connect(snapshot / 'state.sqlite3')) as dst:
                    src.backup(dst)
                sidecars = []
                for suffix in ['-wal', '-shm']:
                    path = Path(str(database) + suffix)
                    if path.exists():
                        shutil.copyfile(path, snapshot / path.name); sidecars.append(path.name)
            with closing(sqlite3.connect((snapshot / 'state.sqlite3').as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
                integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
            require(integrity == 'ok', 'sqlite_backup_readback', integrity, 'ok')
            details['sqlite'] = {'checkpoint': checkpoint, 'backup': str(snapshot / 'state.sqlite3'), 'sidecars_copied_if_present': sidecars, 'integrity': integrity}
        for directory in ['peer', 'roles']:
            if (self.root / directory).exists():
                shutil.copytree(self.root / directory, self.output / ('scratch-' + directory),
                                ignore=shutil.ignore_patterns('home', 'claude', 'tmp', 'shell', 'user-data'))
        if self.request_dir and self.request_dir.exists():
            require(self.request_dir.resolve().parent == Path('/private/tmp') and self.request_dir.name.startswith('a2a-requests-'),
                    'owned_worker_request_directory', str(self.request_dir))
            shutil.rmtree(self.request_dir)
        shutil.rmtree(self.root)
        details.update(status='PASS', scratch_removed=True)
        save(self.output / 'cleanup.json', details)
        return details


def process_exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    try:
        check = preflight()
    except Exception as error:
        value = {'status': 'INCOMPLETE', 'step': 'preflight', 'error': repr(error), 'traceback': traceback.format_exc(), 'no_runtime_started': True}
        save(out / 'preflight.json', value); print(json.dumps(value, ensure_ascii=False)); return 1
    save(out / 'preflight.json', check)
    if args.check_only:
        print(json.dumps(check, ensure_ascii=False)); return 0
    require(Path('/Volumes/WD-Elements').is_mount(), 'external_build_volume')
    overall = {'status': 'INCOMPLETE', 'scenes': [], 'real_model_turns': 0, 'scope': __doc__,
               'source_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
               'source_state': 'uncommitted candidate copied below; independent review of product unchanged'}
    sources = out / 'source'; sources.mkdir()
    source_files = [TESTS / name for name in ['t078_09b_rehearsal_host.ts', 't078_09b_rehearsal_peer.py', 'test_t078_a14_rehearsal.py',
                    't078_09b_fake_api.py', 't078_09b_protocol_core.py', 't078_09b_phase_registry.py', 't078_09b_phase_driver.py',
                    't078_09b_i1_driver.py', 't078_09b_i1_permission.py', 'electron_driver.mjs']]
    source_files += [BASE / 'prepare-a14.py']
    source_files += [SOURCE / 'workbench/src' / name for name in ['daemon.ts', 'panes.ts', 'relay.ts', 'hookTrace.ts', 'gates/core.ts']]
    for path in source_files:
        target = sources / path.relative_to(SOURCE); target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    started = time.monotonic()
    def hard_timeout(signum, frame):
        raise TimeoutError('rehearsal_hard_timeout_500_seconds')
    previous = {number: signal.signal(number, hard_timeout) for number in [signal.SIGALRM, signal.SIGTERM, signal.SIGINT]}
    signal.alarm(500)
    try:
        for kind in ['flow', 'timeout']:
            print(json.dumps({'scene': kind, 'status': 'STARTING', 'runtime_model': 0}), flush=True)
            scene = Scene(out / kind, kind)
            row = {'kind': kind, 'status': 'INCOMPLETE'}; overall['scenes'].append(row)
            try:
                row.update(getattr(scene, kind)())
            except Exception as error:
                row.update(error=repr(error), traceback=traceback.format_exc())
                raise
            finally:
                try:
                    row['cleanup'] = scene.cleanup()
                except Exception as error:
                    row['cleanup'] = {'status': 'BLOCKED', 'error': repr(error), 'traceback': traceback.format_exc(),
                                      'root': str(scene.root), 'scratch_removed': False}
                    if 'error' not in row:
                        raise
            print(json.dumps({'scene': kind, 'status': row['status'], 'cleanup': row['cleanup']['status']}), flush=True)
        for path in source_files:
            require(path.read_bytes() == (sources / path.relative_to(SOURCE)).read_bytes(), 'candidate_source_unchanged', str(path))
        overall['status'] = 'PASS'
    except Exception as error:
        overall.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        for number, handler in previous.items():
            signal.signal(number, handler)
        overall['elapsed_seconds'] = time.monotonic() - started
        save(out / 'result.json', overall)
    print(json.dumps({'status': overall['status'], 'output': str(out), 'error': overall.get('error')}, ensure_ascii=False))
    return 0 if overall['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
