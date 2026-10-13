#!/usr/bin/env python3
"""B contract at the real CLI: queue explicit requests without a daemon/socket."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
root = Path(__file__).resolve().parents[2]
fixture = Path(tempfile.mkdtemp(prefix='a2a-relay-cli-', dir='/tmp'))
requests = fixture / 'requests'; requests.mkdir()
env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_'))}
env.update(A2A_TASK='fixture', A2A_ATTEMPT='attempt', A2A_SESSION='session', A2A_ROLE='worker',
           A2A_LAUNCH='launch', A2A_CAPABILITY='fixture-capability', A2A_FENCE='1', A2A_SPEC_REV='1',
           A2A_REQUEST_DIR=str(requests), A2A_STATE=str(fixture / 'no-daemon'))
commands = []
failures = []
for command, extra in [('submit', ['--attempt', 'attempt', '--session', 'session', '--fence', '1', '--spec-rev', '1', '--commit', 'a' * 40]),
                       ('status', []), ('issue', ['--title', '夹具问题', '--body', '验证异步问题转交', '--blocking', 'false'])]:
    argv = ['node', str(root / 'workbench/src/gates/cli.ts'), command, '--task', 'fixture', '--request-id', command + '-fixture', *extra]
    p = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=10)
    commands.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    try:
        assert p.returncode == 0, 'request writer must not require a daemon connection'
        reply = json.loads(p.stdout)
        assert reply['queued'] is True and reply['delivered'] is False
        request = json.loads((requests / (command + '-fixture.json')).read_text(encoding='utf-8'))
        for key, expected in {'task': 'fixture', 'attempt': 'attempt', 'session': 'session', 'fence': 1, 'spec_rev': 1, 'command': command}.items():
            assert request[key] == expected, key
        if command == 'submit': assert request['commit'] == 'a' * 40
    except (AssertionError, OSError, ValueError, KeyError) as error:
        failures.append({'command': command, 'error': str(error)})
record = {'status': 'PASS' if not failures else 'INCOMPLETE', 'fixture': str(fixture), 'commands': commands, 'failures': failures}
(args.output / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': record['status'], 'failures': failures}, ensure_ascii=False))
raise SystemExit(1 if failures else 0)
