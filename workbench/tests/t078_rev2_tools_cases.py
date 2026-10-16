"""Independent contract cases with real files and explicitly simulated windows."""
import base64
import copy
from contextlib import closing
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shutil
import sqlite3
import tarfile
import tempfile
from unittest.mock import patch

import t078_raw_retention as raw
import t078_09c_driver as c


def check(ok, label):
    if not ok: raise AssertionError(label)


def fixture(parent):
    root = Path(tempfile.mkdtemp(prefix='t078-rev2-files-', dir='/private/tmp')).resolve()
    (root / 'state').mkdir(); (root / 'target').mkdir(); (root / 'target/received.bin').write_bytes(b'\x1b')
    (root / 'target/baseline.bin').write_bytes(b'')
    (root / 'retention-secrets.json').write_text('["fixture-secret-value"]\n', encoding='utf-8')
    for role in raw.ROLES:
        api = root / 'roles' / role; api.mkdir(parents=True)
        sink = io.BytesIO()
        for sequence in (1, 2):
            body = json.dumps({'messages': [{'role': 'user', 'content': 'preserve 中文 tool_result'}],
                               'api_key': 'fixture-secret-value'}, ensure_ascii=False).encode('utf-8')
            record = raw.HttpExchange(api, sequence, 'POST', '/v1/messages?beta=true', 'application/json', body, role)
            payload = b'data: {"type":"message_stop"}\n\n' if sequence == 1 else b'{"error":"rejected_request"}'
            record.write(sink, payload); record.finish(200 if sequence == 1 else 409, 'application/json', True)
        for number, event in enumerate(('UserPromptSubmit', 'Stop', 'PermissionRequest')):
            trace = api / 'hooks' / f'trace-{number}'; trace.mkdir(parents=True)
            raw.save(trace / 'started.json', {'launch': role + '-launch', 'pid': 100 + number})
            raw.save(trace / 'stdin.bin', {'hook_event_name': event, 'prompt_id': 'prompt-' + role, 'session_id': 'session-' + role})
            (trace / 'stdout.bin').write_bytes(b'{}'); (trace / 'stderr.bin').write_bytes(b'')
            raw.save(trace / 'finished.json', {'exit_code': 0, 'duration_ms': 3})
    with closing(sqlite3.connect(root / 'state/state.sqlite3')) as db, db:
        db.execute('CREATE TABLE dispatch_records(seq INTEGER, data TEXT)')
        db.execute('CREATE TABLE orchestration_events(seq INTEGER, data TEXT)')
        db.execute('INSERT INTO orchestration_events VALUES(1, ?)', (json.dumps({'type': 'pending', 'text': 'preserve event'}),))
    processes = {name: {'pid': index + 1000, 'started': 'fixture-lstart', 'command': name + ' ' + str(root)}
                 for index, name in enumerate(('daemon', 'ideation_api', 'executor_api'))}
    target = {name: 'fixture-' + name for name in ('task_id', 'attempt_id', 'session_id', 'spec_rev', 'thread_id', 'workspace', 'launch')}
    target['fence'] = 1
    owner = {'scene': 'REHEARSAL', 'root': str(root), 'source_revision': 'unbound-tools-fixture', 'target_binding': target,
             'processes': processes, 'target_bytes': 'target/received.bin', 'target_baseline': 'target/baseline.bin'}
    stage = parent / 'redacted'; raw.capture(owner, stage)
    archive = parent / 'external' / 'scene.tar.gz'; receipt = raw.archive_capture(owner, stage, archive)
    approval = {**owner, 'approved_by': 'executor', 'approval_ref': 'deterministic rehearsal only', 'archive': str(archive)}
    independent = {'approved_by': 'executor', 'approval_ref': 'independent tar recount fixture',
                   'archive': str(archive), 'counts': raw.readback(archive)}
    return root, owner, stage, receipt, approval, independent


