"""Own one named Muster server; run acceptance from its shell pane."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--red', action='store_true')
    p.add_argument('--checks', action='store_true')
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    runtime = Path(tempfile.mkdtemp(prefix='t029-', dir='/tmp'))
    session = 'a2a-' + runtime.name
    removed = [k for k in os.environ if k.startswith(('HERDR_', 'MUSTER_')) or k in ('CODEX_THREAD_ID', 'CODEX_HOME')]
    env = {k: v for k, v in os.environ.items() if k not in removed}
    env.update(XDG_CONFIG_HOME=str(runtime / 'c'), XDG_STATE_HOME=str(runtime / 's'),
               XDG_CACHE_HOME=str(runtime / 'k'), SHELL='/bin/sh', MUSTER_DISABLE_SOUND='1')
    home_files = [Path.home() / '.codex' / name for name in ('config.toml', 'hooks.json', 'herdr-agent-state.sh')]
    home_before = {str(path): path.read_bytes() if path.exists() else None for path in home_files}
    config = runtime / 'c/muster/config.toml'
    config.parent.mkdir(parents=True)
    config.write_text('onboarding = false\n[terminal]\ndefault_shell = "/bin/sh"\n', encoding='utf-8')
    events = (out / 'commands.jsonl').open('a', encoding='utf-8')

    def command(argv, required=True):
        argv = [str(v) for v in argv]
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        process = subprocess.run(argv, env=env, cwd=ROOT, text=True, capture_output=True, timeout=45)
        events.write(json.dumps(dict(argv=argv, started=started, exit_code=process.returncode,
                                    stdout=process.stdout, stderr=process.stderr), ensure_ascii=False) + '\n')
        events.flush()
        if required:
            assert process.returncode == 0, process.stderr or process.stdout
        return process.stdout

    def muster(*argv):
        return json.loads(command([args.binary.resolve(), '--session', session, *argv]))['result']

    start = [str(args.binary.resolve()), '--session', session, 'server']
    stdio = (out / 'server-stdio.txt').open('w', encoding='utf-8')
    server = subprocess.Popen(start, env=env, stdin=subprocess.DEVNULL, stdout=stdio, stderr=stdio)
    socket = runtime / 'c/muster/sessions' / session / 'muster.sock'
    deadline = time.monotonic() + 20
    while not socket.exists():
        assert server.poll() is None and time.monotonic() < deadline, 'Owned server did not start'
        time.sleep(.2)
    project = muster('workspace', 'create', '--cwd', str(ROOT), '--label', 'T-029 acceptance',
                     '--env', 'MUSTER_BIN=' + str(args.binary.resolve()), '--no-focus')
    pane = project['root_pane']['pane_id']
    context = dict(binary=str(args.binary.resolve()), session=session, server_pid=server.pid,
                   server_argv=start, runtime=str(runtime), environment=env,
                   parent_pane=pane, workspace=project, removed_environment=removed,
                   code_revision=command(['git', 'rev-parse', 'HEAD']).strip(),
                   codex_home=str(Path.home() / '.codex'), version=command([args.binary.resolve(), '--version']))
    # Never persist the full inherited environment (credentials may be present).
    context['environment'] = {k: env[k] for k in ('XDG_CONFIG_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME', 'SHELL', 'MUSTER_DISABLE_SOUND')}
    (out / 'context.json').write_text(json.dumps(context, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    command([args.binary.resolve(), '--session', session, 'status', '--json'])
    if args.checks:
        jobs = [(ROOT / 'evidence/2026-10-07-m1-batch3/T-029/run_checks.py', out / 'suites', [])]
        mutant = out / 'coop-ignore-fence.py'
        code = (ROOT / 'coop.py').read_text(encoding='utf-8')
        line = '            require(attempt["fence"] == args.fence, "stale_fence")\n'
        assert code.count(line) == 1
        mutant.write_text(code.replace(line, '', 1), encoding='utf-8')
        for label, script in [('fence-correct', ROOT / 'coop.py'), ('fence-mutant', mutant)]:
            jobs.append((ROOT / 'evidence/2026-10-07-m1-batch3/T-029/check_fence.py', out / label,
                         ['--coop', str(script)]))
        for script, destination, extra in jobs:
            argv = [sys.executable, '-B', str(script), '--output', str(destination), *extra]
            shell = shlex.join(argv) + ' > ' + shlex.quote(str(out / (destination.name + '.log'))) + ' 2>&1'
            command([args.binary.resolve(), '--session', session, 'pane', 'run', pane, shell])
            deadline = time.monotonic() + 300
            while not (destination / 'result.json').exists():
                assert time.monotonic() < deadline, 'Check has no saved result: ' + str(destination)
                time.sleep(2)
            status = json.loads((destination / 'result.json').read_text(encoding='utf-8'))['status']
            assert status == ('INCOMPLETE' if destination.name == 'fence-mutant' else 'PASS'), str(destination)
    fixture = runtime / 'fixture'
    fixture.mkdir()
    for name in ('pager.py', 'CONTRACT.md'):
        shutil.copyfile(ROOT / 'fixtures/pagination' / name, fixture / name)
    for tail in [('init', '-b', 'main'), ('config', 'user.name', 'T-029 isolated fixture'),
                 ('config', 'user.email', 'fixture@localhost'), ('config', 'commit.gpgsign', 'false'),
                 ('add', 'pager.py', 'CONTRACT.md'), ('commit', '-m', 'test: incomplete pagination task')]:
        command(['git', '-C', fixture, *tail])
    modes = ['live_herdr.py', 'live_run.py'] if args.red else ['live_run.py']
    results = []
    paused = False
    for name in modes:
        source = (subprocess.check_output(['git', 'show', '50d93d341421928508e5a8f14cebc95601adfd04:acceptance/' + name], cwd=ROOT, text=True)
                  if args.red else (ROOT / 'acceptance' / name).read_text(encoding='utf-8'))
        if args.red:
            source = source.replace('import argparse', 'import argparse\nimport os', 1)
            source = source.replace('root = Path(__file__).resolve().parents[1]', 'root = Path(' + repr(str(ROOT)) + ')', 1)
            source = source.replace("['herdr',", "[os.environ['MUSTER_BIN'],")
            script = out / ('red-' + name)
            script.write_text(source, encoding='utf-8')
        else:
            script = ROOT / 'acceptance' / name
        label = out.name + '-' + name[:-3]
        live_out = out / label
        argv = [sys.executable, '-B', str(script), '--parent-pane', pane,
                '--fixture-repo', str(fixture), '--output', str(live_out)]
        if name == 'live_run.py':
            argv += ['--wait-seconds', '600']
        shell = shlex.join(argv) + ' > ' + shlex.quote(str(out / (name + '.stdout'))) + ' 2> ' + shlex.quote(str(out / (name + '.stderr')))
        command([args.binary.resolve(), '--session', session, 'pane', 'run', pane, shell])
        deadline = time.monotonic() + (60 if args.red else 850)
        while not (live_out / 'result.json').exists():
            assert time.monotonic() < deadline, 'Real acceptance has no result by deadline'
            time.sleep(2)
        result = json.loads((live_out / 'result.json').read_text(encoding='utf-8'))
        results.append(result)
        if not args.red and result['status'] != 'PASS':
            paused = True
            break
    panes = muster('pane', 'list')
    for item in panes['panes']:
        text = command([args.binary.resolve(), '--session', session, 'pane', 'read', item['pane_id'],
                        '--source', 'recent-unwrapped', '--lines', '160'], required=False)
        (out / (item['pane_id'].replace(':', '-') + '.txt')).write_text(text, encoding='utf-8')
    (out / 'panes-final.json').write_text(json.dumps(panes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not paused:
        command([args.binary.resolve(), '--session', session, 'server', 'stop'])
        server.wait(timeout=20)
    final = dict(status='INCOMPLETE' if args.red else 'BLOCKED' if paused else 'PASS',
                 results=results, paused=paused, context=str(out / 'context.json'),
                 server_stopped=server.poll() is not None)
    final['user_configuration_unchanged'] = {str(path): home_before[str(path)] == (path.read_bytes() if path.exists() else None)
                                              for path in home_files}
    assert all(final['user_configuration_unchanged'].values()), 'User configuration changed; preserve and ask controller'
    # Archive only isolated runtime/state; the normal Codex home is never copied.
    with tarfile.open(out / 'runtime-artifacts.tar.gz', 'w:gz') as archive:
        archive.add(runtime, arcname=runtime.name)
        for item in results:
            state = Path(item['state']) if 'state' in item else Path(item['runtime']) / 'state'
            archive.add(state.parent, arcname='managed-' + state.parent.name)
        for label in ('fence-correct', 'fence-mutant'):
            fence_result = out / label / 'result.json'
            if fence_result.exists():
                retained = Path(json.loads(fence_result.read_text(encoding='utf-8'))['runtime'])
                archive.add(retained, arcname=retained.name)
    (out / 'result.json').write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(final, ensure_ascii=False), flush=True)
    return 0 if final['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
