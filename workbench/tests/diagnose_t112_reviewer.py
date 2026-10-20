"""Real reviewer -> native CLI -> local Responses API -> shell -> file boundary.

No sandbox subcommand, PTY replacement, global config or model calls. Python 3.9.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from run_t112_native import extract_baseline
from t108_cleanup import observe, stop_owned


BINARY = Path('/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex')
BASELINE = 'e3102389eda8952ea92cae4b373e14eaff898314'


def shell_item(tools, command, cwd):
    """Use the CLI's advertised shell tool; never return a made-up tool name."""
    flattened = []
    for tool in tools:
        if tool['type'] == 'namespace':
            flattened.extend((child, tool['name']) for child in tool['tools'])
        else:
            flattened.append((tool, None))
    for tool, namespace in flattened:
        name = tool.get('name')
        if tool['type'] == 'function' and name in ('exec_command', 'shell_command'):
            field = 'cmd' if name == 'exec_command' else 'command'
            args = {field: command, 'workdir': str(cwd)}
            if name == 'exec_command': args['yield_time_ms'] = 10000
            item = dict(type='function_call', name=name, arguments=json.dumps(args))
            break
        if tool['type'] == 'custom' and name == 'exec':
            code = 'text(await tools.exec_command(' + json.dumps({'cmd': command, 'workdir': str(cwd), 'yield_time_ms': 10000}) + '));'
            item = dict(type='custom_tool_call', name=name, input=code)
            break
    else:
        raise AssertionError('CLI did not advertise a supported shell tool: ' + json.dumps(tools))
    item.update(id='fc_' + uuid.uuid4().hex, call_id='call_t112_' + uuid.uuid4().hex)
    if namespace:
        item['namespace'] = namespace
    return item


