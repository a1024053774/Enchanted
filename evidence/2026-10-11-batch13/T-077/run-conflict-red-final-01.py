#!/usr/bin/env python3
"""Controller-only targeted conflict counterfactuals; no model execution."""
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
PRODUCT = '5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4'
HARNESS = '178d15f3ddb13f06a00eac19d7655225519f98e2'
PREP = E / 'conflict-red-final-01-preparation-02'
OUT = E / 'outside-conflict-red-final-01'
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog

CASES = [
    ('test_conflict_active_worker_reworks_and_integrates', 'CONFLICT-ACTIVE-WRITEBACK', 'no-conflict-feedback'),
    ('test_conflict_ended_session_gets_new_attempt', 'CONFLICT-ENDED-NEW-ATTEMPT', 'no-conflict-feedback'),
    ('test_conflict_unknown_session_preserves_scene_and_reports', 'CONFLICT-UNKNOWN-SESSION-REPORT', 'no-conflict-feedback'),
    ('test_conflict_unknown_delivery_does_not_resend', 'CONFLICT-UNKNOWN-DELIVERY-ONCE', 'no-conflict-feedback'),
    ('test_merge_command_error_is_not_text_conflict', 'CONFLICT-GIT-ERROR-CLASSIFICATION', 'io-as-text-conflict'),
    ('test_conflict_rework_still_rejects_forbidden_path', 'CONFLICT-REWORK-FORBIDDEN-PATH', 'rework-path-guard'),
    ('test_conflict_rework_still_rejects_foreign_trailer', 'CONFLICT-REWORK-FOREIGN-TRAILER', 'rework-trailer-task-guard'),
]
TARGET_PREREQUISITES = {
    'CONFLICT-ACTIVE-WRITEBACK': (
        'scenario_prepared', 'worker_session_input_available', 'text_conflict_observed', 'conflict_handling_entered'),
    'CONFLICT-ENDED-NEW-ATTEMPT': (
        'scenario_prepared', 'ended_session_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    'CONFLICT-UNKNOWN-SESSION-REPORT': (
        'scenario_prepared', 'unknown_session_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    'CONFLICT-UNKNOWN-DELIVERY-ONCE': (
        'scenario_prepared', 'delivery_unknown_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    'CONFLICT-GIT-ERROR-CLASSIFICATION': (
        'scenario_prepared', 'git_io_failure_observed', 'target_verify_executed'),
    'CONFLICT-REWORK-FORBIDDEN-PATH': (
        'scenario_prepared', 'text_conflict_observed', 'conflict_handling_entered',
        'conflict_delivered', 'explicit_resubmitted', 'target_verify_executed'),
    'CONFLICT-REWORK-FOREIGN-TRAILER': (
        'scenario_prepared', 'text_conflict_observed', 'conflict_handling_entered',
        'conflict_delivered', 'explicit_resubmitted', 'target_verify_executed'),
}
TARGET_CONTRACTS = [{'case': case, 'target_assertion_id': target, 'mutation': mutation,
                     'required_preconditions': list(TARGET_PREREQUISITES[target])} for case, target, mutation in CASES]
RECIPES = {
    'no-conflict-feedback': ('await this.writeConflict(task, attempt, v);', '// Test mutant: omit conflict worker handoff.'),
    'io-as-text-conflict': (
        'if (merge.returncode !== 1 || !unmerged.stdout) throw new Refusal("git_failed", merge);',
        'if (merge.returncode !== 1 || !unmerged.stdout) throw new Refusal("merge_conflict", v);'),
    'rework-path-guard': (
        'requireGate(forbidden.length === 0, "path_boundary_failed", { forbidden });',
        'requireGate(attempt.rework?.state === "submitted" || forbidden.length === 0, "path_boundary_failed", { forbidden });'),
    'rework-trailer-task-guard': (
        'if (trailers.task?.some((value) => value !== task.task_id)) error = "trailer_task_mismatch";',
        'if (attempt.rework?.state !== "submitted" && trailers.task?.some((value) => value !== task.task_id)) error = "trailer_task_mismatch";'),
}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def guard():
    head = git('rev-parse', 'HEAD').decode().strip()
    if subprocess.run(['git', 'merge-base', '--is-ancestor', HARNESS, head], cwd=ROOT, capture_output=True).returncode:
        raise RuntimeError('Checkout is not descended from the frozen fixture commit')
    if git('branch', '--show-current').decode().strip() != 'exec/t077': raise RuntimeError('Wrong worker branch')
    changed = git('diff', '--name-only', '-z', HARNESS, head).decode().split(chr(0))
    if any(name and not name.startswith(str(E.relative_to(ROOT)) + '/') for name in changed):
        raise RuntimeError('Only this ticket evidence commits may follow the frozen fixture')
    for name in ('workbench/src', 'workbench/hooks', 'workbench/README.md', 'acceptance'):
        if git('diff', PRODUCT, '--', name): raise RuntimeError('Frozen product changed: ' + name)
    if git('diff', HARNESS, '--', 'workbench/tests'): raise RuntimeError('Frozen fixture changed')
    for kind in ('rebase-merge', 'rebase-apply'):
        if Path(git('rev-parse', '--git-path', kind).decode().strip()).exists(): raise RuntimeError('Rebase is active')
    if not os.path.ismount('/Volumes/WD-Elements'): raise RuntimeError('Required external disk is not mounted')


