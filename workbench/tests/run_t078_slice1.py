"""Executor-approved root submit, one native tool permission, and slice readback."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import tarfile
import time
import traceback
from command_evidence import CommandLog, command_json
from p1_processes import identity_from_ps

SOURCE = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--materials', type=Path, required=True)
    p.add_argument('--phase', choices=['submit', 'permission', 'readback'], required=True)
    p.add_argument('--label')
    p.add_argument('--readiness-file', type=Path)
    p.add_argument('--approval-file', type=Path)
    args = p.parse_args()
    materials = args.materials.resolve()
    approval = json.loads((materials / 'approval.json').read_bytes())
    manifest = approval['input']; root = Path(manifest['root']); state = root / 'state'
    scenario = json.loads((materials / 'scenario.json').read_bytes())
    if scenario['name'] not in ('slice1-inbox-red', 'slice1-inbox-green'):
        raise ValueError('A declared one-role inbox slice is required.')
    green = scenario['name'] == 'slice1-inbox-green'
    label = args.label or args.phase
    if Path(label).name != label or label in ('.', '..'):
        raise ValueError('A new single directory name is required.')
    out = materials / label; out.mkdir()
    log = CommandLog(out)
    env = json.loads((materials / 'control-plane.json').read_bytes())['environment']
    cli = [approval['launch']['node_executable'], SOURCE / 'workbench/src/gates/cli.ts', '--state', state]
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'phase': args.phase,
              'scope': 'One real Claude CLI, scripted fake API, actual Bash/inbox/hook; no vendor model',
              'input': manifest, 'real_model_turns': 0, 'source': 'test-simulated-user'}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, child_env=env, timeout=20):
        value = log.run(argv, cwd=SOURCE, env=child_env, timeout=timeout)
        if value.returncode:
            raise RuntimeError({'command_failed': value.evidence})
        return value

    def call(command, *values):
        result = command_json(run([*cli, command, *values]))
        if not result.get('ok'):
            raise RuntimeError(result)
        return result

    def rows(table):
        with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
            return [json.loads(r[0]) for r in db.execute('SELECT data FROM ' + table)]

    def count(table):
        with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
            return db.execute('SELECT count(*) FROM ' + table).fetchone()[0]

    def events():
        with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
            return [{'seq': r[0], 'type': r[1], 'launch': r[2], 'data': json.loads(r[3])}
                    for r in db.execute('SELECT seq,type,launch,data FROM orchestration_events WHERE launch=? ORDER BY seq', (manifest['launch'],))]

    def wait(predicate, seconds=30):
        deadline = time.monotonic() + seconds
        while not predicate():
            if (root / 'api-error.json').exists():
                raise RuntimeError('Fake API protocol or budget error; no retry.')
            if time.monotonic() > deadline:
                raise RuntimeError('Observation deadline; retain the live fixture.')
            time.sleep(.05)

    def snapshot():
        value = call('pane_output', '--launch', manifest['launch'], '--offset', '0')
        if value['next_offset'] != value['total_bytes']:
            raise RuntimeError('Full screen exceeds the read limit.')
        return value, base64.b64decode(value['data_base64'])

    def consent():
        if not args.approval_file:
            raise ValueError('A separate executor approval file is required.')
        value = json.loads(args.approval_file.read_bytes())
        if (any(value.get(k) != manifest[k] for k in ['launch', 'session', 'thread'])
                or value.get('approved_by') != 'executor' or not value.get('approval_ref')
                or not value.get('basis') or value.get('source') != 'test-simulated-user'
                or value.get('bash_command') != scenario['bash_command']):
            raise ValueError('Approval identity, action or source does not match.')
        record['approval'] = value; save()
        return value

    def readback():
        if green:
            return readback_green()
        wait(lambda: (root / 'api-finished-2.json').exists())
        wait(lambda: call('pane_status', '--thread', manifest['thread'])['state'] == 'idle')
        wait(lambda: any((d / 'finished.json').exists() and
             json.loads((d / 'stdin.bin').read_bytes()).get('hook_event_name') == 'Stop'
             for d in (root / 'hooks').iterdir()))
        hook_rows = []
        for directory in (root / 'hooks').iterdir():
            if (directory / 'finished.json').exists():
                payload = json.loads((directory / 'stdin.bin').read_bytes())
                done = json.loads((directory / 'finished.json').read_bytes())
                hook_rows.append({'input': payload, 'finished': done, 'directory': str(directory)})
        ups = [h for h in hook_rows if h['input'].get('hook_event_name') == 'UserPromptSubmit']
        stops = [h for h in hook_rows if h['input'].get('hook_event_name') == 'Stop']
        actual = json.loads((root / 'actual-tool-result.json').read_bytes())
        trace = events()
        if (len(ups) != 1 or len(stops) != 1 or ups[0]['input']['prompt'] != '⟦主控 #1⟧\n' + scenario['nonce']
                or ups[0]['input']['prompt_id'] != stops[0]['input']['prompt_id']
                or any(h['input']['session_id'] != manifest['session'] or h['finished']['exit_code'] != 0 for h in hook_rows)
                or actual['tool_result'].get('is_error') is not True
                or 'worker_request_directory_required' not in actual['text']
                or 'daemon_call_failed' not in actual['text']):
            raise RuntimeError('The actual tool/hook evidence does not establish the predicted entry red.')
        intents = [e for e in trace if e['type'] == 'turn_submit_intent']
        registered = [e for e in intents if e['data'].get('source') != 'user']
        keyboard = [e for e in intents if e['data'].get('source') == 'user']
        controls = [a for a in rows('user_inputs') if a.get('target', {}).get('thread') == manifest['thread']
                    and a.get('content', {}).get('data') == '\r' and a.get('form') == 'action']
        if (len(registered) != 1 or len(keyboard) > 1 or len(keyboard) != len(controls)
                or (keyboard and keyboard[0]['data'].get('request_id') != controls[0].get('source_ref', {}).get('command_id'))
                or len([e for e in trace if e['type'] == 'pane_idle']) != 1
                or list((root / 'requests').glob('*.json')) or rows('inbox_records')
                or count('relay_requests') or count('relay_results') or (root / 'api-error.json').exists()):
            raise RuntimeError('Root budget, negative transfer facts or completion do not match.')
        messages = [json.loads(s) for s in (root / 'api.jsonl').read_text(encoding='utf-8').splitlines()]
        if len([m for m in messages if m['path'] == '/v1/messages']) != 2:
            raise RuntimeError('Messages budget does not match.')
        output, raw = snapshot(); (out / 'screen.bin').write_bytes(raw)
        record.update(status='PASS', red_evidence_status='PASS', product_status='INCOMPLETE',
                      claim='Actual controller inbox tool is rejected before request-file admission; Stop does not transfer it.',
                      actual_native_root_submits=len(ups), registered_root_intents=registered,
                      permission_enter_false_root_intents=keyboard,
                      submission_ledger_status='INCOMPLETE' if keyboard else 'not_exercised',
                      original_registration_settlement='INCOMPLETE' if keyboard else 'observed_without_permission_key',
                      tool_result=actual, hooks=hook_rows, events=trace, api_requests=messages,
                      output=output, final=call('pane_status', '--thread', manifest['thread']))
        save()

    def readback_green():
        wait(lambda: (root / 'api-finished-3.json').exists())
        wait(lambda: call('pane_status', '--thread', manifest['thread'])['state'] == 'idle')
        def completed_hooks():
            return [{'input': json.loads((d / 'stdin.bin').read_bytes()),
                     'finished': json.loads((d / 'finished.json').read_bytes()), 'directory': str(d)}
                    for d in (root / 'hooks').iterdir() if (d / 'finished.json').exists()]
        wait(lambda: len([h for h in completed_hooks() if h['input'].get('hook_event_name') == 'Stop']) == 2)
        hooks = completed_hooks()
        ups = [h['input'] for h in hooks if h['input']['hook_event_name'] == 'UserPromptSubmit']
        stops = [h['input'] for h in hooks if h['input']['hook_event_name'] == 'Stop']
        if (len(ups) != 2 or len(stops) != 2 or len({h['prompt_id'] for h in ups}) != 2
                or {h['prompt_id'] for h in ups} != {h['prompt_id'] for h in stops}
                or any(h['finished']['exit_code'] != 0 or h['input']['session_id'] != manifest['session'] for h in hooks)):
            raise RuntimeError('Two distinct native roots and matched successful Stops are required.')
        first = next(h for h in ups if h['prompt'] == '⟦主控 #1⟧\n' + scenario['nonce'])
        feedback = next(h for h in ups if h['prompt'].startswith('⟦门禁 #2⟧\n'))
        trace = events(); intents = [e for e in trace if e['type'] == 'turn_submit_intent']
        idle = [e for e in trace if e['type'] == 'pane_idle']
        if len(intents) != 2 or any(e['data'].get('source') == 'user' for e in intents) or len(idle) != 2:
            raise RuntimeError('Permission Enter must not add a root or replace either registration.')
        if {e['data']['submission'] for e in idle} != {e['data']['id'] for e in intents}:
            raise RuntimeError('Both original registered submissions must settle.')
        with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
            receipts = [json.loads(r[0]) for r in db.execute('SELECT data FROM relay_results')]
            requests = [dict(zip(['input','attempt'], r)) for r in db.execute('SELECT input,attempt FROM relay_requests')]
        expected = [entry['id'] for entry in scenario['inbox_fixture'] if entry['to'] == 'ideation']
        if (len(receipts) != 1 or len(requests) != 1 or receipts[0].get('ok') is not True
                or [v['entry']['id'] for v in receipts[0]['entries']] != expected or requests[0]['attempt'] is not None):
            raise RuntimeError('Exactly one real role-scoped execution must be persisted.')
        packet = json.loads(requests[0]['input'])
        if (packet['schema'] != 2 or packet['preset'] != 'ideation' or packet['launch'] != manifest['launch']
                or packet['prompt_id'] != first['prompt_id'] or 'attempt' in packet or 'fence' in packet):
            raise RuntimeError('Controller request identity must be genuine and have no worker attempt.')
        api = [json.loads(s) for s in (root / 'api.jsonl').read_text(encoding='utf-8').splitlines()]
        if len([m for m in api if m['path'] == '/v1/messages']) != 3 or (root / 'api-error.json').exists():
            raise RuntimeError('Green Messages budget or protocol did not hold.')
        if count('inbox_records') != len(scenario['inbox_fixture']) or count('inbox_deliveries') != 0:
            raise RuntimeError('Read-only list must not create or acknowledge business entries.')
        if len(list((root / 'requests').glob('*.json'))) != 1:
            raise RuntimeError('One original request file is required; no resend.')
        output, raw = snapshot(); (out / 'screen.bin').write_bytes(raw)
        record.update(status='PASS', product_status='PASS', claim='One controller inbox request executed once at real Stop and received actual feedback; permission Enter preserved registration',
                      scope='Single-role fake-API green only; not 09B/09C/full ticket acceptance',
                      hooks=hooks, events=trace, execution_results=receipts, request=packet,
                      first_prompt=first, feedback_prompt=feedback, api_requests=api, output=output)
        save()

    save()
    try:
        for name in ['input.json', 'scenario.json', 'nonce.txt', 'role.md']:
            if (root / name).read_bytes() != (materials / name).read_bytes():
                raise RuntimeError('Approved input changed: ' + name)
        with tarfile.open(materials / 'sources.tar.gz') as archive:
            for name in json.loads((materials / 'source-files.json').read_bytes()):
                if (SOURCE / name).read_bytes() != archive.extractfile(name).read():
                    raise RuntimeError('Frozen source changed: ' + name)
        owner = json.loads((materials / 'launch/process-manifest.json').read_bytes())
        ps = log.run(['/bin/ps', '-p', str(owner['cli']['pid']), '-o', 'pid=,lstart=,comm='],
                     cwd=SOURCE, env={**env, 'LC_ALL': 'C', 'LANG': 'C'}, timeout=10)
        if (any(owner[k] != manifest[k] for k in ('launch', 'session'))
                or identity_from_ps(owner['cli']['pid'], ps.returncode, ps.stdout, ps.stderr) != owner['cli']):
            raise RuntimeError('Recorded native CLI identity changed.')
        if args.phase == 'submit':
            value = consent()
            if (not args.readiness_file or value.get('nonce') != scenario['nonce']
                    or any(value.get(k) != v for k, v in [('root_submit_budget', scenario['root_submit_budget']), ('messages_request_budget', scenario['messages_request_budget']), ('tool_call_budget', 1)])):
                raise ValueError('The declared root, Messages and tool budgets require approval.')
            ready = json.loads(args.readiness_file.read_bytes())
            if (any(ready.get(k) != manifest[k] for k in ('launch', 'session'))
                    or ready.get('confirmed_by') != 'executor' or ready.get('readiness') != 'confirmed' or not ready.get('basis')):
                raise ValueError('Fresh startup-readiness approval is required.')
            if any(e['type'] == 'turn_submit_intent' for e in events()):
                raise RuntimeError('This instance already submitted its only root; no replay.')
            call('pane_release', '--thread', manifest['thread'], '--reason', 'Executor approved slice1 initial readiness')
            record['dispatch'] = call('pane_dispatch', '--thread', manifest['thread'], '--body-file', root / 'nonce.txt'); save()
            wait(lambda: (root / 'actual-tool-result.json').exists() or any(e['type'] == 'permission_wait' for e in events()))
            if (root / 'actual-tool-result.json').exists():
                readback()
            else:
                output, raw = snapshot(); (out / 'screen.bin').write_bytes(raw)
                record.update(output=output, events=events(), next='Read the native Bash permission screen; separately approve one Yes/Enter. No key sent.')
        elif args.phase == 'permission':
            value = consent()
            screen = Path(value['screen_file']); output, raw = snapshot()
            if raw != screen.read_bytes() or value.get('key') != 'Enter' or value.get('selected_label') != 'Yes':
                raise ValueError('Permission screen changed or the one-time Yes action was not approved.')
            waits = [e for e in events() if e['type'] == 'permission_wait' and e['seq'] == value.get('permission_seq')]
            pane = call('pane_status', '--thread', manifest['thread'])
            if (len(waits) != 1 or waits[0]['data'].get('tool_name') != 'Bash'
                    or waits[0]['data'].get('tool_input', {}).get('command') != scenario['bash_command']
                    or pane['state'] != 'busy' or pane.get('failed') or not pane.get('active')
                    or pane['active']['dispatch'] != value.get('dispatch') or (root / 'actual-tool-result.json').exists()):
                raise ValueError('Native permission, command or active dispatch no longer matches.')
            from electron_client import ElectronClient
            slot = 't078-slice1-' + manifest['launch']
            run(['node', SOURCE / 'workbench/app/build.mjs', '--slot', slot], timeout=90)
            build = Path('/Volumes/WD-Elements/a2a-workbench') / slot / 'dist'
            record['frontend_slot'] = str(build); save()
            client = ElectronClient(SOURCE, build, state, manifest['task'], root / 'electron-home', out / 'electron', env, launch=manifest['launch'])
            try:
                line = value.get('selected_line', '')
                if not re.fullmatch(r'\s*❯\s*1\.\s*Yes\s*', line):
                    raise ValueError('Only the exact one-time Yes cursor line is supported.')
                view = client.wait(lambda v: v.get('input_enabled') and v.get('active_dispatch') == value['dispatch']
                                   and line.strip() in v['terminal'])
                if (line.strip() not in view['terminal']
                        or view['thread'] != manifest['thread'] or view['launch'] != manifest['launch']):
                    raise ValueError('The approved cursor is not visibly on the one-time Yes option.')
                client.call('capture', name='permission-before-key')
                _, current = snapshot()
                if current != raw:
                    raise ValueError('Permission screen changed before the key; no key sent.')
                before = events()[-1]['seq']
                record['key_attempt'] = client.call('terminal-key', key='Enter', permission=True,
                    launch=manifest['launch'], thread=manifest['thread'], dispatch=value['dispatch'],
                    window_id=view['window_id'], source='test-simulated-user', approval_ref=value['approval_ref']); save()
                wait(lambda: any(e['seq'] > before and e['type'] == 'terminal_input_written' for e in events()))
                after = [e for e in events() if e['seq'] > before]
                intents = [e for e in after if e['type'] == 'terminal_input_write_intent' and e['data'].get('data') == '\r']
                if len(intents) != 1:
                    raise RuntimeError('Exactly one control Enter intent is required.')
                receipt = intents[0]['data']
                for kind in ['window_request_admitted', 'terminal_input_written']:
                    if len([e for e in after if e['type'] == kind and e['data'].get('request_id') == receipt['request_id']
                            and e['data'].get('window_id') == view['window_id']]) != 1:
                        raise RuntimeError('The Enter lacks its matched window/write receipt.')
                actions = [a for a in rows('user_inputs') if a.get('source_ref', {}).get('command_id') == receipt['request_id']]
                if len(actions) != 1 or actions[0]['form'] != 'action' or actions[0].get('content', {}).get('data') != '\r':
                    raise RuntimeError('Native permission Enter must be a control action, not a message.')
                record['control_action'] = actions[0]; readback()
                client.call('capture', name='red-completion')
            finally:
                client.close()
        else:
            readback()
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        save()
    print(json.dumps({'status': record['status'], 'product_status': record['product_status'],
                      'phase': args.phase, 'output': str(out), 'next': record.get('next'), 'error': record.get('error')}))
    return 1 if record.get('error') else 0


if __name__ == '__main__':
    raise SystemExit(main())
