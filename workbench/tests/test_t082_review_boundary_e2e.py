"""T-082 controlled review-copy tracer and launch-boundary refusals.

The host supplies only PTY/process observations. The gate remains responsible
for the review request, candidate-copy lifecycle, launch policy, and refusal.
"""
import argparse
import json
from pathlib import Path

from test_quality_chain_e2e import HarnessFailure, run_cases, save
from test_quality_tracer_e2e import Tracer


class ReviewBoundary(Tracer):
    def start_review(self, candidate):
        reply = self.gate('verify', '--attempt', self.a['attempt_id'])
        self.check('T082-REVIEW-START', reply['ok'] and reply['task']['state'] == 'reviewing'
                   and isinstance(reply['task'].get('review'), dict),
                   'mechanical success creates a pending review', reply)
        review = reply['task']['review']
        launch = self.gate('pane_status', '--thread', review['thread_id'], task=False)['launch']
        record = json.loads((self.control / (launch + '.json')).read_text(encoding='utf-8'))
        rows = [json.loads(row['data']) for row in self.rows('launch_records')]
        details = next(row for row in rows if row['id'] == launch)
        self.check('T082-REVIEW-ARGV', details['sandbox'] == 'workspace-write'
                   and details['argv'][details['argv'].index('--sandbox') + 1] == 'workspace-write'
                   and details['argv'][details['argv'].index('-C') + 1] == review['candidate_workspace']
                   and details['worktree'] == review['candidate_workspace']
                   and 'sandbox_workspace_write.network_access=false' in details['argv']
                   and 'features.network_proxy=false' in details['argv']
                   and 'sandbox_workspace_write.exclude_slash_tmp=true' in details['argv']
                   and 'sandbox_workspace_write.exclude_tmpdir_env_var=true' in details['argv'],
                   'reviewer starts in the writable candidate copy with the required network/tmp boundary', details)
        self.gate('pane_release', '--thread', review['thread_id'], '--reason',
                  'controlled fresh reviewer release', task=False)
        self.wait_for(lambda: self.gate('pane_status', '--thread', review['thread_id'], task=False),
                      lambda pane: pane['state'] == 'busy' and pane['turn'] == 'fixture-turn-1')
        return review, record

    def tracer_review_copy(self):
        _, candidate = self.good_submission()
        review, record = self.start_review(candidate)
        dispatches = [event for event in self.orchestration() if event['type'] == 'dispatch_queued']
        prompt = '\n'.join(event['data'].get('text', '') for event in dispatches)
        self.check('T082-REQUEST-COMPLETION', '完成条件' in prompt and 'oracle_paths' in prompt,
                   'review request requires completion-condition sufficiency review including oracle paths', prompt)
        self.check('T082-REQUEST-MUTATIONS', '2～5' in prompt and '完成条件与变异检查' in prompt,
                   'review request requires two to five mutations and a named report section', prompt)
        self.check('T082-COPY-CREATED', Path(review['candidate_workspace']).is_dir()
                   and not (Path(review['candidate_workspace']) / '.git').exists()
                   and any(event['type'] == 'review_candidate_copy_created' for event in self.events()),
                   'gate creates a disposable non-Git candidate copy before reviewer launch', review)
        current = self.send_review(review, record, self.review_packet(review, candidate))
        self.check('T082-REVIEW-VERDICT', current['state'] == 'verified',
                   'valid reviewer result remains bound to the candidate', current)
        self.wait_review_reclaimed(review)
        events = self.events()
        self.check('T082-COPY-REMOVED', not Path(review['candidate_workspace']).exists()
                   and any(event['type'] == 'review_candidate_copy_removed' for event in events),
                   'candidate copy is removed only after the review result and boundary checks', events)

    def launch_boundary_refused(self):
        _, candidate = self.good_submission()
        reply = self.gate('verify', '--attempt', self.a['attempt_id'])
        self.check('T082-LAUNCH-REFUSED', not reply['ok'] and reply.get('error') == 'review_launch_boundary',
                   'reviewer launch outside the approved boundary is rejected by the gate', reply)
        task = self.cli('status')['task']
        self.check('T082-LAUNCH-PAUSED', task['state'] == 'paused'
                   and task.get('review', {}).get('state') == 'unknown',
                   'boundary refusal invalidates the review and pauses the task', task)
        self.check('T082-LAUNCH-ISSUE', any(event['type'] == 'issue_issue' for event in self.events()),
                   'boundary refusal creates an issue record', self.events())

    def external_review_boundary_invalidated(self):
        _, candidate = self.good_submission()
        review, record = self.start_review(candidate)
        outside = Path(review['workspace']) / 'external-review-change.txt'
        outside.write_text('outside reviewer boundary\n', encoding='utf-8')
        self.send_review(review, record, self.review_packet(review, candidate))
        events = self.wait_for(lambda: self.events(), lambda rows: any(
            event['type'] == 'review_lifecycle_failed' for event in rows))
        task = self.cli('status')['task']
        self.check('T082-END-CHECK-INVALID', task['state'] == 'paused'
                   and task.get('review', {}).get('state') == 'unknown'
                   and outside.exists()
                   and Path(review['candidate_workspace']).exists()
                   and not any(event['type'] == 'review_candidate_copy_removed' for event in events),
                   'outside review-worktree change invalidates the result and preserves the disposable copy for diagnosis',
                   {'task': task, 'events': events})

    def real_payload_report_roundtrip(self):
        _, candidate = self.good_submission()
        review, record = self.start_review(candidate)
        captured = Path(__file__).resolve().parents[2] / 'evidence/2026-10-15-batch15/T-082/protocol-red-green-01/real-review-submit.json'
        actual = json.loads(captured.read_text(encoding='utf-8'))
        packet = self.review_packet(review, candidate)
        packet['report'] = actual['report']
        dispatch = next(json.loads(row['data'])['text'] for row in self.rows('dispatch_records')
                        if row['launch'] == record['launch'])
        template_start = dispatch.rfind('\n{\n  "schema":')
        if template_start < 0:
            raise HarnessFailure('No final response template in the product review request')
        template = json.loads(dispatch[template_start:])
        self.check('T082-TEMPLATE-FIELDS', set(template) == set(actual),
                   'product response template declares every field returned by the real reviewer', list(template))
        self.check('T082-TEMPLATE-REPORT', isinstance(template['report'], dict),
                   'response template explicitly requires an object report', template['report'])
        current = self.send_review(review, record, packet)
        self.wait_review_reclaimed(review)
        current = self.cli('status')['task']
        result = current['review'].get('result', {})
        self.check('T082-REPORT-PERSISTED', current['state'] == 'verified'
                   and result.get('report') == actual['report']
                   and result.get('review_requirements') == packet['review_requirements'],
                   'Stop/strict parser/relay/gate persist the complete report without changing the verdict binding', current)
        self.check('T082-REPORT-COPY-REMOVED', not Path(review['candidate_workspace']).exists(),
                   'report submission completes the gate-owned copy lifecycle', review['candidate_workspace'])


CASES = ['tracer_review_copy', 'launch_boundary_refused', 'external_review_boundary_invalidated',
         'real_payload_report_roundtrip']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    args = parser.parse_args()
    return run_cases(args.source, args.output, args.case or CASES, ReviewBoundary,
                     dialect='current', stop_on_failure=True)


if __name__ == '__main__':
    raise SystemExit(main())
