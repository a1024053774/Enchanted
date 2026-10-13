"""Controller-only baseline evidence; preserve all failures, use no model turns.

Freeze the supplied baseline, run trailer and receipt identity contracts, record
the missing checker, then measure the original five mutant coverage categories.
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

from command_evidence import CommandLog, command_json
from prepare_workbench_mutants import prepare

ROOT = Path(__file__).resolve().parents[2]


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=['focused', 'mutants'], required=True)
    parser.add_argument('--recorded', type=Path)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    commands = CommandLog(out)
    record = {'status': 'INCOMPLETE', 'task': 'T-076-1', 'ready_rev': 1, 'baseline': args.baseline,
              'phase': args.phase, 'argv': sys.argv, 'real_codex_turns': 0, 'steps': [],
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    captured_harness = {}
    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk not mounted; do not install dependencies or fall back')
        for argv in (['node', '--version'], ['git', '--version']):
            result = commands.run(argv, cwd=ROOT, env=env)
            if result.returncode:
                raise RuntimeError({'preflight_failed': result.evidence})
            if argv[0] == 'node' and not result.stdout.strip().startswith('v26.5.'):
                raise RuntimeError('This fixture requires the approved Node 26.5 series')
        fixture = Path(tempfile.mkdtemp(prefix='r76-', dir='/tmp')).resolve()
        source = fixture / 'source'; source.mkdir()
        archive_path = out / 'baseline-source.tar'
        result = commands.run(['git', 'archive', '--format=tar', args.baseline, 'workbench', 'acceptance', 'fixtures'],
                              cwd=ROOT, env=env, stdout_file=archive_path)
        if result.returncode:
            raise RuntimeError('Cannot freeze baseline source')
        with tarfile.open(archive_path) as archive:
            # This Python predates tarfile's extraction-filter parameter. The
            # archive comes only from the pinned local Git revision; validate
            # all names and links before extraction, without a version retry.
            for member in archive.getmembers():
                destination = (source / member.name).resolve()
                if source not in destination.parents:
                    raise RuntimeError('Git archive member escapes the source fixture')
                if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise RuntimeError('Git archive contains a special file')
                if member.issym() or member.islnk():
                    target = ((destination.parent if member.issym() else source) / member.linkname).resolve()
                    if source not in target.parents:
                        raise RuntimeError('Git archive link escapes the source fixture')
            archive.extractall(source)
        (source / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        record['source'] = str(source)
        with tarfile.open(out / 'baseline-source.tar.gz', 'x:gz') as archive:
            archive.add(source / 'workbench', arcname='workbench')
            archive.add(source / 'acceptance', arcname='acceptance')
            archive.add(source / 'fixtures', arcname='fixtures')
        # The uncompressed file was created by this invocation solely to unpack
        # git archive. Keep the compressed source evidence, never earlier files.
        archive_path.unlink()
        harness_paths = [Path(__file__).with_name(name) for name in (
            'run_t076_red.py', 'test_hook_turn_facts.py', 'test_multiturn_identity_e2e.py',
            'multiturn_identity_host.ts', 'test_build_volume_contract.py', 'prepare_workbench_mutants.py',
            'command_evidence.py', 'test_task_cards_e2e.py')]
        captured_harness = {path: path.read_bytes() for path in harness_paths}
        with tarfile.open(out / 'harness-source.tar.gz', 'x:gz') as archive:
            for path in harness_paths:
                archive.add(path, arcname=str(path.relative_to(ROOT)))
        write_new(out / 'source-manifest.json', {'baseline': args.baseline, 'source': str(source),
                  'dependencies': str((ROOT / 'workbench/node_modules').resolve()),
                  'harness_files': [str(path) for path in harness_paths],
                  'harness_snapshot': str(out / 'harness-source.tar.gz')})

        def child(name, argv, result_file):
            result = commands.run(argv, cwd=ROOT, env=env, timeout=600,
                                  stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
            value = json.loads(result_file.read_text(encoding='utf-8')) if result_file.exists() else None
            step = {'name': name, 'command': result.evidence, 'result_path': str(result_file), 'result': value}
            record['steps'].append(step)
            write_new(out / (name + '.receipt.json'), step)
            print(json.dumps({'step': name, 'exit': result.returncode, 'result': str(result_file)}), flush=True)
            return result, value

        if args.phase == 'focused':
            # Independent contract red must still be recorded if a later
            # runtime fixture fails. This command creates no state directory.
            checker = source / 'workbench/src/stateConsistency.ts'
            result = commands.run(['node', checker, '--state', out / 'unused-checker-state', '--output', out / 'checker-output.json'],
                                  cwd=source, env=env)
            checker_red = {'classification': 'missing-contract-entry', 'entry_exists': checker.exists(),
                           'command': result.evidence, 'pass': not checker.exists() and result.returncode != 0}
            write_new(out / 'checker-contract-red.json', checker_red)
            if not checker_red['pass']:
                raise RuntimeError('Baseline checker absence was not established')
            hook_out = out / 'trailers'
            result, hook = child('trailers', [sys.executable, '-B', ROOT / 'workbench/tests/test_hook_turn_facts.py',
                                '--source', source, '--output', hook_out], hook_out / 'run.json')
            if not (hook and result.returncode == 1 and
                    [r['classification'] for r in hook['cases']] == ['business-red'] * 4 + ['business-pass'] and
                    all(r['observed'].get('A2A-Model') == ['unknown'] and r['observed'].get('A2A-Effort') == ['unknown']
                        for r in hook['cases'][:4])):
                raise RuntimeError('Trailer baseline did not fail at the required unknown assertions')
            for case in ('reclaim', 'run'):
                target = out / case
                result, value = child(case, [sys.executable, '-B', ROOT / 'workbench/tests/test_multiturn_identity_e2e.py',
                                      '--source', source, '--case', case, '--output', target], target / 'run.json')
                refusals = [json.loads(c['stdout']) for c in value['commands']
                            if c.get('exit') == 1 and c.get('stdout')] if value else []
                if not (value and result.returncode == 1 and value['tests_run'] == 1 and
                        value['failures'] == 1 and value['errors'] == value['skipped'] == 0 and
                        not value.get('collection_error') and len(value.get('readbacks', [])) == 1 and
                        any(v.get('error') == 'identity_conflict' for v in refusals)):
                    raise RuntimeError('Receipt baseline was not the required identity_conflict business failure: ' + case)
            record.update(status='PASS', scope='Only focused red evidence; no repaired behavior or real Codex proved')
        else:
            if args.recorded is None:
                raise RuntimeError('--recorded is required for zero-turn offline mutant coverage')
            recorded = args.recorded.resolve()
            for filename in ('launch-record.json', 'state.sqlite3'):
                if not (recorded / filename).is_file():
                    raise RuntimeError('Recorded fixture is missing: ' + filename)
            # Re-run original assertions on this frozen product source. Prior
            # green evidence does not stand in for this baseline invocation.
            target = out / 'control-offline'
            result, value = child('control-offline', [sys.executable, '-B', source / 'workbench/tests/test_offline_trace_e2e.py',
                 '--source', source, '--recorded', recorded, '--output', target], target / 'verdict.json')
            if not (value and result.returncode == 0 and value['status'] == 'PASS'):
                raise RuntimeError('Offline control failed; do not classify any mutants')
            target = out / 'control-volume'
            result, value = child('control-volume', [sys.executable, '-B', ROOT / 'workbench/tests/test_build_volume_contract.py',
                 '--source', source, '--output', target], target / 'run.json')
            if not (value and result.returncode == 0 and value['status'] == 'PASS'):
                raise RuntimeError('Volume control failed; do not classify any mutants')
            manifest = prepare(source, out / 'mutant-sources')
            coverage = []
            for name, mutant in manifest['mutants'].items():
                target = out / name
                if name == 'missing_volume_builds':
                    argv = [sys.executable, '-B', ROOT / 'workbench/tests/test_build_volume_contract.py',
                            '--source', mutant['source'], '--output', target]
                    result, value = child(name, argv, target / 'run.json')
                    killed = bool(value and result.returncode == 1 and value.get('classification') == 'business-red' and
                                  value['command']['exit'] == 0 and value['created_volume'])
                    existed = False
                else:
                    argv = [sys.executable, '-B', source / 'workbench/tests/test_offline_trace_e2e.py',
                            '--source', mutant['source'], '--recorded', recorded, '--output', target]
                    result, value = child(name, argv, target / 'verdict.json')
                    # Existing test saves the exception repr and full traceback.
                    # This is a formal exception-type check, not a content judge.
                    killed = bool(value and result.returncode == 1 and value.get('error', '').startswith('AssertionError('))
                    existed = True
                coverage.append({'mutant': name, 'existing_test': existed, 'business_failure': killed,
                                 'baseline_coverage': '已有覆盖' if existed and killed else '缺测试' if not existed else '未检出',
                                 'result': str(target), 'patch': mutant['patch']})
                if not killed:
                    # A clean pass is missing coverage. Other failures are not
                    # a qualifying mutant result and require controller review.
                    if not (value and result.returncode == 0 and value['status'] == 'PASS'):
                        raise RuntimeError('Mutation did not fail at a business assertion: ' + name)
            record.update(status='PASS', coverage=coverage,
                          scope='Baseline mutant coverage inventory only; candidate must be re-run separately')
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        record.update(error=repr(error), traceback=traceback.format_exc(), classification='evidence-incomplete')
    finally:
        changed = [str(path) for path, original in captured_harness.items()
                   if not path.is_file() or path.read_bytes() != original]
        record['changed_harness_files'] = changed
        if changed:
            record.update(status='INCOMPLETE', classification='harness-changed-during-run')
        record['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_new(out / 'run.json', record)
    print(json.dumps({key: record[key] for key in ('status', 'phase', 'baseline', 'real_codex_turns')}), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
