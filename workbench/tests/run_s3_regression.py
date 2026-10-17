#!/usr/bin/env python3
"""T-077 regression runner: original methods, daemon lifecycle, explicit scope audit."""
import argparse
import copy
import gzip
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

import audit_s3_assertions as audit
from archive_evidence import archive_large_files
import daemon_acceptance_adapter as adapter
import test_task_cards_e2e as cards
from test_daemon_gates_e2e import DaemonCards
from test_worktree_lifecycle_e2e import snapshot_source, write_new, write_gzip

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-077'
COUNTS = {'coop': 8, 'recovery': 9, 'run': 18, 'cas': 1, 'cards': 15}


def observe(argv):
    p = subprocess.run([str(value) for value in argv], cwd=ROOT, capture_output=True, text=True)
    return {'argv': [str(value) for value in argv], 'cwd': str(ROOT), 'exit_code': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr}


def finish_evidence(out, fixture_root, artifacts):
    derived = copy.deepcopy(artifacts)
    collection_errors = []
    for artifact in derived:
        source = artifact.get('state_readback')
        if not source:
            # Card fixtures do not have the recovery adapter's before-stop reader.
            continue
        try:
            path = Path(source)
            data = path.read_bytes()
            value = json.loads(data.decode('utf-8'))
            if value['test'] != artifact['test'] or value['database'] != str((Path(artifact['state']) / 'state.sqlite3').resolve()):
                raise ValueError('Readback identity does not match its fixture')
            compressed = path.with_suffix(path.suffix + '.gz')
            with gzip.open(compressed, 'xb') as handle:
                handle.write(data)
            if gzip.decompress(compressed.read_bytes()) != data:
                raise ValueError('Compressed readback does not preserve the original bytes')
            artifact.update(state_readback=str(compressed), state_readback_format='gzip-json',
                            state_readback_original=str(path))
            path.unlink()  # This run created the file; the verified gzip retains every byte.
        except (OSError, ValueError, KeyError) as error:
            collection_errors.append({'test': artifact.get('test'), 'source': source, 'error': repr(error)})
    with tarfile.open(out / 'fixtures.tar.gz', 'x:gz') as archive:
        archive.add(fixture_root, arcname=fixture_root.name)
    return derived, collection_errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', required=True, choices=COUNTS)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--base', default=audit.INITIAL)
    parser.add_argument('--case')
    parser.add_argument('--mutant-core', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != EVIDENCE.resolve():
        raise ValueError('The regression output must be a new directory in this task evidence folder')
    out.mkdir(exist_ok=False)
    for key in list(os.environ):
        if key.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_')):
            del os.environ[key]
    scope = audit.audit_checkout(args.base)
    scope['auditor_self_check'] = audit.self_check()
    write_new(out / 'assertion-scope.json', scope)
    preflight = {'node': observe(['node', '--version']), 'git': observe(['git', '--version']),
                 'head': observe(['git', 'rev-parse', 'HEAD']), 'diff': observe(['git', 'diff', '--', 'workbench', 'acceptance']),
                 'volume_mounted': os.path.ismount('/Volumes/WD-Elements')}
    write_new(out / 'preflight.json', preflight)
    if scope['status'] != 'PASS' or scope['auditor_self_check']['status'] != 'PASS':
        raise RuntimeError('Assertion edit exceeds the approved whitelist')
    if not preflight['volume_mounted'] or preflight['node']['exit_code'] != 0 or not preflight['node']['stdout'].startswith('v26.5.'):
        raise RuntimeError('Required external volume or Node 26.5 is unavailable')
    if any(value['exit_code'] != 0 for value in preflight.values() if isinstance(value, dict)):
        raise RuntimeError('Preflight command failed')
    snapshot_source(out, ROOT)
    source_names = json.loads((out / 'source-files.json').read_text(encoding='utf-8'))
    frozen = {name: (ROOT / name).read_bytes() for name in source_names}
    fixture_root = Path(tempfile.mkdtemp(prefix='s3r-', dir='/tmp')).resolve()
    os.environ['COOP_E2E_ARTIFACT_ROOT'] = str(fixture_root)
    os.environ['COOP_E2E_TRACE'] = str(fixture_root / 'subprocess-trace.json')
    os.environ['COOP_E2E_READBACK_ROOT'] = str(out / 'readbacks')
    os.environ['COOP_SCRIPT'] = str(adapter.ENTRY)
    os.environ['COOP_NATIVE_ENTRY'] = str(adapter.CLI)
    (out / 'readbacks').mkdir()
    cards.ARTIFACT_ROOT = fixture_root
    if args.mutant_core:
        os.environ['COOP_E2E_MUTANT_CORE'] = str(args.mutant_core.resolve(strict=True))
        with (out / 'mutant-core.ts').open('xb') as handle:
            handle.write(args.mutant_core.read_bytes())
    selections = {
        'coop': (adapter.DaemonDelivery, adapter.delivery.ManagedDeliveryCLI, unittest.TextTestResult),
        'recovery': (adapter.DaemonRecovery, adapter.recovery.RecoveryCLI, adapter.recovery.EvidenceResult),
        'run': (adapter.DaemonRun, adapter.orchestration.RunCLI, adapter.orchestration.EvidenceResult),
        'cas': (adapter.DaemonCAS, adapter.cas.CASRace, adapter.recovery.EvidenceResult),
        'cards': (DaemonCards, None, unittest.TextTestResult),
    }
    cls, original, result_class = selections[args.suite]
    names = sorted(name for name in original.__dict__ if name.startswith('test_')) if original else unittest.defaultTestLoader.getTestCaseNames(cls)
    if len(names) != COUNTS[args.suite]:
        raise RuntimeError('The required suite membership changed')
    if original:
        for name in names:
            if getattr(cls, name) is not getattr(original, name):
                raise RuntimeError('A lifecycle adapter replaced a business test: ' + name)
    else:
        for name in cards.TaskCardsCLI.__dict__:
            if name.startswith('test_') and getattr(cls, name) is not getattr(cards.TaskCardsCLI, name):
                raise RuntimeError('The card lifecycle adapter replaced a business test: ' + name)
    if args.case:
        if args.case not in names:
            raise ValueError('The requested case is not an original suite member')
        names = [args.case]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=result_class, failfast=True).run(
        unittest.TestSuite(cls(name) for name in names))
    with (out / 'unittest.txt').open('x', encoding='utf-8') as handle:
        handle.write(stream.getvalue())
    changed = [name for name, data in frozen.items() if not (ROOT / name).is_file() or (ROOT / name).read_bytes() != data]
    passed = result.wasSuccessful() and result.testsRun == len(names) and not result.skipped and not changed
    summary = {'status': 'PASS' if passed else 'INCOMPLETE', 'task': 'T-077-1', 'suite': args.suite,
               'scope': 'Selected original cases' if args.case else 'Complete original suite',
               'argv': sys.argv, 'cwd': str(ROOT), 'source_commit': preflight['head']['stdout'].strip(),
               'mutant_core': str(args.mutant_core) if args.mutant_core else None,
               'real_codex_turns': 0, 'expected_tests': len(names), 'tests_run': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
               'selected_original_methods': names, 'changed_source_paths': changed,
               'failure_text': [{'test': t.id(), 'traceback': text} for t, text in result.failures],
               'error_text': [{'test': t.id(), 'traceback': text} for t, text in result.errors]}
    write_new(out / 'test-result.json', summary)
    if args.suite == 'cards':
        # TaskCardsCLI records root, not state; its declared layout is root/state.
        # Normalize this producer explicitly without changing its original records.
        artifacts = [{**artifact, 'state': str(Path(artifact['root']) / 'state')} for artifact in cards.ARTIFACTS]
    else:
        artifacts = adapter.delivery.ARTIFACTS
    commands = cards.COMMANDS if args.suite == 'cards' else adapter.delivery.COMMANDS
    write_gzip(out / 'commands.json.gz', commands)
    write_gzip(out / 'assertions.json.gz', adapter.recovery.ASSERTIONS)
    derived, collection_errors = finish_evidence(out, fixture_root, artifacts)
    for artifact in artifacts:
        state = Path(artifact['state'])
        if (state / 'daemon.pid').exists() or (state / 'control.sock').exists():
            collection_errors.append({'test': artifact['test'], 'error': 'Own daemon endpoint or PID still exists', 'state': str(state)})
    write_gzip(out / 'artifacts.json.gz', derived)
    summary.update(artifact_root=str(fixture_root), collection_errors=collection_errors,
                   runtime_layers={a['test']: a.get('evidence_layer', 'default-daemon-cards') for a in artifacts})
    if passed and args.suite == 'run' and not args.case and not args.mutant_core:
        layers = list(summary['runtime_layers'].values())
        if layers.count('isolated-orchestration') != 13 or layers.count('default-production-daemon') != 5:
            collection_errors.append({'error': 'The expected 13 controlled / 5 default runtime split changed', 'layers': layers})
    relocated = archive_large_files(
        out, archive_root=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077') / out.name,
        minimum_bytes=5 * 1024 * 1024,
        replay=['python3', '-B', str(ROOT / 'workbench/tests/run_s3_regression.py'), *sys.argv[1:]])
    summary['external_archives'] = relocated
    summary.pop('failure_text')
    summary.pop('error_text')
    summary['test_result'] = str(out / 'test-result.json')
    passed = passed and not collection_errors
    summary['status'] = 'PASS' if passed else 'INCOMPLETE'
    summary['exit_code'] = 0 if passed else 1
    write_new(out / 'run.json', summary)
    print(json.dumps({key: summary[key] for key in ('status', 'suite', 'tests_run', 'failures', 'errors', 'skipped', 'exit_code')}, ensure_ascii=False))
    return summary['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
