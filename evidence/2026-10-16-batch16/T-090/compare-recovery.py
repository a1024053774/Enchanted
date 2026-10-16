"""串行采集历史版本的原恢复用例或完整编排组；不是产品通过判定。"""
import argparse
import ast
import collections
import datetime
import difflib
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ARCHIVE_ROOT = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090')
VERSIONS = [('pre-T082', '150ef6516f6ef5aaa6855631b770ce262991ffbf'),
            ('main-before-T082', '271ac55d82d0e20067e03e2fa4a990e55ef7b434'),
            ('main-T082', '0e6c2b833f6da64243f71d670ea45bb9116fda4d'),
            ('T090', 'a74adeddc5494474472560a150f5ac33ab4a502e')]
CASES = ['test_after_CAS_deleted_ref_requires_reconciliation',
         'test_after_CAS_external_X_requires_reconciliation']
RUNNER = 'workbench/tests/run_s3_rebased_regression.py'
PROTECTED = ['workbench/src', 'acceptance', 'fixtures', 'scripts']


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def inventory(path):
    paths = list(path.rglob('*'))
    return {'files': sum(p.is_file() or p.is_symlink() for p in paths),
            'bytes': sum(p.lstat().st_size for p in paths if p.is_file() or p.is_symlink())}


def daemon_exit_evidence(artifact, daemon):
    if not daemon.get('confirmed_exited'):
        raise RuntimeError('宿主退出未确认')
    injected = [entry for entry in artifact['signals']
                if entry.get('pid') == daemon['pid'] and entry.get('target') == 'owned-daemon'
                and entry.get('daemon_generation') == daemon['generation']
                and entry.get('signal') == 'SIGKILL' and entry.get('signal_number') == 9
                and entry.get('reason') == 'after real Git CAS']
    if len(injected) > 1: raise RuntimeError('同代次故障注入记录不唯一')
    expected = -9 if injected else 0
    if daemon.get('process_exit') != expected:
        raise RuntimeError('宿主退出状态与该 PID/代次的故障注入不符')
    return {'test': artifact['test'], 'pid': daemon['pid'], 'generation': daemon['generation'],
            'confirmed_exited': daemon['confirmed_exited'], 'process_exit': daemon['process_exit'],
            'expected_exit': expected, 'fault_injection': injected[0]['reason'] if injected else None}


def process_sample(root_pid, env):
    """Read process names and ancestry, without command arguments or environments."""
    started = time.monotonic()
    sampled_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    argv = ['/bin/ps', '-axo', 'pid=,ppid=,pgid=,stat=,pcpu=,time=,comm=']
    result = subprocess.run(argv, env=dict(env, LC_ALL='C'), capture_output=True, text=True, timeout=10)
    if result.returncode: raise RuntimeError('ps sample failed: ' + result.stderr)
    processes = []
    for line in result.stdout.splitlines():
        if not line.strip(): continue
        pid, ppid, pgid, state, cpu, cpu_time, name = line.split(None, 6)
        processes.append(dict(pid=int(pid), ppid=int(ppid), pgid=int(pgid), state=state,
                              reported_pcpu=float(cpu), reported_cpu_time=cpu_time, name=name))
    parents = {row['pid']: row['ppid'] for row in processes}
    for row in processes:
        pid = row['pid']; seen = set()
        while pid in parents and pid != root_pid and pid not in seen:
            seen.add(pid); pid = parents[pid]
        row['observed_test_descendant'] = pid == root_pid
    uptime = subprocess.run(['/usr/bin/uptime'], env=dict(env, LC_ALL='C'),
                            capture_output=True, text=True, timeout=10)
    if uptime.returncode: raise RuntimeError('uptime sample failed: ' + uptime.stderr)
    return dict(sampled_at=sampled_at, elapsed_seconds=time.monotonic() - started,
                root_pid=root_pid, sampler_pid=os.getpid(), ps_argv=argv,
                uptime=uptime.stdout.strip(), processes=processes)


