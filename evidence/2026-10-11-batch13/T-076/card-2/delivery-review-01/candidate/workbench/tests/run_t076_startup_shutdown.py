"""Freeze the current candidate for zero-model-turn startup/shutdown checks."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback

from command_evidence import CommandLog

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['red', 'green'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    commands = CommandLog(out)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_'))}
    record = {'status': 'INCOMPLETE', 'mode': args.mode, 'argv': sys.argv, 'real_codex_turns': 0, 'steps': []}
    captured = {}
    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk is not mounted; no cache fallback')
        version = commands.run(['node', '--version'], cwd=ROOT, env=env)
        if version.returncode or not version.stdout.strip().startswith('v26.5.'):
            raise RuntimeError('Approved Node 26.5 runtime is unavailable')
        source = Path(tempfile.mkdtemp(prefix='sd76-', dir='/tmp')).resolve() / 'source'
        shutil.copytree(ROOT / 'workbench', source / 'workbench', symlinks=True,
            ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
        (source / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        captured = {path: path.read_bytes() for part in ('src', 'hooks', 'tests')
                    for path in (ROOT / 'workbench' / part).rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
            archive.add(source / 'workbench', arcname='workbench')
        head = commands.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env).stdout.strip()
        record.update(source=str(source), head=head, code_is_uncommitted_candidate=True)
        expectations = [('initial-release', 'test_initial_worker_release.py', 4,
                         ['test_first_input_precedes_native_log']),
                        ('daemon-stop', 'test_startup_shutdown_e2e.py', 4,
                         ['test_stop_drains_existing_gate_before_final_event', 'test_stop_during_deadline_cleanup', 'test_stop_during_waiting_submit'])]
        for name, filename, count, red_methods in expectations:
            target = out / name
            result = commands.run([sys.executable, '-B', source / 'workbench/tests' / filename,
                '--source', source, '--output', target], cwd=ROOT, env=env, timeout=120,
                stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
            value = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            step = {'name': name, 'exit': result.returncode, 'result': str(target / 'run.json'),
                    'tests_run': value['tests_run'], 'failures': value['failures'], 'errors': value['errors']}
            record['steps'].append(step)
            if value['tests_run'] != count or value['errors'] or value['skipped']:
                raise RuntimeError('Fixture/environment error is not business evidence: ' + name)
            failures = sorted(item['test'].rsplit('.', 1)[-1] for item in value['failures'])
            expected = sorted(red_methods) if args.mode == 'red' else []
            if failures != expected or result.returncode != (1 if expected else 0):
                raise RuntimeError('Focused results do not match the required failure/pass set: ' + name)
        if args.mode == 'green':
            # Keep a counterfactual for the new shutdown ordering assertion.
            # Remove only the request-drain wait; all other candidate behavior
            # and the controlled gate barrier remain unchanged.
            mutant = source.parent / 'ordering-mutant'
            shutil.copytree(source / 'workbench', mutant / 'workbench', symlinks=True)
            daemon = mutant / 'workbench/src/daemon.ts'
            original = daemon.read_text(encoding='utf-8')
            before = '    if (activeRequests > 0) await new Promise<void>((resolve) => { requestsDrained = resolve; });\n'
            if original.count(before) != 1: raise RuntimeError('Ordering counterfactual site is ambiguous')
            daemon.write_text(original.replace(before, ''), encoding='utf-8')
            target = out / 'ordering-counterfactual'
            result = commands.run([sys.executable, '-B', source / 'workbench/tests/test_startup_shutdown_e2e.py',
                '--source', mutant, '--case', 'ordering', '--output', target], cwd=ROOT, env=env, timeout=60,
                stdout_file=out / 'ordering-counterfactual.stdout.txt', stderr_file=out / 'ordering-counterfactual.stderr.txt')
            value = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            witness = value['artifacts'][0].get('shutdown_precompletion')
            if (result.returncode != 1 or value['tests_run'] != 1 or len(value['failures']) != 1 or
                    value['errors'] or value['skipped'] or not witness or not witness['gate_still_held'] or
                    witness['violation'] != 'final_event_before_gate' or witness['creating_state'] != 'creating' or
                    witness['create_request_result_seq'] is not None or witness['daemon_stopped_seq'] is None):
                raise RuntimeError('Missing request-drain wait was not rejected at the event-order assertion')
            record['steps'].append({'name': 'ordering-counterfactual', 'exit': 1, 'result': str(target / 'run.json'),
                'shutdown_precompletion': witness, 'classification': 'business-red', 'mutation': before, 'source': str(mutant)})
            with tarfile.open(out / 'ordering-mutant-source.tar.gz', 'x:gz') as archive:
                archive.add(mutant / 'workbench', arcname='workbench')
            target = out / 'identity'
            result = commands.run([sys.executable, '-B', source / 'workbench/tests/test_multiturn_identity_e2e.py',
                '--source', source, '--case', 'all', '--output', target], cwd=ROOT, env=env, timeout=120,
                stdout_file=out / 'identity.stdout.txt', stderr_file=out / 'identity.stderr.txt')
            value = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            if result.returncode != 0 or (value['tests_run'], value['failures'], value['errors'], value['skipped']) != (4, 0, 0, 0):
                raise RuntimeError('Multiturn identity positive/foreign-owner cases did not all pass')
            record['steps'].append({'name': 'identity', 'exit': 0, 'tests_run': 4, 'result': str(target / 'run.json')})
        record['status'] = 'PASS'
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        changed = [str(path) for path, data in captured.items() if not path.is_file() or path.read_bytes() != data]
        record['changed_source_paths'] = changed
        if changed: record.update(status='INCOMPLETE', error='Candidate source changed during the focused run')
        with (out / 'run.json').open('x', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'mode': args.mode, 'real_codex_turns': 0}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
