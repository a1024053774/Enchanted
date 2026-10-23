"""T-152 isolated current-contract runs; infrastructure failures never count as red."""
import argparse
import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[3]
MUTANTS = {
    'no-end-check': ('src/gates/core.ts',
        'requireGate(ended, "review_end_check_required");',
        'requireGate(row, "review_end_check_required");',
        'integration_before_end_check_clean', 'REVIEW-END-BEFORE-INTEGRATE'),
    'nonempty-workspace': ('src/gates/core.ts',
        'requireGate(evidence.review_requirements.mutation_checks.workspace === review.candidate_workspace,',
        'requireGate(Boolean(evidence.review_requirements.mutation_checks.workspace),',
        'requirements_workspace_changed', 'REVIEW-REQUIREMENTS-WORKSPACE'),
    'omit-shared-refs': ('src/gates/core.ts',
        'requireGate(this.reviewRefsUnchanged(task, review, refs), "review_shared_refs_changed",',
        'requireGate(true, "review_shared_refs_changed",',
        'shared_refs_changed', 'REVIEW-REFS-INVALIDATE'),
    'false-copy-removed': ('src/gates/core.ts',
        '    rmSync(review.candidate_workspace, { recursive: true, force: false });\n'
        '    requireGate(!existsSync(review.candidate_workspace), "review_candidate_copy_unconfirmed", binding);',
        '    // Deliberately retain the copy while recording successful cleanup.',
        'tracer_review_copy', 'T082-COPY-REMOVED'),
    'readonly-argv': ('src/panes.ts',
        'const sandboxMode = monitor && !extraDirectories.length ? "read-only" : "workspace-write";',
        'const sandboxMode = review || monitor && !extraDirectories.length ? "read-only" : "workspace-write";',
        'launch_boundary_refused', None),
    'wrong-workspace': ('src/panes.ts',
        'const launchWorkspace = review ? review.candidate_workspace : attempt.workspace;',
        'const launchWorkspace = review ? review.workspace : attempt.workspace;',
        'launch_boundary_refused', None),
    'network-disabled': ('src/panes.ts',
        '"sandbox_workspace_write.network_access=true"',
        'review ? "sandbox_workspace_write.network_access=false" : "sandbox_workspace_write.network_access=true"',
        'launch_boundary_refused', None),
    'tmp-writable': ('src/panes.ts',
        '"sandbox_workspace_write.exclude_slash_tmp=true"',
        'review ? "sandbox_workspace_write.exclude_slash_tmp=false" : "sandbox_workspace_write.exclude_slash_tmp=true"',
        'launch_boundary_refused', None),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision', default='HEAD')
    parser.add_argument('--mutant', choices=MUTANTS)
    parser.add_argument('--worker-regression', action='store_true')
    parser.add_argument('--case', help='Run one named normal T-082 case in a fresh fixture')
    args = parser.parse_args()
    if args.case and (args.mutant or args.worker_regression):
        parser.error('--case cannot be combined with --mutant or --worker-regression')
    source = args.source.resolve()
    summary = args.summary.resolve()
    summary.parent.mkdir(parents=True, exist_ok=True)
    # Reserve before any run; preserve previous evidence even on failure.
    with summary.open('x', encoding='utf-8') as stream:
        scratch = Path(tempfile.mkdtemp(prefix='t152-', dir='/private/tmp'))
        record = {'status': 'INCOMPLETE', 'task': 'T-152-1', 'attempt': 'a1',
                  'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'command': sys.argv, 'artifact_root': str(scratch),
                  'mutant': args.mutant, 'real_model_turns': 0}
        try:
            revision = subprocess.check_output(['git', '-C', source, 'rev-parse', args.revision + '^{commit}'], text=True).strip()
            record['source_revision'] = revision
            record['test_worktree_revision'] = subprocess.check_output(['git', '-C', ROOT, 'rev-parse', 'HEAD'], text=True).strip()
            record['test_worktree_status'] = subprocess.check_output(['git', '-C', ROOT, 'status', '--short'], text=True)
            record['node_version'] = subprocess.check_output(['node', '--version'], text=True).strip()
            product = scratch / 'source'
            product.mkdir()
            archive = subprocess.check_output(['git', '-C', source, 'archive', revision, 'workbench'])
            # Trusted tracked archive from the requested local repository.
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(product)
            (product / 'workbench/node_modules').symlink_to(source / 'workbench/node_modules', target_is_directory=True)
            name = 'test_t090_review_worker_boundary_e2e.py' if args.worker_regression else 'test_t082_review_boundary_e2e.py'
            argv = [sys.executable, '-B', str(ROOT / 'workbench/tests' / name),
                    '--source', str(product), '--output', str(scratch / 'run')]
            failure_id = None
            if args.case:
                argv.extend(['--case', args.case])
            if args.mutant:
                path, before, after, case, failure_id = MUTANTS[args.mutant]
                target = product / 'workbench' / path
                original = target.read_text(encoding='utf-8')
                if original.count(before) != 1:
                    raise RuntimeError('Mutation anchor must occur exactly once: ' + before)
                target.write_text(original.replace(before, after), encoding='utf-8')
                record['mutation'] = {'path': path, 'before': before, 'after': after}
                argv.extend(['--case', case])
            record['run_command'] = argv
            env = {**os.environ, 'A2A_TEST_ARTIFACT_PARENT': '/private/tmp'}
            completed = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=900)
            for label, data in [('stdout', completed.stdout), ('stderr', completed.stderr)]:
                (scratch / (label + '.bin')).write_bytes(data)
            report = json.loads((scratch / 'run/run.json').read_text(encoding='utf-8'))
            record.update(exit_code=completed.returncode, run_report=str(scratch / 'run/run.json'),
                          fixture_root=report['artifact_root'], evidence_layer=report['evidence_layer'])
            record['cases'] = [{key: row.get(key) for key in ('case', 'outcome', 'failure_id', 'error', 'cleanup_failures')}
                               | {'assertions': [{'id': a['id'], 'passed': a['passed']} for a in row['assertions']]}
                               for row in report['cases']]
            if failure_id:
                row = report['cases'][0]
                passed = (completed.returncode == 1 and len(report['cases']) == 1
                          and row['outcome'] == 'contract_failure' and row.get('failure_id') == failure_id
                          and not row['cleanup_failures'])
                record['expected_failure_id'] = failure_id
            else:
                passed = completed.returncode == 0 and report['status'] == 'PASS'
            record['status'] = 'PASS' if passed else 'INCOMPLETE'
        except Exception as error:
            record['error'] = repr(error)
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': record['status'], 'summary': str(summary)}), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