class Lifecycle:
    def __init__(self, owner, tail=False):
        self.owner = owner; self.current = copy.deepcopy(owner['processes']); self.calls = []; self.tail = tail
    def identities(self): return copy.deepcopy(self.current)
    def normal_stop(self):
        self.calls.append('daemon_stop')
        self.current['daemon'] = None
        # If cleanup reads SQLite after this point it will fail the green.
        shutil.rmtree(Path(self.owner['root']) / 'state')
        if self.tail:
            raw.save(Path(self.owner['root']) / 'roles/ideation/hooks/late-finished.json', {'exit_code': 0})
    def terminate(self, label): self.calls.append('SIGTERM:' + label); self.current[label] = None
    def wait_absent(self, labels, seconds): check(all(self.current[name] is None for name in labels), 'exit confirmation')


def corrupt(archive):
    with tarfile.open(archive, 'r:gz') as tar:
        members = [(member, tar.extractfile(member).read() if member.isfile() else None) for member in tar.getmembers()]
    with tarfile.open(archive, 'w:gz') as tar:
        for member, data in members:
            if member.name.endswith('0001.response.bin'):
                data = b'MUTATED'; member.size = len(data)
            tar.addfile(member, io.BytesIO(data) if data is not None else None)


def retention_cases(output, checks):
    for label in ('green', 'dry-run', 'bad-archive', 'missing-readback', 'wrong-PID', 'raw-before-stop', 'tail-after-stop', 'mutant-skip-bytes'):
        folder = output / ('retention-' + label); folder.mkdir()
        root, owner, stage, receipt, approval, independent = fixture(folder)
        runtime = Lifecycle(owner, tail=label == 'tail-after-stop')
        try:
            counts = raw.readback(receipt['archive'])
            check(counts['Messages_POST'] == {'ideation': 2, 'executor': 2}, 'rejected POST retained in raw recount')
            for role in raw.ROLES:
                check(counts['hooks'][role] == {'UserPromptSubmit': 1, 'Stop': 1, 'PermissionRequest': 1}, 'all hook kinds retained')
            check(b'fixture-secret-value' not in b''.join(path.read_bytes() for path in stage.rglob('*') if path.is_file()), 'secret removed')
            check('preserve 中文 tool_result' in (stage / 'files/roles/ideation/http-exchanges/0001.request.bin').read_text(encoding='utf-8'), 'business body preserved')
            if label in ('bad-archive', 'mutant-skip-bytes'): corrupt(receipt['archive'])
            if label == 'missing-readback': independent['approved_by'] = None
            if label == 'wrong-PID': runtime.current['ideation_api']['started'] = 'reused-PID'
            if label == 'raw-before-stop': (root / 'roles/ideation/http-exchanges/0003.request.bin').write_bytes(b'late')
            mutant = label == 'mutant-skip-bytes'
            with patch.object(raw, 'verify_archive', return_value=receipt['inventory']) if mutant else nullcontext():
                result = raw.finish(owner, approval, receipt, independent, folder / 'cleanup', runtime, dry_run=label == 'dry-run')
            if label in ('green', 'mutant-skip-bytes'):
                if mutant:
                    # This is the new oracle's expected RED for the bad tool.
                    try: check(runtime.calls == [] and root.exists(), 'corrupt archive must prevent stop and delete')
                    except AssertionError as error:
                        checks.append({'name': label, 'status': 'PASS', 'known_bad_observed': 'RED', 'assertion': str(error), 'calls': runtime.calls})
                    else: raise AssertionError('byte-check mutation survived')
                else:
                    check(result['status'] == 'PASS' and not root.exists(), 'archive before stop; file-only verification then root removed')
                    check(runtime.calls == ['daemon_stop', 'SIGTERM:ideation_api', 'SIGTERM:executor_api'], 'one normal stop and one SIGTERM per API')
            elif label == 'tail-after-stop':
                check(result['status'] == 'BLOCKED' and root.exists() and 'raw_member_set_changed' in result['error'], 'shutdown tail blocks deletion')
            elif label == 'dry-run':
                check(result['status'] == 'PASS' and not runtime.calls and root.exists(), 'dry-run zero side effects')
            else:
                check(result['status'] == 'BLOCKED' and not runtime.calls and root.exists(), label + ' blocks stop and delete')
            if not mutant: checks.append({'name': 'retention-' + label, 'status': 'PASS', 'actual': result['status'], 'calls': runtime.calls})
        finally:
            if root.exists(): shutil.rmtree(root)


class nullcontext:
    def __enter__(self): return self
    def __exit__(self, *args): return False


