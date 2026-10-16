"""T-090: worker changes during review must invalidate the persisted verdict.

Expectations come from T-090/T-082: retain frozen C and the failed scene,
pause/report the review, and prohibit reclaim or integration. Git mutations
are external actors through the real daemon/CLI; no gate result is supplied.
"""
import argparse
from pathlib import Path

from test_quality_chain_e2e import run_cases, save
from test_t082_review_boundary_e2e import ReviewBoundary


class WorkerBoundary(ReviewBoundary):
    def worker_changed(self, change):
        attempt, candidate = self.good_submission()
        worker = Path(attempt['workspace'])
        if change == 'branch':
            # Create the alternative before the snapshot. Switching between
            # existing branches at the same commit does not alter shared refs.
            self.git('branch', 't090-existing-branch', candidate)
        before = {'head': self.oid(worker),
                  'branch': self.git('rev-parse', '--abbrev-ref', 'HEAD', cwd=worker),
                  'status': self.git('status', '--porcelain=v1', '--untracked-files=all', cwd=worker),
                  'refs': self.git('for-each-ref', '--format=%(refname)=%(objectname)')}
        review, record = self.start_review(candidate)
        # Verification creates its retained ref before review starts.
        refs_at_start = self.git('for-each-ref', '--format=%(refname)=%(objectname)')
        if change == 'head':
            self.git('checkout', '--detach', self.base, cwd=worker)
        elif change == 'branch':
            self.git('checkout', 't090-existing-branch', cwd=worker)
        elif change == 'dirty':
            (worker / 'src/value.txt').write_text('external edit during review\n', encoding='utf-8')
        else:
            raise ValueError(change)
        after = {'head': self.oid(worker),
                 'branch': self.git('rev-parse', '--abbrev-ref', 'HEAD', cwd=worker),
                 'status': self.git('status', '--porcelain=v1', '--untracked-files=all', cwd=worker),
                 'refs': self.git('for-each-ref', '--format=%(refname)=%(objectname)')}
        self.check('T090-EXTERNAL-MUTATION', before['head'] == candidate and not before['status']
                   and after['refs'] == refs_at_start
                   and (after['head'] != candidate if change == 'head' else after['head'] == candidate)
                   and (after['branch'] != before['branch'] if change == 'branch' else True)
                   and (bool(after['status']) if change == 'dirty' else not after['status']),
                   'the external worker mutation leaves shared refs unchanged and isolates the worker boundary',
                   {'before': before, 'after': after, 'refs_at_review_start': refs_at_start})
        self.send_review(review, record, self.review_packet(review, candidate))
        events = self.wait_for(self.events, lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        task = self.cli('status')['task']
        proof = {'change': change, 'before': before, 'after': after, 'task': task,
                 'events': events, 'main_head': self.oid(),
                 'copy_exists': Path(review['candidate_workspace']).exists(),
                 'review_workspace_exists': Path(review['workspace']).exists()}
        save(self.evidence / 'worker-boundary-readback.json', proof)
        self.check('T090-WORKER-' + change.upper(), task['state'] == 'paused'
                   and task['review']['state'] == 'unknown' and task['candidate_commit'] == candidate
                   and proof['main_head'] == self.base and proof['copy_exists']
                   and proof['review_workspace_exists'] and worker.exists()
                   and any(e['type'] == 'issue_issue' for e in events)
                   and any(e['type'] == 'review_lifecycle_failed'
                           and e['details']['details'].get('error') == 'review_worker_workspace_changed' for e in events)
                   and not any(e['type'] in ('review_reclaimed', 'integrated', 'review_candidate_copy_removed') for e in events),
                   'a changed worker invalidates the result, reports an issue and retains the scene before integration', proof)

    def worker_head_changed(self):
        self.worker_changed('head')

    def worker_became_dirty(self):
        self.worker_changed('dirty')

    def worker_branch_changed(self):
        self.worker_changed('branch')


CASES = ['worker_head_changed', 'worker_became_dirty', 'worker_branch_changed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    args = parser.parse_args()
    raise SystemExit(run_cases(args.source, args.output, args.case or CASES, WorkerBoundary,
                              dialect='current', stop_on_failure=True))
