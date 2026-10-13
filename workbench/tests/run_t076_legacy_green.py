"""One controller-run phase: new provenance reds, then approved legacy regression.

No real provider/model execution. Failures stop the phase without a retry.
"""
import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import traceback

from audit_legacy_scope import audit
from command_evidence import CommandLog
from prepare_workbench_mutants import prepare
from run_t076_quality_red import archive_directory

ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / 'evidence/2026-10-11-batch13/T-076/card-2'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    log = CommandLog(out)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    report = dict(status='INCOMPLETE', product_status='INCOMPLETE', real_codex_turns=0, argv=sys.argv, steps=[], archives=[],
                  remaining=['real P-review and full real delivery', 'T-077 joint verification', 'independent delivery review'])
    captured = {}; fixtures = []
    try:
        if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External disk is not mounted.')
        version = log.run(['node', '--version'], cwd=ROOT, env=env)
        if version.returncode or not version.stdout.strip().startswith('v26.5.'): raise RuntimeError('Approved Node unavailable.')
        save(out / 'scope.json', audit(ROOT))
        workspace = Path(tempfile.mkdtemp(prefix='l76-', dir='/tmp')).resolve()
        source = workspace / 'candidate'
        shutil.copytree(ROOT / 'workbench', source / 'workbench', symlinks=True,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
        (source / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        for folder in ('acceptance', 'fixtures'):
            shutil.copytree(ROOT / folder, source / folder, ignore=shutil.ignore_patterns('__pycache__'))
        for base in ('workbench/src', 'workbench/hooks', 'workbench/tests', 'workbench/app', 'acceptance'):
            for path in (ROOT / base).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts: captured[path] = path.read_bytes()
        with tarfile.open(out / 'candidate-and-harness.tar.gz', 'x:gz') as archive:
            for name in ('workbench', 'acceptance', 'fixtures'): archive.add(source / name, arcname=name)
        save(out / 'source.json', {'source': str(source), 'legacy_suite_source': str(ROOT),
             'legacy_source_is_frozen_by_capture_and_end_readback': True, 'paths': [str(p.relative_to(ROOT)) for p in captured]})

        def child(name, argv, filename='run.json', expected=0):
            target = out / name
            result = log.run(argv, cwd=ROOT, env=env, timeout=900,
                             stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
            path = target / filename
            value = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None
            report['steps'].append({'name': name, 'exit': result.returncode, 'report': str(path), 'expected_exit': expected})
            print(json.dumps({'step': name, 'exit': result.returncode}), flush=True)
            if value and value.get('artifact_root') and not (target / 'artifacts.tar.gz').exists():
                fixtures.append(Path(value['artifact_root']))
            if result.returncode != expected or not value: raise RuntimeError('Child failed; preserve and stop: ' + name)
            if expected == 0 and value.get('status', 'PASS' if value.get('failure') is None else 'INCOMPLETE') != 'PASS':
                raise RuntimeError('Child did not pass: ' + name)
            return value

        def quality(name, selected, cases, expected=0):
            argv = [sys.executable, '-B', source / 'workbench/tests/test_quality_legacy_e2e.py', '--source', selected, '--output', out / name]
            for case in cases: argv.extend(['--case', case])
            value = child(name, argv, expected=expected)
            if any(row['outcome'] == 'harness_error' or row['cleanup_failures'] for row in value['cases']):
                raise RuntimeError('Quality fixture error is not a contract red.')
            return value

        def legacy(name, suite, method=None, mutant=None, expected=0):
            argv = [sys.executable, '-B', ROOT / 'workbench/tests/run_daemon_acceptance.py',
                    '--suite', suite, '--output-root', out, '--label', name]
            if method: argv.extend(['--test', method])
            if mutant: argv.extend(['--mutant', 'provenance', '--mutant-manifest', mutant])
            value = child(name, argv, expected=expected)
            count = 1 if method else {'coop': 8, 'recovery': 9, 'run': 18}[suite]
            if value['tests_run'] != count or value['errors'] or value['skipped']:
                raise RuntimeError('Legacy membership or fixture failure: ' + name)
            return value

        # New assertions run red BEFORE their candidate green. One exact source
        # guard is removed; no fake delivery, launch or acceptance is inserted.
        mutant = workspace / 'provenance-mutant'; shutil.copytree(source, mutant, symlinks=True)
        core = mutant / 'workbench/src/gates/core.ts'; text = core.read_text(encoding='utf-8')
        before = '        requireGate(attempt.delivery, "score_provenance_required");'
        if text.count(before) != 1: raise RuntimeError('Provenance mutation target is not unique.')
        after = '        // Controlled mutant: omit provenance before CAS.'
        core.write_text(text.replace(before, after), encoding='utf-8')
        manifest = out / 'provenance-mutant.json'
        save(manifest, {'mutants': {'provenance': {'core': str(core)}}, 'before': before,
                        'after': after, 'failures': ['MANUAL-CLAIM-SOURCE', 'W07-MANUAL-SOURCE']})
        red = quality('f10-red', mutant, ['manual_claim_reviewed_score_refused'], 1)
        if red['cases'][0].get('failure_id') != 'MANUAL-CLAIM-SOURCE': raise RuntimeError('F10 mutant missed its intended assertion.')
        frozen_method = 'test_submit_requires_clean_head_and_cannot_replace_frozen_candidate'
        red = legacy('w07-red', 'coop', frozen_method, manifest, 1)
        if red['failures'] != 1 or not any('W07-MANUAL-SOURCE' in row['traceback'] for row in red['failure_text']):
            raise RuntimeError('W07 did not fail at its ref-preservation assertion.')
        base = red['artifacts'][0]['base_commit']
        writes = [row for row in red['commands'] if row.get('label') == 'git' and row['argv'][-2:] == ['rev-parse', 'refs/heads/main']]
        if not writes or writes[-1]['stdout'].strip() == base: raise RuntimeError('W07 red lacks actual changed Git readback.')
        quality('provenance-and-frozen-green', source, ['manual_claim_reviewed_score_refused', 'managed_frozen_candidate_integrates_original'])
        for suite in ('coop', 'recovery', 'run'): legacy(suite, suite)

        child('task-cards', [sys.executable, '-B', ROOT / 'workbench/tests/test_daemon_gates_e2e.py', '--output', out / 'task-cards'])
        child('relay-core', ['node', source / 'workbench/tests/test_relay_core.ts', out / 'relay-core'], 'results.json')
        child('relay-cli', [sys.executable, '-B', source / 'workbench/tests/test_relay_cli.py', '--output', out / 'relay-cli'], 'results.json')
        for name, script, report_file, extra in [
            ('hook-turn', 'test_hook_turn_facts.py', 'run.json', ['--source', source]),
            ('hook-environment', 'test_hook_environment.py', 'results.json', []),
            ('multiturn', 'test_multiturn_identity_e2e.py', 'run.json', ['--source', source, '--check-consistency']),
            ('initial-release', 'test_initial_worker_release.py', 'run.json', ['--source', source]),
            ('daemon-stop', 'test_startup_shutdown_e2e.py', 'run.json', ['--source', source]),
        ]:
            value = child(name, [sys.executable, '-B', source / 'workbench/tests' / script, *extra, '--output', out / name], report_file)
            if name == 'multiturn': report['consistency'] = [{k: a.get(k) for k in ('consistency_status', 'consistency_report')} for a in value['artifacts'] if a.get('consistency_report')]

        ordering = workspace / 'ordering-mutant'; shutil.copytree(source, ordering, symlinks=True)
        daemon = ordering / 'workbench/src/daemon.ts'; text = daemon.read_text(encoding='utf-8')
        before = '    if (activeRequests > 0) await new Promise<void>((resolve) => { requestsDrained = resolve; });\n'
        if text.count(before) != 1: raise RuntimeError('Ordering mutant target is not unique.')
        daemon.write_text(text.replace(before, ''), encoding='utf-8')
        value = child('stop-ordering-red', [sys.executable, '-B', source / 'workbench/tests/test_startup_shutdown_e2e.py',
                      '--source', ordering, '--case', 'ordering', '--output', out / 'stop-ordering-red'], expected=1)
        witness = value['artifacts'][0].get('shutdown_precompletion')
        if value['errors'] or len(value['failures']) != 1 or not witness or witness['violation'] != 'final_event_before_gate':
            raise RuntimeError('Ordering mutation did not reach its business assertion.')
        recorded = ROOT / 'evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/lifecycle'
        def surface(name, selected, volume=False, expected=0):
            script = 'test_build_volume_contract.py' if volume else 'test_offline_trace_e2e.py'
            argv = [sys.executable, '-B', source / 'workbench/tests' / script, '--source', selected, '--output', out / name]
            if not volume: argv.extend(['--recorded', recorded])
            return child(name, argv, 'run.json' if volume else 'verdict.json', expected)
        surface('offline-control', source); surface('volume-control', source, True)
        mutants = prepare(source, out / 'five-mutant-sources')
        for name, entry in mutants['mutants'].items():
            volume = name == 'missing_volume_builds'; value = surface(name, entry['source'], volume, 1)
            killed = value.get('classification') == 'business-red' and value['command']['exit'] == 0 if volume else value.get('error', '').startswith('AssertionError(')
            if not killed: raise RuntimeError('Five-category mutant did not fail at its business boundary: ' + name)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        for index, fixture in enumerate(fixtures):
            try: report['archives'].append(archive_directory(fixture, out / ('fixture-%02d.tar.gz' % index), out.name))
            except Exception as error: report.update(status='INCOMPLETE', archive_error=repr(error))
        changed = [str(path) for path, value in captured.items() if not path.exists() or path.read_bytes() != value]
        report['changed_source_paths'] = changed
        if changed: report.update(status='INCOMPLETE', error='Source changed during execution.')
        report['compressed_files'] = []
        for path in list(out.rglob('*')):
            if not path.is_file() or path.stat().st_size <= 5 * 1024 * 1024: continue
            if path.suffix not in ('.gz', '.zip'):
                compressed = path.with_name(path.name + '.gz')
                with path.open('rb') as src, gzip.open(compressed, 'xb') as dst: shutil.copyfileobj(src, dst)
                if gzip.decompress(compressed.read_bytes()) != path.read_bytes(): raise RuntimeError('Compressed readback differs.')
                path.unlink(); report['compressed_files'].append({'original': str(path), 'gzip': str(compressed)})
        report['oversize_files'] = [str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
        if report['oversize_files']: report.update(status='INCOMPLETE', archive_required=True)
        save(out / 'run.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'product_status', 'real_codex_turns')}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