class FixtureClock:
    def __init__(self): self.elapsed = 0
    def wall(self): return 1800000000000 + self.elapsed
    def mono(self): return 7000000 + self.elapsed
    def sleep(self, seconds): self.elapsed += seconds * 1000


def permission_fixture(folder, clock=None):
    folder.mkdir(parents=True)
    clock = clock or FixtureClock()
    stop = {'id': 'actual-fixture-stop', 'request_id': 'queued-fixture-request',
            'created_at': datetime.fromtimestamp(clock.wall() / 1000, timezone.utc).isoformat()}
    start = c.origin(stop, clock)
    target = {key: 'fixture-' + key for key in c.TARGET_KEYS}; target['fence'] = 1
    binding = {key: 'fixture-' + key for key in c.BINDING_KEYS}
    argv = ['/usr/bin/node', '/fixture/cli.ts', 'stop', '--thread', target['thread_id'], '--stop-id', stop['id']]
    binding.update(global_seq=17, permission_seq=338, input_generation=0, target=target, stop=stop, argv=argv, command=c.shlex.join(argv))
    screen = ('old terminal output\n' * 5000).encode() + ('\nBash\n' + binding['command'] + '\n❯ 1. Yes\n  2. No\n').encode()
    actual = {'binding': binding, 'active': True, 'ack': False, 'demand_valid': True, 'selected_line': '❯ 1. Yes',
              'visible_command': binding['command']}
    runtime = Window(actual, screen, clock)
    observed = c.read_complete_output(runtime.fetch_page, binding['launch'])
    (folder / 'approved-screen.bin').write_bytes(screen)
    template = {'stage': 'C-I3', 'approved_by': 'executor', 'approval_ref': 'deterministic fixture authorization only',
                'source': 'test-simulated-user', 'key': 'Enter', 'selected_label': 'Yes', 'selected_line': '❯ 1. Yes', 'max_writes': 1,
                'binding': copy.deepcopy(binding), 'screen_file': str(folder / 'approved-screen.bin'),
                'screen_capture': observed['capture'], 'intent_file': str(folder / 'durable-intent.json')}
    return template, runtime, start, clock


class Window:
    def __init__(self, actual, screen, clock):
        self.value = copy.deepcopy(actual); self.screen = screen; self.clock = clock; self.keys = []; self.mode = 'complete'
    def actual(self): return copy.deepcopy(self.value)
    def fetch_page(self, offset):
        total = len(self.screen); raw_bytes = self.screen[offset:offset + 32768]
        if self.mode == 'zero-progress': raw_bytes = b''
        if self.mode == 'total-changed' and offset: total += 1
        if self.mode == 'one-page' and offset: raw_bytes = b''
        return {'launch': self.value['binding']['launch'], 'start_offset': offset,
                'next_offset': offset + len(raw_bytes), 'total_bytes': total, 'data_base64': base64.b64encode(raw_bytes).decode()}
    def enter(self, template):
        self.keys.append(b'\r')
        return {'form': 'action', 'data': '\r', 'intent_count': 1, 'written_count': 1, 'new_turn_intents': 0,
                'scope': 'deterministic window transport spy; no Electron/Claude'}


