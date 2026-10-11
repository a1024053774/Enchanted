#!/usr/bin/env python3
"""Freeze sources and run the selected controller-authorized checks."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import traceback


BASELINE = 'e55da7db17c25d9712909666119104fc96969a93'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--phase', choices=['red', 'checks', 'window', 'bisect', 'offline', 'live'], required=True)
    args = parser.parse_args()
    if not args.label or not all(char.isascii() and (char.isalnum() or char in '-_') for char in args.label):
        parser.error('label must contain only ASCII letters, digits, underscores, or hyphens')
    evidence = Path(__file__).resolve().parent
    root = evidence.parents[3]
    sys.path.insert(0, str(root / 'workbench/tests'))
    from command_evidence import CommandLog
    output = evidence / ('outside-' + args.label)
    output.mkdir(exist_ok=False)
    temporary = Path(tempfile.mkdtemp(prefix='a2a4src-', dir='/tmp')).resolve()
    source = temporary / 'source'
    source.mkdir()
    command_log = CommandLog(output)
    journal = []
    verdict = {'status': 'INCOMPLETE', 'phase': args.phase, 'baseline': BASELINE,
               'source': str(source), 'model_turns': 0, 'electron_started': False}

    def record(argv, *, stdout_file=None):
        result = command_log.run(argv, cwd=root, stdout_file=stdout_file)
        entry = result.evidence
        journal.append(entry)
        (output / 'preparation.json').write_text(json.dumps(journal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if result.returncode:
            raise RuntimeError(entry)
        return result

    try:
        record(['git', 'rev-parse', 'HEAD'])
        record(['git', 'status', '--short'])
        if args.phase == 'red':
            source_archive = output / 'baseline-workbench.tar'
            record(['git', 'archive', '--format=tar', BASELINE, 'workbench'], stdout_file=source_archive)
        else:
            verdict['baseline'] = None
            verdict['base_head'] = journal[0]['stdout'].strip()
            record(['git', 'diff', '--', 'workbench'], stdout_file=output / 'source.diff')
            source_archive = output / 'candidate-source.tar.gz'
            def source_filter(member):
                if any(part in {'node_modules', '__pycache__', '.DS_Store'} for part in Path(member.name).parts):
                    return None
                return member
            with tarfile.open(source_archive, 'x:gz') as archive:
                paths = ['workbench', 'acceptance', 'fixtures/pagination']
                if args.phase == 'live':
                    paths += ['.project-map/roles/worker.md', '.project-map/tickets/T-075-tracer-bullet-daemon-gate-pane.md']
                for name in paths:
                    archive.add(root / name, arcname=name, filter=source_filter)
        with tarfile.open(source_archive, 'r:*') as archive:
            # Extract tracked files and the reviewed local hook.py links.
            # No checkout, reset, or shared output replacement occurs.
            for member in archive.getmembers():
                relative = Path(member.name)
                if relative.is_absolute() or '..' in relative.parts or relative.parts[0] not in {'workbench', 'acceptance', 'fixtures', '.project-map'}:
                    raise RuntimeError('Unexpected archive path: ' + member.name)
                target = source / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open('xb') as stream, archive.extractfile(member) as original:
                        shutil.copyfileobj(original, stream)
                    target.chmod(member.mode)
                elif member.issym() and relative.parent == Path('workbench/hooks') and member.linkname == 'hook.py':
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to('hook.py')
                else:
                    raise RuntimeError('Baseline archive has an unreviewed link: ' + member.name)
        dependencies = root / 'workbench/node_modules'
        if not dependencies.is_dir():
            raise RuntimeError('Installed dependencies are unavailable; do not install them automatically')
        # This link is in an isolated source checkout, never in a build output.
        (source / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
        if args.phase in {'checks', 'window', 'bisect', 'offline', 'live'}:
            checks = []
            command_env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
            command_env.pop('ELECTRON_RUN_AS_NODE', None)
            def check(label, argv, extra_env=None, expected_exit=0):
                result = command_log.run(argv, cwd=source, timeout=None,
                                         env={**command_env, **(extra_env or {})},
                                         stdout_file=output / (label + '.stdout.txt'),
                                         stderr_file=output / (label + '.stderr.txt'))
                entry = {'label': label, 'argv': [str(item) for item in argv], 'exit': result.returncode,
                         'expected_exit': expected_exit, 'environment_overrides': extra_env or {},
                         'command_id': result.evidence['id'], 'stdout_file': result.evidence['stdout_file'],
                         'stderr_file': result.evidence['stderr_file']}
                checks.append(entry)
                (output / 'checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                return result.returncode == expected_exit
            if args.phase in {'offline', 'live'}:
                offline_ok = check('offline-trace', [sys.executable, '-B', source / 'workbench/tests/test_offline_trace_e2e.py',
                    '--source', source, '--recorded', evidence / 'outside-live-01/lifecycle', '--output', output / 'offline-trace'])
                verdict['electron_started'] = 'see offline-trace/window-driver.jsonl and offline-trace/verdict.json'
                if not offline_ok or args.phase == 'offline':
                    verdict.update(status='PASS' if offline_ok else 'INCOMPLETE', checks=checks, model_turns=0,
                                   claim='确定性离线trace：中文跨块、原文字节、不读屏；没有真实PTY或模型回合')
                    print(json.dumps(verdict, ensure_ascii=False))
                    return 0 if offline_ok else 1
            if args.phase == 'live':
                passed = check('lifecycle', [sys.executable, '-B', source / 'workbench/tests/run_pane_lifecycle.py',
                    '--source', source, '--repository', root, '--output', output / 'lifecycle',
                    '--budget', evidence / 'turn-budget.jsonl'])
                child = json.loads((output / 'lifecycle/verdict.json').read_text(encoding='utf-8'))
                passed = passed and child['status'] == 'PASS'
                verdict.update(status='PASS' if passed else 'BLOCKED' if child['status'] == 'BLOCKED' else 'INCOMPLETE', checks=checks,
                               model_turns=child.get('observed_main_turns'), reserved_turns=child.get('real_turns_reserved'),
                               claim='真实窗格生命周期；完整结果及限制见 lifecycle/verdict.json')
                print(json.dumps(verdict, ensure_ascii=False))
                return 0 if passed else 1
            if args.phase == 'bisect':
                previous = evidence / 'outside-checks-04'
                previous_source = Path(json.loads((previous / 'verdict.json').read_text(encoding='utf-8'))['source'])
                previous_build = json.loads((previous / 'window/build.json').read_text(encoding='utf-8'))['out']
                ready_ok = check('ready-bisect', [sys.executable, '-B', source / 'workbench/tests/bisect_electron_ready.py',
                    '--source', source, '--old-driver', previous_source / 'workbench/tests/electron_driver.mjs',
                    '--build', previous_build, '--output', output / 'ready-bisect'])
                if not ready_ok:
                    verdict.update(status='INCOMPLETE', checks=checks, claim='ready 二分未形成预期对照；停止，不继续窗口验收')
                    print(json.dumps(verdict, ensure_ascii=False))
                    return 1
            check('window', [sys.executable, '-B', source / 'workbench/tests/test_electron_e2e.py',
                            '--source', source, '--output', output / 'window', '--stage', 'window'])
            if args.phase in {'window', 'bisect'}:
                passed = all(item['exit'] == item['expected_exit'] for item in checks)
                verdict.update(status='PASS' if passed else 'INCOMPLETE', checks=checks,
                               claim='仅复跑修复后的界面构建与窗口检查；其余八项沿用 checks-01/02 的同产品版本证据',
                               electron_started='see window/window-driver.jsonl and window/verdict.json')
                print(json.dumps(verdict, ensure_ascii=False))
                return 0 if passed else 1
            cache_paths = [source / 'workbench/node_modules/.vite', source / 'workbench/node_modules/.vite-temp',
                           source / 'workbench/app/node_modules/.vite', source / 'workbench/app/dist']
            def inventory():
                return {str(path): sorted(item.name for item in path.iterdir()) if path.is_dir() else ('file' if path.exists() else None)
                        for path in cache_paths}
            before = inventory()
            missing = temporary / 'missing-volume'
            ordinary = temporary / 'ordinary-directory'; ordinary.mkdir()
            for label, volume in [('missing-volume', missing), ('ordinary-directory', ordinary)]:
                check(label, ['node', source / 'workbench/app/build.mjs', '--slot', 'must-not-build'],
                      {'A2A_BUILD_VOLUME': str(volume)}, expected_exit=1)
            after = inventory()
            cache_check = {'before': before, 'after': after, 'missing_path_created': missing.exists(),
                           'ordinary_directory_entries': sorted(path.name for path in ordinary.iterdir())}
            cache_check['status'] = 'PASS' if before == after and not missing.exists() and not list(ordinary.iterdir()) else 'INCOMPLETE'
            (output / 'cache-readback.json').write_text(json.dumps(cache_check, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            for name in ['test_pane_dispatch_state', 'test_pane_trace_failure', 'test_relay_core']:
                check(name, ['node', source / ('workbench/tests/' + name + '.ts'), output / name])
            for name in ['test_relay_cli', 'test_daemon_gates_e2e', 'test_daemon_recovery_e2e']:
                check(name, [sys.executable, '-B', source / ('workbench/tests/' + name + '.py'), '--output', output / name])
            passed = all(item['exit'] == item['expected_exit'] for item in checks) and cache_check['status'] == 'PASS'
            verdict.update(status='PASS' if passed else 'INCOMPLETE', checks=checks,
                           claim='零模型回合：界面预检、空窗格截图、缺盘反例和相关后台回归；不代表真实 PTY 生命周期已验收',
                           electron_started='see window/verdict.json')
            print(json.dumps(verdict, ensure_ascii=False))
            return 0 if passed else 1
        frozen_test = output / 'test_electron_e2e.py'
        shutil.copyfile(root / 'workbench/tests/test_electron_e2e.py', frozen_test)
        shutil.copyfile(root / 'workbench/tests/command_evidence.py', output / 'command_evidence.py')
        argv = [sys.executable, '-B', str(frozen_test), '--source', str(source),
                '--output', str(output / 'preflight'), '--stage', 'preflight']
        (output / 'command.json').write_text(json.dumps({'argv': argv}, indent=2) + '\n', encoding='utf-8')
        result = command_log.run(argv, cwd=root, timeout=None, stdout_file=output / 'preflight.stdout.txt',
                                 stderr_file=output / 'preflight.stderr.txt')
        (output / 'preflight.exit-code.txt').write_text(str(result.returncode) + '\n', encoding='utf-8')
        child = json.loads((output / 'preflight/verdict.json').read_text(encoding='utf-8'))
        if child.get('harness_error') or child.get('cleanup_error'):
            raise RuntimeError('Harness or cleanup error is not a contract red; inspect preflight/verdict.json')
        expected = {'electron_build_entry', 'daemon_workbench_snapshot', 'daemon_output_unknown_launch'}
        failed = {item['name'] for item in child['checks'] if item.get('kind') == 'contract_failure'}
        if (result.returncode != 1 or failed != expected or child.get('fixture_setup') != 'PASS'
                or child.get('build_entry_exists') is not False or child.get('daemon_stopped') is not True):
            raise RuntimeError('The baseline did not produce the three expected missing-interface failures')
        verdict.update(status='PASS', claim='仅起点合同红态已取得；产品实施和验收仍 INCOMPLETE',
                       contract_failures=sorted(failed))
    except Exception as error:
        verdict['error'] = repr(error)
        verdict['traceback'] = traceback.format_exc()
    finally:
        (output / 'verdict.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
