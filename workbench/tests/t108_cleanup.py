"""Identity-bound cleanup for T-108's own temporary native CLI fixtures (Python 3.9)."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def observe(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,ppid=,pgid=,lstart=,stat=,command='],
                            env={**os.environ, 'LC_ALL': 'C'}, capture_output=True, text=True, check=False)
    if result.returncode == 1 and not result.stdout.strip():
        return None
    if result.returncode != 0:
        raise RuntimeError('Cannot inspect process identity: ' + result.stderr)
    fields = result.stdout.strip().split(None, 9)
    if len(fields) != 10 or int(fields[0]) != pid:
        raise RuntimeError('Invalid process observation: ' + result.stdout)
    return {'pid': pid, 'ppid': int(fields[1]), 'pgid': int(fields[2]),
            'started': ' '.join(fields[3:8]), 'stat': fields[8], 'command': fields[9]}


def stop_owned(owner):
    signals, exit_states = [], []
    def current():
        found = observe(owner['pid'])
        if found is None:
            return None
        for key in ['pid', 'pgid', 'started']:
            if found[key] != owner[key]:
                raise RuntimeError('Process identity changed; refuse signal: ' + json.dumps(found))
        # macOS can replace command text while the same process is exiting.
        # E is an additional flag (e.g. ?E); Z is the zombie state. Wait only.
        if any(flag in found['stat'] for flag in ('E', 'Z')):
            if found['stat'] not in exit_states:
                exit_states.append(found['stat'])
        elif found['command'] != owner['command']:
            # Claude can set its process title to just "(version)" while still
            # running, including after its parent exits. The three identity
            # fields above must match before this title change is considered.
            executable = Path(owner['command'].split(None, 1)[0])
            claude_title = re.fullmatch(r'\([0-9]+\.[0-9]+\.[0-9]+\)', found['command'])
            claude_owner = executable.name == 'claude' or (
                executable.parent.name == 'versions' and executable.parent.parent.name == 'claude'
                and found['command'] == '(' + executable.name + ')')
            if not (claude_owner and claude_title):
                raise RuntimeError('Process identity changed; refuse signal: ' + json.dumps(found))
        return found
    for sig in [signal.SIGTERM, signal.SIGKILL]:
        found = current()
        if found is None:
            return {'pid': owner['pid'], 'status': 'exited', 'signals': signals, 'exit_states': exit_states}
        if not any(flag in found['stat'] for flag in ('E', 'Z')):
            os.kill(owner['pid'], sig)  # Exact verified PID; never a shared process group.
            signals.append(sig.name)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if current() is None:
                return {'pid': owner['pid'], 'status': 'exited', 'signals': signals, 'exit_states': exit_states}
            time.sleep(.05)
    raise RuntimeError('Verified test process remains alive: ' + str(owner['pid']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True, type=Path)
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve previous results; supply a fresh summary path'
    root = Path('/private/tmp/t078-2-t108-a9ttufj7')
    manifest = json.loads((root/'manifest.json').read_text())
    assert manifest['root'] == str(root) and manifest['state'] == str(root/'state')
    assert manifest['session'] == '5e7c563d-f285-4c6e-b295-0fd148f71ac8'
    report = {'status': 'INCOMPLETE', 'fixture': str(root), 'model_calls': 0, 'vendor_calls': 0, 'processes': []}
    try:
        for pid, kind in [(32252, 'native'), (32190, 'daemon')]:
            owner = observe(pid)
            if owner is None or owner['stat'].startswith('Z'):
                report['processes'].append({'pid': pid, 'status': 'already_exited'})
                continue
            command = owner['command']
            if kind == 'native':
                assert command.startswith(('claude ', '/Users/luckye/.local/share/claude/versions/2.1.304 ')), command
                assert '--session-id '+manifest['session'] in command, command
                assert '--debug-file '+str(root/'roles/ideation/claude-debug.log') in command, command
            else:
                assert '/Users/luckye/Documents/Code/a2a-wt-t108/workbench/src/daemon.ts '+str(root/'state') in command, command
            report['processes'].append({'identity': owner, 'result': stop_owned(owner)})
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = str(error)
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'summary': str(args.summary)}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
