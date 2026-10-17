"""Real HTTP and >120s system-clock rehearsal, deterministic actors only.

The database rows and window are fixtures. This proves test-tool transport and
timing, not product relay/CLI acceptance. No Claude/Codex/model is started.
"""
import argparse
import ast
from contextlib import closing
import copy
import importlib.util
import io
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.request

import t078_09c_driver as c
import t078_raw_retention as raw
from t078_09b_rehearsal_peer import initial_messages, tool_result_message, parse_sse
from t078_rev2_tools_cases import permission_fixture, check

SOURCE = Path(__file__).resolve().parents[2]
TESTS = SOURCE / 'workbench/tests'
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
STRUCTURE = BASE / '09b-a14-rehearsal-fixture-01/request-structure.json'


def preflight():
    paths = [Path(__file__), TESTS / 't078_09b_fake_api.py', TESTS / 't078_raw_retention.py',
             TESTS / 't078_09c_driver.py', TESTS / 'p1_output.py', STRUCTURE,
             BASE / '09b-materials-01/protocol.json']
    for path in paths:
        check(path.is_file(), 'existing command/input path: ' + str(path))
        if path.suffix == '.py': ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    structure = raw.read_json(STRUCTURE)
    schema = structure['request']['tools'][0]['input_schema']
    check('command' in schema['required'] and 'argv' not in schema['properties'], 'real recorded Bash input schema')
    return {'status': 'PASS', 'paths': list(map(str, paths)), 'no_runtime_started': True,
            'request_sources': [structure['source_initial'], structure['source_tool_result']],
            'schema': schema, 'hard_timeout_seconds': 210, 'expected_real_wait_seconds': 120.1}


