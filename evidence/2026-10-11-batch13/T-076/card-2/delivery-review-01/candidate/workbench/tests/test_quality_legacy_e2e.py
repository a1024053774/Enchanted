"""Decision 02/03 provenance refusal and preserved managed frozen-candidate proof."""
import argparse
from pathlib import Path

import test_quality_chain_e2e as q
from test_quality_chain_e2e import run_cases, save
from test_quality_tracer_e2e import Tracer
from legacy_quality_driver import QualityDriver


class LegacyQuality(Tracer):
    def begin_worker_turn(self, stage, previous_turn, next_turn):
        before = self.gate('pane_status', '--thread', self.a['thread_id'], task=False)
        self.check('MANAGED-FROZEN-IDLE-' + stage, before['state'] == 'idle' and before['active'] is None
                   and before['turn'] == previous_turn and not before['writing'] and not before['queued']
                   and before['failed'] is None and before['native_session'] == self.native['native'],
                   'previous receipt ended; the original worker needs explicit new input', before)
        body = self.root / ('controlled-input-' + stage + '.txt')
        body.write_text('受控夹具下一回合：' + stage + '。保持原attempt；没有质量打回授权。\n', encoding='utf-8')
        self.gate('pane_dispatch', '--thread', self.a['thread_id'], '--body-file', body, task=False)
        active = self.wait_pane(lambda p: p['state'] == 'busy' and p['turn'] == next_turn)
        current = self.cli('status')['task']
        self.check('MANAGED-FROZEN-ACTIVE-' + stage, active['active']['nativeTurn'] == next_turn
                   and active['native_session'] == self.native['native'] and current['repair'] is None
                   and current['current_attempt']['attempt_id'] == self.a['attempt_id'],
                   'registered input starts a new turn without authorizing candidate replacement', current)
        save(self.evidence / ('turn-boundary-' + stage + '.json'), {'before': before, 'active': active, 'task': current})

    def manual_claim_reviewed_score_refused(self):
        a, c = self.manual_candidate()
        driver = QualityDriver(q.base.GATE, self.state, self.control, self.env)
        driver.preparation(self.task, a, '手工 claim')
        self.cli('verify')
        reviewed = driver.complete_review(self.task, a, c)
        self.check('MANUAL-CLAIM-PRECONDITIONS', not a['thread_id'] and not reviewed['current_attempt'].get('delivery')
                   and reviewed['review']['result']['verdict'] == '可合并' and reviewed['review']['candidate_commit'] == c,
                   'valid independent review with no managed worker launch provenance', reviewed)
        before = self.oid(); log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        contents = (self.repo / 'src/value.txt').read_bytes()
        value = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', driver.score_file(a))
        events = self.events()
        # A mutant may still return a score error AFTER changing Git. That must fail.
        self.check('MANUAL-CLAIM-SOURCE', value.get('error') == 'score_provenance_required'
                   and self.oid() == before and self.git('reflog', 'show', '--format=%H', 'refs/heads/main') == log
                   and (self.repo / 'src/value.txt').read_bytes() == contents
                   and self.cli('status')['task']['state'] == 'verified'
                   and not any(e['type'] == 'score_recorded' for e in events)
                   and any(e['type'] == 'rejected' and e['details'].get('error') == 'score_provenance_required'
                           and e['details']['input']['command'] == 'integrate' for e in events),
                   'refuse before Git or final score; retain a specific rejection', {'reply': value, 'ref': self.oid(), 'events': events})

    def managed_frozen_candidate_integrates_original(self):
        a = self.start_worker(); c = self.commit(a)
        path = Path(a['workspace']) / 'src/value.txt'
        path.write_text('dirty candidate\n', encoding='utf-8')
        refused = self.worker_submit(c, request_id='dirty')
        self.check('MANAGED-FROZEN-DIRTY', not refused['ok'] and self.cli('status')['task']['candidate_commit'] is None,
                   'dirty workspace cannot submit', refused)
        self.begin_worker_turn('clean-head', 'fixture-turn-2', 'fixture-turn-3')
        self.git('checkout', '--', 'src/value.txt', cwd=Path(a['workspace']))
        directory = Path(self.native['env']['A2A_REQUEST_DIR'])
        common = dict(schema=1, command='submit', task=self.task, attempt=a['attempt_id'], session=a['session_id'],
                      fence=a['fence'], spec_rev=a['spec_rev'])
        for name, value in [('00-short', c[:12]), ('01-base', self.base), ('zz-duplicate', c)]:
            save(directory / (name + '.json'), {**common, 'request_id': name, 'commit': value})
        submitted = self.worker_submit(c, request_id='delivery')
        self.check('MANAGED-FROZEN-HEAD', submitted['ok'] and not self.relay_result('00-short')['ok']
                   and not self.relay_result('01-base')['ok'] and self.relay_result('zz-duplicate')['ok'],
                   'full clean HEAD succeeds exactly once; short SHA/base fail', self.cli('status')['task'])
        frozen = self.cli('status')['task']
        self.begin_worker_turn('frozen-candidate', 'fixture-turn-4', 'fixture-turn-5')
        later_bad = self.commit(a, {'src/value.txt': 'not the independent required content\n'})
        refused = self.worker_submit(later_bad, request_id='later-bad')
        current = self.cli('status')['task']
        self.check('MANAGED-FROZEN-CANDIDATE', not refused['ok'] and current['candidate_commit'] == c
                   and current['current_attempt']['delivery'] == frozen['current_attempt']['delivery'],
                   'no rejection authorization: C cannot be replaced', {'reply': refused, 'task': current})
        self.approve(c)
        self.integrate_scored(c, rounds=1, identity_failures=4)
        self.check('MANAGED-FROZEN-INTEGRATION', self.oid() == c and self.oid() != later_bad,
                   'integrate the verified frozen C, never the later worktree HEAD', self.oid())


CASES = ['manual_claim_reviewed_score_refused', 'managed_frozen_candidate_integrates_original']
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    args = parser.parse_args()
    raise SystemExit(run_cases(args.source, args.output, args.case or CASES, LegacyQuality, dialect='current', stop_on_failure=True))
