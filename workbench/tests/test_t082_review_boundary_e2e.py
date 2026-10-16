"""T-082 controlled review-copy tracer and launch-boundary refusals.

The host supplies only PTY/process observations. The gate remains responsible
for the review request, candidate-copy lifecycle, launch policy, and refusal.
"""
import argparse
import datetime
import json
from pathlib import Path
import socket
import uuid

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

    def shared_refs_changed(self):
        _, candidate = self.good_submission()
        review, record = self.start_review(candidate)
        self.git('update-ref', 'refs/t082/unexpected', candidate)
        self.send_review(review, record, self.review_packet(review, candidate))
        events = self.wait_for(self.events, lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        task = self.cli('status')['task']
        proof = {'task': task, 'events': events,
                 'refs': self.git('for-each-ref', '--format=%(refname)=%(objectname)'),
                 'copy_exists': Path(review['candidate_workspace']).exists(), 'main_head': self.oid()}
        save(self.evidence / 'shared-refs-readback.json', proof)
        self.check('REVIEW-REFS-INVALIDATE', task['state'] == 'paused' and task['review']['state'] == 'unknown'
                   and proof['copy_exists'] and proof['main_head'] == self.base
                   and any(e['type'] == 'issue_issue' for e in events)
                   and any(e['type'] == 'review_lifecycle_failed'
                           and e['details']['details'].get('error') == 'review_shared_refs_changed' for e in events)
                   and not any(e['type'] == 'review_reclaimed' for e in events),
                   'changed shared refs invalidate the review, report an issue and retain the copy before integration', proof)

    def requirements_workspace_changed(self):
        _, candidate = self.good_submission()
        review, record = self.start_review(candidate)
        packet = self.review_packet(review, candidate)
        packet['review_requirements']['mutation_checks']['workspace'] = str(self.root / 'wrong-copy')
        task = self.send_review(review, record, packet)
        proof = {'submitted': packet, 'task': task, 'expected_workspace': review['candidate_workspace'],
                 'events': self.events()}
        save(self.evidence / 'requirements-workspace-readback.json', proof)
        self.check('REVIEW-REQUIREMENTS-WORKSPACE', task['state'] == 'paused'
                   and task['review']['state'] == 'unknown' and not task['review'].get('result')
                   and not any(e['type'] == 'review_result' for e in proof['events']),
                   'changed request workspace is refused before any report is persisted', proof)

    def integration_before_end_check(self):
        self.integration_window(dirty=True)

    def integration_before_end_check_clean(self):
        self.integration_window(dirty=False)

    def integration_window(self, dirty):
        _, candidate = self.good_submission()
        review, record = self.start_review(candidate)
        outside = Path(review['workspace']) / 'external-before-end.txt'
        if dirty:
            outside.write_text('External change must be checked before integration.\n', encoding='utf-8')
        stop = {'session_id': record['native'], 'turn_id': 'fixture-turn-1', 'hook_event_name': 'Stop',
                'last_assistant_message': json.dumps(self.review_packet(review, candidate), ensure_ascii=False)}
        message = {'id': str(uuid.uuid4()), 'input': {'command': 'signal', 'launch': record['launch'],
                   'raw_stdin': json.dumps(stop, ensure_ascii=False),
                   'received_at': datetime.datetime.now(datetime.timezone.utc).isoformat()},
                   'identity': {'launch': record['launch'], 'token': record['env']['A2A_CAPABILITY'],
                                'native_session': record['native']}}
        # Keep the real socket's client write-half open. The product still owns
        # signal handling and its close-triggered reclaim; no callback is mocked.
        held = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        held.settimeout(15)
        try:
            held.connect(str(self.state / 'control.sock'))
            held.sendall((json.dumps(message, ensure_ascii=False) + '\n').encode())
            response = b''
            while b'\n' not in response:
                chunk = held.recv(65536)
                if not chunk:
                    raise HarnessFailure('Signal socket closed before a complete receipt.')
                response += chunk
            receipt = json.loads(response.split(b'\n', 1)[0])
            if not receipt.get('ok') or not receipt.get('completedReview'):
                raise HarnessFailure('Valid report was not received: ' + json.dumps(receipt))
            events = self.events()
            if any(e['type'] == 'review_reclaimed' for e in events):
                raise HarnessFailure('The held-socket boundary was not established.')
            before = self.cli('status')['task']
            result = self.gate('integrate', '--attempt', self.a['attempt_id'], '--score-file', self.score_file())
            proof = {'stop_receipt': receipt, 'before_integration': before, 'integration': result,
                     'main_head': self.oid(), 'base': self.base, 'dirty': dirty,
                     'outside_change_exists': outside.exists(), 'events': self.events()}
            save(self.evidence / 'integration-before-end-check.json', proof)
        finally:
            held.close()
        events = self.wait_for(self.events, lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        task = self.cli('status')['task']
        save(self.evidence / 'after-release.json', {'task': task, 'events': events, 'main_head': self.oid()})
        self.check('REVIEW-END-BEFORE-INTEGRATE', not result.get('ok') and proof['main_head'] == self.base,
                   'integration before the review end check must refuse and leave main unchanged', proof)
        if dirty:
            self.check('T082-DIRTY-END-INVALIDATE', task['state'] == 'paused'
                       and task['review']['state'] == 'unknown' and self.oid() == self.base
                       and not any(e['type'] in ('review_reclaimed', 'integrated') for e in events)
                       and any(e['type'] == 'issue_issue' for e in events),
                       'end-check failure invalidates the report before any integration', task)
        else:
            integrated = self.gate('integrate', '--attempt', self.a['attempt_id'], '--score-file', self.score_file())
            self.check('T082-INTEGRATE-AFTER-END', integrated['ok'] and self.oid() == candidate,
                       'the same valid candidate can integrate after confirmed end checks and cleanup', integrated)

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
         'real_payload_report_roundtrip', 'shared_refs_changed', 'requirements_workspace_changed',
         'integration_before_end_check', 'integration_before_end_check_clean']


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
