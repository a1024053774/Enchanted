"""T-080：真实 CLI/daemon/relay/Git 的验收文件正反例；无真实模型。"""
import argparse
import copy
import json
from pathlib import Path
import sys

from test_quality_chain_e2e import HarnessFailure, run_cases, save
from test_quality_tracer_e2e import Tracer


CRITERION = 'acceptance/criterion.py'
ORIGINAL = ('from pathlib import Path\n'
            'assert Path("src/value.txt").read_text() == "worker\\n", '
            '"independent required product value"\n')


class ProtectedAcceptance(Tracer):
    def id(self):
        return 'T-080.' + self.case

    def prepare(self, directory=False):
        (self.repo / CRITERION).write_text(ORIGINAL, encoding='utf-8')
        self.git('add', CRITERION)
        self.git('commit', '-m', 'Freeze independent T-080 acceptance input')
        self.base = self.oid()
        self.card.update(paths={'allow': ['.'], 'deny': []},
                         oracle_paths=['acceptance/'] if directory else [CRITERION],
                         completion_conditions=[{'argv': [sys.executable, '-I', '-B', CRITERION]}])
        save(self.evidence / 'independent-input.json', {'criterion': ORIGINAL, 'required_value': 'worker\n',
             'oracle_paths': self.card['oracle_paths'], 'base': self.base})

    def delivered(self, files):
        a = self.start_worker()
        c = self.commit(a, files)
        value = self.worker_submit(c)
        if not value['ok']:
            raise HarnessFailure('合法身份的候选没有完成显式 submit：' + json.dumps(value))
        return a, c

    def refuse_oracle(self, expected_paths, count=1):
        ref = self.oid()
        log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        before = self.events()
        messages = self.gate_messages()
        value = self.gate('verify', '--attempt', self.a['attempt_id'])
        # This literal business assertion must fail when only the new check is removed.
        self.check('ORACLE-MODIFIED', value.get('ok') is False and value.get('error') == 'oracle_modified',
                   {'ok': False, 'error': 'oracle_modified'}, value)
        task = self.cli('status')['task']
        events = self.events()[len(before):]
        checks = [e for e in events if e['type'] == 'oracle_check']
        self.check('ORACLE-PATHS', len(checks) == 1 and checks[0]['details']['modified'] == sorted(expected_paths)
                   and checks[0]['details']['passed'] is False
                   and checks[0]['details']['card_snapshot_id'] == self.a['card_snapshot_id'],
                   {'modified': sorted(expected_paths), 'snapshot': self.a['card_snapshot_id']}, checks)
        types = [e['type'] for e in events]
        rejected = [e for e in events if e['type'] == 'delivery_rejected']
        self.check('ORACLE-BEFORE-COMPLETION', types.index('path_check') < types.index('oracle_check')
                   and not any(t in types for t in ('completion_intent', 'completion_check', 'review_requested', 'integrated')),
                   '路径边界通过后拒收，完成条件与审查未执行', types)
        self.check('ORACLE-REPAIR', len(rejected) == 1 and task['repair']['check'] == 'oracle'
                   and task['repair']['count'] == count and task['repair']['failure']['details']['modified'] == sorted(expected_paths)
                   and task['current_attempt']['attempt_id'] == self.a['attempt_id'],
                   {'check': 'oracle', 'count': count, 'modified': sorted(expected_paths)}, task)
        self.check('ORACLE-NO-INTEGRATION', self.oid() == ref
                   and self.git('reflog', 'show', '--format=%H', 'refs/heads/main') == log
                   and not any(e['type'] in ('integrated', 'score_recorded') for e in self.events()),
                   {'ref': ref, 'reflog': log}, {'ref': self.oid(), 'state': task['state']})
        if count < 3:
            pane = self.wait_pane(lambda p: p['state'] == 'busy')
            feedback = self.gate_messages()[len(messages):]
            self.check('ORACLE-FEEDBACK', len(feedback) == 1 and feedback[0]['launch'] == self.launch
                       and feedback[0]['data']['context']['kind'] == 'quality-repair'
                       and 'oracle_modified' in json.dumps(feedback[0]['data'])
                       and all(path in json.dumps(feedback[0]['data']) for path in expected_paths)
                       and pane['native_session'] == self.native['native'],
                       '回写原 worker，包含拒收码及具体路径', feedback)
            writes = self.read_lines(self.control / 'writes.jsonl')
            self.check('ORACLE-PTY-WRITE', any(row['data'].startswith('\x1b[200~⟦门禁 #')
                       and 'oracle_modified' in row['data'] for row in writes), '门禁反馈实际写入受控 PTY', writes)
        else:
            self.check('ORACLE-THREE-LIMIT', task['state'] == 'paused' and task['repair']['stopped']
                       and len(self.gate_messages()) == len(messages), '第三次打回暂停，停止自动回写', task)
        save(self.evidence / ('rejection-%d.json' % count), {'reply': value, 'events': events, 'task': task,
             'ref': ref, 'candidate': task['candidate_commit']})

    def oracle_modified(self):
        self.prepare()
        probe = self.process([sys.executable, '-I', '-B', CRITERION], cwd=self.repo)
        if probe.returncode != 1 or 'AssertionError: independent required product value' not in probe.stderr:
            raise HarnessFailure('原始验收文件没有在要求的业务断言上失败。')
        a, c = self.delivered({CRITERION: 'pass\n'})
        changed = self.git('diff', '--name-only', a['base_commit'], c).splitlines()
        if changed != [CRITERION]:
            raise HarnessFailure('复验必须与 red-02 一样只篡改完成条件调用的测试。')
        self.refuse_oracle([CRITERION])
        self.check('ORACLE-PRODUCT-STILL-BAD', (self.repo / 'src/value.txt').read_text() == 'base\n',
                   'base\n', (self.repo / 'src/value.txt').read_text())

    def oracle_directory_added(self):
        self.prepare(directory=True)
        self.delivered({'acceptance/always_pass.py': 'pass\n', 'src/value.txt': 'worker\n'})
        self.refuse_oracle(['acceptance/always_pass.py'])

    def oracle_deleted(self):
        self.prepare()
        a = self.start_worker()
        (Path(a['workspace']) / CRITERION).unlink()
        c = self.commit(a, {'src/value.txt': 'worker\n'})
        if not self.worker_submit(c)['ok']:
            raise HarnessFailure('删除测试候选未完成显式 submit。')
        self.refuse_oracle([CRITERION])

    def oracle_renamed(self):
        self.prepare()
        a = self.start_worker()
        (Path(a['workspace']) / CRITERION).rename(Path(a['workspace']) / 'replacement.py')
        c = self.commit(a, {'src/value.txt': 'worker\n'})
        if not self.worker_submit(c)['ok']:
            raise HarnessFailure('重命名测试候选未完成显式 submit。')
        self.refuse_oracle([CRITERION])

    def oracle_correct_delivery(self):
        self.prepare(directory=True)
        _, c = self.delivered({'src/value.txt': 'worker\n', 'acceptance-other/sentinel.py': 'pass\n'})
        self.approve(c)
        self.integrate_scored(c, rounds=1)
        check = next(e for e in self.events() if e['type'] == 'oracle_check')
        self.check('ORACLE-CORRECT', check['details']['modified'] == [] and check['details']['passed'],
                   '正确交付通过，目录前缀不误伤相邻目录', check)

    def oracle_repair_score(self):
        self.prepare()
        a, _ = self.delivered({CRITERION: 'pass\n'})
        self.refuse_oracle([CRITERION])
        c = self.commit(a, {CRITERION: ORIGINAL, 'src/value.txt': 'worker\n'})
        if not self.worker_submit(c, request_id='delivery-2')['ok']:
            raise HarnessFailure('原 attempt 修复后显式重交失败。')
        self.approve(c)
        self.integrate_scored(c, rounds=2, oracle_failures=1)
        events = self.events()
        scores = [e['details'] for e in events if e['type'] == 'score_recorded']
        rejects = [e for e in events if e['type'] == 'delivery_rejected' and e['details']['repair']['check'] == 'oracle']
        self.check('ORACLE-SCORE', len(rejects) == scores[0]['facts']['rejections']['oracle'] == 1
                   and scores[0]['facts']['rejections']['path_boundary'] == 0,
                   'oracle 单列且与事件一致，路径边界计数不变', scores)

    def oracle_three_rejections(self):
        self.prepare()
        a = self.start_worker()
        for number in range(1, 4):
            c = self.commit(a, {CRITERION: 'pass  # invalid round %d\n' % number})
            if not self.worker_submit(c, request_id='delivery-%d' % number)['ok']:
                raise HarnessFailure('三次拒收夹具的合法重交失败。')
            self.refuse_oracle([CRITERION], number)
        events = self.events()
        task = self.cli('status')['task']
        repair = task['repair']
        rejected = [e['details']['repair'] for e in events if e['type'] == 'delivery_rejected'
                    and e['attempt'] == a['attempt_id']]
        self.check('ORACLE-LIMIT-COUNTS', [r['count'] for r in rejected] == [1, 2, 3]
                   and all(r['check'] == 'oracle' and r['failure']['error'] == 'oracle_modified' for r in rejected)
                   and task['state'] == 'paused' and repair['count'] == 3 and repair['stopped'] is True
                   and task['current_attempt']['attempt_id'] == a['attempt_id'] and task['fence'] == a['fence'],
                   '原 attempt 的三次 oracle 打回计数为 1/2/3，第三次进入暂停', {'task': task, 'rejections': rejected})
        issues = [e['details'] for e in events if e['type'] == 'issue_issue'
                  and e['details']['attempt_id'] == a['attempt_id']]
        self.check('ORACLE-LIMIT-ESCALATION', len(issues) == 1 and issues[0]['from'] == 'system'
                   and issues[0]['to'] == 'executor' and issues[0]['blocking'] is True
                   and json.loads(issues[0]['body']) == repair,
                   '第三次打回将同一 repair 的阻塞问题交给执行主控', issues)
        stopped = [e for e in self.orchestration() if e['type'] == 'quality_feedback_stopped'
                   and e['launch'] == self.launch and e['attempt'] == a['attempt_id']]
        messages = self.gate_messages()
        repair_messages = [m for m in messages if m['data'].get('context', {}).get('kind') == 'quality-repair']
        pane = self.gate('pane_status', '--thread', a['thread_id'], task=False)
        self.check('ORACLE-LIMIT-STOP-EVENT', len(stopped) == 1 and stopped[0]['data']['repair'] == repair
                   and len(repair_messages) == 2 and all(m['launch'] == self.launch for m in repair_messages)
                   and pane['state'] == 'idle' and not pane['queued'] and not pane['writing'],
                   '原 worker 已停止自动回写：只回写前两次，停止事件绑定第三次 repair，窗格空闲且队列为空',
                   {'stopped': stopped, 'messages': messages, 'pane': pane})
        # Spec §3 and T-076 require pause/escalation and no further automatic work.
        # They do not promise one error code for replaying verify on a paused task.
        before = self.events()
        ref = self.oid()
        reflog = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        reply = self.gate('verify', '--attempt', a['attempt_id'])
        after = self.events()
        current = self.cli('status')['task']
        after_pane = self.gate('pane_status', '--thread', a['thread_id'], task=False)
        progress = {'verification_intent', 'merge_candidate', 'path_check', 'oracle_check', 'completion_intent',
                    'completion_check', 'red_check', 'rule_check', 'trailer_check', 'review_requested',
                    'delivery_rejected', 'integrated'}
        self.check('ORACLE-LIMIT-REPLAY', reply.get('ok') is False and current['state'] == 'paused'
                   and current['repair'] == repair and current['candidate_commit'] == task['candidate_commit']
                   and current['current_attempt']['attempt_id'] == a['attempt_id'] and current['fence'] == a['fence']
                   and current['verification']['verification_id'] == task['verification']['verification_id']
                   and len([e for e in after if e['type'] == 'delivery_rejected']) == 3
                   and not any(e['type'] in progress for e in after[len(before):])
                   and self.gate_messages() == messages and after_pane['state'] == 'idle'
                   and not after_pane['queued'] and not after_pane['writing'] and self.oid() == ref
                   and self.git('reflog', 'show', '--format=%H', 'refs/heads/main') == reflog,
                   '暂停后的 verify 必须拒绝且不推进：repair/候选/attempt/fence 不变，不重跑、不再回写或集成',
                   {'reply': reply, 'task': current, 'new_events': after[len(before):], 'pane': after_pane})
        save(self.evidence / 'limit-replay.json', {'reply': reply, 'task': current,
             'new_events': after[len(before):], 'stop_events': stopped, 'issues': issues,
             'messages': messages, 'pane': after_pane, 'ref': ref})

    def oracle_schema(self):
        self.prepare()
        variants = [None, [], 'acceptance/criterion.py', ['.'], ['/absolute'], ['../outside'],
                    ['a/../b'], ['*.py'], ['a?.py'], ['a[0].py'], ['.git/config'],
                    ['x/.Git/'], ['a\\b'], ['a//b'], ['a/./b']]
        for index, value in enumerate(variants):
            card = copy.deepcopy(self.card)
            if value is None:
                del card['oracle_paths']
            else:
                card['oracle_paths'] = value
            self.card_file.write_text(json.dumps(card), encoding='utf-8')
            reply = self.gate('card_validate', '--card', self.card_file)
            self.check('ORACLE-SCHEMA-%d' % index, reply.get('error') == 'invalid_task_card',
                       {'invalid_oracle_paths': value}, reply)
            if index < 2:
                saved = self.gate('card_save', '--card', self.card_file, '--expected-version', '0')
                self.check('ORACLE-SAVE-REQUIRED-%d' % index, saved.get('error') == 'invalid_task_card',
                           '缺字段或空数组不能保存卡片', saved)
        for rule in (CRITERION, 'acceptance/'):
            card = copy.deepcopy(self.card)
            card['oracle_paths'] = [rule]
            card['red_commands'] = [{'argv': [sys.executable, '-c', 'pass'], 'test_paths': [CRITERION]}]
            self.card_file.write_text(json.dumps(card), encoding='utf-8')
            reply = self.gate('card_validate', '--card', self.card_file)
            self.check('ORACLE-RED-OVERLAP', reply.get('error') == 'invalid_task_card',
                       '验收文件与红态测试不得有交集', reply)
        card['red_commands'][0]['test_paths'] = ['acceptance-other/red.py']
        self.card_file.write_text(json.dumps(card), encoding='utf-8')
        reply = self.gate('card_validate', '--card', self.card_file)
        self.check('ORACLE-RED-DISJOINT', reply['ok'], '相邻目录不构成交集', reply)

    def oracle_claim_missing(self):
        self.prepare()
        self.card['oracle_paths'] = [CRITERION, 'not-in-base.py', 'empty/']
        (self.repo / 'empty').mkdir()
        (self.repo / 'empty/untracked.py').write_text('pass\n', encoding='utf-8')
        self.registered()
        ref = self.oid()
        reply = self.gate('claim', '--owner', 'independent-fixture')
        task = self.cli('status')['task']
        self.check('ORACLE-CLAIM-MISSING', reply.get('error') == 'oracle_not_found'
                   and sorted(reply['details']['missing']) == ['empty/', 'not-in-base.py']
                   and task['current_attempt'] is None and task['fence'] == 0 and self.oid() == ref,
                   '只查起点 Git tree；缺路径在创建 attempt/worktree 前拒绝', {'reply': reply, 'task': task})
        self.check('ORACLE-NO-WORKTREE', not (self.state / 'worktrees').exists(), '未创建 worktree', str(self.state))

    def oracle_claim_current_base(self):
        self.prepare()
        self.card['oracle_paths'] = ['late/']
        self.registered()
        (self.repo / 'late').mkdir()
        (self.repo / 'late/criterion.py').write_text(ORIGINAL, encoding='utf-8')
        self.git('add', 'late/criterion.py')
        self.git('commit', '-m', 'Acceptance file committed after registration before claim')
        current = self.oid()
        reply = self.gate('claim', '--owner', 'independent-fixture')
        self.check('ORACLE-CLAIM-BASE', reply['ok'] and reply['attempt']['base_commit'] == current,
                   '存在性按认领时头，目录前缀至少一个受控文件', reply)

    def oracle_boundary_first(self):
        self.prepare()
        self.card['paths']['deny'] = ['forbidden.py']
        _, _ = self.delivered({CRITERION: 'pass\n', 'forbidden.py': 'pass\n'})
        before = len(self.events())
        reply = self.gate('verify', '--attempt', self.a['attempt_id'])
        types = [e['type'] for e in self.events()[before:]]
        self.check('ORACLE-BOUNDARY-FIRST', reply.get('error') == 'path_boundary_failed'
                   and 'oracle_check' not in types and 'completion_check' not in types,
                   '路径边界失败时先打回，不进入验收文件检查', {'reply': reply, 'events': types})

    def oracle_card_snapshot(self):
        self.prepare()
        a, _ = self.delivered({CRITERION: 'pass\n'})
        later = copy.deepcopy(self.card)
        later['oracle_paths'] = ['host.txt']
        self.save_card(1, later)
        self.check('ORACLE-SNAPSHOT-VERSION', self.cli('status')['task']['card_version'] == 1
                   and self.cli('card_show', '--card-version', '2')['card']['oracle_paths'] == ['host.txt'],
                   '保存新卡不更换当前 attempt 的冻结快照', a['card_snapshot_id'])
        self.refuse_oracle([CRITERION])


CASES = ['oracle_modified', 'oracle_directory_added', 'oracle_deleted', 'oracle_renamed',
         'oracle_correct_delivery', 'oracle_repair_score', 'oracle_three_rejections',
         'oracle_schema', 'oracle_claim_missing', 'oracle_claim_current_base', 'oracle_boundary_first', 'oracle_card_snapshot']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    args = parser.parse_args()
    return run_cases(args.source, args.output, args.case or CASES, ProtectedAcceptance, dialect='current')


if __name__ == '__main__':
    raise SystemExit(main())
