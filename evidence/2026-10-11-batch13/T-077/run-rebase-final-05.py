#!/usr/bin/env python3
"""Controller-only frozen S3/T-076 joint phase. No real model execution."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
E = ROOT / 'evidence/2026-10-11-batch13/T-077'
REVISION = '5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4'
HARNESS_REVISION = 'be91b3c047195e23fff0e1d6fd68e82ab63bf72f'
REVIEW_PREIMAGE = '7b3463c4a55381d0fb97f782e69cc0029522f6da'
PREP = E / 'rebase-final-05-preparation-01'
OUT = E / 'outside-rebase-final-05'
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog
from test_s3_quality_joint_e2e import CASES as JOINT
from test_review_worktree_lifecycle_e2e import CASES as REVIEW_CASES
from test_worktree_lifecycle_e2e import CASES as S3

CONFLICTS = [name for _, name in S3 if name.startswith('test_conflict_') or name == 'test_merge_command_error_is_not_text_conflict']
RECIPES = {
    'same-c-new-review': (
        'if (task.review?.state === "passed" && task.review.candidate_commit === v.C) {',
        'if (false && task.review?.state === "passed" && task.review.candidate_commit === v.C) {'),
    'new-c-old-review': (
        'await this.requestReview(task, attempt);',
        'if (task.review?.state === "passed") { task.state = "verified"; this.save(task, "test_mutant_old_review", { task }); } else await this.requestReview(task, attempt);'),
    'rework-quality-not-authorized': (
        'const reworkSubmission = repairing || Boolean(task.repair && !task.repair.stopped &&\n'
        '          task.repair.candidate_commit === task.candidate_commit && attempt.rework?.state === "submitted");',
        'const reworkSubmission = repairing;'),
    'no-conflict-feedback': ('await this.writeConflict(task, attempt, v);', '// Test mutant: omit conflict worker handoff.'),
    'io-as-text-conflict': (
        'if (merge.returncode !== 1 || !unmerged.stdout) throw new Refusal("git_failed", merge);',
        'if (merge.returncode !== 1 || !unmerged.stdout) throw new Refusal("merge_conflict", v);'),
}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def guard():
    checkout = git('rev-parse', 'HEAD').decode().strip()
    ancestry = subprocess.run(['git', 'merge-base', '--is-ancestor', HARNESS_REVISION, checkout], cwd=ROOT, capture_output=True)
    if ancestry.returncode: raise RuntimeError('Checkout is not descended from the frozen harness')
    changed = git('diff', '--name-only', '-z', HARNESS_REVISION, checkout).decode().split(chr(0))
    evidence_prefix = str(E.relative_to(ROOT)) + '/'
    if any(name and not name.startswith(evidence_prefix) for name in changed):
        raise RuntimeError('Only this ticket evidence commits may follow the frozen harness')
    if git('branch', '--show-current').decode().strip() != 'exec/t077': raise RuntimeError('Wrong worker branch')
    for kind in ('rebase-merge', 'rebase-apply'):
        if Path(git('rev-parse', '--git-path', kind).decode().strip()).exists(): raise RuntimeError('Rebase is still active')
    approved_fixtures = {'workbench/tests/daemon_acceptance_adapter.py', 'workbench/tests/run_s3_rebased_regression.py',
                         'workbench/tests/test_relay_conflict_e2e.py'}
    fixture_delta = git('diff', '--name-only', '-z', REVISION, HARNESS_REVISION).decode().split(chr(0))
    if any(name and name not in approved_fixtures and not name.startswith(evidence_prefix) for name in fixture_delta):
        raise RuntimeError('Frozen fixture revision contains an unapproved change')
    for folder in ('workbench/src', 'workbench/hooks', 'workbench/README.md', 'acceptance'):
        if git('diff', REVISION, '--', folder): raise RuntimeError('Frozen product or acceptance changed: ' + folder)
    if git('diff', HARNESS_REVISION, '--', 'workbench/tests'):
        raise RuntimeError('Frozen harness changed: workbench/tests')
    if not os.path.ismount('/Volumes/WD-Elements'): raise RuntimeError('Required external dependency disk is not mounted')


def source_files():
    paths = []
    for folder in ('workbench/src', 'workbench/hooks', 'workbench/tests', 'acceptance', 'fixtures/pagination'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(ROOT / name for name in ('workbench/package.json', 'workbench/package-lock.json',
        '.project-map/tickets/T-077-worktree-lifecycle-conflicts.md',
        '.project-map/specs/native-cli-orchestration-2026-10-10.md'))
    paths.extend([Path(__file__).resolve(), E / 'outside-sandbox.sh', E / 'controlled-trailer-input.json', E / 'check-relay-mutants.py'])
    paths.extend(E / name for name in ('preflight-final-05.py', 'preflight-boundaries-05.py',
        'probe-fixture-helpers-05.py', 'final05-preflight-complete/run.json',
        'final05-helpers-after/run.json', 'final05-boundaries-before/run.json', 'final05-boundaries-completion/run.json'))
    return sorted(set(paths))


def verify_snapshot():
    with tarfile.open(PREP / 'frozen-source-and-harness.tar.gz', 'r:gz') as archive:
        for item in archive.getmembers():
            if item.isfile() and archive.extractfile(item).read() != (ROOT / item.name).read_bytes():
                raise RuntimeError('Prepared source or harness changed: ' + item.name)


def large_files(path):
    return [str(p) for p in path.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]


def prepare():
    guard(); PREP.mkdir(parents=True, exist_ok=False)
    if (len(JOINT), len(S3), len(CONFLICTS), len(REVIEW_CASES)) != (3, 25, 7, 4): raise RuntimeError('Approved suite membership changed')
    core = (ROOT / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
    counts = {name: core.count(before) for name, (before, _) in RECIPES.items()}
    if set(counts.values()) != {1}: raise RuntimeError('Mutation target is not unique: ' + repr(counts))
    with tarfile.open(PREP / 'frozen-source-and-harness.tar.gz', 'x:gz') as archive:
        for path in source_files(): archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    report = {'status': 'READY', 'business_status': 'INCOMPLETE: outside phase not run', 'planned_subphases': 39,
        'revision': REVISION, 'harness_revision': HARNESS_REVISION, 'checkout_revision': git('rev-parse', 'HEAD').decode().strip(), 'real_codex_turns': 0, 'joint_cases': JOINT, 'review_lifecycle_cases': REVIEW_CASES, 'review_preimage': REVIEW_PREIMAGE,
        'joint_red_failure_ids': ['JOINT-SAME-C-REUSE', 'JOINT-NEW-C-REVIEW', 'JOINT-CONFLICT-QUALITY-SUBMIT'],
        'mutation_target_counts': counts, 'conflict_cases': CONFLICTS,
        'preflight': {'classes': 8, 'selected_cases': 52, 'explicit_call_bindings': 1170,
                      'scope': 'fixture resolution and offline boundaries only; dispatch-state real ps remains outside',
                      'source': 'DIAGNOSIS-rebase-final-04.md'},
        'review_worktree_issue': '20261014T023857Z-worker:s13-t077s-issue-001; implementation candidate, acceptance pending',
        's3_expected': len(S3), 'legacy_expected': {'coop': 8, 'recovery': 9, 'run': 18, 'cas': 1, 'cards': 15},
        'files': [str(path.relative_to(ROOT)) for path in source_files()],
        'test_diff': git('diff', 'HEAD', '--', 'workbench/tests').decode(),
        'command': ['bash', str(E / 'outside-sandbox.sh'), 'rebase-final-05'],
        'files_over_5mb': large_files(PREP)}
    if report['files_over_5mb']: raise RuntimeError('Controller archive required: ' + repr(report['files_over_5mb']))
    save(PREP / 'plan.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'revision', 'real_codex_turns', 's3_expected')}))


def run():
    guard(); verify_snapshot(); OUT.mkdir(parents=True, exist_ok=False)
    checkout_revision = git('rev-parse', 'HEAD').decode().strip()
    log = CommandLog(OUT)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'revision': REVISION, 'harness_revision': HARNESS_REVISION, 'checkout_revision': checkout_revision, 'real_codex_turns': 0, 'argv': sys.argv,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'steps': [], 'mutation_recipes': {},
              'scope': 'Frozen S3 and T-076 controlled entry checks; no model, GUI or fresh-context review',
              'review_worktree_issue': '20261014T023857Z-worker:s13-t077s-issue-001; implementation candidate, acceptance pending'}
    workspace = Path(tempfile.mkdtemp(prefix='t77final-', dir='/tmp')).resolve()
    fixtures = []
    try:
        version = log.run(['node', '--version'], cwd=ROOT, env=env)
        if version.returncode or not version.stdout.startswith('v26.5.'): raise RuntimeError('Approved Node 26.5 is required')

        def child(name, argv, filename='run.json', expected_exit=0, verdict='pass'):
            guard(); verify_snapshot()
            if git('rev-parse', 'HEAD').decode().strip() != checkout_revision: raise RuntimeError('Checkout changed during the phase')
            result = log.run(argv, cwd=ROOT, env=env, timeout=None,
                stdout_file=OUT / (name + '.stdout.txt'), stderr_file=OUT / (name + '.stderr.txt'))
            path = OUT / name / filename
            value = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None
            step = {'name': name, 'argv': list(map(str, argv)), 'exit': result.returncode,
                    'expected_exit': expected_exit, 'verdict': verdict, 'result': str(path)}
            record['steps'].append(step); save(OUT / (name + '.receipt.json'), step)
            print(json.dumps({'step': name, 'exit': result.returncode, 'report': str(path)}), flush=True)
            if value and value.get('artifact_root'): fixtures.append(Path(value['artifact_root']))
            oversized = large_files(OUT)
            if oversized: raise RuntimeError('File exceeds 5 MB; stop for controller archive: ' + repr(oversized))
            if result.returncode != expected_exit or value is None: raise RuntimeError('Child failed; preserve without retry: ' + name)
            if verdict == 'pass' and value.get('status', 'PASS' if value.get('failure') is None else 'INCOMPLETE') != 'PASS':
                raise RuntimeError('Candidate phase did not pass: ' + name)
            guard(); verify_snapshot()
            if git('rev-parse', 'HEAD').decode().strip() != checkout_revision: raise RuntimeError('Checkout changed during the phase')
            return value

        def clone(name):
            target = workspace / name
            for folder in ('workbench', 'acceptance', 'fixtures'):
                shutil.copytree(ROOT / folder, target / folder, symlinks=True,
                    ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
            (target / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
            return target

        def mutant(name, recipe):
            target = clone(name)
            core = target / 'workbench/src/gates/core.ts'; source = core.read_text(encoding='utf-8')
            before, after = RECIPES[recipe]
            if source.count(before) != 1: raise RuntimeError('Mutation target changed: ' + recipe)
            core.write_text(source.replace(before, after, 1), encoding='utf-8')
            record['mutation_recipes'][name] = {'root': str(target), 'file': 'workbench/src/gates/core.ts',
                'before': before, 'after': after, 'source_committed': False}
            syntax = log.run(['node', '--check', core], cwd=ROOT, env=env)
            if syntax.returncode: raise RuntimeError('Mutation is a syntax error, not business evidence: ' + recipe)
            return target

        # Fresh real-entry counterfactuals use the committed pre-fix product,
        # with the current unchanged external-actor harness and no state edits.
        child('driver-readiness', [sys.executable, '-B', ROOT / 'workbench/tests/test_legacy_driver_readiness.py',
              '--output', OUT / 'driver-readiness'])
        preimage = clone('review-lifecycle-preimage')
        archive_path = workspace / 'review-preimage.tar'
        argv = ['git', 'archive', REVIEW_PREIMAGE, 'workbench/src', 'workbench/hooks',
                'workbench/package.json', 'workbench/package-lock.json']
        archived = log.run(argv, cwd=ROOT, env=env, timeout=None, stdout_file=archive_path)
        if archived.returncode: raise RuntimeError('Cannot reconstruct committed review preimage')
        with tarfile.open(archive_path, 'r:') as archive:
            for member in archive.getmembers():
                if member.isdir(): continue
                if member.name.startswith('/') or '..' in Path(member.name).parts:
                    raise RuntimeError('Unexpected preimage archive entry')
                target = preimage / member.name
                if member.issym() and Path(member.name).parent == Path('workbench/hooks') and member.linkname == 'hook.py':
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.is_symlink(): target.unlink()
                    target.symlink_to(member.linkname)
                    continue
                if not member.isfile():
                    raise RuntimeError('Unexpected preimage archive entry')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
                target.chmod(member.mode)
        record['review_preimage'] = {'revision': REVIEW_PREIMAGE, 'root': str(preimage),
            'command': list(map(str, argv)), 'temporary_copy_committed': False}
        review_script = ROOT / 'workbench/tests/test_review_worktree_lifecycle_e2e.py'
        failures = ['REVIEW-DIRECTORY-REMOVED', 'REVIEW-S3-NAMES', 'REVIEW-DIRTY-PRESERVED', 'REVIEW-UNKNOWN-HEAD-PRESERVED']
        for index, (case, failure) in enumerate(zip(REVIEW_CASES, failures), 1):
            phase = 'review-lifecycle-red-%02d' % index
            value = child(phase, [sys.executable, '-B', review_script, '--source', preimage, '--case', case,
                '--output', OUT / phase], expected_exit=1, verdict='business-red')
            rows = value['cases']
            if len(rows) != 1 or rows[0]['outcome'] != 'contract_failure' or rows[0].get('failure_id') != failure or rows[0]['cleanup_failures']:
                raise RuntimeError('Review preimage failed outside the intended contract: ' + case)
        child('review-lifecycle-candidate', [sys.executable, '-B', review_script, '--source', ROOT,
              '--output', OUT / 'review-lifecycle-candidate'])

        joint_script = ROOT / 'workbench/tests/test_s3_quality_joint_e2e.py'
        for name, case, failure in zip(['same-c-new-review', 'new-c-old-review', 'rework-quality-not-authorized'],
                JOINT, ['JOINT-SAME-C-REUSE', 'JOINT-NEW-C-REVIEW', 'JOINT-CONFLICT-QUALITY-SUBMIT']):
            target = mutant(name, name); phase = 'joint-red-' + name
            value = child(phase, [sys.executable, '-B', joint_script, '--source', target, '--case', case,
                '--output', OUT / phase], expected_exit=1, verdict='business-red')
            rows = value['cases']
            if len(rows) != 1 or rows[0]['outcome'] != 'contract_failure' or rows[0].get('failure_id') != failure or rows[0]['cleanup_failures']:
                raise RuntimeError('Joint counterfactual did not fail at its specified contract: ' + name)

        # Text conflict and command-error classification get distinct known-bad
        # variants; every one of the seven existing contracts must reach red.
        no_feedback = mutant('no-conflict-feedback', 'no-conflict-feedback')
        wrong_error = mutant('io-as-text-conflict', 'io-as-text-conflict')
        for index, case in enumerate(CONFLICTS, 1):
            phase = 'conflict-red-%02d' % index
            target = wrong_error if case == 'test_merge_command_error_is_not_text_conflict' else no_feedback
            value = child(phase, [sys.executable, '-B', ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py',
                '--phase', 'baseline', '--mutant-product', target, '--case', case, '--output', OUT / phase], verdict='business-red')
            if value['red_confirmed'] is not True or len(value['cases']) != 1 or value['cases'][0]['errors']:
                raise RuntimeError('Conflict counterfactual is not business red: ' + case)

        child('joint-candidate', [sys.executable, '-B', joint_script, '--source', ROOT, '--output', OUT / 'joint-candidate'])
        child('s3-all', [sys.executable, '-B', ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py',
            '--phase', 'candidate', '--output', OUT / 's3-all'])
        for suite, expected_count in (('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1), ('cards', 15)):
            value = child(suite, [sys.executable, '-B', ROOT / 'workbench/tests/run_s3_rebased_regression.py',
                '--suite', suite, '--revision', checkout_revision, '--output', OUT / suite])
            if (value['tests_run'] != expected_count or len(value['original_methods']) != expected_count
                    or value['executed_methods'] != value['original_methods']
                    or value['unexecuted_methods'] or value['failfast'] is not False):
                raise RuntimeError('Regression suite did not execute every required method: ' + suite)
        for name, script, extra in [
            ('relay-conflict', 'test_relay_conflict_e2e.py', ['--source', ROOT]),
            ('controlled-trailer-candidate', 'test_conflict_trailer_proofs.py',
             ['--source', ROOT, '--case', 'both', '--input', E / 'controlled-trailer-input.json']),
            ('identity', 'test_multiturn_identity_e2e.py', ['--source', ROOT, '--case', 'all', '--check-consistency']),
            ('shutdown', 'test_startup_shutdown_e2e.py', ['--source', ROOT]),
            ('t076-final-tracer', 'test_quality_tracer_e2e.py', ['--source', ROOT]),
            ('t076-final-wide', 'test_quality_widen_e2e.py', ['--source', ROOT, '--group', 'wide']),
            ('t076-final-review-faults', 'test_quality_widen_e2e.py', ['--source', ROOT, '--group', 'review-red']),
            ('t076-final-controls', 'test_quality_chain_e2e.py', ['--source', ROOT, '--group', 'controls', '--card-dialect', 'current']),
            ('t076-final-provenance', 'test_quality_legacy_e2e.py', ['--source', ROOT]),
        ]:
            child(name, [sys.executable, '-B', ROOT / 'workbench/tests' / script, *extra, '--output', OUT / name])
        child('relay-core', ['node', ROOT / 'workbench/tests/test_relay_core.ts', OUT / 'relay-core'], 'results.json')
        child('relay-cli', [sys.executable, '-B', ROOT / 'workbench/tests/test_relay_cli.py', '--output', OUT / 'relay-cli'], 'results.json')
        child('relay-scope', ['node', ROOT / 'workbench/tests/test_relay_scope.ts', ROOT / 'workbench/src/relay.ts', OUT / 'relay-scope'])
        child('relay-global-mutant', [sys.executable, '-B', E / 'check-relay-mutants.py', '--mutant', 'global-lookup',
              '--output', OUT / 'relay-global-mutant'])
        for name, script in [('native-final', 'test_native_final_read.ts'), ('dispatch-state', 'test_pane_dispatch_state.ts')]:
            child(name, ['node', ROOT / 'workbench/tests' / script, OUT / name], 'results.json')
        panes = log.run(['node', ROOT / 'workbench/tests/test_conflict_panes.ts', '--product', ROOT,
                        '--output', OUT / 'panes.json'], cwd=ROOT, env=env, timeout=None)
        record['steps'].append({'name': 'panes', 'exit': panes.returncode, 'result': str(OUT / 'panes.json')})
        if panes.returncode: raise RuntimeError('Pane lifecycle contract failed')
        if len(record['steps']) != 39: raise RuntimeError('The required complete phase membership changed')
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        # Archive only runtime scenes. Temporary mutant source is retained in
        # /tmp and reproducible from recipes, never added to repository evidence.
        for index, fixture in enumerate(dict.fromkeys(fixtures)):
            target = OUT / ('runtime-fixture-%02d.tar.gz' % index)
            try:
                with tarfile.open(target, 'x:gz') as archive: archive.add(fixture, arcname=fixture.name)
                if target.stat().st_size > 5 * 1024 * 1024:
                    record.update(status='INCOMPLETE', archive_required=str(target)); break
            except Exception as error:
                record.update(status='INCOMPLETE', archive_error=repr(error)); break
        record['files_over_5mb'] = large_files(OUT)
        if record['files_over_5mb']: record.update(status='INCOMPLETE', archive_required=True)
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(OUT / 'run.json', record)
        print(json.dumps({k: record[k] for k in ('status', 'revision', 'real_codex_turns', 'files_over_5mb')}), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if args.prepare_only: prepare()
    else: raise SystemExit(run())
