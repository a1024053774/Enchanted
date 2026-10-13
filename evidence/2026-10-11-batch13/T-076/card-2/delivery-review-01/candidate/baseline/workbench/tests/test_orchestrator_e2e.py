#!/usr/bin/env python3
"""Exercise the public daemon CLI; preserve each command and independent readback."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    state = Path(tempfile.mkdtemp(prefix='a2a-t0753-host-', dir='/tmp')) / 'state'
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_'))}
    commands = []

    def run(argv):
        p = subprocess.run([str(x) for x in argv], env=env, capture_output=True, text=True, timeout=30)
        commands.append(dict(argv=[str(x) for x in argv], exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr))
        (args.output / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return p

    cli = ['node', args.source.resolve() / 'workbench/src/gates/cli.ts', '--state', state]
    started = False
    try:
        # This contract comes from card 3: a command outlives its launcher, then
        # another process can query the same daemon and its operating-system ID.
        p = run([*cli, 'daemon_start'])
        assert p.returncode == 0, ('daemon_start must exist and succeed', commands[-1])
        start = json.loads(p.stdout)
        assert start['ok'] is True
        started = True
        p = run([*cli, 'daemon_status'])
        assert p.returncode == 0, commands[-1]
        current = json.loads(p.stdout)
        assert current['pid'] == start['pid']
        p = run(['/bin/ps', '-o', 'pid=,ppid=,pgid=,sess=', '-p', str(start['pid'])])
        assert p.returncode == 0 and p.stdout.strip(), commands[-1]
        fields = p.stdout.split()
        assert int(fields[0]) == start['pid']
        assert int(fields[2]) == start['pid'], 'detached daemon must lead its process group'
        process_ids = {'daemon_pid': start['pid'], 'daemon_pgid': os.getpgid(start['pid']),
                       'daemon_sid': os.getsid(start['pid']), 'checker_pid': os.getpid(),
                       'checker_pgid': os.getpgrp(), 'checker_sid': os.getsid(0)}
        (args.output / 'process-readback.json').write_text(json.dumps(process_ids, indent=2) + '\n', encoding='utf-8')
        assert process_ids['daemon_sid'] == start['pid'], 'detached daemon must lead its session'
        assert process_ids['daemon_sid'] != process_ids['checker_sid']
        assert process_ids['daemon_pgid'] != process_ids['checker_pgid']
        (args.output / 'verdict.json').write_text(json.dumps({'status': 'PASS', 'state': str(state), 'pid': start['pid']}) + '\n', encoding='utf-8')
    except (AssertionError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        (args.output / 'verdict.json').write_text(json.dumps({'status': 'INCOMPLETE', 'state': str(state), 'failure': str(exc)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        raise
    finally:
        if started:
            stop = run([*cli, 'daemon_stop'])
            assert stop.returncode == 0, commands[-1]


if __name__ == '__main__':
    main()