def permission_cases(output, checks):
    labels = ['green', 'changed-screen', 'one-page', 'total-changed', 'zero-progress', 'missing-EOF',
              'unsigned', 'ack', 'demand-revoked', 'late', 'after-scene-deadline', 'clock-jump', 'uncertain-write', 'mutant-template-guard', 'visible-command', 'mutant-clock-guard']
    labels += ['binding-' + key for key in c.BINDING_KEYS]
    for label in labels:
        template, runtime, start, clock = permission_fixture(output / ('permission-' + label))
        if label == 'changed-screen': runtime.screen += b'changed'
        if label in ('one-page', 'total-changed', 'zero-progress'): runtime.mode = label
        if label == 'missing-EOF': template['screen_capture']['pages'].pop()
        if label == 'unsigned': template['approved_by'] = None
        if label == 'visible-command': runtime.value['visible_command'] += ' --extra'
        if label == 'ack': runtime.value['ack'] = True
        if label == 'demand-revoked': runtime.value['demand_valid'] = False
        if label == 'late': clock.elapsed = 130001
        if label == 'after-scene-deadline': clock.elapsed = 150001
        if label == 'clock-jump': start['wall_ms'] -= 10000
        if label == 'uncertain-write':
            def uncertain(value): runtime.keys.append(b'\r'); raise TimeoutError('unknown write')
            runtime.enter = uncertain
        if label.startswith('binding-'):
            key = label[len('binding-'):]; runtime.value['binding'][key] = 'changed'
        if label == 'mutant-template-guard': runtime.value['binding']['window_id'] = 'wrong-window'
        mutation = nullcontext()
        if label == 'mutant-template-guard': mutation = patch.object(c, 'validate_permission', return_value=None)
        if label == 'mutant-clock-guard': mutation = patch.object(c, 'timing', return_value={'wall_age_ms': 120200, 'observed_elapsed_ms': 120200})
        with mutation:
            result = c.conditional_enter(template, runtime, start, output / ('enter-' + label), clock)
        if label == 'green':
            check(result['status'] == 'PASS' and runtime.keys == [b'\r'], 'one conditional Enter')
            check(result['enter_at']['wall_age_ms'] > 120000 and result['enter_at']['observed_elapsed_ms'] >= 120100, 'strict two clock threshold')
            again = c.conditional_enter(template, runtime, start, output / 'enter-green-repeat', clock)
            check(again['status'] == 'INCOMPLETE' and runtime.keys == [b'\r'], 'durable intent prevents repeat')
        elif label == 'mutant-template-guard':
            try: check(result['status'] == 'INCOMPLETE' and not runtime.keys, 'template mismatch must write zero keys')
            except AssertionError as error:
                checks.append({'name': label, 'status': 'PASS', 'known_bad_observed': 'RED', 'assertion': str(error), 'keys': len(runtime.keys)})
            else: raise AssertionError('template-check mutation survived')
            continue
        elif label == 'mutant-clock-guard':
            try: check(clock.elapsed >= 120100 or not runtime.keys, 'actual elapsed clock must prevent early Enter')
            except AssertionError as error:
                checks.append({'name': label, 'status': 'PASS', 'known_bad_observed': 'RED', 'assertion': str(error), 'actual_elapsed_ms': clock.elapsed})
            else: raise AssertionError('clock-check mutation survived')
            continue
        elif label == 'uncertain-write':
            check(result['status'] == 'INCOMPLETE' and runtime.keys == [b'\r'], 'unknown write is incomplete')
            again = c.conditional_enter(template, runtime, start, output / 'enter-uncertain-repeat', clock)
            check(again['status'] == 'INCOMPLETE' and runtime.keys == [b'\r'], 'unknown write cannot retry')
        else:
            check(result['status'] == 'INCOMPLETE' and not runtime.keys, label + ': no key')
        checks.append({'name': 'permission-' + label, 'status': 'PASS', 'actual': result['status'],
                       'keys': len(runtime.keys), 'error': result.get('error'), 'clock': 'injected unit clock, not real-time evidence'})


def run(output, checks):
    retention_cases(output, checks)
    permission_cases(output, checks)
    adapter_cases(output, checks)


