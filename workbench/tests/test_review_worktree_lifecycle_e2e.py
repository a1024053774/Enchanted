"""Review worktree names and cleanup through the real controlled gate entry.

Independent expectations: spec section 4, T-077, controller #110. Only the
external PTY/process/native facts and explicit reviewer decisions are supplied.
Failure modes: leaked registered directory, reused ordinal, attached branch,
cleanup before persisted result/reclaim, changed candidate binding, dirty/unknown
scene deletion, or loss of the review result used by R8.
"""
import argparse
import json
from pathlib import Path

from test_quality_chain_e2e import run_cases, save
from test_quality_tracer_e2e import Tracer


class ReviewWorktree(Tracer):
    def registration(self, workspace):
        result = self.process(['git', '-C', self.repo, 'worktree', 'list', '--porcelain', '-z'])
        if result.returncode: raise RuntimeError('Cannot independently read Git worktree registry')
        return 'worktree ' + workspace in result.stdout.split('\0'), result.stdout

    def cleanup_after_persisted_result(self):
        _, c = self.good_submission()
        review, record = self.start_review(c)
        attached = self.process(['git', '-C', review['workspace'], 'symbolic-ref', '--quiet', 'HEAD'])
        self.check('REVIEW-DETACHED', attached.returncode == 1, 'detached reviewer checkout', attached.stdout)
        self.check('REVIEW-CANDIDATE-HEAD', self.oid(Path(review['workspace'])) == c, c, self.oid(Path(review['workspace'])))
        self.send_review(review, record, self.review_packet(review, c))
        self.wait_review_reclaimed(review)
        task = self.cli('status')['task']; events = self.events()
        registered, raw = self.registration(review['workspace'])
        exists = Path(review['workspace']).exists()
        save(self.evidence / 'review-lifecycle-proof.json', {'review': review, 'task': task, 'events': events,
             'directory_exists': exists, 'git_registered': registered, 'git_worktrees': raw})
        self.check('REVIEW-DIRECTORY-REMOVED', not exists and not registered,
                   {'directory_exists': False, 'git_registered': False}, {'directory_exists': exists, 'git_registered': registered})
        relevant = [e for e in events if e['type'] in ('review_result', 'review_worktree_cleanup_intent',
                    'review_worktree_removed', 'review_reclaimed') and
                    (e['details'].get('review_id') or e['details'].get('review', {}).get('review_id')) == review['review_id']]
        self.check('REVIEW-RESULT-BEFORE-REMOVE', [e['type'] for e in relevant] ==
                   ['review_result', 'review_worktree_cleanup_intent', 'review_worktree_removed', 'review_reclaimed'],
                   'stored result, confirmed stopped pane, cleanup intent/removal, then completed reclaim', relevant)
        self.check('REVIEW-RESULT-UNCHANGED', task['review'] == next(e['details']['review'] for e in events if e['type'] == 'review_result'),
                   'cleanup leaves the review object byte-equivalent to its durable result binding', task['review'])
        self.integrate_scored(c, rounds=1)

    def names_and_ordinals(self):
        c2, second, _ = self.fix_after_review()
        self.wait_review_reclaimed(second)
        task = self.cli('status')['task']; events = self.events()
        requested = [e['details']['review'] for e in events if e['type'] == 'review_requested']
        expected = [str(self.state / 'worktrees' / task['project_id'] /
                        (self.task + '-a1-review-' + str(i))) for i in (1, 2)]
        save(self.evidence / 'review-names-proof.json', {'requested': requested, 'expected': expected, 'events': events})
        self.check('REVIEW-S3-NAMES', len(requested) == 2 and [r['workspace'] for r in requested] == expected
                   and [r.get('ordinal') for r in requested] == [1, 2]
                   and len({r['review_id'] for r in requested}) == 2
                   and requested[0]['candidate_commit'] != requested[1]['candidate_commit'],
                   {'paths': expected, 'ordinals': [1, 2], 'fresh_candidates': True}, requested)
        for item in requested:
            registered, raw = self.registration(item['workspace'])
            self.check('REVIEW-EACH-RESULT-CLEANED', not Path(item['workspace']).exists() and not registered,
                       'both needs-fix and passed review directories are removed after their results', raw)
        self.integrate_scored(c2, rounds=2, review_failures=1)

    def dirty_review_is_preserved_and_reported(self):
        _, c = self.good_submission()
        review, record = self.start_review(c)
        # A deliberate external actor change, outside the read-only reviewer.
        path = Path(review['workspace']) / 'unexpected-external.txt'
        content = b'Independent external content must survive.\n'
        path.write_bytes(content)
        self.send_review(review, record, self.review_packet(review, c))
        events = self.wait_for(lambda: self.events(), lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        current = self.cli('status')['task']; registered, raw = self.registration(review['workspace'])
        save(self.evidence / 'review-dirty-proof.json', {'review': review, 'task': current,
             'events': events, 'git_worktrees': raw, 'file_bytes': list(path.read_bytes()) if path.exists() else None})
        self.check('REVIEW-DIRTY-PRESERVED', current['state'] == 'paused' and current['review']['state'] == 'unknown'
                   and registered and path.exists() and path.read_bytes() == content and self.oid() == self.base
                   and any(e['type'] == 'issue_issue' for e in events)
                   and not any(e['type'] == 'review_reclaimed' for e in events)
                   and not any(e['type'] == 'review_worktree_removed' for e in events),
                   'dirty reviewer scene is retained and reported; no successful reclaim or integration', current)

    def changed_review_head_is_preserved_and_reported(self):
        _, c = self.good_submission()
        review, record = self.start_review(c)
        # A clean but different detached HEAD is not the reviewed candidate.
        self.git('commit', '--allow-empty', '-m', 'External unreviewed tip', cwd=review['workspace'])
        other = self.oid(Path(review['workspace']))
        self.send_review(review, record, self.review_packet(review, c))
        events = self.wait_for(lambda: self.events(), lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        current = self.cli('status')['task']; registered, raw = self.registration(review['workspace'])
        remains = Path(review['workspace']).exists()
        actual = self.oid(Path(review['workspace'])) if remains else None
        save(self.evidence / 'review-changed-head-proof.json', {'C': c, 'external': other, 'actual': actual,
             'review': review, 'task': current, 'events': events, 'git_worktrees': raw})
        self.check('REVIEW-UNKNOWN-HEAD-PRESERVED', other != c and current['state'] == 'paused'
                   and current['review']['state'] == 'unknown' and registered and remains and actual == other
                   and any(e['type'] == 'issue_issue' for e in events)
                   and not any(e['type'] == 'review_worktree_removed' for e in events)
                   and not any(e['type'] == 'review_reclaimed' for e in events) and self.oid() == self.base,
                   'unknown clean HEAD is retained and reported without deleting or integrating it', current)


CASES = ['cleanup_after_persisted_result', 'names_and_ordinals', 'dirty_review_is_preserved_and_reported',
         'changed_review_head_is_preserved_and_reported']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    args = parser.parse_args()
    return run_cases(args.source, args.output, args.case or CASES, ReviewWorktree, dialect='current', stop_on_failure=True)


if __name__ == '__main__': raise SystemExit(main())
