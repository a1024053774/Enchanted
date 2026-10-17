"""Pure checks for run limits: refuse excess RPCs before writing, reserve close.

Failure cases: ignored count limits; a refused call still sends bytes; exhausted
observation budget prevents normal cleanup. No process, ps, socket or GUI starts.
The answer is supplied here: two probe requests may pass, the third must not send.
"""
import io
import json
from pathlib import Path
import subprocess
import sys


def exercise(source, name):
    scope = {'__name__': 'budget_probe'}
    if name == 'Observer':
        # Load the actual class without importing the controller's OS helpers.
        start = source.index('class Observer:')
        end = source.index('\ndef main():', start)
        exec('import json\n' + source[start:end], scope)
    else:
        exec(compile(source, 'electron_client.py', 'exec'), scope)
    client = scope[name].__new__(scope[name])
    client.max_calls = 2
    client.number = client.sequence = client.calls = 0
    client.max_stdout_bytes = 1024
    client.stdout = io.BytesIO()
    client.process = type('Child', (), {'stdin': io.BytesIO()})()
    client.record = lambda value: None
    client.receive = lambda *args: {'id': max(client.number, client.sequence), 'ok': True, 'value': {}}
    client.call('inspect')
    client.call('inspect-all')
    sent = client.process.stdin.getvalue()
    refused = False
    try:
        client.call('inspect')
    except RuntimeError:
        refused = True
    assert refused and client.process.stdin.getvalue() == sent, 'Excess RPC must be refused before writing'
    client.number = client.calls = 0
    client.stdout.write(b'x' * 1024)
    refused = False
    try:
        client.call('inspect')
    except RuntimeError:
        refused = True
    assert refused and client.process.stdin.getvalue() == sent, 'Stdout threshold must stop the next probe'
    # A close request is not another screen read and must remain available.
    if name == 'ElectronClient':
        client.call('close')
        assert json.loads(client.process.stdin.getvalue().splitlines()[-1])['command'] == 'close'
    return name


root = Path(__file__).resolve().parents[2]
report = {'status': 'INCOMPLETE', 'argv': sys.argv, 'checks': [], 'known_bad': []}
try:
    for path, name in [('evidence/2026-10-16-batch16/T-091/run_red.py', 'Observer'),
                       ('workbench/tests/electron_client.py', 'ElectronClient')]:
        old = subprocess.check_output(['git', 'show', '3ac3edc92afdd40f31926b94d83fdba4c8c5bf65:' + path], text=True)
        try:
            exercise(old, name)
        except AssertionError as error:
            report['known_bad'].append({'class': name, 'rejected': str(error) == 'Excess RPC must be refused before writing'})
        assert report['known_bad'] and report['known_bad'][-1]['class'] == name and report['known_bad'][-1]['rejected']
        report['checks'].append(exercise((root / path).read_text(encoding='utf-8'), name))
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = repr(error)
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    json.dump(report, output, ensure_ascii=False, indent=2)
    output.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