def adapter_cases(output, checks):
    # The exact native writer receipt has no data field on the written event.
    # This entry probe checks NativePermission.enter, not a restated spy result.
    import t078_09b_i1_permission as permission
    folder = output / 'native-adapter'; folder.mkdir()
    template, window, start, clock = permission_fixture(folder / 'fixture')
    state = {'events': [], 'actions': [], 'calls': []}
    class Client:
        def call(self, command, **kwargs):
            state['calls'].append({'command': command, **kwargs})
            state['events'] = [
                {'seq': 31, 'type': 'terminal_input_write_intent', 'data': {'data': '\r', 'request_id': 'actual-command'}},
                {'seq': 32, 'type': 'terminal_input_written', 'data': {'request_id': 'actual-command', 'byte_length': 1}},
                {'seq': 33, 'type': 'turn_submit_intent', 'data': {'source': 'gate', 'dispatch': 'actual-C-I4', 'id': 'later-feedback-root'}}]
            state['actions'] = [{'form': 'action', 'source_ref': {'command_id': 'actual-command'}, 'content': {'data': '\r'}}]
            return {'written': True}
    plan = {'root': str(folder), 'roles': {'ideation': {'launch': template['binding']['launch'], 'thread': 'fixture-thread'}}}
    native = c.NativePermission(plan, 'C-I3', Client())
    with patch.object(permission, 'events', side_effect=lambda *args: copy.deepcopy(state['events'])), \
         patch.object(permission, 'rows', side_effect=lambda *args: copy.deepcopy(state['actions'])):
        receipt = native.enter(template)
    check(receipt['intent_count'] == receipt['written_count'] == 1 and receipt['form'] == 'action' and
          receipt['new_turn_intents'] == 0 and state['calls'][0]['permission'] is True, 'actual native adapter entry maps the real receipt shape')
    check(c.visible_command('Bash command\nRun shell command\n│ /node /cli stop\n│ --stop-id actual\nThis command requires approval\n❯ 1. Yes') == '/node /cli stop --stop-id actual', 'native wrapped command box parsed')
    clean, ranges = raw.redact(json.dumps({'data': json.dumps({'A2A_WINDOW_CAPABILITY': 'nested-private-capability',
                                                             'body': 'keep full original business text'})}).encode(), [])
    check(b'nested-private-capability' not in clean and b'keep full original business text' in clean and ranges,
          'embedded JSON capability redacted without dropping body')
    raw.save(folder / 'readback.json', {'status': 'PASS', 'receipt': receipt, 'calls': state['calls'],
                                      'redaction_ranges': ranges, 'scope': 'actual Python adapter, deterministic client and event reads'})
    checks.append({'name': 'native-permission-adapter-and-redaction', 'status': 'PASS', 'real_Electron': False})
    with tempfile.TemporaryDirectory(prefix='t078-C-start-', dir='/private/tmp') as tmp:
        root = Path(tmp).resolve(); prompt = root / 'prompt.txt'; prompt.write_text('真实尾换行\n', encoding='utf-8')
        plan = {'root': str(root), 'prompt_file': str(prompt), 'i1_prompt': '真实尾换行\n', 'synthetic_input_id': 'actual-input',
                'roles': {'ideation': {'thread': 'actual-I-thread', 'launch': 'actual-I-launch'},
                          'executor': {'thread': 'actual-E-thread', 'launch': 'actual-E-launch'}}}
        calls = []
        def gate(root, command, *args):
            calls.append(command)
            if command == 'pane_status': return {'ok': True, 'state': 'idle', 'active': None, 'queued': []}
            if command == 'pane_dispatch': return {'ok': True, 'dispatch': {'id': 'actual-dispatch', 'seq': 47, 'text': '⟦主控 #47⟧\n真实尾换行'}}
            if command == 'pane_release': raise RuntimeError('initial_release_only')
            raise AssertionError(command)
        first = c.start_first_turn(plan, {'approval_ref': 'fixture window request'}, gate)
        check(first['dispatch']['seq'] == 47 and calls == ['pane_status', 'pane_status', 'pane_dispatch'],
              'real gate wrapper/global seq and trailing-newline canonical form')
        try: c.start_first_turn(plan, {'approval_ref': 'fixture window request'}, gate)
        except FileExistsError: pass
        else: raise AssertionError('uncertain C dispatch could be sent twice')
        check(calls.count('pane_dispatch') == 1, 'exclusive action journal prevents C dispatch retry')
        raw.save(folder / 'C-start-receipt.json', {'status': 'PASS', 'result': first, 'calls': calls})
    checks.append({'name': 'C-start-real-gate-response-shape', 'status': 'PASS', 'real_gates': False})
    late = output / 'late-C-business-failure'
    def late_failure():
        c.ENTRY_OUTPUT = late; late.mkdir()
        raw.save(late / 'result.json', {'status': 'PASS', 'scope': 'intermediate control receipt'})
        raise RuntimeError('actual_Stop_or_relay_not_proven')
    with patch.object(c, 'main', side_effect=late_failure):
        code = c.run_cli()
    check(code == 1 and raw.read_json(late / 'result.json')['status'] == 'INCOMPLETE' and
          raw.read_json(late / 'partial-result.json')['status'] == 'PASS', 'late failure must not leave a top-level PASS')
    checks.append({'name': 'C-entry-late-failure-preserves-partial-and-is-incomplete', 'status': 'PASS'})
