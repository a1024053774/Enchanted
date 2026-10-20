"""Protocol preflight only, not native sandbox evidence.

Failures: missing argument/input deltas, wrong command/cwd/namespace, and an
unadvertised tool substituted for the CLI's tool. Uses independent sentinel input.
"""
import argparse
import json
from pathlib import Path
from diagnose_t112_reviewer import shell_item, tool_events, assert_native_call


def check(events=tool_events):
    command = '/usr/bin/printf "T112 sentinel with spaces"'
    cwd = Path('/private/tmp/t112 independent workspace')
    tools = [
        [{'type': 'namespace', 'name': 'functions', 'tools': [{'type': 'function', 'name': 'exec_command', 'parameters': {}}]}],
        [{'type': 'custom', 'name': 'exec', 'format': {'type': 'text'}}],
        [{'type': 'function', 'name': 'shell_command', 'parameters': {}}],
    ]
    for advertised in tools:
        item = shell_item(advertised, command, cwd)
        stream = events(item, 'gpt-6.1-sol')
        assert stream[0][0] == 'response.created' and stream[-1][0] == 'response.completed'
        assert stream[-2][0] == 'response.output_item.done'
        payload = ''.join(value['delta'] for event, value in stream if event.endswith('.delta'))
        assert payload, 'Native stream consumer needs a tool argument/input delta'
        completed = stream[-1][1]['response']['output'][0]
        assert completed['call_id'] == item['call_id']
        assert_native_call(item, [completed])
        changed = dict(completed)
        if item['type'] == 'function_call':
            changed['arguments'] = json.dumps({'cmd': 'ignored command', 'workdir': '/wrong'})
        else:
            changed['input'] = 'text("ignored command");'
        try:
            assert_native_call(item, [changed])
        except AssertionError:
            pass
        else:
            raise AssertionError('Matching call_id with changed command must fail')
        if advertised[0]['type'] == 'namespace':
            assert completed['namespace'] == 'functions' and completed['name'] == 'exec_command'
        if item['type'] == 'function_call':
            args = json.loads(payload)
            assert args['cmd' if item['name'] == 'exec_command' else 'command'] == command
            assert args['workdir'] == str(cwd)
            assert completed['arguments'] == payload
        else:
            # Inspect the actual tool arguments passed to exec_command, not a
            # string-presence check on the generated function body.
            assert payload.startswith('text(await tools.exec_command(') and payload.endswith('));')
            args = json.loads(payload[len('text(await tools.exec_command('):-3])
            assert args['cmd'] == command and args['workdir'] == str(cwd)
            assert completed['input'] == payload
    try:
        shell_item([{'type': 'function', 'name': 'unknown'}], command, cwd)
    except AssertionError:
        pass
    else:
        raise AssertionError('Unsupported tool must not be substituted')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    assert not args.summary.exists()
    report = dict(status='INCOMPLETE', model_calls=0, scope='protocol preflight; no native CLI or sandbox')
    try:
        check()
        def no_deltas(item, model):
            return [(event, value) for event, value in tool_events(item, model) if not event.endswith('.delta')]
        try:
            check(no_deltas)
        except AssertionError as error:
            assert str(error) == 'Native stream consumer needs a tool argument/input delta'
            report['known_bad_rejected'] = str(error)
        else:
            raise AssertionError('Missing-delta mutant must fail')
        report.update(status='PASS', checks=['namespaced_function_arguments', 'custom_exec_arguments', 'shell_command_arguments', 'unsupported_tool_refused', 'missing_delta_mutant_rejected', 'matching_call_id_changed_command_rejected'])
    except Exception as error:
        report['error'] = str(error)
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
