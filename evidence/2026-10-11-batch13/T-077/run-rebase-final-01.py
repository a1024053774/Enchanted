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
REVISION = 'c3eb705cd8b8c949850c8483c861ddb9d7f87b89'
PREP = E / 'rebase-final-preparation-03'
OUT = E / 'outside-rebase-final-01'
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog
from test_s3_quality_joint_e2e import CASES as JOINT
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
    if git('rev-parse', 'HEAD').decode().strip() != REVISION: raise RuntimeError('Frozen HEAD changed')
    if git('branch', '--show-current').decode().strip() != 'exec/t077': raise RuntimeError('Wrong worker branch')
    for kind in ('rebase-merge', 'rebase-apply'):
        if Path(git('rev-parse', '--git-path', kind).decode().strip()).exists(): raise RuntimeError('Rebase is still active')
    for folder in ('workbench/src', 'workbench/hooks', 'acceptance'):
        if git('diff', 'HEAD', '--', folder): raise RuntimeError('Frozen product or acceptance changed: ' + folder)
    if not os.path.ismount('/Volumes/WD-Elements'): raise RuntimeError('Required external dependency disk is not mounted')


def source_files():
    paths = []
    for folder in ('workbench/src', 'workbench/hooks', 'workbench/tests', 'acceptance', 'fixtures/pagination'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(ROOT / name for name in ('workbench/package.json', 'workbench/package-lock.json',
        '.project-map/tickets/T-077-worktree-lifecycle-conflicts.md',
        '.project-map/specs/native-cli-orchestration-2026-10-10.md'))
    paths.extend([Path(__file__).resolve(), E / 'outside-sandbox.sh', E / 'controlled-trailer-input.json', E / 'check-relay-mutants.py'])
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
    if (len(JOINT), len(S3), len(CONFLICTS)) != (3, 25, 7): raise RuntimeError('Approved suite membership changed')
    core = (ROOT / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
    counts = {name: core.count(before) for name, (before, _) in RECIPES.items()}
    if set(counts.values()) != {1}: raise RuntimeError('Mutation target is not unique: ' + repr(counts))
    with tarfile.open(PREP / 'frozen-source-and-harness.tar.gz', 'x:gz') as archive:
        for path in source_files(): archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    report = {'status': 'READY', 'business_status': 'INCOMPLETE: outside phase not run',
        'revision': REVISION, 'real_codex_turns': 0, 'joint_cases': JOINT,
        'joint_red_failure_ids': ['JOINT-SAME-C-REUSE', 'JOINT-NEW-C-REVIEW', 'JOINT-CONFLICT-QUALITY-SUBMIT'],
        'mutation_target_counts': counts, 'conflict_cases': CONFLICTS,
        'open_handoff_issue': '20261014T023857Z-worker:s13-t077s-issue-001',
        's3_expected': len(S3), 'legacy_expected': {'coop': 8, 'recovery': 9, 'run': 18, 'cas': 1, 'cards': 15},
        'files': [str(path.relative_to(ROOT)) for path in source_files()],
        'test_diff': git('diff', 'HEAD', '--', 'workbench/tests').decode(),
        'command': ['bash', str(E / 'outside-sandbox.sh'), 'rebase-final-01'],
        'files_over_5mb': large_files(PREP)}
    if report['files_over_5mb']: raise RuntimeError('Controller archive required: ' + repr(report['files_over_5mb']))
    save(PREP / 'plan.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'revision', 'real_codex_turns', 's3_expected')}))


def run():
    guard(); verify_snapshot(); OUT.mkdir(parents=True, exist_ok=False)
    log = CommandLog(OUT)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'revision': REVISION, 'real_codex_turns': 0, 'argv': sys.argv,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'steps': [], 'mutation_recipes': {},
              'scope': 'Frozen S3 and T-076 controlled entry checks; no model, GUI or fresh-context review',
              'open_handoff_issue': '20261014T023857Z-worker:s13-t077s-issue-001'}
    workspace = Path(tempfile.mkdtemp(prefix='t77final-', dir='/tmp')).resolve()
    fixtures = []
    try:
        version = log.run(['node', '--version'], cwd=ROOT, env=env)
        if version.returncode or not version.stdout.startswith('v26.5.'): raise RuntimeError('Approved Node 26.5 is required')

        def child(name, argv, filename='run.json', expected_exit=0, verdict='pass'):
            guard(); verify_snapshot()
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
            return value

        def mutant(name, recipe):
            target = workspace / name
            for folder in ('workbench', 'acceptance', 'fixtures'):
                shutil.copytree(ROOT / folder, target / folder, symlinks=True,
                    ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
            (target / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
            core = target / 'workbench/src/gates/core.ts'; source = core.read_text(encoding='utf-8')
            before, after = RECIPES[recipe]
            if source.count(before) != 1: raise RuntimeError('Mutation target changed: ' + recipe)
            core.write_text(source.replace(before, after, 1), encoding='utf-8')
            record['mutation_recipes'][name] = {'root': str(target), 'file': 'workbench/src/gates/core.ts',
                'before': before, 'after': after, 'source_committed': False}
            syntax = log.run(['node', '--check', core], cwd=ROOT, env=env)
            if syntax.returncode: raise RuntimeError('Mutation is a syntax error, not business evidence: ' + recipe)
            return target

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
        for suite in ('coop', 'recovery', 'run', 'cas', 'cards'):
            child(suite, [sys.executable, '-B', ROOT / 'workbench/tests/run_s3_rebased_regression.py',
                '--suite', suite, '--revision', REVISION, '--output', OUT / suite])
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
