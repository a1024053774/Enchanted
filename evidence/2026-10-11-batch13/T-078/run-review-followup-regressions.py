"""Run full 8/9/18, CAS, T075 card boundaries and three known-bad gate cases, serially."""
import argparse
import ast
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
SUITES = [('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1), ('cards', 15)]
BAD = {'fence': ('coop', 'test_identity_gates_and_revocation_reject_old_verified_attempt'),
       'cas': ('cas', 'test_external_write_between_read_and_cas_is_preserved'),
       'lock': ('recovery', 'test_live_verify_excludes_verify_and_integrate')}
PROTECTED = ['workbench', 'acceptance', 'scripts',
             str((BASE / 'prepare-09b-executable.py').relative_to(SOURCE)),
             str(Path(__file__).resolve().relative_to(SOURCE))]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()


def check_paths(out):
    assert out.parent == BASE and not out.exists()
    required = [SOURCE / 'workbench/tests' / name for name in
                ['run_s3_rebased_regression.py', 'prepare_daemon_mutants.py', 'daemon_acceptance_adapter.py',
                 'daemon_acceptance_host.ts', 'test_task_cards_e2e.py', 'test_cas_race.py']]
    required += [SOURCE / 'acceptance' / name for name in ['test_coop_e2e.py', 'test_recovery_e2e.py', 'test_run_e2e.py']]
    for path in required:
        assert path.is_file(), path
        if path.suffix == '.py': ast.parse(path.read_text(encoding='utf-8'))
    helper = ast.parse((SOURCE / 'workbench/tests/prepare_daemon_mutants.py').read_text(encoding='utf-8'))
    assignment = next(node for node in ast.walk(helper) if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == 'changes' for target in node.targets))
    changes = ast.literal_eval(assignment.value)
    core = (SOURCE / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
    assert all(core.count(before) == 1 for before, _ in changes.values())
    return required


def verify_mutant(folder, name, core, code):
    result = json.loads((folder / 'run.json').read_bytes())
    assert code == 1 and result['tests_run'] == 1 and result['failures'] > 0 and result['errors'] == result['skipped'] == 0
    artifacts = json.loads(gzip.decompress((folder / 'artifacts.json.gz').read_bytes()))
    loaded = [generation['host_ready']['gate'] for artifact in artifacts for generation in artifact['daemons']]
    assert loaded and all(path == str(core) for path in loaded)
    assertions = json.loads(gzip.decompress((folder / 'assertions.json.gz').read_bytes()))
    commands = json.loads(gzip.decompress((folder / 'commands.json.gz').read_bytes()))
    if name == 'fence':
        claims = [json.loads(item['stdout'])['attempt'] for item in commands if item.get('label') == 'coop:claim' and item.get('exit_code') == 0]
        violations = []
        for item in commands:
            if item.get('label') != 'coop:submit': continue
            argv = item['argv']; fence = int(argv[argv.index('--fence') + 1]); session = argv[argv.index('--session') + 1]
            if any(fence == claim['fence'] + 31 and session == claim['session_id'] for claim in claims):
                violations.append(json.loads(item['stdout']).get('ok') is True)
        assert any(violations), 'fence red must show the wrong fence was accepted'
    else:
        labels = {'CAS rejects a changed expected old value', 'CAS preserves the external writer reference'} if name == 'cas' else {
            'Live operation excludes concurrent verify', 'Live operation excludes concurrent integrate', 'Busy commands never start a second oracle'}
        assert any(item['claim'] in labels and item['pass'] is False for item in assertions)
        assert any(item.get('classification') == 'business-red' for item in result['original_results'])
    return {'status': 'PASS', 'expected_exit': 1, 'actual_exit': code,
            'business_assertion_rejected_mutant': True, 'errors': 0, 'loaded_core': str(core)}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true'); args = parser.parse_args()
    out = args.output.resolve(); required = check_paths(out)
    if args.check_only:
        print(json.dumps({'status': 'PASS', 'scope': 'paths, syntax, mutation sites only; no runtime tests',
              'required_inputs': [str(path) for path in required], 'suites': SUITES, 'mutants': BAD,
              'new_processes': 0, 'real_model_turns': 0})); return 0
    freeze = json.loads((BASE / 'review-followup-source.json').read_bytes()); head = git('rev-parse', 'HEAD')
    subprocess.run(['git', 'merge-base', '--is-ancestor', freeze['revision'], head], cwd=SOURCE, check=True)
    assert not git('diff', freeze['revision'], '--', *PROTECTED), 'Frozen source changed'
    assert not git('ls-files', '--others', '--exclude-standard', '--', 'workbench', 'acceptance', 'scripts')
    assert not git('diff', 'dedd4f66bc424610183cbff2d7114e991483e1c6', '--', 'workbench/src', 'workbench/app')
    assert Path('/Volumes/WD-Elements').is_mount(), 'External build disk required'
    out.mkdir(exist_ok=False)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'COOP_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'revision': head, 'business_revision': freeze['business_revision'],
              'real_model_turns': 0, 'vendor_CLI_sessions': 0, 'stages': []}
    def save(): (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    def run(argv, name, timeout=900):
        row = {'name': name, 'argv': list(map(str, argv)), 'timeout_seconds': timeout, 'status': 'INCOMPLETE'}
        record['stages'].append(row); save()
        with (out / (name + '.stdout.bin')).open('xb') as stdout, (out / (name + '.stderr.bin')).open('xb') as stderr:
            child = subprocess.Popen(row['argv'], cwd=SOURCE, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            row.update(pid=child.pid, started_at=time.time()); save()
            # On timeout retain the detached harness/fixture identities; no blind signal or retry.
            code = child.wait(timeout=timeout)
        row['exit_code'] = code; save(); return row, code
    save()
    try:
        entry = SOURCE / 'workbench/tests/run_s3_rebased_regression.py'
        for suite, count in SUITES:
            row, code = run([sys.executable, '-B', entry, '--suite', suite, '--revision', head, '--output', out / suite], suite)
            result = json.loads((out / suite / 'run.json').read_bytes())
            assert code == 0 and result['status'] == 'PASS' and result['tests_run'] == count
            assert result['failures'] == result['errors'] == result['skipped'] == 0
            assert not result['unexecuted_methods'] and not result['collection_errors']
            row['status'] = 'PASS'; save()
        spec = importlib.util.spec_from_file_location('original_T075_mutations', SOURCE / 'workbench/tests/prepare_daemon_mutants.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        manifest_path = helper.prepare(out / 'mutants', task='T-078-review-followup-F4')
        manifest = json.loads(manifest_path.read_bytes())
        record['mutation_source_fixture'] = manifest['root']; save()
        for name, (suite, case) in BAD.items():
            core = Path(manifest['mutants'][name]['core']); folder = out / ('mutant-' + name)
            row, code = run([sys.executable, '-B', entry, '--suite', suite, '--revision', head, '--case', case, '--mutant-core', core, '--output', folder], 'mutant-' + name)
            row['verdict'] = verify_mutant(folder, name, core, code); row['status'] = 'PASS'; save()
        assert git('rev-parse', 'HEAD') == head and not git('diff', freeze['revision'], '--', *PROTECTED)
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc(), retry=False)
    save(); print(json.dumps({'status': record['status'], 'output': str(out), 'error': record.get('error')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