class Rehearsal:
    def __init__(self, output, offline=False, mutant=None):
        self.out = output; self.children = []; self.threads = []; self.results = []
        self.offline = offline; self.local_modules = {}; self.clock = None
        self.root = Path(tempfile.mkdtemp(prefix='t078-rev2-http-', dir='/private/tmp')).resolve()
        self.db = self.root / 'state/state.sqlite3'; self.db.parent.mkdir()
        (self.root / 'target').mkdir(); (self.root / 'target/received.bin').write_bytes(b'')
        (self.root / 'target/baseline.bin').write_bytes(b'')
        (self.root / 'retention-secrets.json').write_text('[]\n', encoding='utf-8')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.executescript('CREATE TABLE launch_records(id TEXT,data TEXT);'
                'CREATE TABLE orchestration_events(seq INTEGER PRIMARY KEY,type TEXT,launch TEXT,data TEXT);'
                'CREATE TABLE dispatch_records(seq INTEGER,data TEXT);'
                'CREATE TABLE inbox_records(id TEXT,data TEXT);'
                'CREATE TABLE relay_results(key TEXT,data TEXT);')
        self.plan = {'scene': '09C', 'root': str(self.root), 'source': str(SOURCE), 'node': sys.executable,
            'source_revision': 'UNBOUND_TEST_TOOL_REHEARSAL', 'i1_prompt': 'approved deterministic stop request',
            'synthetic_input_id': 'fixture-input', 'protocol_source': str(BASE / '09b-materials-01/protocol.json'),
            'target_binding': {key: 'fixture-' + key for key in ('task_id', 'attempt_id', 'session_id', 'spec_rev', 'thread_id', 'workspace', 'launch')}, 'roles': {}}
        self.plan['node'] = str(Path('/opt/homebrew/bin/node').resolve(strict=True))
        self.plan['target_binding']['fence'] = 1
        for role in raw.ROLES:
            inp = {'preset': role, 'launch': 'fixture-launch-' + role, 'session': 'fixture-session-' + role,
                   'thread': 'fixture-thread-' + role, 'task': 'fixture-task', 'code_revision': self.plan['source_revision']}
            self.plan['roles'][role] = inp
            self.insert('launch_records', ('id', 'data'), (inp['launch'], json.dumps(inp)))
            api = self.root / 'roles' / role; (api / 'hooks').mkdir(parents=True)
            raw.save(api / 'protocol-registry.json', {'phase_plan': str(self.root / 'plan.json')})
            for stage, (stage_role, _, _) in c.STAGES.items():
                if stage_role == role:
                    raw.save(api / 'stage-approvals' / (stage + '.json'),
                        {'approved_by': 'executor', 'approval_ref': 'deterministic HTTP rehearsal only',
                         'stage': stage, 'role': role, 'launch': inp['launch'], 'session': inp['session'],
                         'target_binding': self.plan['target_binding'], 'source_revision': inp['code_revision']})
        raw.save(self.root / 'plan.json', self.plan)
        self.structure = raw.read_json(STRUCTURE); self.sequence = 0
        for role in raw.ROLES:
            api = self.root / 'roles' / role
            if offline:
                spec = importlib.util.spec_from_file_location('fixture_api_' + role, TESTS / 't078_09b_fake_api.py')
                module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
                module.configure(api, role, True); self.local_modules[role] = module
                if mutant == 'bash-schema' and role == 'ideation':
                    native_sse = module.anthropic_sse
                    def bad_schema(result, model, request_id):
                        events = native_sse(result, model, request_id)
                        if result.get('tool_use'):
                            events[2]['delta']['partial_json'] = json.dumps({'argv': ['/wrong/legacy/schema']})
                        return events
                    module.anthropic_sse = bad_schema
                raw.save(api / 'api-ready.json', {'api_url': 'in-memory-handler://' + role,
                    'pid':os.getpid()+10000+raw.ROLES.index(role),'role':role,'stage':'A',
                    'protocol':'rev2-raw-c-profile-v1','model_turns':0,'scope':'in-memory unit fixture, not an actual ready process'})
                continue
            stdout = (output / (role + '.stdout.bin')).open('xb'); stderr = (output / (role + '.stderr.bin')).open('xb')
            child = subprocess.Popen([sys.executable, '-B', str(TESTS / 't078_09b_fake_api.py'), '--root', str(api),
                                      '--role', role, '--protocol'], stdout=stdout, stderr=stderr, start_new_session=True)
            self.children.append((child, stdout, stderr))
            deadline = time.monotonic() + 5
            while not (api / 'api-ready.json').is_file():
                check(child.poll() is None, 'fake API alive before readiness')
                check(time.monotonic() < deadline, 'fake API readiness deadline')
                time.sleep(.02)
        self.apis = {role: raw.read_json(self.root / 'roles' / role / 'api-ready.json')['api_url'] for role in raw.ROLES}
        raw.save(output / 'fixture-scope.json', {'root': str(self.root), 'role_CLIs': 0, 'models': 0,
            'database': 'deterministic fixture rows; not product daemon/relay', 'APIs': self.apis,
            'transport': 'real Handler with byte streams, no port' if offline else 'real loopback HTTP',
            'clock': 'injected unit clock' if offline else 'system wall and monotonic clocks'})

    def insert(self, table, columns, values):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('INSERT INTO ' + table + '(' + ','.join(columns) + ') VALUES(' + ','.join('?' for _ in values) + ')', values)

    def dispatch(self, role, seq, source, text, **extra):
        dispatch = {'id': 'fixture-dispatch-' + str(seq), 'seq': seq, 'source': source,
                    'text': f'⟦主控 #{seq}⟧\n' + text, **extra}
        launch = self.plan['roles'][role]['launch']
        self.insert('orchestration_events', ('type', 'launch', 'data'), ('dispatch_queued', launch, json.dumps(dispatch, ensure_ascii=False)))
        self.insert('orchestration_events', ('type', 'launch', 'data'), ('turn_submitted', launch, json.dumps({'dispatch': dispatch['id']})))
        return dispatch

    def feedback(self, request_id, ok, **result):
        receipt = {'key': 'fixture-key-' + request_id, 'request_id': request_id, 'replayed': False,
                   'result': {'ok': ok, **result}}
        return 'actual-format deterministic gate receipt\n' + json.dumps([receipt], ensure_ascii=False)

    def post(self, role, body):
        self.sequence += 1; number = self.sequence
        encoded = json.dumps(body, ensure_ascii=False).encode()
        if self.offline:
            handler = self.local_modules[role].Handler.__new__(self.local_modules[role].Handler)
            handler.path = '/v1/messages?beta=true'; handler.rfile = io.BytesIO(encoded); handler.wfile = io.BytesIO()
            handler.headers = {'Content-Length': str(len(encoded)), 'Content-Type': 'application/json',
                               'Authorization': 'Bearer NEVER_RETAIN_THIS_HEADER'}
            observed = {}; handler.send_response = lambda code: observed.update(status=code)
            handler.send_header = lambda *args: None; handler.end_headers = lambda: None
            handler.do_POST(); status, payload = observed['status'], handler.wfile.getvalue()
        else:
            request = urllib.request.Request(self.apis[role] + '/v1/messages?beta=true', data=encoded,
                                        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer NEVER_RETAIN_THIS_HEADER'})
            try:
                with urllib.request.urlopen(request, timeout=155) as response: status, payload = response.status, response.read()
            except urllib.error.HTTPError as error: status, payload = error.code, error.read()
        (self.out / f'wire-{number:02d}.bin').write_bytes(payload)
        self.results.append({'number': number, 'role': role, 'status': status, 'response_bytes': len(payload)})
        return status, payload

    def request(self, text):
        return {**self.structure['request'], 'messages': initial_messages(self.structure, text)}

    def tool_turn(self, stage, dispatch):
        role = c.STAGES[stage][0]; body = self.request(dispatch['text'])
        status, response = self.post(role, body); check(status == 200, stage + ' first POST 200')
        tool = parse_sse(response); check(tool['type'] == 'tool_use', stage + ' actual SSE tool_use')
        schema = self.structure['request']['tools'][0]['input_schema']
        check(set(tool['input']) == set(schema['required']) == {'command'}, 'recorded Claude Bash schema rejects argv')
        request_id = 'fixture-queued-' + stage
        queued = {'ok': True, 'queued': True, 'delivered': False, 'request_id': request_id,
                  'path': str(self.root / 'roles' / role / 'requests' / (request_id + '.json'))}
        body['messages'].append({'role': 'assistant', 'content': [tool]})
        body['messages'].append(tool_result_message(self.structure, tool, queued))
        body['messages'].extend(copy.deepcopy([msg for msg in self.structure['request']['messages'] if msg['role'] == 'system']))
        status, response = self.post(role, body)
        check(status == 200 and parse_sse(response)['type'] == 'text', stage + ' queued tool_result neutrally settled')
        return request_id, tool

    def flow(self):
        first = self.dispatch('ideation', 2, 'executor', self.plan['i1_prompt'])
        request_id, _ = self.tool_turn('C-I1', first)
        stop = {'id': 'fixture-stop', 'kind': 'stop', 'from': 'ideation', 'to': 'executor',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'refs': ['thread:fixture-thread_id', 'attempt:fixture-attempt_id', 'input:fixture-input']}
        if self.offline:
            from t078_rev2_tools_cases import FixtureClock
            class UnitClock(FixtureClock):
                def wall(self): return c.created_ms(stop['created_at']) + self.elapsed
            self.clock = UnitClock()
        self.insert('inbox_records', ('id', 'data'), (stop['id'], json.dumps(stop)))
        executor = self.dispatch('executor', 3, 'inbox', 'stop fixture-stop', inbox_entry=stop['id'])
        held = {}
        def hold():
            try: held['status'], held['body'] = self.post('executor', self.request(executor['text']))
            except Exception as error: held['error'] = repr(error)
        thread = threading.Thread(target=hold); thread.start(); self.threads.append(thread)
        waiting = self.root / 'roles/executor/http-exchanges/0001.meta.json'
        deadline = time.monotonic() + 5
        while not waiting.exists() or raw.read_json(waiting).get('wire_bytes_confirmed', 0) == 0:
            check(time.monotonic() < deadline, 'C-E1 heartbeat readiness'); time.sleep(.05)
        check(thread.is_alive() and not raw.read_json(waiting)['complete'], 'executor one held POST')
        second = self.dispatch('ideation', 4, 'gate', self.feedback(request_id, True, entry=stop, delivery={'state': 'delivered'}))
        early_request, _ = self.tool_turn('C-I2', second)
        third = self.dispatch('ideation', 5, 'gate', self.feedback(early_request, False, error='stop_too_early'))
        # Obtain C-I3's tool_use before waiting, exactly as the real plan parks
        # on PermissionRequest. Only the deterministic transport is simulated.
        third_body = self.request(third['text']); status, response = self.post('ideation', third_body)
        check(status == 200, 'C-I3 first POST'); late_tool = parse_sse(response)
        clock = self.clock or c.Clock()
        template, window, _, _ = permission_fixture(self.out / 'real-clock-window', clock)
        template['binding']['stop'] = {'id': stop['id'], 'created_at': stop['created_at'], 'request_id': request_id}
        template['binding']['command'] = late_tool['input']['command']; template['binding']['argv'] = c.shlex.split(late_tool['input']['command'])
        window.value['binding'] = copy.deepcopy(template['binding'])
        window.value['visible_command'] = late_tool['input']['command']
        window.screen = ('Bash command\nRun shell command\n│ ' + late_tool['input']['command'] + '\nThis command requires approval\n❯ 1. Yes\n').encode()
        Path(template['screen_file']).write_bytes(window.screen)
        template['screen_capture'] = c.read_complete_output(window.fetch_page, template['binding']['launch'])['capture']
        start = c.origin(template['binding']['stop'], clock)
        # This path is the same conditional_enter entry exercised by unit
        # cases. No injected sleep/time implementation is supplied here.
        result = c.conditional_enter(template, window, start, self.out / 'real-clock-enter', clock)
        check(result['status'] == 'PASS' and window.keys == [b'\r'], 'conditional one Enter after threshold')
        check(result['enter_at']['wall_age_ms'] > 120000 and result['enter_at']['observed_elapsed_ms'] >= 120100,
              'real-clock threshold independently read from retained timestamps')
        late_request = 'fixture-queued-C-I3'
        third_body['messages'] += [{'role': 'assistant', 'content': [late_tool]}, tool_result_message(self.structure, late_tool,
            {'ok': True, 'queued': True, 'delivered': False, 'request_id': late_request,
             'path': str(self.root / 'roles/ideation/requests' / (late_request + '.json'))})]
        status, response = self.post('ideation', third_body); check(status == 200 and parse_sse(response)['type'] == 'text', 'C-I3 settlement')
        raw.save(self.root / 'roles/executor/hold-release.json', {'stop_id': stop['id'], 'source_revision': self.plan['source_revision']})
        fourth = self.dispatch('ideation', 6, 'gate', self.feedback(late_request, True, interruptRequested=True))
        status, response = self.post('ideation', self.request(fourth['text'])); check(status == 200 and parse_sse(response)['type'] == 'text', 'C-I4 neutral confirmation')
        thread.join(timeout=5); check(not thread.is_alive() and held.get('status') == 200, 'executor held request finished once')
        # Heartbeat comments do not count as additional SSE model messages.
        check(parse_sse(held['body'])['type'] == 'text', 'executor complete neutral SSE')
        check(sum(item['role'] == 'ideation' for item in self.results) == 7 and
              sum(item['role'] == 'executor' for item in self.results) == 1, 'actual wire POST budget 7/1')
        counts = {}
        for role in raw.ROLES:
            calls = [json.loads(line) for line in (self.root / 'roles' / role / 'requests.ndjson').read_text(encoding='utf-8').splitlines()]
            for call in calls: counts[call['phase']] = counts.get(call['phase'], 0) + 1
        check(counts == {'C-I1': 2, 'C-E1': 1, 'C-I2': 2, 'C-I3': 2, 'C-I4': 1}, 'actual per-stage POST counts')
        # Rejected calls are still counted and retained after the positive
        # scenario. They are distinct counterexamples, not free budget calls.
        status, response = self.post('ideation', self.request('unregistered text'))
        check(status == 409 and json.loads(response)['error'] == 'registered_text_mismatch', 'unregistered text rejected')
        status, response = self.post('executor', self.request(first['text']))
        check(status == 409 and json.loads(response)['error'] == 'registered_text_mismatch', 'wrong role rejected')
        bound_file = self.root / 'roles/ideation' / ('bound-' + fourth['id'] + '.json')
        bound = raw.read_json(bound_file); bound['seq'] = 999; bound_file.write_text(json.dumps(bound), encoding='utf-8')
        status, response = self.post('ideation', self.request(fourth['text']))
        check(status == 409 and json.loads(response)['error'] == 'bound_dispatch_changed', 'global seq changed rejected')
        inp = self.plan['roles']['ideation']
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE launch_records SET data=? WHERE id=?', (json.dumps({**inp, 'session': 'wrong-session'}), inp['launch']))
        status, response = self.post('ideation', self.request(first['text']))
        check(status == 409 and json.loads(response)['error'] == 'actual_controller_launch_required', 'actual launch identity rejected')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('UPDATE launch_records SET data=? WHERE id=?', (json.dumps(inp), inp['launch']))
        excess = self.dispatch('ideation', 7, 'gate', self.feedback(late_request, True, interruptRequested=True))
        status, response = self.post('ideation', self.request(excess['text']))
        check(status == 409 and json.loads(response)['error'] == 'message_budget_exhausted', 'actual POST budget rejected')
        raw.save(self.out / 'positive-flow.json', {'status': 'PASS', 'actual_POST_counts': counts, 'clock': result['enter_at'],
                 'actor_scope': 'fixture rows and deterministic window; no product relay claim',
                 'transport': 'in-memory real Handler' if self.offline else 'real HTTP',
                 'clock_scope': 'injected unit clock' if self.offline else 'real system clocks'})
        raw.save(self.out / 'wire-counts-with-counterexamples.json', self.results)
        # Save a consistent DB backup before shutting down APIs, not WAL-less
        # copying. This DB contains only synthetic rows, no credentials.
        with closing(sqlite3.connect(self.db)) as src, closing(sqlite3.connect(self.out / 'fixture.sqlite3')) as dst: src.backup(dst)
        owner = {'scene': '09C', 'root': str(self.root), 'source_revision': self.plan['source_revision'],
                 'target_binding': self.plan['target_binding'], 'target_bytes': 'target/received.bin', 'target_baseline': 'target/baseline.bin'}
        owned_apis = {role + '_api': item[0] for role, item in zip(raw.ROLES, self.children)}
        owner['processes'] = {'daemon': {'pid': os.getpid(), 'started': 'fixture-coordinator', 'command': 'normal-stop spy; never signalled'}}
        for label, child in owned_apis.items():
            owner['processes'][label] = {'pid': child.pid, 'started': 'owned-unreaped-Popen-lifetime', 'command': c.shlex.join(child.args)}
        if self.offline:
            for index, role in enumerate(raw.ROLES):
                owner['processes'][role + '_api'] = {'pid': os.getpid() + 10000 + index, 'started': 'in-memory fixture only', 'command': role + ' handler; no process or signal'}
        from t078_owner_receipt_fixture import write_owner_receipts
        write_owner_receipts(owner,self.out/'unit-owner-receipts')
        raw.capture(owner, self.out / 'redacted')
        archived = raw.archive_capture(owner, self.out / 'redacted', self.out / 'archive' / 'scene.tar.gz')
        check(b'NEVER_RETAIN_THIS_HEADER' not in b''.join(path.read_bytes() for path in (self.out / 'redacted').rglob('*') if path.is_file()), 'authorization value absent from originals')
        readback = raw.readback(archived['archive'])
        check(readback['Messages_POST'] == {'ideation': 11, 'executor': 2} and not readback['unfinished_http'], 'all accepted/rejected HTTP originals independently recounted')
        raw.save(self.out / 'archive-readback.json', readback)
        scene = self
        class Lifecycle:
            # Only the normal daemon_stop is a fixture callback here. The two
            # real HTTP processes are unreaped Popen children, so PID reuse is
            # impossible. This does not claim the operational nine-PID probe.
            def __init__(self): self.stopped = False; self.api_alive = {role + '_api': True for role in raw.ROLES}
            def identities(self):
                return {label: (None if (self.stopped if label == 'daemon' else
                        ((not self.api_alive[label] if scene.offline else owned_apis[label].poll() is not None) if label.endswith('_api') else self.stopped)) else value)
                        for label, value in owner['processes'].items()}
            def topology(self):check(len(owner['processes'])==9,'unit fixture reaches topology transport')
            def normal_stop(self):
                self.stopped = True; shutil.rmtree(scene.root / 'state')
            def terminate(self, label):
                if scene.offline: self.api_alive[label] = False
                else: owned_apis[label].terminate()
            def wait_absent(self, labels, seconds):
                for label in labels:
                    if label.endswith('_api') and not scene.offline: owned_apis[label].wait(timeout=seconds)
                check(all(self.identities()[label] is None for label in labels), 'owned lifecycle exit')
        cleaned = raw.finish(owner, {**owner, 'approved_by': 'executor', 'approval_ref': 'test-tool fixture cleanup, not live role authority',
                             'archive': archived['archive']}, archived,
                             {'approved_by': 'executor', 'approval_ref': 'independent raw tar recount fixture',
                              'archive': archived['archive'], 'counts': readback}, self.out / 'cleanup', Lifecycle())
        check(cleaned['status'] == 'PASS' and cleaned['root_removed'], 'archive-readback before stop; no SQLite after stop; remove root')

    def close(self):
        # These are our unreaped Popen children, with no PID reuse possible.
        for child, stdout, stderr in self.children:
            if child.poll() is None: child.terminate()
            child.wait(timeout=3); stdout.close(); stderr.close()
        for thread in self.threads:
            thread.join(timeout=3); check(not thread.is_alive(), 'HTTP actor thread exited')
        if self.root.exists(): shutil.rmtree(self.root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--offline', action='store_true', help='Use the real Handler with byte streams and an injected unit clock; no ports/processes')
    parser.add_argument('--mutant', choices=['bash-schema'])
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    check(args.mutant is None or args.offline, 'mutants use deterministic in-memory handlers only')
    record = {'status': 'INCOMPLETE', 'real_role_CLIs': 0, 'model_turns': 0, 'offline': args.offline,
              'clock_scope': 'injected unit clock' if args.offline else 'real system wall and monotonic clocks',
              'HTTP_transport': 'real Handler byte streams' if args.offline else 'real loopback HTTP',
              'product_daemon_relay_and_Electron': 'not exercised; deterministic rows/window/normal_stop boundary'}
    scene = None
    def timeout(*_): raise TimeoutError('rev2_rehearsal_hard_deadline_210_seconds')
    previous = {number: signal.signal(number, timeout) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    signal.alarm(210)
    try:
        record['preflight'] = preflight()
        if not args.check_only:
            scene = Rehearsal.__new__(Rehearsal)
            scene.__init__(out, args.offline, args.mutant); scene.flow()
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            if scene:
                scene.close(); record['owned_processes_exited'] = True; record['scratch_removed'] = not scene.root.exists()
        except Exception as error:
            record.update(status='BLOCKED', cleanup_error=repr(error), cleanup_traceback=traceback.format_exc())
        signal.alarm(0)
        for number, handler in previous.items(): signal.signal(number, handler)
        raw.save(out / 'result.json', record)
    print(json.dumps(record, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
