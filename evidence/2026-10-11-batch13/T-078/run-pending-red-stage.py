"""Reproduce the current missing-controller contract failure without Claude/API/model."""
import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    entry = SOURCE / 'workbench/tests/test_t078_a13_rehearsal.ts'
    assert entry.is_file() and out.parent.is_dir() and not out.exists()
    command = [shutil.which('node'), str(entry), str(out), '--recipient-offline']
    env = {key: value for key, value in os.environ.items() if not key.startswith('A2A_')}
    started = time.monotonic()
    response = subprocess.run(command, cwd=SOURCE, env=env, capture_output=True, text=True, timeout=40)
    raw = json.loads((out / 'result.json').read_bytes())
    observed = json.loads((out / 'offline-observed.json').read_bytes())['observed']
    expected = {'entry_count': 1, 'sender': 'ideation', 'delivery': 'undelivered',
                'reason': 'role_session_missing', 'relay_ok': False,
                'relay_error': 'wake_undelivered', 'feedback_count': 1}
    reproduced = (response.returncode == 1 and raw['status'] == 'INCOMPLETE'
                  and raw['scratch_removed'] is True and observed == expected)
    result = {'status': 'PASS' if reproduced else 'INCOMPLETE', 'product_contract': 'INCOMPLETE',
              'expected_red': True, 'observed': observed, 'expected_old_behavior': expected,
              'command': command, 'exit_code': response.returncode,
              'elapsed_seconds': round(time.monotonic() - started, 3),
              'stdout': response.stdout, 'stderr': response.stderr,
              'scratch_removed': raw['scratch_removed'],
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
              'scope': 'real daemon/relay/inbox/Stop; native process and PTY spies; no Claude/API/model'}
    (out / 'red-verdict.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if reproduced else 1


if __name__ == '__main__':
    raise SystemExit(main())
