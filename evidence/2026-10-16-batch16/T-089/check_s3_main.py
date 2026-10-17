#!/usr/bin/env python3
"""真实 S3 main() 对照；隔离路径、审计替换及强制产物均在测试驱动中。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
BASE = 'c544b29049861998e11eeb7344b457103fab3c98'
OLD_ARCHIVE = '/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077'
EXTERNAL = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write('\n')


def drive(request):
    checkout = Path(request['checkout'])
    area = Path(request['area'])
    sys.path.insert(0, str(checkout / 'workbench/tests'))
    import run_s3_regression as runner
    trace = {'main': str(checkout / 'workbench/tests/run_s3_regression.py'),
             'archive_call_wrapped': False, 'path_redirects': [], 'forced_output': []}

    def scoped_audit(base):
        if base != BASE:
            raise ValueError('Unexpected frozen baseline')
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--',
                                         'acceptance', 'workbench/tests'], cwd=checkout, text=True).splitlines()
        changed = []
        for name in names:
            if name == 'workbench/tests/run_s3_regression.py':
                continue  # The explicitly reviewed call-site change is under test.
            original = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=checkout)
            if (checkout / name).read_bytes() != original:
                changed.append(name)
        return {'status': 'NO_GO' if changed else 'PASS', 'base': BASE,
                'replacement': 'test driver only; old pre-T-076 coordinates cannot audit this merged revision',
                'protected_source_changes': changed,
                'rule': 'acceptance and all existing test helpers except the runner equal the frozen baseline'}

    runner.audit.audit_checkout = scoped_audit
    # Keep the actual self_check(), preflight, snapshot, original CAS method,
    # collection, archive call and final summary generation unchanged.
    runner.EVIDENCE = area / 'output'
    runner.EVIDENCE.mkdir()
    archive_base = area / 'archive'

    def isolated_path(value, *rest):
        if str(value) == OLD_ARCHIVE:
            trace['path_redirects'].append({'requested': str(value), 'mapped': str(archive_base)})
            return archive_base.joinpath(*rest)
        path = Path(value, *rest)
        if str(path).startswith('/Volumes/WD-Elements/a2a-evidence/') and area not in [path, *path.parents]:
            raise ValueError('Test driver refuses a destination outside this new test area: ' + str(path))
        return path

    runner.Path = isolated_path
    original_finish = runner.finish_evidence

    def forced_output(out, fixture_root, artifacts):
        result = original_finish(out, fixture_root, artifacts)
        for name in ('forced-large.dat', 'retained-small.bin'):
            shutil.copyfile(Path(request['fixtures']) / name, out / name)
            trace['forced_output'].append(str(out / name))
        return result

    runner.finish_evidence = forced_output
    sys.argv = [str(checkout / 'workbench/tests/run_s3_regression.py'), '--suite', 'cas',
                '--base', BASE, '--output', str(runner.EVIDENCE / 'cas')]
    trace['argv'] = list(sys.argv)
    try:
        return runner.main()
    finally:
        save(area / 'driver.json', trace)


def checkout_for(phase, env):
    parent = Path(tempfile.mkdtemp(prefix='t089-main-', dir='/tmp'))
    checkout = parent / 'repo'
    subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(ROOT), str(checkout)],
                   env=env, check=True, capture_output=True)
    subprocess.run(['git', '-C', str(checkout), 'config', 'core.sparseCheckout', 'true'], env=env, check=True)
    patterns = ['/workbench/', '/acceptance/', '/scripts/', '/.project-map/', '/fixtures/']
    patterns += ['/evidence/2026-10-11-batch13/T-077/' + name for name in
                 ('PLAN.md', 'controller-decision-01.md', 'controller-decision-02.md', 'outside-sandbox.sh')]
    (checkout / '.git/info/sparse-checkout').write_text('\n'.join(patterns) + '\n', encoding='utf-8')
    subprocess.run(['git', '-C', str(checkout), 'checkout', '--detach', BASE], env=env, check=True, capture_output=True)
    if phase != 'baseline':
        for name in ('run_s3_regression.py', 'archive_evidence.py'):
            shutil.copyfile(ROOT / 'workbench/tests' / name, checkout / 'workbench/tests' / name)
    if phase.endswith('mutant'):
        path = checkout / 'workbench/tests/run_s3_regression.py'
        text = path.read_text(encoding='utf-8')
        before, after = (('minimum_bytes=5 * 1024 * 1024', 'minimum_bytes=6 * 1024 * 1024')
                         if phase == 'threshold-mutant' else
                         ("/ out.name,", "/ (out.name + '-wrong'),"))
        if text.count(before) != 1:
            raise RuntimeError('Mutation site is not unique')
        path.write_text(text.replace(before, after, 1), encoding='utf-8')
    dependencies = Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules')
    if not dependencies.is_dir():
        raise RuntimeError('Existing dependencies unavailable; do not install')
    (checkout / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
    return checkout.resolve()


def oracle(area, fixtures):
    out = area / 'output/cas'
    summary = json.loads((out / 'run.json').read_text(encoding='utf-8'))
    assert summary['status'] == 'PASS' and summary['tests_run'] == 1
    assert summary['failures'] == summary['errors'] == summary['skipped'] == 0
    assert summary['selected_original_methods'] == ['test_external_write_between_read_and_cas_is_preserved']
    assert not (out / 'forced-large.dat').exists(), 'actual main used the wrong archive threshold'
    assert (out / 'retained-small.bin').read_bytes() == (fixtures / 'retained-small.bin').read_bytes()
    target = area / 'archive/cas/forced-large.dat'
    assert target.read_bytes() == (fixtures / 'forced-large.dat').read_bytes(), 'actual main used the wrong target'
    manifest = json.loads((out / 'forced-large.dat.archive.json').read_text(encoding='utf-8'))
    assert manifest['original'] == str(out / 'forced-large.dat')
    assert manifest['archive'] == str(target) and manifest['bytes'] == target.stat().st_size
    matches = [entry for entry in summary['external_archives'] if entry['original'] == str(out / 'forced-large.dat')]
    assert matches == [manifest], 'summary external_archives must contain the actual manifest'
    assert not any(entry['original'] == str(out / 'retained-small.bin') for entry in summary['external_archives'])
    assert manifest['replay'] == ['python3', '-B', *summary['argv']]
    trace = json.loads((area / 'driver.json').read_text(encoding='utf-8'))
    assert trace['archive_call_wrapped'] is False and trace['path_redirects']
    assert all(row == {'requested': OLD_ARCHIVE, 'mapped': str(area / 'archive')}
               for row in trace['path_redirects'])
    return {'status': 'PASS', 'tests_run': 1, 'moved_bytes': manifest['bytes'],
            'retained_bytes': (out / 'retained-small.bin').stat().st_size,
            'manifest': manifest, 'main': trace['main']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not os.path.ismount('/Volumes/WD-Elements'):
        raise RuntimeError('External volume not mounted; no fallback')
    area = Path(tempfile.mkdtemp(prefix='s3-main-02-', dir=EXTERNAL))
    fixtures = area / 'inputs'
    fixtures.mkdir()
    nonce = uuid.uuid4().hex.encode('ascii')
    (fixtures / 'forced-large.dat').write_bytes(bytes(range(256)) * 20480 + nonce)
    (fixtures / 'retained-small.bin').write_bytes(b'k' * (5 * 1024 * 1024))
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_'))}
    rows = []
    for phase in ('baseline', 'candidate', 'threshold-mutant', 'destination-mutant'):
        checkout = checkout_for(phase, env)
        target = area / phase
        target.mkdir()
        request = {'checkout': str(checkout), 'area': str(target), 'fixtures': str(fixtures)}
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), '--drive']
        p = subprocess.run(argv, input=json.dumps(request), cwd=checkout, env=env,
                           capture_output=True, text=True, timeout=300, start_new_session=True)
        command = {'argv': argv, 'request': request, 'cwd': str(checkout),
                   'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
        save(target / 'command.json', command)
        verdict = None
        try:
            if p.returncode:
                raise RuntimeError('actual main failed: ' + p.stderr)
            verdict = oracle(target, fixtures)
            accepted = not phase.endswith('mutant')
        except (AssertionError, OSError, ValueError, KeyError, RuntimeError) as error:
            verdict = {'status': 'NO_GO', 'error': repr(error)}
            accepted = p.returncode == 0 and (
                (phase == 'threshold-mutant' and isinstance(error, AssertionError) and 'threshold' in str(error))
                or (phase == 'destination-mutant' and isinstance(error, FileNotFoundError)
                    and error.filename == str(target / 'archive/cas/forced-large.dat')))
        save(target / 'oracle.json', verdict)
        rows.append({'phase': phase, 'main_exit_code': p.returncode, 'accepted': accepted,
                     'oracle': verdict, 'command': str(target / 'command.json')})
    result = {'status': 'PASS' if all(row['accepted'] for row in rows) else 'INCOMPLETE',
              'base': BASE, 'external_area': str(area), 'cases': rows,
              'substitutions': ['audit_checkout validates frozen source instead of old coordinates',
                                'runner.EVIDENCE and runner.Path redirect output and only the fixed T-077 root',
                                'finish_evidence calls its original function and adds two independent fixture files'],
              'not_replaced': ['main()', 'archive_large_files call or arguments', 'original CAS method',
                               'audit self_check', 'summary generation'],
              'real_codex_turns': 0}
    save(args.output, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    if sys.argv[1:] == ['--drive']:
        raise SystemExit(drive(json.load(sys.stdin)))
    raise SystemExit(main())
