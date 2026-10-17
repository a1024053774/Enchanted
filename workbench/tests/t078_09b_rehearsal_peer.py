"""Deterministic PTY replacement for Claude; real hooks, HTTP and native Bash."""
import argparse
import copy
import json
import os
import shlex
import signal
import subprocess
import sys
import termios
import time
import tty
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def initial_messages(template, text):
    messages = copy.deepcopy(template['request']['messages'])
    for message in messages:
        for block in message['content']:
            if block.get('text') == '{{dispatch}}':
                block['text'] = text
    return messages


def tool_result_message(template, tool, payload):
    message = copy.deepcopy(template['tool_result_message'])
    message['content'][0].update(tool_use_id=tool['id'], content=json.dumps(payload, ensure_ascii=False))
    return message


def parse_sse(raw):
    events = [json.loads(line[6:]) for line in raw.decode('utf-8').splitlines() if line.startswith('data: ')]
    if [event['type'] for event in events] != ['message_start', 'content_block_start', 'content_block_delta',
                                            'content_block_stop', 'message_delta', 'message_stop']:
        raise RuntimeError('six_complete_sse_events_required')
    block = events[1]['content_block']
    if block['type'] == 'tool_use':
        return {'type': 'tool_use', 'id': block['id'], 'name': block['name'],
                'input': json.loads(events[2]['delta']['partial_json'])}
    if block['type'] != 'text':
        raise RuntimeError('unexpected_response_block')
    return {'type': 'text', 'text': events[2]['delta']['text']}


