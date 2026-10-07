#!/usr/bin/env python3
"""T-027 contract through the real CLI; isolated runtime, append-only evidence."""
import argparse
import datetime
import json
import importlib.util
from types import SimpleNamespace
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
    removed = [k for k in os.environ if k.startswith(('HERDR_', 'MUSTER_')) or k == 'CODEX_THREAD_ID']
    env = {k: v for k, v in os.environ.items() if k not in removed}
    env.update(XDG_CONFIG_HOME=str(runtime / 'c'), XDG_STATE_HOME=str(runtime / 's'),
               XDG_CACHE_HOME=str(runtime / 'k'), SHELL='/bin/sh', MUSTER_DISABLE_SOUND='1')
    checks = []
    server = None
    client = None
    codex_dir = None
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
        default = next(item for item in json.loads(state['sessions'])['sessions'] if item['default'])
        pids = subprocess.check_output(['lsof', '-t', default['socket_path']], text=True).split()
        state['server_identity'] = subprocess.check_output(
            ['ps', '-p', ','.join(pids), '-o', 'pid=,lstart=,comm='], text=True).strip()
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
        # A real generation-1 endpoint client negotiates, receives frames, then detaches.
        helper = ROOT / 'evidence/2026-10-06-m1-batch1/T-024/probe.py'
        shutil.copyfile(helper, output / 'endpoint-helper.py')
        spec = importlib.util.spec_from_file_location('t027_endpoint', output / 'endpoint-helper.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        endpoint_probe = SimpleNamespace(log=log, check=check,
            client_socket=session_dir / 'muster-client.sock', clients=[])
        client = module.Client(endpoint_probe, 't027-endpoint', 120, 40)
        background = 'T027-DETACHED-' + runtime.name
        command(['pane', 'run', shell_pane, "sleep 1; printf '%s\\n' " + background])
        client.close()
        client = None
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
            shutil.copyfile(Path.home() / '.codex/config.toml', codex_dir / 'config.toml')
            readonly_hooks = runtime / 'user-hooks-readonly.json'
            shutil.copyfile(original_hooks, readonly_hooks)
            readonly_hooks.chmod(0o444)
            command(['integration', 'install', 'codex'], overrides={'CODEX_HOME': str(codex_dir)})
            hook_data = (codex_dir / 'hooks.json').read_text(encoding='utf-8')
            (output / 'isolated-hooks.json').write_text(hook_data, encoding='utf-8')
            check('muster-hook-installed', 'muster-agent-state.sh' in hook_data, True)
            old_commands = [h['command'] for entries in json.loads(prior_hooks)['hooks'].values()
                            for entry in entries for h in entry.get('hooks', []) if 'command' in h]
            new_commands = [h['command'] for entries in json.loads(hook_data)['hooks'].values()
                            for entry in entries for h in entry.get('hooks', []) if 'command' in h]
            check('only-four-muster-hooks', len(new_commands) == 4 and all('muster-agent-state.sh' in c for c in new_commands), True)
            check('readonly-herdr-hook-copy', readonly_hooks.read_bytes() == prior_hooks, True)
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
            # User/controller grant applies only to this next fresh home and exactly four hooks.
            grant = ROOT / 'evidence/2026-10-06-m1-batch2/T-027/approval-granted.md'
            assert grant.is_file(), 'explicit hook approval is required'
            def approved_hook_dialog():
                text = command(['agent', 'read', 't027-codex', '--lines', '120']).stdout
                if 'Hooks need review' not in text:
                    return False
                assert '4 hooks are new or changed.' in text, 'unexpected trust scope; do not approve'
                return text
            dialog = wait_for(approved_hook_dialog, 20)
            (output / 'approved-hook-dialog.txt').write_text(dialog, encoding='utf-8')
            log('explicit-approval', source=str(grant), action='trust exactly four Muster hooks in this isolated home')
            command(['agent', 'send-keys', 't027-codex', '2', 'enter'])
            wait_for(lambda: 'Hooks need review' not in command(['agent', 'read', 't027-codex', '--lines', '120']).stdout)
            agent = api(['agent', 'get', 't027-codex'])['agent']
            log('agent-before-prompt', agent=agent)
            check('idle-before-prompt', agent.get('agent_status') in ['idle', 'done'], True)
            command(['agent', 'prompt', 't027-codex',
                     'Run sleep 4 in the terminal, then reply exactly T027-CODEX-OK. Do not edit files.'])
            working = wait_for(lambda: (api(['agent', 'get', 't027-codex'])['agent'].get('agent_status') == 'working'))
            check('working-observed', working, True)
            wait_for(lambda: api(['agent', 'get', 't027-codex'])['agent'].get('agent_status') in ['idle', 'done'], 120)
            final_agent = api(['agent', 'get', 't027-codex'])['agent']
            session_info = final_agent.get('agent_session') or {}
            check('native-session-hook-source', session_info.get('source'), 'muster:codex')
            check('native-session-id', bool(session_info.get('value')), True)
            log('agent-after-prompt', agent=final_agent)
            check('completion-output', 'T027-CODEX-OK' in command(['agent', 'read', 't027-codex', '--lines', '120']).stdout, True)
            check('user-hooks-preserved', original_hooks.read_bytes() == prior_hooks, True)
        tcp = subprocess.run(['lsof', '-a', '-p', str(server.pid), '-iTCP', '-nP'],
                             capture_output=True, text=True, timeout=10)
        log('server-network-snapshot', returncode=tcp.returncode, stdout=tcp.stdout, stderr=tcp.stderr)
        check('server-tcp-connections', tcp.stdout.strip(), '')
        check('network-subprocess-attempts', network_log.read_text(), '')
        after = herdr_snapshot('after')
        check('herdr-server-status-unchanged', after['status'], before['status'])
        check('herdr-server-identity-unchanged', after['server_identity'], before['server_identity'])
        old_info = json.loads(before['controller'])['result']['process_info']
        new_info = json.loads(after['controller'])['result']['process_info']
        for field in ['shell_pid', 'foreground_process_group_id']:
            check('controller-' + field + '-unchanged', new_info[field], old_info[field])
        # Process identity fields are reviewed from saved raw JSON; lifecycle is allowed to advance.
        check('herdr-and-muster-running', 'status: running' in after['status'] and server.poll() is None, True)
        (output / 'shell-read.txt').write_text(read(shell_pane), encoding='utf-8')
        status = 'PASS'
    except Exception:
        log('failure', traceback=traceback.format_exc())
        if server is not None and server.poll() is None:
            command(['agent', 'read', 't027-codex', '--lines', '120'], required=False)
        (output / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if client is not None:
            client.close()
        if server is not None and server.poll() is None:
            stop = command(['server', 'stop'], required=False)
            if stop.returncode == 0:
                server.wait(timeout=20)
                check('owned-server-stopped', server.returncode, 0)
            else:
                status = 'INCOMPLETE'
                log('cleanup-incomplete', pid=server.pid)
        for base in ['c', 's', 'k']:
            for source in (runtime / base).rglob('*'):
                if source.is_file() and not source.is_symlink():
                    target = output / 'runtime' / source.relative_to(runtime)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
        if codex_dir is not None and codex_dir.exists():
            assert codex_dir.parent == runtime and runtime.name.startswith('t027-')
            shutil.rmtree(codex_dir)
            log('isolated-codex-home-deleted', command='python3 shutil.rmtree(' + repr(str(codex_dir)) + ')', absent=not codex_dir.exists())
            check('isolated-codex-home-deleted', codex_dir.exists(), False)
        result = dict(status=status, runtime=str(runtime), session=session, checks=checks)
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        events.close()
    if status != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
