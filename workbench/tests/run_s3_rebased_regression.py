"""Run unchanged acceptance methods at the explicitly frozen merged revision.

The old S3 assertion auditor uses pre-T-076 coordinates. This runner checks the
approved merged acceptance files byte-for-byte against --revision, retains
original method identity and membership, and uses the current external actors.
It does not weaken or replace any acceptance assertion.
"""
import argparse
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

import daemon_acceptance_adapter as adapter
import test_task_cards_e2e as cards
from test_daemon_gates_e2e import DaemonCards

ROOT = Path(__file__).resolve().parents[2]
COUNTS = {'coop': 8, 'recovery': 9, 'run': 18, 'cas': 1, 'cards': 15}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def compressed(path, value):
    with gzip.open(path, 'xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=COUNTS, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != args.revision: raise RuntimeError('Frozen revision changed')
    protected = ['acceptance/test_coop_e2e.py', 'acceptance/test_recovery_e2e.py', 'acceptance/test_run_e2e.py']
    for name in protected:
        if (ROOT / name).read_bytes() != subprocess.check_output(['git', 'show', args.revision + ':' + name], cwd=ROOT):
            raise RuntimeError('Frozen acceptance file changed: ' + name)
    save(out / 'scope.json', {'frozen_revision': head, 'unchanged_acceptance_files': protected,
         'authority': 'Controller #101/#102/#108 approved merged semantics; no assertion override',
         'original_coordinate_audit_is_historical_only': True})
    for key in list(os.environ):
        if key.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_')): del os.environ[key]
    fixtures = Path(tempfile.mkdtemp(prefix='s3f-', dir='/tmp')).resolve()
    os.environ.update(COOP_E2E_ARTIFACT_ROOT=str(fixtures), COOP_E2E_TRACE=str(fixtures / 'trace.json'),
                     COOP_E2E_READBACK_ROOT=str(out / 'readbacks'), COOP_SCRIPT=str(adapter.ENTRY),
                     COOP_NATIVE_ENTRY=str(adapter.CLI))
    (out / 'readbacks').mkdir(); cards.ARTIFACT_ROOT = fixtures
    selections = {'coop': (adapter.DaemonDelivery, adapter.delivery.ManagedDeliveryCLI),
        'recovery': (adapter.DaemonRecovery, adapter.recovery.RecoveryCLI),
        'run': (adapter.DaemonRun, adapter.orchestration.RunCLI),
        'cas': (adapter.DaemonCAS, adapter.cas.CASRace), 'cards': (DaemonCards, None)}
    cls, original = selections[args.suite]
    names = sorted(n for n in original.__dict__ if n.startswith('test_')) if original else unittest.defaultTestLoader.getTestCaseNames(cls)
    if len(names) != COUNTS[args.suite]: raise RuntimeError('Required suite membership changed')
    owner = original or cards.TaskCardsCLI
    for name in owner.__dict__:
        if name.startswith('test_') and getattr(cls, name) is not getattr(owner, name):
            raise RuntimeError('Adapter replaced an original business test: ' + name)
    stream = io.StringIO()
    result_class = unittest.TextTestResult if args.suite in ('coop', 'cards') else adapter.recovery.EvidenceResult
    executed = []

    class SuiteResult(result_class):
        def startTest(self, test):
            executed.append(test._testMethodName)
            super().startTest(test)

    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=SuiteResult, failfast=False).run(
        unittest.TestSuite(cls(name) for name in names))
    (out / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    commands = cards.COMMANDS if args.suite == 'cards' else adapter.delivery.COMMANDS
    artifacts = cards.ARTIFACTS if args.suite == 'cards' else adapter.delivery.ARTIFACTS
    compressed(out / 'commands.json.gz', commands)
    compressed(out / 'artifacts.json.gz', artifacts)
    compressed(out / 'assertions.json.gz', adapter.recovery.ASSERTIONS)
    states = [Path(a['root']) / 'state' if args.suite == 'cards' else Path(a['state']) for a in artifacts]
    leftovers = [str(p) for state in states for p in (state / 'daemon.pid', state / 'control.sock') if p.exists()]
    with tarfile.open(out / 'fixtures.tar.gz', 'x:gz') as archive:
        archive.add(fixtures, arcname=fixtures.name)
    large = [str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
    passed = (result.wasSuccessful() and result.testsRun == COUNTS[args.suite] and executed == names
              and not result.skipped and not leftovers and not large)
    record = {'status': 'PASS' if passed else 'INCOMPLETE', 'suite': args.suite,
        'revision': head, 'argv': sys.argv, 'tests_run': result.testsRun, 'expected_tests': COUNTS[args.suite],
        'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
        'failure_text': [{'test': t.id(), 'traceback': text} for t, text in result.failures],
        'error_text': [{'test': t.id(), 'traceback': text} for t, text in result.errors],
        'original_methods': names, 'executed_methods': executed,
        'unexecuted_methods': [name for name in names if name not in executed], 'failfast': False,
        'no_business_test_overrides': True, 'artifact_root': str(fixtures),
        'collection_errors': leftovers, 'files_over_5mb': large, 'real_codex_turns': 0}
    save(out / 'run.json', record)
    print(json.dumps({k: record[k] for k in ('status', 'suite', 'tests_run', 'failures', 'errors', 'skipped')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
