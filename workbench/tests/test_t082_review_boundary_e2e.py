"""T-082 controlled review-copy tracer and launch-boundary refusals.

The host supplies only PTY/process observations. The gate remains responsible
for the review request, candidate-copy lifecycle, launch policy, and refusal.

Failure modes (T-152, current T-082/T-141 contract): wrong reviewer cwd or
sandbox/tmp boundary; network forced off; missing completion/mutation request;
copy not created/removed; changed shared refs or request workspace accepted;
integration before end checks (held-socket dirty/clean controls); dirty review
end accepted; complete report lost in the native Stop/relay/gate path.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import uuid

import test_quality_chain_e2e as chain
from test_quality_chain_e2e import HarnessFailure, run_cases, save
from test_quality_tracer_e2e import Tracer


class ReviewBoundary(Tracer):
    def start_host(self):
        # Dedicated native-ready fixture; shared historical hosts remain intact.
        if self.host is not None and self.host.poll() is None:
            raise HarnessFailure('The fixture already owns a live host.')
        self.host_generation += 1
        prefix = 'host-%02d' % self.host_generation
        credential = self.root / ('operator-%02d.credential.json' % self.host_generation)
        if credential.exists() or credential.is_symlink():
            raise HarnessFailure('Owned host credential path is already occupied.')
        self.env['A2A_OPERATOR_CREDENTIAL'] = str(credential)
        self.operator_credentials.append(credential)
        ready = self.root / (prefix + '.ready.json')
        stdout = (self.evidence / (prefix + '.stdout.bin')).open('xb')
        stderr = (self.evidence / (prefix + '.stderr.bin')).open('xb')
        self.streams.extend([stdout, stderr])
        argv = ['node', Path(__file__).with_name('t152_review_host.ts'),
                chain.SOURCE, self.state, self.control, ready]
        save(self.evidence / (prefix + '.start.json'), {'argv': list(map(str, argv)),
             'cwd': str(self.root), 'start_new_session': True, 'real_codex_turns': 0})
        self.host = subprocess.Popen(list(map(str, argv)), cwd=self.root, env=self.env,
                                     stdout=stdout, stderr=stderr, start_new_session=True)
        deadline = time.monotonic() + 10
        while not ready.exists():
            if self.host.poll() is not None or time.monotonic() >= deadline:
                raise HarnessFailure('Controlled host startup failed; stderr=' + str(self.evidence / (prefix + '.stderr.bin')))
            time.sleep(0.02)
        self.ready = json.loads(ready.read_text(encoding='utf-8'))
        if self.ready['pid'] != self.host.pid or self.ready['root'] != str(self.state):
            raise HarnessFailure('Host readiness identity mismatch.')
        if self.gate('daemon_status', task=False).get('pid') != self.host.pid:
            raise HarnessFailure('CLI and owned host PID disagree.')
        observed = self.process(['/bin/ps', '-p', str(self.host.pid), '-o', 'pid=,ppid=,pgid=,command='])
        group = {'pid': self.host.pid, 'pgid': os.getpgid(self.host.pid), 'sid': os.getsid(self.host.pid),
                 'caller_pgid': os.getpgrp(), 'ps_exit': observed.returncode, 'ps_stdout': observed.stdout}
        save(self.evidence / (prefix + '.process.json'), group)
        if observed.returncode or not (group['pid'] == group['pgid'] == group['sid']) or group['caller_pgid'] == group['pgid']:
            raise HarnessFailure('Owned daemon is not detached from the invoking process group.')

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
                   and 'sandbox_workspace_write.network_access=true' in details['argv']
                   and 'features.network_proxy=false' not in details['argv']
                   and details['argv'][details['argv'].index('-a') + 1] == 'never'
                   and f'projects={{{json.dumps(str(Path(review["candidate_workspace"]).resolve()))}={{trust_level="untrusted"}}}}' in details['argv']
                   and 'sandbox_workspace_write.exclude_slash_tmp=true' in details['argv']
                   and 'sandbox_workspace_write.exclude_tmpdir_env_var=true' in details['argv'],
                   'T-141 reviewer: candidate-copy writes, open network, inherited proxy, never approval, untrusted copy and excluded shared tmp', details)
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
            self.check('REVIEW-END-BEFORE-INTEGRATE', not result.get('ok')
                       and result.get('error') == 'review_end_check_required' and proof['main_head'] == self.base,
                       'integration before the review end check must refuse and leave main unchanged', proof)
        finally:
            held.close()
        events = self.wait_for(self.events, lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        task = self.cli('status')['task']
        save(self.evidence / 'after-release.json', {'task': task, 'events': events, 'main_head': self.oid()})
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
        captured = Path(__file__).with_name('t152_real_review_submit.json')
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
    # Launch refusal needs an explicitly mutated source; it is not a green case.
    names = args.case or [name for name in CASES if name != 'launch_boundary_refused']
    return run_cases(args.source, args.output, names, ReviewBoundary,
                     dialect='current', stop_on_failure=True)


if __name__ == '__main__':
    raise SystemExit(main())