def tool_events(item, model):
    response = dict(id='resp_' + uuid.uuid4().hex, object='response', status='completed', model=model,
                    output=[item], usage={'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15})
    field = 'input' if item['type'] == 'custom_tool_call' else 'arguments'
    stem = 'response.custom_tool_call_input' if field == 'input' else 'response.function_call_arguments'
    return [('response.created', {'response': dict(response, status='in_progress', output=[])}),
            ('response.output_item.added', {'output_index': 0, 'item': dict(item, **{field: ''}, status='in_progress')}),
            (stem + '.delta', {'output_index': 0, 'item_id': item['id'], 'delta': item[field]}),
            (stem + '.done', {'output_index': 0, 'item_id': item['id'], field: item[field]}),
            ('response.output_item.done', {'output_index': 0, 'item': dict(item, status='completed')}),
            ('response.completed', {'response': response})]


def assert_native_call(emitted, native_records):
    calls = [row for row in native_records if row.get('type') == emitted['type'] and row.get('call_id') == emitted['call_id']]
    assert len(calls) == 1, 'Expected one matching persisted native call'
    actual = calls[0]
    assert actual['name'] == emitted['name'], 'Native tool name changed'
    if emitted['type'] == 'function_call':
        assert json.loads(actual['arguments']) == json.loads(emitted['arguments']), 'Native command or cwd changed'
    else:
        assert actual['input'] == emitted['input'], 'Native code input changed'


def run_reviewer_case(source, tree, case, revision, env, report, bad=False):
    case.mkdir()
    for name in ('candidate', 'worker-home', 'reviewer-home'):
        (case / name).mkdir()
    (case / 'role.md').write_text('仅执行本地固定权限探针，不提交或验收。\n', encoding='utf-8')
    protected, writable = case / 'protected.txt', case / 'candidate/candidate-probe.txt'
    protected.write_text('unchanged\n', encoding='utf-8')
    nonce = uuid.uuid4().hex
    candidate_value, forbidden_value = 'candidate-only-' + nonce, 'forbidden-' + nonce
    python = 'from pathlib import Path; Path(' + repr(str(writable)) + ').write_text(' + repr(candidate_value) + '); Path(' + repr(str(protected)) + ').write_text(' + repr(forbidden_value) + ')'
    command = shlex.join(['/usr/bin/python3', '-I', '-S', '-B', '-c', python])
    requests, api_errors = [], []
    done = threading.Event()
    result = dict(label=case.name, revision=revision, bad_parent_writable=bad,
                  expected_writes={'candidate': candidate_value, 'protected': forbidden_value})
    report.setdefault('cases', []).append(result)
    emitted = None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args): pass

        def do_GET(self):
            assert self.path in ('/v1/models', '/models'), self.path
            body = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(body)

        def do_POST(self):
            nonlocal emitted
            try:
                assert self.path in ('/v1/responses', '/responses'), self.path
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(body)
                result.setdefault('api_selections', []).append({key: body.get(key) for key in ('model', 'reasoning', 'service_tier')})
                assert len(requests) <= 2, 'Unexpected additional API request'
                if emitted is not None:
                    outputs = [row for row in body.get('input', []) if row.get('call_id') == emitted['call_id'] and
                               row.get('type') in ('function_call_output', 'custom_tool_call_output')]
                    assert outputs, 'Continuation must contain the exact native tool result'
                    result['tool_outputs'] = outputs
                    self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                    # The probe ends at the shell receipt. Do not fabricate a
                    # valid review or run the Stop/delivery part of another task.
                    done.wait(90)
                    return
                emitted = shell_item(body['tools'], command, case / 'candidate')
                result['advertised_tools'] = body['tools']
                result['emitted_tool_call'] = emitted
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(tool_events(emitted, body['model'])):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api_errors.append(str(error))
                self.send_error(500)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    config = ('model_provider = "t112_fixture"\ncli_auth_credentials_store = "file"\n'
              '[model_providers.t112_fixture]\nname = "T112 local fixture"\nbase_url = "http://127.0.0.1:' + str(server.server_port) + '/v1"\n'
              'wire_api = "responses"\nrequires_openai_auth = false\n[projects.' + json.dumps(str(case)) + ']\ntrust_level = "trusted"\n')
    if bad:
        config += '[sandbox_workspace_write]\nwritable_roots = [' + json.dumps(str(case)) + ']\n'
    (case / 'reviewer-home/config.toml').write_text(config, encoding='utf-8')
    result['isolated_config'] = config
    manifest = dict(source=str(tree / 'workbench'), root=str(case), binary=str(BINARY), revision=revision)
    (case / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    argv = ['node', str(source / 'workbench/tests/t112_reviewer_record.mjs'), str(case / 'manifest.json')]
    owners = []
    process = None
    logs = []
    local_env = {**env, 'A2A_OPERATOR_CREDENTIAL': str(case / 'operator.json')}
    try:
        for name in ('stdout', 'stderr'):
            logs.append((case / ('host.' + name)).open('w', encoding='utf-8'))
        process = subprocess.Popen(argv, env=local_env, stdout=logs[0], stderr=logs[1], start_new_session=True)
        owner = observe(process.pid); assert owner and str(case / 'manifest.json') in owner['command']; owners.append(owner)
        end = time.monotonic() + 90
        while not result.get('tool_outputs'):
            assert not api_errors, api_errors
            assert process.poll() is None, 'Reviewer host exited before native tool output'
            assert not (case / 'host-error.json').exists(), (case / 'host-error.json').read_text() if (case / 'host-error.json').exists() else ''
            assert time.monotonic() < end, 'Native reviewer shell receipt deadline'
            time.sleep(.1)
        result['launch'] = json.loads((case / 'launch.json').read_text(encoding='utf-8'))
        result['native_identity'] = json.loads((case / 'identity.json').read_text(encoding='utf-8'))
        assert result['launch']['argv'][0] == str(BINARY) and result['launch']['cli_version'] == 'codex-cli 0.162.1'
        recorded = result['launch']['argv']
        expected_effort = 'xhigh' if revision == BASELINE else 'low'
        assert result['launch']['effort_requested'] == expected_effort
        assert 'model_reasoning_effort=' + json.dumps(expected_effort) in recorded
        assert all(row['model'] == 'gpt-6.1-sol' and row['reasoning']['effort'] == expected_effort for row in result['api_selections'])
        for flag, expected in [('-C', str(case / 'candidate')), ('-a', 'never'), ('--sandbox', 'workspace-write'), ('-m', 'gpt-6.1-sol')]:
            assert recorded[recorded.index(flag) + 1] == expected, (flag, recorded)
        for setting in ('sandbox_workspace_write.network_access=false', 'features.network_proxy=false',
                        'sandbox_workspace_write.exclude_slash_tmp=true', 'sandbox_workspace_write.exclude_tmpdir_env_var=true'):
            assert setting in recorded, (setting, recorded)
        assert '--dangerously-bypass-approvals-and-sandbox' not in recorded
        assert '--dangerously-bypass-hook-trust' in recorded
        assert all(any(argument.startswith('hooks.' + event + '=') for argument in recorded)
                   for event in ('UserPromptSubmit', 'Stop', 'PermissionRequest', 'PreToolUse', 'PostToolUse'))
        logs_native = list((case / 'reviewer-home/sessions').rglob('*.jsonl'))
        assert len(logs_native) == 1, logs_native
        # The tool receipt can reach the API while the rollout writer is still
        # flushing. Read complete lines and wait for the matching native output.
        end = time.monotonic() + 10
        while True:
            text = logs_native[0].read_text(encoding='utf-8')
            rows = [json.loads(line) for line in text.split('\n')[:-1] if line]
            matched = [row['payload'] for row in rows if row['type'] == 'response_item' and row['payload'].get('call_id') == emitted['call_id']]
            if any(row.get('type') in ('function_call_output', 'custom_tool_call_output') for row in matched):
                break
            assert time.monotonic() < end, 'Matching native tool output was not persisted'
            time.sleep(.1)
        result['turn_contexts'] = [row['payload'] for row in rows if row['type'] == 'turn_context']
        result['native_tool_records'] = matched
        assert_native_call(emitted, matched)
        assert result['turn_contexts'], 'Native resolved sandbox context is required'
        for context in result['turn_contexts']:
            policy = context['sandbox_policy']
            assert context['approval_policy'] == 'never' and policy['type'] == 'workspace-write', context
            if bad:
                assert str(case) in policy['writable_roots'], policy
        result['resolved_policy_matches_requested'] = all(context['sandbox_policy'].get('exclude_slash_tmp') is True and
            context['sandbox_policy'].get('exclude_tmpdir_env_var') is True and context['sandbox_policy'].get('network_access') is False
            for context in result['turn_contexts'])
        assert result['resolved_policy_matches_requested'], 'Native resolved policy differs from requested reviewer restrictions'
        result['candidate_write'] = writable.exists() and writable.read_text(encoding='utf-8') == candidate_value
        result['protected_value'] = protected.read_text(encoding='utf-8')
        assert result['candidate_write'], 'Candidate write must succeed; startup or tool failure is not sandbox evidence'
        output = json.dumps(result['tool_outputs'])
        result['boundary_oracle_passed'] = result['protected_value'] == 'unchanged\n' and 'PermissionError' in output
        result['unsafe_write_observed'] = result['protected_value'] == forbidden_value
        if bad:
            assert result['unsafe_write_observed'] and not result['boundary_oracle_passed'], 'The oracle must reject the parent-writable mutant'
        result['status'] = 'OBSERVED'
    finally:
        result['api_requests'] = len(requests)
        result['api_errors'] = api_errors
        # Capture descendants before shutdown, then bind every signal to the
        # observed PID/start time/command. No shared process group is signalled.
        if process and process.poll() is None:
            try:
                snapshot = subprocess.run(['/usr/bin/python3', '-I', '-S', '-B', str(tree / 'workbench/src/processSnapshot.py'), str(process.pid)],
                                          env=env, capture_output=True, text=True, timeout=10)
                assert snapshot.returncode == 0, snapshot.stderr
                for row in json.loads(snapshot.stdout)['rows']:
                    if row['pid'] != process.pid:
                        owner = observe(row['pid'])
                        if owner: owners.append(owner)
            except Exception as error:
                result.setdefault('cleanup_errors', []).append('Cannot inspect reviewer descendants: ' + str(error))
            if (case / 'state/control.sock').exists():
                try:
                    stop = subprocess.run(['node', str(tree / 'workbench/src/gates/cli.ts'), '--state', str(case / 'state'), 'daemon_stop'],
                                          env=local_env, capture_output=True, text=True, timeout=30)
                    result['shutdown'] = dict(exit=stop.returncode, stdout=stop.stdout, stderr=stop.stderr)
                    assert stop.returncode == 0 and json.loads(stop.stdout)['ok'], result['shutdown']
                    process.wait(timeout=15)
                except Exception as error:
                    result.setdefault('cleanup_errors', []).append('Daemon shutdown: ' + str(error))
        result['cleanup'] = []
        for owner in reversed(owners):
            try:
                result['cleanup'].append(stop_owned(owner))
            except Exception as error:
                result.setdefault('cleanup_errors', []).append('Owned process: ' + str(error))
        if process:
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired as error: result.setdefault('cleanup_errors', []).append(str(error))
        done.set(); server.shutdown(); server.server_close()
        for stream in logs: stream.close()
        result['host_logs'] = {name: (case / ('host.' + name)).read_text(encoding='utf-8')[-5000:] for name in ('stdout', 'stderr')}
        result['terminal_tails'] = [file.read_bytes()[-4000:].decode('utf-8', errors='replace') for file in (case / 'state/traces').glob('*/pty.raw')]
        result['final_file_readback'] = {'candidate': writable.read_text(encoding='utf-8') if writable.exists() else None,
                                         'protected': protected.read_text(encoding='utf-8')}
        if not result.get('cleanup_errors') and (case / 'state/state.sqlite3').is_file():
            assert not (case / 'state/state.sqlite3-wal').exists(), 'Database still has a WAL after shutdown'
            with closing(sqlite3.connect((case / 'state/state.sqlite3').as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
                request_dirs = [json.loads(row[0]).get('request_dir') for row in db.execute('SELECT data FROM launch_records')]
            for directory in filter(None, request_dirs):
                target = Path(directory)
                assert target.parent == Path('/private/tmp') and target.name.startswith('a2a-requests-')
                shutil.rmtree(target)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve earlier evidence'
    source = Path(__file__).resolve().parents[2]
    root = Path(tempfile.mkdtemp(prefix='t112-review-native-', dir='/private/tmp'))
    report = dict(status='INCOMPLETE', api_mode='isolated loopback fake Responses API; no credentials',
                  model_calls_by_fixture=0, vendor_egress_observed=None,
                  egress_limitation='No independent system-wide egress monitor; do not interpret local request counts as an egress proof',
                  cases=[], fixture=str(root))
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))}
    manager = root / 'manager'; manager.mkdir()
    env.update(HOME=str(manager), LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    env.pop('NODE_OPTIONS', None)
    try:
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, env=env, text=True).strip()
        report.update(source_head=head, baseline=BASELINE)
        shutil.copytree(source / 'workbench/node_modules', root / 'node_modules', symlinks=False,
                        ignore=shutil.ignore_patterns('.bin', 'win32-*', 'linux-*'))
        (root / 'node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper').chmod(0o755)
        for label, revision in [('baseline', BASELINE), ('candidate', head)]:
            tree = root / label
            archive = subprocess.check_output(['git', 'archive', revision, 'workbench'], cwd=source, env=env)
            extract_baseline(archive, tree)
            for bad in (False, True):
                run_reviewer_case(source, tree, root / (label + ('-bad' if bad else '-good')), revision, env, report, bad)
        baseline, _, candidate, _ = report['cases']
        if baseline['boundary_oracle_passed'] and candidate['boundary_oracle_passed']:
            report.update(status='PASS', classification='old_profile_probe_was_not_the_real_reviewer_sandbox')
        elif baseline['unsafe_write_observed'] and candidate['unsafe_write_observed']:
            report['classification'] = 'preexisting_permission_issue_requires_blocking_report'
        elif baseline['boundary_oracle_passed'] and candidate['unsafe_write_observed']:
            report['classification'] = 'candidate_permission_regression'
        else:
            report['classification'] = 'inconclusive_native_results'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        if all(not row.get('cleanup_errors') and row.get('cleanup') and all(item['status'] == 'exited' for item in row['cleanup']) for row in report['cases']):
            shutil.rmtree(root); report['fixture_removed'] = not root.exists()
        else:
            report['status'] = 'INCOMPLETE'
            report['fixture_retained_reason'] = 'native_cleanup_not_confirmed'
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(status=report['status'], summary=str(args.summary), classification=report.get('classification'))))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
