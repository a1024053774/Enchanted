import json
from pathlib import Path
import subprocess
from uuid import uuid4

root = Path(__file__).resolve().parent
script = '/Users/luckye/Documents/Code/a2a-wt-t093/evidence/2026-10-16-batch16/T-093/T093-OS-16.sh'
nonce = str(uuid4())
repo = '/review/repo with spaces'
candidate = '8771ba58d71a3fc025b09e32c45096b39858572e'
output = '/private/tmp/review output ' + nonce + '.json'
inputs = ['/private/tmp/' + nonce + ' receipt ' + str(i) + '.json' for i in range(6)]
shell = 'exec() { printf "%s\\0" "$@"; }; script=$1; shift; . "$script" "$@"'
checks = []
for mode, flag in [('verify-six', []), ('verify-rehearsal', ['--rehearsal']), ('verify-counts', ['--counts-only'])]:
    run = subprocess.run(['/bin/bash', '-c', shell, 'independent-wrapper', script, mode, repo, candidate, output, *inputs], capture_output=True, timeout=5)
    actual = [part.decode() for part in run.stdout.split(b'\0') if part]
    expected = ['/usr/bin/python3', '-I', '-S', '-B', repo + '/workbench/tests/check_t093_chain_results.py', '--candidate', candidate, *flag, '--output', output, *inputs]
    checks.append({'case': mode, 'passed': run.returncode == 0 and actual == expected,
                   'rc': run.returncode, 'stderr': run.stderr.decode(), 'actual': actual, 'expected': expected})
report = {'status': 'PASS' if all(row['passed'] for row in checks) else 'FAIL',
          'scope': 'actual Bash wrapper; six fresh sentinel receipt names preserved; exec never delegates', 'checks': checks}
with (root / 'wrapper-sentinel.json').open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2); stream.write('\n')
print(json.dumps({'status': report['status'], 'checks': len(checks)}))
raise SystemExit(0 if report['status'] == 'PASS' else 2)
