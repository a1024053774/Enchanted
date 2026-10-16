"""串行采集选定历史版本的两个原恢复用例；不是产品通过判定。"""
import argparse
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

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ARCHIVE_ROOT = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090')
VERSIONS = [('pre-T082', '150ef6516f6ef5aaa6855631b770ce262991ffbf'),
            ('main-before-T082', '271ac55d82d0e20067e03e2fa4a990e55ef7b434'),
            ('main-T082', '0e6c2b833f6da64243f71d670ea45bb9116fda4d'),
            ('T090', '18dd12c29f523227d9fc6fd4c123a674f10bf7fa')]
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


def summarize(folder):
    rows = []
    for path in sorted((folder / 'readbacks').glob('*.json')):
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        if not any(snapshot['test'].endswith('.' + name) for name in CASES): continue
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
    for _, revision in VERSIONS:
        if git('rev-parse', revision).decode().strip() != revision: raise RuntimeError('Revision mismatch')
        originals.append(git('show', revision + ':acceptance/test_recovery_e2e.py'))
        for path in (RUNNER, 'workbench/tests/daemon_acceptance_adapter.py',
                     'workbench/tests/legacy_quality_driver.py', 'workbench/tests/daemon_acceptance_host.ts'):
            git('cat-file', '-e', revision + ':' + path)
    if not all(data == originals[0] for data in originals): raise RuntimeError('原恢复验收跨版本字节不同')
    if args.check_only:
        print(json.dumps({'status': 'PASS', 'scope': 'Git objects and dependency paths only; no host/test/clone',
            'versions': VERSIONS, 'selected': selected, 'cases': CASES, 'acceptance_same_bytes': True,
            'overlay_only': RUNNER, 'real_model_turns': 0}, ensure_ascii=False))
        return 0
    if git('diff', 'HEAD', '--', *PROTECTED, RUNNER): raise RuntimeError('当前相关源码有未提交改动')
    out = ARCHIVE_ROOT / args.label; out.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix='t090-compare-', dir='/tmp')).resolve()
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'argv': sys.argv,
              'scope': 'Selected historical diagnostic capture; test outcomes are not overwritten',
              'selected': selected,
              'real_model_turns': 0, 'vendor_CLI_starts': 0, 'cases': CASES, 'versions': [],
              'source_workspace': str(workspace), 'commands': [], 'archive': str(out),
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

    def command(argv, cwd=ROOT, timeout=360):
        number = len(record['commands']) + 1
        row = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'timeout': timeout}
        record['commands'].append(row)
        with (out / f'{number:02d}.stdout.txt').open('xb') as stdout, \
                (out / f'{number:02d}.stderr.txt').open('xb') as stderr:
            child = subprocess.Popen(row['argv'], cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            row['pid'] = child.pid
            row['exit_code'] = child.wait(timeout=timeout)
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
        if git('diff', revision, '--', *PROTECTED, cwd=checkout): raise RuntimeError('产品或验收文件被改变')
        changed = git('diff', '--name-only', revision, '--', 'workbench/tests', cwd=checkout).decode().splitlines()
        if any(path != RUNNER for path in changed): raise RuntimeError('除选择器以外的历史测试工具被改变')
        if (checkout / RUNNER).read_bytes() != overlay: raise RuntimeError('选择器变化')

    try:
        code = command(['node', '--version'])
        version = (out / '01.stdout.txt').read_text(encoding='utf-8').strip()
        if code or not version.startswith('v26.5.'): raise RuntimeError('需要已核对的 Node 26.5 系列')
        record['node'] = version
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
            target = folder / 'recovery'
            argv = [sys.executable, '-B', checkout / RUNNER, '--suite', 'recovery',
                    '--revision', revision, '--output', target]
            for case in CASES: argv.extend(['--case', case])
            row = {'name': name, 'revision': revision, 'capture_status': 'INCOMPLETE',
                   'overlay_only': RUNNER, 'acceptance_or_product_changes': []}
            record['versions'].append(row)
            code = command(argv, checkout)
            result = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            row.update(exit_code=code, test_status=result['status'], tests_run=result['tests_run'],
                       failures=result['failures'], errors=result['errors'], error_text=result['error_text'],
                       failure_text=result['failure_text'], readbacks=summarize(target))
            if code not in (0, 1) or result['tests_run'] != 2 or result['skipped'] or result['executed_methods'] != CASES:
                raise RuntimeError('选择的原方法或运行结果不完整')
            if result['collection_errors']: raise RuntimeError('宿主清理有误，保留全部现场并停止后续版本')
            artifacts = json.loads(gzip.decompress((target / 'artifacts.json.gz').read_bytes()))
            if len(artifacts) != 2: raise RuntimeError('无法绑定两条原始夹具')
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
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), action='preserve; no retry, timeout change, signal or product edit')
        raise
    finally:
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', record)
        save(BASE / (args.label + '.json'), record)
        save(BASE / (args.label + '.archive.json'), {'original': str(out), 'archive': str(out),
             **inventory(out), 'replay': record['argv']})
        print(json.dumps({'status': record['status'], 'product_status': record['product_status'],
                          'archive': str(out)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
