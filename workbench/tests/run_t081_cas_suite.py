"""主控运行：复用原 CAS 竞争用例，串行证明去掉旧值比较先红、候选重验绿态。"""
import argparse
import difflib
import gzip
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest

from command_evidence import CommandLog

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/2026-10-14-batch14/T-081'
METHOD = 'test_external_write_between_read_and_cas_is_preserved'
CLAIM = 'CAS revalidation binds the new G and unchanged C'
LIMIT = 5_000_000


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def sizes(root):
    for path in root.rglob('*'):
        if path.is_file() and not path.is_symlink() and path.stat().st_size > LIMIT:
            raise RuntimeError('单文件超过 5 MB，停止并保留：' + str(path))


def phase(core, out):
    # Import after sanitizing inherited harness configuration. The adapter
    # supplies external workers/reviewers; the original business method runs.
    for key in list(os.environ):
        if key.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_')):
            del os.environ[key]
    import daemon_acceptance_adapter as adapter
    fixtures = Path(tempfile.mkdtemp(prefix='t81cas-', dir='/tmp')).resolve()
    (out / 'readbacks').mkdir()
    os.environ.update(COOP_E2E_ARTIFACT_ROOT=str(fixtures), COOP_E2E_TRACE=str(fixtures / 'trace.json'),
                      COOP_E2E_READBACK_ROOT=str(out / 'readbacks'),
                      COOP_E2E_MUTANT_CORE=str(core.resolve()), COOP_SCRIPT=str(adapter.ENTRY),
                      COOP_NATIVE_ENTRY=str(adapter.CLI))
    assert getattr(adapter.DaemonCAS, METHOD) is getattr(adapter.cas.CASRace, METHOD)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=adapter.recovery.EvidenceResult).run(
        unittest.TestSuite([adapter.DaemonCAS(METHOD)]))
    (out / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    for name, data in [('assertions', adapter.recovery.ASSERTIONS), ('commands', adapter.delivery.COMMANDS),
                       ('artifacts', adapter.delivery.ARTIFACTS)]:
        with gzip.open(out / (name + '.json.gz'), 'wt', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False)
    states = [Path(row['state']) for row in adapter.delivery.ARTIFACTS]
    leftovers = [str(path) for state in states for path in (state / 'control.sock', state / 'daemon.pid') if path.exists()]
    assertions = adapter.recovery.ASSERTIONS
    receipts = []
    for path in fixtures.rglob('*.result.json'):
        value = json.loads(path.read_text(encoding='utf-8'))
        if 'stdin' in value and 'argv' in value:
            receipts.append({'source': str(path), **value})
    failed = [row['claim'] for row in assertions if not row['pass']]
    outcome = 'passed' if result.wasSuccessful() else ('contract_failure' if result.failures and not result.errors and failed else 'harness_error')
    sizes(fixtures)
    with tarfile.open(out / 'fixtures.tar.gz', 'x:gz') as archive:
        archive.add(fixtures, arcname=fixtures.name)
    sizes(out)
    report = {'status': 'PASS' if outcome == 'passed' and not leftovers else 'INCOMPLETE',
              'outcome': outcome, 'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped), 'failed_claims': failed,
              'assertions': assertions, 'results': adapter.recovery.TEST_RESULTS,
              'git_transaction_receipts': receipts,
              'core': str(core), 'fixture_root': str(fixtures), 'leftover_endpoints': leftovers,
              'method': METHOD, 'no_business_test_overrides': True, 'real_codex_turns': 0}
    save(out / 'run.json', report)
    return 0 if report['status'] == 'PASS' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--phase', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--core', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    if args.phase:
        return phase(args.core, out)
    log = CommandLog(out)
    report = {'status': 'INCOMPLETE', 'real_codex_turns': 0, 'scope': 'T-081 第 7 项 CAS 受控补充',
              'full04_green': str(EVIDENCE / 'full-04/t075-cas/run.json'), 'steps': []}
    try:
        source = args.source.resolve()
        head = log.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
        if head.returncode:
            raise RuntimeError('无法记录代码版本。')
        report.update(code_revision=head.stdout.strip(), source=str(source))
        shutil.copyfile(Path(__file__), out / 'driver.py')
        shutil.copyfile(ROOT / 'workbench/tests/test_cas_race.py', out / 'frozen-business-case.py')
        # Freeze the public test before loading a mutant. Never edit its oracle.
        for name in ('workbench/tests/test_cas_race.py', 'acceptance/test_recovery_e2e.py'):
            result = log.run(['git', 'show', 'HEAD:' + name], cwd=ROOT)
            if result.returncode or result.stdout != (ROOT / name).read_text(encoding='utf-8'):
                raise RuntimeError('原有验收断言发生变化：' + name)
        fixture = Path(tempfile.mkdtemp(prefix='t81mut-', dir='/tmp')).resolve()
        mutant = fixture / 'mutant'
        for directory in ('src', 'hooks'):
            shutil.copytree(source / 'workbench' / directory, mutant / 'workbench' / directory, symlinks=True)
        shutil.copyfile(source / 'workbench/package.json', mutant / 'workbench/package.json')
        (mutant / 'workbench/node_modules').symlink_to((source / 'workbench/node_modules').resolve(), target_is_directory=True)
        original = (source / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
        before = 'await send(`update ${intent.integration_ref} ${intent.M} ${intent.G}\\nprepare\\n`, "prepare: ok");'
        after = 'await send(`update ${intent.integration_ref} ${intent.M}\\nprepare\\n`, "prepare: ok");'
        if original.count(before) != 1:
            raise RuntimeError('CAS 事务旧值比较的变异位置必须唯一。')
        changed = original.replace(before, after)
        (out / 'candidate-core.ts').write_text(original, encoding='utf-8')
        (out / 'mutant-core.ts').write_text(changed, encoding='utf-8')
        (mutant / 'workbench/src/gates/core.ts').write_text(changed, encoding='utf-8')
        (out / 'cas-old-value.patch').write_text(''.join(difflib.unified_diff(
            original.splitlines(True), changed.splitlines(True), fromfile='candidate/core.ts', tofile='cas-no-old-value/core.ts')), encoding='utf-8')
        sizes(mutant)
        env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_'))}
        for label, selected in [('red', mutant), ('green', source)]:
            destination = out / label
            result = log.run([sys.executable, '-B', Path(__file__).resolve(), '--phase',
                              '--core', selected / 'workbench/src/gates/core.ts', '--output', destination],
                             cwd=ROOT, env=env, timeout=240)
            data = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
            valid = data['tests_run'] == 1 and data['errors'] == data['skipped'] == 0 and not data['leftover_endpoints']
            writes = [line.split() for receipt in data['git_transaction_receipts'] for line in receipt['stdin'] if line.startswith('update ')]
            valid = valid and any(len(parts) == (3 if label == 'red' else 4) for parts in writes)
            if label == 'red':
                passed_claims = [row['claim'] for row in data['assertions'] if row['pass']]
                valid = valid and result.returncode == 1 and data['outcome'] == 'contract_failure' and CLAIM in data['failed_claims'] and 'Only the new complete verification accepts' in passed_claims
            else:
                valid = valid and result.returncode == 0 and data['status'] == 'PASS' and not data['failed_claims']
            report['steps'].append({'label': label, 'report': str(destination / 'run.json'), 'exit': result.returncode,
                                    'valid_evidence': valid, 'outcome': data['outcome'], 'failed_claims': data['failed_claims']})
            sizes(out)
            if not valid:
                raise RuntimeError('CAS 不是所需业务红态/重验绿态；停止，不把其他拒绝或 harness_error 算通过：' + label)
        report.update(status='PASS', mutant='只去掉真实 Git 事务 update 的旧值参数；预读比较不变',
                      oracle='原 CASRace 方法：新 G/C 绑定、外来提交与候选都是祖先、外来内容保留、oracle 再执行一次')
    except Exception as error:
        import traceback
        report.update(error=repr(error), traceback=traceback.format_exc())
    save(out / 'run.json', report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