def large_files(path):
    return [str(p) for p in path.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]


def source_files():
    paths = []
    for folder in ('workbench/src', 'workbench/hooks', 'workbench/tests', 'acceptance', 'fixtures/pagination'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(ROOT / name for name in ('workbench/package.json', 'workbench/package-lock.json',
        '.project-map/tickets/T-077-worktree-lifecycle-conflicts.md', '.project-map/specs/native-cli-orchestration-2026-10-10.md'))
    paths.extend([Path(__file__).resolve(), E / 'outside-sandbox.sh', E / 'check-conflict-classifier-01.py'])
    return sorted(set(paths))


def verify_snapshot():
    with tarfile.open(PREP / 'frozen-source-and-harness.tar.gz', 'r:gz') as archive:
        for member in archive.getmembers():
            if member.isfile() and archive.extractfile(member).read() != (ROOT / member.name).read_bytes():
                raise RuntimeError('Prepared input changed: ' + member.name)


def prepare():
    guard(); PREP.mkdir(exist_ok=False)
    source = (ROOT / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
    log = CommandLog(PREP)
    syntax_root = Path(tempfile.mkdtemp(prefix='t077-conflict-syntax-', dir='/tmp'))
    for name, (before, after) in RECIPES.items():
        if source.count(before) != 1: raise RuntimeError('Mutation target is not unique: ' + name)
        path = syntax_root / (name + '.ts'); path.write_text(source.replace(before, after, 1), encoding='utf-8')
        if log.run(['node', '--check', path], cwd=ROOT).returncode: raise RuntimeError('Invalid mutation syntax: ' + name)
    with tarfile.open(PREP / 'frozen-source-and-harness.tar.gz', 'x:gz') as archive:
        for path in source_files(): archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    large = large_files(PREP)
    if large: raise RuntimeError('Controller archive required: ' + repr(large))
    save(PREP / 'plan.json', {'status': 'READY', 'business_status': 'INCOMPLETE: outside stage not run',
        'product': PRODUCT, 'harness': HARNESS, 'checkout': git('rev-parse', 'HEAD').decode().strip(),
        'planned_subphases': 8, 'cases': TARGET_CONTRACTS, 'recipes': RECIPES, 'candidate_case_count': 7,
        'precondition_policy': 'Controller #123: each target requires its declared prior facts. Missing, false or late receipts mean NOT_COVERED.',
        'command': ['bash', str(E / 'outside-sandbox.sh'), 'conflict-red-final-01'],
        'source_files': [str(p.relative_to(ROOT)) for p in source_files()], 'files_over_5mb': large, 'real_codex_turns': 0})
    print(json.dumps({'status': 'READY', 'planned_subphases': 8, 'real_codex_turns': 0}))


def run():
    guard(); verify_snapshot(); OUT.mkdir(exist_ok=False)
    head = git('rev-parse', 'HEAD').decode().strip()
    log = CommandLog(OUT)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    workspace = Path(tempfile.mkdtemp(prefix='t077-conflict-final-', dir='/tmp')).resolve()
    record = {'status': 'INCOMPLETE', 'product': PRODUCT, 'harness': HARNESS, 'checkout': head,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'steps': [], 'mutations': {},
              'real_codex_turns': 0, 'argv': sys.argv, 'not_covered': [], 'target_failures_not_red': [],
              'target_contracts': TARGET_CONTRACTS}
    try:
        version = log.run(['node', '--version'], cwd=ROOT, env=env)
        if version.returncode or not version.stdout.startswith('v26.5.'): raise RuntimeError('Approved Node 26.5 is required')
        products = {}
        for name, (before, after) in RECIPES.items():
            target = workspace / name
            for folder in ('workbench', 'acceptance', 'fixtures'):
                shutil.copytree(ROOT / folder, target / folder, symlinks=True,
                    ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
            (target / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
            path = target / 'workbench/src/gates/core.ts'; text = path.read_text(encoding='utf-8')
            if text.count(before) != 1: raise RuntimeError('Mutation target changed: ' + name)
            path.write_text(text.replace(before, after, 1), encoding='utf-8'); products[name] = target
            record['mutations'][name] = {'root': str(target), 'file': 'workbench/src/gates/core.ts',
                'before': before, 'after': after, 'source_committed': False}

        def child(name, argv):
            guard(); verify_snapshot()
            if git('rev-parse', 'HEAD').decode().strip() != head: raise RuntimeError('Checkout changed during stage')
            result = log.run(argv, cwd=ROOT, env=env, timeout=None,
                stdout_file=OUT / (name + '.stdout.txt'), stderr_file=OUT / (name + '.stderr.txt'))
            path = OUT / name / 'run.json'
            step = {'name': name, 'argv': list(map(str, argv)), 'exit': result.returncode, 'result': str(path)}
            record['steps'].append(step); save(OUT / (name + '.receipt.json'), step)
            if large_files(OUT): raise RuntimeError('Evidence exceeds 5 MB; stop for controller archive')
            if not path.is_file(): raise RuntimeError('Child has no result; preserve without retry: ' + name)
            value = json.loads(path.read_text(encoding='utf-8'))
            if result.returncode not in (0, 1): raise RuntimeError('Unexpected child exit: ' + name)
            guard(); verify_snapshot()
            if git('rev-parse', 'HEAD').decode().strip() != head: raise RuntimeError('Checkout changed during stage')
            return result.returncode, value

        script = ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py'
        reds = []
        for index, (case, target_id, mutation) in enumerate(CASES, 1):
            name = 'red-%02d' % index
            code, value = child(name, [sys.executable, '-B', script, '--phase', 'baseline',
                '--mutant-product', products[mutation], '--case', case, '--output', OUT / name])
            if len(value['cases']) != 1 or value['cases'][0]['case'] != case: raise RuntimeError('Wrong counterfactual membership')
            row = value['cases'][0]
            if row['target_assertion_id'] != target_id: raise RuntimeError('Wrong stable target identifier')
            if row['required_preconditions'] != list(TARGET_PREREQUISITES[target_id]):
                raise RuntimeError('Target prerequisite list differs from the frozen contract')
            if row['errors'] or row['skipped'] or row['cleanup_failures']: raise RuntimeError('Counterfactual has infrastructure or cleanup failure: ' + name)
            if row['business_red'] and (not row['target_failed'] or row['target_coverage'] != 'TARGET_FAILED'
                    or row['missing_preconditions'] or row['classification_issues']):
                raise RuntimeError('Target verdict and prerequisite receipt disagree')
            if code != (0 if row['business_red'] else 1) or value['red_confirmed'] is not row['business_red']:
                raise RuntimeError('Child exit and target receipt disagree: ' + name)
            summary = {'phase': name, 'case': case, 'target': target_id, 'target_failed': row['target_failed'],
                'business_red': row['business_red'], 'coverage': row['target_coverage'],
                'required_preconditions': row['required_preconditions'],
                'missing_preconditions': row['missing_preconditions'], 'classification_issues': row['classification_issues']}
            reds.append(summary)
            if row['target_coverage'] == 'NOT_COVERED': record['not_covered'].append(summary)
            if row['target_failed'] and not row['business_red']: record['target_failures_not_red'].append(summary)
            print(json.dumps(summary), flush=True)
        record['counterfactuals'] = reds
        args = [sys.executable, '-B', script, '--phase', 'candidate', '--output', OUT / 'candidate']
        for case, _, _ in CASES: args.extend(['--case', case])
        code, green = child('candidate', args)
        if len(green['cases']) != 7 or [row['case'] for row in green['cases']] != [case for case, _, _ in CASES]:
            raise RuntimeError('Wrong candidate case membership')
        if any(row['target_assertion_id'] != target or row['required_preconditions'] != list(TARGET_PREREQUISITES[target])
               for row, (_, target, _) in zip(green['cases'], CASES)):
            raise RuntimeError('Candidate target contract differs from the frozen prerequisite list')
        candidate_passed = code == 0 and green['status'] == 'PASS' and all(
            row['target_passed'] and row['tests_run'] == 1 and not row['failures'] and not row['errors']
            and not row['skipped'] and not row['cleanup_failures'] and row['target_coverage'] == 'TARGET_PASSED'
            and not row['missing_preconditions'] and not row['classification_issues'] for row in green['cases'])
        record.update(candidate_passed=candidate_passed, red_confirmed=all(row['business_red'] for row in reds))
        if len(record['steps']) != 8: raise RuntimeError('Incomplete stage membership')
        if candidate_passed and record['red_confirmed']: record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        record['files_over_5mb'] = large_files(OUT)
        if record['files_over_5mb']: record['status'] = 'INCOMPLETE'
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(OUT / 'run.json', record)
        print(json.dumps({key: record.get(key) for key in ('status', 'red_confirmed', 'candidate_passed', 'not_covered', 'files_over_5mb')}), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if args.prepare_only: prepare()
    else: raise SystemExit(run())
