"""Controller-only candidate checks; no real model phase is enabled here.

The focused phase stops on any actual storage inconsistency or missing history.
Regression and mutant phases are separately selectable after controller review.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import traceback

from command_evidence import CommandLog
from prepare_workbench_mutants import prepare

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '18235b2c53610c412b5f4ea53e0e6e5c56d35849'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['focused', 'attachments', 'checker-counterfactuals', 'regression', 'mutants'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    commands = CommandLog(out)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    record = {'status': 'INCOMPLETE', 'task': 'T-076-1', 'ready_rev': 1, 'phase': args.phase,
              'baseline': BASELINE, 'argv': sys.argv, 'real_codex_turns': 0, 'steps': [],
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    captured = {}
    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk is not mounted; no install or cache fallback')
        preflight = commands.run(['node', '--version'], cwd=ROOT, env=env)
        if preflight.returncode or not preflight.stdout.strip().startswith('v26.5.'):
            raise RuntimeError('Approved Node 26.5 runtime is unavailable')
        diff = commands.run(['git', 'diff', BASELINE, '--', 'acceptance/test_coop_e2e.py',
                             'acceptance/test_recovery_e2e.py', 'acceptance/test_run_e2e.py'], cwd=ROOT, env=env)
        if diff.returncode or diff.stdout:
            raise RuntimeError('Original gate acceptance assertions changed')
        fixture = Path(tempfile.mkdtemp(prefix='g76-', dir='/tmp')).resolve()
        source = fixture / 'source'
        shutil.copytree(ROOT / 'workbench', source / 'workbench', symlinks=True,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
        (source / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        captured = {path: path.read_bytes() for parent in ('src', 'hooks', 'tests', 'app')
                    for path in (ROOT / 'workbench' / parent).rglob('*') if path.is_file() and
                    '__pycache__' not in path.parts}
        for name in ('README.md', 'package.json', 'package-lock.json'):
            path = ROOT / 'workbench' / name; captured[path] = path.read_bytes()
        head = commands.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env)
        patch = commands.run(['git', 'diff', '--', 'workbench/src', 'workbench/hooks', 'workbench/tests',
                              'workbench/README.md'], cwd=ROOT, env=env)
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
            archive.add(source / 'workbench', arcname='workbench')
        save(out / 'source-manifest.json', {'source': str(source), 'head': head.stdout.strip(),
             'tracked_diff': patch.stdout, 'paths': [str(path.relative_to(ROOT)) for path in captured],
             'dependencies': str((ROOT / 'workbench/node_modules').resolve()), 'code_is_uncommitted_candidate': True})
        record['source'] = str(source)

        def child(name, argv, result_path):
            result = commands.run(argv, cwd=ROOT, env=env, timeout=600,
                                  stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
            value = json.loads(result_path.read_text(encoding='utf-8')) if result_path.is_file() else None
            step = {'name': name, 'command': result.evidence, 'result_path': str(result_path), 'result': value}
            record['steps'].append(step); save(out / (name + '.receipt.json'), step)
            print(json.dumps({'step': name, 'exit': result.returncode}), flush=True)
            return result, value

        def green(name, argv, result_path):
            result, value = child(name, argv, result_path)
            if not (result.returncode == 0 and value and value['status'] == 'PASS'):
                raise RuntimeError('Candidate check failed; preserve and report: ' + name)
            return value

        if args.phase == 'focused':
            target = out / 'trailers'
            green('trailers', [sys.executable, '-B', source / 'workbench/tests/test_hook_turn_facts.py',
                  '--source', source, '--output', target], target / 'run.json')
            target = out / 'hook-environment'
            green('hook-environment', [sys.executable, '-B', source / 'workbench/tests/test_hook_environment.py',
                  '--output', target], target / 'results.json')
            target = out / 'identity'
            value = green('identity', [sys.executable, '-B', source / 'workbench/tests/test_multiturn_identity_e2e.py',
                         '--source', source, '--case', 'all', '--output', target], target / 'run.json')
            if (value['tests_run'], value['failures'], value['errors'], value['skipped']) != (4, 0, 0, 0):
                raise RuntimeError('Identity suite did not execute all positive and negative contracts')
            # A distinct full delivery supplies the checker input. Its report
            # is not an assertion that all stores are reconstructable.
            target = out / 'consistency-delivery'
            value = green('consistency-delivery', [sys.executable, '-B', source / 'workbench/tests/test_multiturn_identity_e2e.py',
                         '--source', source, '--case', 'reclaim', '--check-consistency', '--output', target], target / 'run.json')
            artifact = value['artifacts'][0]
            report_path = Path(artifact['consistency_report'])
            report = json.loads(report_path.read_text(encoding='utf-8'))
            record['consistency'] = {'path': str(report_path), 'report': report,
                                     'database_snapshot': artifact['database_snapshot']}
            if report['status'] != 'PASS':
                record['stop_reason'] = '一致性检查报告不一致或无法重建；按主控决定01停下，不改存储'
                raise RuntimeError(record['stop_reason'])
            target = out / 'checker-counterfactuals'
            green('checker-counterfactuals', ['node', source / 'workbench/tests/test_state_consistency.ts',
                  source, artifact['database_snapshot'], target], target / 'run.json')
        elif args.phase == 'attachments':
            target = out / 'windows'
            value = green('attachment-windows', [sys.executable, '-B', source / 'workbench/tests/test_attachment_windows.py',
                         '--source', source, '--output', target], target / 'run.json')
            if len(value['cases']) != 2 or any(row['conclusion'] not in ('一致', '不一致', '无法重建') for row in value['cases']):
                raise RuntimeError('Both attachment conclusions must be explicitly recorded')
            record['attachment_conclusions'] = [{key: row[key] for key in ('mode', 'conclusion', 'reason')} for row in value['cases']]
            record['scope'] = '取证完成；结论如实记录，不表示附件存储一致，按主控#9不修存储'
        elif args.phase == 'checker-counterfactuals':
            snapshot = ROOT / 'evidence/2026-10-11-batch13/T-076/card-1/outside-green-focused-01/consistency-delivery/databases-c-gaod4as5'
            target = out / 'counterfactuals'
            green('checker-counterfactuals', ['node', source / 'workbench/tests/test_state_consistency.ts',
                  source, snapshot, target], target / 'run.json')
        elif args.phase == 'regression':
            for suite, count in (('coop', 8), ('recovery', 9), ('run', 18)):
                target = out / suite
                value = green(suite, [sys.executable, '-B', ROOT / 'workbench/tests/run_daemon_acceptance.py',
                             '--suite', suite, '--label', suite, '--output-root', out], target / 'run.json')
                if (value['tests_run'], value['failures'], value['errors'], value['skipped']) != (count, 0, 0, 0):
                    raise RuntimeError('Original suite membership/result changed: ' + suite)
        else:
            recorded = ROOT / 'evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/lifecycle'
            for name in ('control-offline', 'control-volume'):
                target = out / name
                if name == 'control-offline':
                    argv = [sys.executable, '-B', source / 'workbench/tests/test_offline_trace_e2e.py',
                            '--source', source, '--recorded', recorded, '--output', target]
                    result_path = target / 'verdict.json'
                else:
                    argv = [sys.executable, '-B', source / 'workbench/tests/test_build_volume_contract.py',
                            '--source', source, '--output', target]
                    result_path = target / 'run.json'
                green(name, argv, result_path)
            manifest = prepare(source, out / 'mutant-sources')
            for name, mutant in manifest['mutants'].items():
                target = out / name
                if name == 'missing_volume_builds':
                    result, value = child(name, [sys.executable, '-B', source / 'workbench/tests/test_build_volume_contract.py',
                        '--source', mutant['source'], '--output', target], target / 'run.json')
                    killed = value and value.get('classification') == 'business-red' and value['command']['exit'] == 0
                else:
                    result, value = child(name, [sys.executable, '-B', source / 'workbench/tests/test_offline_trace_e2e.py',
                        '--source', mutant['source'], '--recorded', recorded, '--output', target], target / 'verdict.json')
                    killed = value and value.get('error', '').startswith('AssertionError(')
                if result.returncode != 1 or not killed:
                    raise RuntimeError('Mutant was not rejected at a business assertion: ' + name)
        record['status'] = 'PASS'
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        changed = [str(path) for path, data in captured.items() if not path.is_file() or path.read_bytes() != data]
        record['changed_source_paths'] = changed
        if changed:
            record.update(status='INCOMPLETE', error='Candidate source changed during execution')
        record['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', record)
    print(json.dumps({key: record[key] for key in ('status', 'phase', 'real_codex_turns')}), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