def summarize(folder, cases=CASES):
    rows = []
    for path in sorted((folder / 'readbacks').glob('*.json')):
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        if not any(snapshot['test'].endswith('.' + name) for name in cases): continue
        events = [{**e, 'details': json.loads(e['details'])} for e in snapshot['tables']['events']]
        tasks = [json.loads(t['data']) for t in snapshot['tables']['tasks']]
        reviews = []
        for event in events:
            if not event['type'].startswith('review_'): continue
            details = event['details']; review = details.get('review', {})
            reviews.append({'seq': event['seq'], 'time': event['time'], 'type': event['type'],
                'review_id': details.get('review_id', review.get('review_id')),
                'candidate': review.get('candidate_commit'), 'worker_boundary': details.get('worker_boundary'),
                'state': review.get('state'), 'phase': details.get('phase'),
                'error': details.get('details', {}).get('error')})
        requests = []
        for event in snapshot['tables']['orchestration_events']:
            if event['type'] not in ('request_received', 'request_result'): continue
            details = json.loads(event['data'])
            requests.append({'seq': event['seq'], 'time': event['time'], 'type': event['type'],
                'id': details.get('id'), 'command': details.get('input', {}).get('command', details.get('command')),
                'ok': details.get('ok')})
        tail = []
        for event in events[-12:]:
            details = event['details']; argv = details.get('argv', [])
            tail.append({'seq': event['seq'], 'time': event['time'], 'type': event['type'],
                         'git_argv': argv if argv[:1] == ['git'] else None,
                         'exit': details.get('returncode')})
        rows.append({'test': snapshot['test'], 'readback': str(path), 'cutoff': snapshot['captured_at'],
            'daemon_pid': snapshot['daemon_pid'], 'event_counts': dict(collections.Counter(e['type'] for e in events)),
            'task_states': [{'task': t['task_id'], 'state': t['state'],
                             'review_state': (t.get('review') or {}).get('state')} for t in tasks],
            'review_events': reviews, 'last_events': tail, 'requests': requests})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--suite', choices=['recovery', 'run'], default='recovery')
    parser.add_argument('--sample-processes', action='store_true',
                        help='Sample ps/uptime every five seconds outside the test process')
    parser.add_argument('--version', choices=[name for name, _ in VERSIONS], action='append')
    parser.add_argument('--dependencies', type=Path,
                        default=Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules'))
    args = parser.parse_args()
    if not args.label.replace('-', '').isalnum(): raise RuntimeError('Invalid label')
    if args.version and len(set(args.version)) != len(args.version): raise RuntimeError('Version repeated')
    selected = [(name, revision) for name, revision in VERSIONS if not args.version or name in args.version]
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('A2A_', 'GIT_', 'COOP_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_', 'NODE_COMPILE_CACHE'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')

    def git(*argv, cwd=ROOT):
        return subprocess.check_output(['git', *argv], cwd=cwd, env=env)

    dependencies = args.dependencies.resolve(strict=True)
    if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('外置盘未挂载')
    if not (dependencies / 'effect').is_dir() or not (dependencies / 'node-pty').is_dir():
        raise RuntimeError('缺少既有依赖；不安装、不回退缓存')
    overlay = (ROOT / RUNNER).read_bytes()
    originals = []
    acceptance_path = 'acceptance/test_run_e2e.py' if args.suite == 'run' else 'acceptance/test_recovery_e2e.py'
    for _, revision in selected:
        if git('rev-parse', revision).decode().strip() != revision: raise RuntimeError('Revision mismatch')
        originals.append(git('show', revision + ':' + acceptance_path))
        for path in (RUNNER, 'workbench/tests/daemon_acceptance_adapter.py',
                     'workbench/tests/legacy_quality_driver.py', 'workbench/tests/daemon_acceptance_host.ts'):
            git('cat-file', '-e', revision + ':' + path)
    if not all(data == originals[0] for data in originals): raise RuntimeError('原验收跨版本字节不同')
    if args.suite == 'run':
        owner = next(node for node in ast.parse(originals[0]).body
                     if isinstance(node, ast.ClassDef) and node.name == 'RunCLI')
        cases = sorted(node.name for node in owner.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
        if len(cases) != 18: raise RuntimeError('原编排组方法数不是 18')
    else:
        cases = CASES
    if args.check_only:
        print(json.dumps({'status': 'PASS', 'scope': 'Git objects and dependency paths only; no host/test/clone',
            'versions': VERSIONS, 'selected': selected, 'suite': args.suite, 'cases': cases, 'acceptance_same_bytes': True,
            'overlay_only': RUNNER, 'real_model_turns': 0,
            'process_sampling_requested': args.sample_processes,
            'process_probe_executed': False}, ensure_ascii=False))
        return 0
    tool_path = str(Path(__file__).resolve().relative_to(ROOT))
    if git('diff', 'HEAD', '--', *PROTECTED, RUNNER, tool_path):
        raise RuntimeError('当前相关源码或诊断工具有未提交改动')
    out = ARCHIVE_ROOT / args.label; out.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix='t090-compare-', dir='/tmp')).resolve()
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'argv': sys.argv,
              'scope': 'Selected historical diagnostic capture; test outcomes are not overwritten',
              'selected': selected, 'suite': args.suite, 'sample_processes': args.sample_processes,
              'real_model_turns': 0, 'vendor_CLI_starts': 0, 'cases': cases, 'versions': [],
              'source_workspace': str(workspace), 'commands': [], 'archive': str(out),
              'tool_revision': git('rev-parse', 'HEAD').decode().strip(), 'python': sys.version,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

    def command(argv, cwd=ROOT, timeout=360, monitor=False):
        number = len(record['commands']) + 1
        row = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'timeout': timeout}
        record['commands'].append(row)
        with (out / f'{number:02d}.stdout.txt').open('xb') as stdout, \
                (out / f'{number:02d}.stderr.txt').open('xb') as stderr:
            child = subprocess.Popen(row['argv'], cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            row['pid'] = child.pid
            stopped = threading.Event()
            sampler = None
            if monitor:
                row['samples'] = str(out / f'{number:02d}.process-samples.jsonl')
                row['sample_count'] = 0
                row['sampling_complete'] = False
                def sample_loop():
                    try:
                        with Path(row['samples']).open('x', encoding='utf-8') as stream:
                            while not stopped.is_set():
                                stream.write(json.dumps(process_sample(child.pid, env), ensure_ascii=False) + '\n')
                                stream.flush()
                                row['sample_count'] += 1
                                if stopped.wait(5): break
                        row['sampling_complete'] = True
                    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                        row['sampling_error'] = repr(error)
                sampler = threading.Thread(target=sample_loop, daemon=True)
                sampler.start()
            try:
                row['exit_code'] = child.wait(timeout=timeout)
            finally:
                stopped.set()
                if sampler is not None:
                    sampler.join()
                    if not row['sampling_complete'] or row['sample_count'] == 0:
                        row.setdefault('sampling_error', 'Process samples were not completed')
        return row['exit_code']

    def archive_owned(path, prefix):
        path = Path(path).resolve()
        if path.parent != Path('/private/tmp') or not path.name.startswith(prefix) or path.is_symlink():
            raise RuntimeError('Unexpected owned source/fixture: ' + str(path))
        target = out / 'fixtures' / path.name
        before = inventory(path); shutil.copytree(path, target, symlinks=True)
        if before != inventory(target): raise RuntimeError('归档文件数或字节数不符')
        save(out / (path.name + '.archive.json'), {'original': str(path), 'archive': str(target),
             **before, 'replay': record['argv']})
        shutil.rmtree(path)
        return str(target)

    def unchanged(checkout, revision):
        if git('rev-parse', 'HEAD', cwd=checkout).decode().strip() != revision:
            raise RuntimeError('冻结版本被改变')
        changed = git('diff', '--name-only', revision, cwd=checkout).decode().splitlines()
        if any(path != RUNNER for path in changed): raise RuntimeError('除选择器以外的历史文件被改变')
        if (checkout / RUNNER).read_bytes() != overlay: raise RuntimeError('选择器变化')

    try:
        code = command(['node', '--version'])
        version = (out / '01.stdout.txt').read_text(encoding='utf-8').strip()
        if code or not version.startswith('v26.5.'): raise RuntimeError('需要已核对的 Node 26.5 系列')
        record['node'] = version
        if args.sample_processes:
            # Fail before starting a test if the host cannot supply the requested
            # observations. No missing sample is replaced with a CPU conclusion.
            save(out / 'process-preflight.json', process_sample(os.getpid(), env))
        for name, revision in selected:
            folder = out / name; folder.mkdir()
            checkout = workspace / name
            for argv in (['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--shared', '--no-checkout', ROOT, checkout],
                         ['git', 'sparse-checkout', 'init', '--cone'],
                         ['git', 'sparse-checkout', 'set', 'workbench', 'acceptance', 'fixtures', 'scripts', '.project-map', '.grilling'],
                         ['git', '-c', 'core.hooksPath=/dev/null', 'checkout', '--detach', revision]):
                cwd = ROOT if argv[1] == '-c' and 'clone' in argv else checkout
                if command(argv, cwd): raise RuntimeError('隔离源码准备失败')
            modules = checkout / 'workbench/node_modules'
            modules.symlink_to(dependencies, target_is_directory=True)
            historical = (checkout / RUNNER).read_bytes()
            (folder / 'historical-runner.py').write_bytes(historical)
            (folder / 'runner-overlay.py').write_bytes(overlay)
            (folder / 'runner-overlay.diff').write_text(''.join(difflib.unified_diff(
                historical.decode().splitlines(True), overlay.decode().splitlines(True),
                fromfile=revision + '/' + RUNNER, tofile='current-case-selector')), encoding='utf-8')
            (checkout / RUNNER).write_bytes(overlay)
            unchanged(checkout, revision)
            target = folder / args.suite
            argv = [sys.executable, '-B', checkout / RUNNER, '--suite', args.suite,
                    '--revision', revision, '--output', target]
            if args.suite == 'recovery':
                for case in cases: argv.extend(['--case', case])
            row = {'name': name, 'revision': revision, 'capture_status': 'INCOMPLETE',
                   'overlay_only': RUNNER, 'acceptance_or_product_changes': []}
            record['versions'].append(row)
            # 600 seconds is the same outer watchdog as run-host.py for the
            # complete 18-method group. Original method deadlines are untouched.
            code = command(argv, checkout, timeout=600 if args.suite == 'run' else 360,
                           monitor=args.sample_processes)
            result = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            row.update(exit_code=code, test_status=result['status'], tests_run=result['tests_run'],
                       failures=result['failures'], errors=result['errors'], error_text=result['error_text'],
                       failure_text=result['failure_text'], readbacks=summarize(target, cases))
            if code not in (0, 1) or result['tests_run'] != len(cases) or result['skipped'] or result['executed_methods'] != cases:
                raise RuntimeError('选择的原方法或运行结果不完整')
            if result['collection_errors']: raise RuntimeError('宿主清理有误，保留全部现场并停止后续版本')
            artifacts = json.loads(gzip.decompress((target / 'artifacts.json.gz').read_bytes()))
            if len(artifacts) != len(cases): raise RuntimeError('无法绑定全部原始夹具')
            row['daemon_exits'] = []
            for artifact in artifacts:
                for daemon in artifact['daemons']:
                    evidence = daemon_exit_evidence(artifact, daemon)
                    row['daemon_exits'].append(evidence)
                    observed = subprocess.run(['/bin/ps', '-p', str(daemon['pid']), '-o', 'pid='], env=env,
                                              capture_output=True, text=True)
                    evidence['ps'] = {'exit_code': observed.returncode, 'stdout': observed.stdout, 'stderr': observed.stderr}
                    if observed.returncode != 1 or observed.stdout.strip():
                        raise RuntimeError('原宿主 PID 仍存在或无法核对，保留全部现场')
            row['fixture_archive'] = archive_owned(Path(result['artifact_root']), 's3f-')
            unchanged(checkout, revision)
            row['capture_status'] = 'PASS'
            print(json.dumps({'version': name, 'capture_status': row['capture_status'],
                              'test_status': row['test_status'], 'errors': row['errors']}), flush=True)
        record['source_archive'] = archive_owned(workspace, 't090-compare-')
        if any(row.get('sampling_error') for row in record['commands']):
            raise RuntimeError('测试结果已采集，但进程采样不完整；不作进程负载归因')
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), action='preserve; no retry, timeout change, signal or product edit')
        raise
    finally:
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', record)
        # Keep the complete readbacks/tracebacks outside the repository. The
        # repository summary links them and preserves every original verdict.
        summary = {**record, 'raw_report': str(out / 'run.json')}
        summary['versions'] = [{k: row[k] for k in ('name', 'revision', 'capture_status', 'exit_code',
            'test_status', 'tests_run', 'failures', 'errors', 'fixture_archive') if k in row} |
            {'error_tests': [e['test'] for e in row.get('error_text', [])],
             'failure_tests': [e['test'] for e in row.get('failure_text', [])],
             'readback_directory': str(out / row['name'] / args.suite / 'readbacks')}
            for row in record['versions']]
        save(BASE / (args.label + '.json'), summary)
        save(BASE / (args.label + '.archive.json'), {'original': str(out), 'archive': str(out),
             **inventory(out), 'replay': record['argv']})
        print(json.dumps({'status': record['status'], 'product_status': record['product_status'],
                          'archive': str(out)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
