#!/usr/bin/env python3
"""T-027 contract through the real CLI; isolated runtime, append-only evidence."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--identity-only', action='store_true')
    parser.add_argument('--codex', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, output / 'probe-used.py')
    runtime = Path(tempfile.mkdtemp(prefix='t027-', dir='/tmp'))
    session = 'a2a-t027-' + runtime.name
    removed = [k for k in os.environ if k.startswith(('HERDR_', 'MUSTER_'))]
    env = {k: v for k, v in os.environ.items() if k not in removed}
    env.update(XDG_CONFIG_HOME=str(runtime / 'c'), XDG_STATE_HOME=str(runtime / 's'),
               XDG_CACHE_HOME=str(runtime / 'k'), SHELL='/bin/sh', MUSTER_DISABLE_SOUND='1')
    checks = []
    server = None
    events = (output / 'events.ndjson').open('a', encoding='utf-8')

    def log(event, **fields):
        events.write(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                     event=event, **fields), ensure_ascii=False) + '\n')
        events.flush()

    def command(tail, required=True, cli=None, overrides=None):
        argv = [str(cli or args.binary.resolve()), '--session', session, *tail]
        result = subprocess.run(argv, env=dict(env, **(overrides or {})), capture_output=True,
                                text=True, timeout=45)
        log('command', argv=argv, stdout=result.stdout, stderr=result.stderr,
            returncode=result.returncode)
        if required:
            assert result.returncode == 0, result.stderr or result.stdout
        return result

    def check(name, actual, expected):
        item = dict(check=name, actual=actual, expected=expected, passed=actual == expected)
        checks.append(item)
        log('check', **item)
        assert item['passed'], str(item)

    def api(tail):
        value = json.loads(command(tail).stdout)
        assert 'error' not in value, value
        return value['result']

    def wait_for(fn, timeout=20):
        deadline = time.monotonic() + timeout
        while True:
            value = fn()
            if value:
                return value
            assert time.monotonic() < deadline, 'observation deadline exceeded'
            time.sleep(.2)

    def read(pane):
        return command(['pane', 'read', pane, '--source', 'recent-unwrapped', '--lines', '120']).stdout

    def output_line(pane, marker):
        return marker in [line.strip() for line in read(pane).splitlines()]

    def herdr_snapshot(phase):
        # Read-only observation of the user's existing server and controller.
        state = {}
        for key, tail in [('status', ['status', 'server']),
                          ('controller', ['pane', 'process-info', '--pane', 'wF:pM']),
                          ('sessions', ['session', 'list', '--json'])]:
            result = subprocess.run([shutil.which('herdr'), '--session', 'default', *tail],
                                    env={k: v for k, v in os.environ.items() if k not in removed},
                                    text=True, capture_output=True, timeout=20, check=True)
            state[key] = result.stdout
        (output / ('herdr-' + phase + '.json')).write_text(json.dumps(state, indent=2), encoding='utf-8')
        return state

    status = 'INCOMPLETE'
    before = None
    try:
        log('context', runtime=str(runtime), session=session, binary=str(args.binary.resolve()),
            removed_environment=removed, git_commit=subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
        help_text = command(['--help']).stdout
        check('product-name', help_text.splitlines()[0].startswith(('muster ', 'Muster ')), True)
        check('herdr-name-absent', 'herdr' in help_text.lower(), False)
        check('config-namespace', '/muster/config.toml' in help_text, True)
        if args.identity_only:
            status = 'PASS'
            return
        before = herdr_snapshot('before')
        # Deliberately request online checks: configuration must not enable them.
        config = runtime / 'c/muster/config.toml'
        config.parent.mkdir(parents=True)
        config.write_text('onboarding = false\n[update]\nversion_check = true\nmanifest_check = true\n'
                          '[terminal]\ndefault_shell = "/bin/sh"\n', encoding='utf-8')
        network_bin = runtime / 'bin'
        network_bin.mkdir()
        network_log = output / 'network-attempts.txt'
        network_log.touch()
        for tool in ['curl', 'wget', 'powershell']:
            wrapper = network_bin / tool
            wrapper.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "' + str(network_log) + '"\nexit 97\n')
            wrapper.chmod(0o755)
        env['PATH'] = str(network_bin) + ':' + env['PATH']
        session_dir = runtime / 'c/muster/sessions' / session
        argv = [str(args.binary.resolve()), '--session', session, 'server']
        log('server-start', argv=argv, config=str(config))
        stdio = (output / 'server-stdio.txt').open('w', encoding='utf-8')
        server = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=stdio, stderr=stdio)
        wait_for(lambda: (session_dir / 'muster.sock').exists() or
                 (server.poll() is not None and (_ for _ in ()).throw(AssertionError('server exited'))))
        check('separate-socket', (session_dir / 'muster.sock').exists(), True)
        check('old-socket-absent', bool(list(runtime.rglob('herdr*.sock'))), False)
        project = api(['workspace', 'create', '--label', 't027-project', '--cwd', str(ROOT)])
        workspace = project['workspace']['workspace_id']
        task = api(['tab', 'create', '--workspace', workspace, '--label', 't027-task', '--cwd', str(ROOT)])
        pane = task['root_pane']['pane_id']
        split = api(['pane', 'split', pane, '--direction', 'right', '--cwd', str(ROOT), '--no-focus'])
        shell_pane = split['pane']['pane_id']
        marker = 'T027-SHELL-' + runtime.name
        command(['pane', 'run', shell_pane, "printf '%s\\n' " + marker])
        wait_for(lambda: output_line(shell_pane, marker))
        check('shell-read-write', output_line(shell_pane, marker), True)
        # A delayed command survives after every CLI client has exited.
        background = 'T027-DETACHED-' + runtime.name
        command(['pane', 'run', shell_pane, "sleep 1; printf '%s\\n' " + background])
        time.sleep(1.5)
        check('server-survives-client-exit', server.poll(), None)
        wait_for(lambda: output_line(shell_pane, background))
        check('pane-survives-client-exit', output_line(shell_pane, background), True)
        env_marker = 'T027-ENV-' + runtime.name
        command(['pane', 'run', shell_pane,
                 "python3 -c 'import os; print(\"" + env_marker +
                 "\",os.environ.get(\"MUSTER_ENV\"),any(k.startswith(\"HERDR_\") for k in os.environ))'"])
        wait_for(lambda: output_line(shell_pane, env_marker + ' 1 False'))
        check('pane-environment', output_line(shell_pane, env_marker + ' 1 False'), True)
        for tail in [['update'], ['channel', 'set', 'preview'], ['server', 'update-agent-manifests', '--json']]:
            result = command(tail, required=False)
            check('online-command-rejected:' + ' '.join(tail), result.returncode != 0, True)
        if args.codex:
            # Integration installation is confined to this new Codex home, never ~/.codex.
            codex_dir = runtime / 'codex'
            codex_dir.mkdir()
            original_hooks = Path.home() / '.codex/hooks.json'
            prior_hooks = original_hooks.read_bytes()
            shutil.copyfile(Path.home() / '.codex/auth.json', codex_dir / 'auth.json')
            (codex_dir / 'auth.json').chmod(0o600)
            (codex_dir / 'config.toml').write_text('check_for_update_on_startup = false\n', encoding='utf-8')
            command(['integration', 'install', 'codex'], overrides={'CODEX_HOME': str(codex_dir)})
            hook_data = (codex_dir / 'hooks.json').read_text(encoding='utf-8')
            (output / 'isolated-hooks.json').write_text(hook_data, encoding='utf-8')
            check('muster-hook-installed', 'muster-agent-state.sh' in hook_data, True)
            agent_pane = api(['pane', 'split', pane, '--direction', 'down', '--cwd', str(ROOT),
                              '--env', 'CODEX_HOME=' + str(codex_dir), '--no-focus'])['pane']['pane_id']
            agent_argv = ['agent', 'start', 't027-codex', '--kind', 'codex', '--pane', agent_pane,
                          '--timeout', '30000', '--', '-m', 'gpt-6.1-sol', '-c',
                          'model_reasoning_effort="xhigh"', '-c', 'service_tier="fast"', '-c',
                          'check_for_update_on_startup=false']
            start = command(agent_argv, required=False)
            if start.returncode:
                command(['agent', 'read', 't027-codex', '--lines', '120'], required=False)
                raise AssertionError('Codex not ready; preserve startup UI; do not approve a dialog')
            agent = api(['agent', 'get', 't027-codex'])['agent']
            log('agent-before-prompt', agent=agent)
            session_info = agent.get('agent_session') or {}
            check('native-session-hook-source', session_info.get('source'), 'muster:codex')
            check('native-session-id', bool(session_info.get('value')), True)
            check('idle-before-prompt', agent.get('status') in ['idle', 'done'], True)
            command(['agent', 'prompt', 't027-codex',
                     'Run sleep 4 in the terminal, then reply exactly T027-CODEX-OK. Do not edit files.'])
            working = wait_for(lambda: (api(['agent', 'get', 't027-codex'])['agent'].get('status') == 'working'))
            check('working-observed', working, True)
            wait_for(lambda: api(['agent', 'get', 't027-codex'])['agent'].get('status') in ['idle', 'done'], 120)
            check('completion-output', 'T027-CODEX-OK' in command(['agent', 'read', 't027-codex', '--lines', '120']).stdout, True)
            check('user-hooks-preserved', original_hooks.read_bytes() == prior_hooks, True)
        tcp = subprocess.run(['lsof', '-a', '-p', str(server.pid), '-iTCP', '-nP'],
                             capture_output=True, text=True, timeout=10)
        log('server-network-snapshot', returncode=tcp.returncode, stdout=tcp.stdout, stderr=tcp.stderr)
        check('server-tcp-connections', tcp.stdout.strip(), '')
        check('network-subprocess-attempts', network_log.read_text(), '')
        after = herdr_snapshot('after')
        check('herdr-server-status-unchanged', after['status'], before['status'])
        # Process identity fields are reviewed from saved raw JSON; lifecycle is allowed to advance.
        check('herdr-and-muster-running', 'status: running' in after['status'] and server.poll() is None, True)
        (output / 'shell-read.txt').write_text(read(shell_pane), encoding='utf-8')
        status = 'PASS'
    except Exception:
        log('failure', traceback=traceback.format_exc())
        (output / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if server is not None and server.poll() is None:
            stop = command(['server', 'stop'], required=False)
            if stop.returncode == 0:
                server.wait(timeout=20)
                check('owned-server-stopped', server.returncode, 0)
            else:
                status = 'INCOMPLETE'
                log('cleanup-incomplete', pid=server.pid)
        result = dict(status=status, runtime=str(runtime), session=session, checks=checks)
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        events.close()
    if status != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