def allowed_command(plan, role, tool):
    """Only the frozen scratch I_SEND_STOP command may execute in this peer."""
    if role != 'ideation' or tool.get('name') != 'Bash' or set(tool.get('input', {})) != {'command'}:
        raise RuntimeError('unapproved_rehearsal_tool')
    if plan.get('scene') == '09C' and shlex.split(tool['input']['command'])[2:3] == ['stop']:
        from t078_09b_phase_registry import stop_entry
        expected = [plan['node'], str(Path(plan['source']) / 'workbench/src/gates/cli.ts'), 'stop',
                    '--thread', plan['target_binding']['thread_id'], '--stop-id', stop_entry(plan)['id']]
        if tool['input']['command'] != shlex.join(expected):
            raise RuntimeError('C_stop_command_outside_owned_target')
        return tool['input']['command']
    protocol = json.loads(Path(plan['protocol_source']).read_bytes())
    replacements = {'target.thread_id': plan['target_binding']['thread_id'],
                    'target.attempt_id': plan['target_binding']['attempt_id'],
                    'synthetic_user_input.id': plan['synthetic_input_id']}
    argv = []
    for token in protocol['commands']['I_SEND_STOP']['argv']:
        for key, value in replacements.items():
            token = token.replace('{' + key + '}', value)
        if token.endswith('/roles/ideation/stop-body.txt'):
            token = str(Path(plan['root']) / 'roles/ideation/stop-body.txt')
        argv.append(token)
    if tool['input']['command'] != shlex.join(argv) or shlex.split(tool['input']['command']) != argv:
        raise RuntimeError('tool_command_outside_frozen_scratch_send')
    body_path = Path(argv[argv.index('--body-file') + 1]).resolve()
    if body_path != Path(plan['root']) / 'roles/ideation/stop-body.txt':
        raise RuntimeError('tool_body_outside_scratch')
    return tool['input']['command']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--role', choices=['ideation', 'executor'], required=True)
    parser.add_argument('--structure', type=Path, required=True)
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--debug-file', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(); role = args.role
    if not root.name.startswith('t078-2-a14-rehearsal-') or root.parent != Path('/private/tmp'):
        raise RuntimeError('owned_scratch_required')
    log = root / 'peer' / role; log.mkdir(parents=True)
    if args.session_id != os.environ['A2A_SESSION'] or args.debug_file != root/'roles'/role/'claude-debug.log':
        raise ValueError('peer_actual_session_or_debug_binding_mismatch')
    with args.debug_file.open('x',encoding='utf-8') as stream:stream.write('Deterministic Python provider; not Claude Code.\n')
    scene = json.loads((root / 'protocol-plan.json').read_bytes())['scene']
    template = json.loads(args.structure.read_bytes())
    hook_argv = shlex.split(os.environ['T078_REHEARSAL_HOOK'])
    expected = [os.environ['T078_REHEARSAL_NODE'], os.environ['T078_REHEARSAL_CLI'], '--state',
                str(root / 'state'), 'signal', '--launch', os.environ['A2A_LAUNCH']]
    if hook_argv != expected:
        raise RuntimeError('native_hook_argv_mismatch')
    sequence = 0; hook_number = 0; history = []

    def hook(event, prompt_id, **extra):
        nonlocal hook_number
        hook_number += 1
        payload = {'session_id': os.environ['A2A_SESSION'], 'hook_event_name': event, 'prompt_id': prompt_id, **extra}
        completed = subprocess.run(hook_argv, input=json.dumps(payload), text=True, capture_output=True, timeout=15)
        save(log / f'hook-{hook_number:02d}.json', {'argv': hook_argv, 'payload': payload,
             'exit_code': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr})
        if completed.returncode or '"decision":"block"' in completed.stdout.replace(' ', ''):
            raise RuntimeError('native_hook_refused_' + event)

    def post():
        nonlocal sequence
        sequence += 1
        body = {**template['request'], 'messages': copy.deepcopy(history)}
        save(log / f'post-{sequence:02d}.json', body)
        started = time.monotonic()
        request = urllib.request.Request(os.environ['ANTHROPIC_BASE_URL'] + '/v1/messages',
                   data=json.dumps(body, ensure_ascii=False).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=205) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as response:
            status, raw = response.code, response.read()
        (log / f'response-{sequence:02d}.bin').write_bytes(raw)
        save(log / f'http-{sequence:02d}.json', {'status': status, 'elapsed_seconds': time.monotonic() - started,
             'retry': False, 'sequence': sequence})
        if status != 200:
            save(log / 'stopped.json', {'status': 'INCOMPLETE', 'http': status, 'error': json.loads(raw).get('error'),
                 'posts': sequence, 'retry': False})
            raise SystemExit(3)
        return parse_sse(raw)

    def run_turn(text):
        nonlocal history
        prompt = str(uuid.uuid4())
        hook('UserPromptSubmit', prompt, prompt=text)
        if not history:
            history = initial_messages(template, text)
        else:
            history.append({'role': 'user', 'content': [{'type': 'text', 'text': text}]})
        response = post()
        if response['type'] == 'tool_use':
            hook('PermissionRequest', prompt, tool_name=response['name'], tool_input=response['input'])
            # E1 stops here; no executor Bash is permitted by this rehearsal.
            save(log / ('permission-' + prompt + '.json'), {'prompt_id': prompt, 'tool_use': response})
            if scene == '09C':
                import textwrap
                box = '\r\n'.join('│ ' + line for line in textwrap.wrap(response['input']['command'], width=60,
                    break_long_words=False, break_on_hyphens=False))
                print('\r\nRun shell command\r\n' + box + '\r\nThis command requires approval\r\n❯ 1. Yes\r\n  2. No', flush=True)
            else:
                print('\r\nBash command:\r\n' + response['input']['command'] + '\r\n❯ 1. Yes\r\n  2. No', flush=True)
            key = os.read(0, 1)
            (log / ('permission-key-' + prompt + '.bin')).write_bytes(key)
            if role == 'executor':
                raise RuntimeError('executor_permission_must_remain_unanswered')
            if key != b'\r':
                raise RuntimeError('permission_requires_one_CR')
            plan = json.loads((root / 'protocol-plan.json').read_bytes())
            command = allowed_command(plan, role, response)
            done = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-c', command],
                                  cwd=root / 'repo', capture_output=True, text=True, timeout=15)
            execution_file = 'tool-execution-' + prompt + '.json' if scene == '09C' else 'tool-execution.json'
            save(log / execution_file, {'command': command, 'exit_code': done.returncode,
                 'stdout': done.stdout, 'stderr': done.stderr, 'source': 'deterministic-role-peer'})
            if done.returncode:
                raise RuntimeError('scratch_tool_execution_failed')
            queued = json.loads(done.stdout)
            if queued.get('ok') is not True or queued.get('queued') is not True or queued.get('delivered') is not False:
                raise RuntimeError('actual_queued_tool_result_required')
            history.append({'role': 'assistant', 'content': [response]})
            history.append(tool_result_message(template, response, queued))
            # Preserve the observed trailing system-message structure.
            history.extend(copy.deepcopy([message for message in template['request']['messages'] if message['role'] == 'system']))
            response = post()
            if response['type'] != 'text':
                raise RuntimeError('tool_settlement_must_be_text')
        history.append({'role': 'assistant', 'content': [response]})
        hook('Stop', prompt, stop_hook_active=False, last_assistant_message=response['text'])
        save(log / ('turn-' + prompt + '.json'), {'status': 'PASS', 'prompt_id': prompt, 'posts': sequence,
             'last_assistant_message': response['text']})
        print('\r\nT078_REHEARSAL_IDLE\r\n', flush=True)

    original = termios.tcgetattr(0); tty.setraw(0)
    # Actual OS helper, not a mocked successful topology receipt. It remains
    # auxiliary to the registered Python provider and is reaped on normal HUP.
    helper=subprocess.Popen(['caffeinate','-i','-t','300'],executable='/usr/bin/caffeinate',
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    save(log/'caffeinate-owner.json',{'pid':helper.pid,'ppid':os.getpid(),'argv':['caffeinate','-i','-t','300'],
                                    'executable':'/usr/bin/caffeinate','scope':'deterministic peer owned helper; not a role identity'})
    def normal_close(*_):
        if helper.poll() is None:helper.terminate()
        helper.wait(timeout=3)
        raise SystemExit(0)
    for number in [signal.SIGHUP,signal.SIGTERM,signal.SIGINT]:signal.signal(number,normal_close)
    ready=log/'ready.pending'
    save(ready,{'pid':os.getpid(),'ppid':os.getppid(),'session':args.session_id,'role':role,'fixture':True})
    os.link(ready,log/'ready.json');ready.unlink()
    print('T078_REHEARSAL_READY\r\n\x1b[?2004h', end='', flush=True)
    buffer = b''
    try:
        while True:
            chunk = os.read(0, 65536)
            if not chunk:
                return 0
            with (log / 'received.bin').open('ab') as stream:
                stream.write(chunk)
            buffer += chunk
            while b'\x1b[201~\r' in buffer:
                start = buffer.find(b'\x1b[200~')
                end = buffer.index(b'\x1b[201~\r')
                if start != 0 or end < start:
                    raise RuntimeError('bracketed_paste_then_submit_required')
                text = buffer[6:end].decode('utf-8'); buffer = buffer[end + 7:]
                run_turn(text)
    finally:
        termios.tcsetattr(0, termios.TCSANOW, original)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        raise
