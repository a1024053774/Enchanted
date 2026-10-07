"""Compare server survival after separate tool invocations end."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--binary', type=Path)
    p.add_argument('--start', choices=['attached-group', 'new-session'])
    p.add_argument('--stop', action='store_true')
    args = p.parse_args()
    out = args.output.resolve()
    env = {k: v for k, v in os.environ.items() if not k.startswith(('HERDR_', 'MUSTER_')) and k != 'CODEX_THREAD_ID'}
    if args.start:
        out.mkdir(parents=True, exist_ok=False)
        runtime = Path(tempfile.mkdtemp(prefix='t029-lifetime-', dir='/tmp'))
        context_env = dict(XDG_CONFIG_HOME=str(runtime / 'c'), XDG_STATE_HOME=str(runtime / 's'),
                           XDG_CACHE_HOME=str(runtime / 'k'), SHELL='/bin/sh', MUSTER_DISABLE_SOUND='1')
        env.update(context_env)
        config = runtime / 'c/muster/config.toml'
        config.parent.mkdir(parents=True)
        config.write_text('onboarding = false\n[terminal]\ndefault_shell = "/bin/sh"\n', encoding='utf-8')
        session = 'a2a-' + runtime.name
        argv = [str(args.binary.resolve()), '--session', session, 'server']
        with (out / 'server-stdio.txt').open('x', encoding='utf-8') as stdio:
            server = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=stdio, stderr=stdio,
                                      start_new_session=args.start == 'new-session')
        socket = runtime / 'c/muster/sessions' / session / 'muster.sock'
        deadline = time.monotonic() + 20
        while not socket.exists():
            assert server.poll() is None and time.monotonic() < deadline, 'Server did not start'
            time.sleep(.2)
        status_argv = [str(args.binary.resolve()), '--session', session, 'status', '--json']
        status = subprocess.run(status_argv, env=env, text=True, capture_output=True, timeout=20)
        assert status.returncode == 0, status.stderr
        context = dict(mode=args.start, binary=str(args.binary.resolve()), runtime=str(runtime), session=session,
                       server_argv=argv, server_pid=server.pid, server_pgid=os.getpgid(server.pid),
                       launcher_pid=os.getpid(), launcher_pgid=os.getpgrp(), environment=context_env,
                       status_before_launcher_exit=dict(argv=status_argv, exit_code=status.returncode,
                                                        stdout=status.stdout, stderr=status.stderr))
        (out / 'context.json').write_text(json.dumps(context, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: context[k] for k in ('mode', 'server_pid', 'server_pgid', 'launcher_pid', 'launcher_pgid')}), flush=True)
        return 0
    context = json.loads((out / 'context.json').read_text(encoding='utf-8'))
    env.update(context['environment'])
    argv = [context['binary'], '--session', context['session'], 'server', 'stop'] if args.stop else [
        context['binary'], '--session', context['session'], 'status', '--json']
    result = subprocess.run(argv, env=env, text=True, capture_output=True, timeout=20)
    ps = subprocess.run(['ps', '-p', str(context['server_pid']), '-o', 'pid=,ppid=,pgid=,stat=,lstart=,command='], text=True, capture_output=True)
    log = Path(context['runtime']) / 'c/muster/sessions' / context['session'] / 'muster-server.log'
    record = dict(argv=argv, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
                  ps_exit=ps.returncode, ps_stdout=ps.stdout, server_log=log.read_text(encoding='utf-8') if log.exists() else '')
    label = 'stop' if args.stop else 'inspection-' + str(time.time_ns())
    (out / (label + '.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
