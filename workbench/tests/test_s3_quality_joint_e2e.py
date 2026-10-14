"""S3/T-076 joint contracts through real CLI, relay, Panes, gates and Git.

Expected behavior is from T-077 Acceptance/R8 and spec sections 3, 4 and 8.
Only PTY/process/native inputs and external worker/reviewer decisions are
controlled. No gate result, state row or review verdict is inserted directly.
"""
import argparse
import json
from pathlib import Path
import sys

from test_quality_chain_e2e import run_cases, save
from test_quality_tracer_e2e import Tracer


class Joint(Tracer):
    def external(self, files, message):
        for name, content in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        self.git('add', *files)
        self.git('commit', '-m', message)
        return self.oid()

    def integrate_current(self, candidate, head):
        before = self.cli('status')['task']
        expected = before['verification']['M']
        reply = self.gate('integrate', '--attempt', self.a['attempt_id'], '--score-file', self.score_file())
        self.check('JOINT-INTEGRATE', reply['ok'] and self.oid() == expected
                   and reply['task']['state'] == 'accepted',
                   {'state': 'accepted', 'main': expected}, reply)
        for ancestor in (candidate, head):
            result = self.process(['git', '-C', self.repo, 'merge-base', '--is-ancestor', ancestor, expected])
            self.check('JOINT-ANCESTOR', result.returncode == 0, ancestor, result.returncode)
        self.check('JOINT-SCORE-ONCE', len([e for e in self.events() if e['type'] == 'score_recorded']) == 1,
                   'one score after real integration', self.events())

    def same_candidate_reuses_review(self):
        marker = self.root / 'independent-rule.jsonl'
        self.write_rule_config('from pathlib import Path\nimport json,os\n'
            'value=Path("host.txt").read_text()\n'
            'assert value in ("base host\\n","external G\\n")\n'
            'with open(' + repr(str(marker)) + ',"a") as out: out.write(json.dumps({"cwd":os.getcwd(),"host":value})+"\\n")')
        a, c = self.good_submission()
        review, _ = self.approve(c)
        initial = self.cli('status')['task']['verification']
        g = self.external({'host.txt': 'external G\n'}, 'Independent G after review of unchanged C')
        reply = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', self.score_file())
        current = self.cli('status')['task']
        events = self.events()
        requests = [e for e in events if e['type'] == 'review_requested']
        results = [e for e in events if e['type'] == 'review_result']
        reused = [e for e in events if e['type'] == 'review_reused']
        v = current['verification']
        self.check('JOINT-SAME-C-REUSE', reply['ok'] and current['state'] == 'accepted'
                   and v['verification_id'] != initial['verification_id'] and v['G'] == g and v['C'] == c
                   and len(requests) == len(results) == len(reused) == 1
                   and current['review']['review_id'] == review['review_id']
                   and reused[0]['details']['verification_id'] == v['verification_id'],
                   'new G/M mechanical verification, same C and one valid independent review',
                   {'reply': reply, 'task': current, 'requests': requests, 'results': results, 'reuse': reused})
        ids = [initial['verification_id'], v['verification_id']]
        for kind in ('path_check', 'completion_check', 'rule_check'):
            self.check('JOINT-SAME-C-MECHANICAL-' + kind,
                       [e['details']['verification_id'] for e in events if e['type'] == kind] == ids,
                       ids, [e for e in events if e['type'] == kind])
        self.check('JOINT-SAME-C-RULE-INPUTS',
                   [json.loads(line)['host'] for line in marker.read_text().splitlines()] == ['base host\n', 'external G\n'],
                   ['base host\n', 'external G\n'], marker.read_text())
        self.check('JOINT-SAME-C-GIT', self.oid() == v['M']
                   and (self.repo / 'host.txt').read_text() == 'external G\n', v['M'], self.oid())
        save(self.evidence / 'joint-proof.json', {'task': current, 'events': events, 'C': c, 'G': g, 'main': self.oid()})

    def changed_candidate_starts_fresh_review(self):
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', '-c',
            'from pathlib import Path; expected="worker2\\n" if Path("host.txt").read_text()=="phase2\\n" else "worker\\n"; '
            'assert Path("src/value.txt").read_text()==expected']}]
        a, c1 = self.good_submission()
        prior, record1 = self.approve(c1)
        g = self.external({'host.txt': 'phase2\n'}, 'Independent G changes completion requirement')
        refused = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', self.score_file())
        self.check('JOINT-NEW-C-REJECTION', refused.get('error') == 'oracle_failed' and self.oid() == g,
                   'new M fails its independent completion assertion and opens repair', refused)
        self.wait_pane(lambda pane: pane['state'] == 'busy' and pane['turn'] == 'fixture-turn-3')
        c2 = self.commit(a, {'src/value.txt': 'worker2\n'})
        submitted = self.worker_submit(c2, request_id='delivery-2')
        self.check('JOINT-NEW-C-SUBMIT', submitted['ok'], 'explicit new C from the bound repair turn', submitted)
        reply = self.gate('verify', '--attempt', a['attempt_id'])
        current = self.cli('status')['task']
        review = current.get('review') or {}
        self.check('JOINT-NEW-C-REVIEW', reply['ok'] and current['state'] == 'reviewing'
                   and review.get('candidate_commit') == c2 and review.get('review_id') != prior['review_id']
                   and review.get('session_id') != prior['session_id'] and review.get('launch_id') != prior['launch_id']
                   and self.oid() == g,
                   'C2 needs a new reviewer/session/launch before any integration', current)
        other, record2 = self.approve(c2, automatic=True)
        self.check('JOINT-NEW-C-NATIVE', record2['native'] != record1['native'], 'fresh reviewer native identity',
                   {'first': record1['native'], 'next': record2['native']})
        self.integrate_current(c2, g)
        events = self.events()
        self.check('JOINT-NEW-C-TWO-REVIEWS',
                   [e['details']['review']['candidate_commit'] for e in events if e['type'] == 'review_result'] == [c1, c2]
                   and not [e for e in events if e['type'] == 'review_reused'],
                   'separate durable independent results for C1 and C2', events)
        save(self.evidence / 'joint-proof.json', {'C1': c1, 'C2': c2, 'G': g, 'review': other,
             'task': self.cli('status')['task'], 'events': events, 'main': self.oid()})

    def conflict_then_quality_repair_submits_again(self):
        self.card['goal'] = 'worker 与 host 设置都为 ready；保留 host-policy.txt'
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', '-c',
            'import json; from pathlib import Path; '
            'assert json.loads(Path("src/settings.json").read_text())=={"worker":"ready","host":"ready"}; '
            'assert Path("host-policy.txt").read_text()=="host policy\\n"']}]
        self.base = self.external({'src/settings.json': '{"worker":"base","host":"base"}\n',
                                  'host-policy.txt': 'baseline\n'}, 'Independent joint conflict baseline')
        a = self.start_worker()
        c1 = self.commit(a, {'src/settings.json': '{"worker":"ready","host":"base"}\n'})
        first = self.worker_submit(c1)
        self.check('JOINT-CONFLICT-C1', first['ok'], 'C1 explicitly submitted', first)
        g = self.external({'src/settings.json': '{"worker":"base","host":"ready"}\n',
                           'host-policy.txt': 'host policy\n'}, 'Independent same-line host conflict')
        conflict = self.gate('verify', '--attempt', a['attempt_id'])
        self.check('JOINT-CONFLICT-WRITEBACK', conflict.get('error') == 'merge_conflict'
                   and self.cli('status')['task']['state'] == 'rework' and self.oid() == g,
                   'real same-line conflict opens worker rework without integrating', conflict)
        self.wait_pane(lambda pane: pane['state'] == 'busy' and pane['turn'] == 'fixture-turn-3')
        # This is the external worker actor in its own temporary worktree.
        # The product gate does not reset or choose conflict content.
        self.git('reset', '--hard', g, cwd=a['workspace'])
        c2 = self.commit(a, {'src/settings.json': '{"worker":"almost","host":"ready"}\n'})
        second = self.worker_submit(c2, request_id='delivery-2')
        self.check('JOINT-CONFLICT-C2', second['ok'], 'conflict rework C2 explicitly submitted', second)
        rejected = self.gate('verify', '--attempt', a['attempt_id'])
        self.check('JOINT-CONFLICT-QUALITY', rejected.get('error') == 'oracle_failed' and self.oid() == g,
                   'C2 is rejected by the independent completion condition', rejected)
        self.wait_pane(lambda pane: pane['state'] == 'busy' and pane['turn'] == 'fixture-turn-5')
        c3 = self.commit(a, {'src/settings.json': '{"worker":"ready","host":"ready"}\n'})
        third = self.worker_submit(c3, request_id='delivery-3')
        self.check('JOINT-CONFLICT-QUALITY-SUBMIT', third['ok'] and third['task']['candidate_commit'] == c3,
                   'same bound rework attempt may explicitly deliver C3 after quality rejection', third)
        verified = self.gate('verify', '--attempt', a['attempt_id'])
        self.check('JOINT-CONFLICT-C3-REVIEW', verified['ok'] and verified['task']['state'] == 'reviewing'
                   and verified['task']['review']['candidate_commit'] == c3,
                   'C3 repeats all mechanical gates and starts independent review', verified)
        self.approve(c3, automatic=True)
        self.integrate_current(c3, g)
        task = self.cli('status')['task']; events = self.events()
        checks = [e for e in events if e['type'] == 'completion_check']
        self.check('JOINT-CONFLICT-FULL-CHAIN', len(checks) == 2
                   and [e['details']['passed'] for e in checks] == [False, True]
                   and len([e for e in events if e['type'] == 'path_check']) == 2
                   and len([e for e in events if e['type'] == 'review_result']) == 1
                   and task['current_attempt']['attempt_id'] == a['attempt_id']
                   and task['current_attempt']['rework']['candidate_commit'] == c3
                   and task['current_attempt']['rework']['base_commit'] == g,
                   'same attempt, immutable recorded G, failed C2 then passed/reviewed/integrated C3',
                   {'task': task, 'events': events})
        save(self.evidence / 'joint-proof.json', {'C1': c1, 'C2': c2, 'C3': c3, 'G': g,
             'task': task, 'events': events, 'main': self.oid()})


CASES = ['same_candidate_reuses_review', 'changed_candidate_starts_fresh_review',
         'conflict_then_quality_repair_submits_again']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    args = parser.parse_args()
    return run_cases(args.source, args.output, args.case or CASES, Joint, dialect='current', stop_on_failure=True)


if __name__ == '__main__':
    raise SystemExit(main())
