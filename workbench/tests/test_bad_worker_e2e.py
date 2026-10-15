"""T-081：真实门禁入口的坏 worker 输入；PTY 与模型记录为受控夹具。"""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import traceback

import test_quality_chain_e2e as chain
from test_quality_chain_e2e import HarnessFailure, run_cases, save
from test_quality_tracer_e2e import Tracer


REFUSALS = {
    'oracle_test': 'oracle_modified',
    'oracle_entry': 'oracle_modified',
    'self_report_unchanged': 'oracle_failed',
    'self_report_wrong': 'oracle_failed',
    'stale_attempt': 'stale_attempt',
    'deny_path': 'path_boundary_failed',
    'trailer_partial': 'invalid_trailers',
    'trailer_duplicate': None,  # 身份冲突必须拒收；具体错误码是运行观察，不作为规范 oracle。
    'trailer_task': 'trailer_task_mismatch',
    'trailer_attempt': 'trailer_identity_mismatch',
}
NEGATIVES = [*REFUSALS, 'after_review']
ABSENT = ['trailer_absent']
ABSENT_EXPECTATION = '完全无尾注恰好记一次人工介入并集成'
ABSENT_BASIS = ['workbench/README.md#完全无 A2A 尾注',
                '.project-map/inbox/20261015T030558Z-ideation-answer-001.md']
IDENTITY_EXPECTATION = '尾注含本会话与其他会话的矛盾身份，必须拒收；实际拒收码单列记录'
IDENTITY_BASIS = ['.project-map/specs/native-cli-orchestration-2026-10-10.md#第8节',
                  '.project-map/tickets/T-072-traceability-scoring-retrospective-metrics.md#提交追溯',
                  '主控 #181：每项尾注必须能追溯到本 attempt/会话']
POSITIVES = ['positive_single', 'positive_multi', 'positive_red_card']
TRACE_FIELDS = {'probe_launch': 'Launch', 'probe_model': 'Model',
                'probe_effort': 'Effort', 'probe_tool': 'Tool'}
PROBES = list(TRACE_FIELDS)
TRACE_VALUES = {'Launch': '00000000-0000-4000-8000-000000000081',
                'Model': 'gpt-6-astra', 'Effort': 'low', 'Tool': 'codex-cli 0.162.0'}
# TRACE_VALUES are fixture commit text; actual sessions still request gpt-6.1-sol xhigh.


class BadWorker(Tracer):
    def id(self):
        return 'T-081.' + self.case

    def setUp(self):
        super().setUp()
        self.task = 'T-081-' + self.case.replace('_', '-')
        self.card['id'] = self.task
        save(self.evidence / 'input.json', {
            'case': self.case, 'product_value': 'worker\n',
            'criterion': "assert Path('src/value.txt').read_text() == 'worker\\n'",
            'oracle_paths': ['acceptance/criterion.py'],
            'expected_refusal': REFUSALS.get(self.case),
            'identity_expectation': IDENTITY_EXPECTATION if self.case == 'trailer_duplicate' else None,
            'expectation_basis': IDENTITY_BASIS if self.case == 'trailer_duplicate' else (
                ABSENT_BASIS if self.case == 'trailer_absent' else None),
            'absent_expectation': ABSENT_EXPECTATION if self.case == 'trailer_absent' else None,
            'trace_field': TRACE_FIELDS.get(self.case), 'trace_fixture_values': TRACE_VALUES,
            'real_codex_turns': 0,
        })

    def make_commit(self, attempt, files, *, changes=None, omit=(), duplicate=None,
                    message='T-081 controlled fixture delivery', empty=False):
        workspace = Path(attempt['workspace'])
        for name, value in files.items():
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value, encoding='utf-8')
        values = {
            'Task': self.task, 'Attempt': attempt['attempt_id'],
            'Session': attempt['session_id'], 'Role': 'worker',
            'Tool': 'codex-cli 0.162.1', 'Model': 'gpt-6.1-sol', 'Effort': 'xhigh',
            'Native-Session': self.native['native'] if attempt['thread_id'] else 'fixture-native',
            'Launch': self.launch if attempt['thread_id'] else 'fixture-launch',
        }
        values.update(changes or {})
        trailers = ['A2A-' + key + ': ' + value for key, value in values.items() if key not in omit]
        if duplicate:
            key, value = duplicate
            trailers.append('A2A-' + key + ': ' + value)
        self.git('add', '.', cwd=workspace)
        self.git('commit', *(['--allow-empty'] if empty else []),
                 '-m', message + '\n\n' + '\n'.join(trailers), cwd=workspace)
        candidate = self.oid(workspace)
        save(self.evidence / ('commit-' + candidate + '.json'), {
            'candidate': candidate, 'files': files, 'trailers': values,
            'omitted': list(omit), 'duplicate': duplicate,
            'message': self.git('show', '-s', '--format=%B', candidate),
        })
        return candidate

    def delivered(self, files, **kwargs):
        a = self.start_worker()
        candidate = self.make_commit(a, files, **kwargs)
        reply = self.worker_submit(candidate)
        if not reply['ok']:
            raise HarnessFailure('合法 submit 在目标检查之前失败：' + json.dumps(reply))
        return a, candidate

    def branch(self):
        return {'ref': self.oid(),
                'reflog': self.git('reflog', 'show', '--format=%H', 'refs/heads/main')}

    def refused(self, *, reply=None, before=None, prior_events=None):
        before = before or self.branch()
        prior_events = self.events() if prior_events is None else prior_events
        reply = reply or self.gate('verify', '--attempt', self.a['attempt_id'])
        current = self.cli('status')['task']
        after = self.events()
        fresh = after[len(prior_events):]
        expected = REFUSALS[self.case]
        actual = {'reply': reply, 'task': current, 'before': before, 'after': self.branch(),
                  'events': fresh, 'expected': expected, 'actual': reply.get('error')}
        matches = reply.get('error') == expected
        expectation = {'ok': False, 'error': expected}
        if self.case == 'trailer_duplicate':
            checks = [event for event in fresh if event['type'] == 'trailer_check'
                      and event['details'].get('commit') == self.duplicate_candidate]
            actual.update(expected=IDENTITY_EXPECTATION, expectation_basis=IDENTITY_BASIS,
                          expected_sessions=self.duplicate_sessions, trailer_checks=checks)
            save(self.evidence / 'duplicate-trailer-check.json', actual)
            self.check('BW-DUPLICATE-TARGET', len(checks) == 1
                       and checks[0]['details']['trailers'].get('session') == self.duplicate_sessions
                       and len(set(self.duplicate_sessions)) == 2,
                       '到达该提交的尾注检查，保留一真一假的两个 Session', checks)
            matches = (isinstance(reply.get('error'), str) and bool(reply['error'])
                       and checks[0]['details'].get('passed') is False
                       and checks[0]['details'].get('error') == reply['error'])
            expectation = {'ok': False, 'behavior': IDENTITY_EXPECTATION, 'code': '运行后记录'}
        save(self.evidence / 'observation.json', actual)
        self.check('BW-REJECT-' + self.case,
                   reply.get('ok') is False and matches, expectation, reply)
        self.check('BW-UNCHANGED-' + self.case,
                   actual['after'] == before and current['state'] != 'accepted'
                   and not any(e['type'] in ('integrated', 'score_recorded') for e in fresh),
                   '工作分支、reflog 与集成状态不推进', actual)
        self.check('BW-EVENT-' + self.case,
                   any(e['type'] == 'rejected' and e['details'].get('error') ==
                       (reply.get('error') if self.case == 'trailer_duplicate' else expected) for e in fresh),
                   '真实门禁追加对应拒收事件', fresh)
        integration = self.gate('integrate', '--attempt', current['current_attempt']['attempt_id'],
                                '--score-file', self.score_file())
        self.check('BW-NO-INTEGRATION-' + self.case,
                   integration.get('ok') is False and self.branch() == before,
                   '被拒的交付不能带分数集成', integration)

    def oracle_case(self, path):
        self.card['paths'] = {'allow': ['.'], 'deny': []}
        entry = self.repo / 'acceptance/entry.py'
        entry.write_text("import runpy\nrunpy.run_path('acceptance/criterion.py')\n", encoding='utf-8')
        self.git('add', 'acceptance/entry.py')
        self.git('commit', '-m', 'Freeze independent acceptance entry')
        self.card['oracle_paths'] = ['acceptance/criterion.py', 'acceptance/entry.py']
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', 'acceptance/entry.py']}]
        self.delivered({path: 'pass\n'})
        self.refused()
        types = [e['type'] for e in self.events()]
        self.check('BW-ORACLE-BEFORE-COMPLETION',
                   'oracle_check' in types and 'completion_intent' not in types and 'review_requested' not in types,
                   '改验收文件在执行该文件前拒收', types)

    def oracle_test(self):
        self.oracle_case('acceptance/criterion.py')

    def oracle_entry(self):
        self.oracle_case('acceptance/entry.py')

    def self_report_unchanged(self):
        self.delivered({}, message='所有测试通过', empty=True)
        self.refused()

    def self_report_wrong(self):
        self.delivered({'src/value.txt': 'wrong\n'}, message='所有测试通过')
        self.refused()

    def deny_path(self):
        self.delivered({'src/value.txt': 'worker\n', 'src/private/secret.txt': 'forbidden\n'})
        self.refused()

    def trailer_partial(self):
        self.delivered({'src/value.txt': 'worker\n'}, omit=('Effort',))
        self.refused()

    def trailer_duplicate(self):
        other = '00000000-0000-4000-8000-000000000181'
        a, candidate = self.delivered({'src/value.txt': 'worker\n'}, duplicate=('Session', other))
        self.check('BW-DUPLICATE-INPUT', a['session_id'] != other,
                   '第二个 Session 确实不是本会话', {'current': a['session_id'], 'other': other})
        self.duplicate_candidate, self.duplicate_sessions = candidate, [a['session_id'], other]
        self.refused()

    def trailer_task(self):
        self.delivered({'src/value.txt': 'worker\n'}, changes={'Task': 'T-081-another-task'})
        self.refused()

    def trailer_attempt(self):
        self.delivered({'src/value.txt': 'worker\n'}, changes={'Attempt': 't081-old-attempt'})
        self.refused()

    def stale_attempt(self):
        # A delayed scripted executor uses the same public submit command.
        # A dirty draft keeps its own old workspace available across revoke.
        self.registered()
        old = self.cli('claim', '--owner', 'old-scripted-worker')['attempt']
        candidate = self.make_commit(old, {'src/value.txt': 'worker\n'})
        draft = Path(old['workspace']) / 'old-worker-draft.txt'
        draft.write_text('保留迟到 worker 的目录\n', encoding='utf-8')
        self.cli('revoke', '--reason', 'explicit replacement for T-081 stale delivery')
        new = self.cli('claim', '--owner', 'new-scripted-worker')['attempt']
        draft.unlink()
        before, events = self.branch(), self.events()
        snapshot = self.cli('status')['task']
        reply = self.gate('submit', '--attempt', old['attempt_id'], '--session', old['session_id'],
                          '--fence', str(old['fence']), '--spec-rev', str(old['spec_rev']), '--commit', candidate)
        self.refused(reply=reply, before=before, prior_events=events)
        current = self.cli('status')['task']
        self.check('BW-NEW-ATTEMPT-PRESERVED',
                   current['current_attempt'] == snapshot['current_attempt']
                   and current['candidate_commit'] == snapshot['candidate_commit']
                   and current['fence'] == new['fence'],
                   '旧交付不得改变新 attempt 身份或候选', current)

    def after_review(self):
        a, c1 = self.delivered({'src/value.txt': 'worker\n'})
        self.approve(c1)
        c2 = self.make_commit(a, {'src/late.txt': 'unreviewed C2\n'})
        body = self.root / 'late-delivery.txt'
        body.write_text('T-081：在新的受控回合提交 C2。\n', encoding='utf-8')
        started = self.gate('pane_dispatch', '--thread', a['thread_id'], '--body-file', body, task=False)
        if not started['ok']:
            raise HarnessFailure('不能启动受控迟到回合。')
        self.wait_pane(lambda p: p['state'] == 'busy' and p['turn'] == 'fixture-turn-3')
        before = self.branch()
        late = self.worker_submit(c2, request_id='unreviewed-c2')
        task = self.cli('status')['task']
        save(self.evidence / 'late-submission.json', {'C1': c1, 'C2': c2, 'reply': late, 'task': task})
        self.check('BW-LATE-SUBMIT', late.get('error') == 'stale_turn'
                   and task['candidate_commit'] == c1 and self.branch() == before,
                   '新回合也不能替换已审查 C1', late)
        result = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', self.score_file())
        observed = {'reply': result, 'C1': c1, 'C2': c2, 'branch': self.branch(),
                    'actual': late.get('error') + '; integrated C1' if self.oid() == c1 else 'wrong integration target',
                    'files': self.git('ls-tree', '-r', '--name-only', 'refs/heads/main'),
                    'task': self.cli('status')['task'], 'events': self.events()}
        save(self.evidence / 'observation.json', observed)
        self.check('BW-FROZEN-INTEGRATION', result.get('ok') is True and self.oid() == c1
                   and 'src/late.txt' not in observed['files'].splitlines()
                   and observed['task']['verification']['C'] == c1
                   and observed['task']['integration_intent']['C'] == c1,
                   '仅集成已验收 C1，C2 新文件不进入工作分支', observed)

    def finish_positive(self, candidate):
        self.approve(candidate)
        self.integrate_scored(candidate, rounds=1)
        save(self.evidence / 'observation.json', {
            'actual': 'integrated', 'candidate': candidate, 'branch': self.branch(),
            'value': (self.repo / 'src/value.txt').read_text(encoding='utf-8'),
            'task': self.cli('status')['task'], 'events': self.events(),
        })
        self.check('BW-POSITIVE-CONTENT',
                   (self.repo / 'src/value.txt').read_text(encoding='utf-8') == 'worker\n',
                   '独立要求的产品值 worker', (self.repo / 'src/value.txt').read_text(encoding='utf-8'))

    def intervention_view(self):
        status = self.cli('status')
        interventions = [event for event in self.events() if event['type'] == 'human_intervention']
        return status, interventions, status['user_inputs']

    def trailer_absent(self):
        # One commit, every A2A field omitted. Partial, duplicate and wrong
        # task/attempt stay on the refusal cases.
        omitted = ('Task', 'Attempt', 'Session', 'Role', 'Tool', 'Model', 'Effort', 'Native-Session', 'Launch')
        attempt, candidate = self.delivered({'src/value.txt': 'worker\n'}, omit=omitted)
        body = self.git('show', '-s', '--format=%B', candidate)
        self.check('BW-ABSENT-INPUT', 'A2A-' not in body and body.strip() == 'T-081 controlled fixture delivery',
                   '提交说明只有受控正文，没有 A2A 尾注', body)
        self.approve(candidate)
        status, interventions, inputs = self.intervention_view()
        checks = [event for event in self.events() if event['type'] == 'trailer_check'
                  and event['details'].get('commit') == candidate]
        observed = {'expected': ABSENT_EXPECTATION, 'expectation_basis': ABSENT_BASIS,
                    'candidate': candidate, 'attempt': attempt['attempt_id'],
                    'intervention_count': len(interventions), 'interventions': interventions,
                    'user_inputs': inputs, 'trailer_checks': checks,
                    'before': self.branch(), 'task': status['task']}
        save(self.evidence / 'observation.json', observed)
        once = (len(checks) == 1 and checks[0]['details'].get('missing') is True
                and checks[0]['details'].get('passed') is True and checks[0]['details'].get('error') is None
                and len(interventions) == 1 and len(inputs) == 1
                and inputs[0]['form'] == 'action' and inputs[0]['certainty'] == 'inferred'
                and inputs[0]['channel'] == 'commit-trailer'
                and inputs[0]['source_ref']['label'] == '推断：缺尾注'
                and inputs[0]['source_ref']['commit'] == candidate
                and inputs[0]['target']['task'] == self.task
                and inputs[0]['target']['attempt'] == attempt['attempt_id']
                and interventions[0]['details']['input_id'] == inputs[0]['id']
                and interventions[0]['details']['attempt_id'] == attempt['attempt_id']
                and interventions[0]['details']['task_id'] == self.task
                and interventions[0]['details']['form'] == 'action'
                and interventions[0]['details']['channel'] == 'commit-trailer')
        self.check('BW-ABSENT-ONCE', once, ABSENT_EXPECTATION, observed)
        before_ref = self.oid()
        reply = self.gate('integrate', '--attempt', attempt['attempt_id'], '--score-file', self.score_file())
        integrated_log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        status, interventions, inputs = self.intervention_view()
        scores = [event['details'] for event in self.events() if event['type'] == 'score_recorded']
        again = self.gate('integrate', '--attempt', attempt['attempt_id'], '--score-file', self.score_file())
        status_again, interventions_again, inputs_again = self.intervention_view()
        after_log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        observed.update(integrate=reply, second_integrate=again, after=self.branch(),
                        task=status_again['task'], intervention_count=len(interventions_again),
                        interventions=interventions_again, user_inputs=inputs_again, scores=scores,
                        value=(self.repo / 'src/value.txt').read_text(encoding='utf-8'),
                        actual='integrated' if self.oid() == candidate else 'not integrated')
        # save() is exclusive-create. The pre-check snapshot is already there.
        (self.evidence / 'observation.json').write_text(
            json.dumps(observed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        self.check('BW-ABSENT-INTEGRATE',
                   reply.get('ok') is True and again.get('ok') is True and self.oid() == candidate
                   and before_ref != candidate and after_log == integrated_log
                   and len(interventions) == 1 and interventions_again == interventions
                   and inputs_again == inputs and len(scores) == 1
                   and scores[0]['facts']['human_interventions'] == 1
                   and len([event for event in self.events() if event['type'] == 'score_recorded']) == 1
                   and observed['value'] == 'worker\n' and status_again['task']['state'] == 'accepted',
                   '集成该提交，再次集成不新增人工介入、分数或工作分支记录', observed)
        self.cli('reclaim', '--attempt', attempt['attempt_id'])

    def positive_single(self):
        _, candidate = self.delivered({'src/value.txt': 'worker\n'})
        self.finish_positive(candidate)

    def positive_multi(self):
        a = self.start_worker()
        self.make_commit(a, {'src/value.txt': 'worker\n'})
        candidate = self.make_commit(a, {'src/second.txt': 'second independent commit\n'})
        if not self.worker_submit(candidate)['ok']:
            raise HarnessFailure('多提交正例 submit 失败。')
        self.finish_positive(candidate)

    def positive_red_card(self):
        self.card['red_commands'] = [{'argv': [sys.executable, '-I', '-B', 'tests/new_test.py'],
                                     'test_paths': ['tests/new_test.py']}]
        test = "from pathlib import Path\nassert Path('src/value.txt').read_text() == 'worker\\n', 'required worker value'\n"
        _, candidate = self.delivered({'src/value.txt': 'worker\n', 'tests/new_test.py': test})
        self.finish_positive(candidate)
        red = [e for e in self.events() if e['type'] == 'red_check']
        self.check('BW-RED-CARD', len(red) == 1 and red[0]['details']['passed'],
                   '新增测试在起点失败，在候选通过', red)

    def observe_trace_field(self, field):
        a = self.start_worker()
        records = [json.loads(row['data']) for row in self.rows('launch_records')]
        launch = next(record for record in records if record['id'] == self.launch)
        reference = {'Launch': launch['id'], 'Model': launch['model_requested'],
                     'Effort': launch['effort_requested'], 'Tool': launch['cli_version']}
        value = TRACE_VALUES[field]
        if reference[field] == value:
            raise HarnessFailure('追溯字段夹具必须确实与本 attempt 启动记录不一致。')
        candidate = self.make_commit(a, {'src/value.txt': 'worker\n'}, changes={field: value})
        fixture = json.loads((self.evidence / ('commit-' + candidate + '.json')).read_text(encoding='utf-8'))
        changed = [key for key, original in reference.items() if fixture['trailers'][key] != original]
        if changed != [field]:
            raise HarnessFailure('每个观察案例只改变一个追溯字段：' + repr(changed))
        save(self.evidence / 'trace-fixture.json', {
            'field': field, 'input_value': value, 'recorded_value': reference[field],
            'recorded_values': reference, 'record_source': 'launch_records id=' + self.launch,
            'launch_record': launch, 'candidate': candidate, 'changed_trace_fields': changed,
            'contract_verdict': '待裁定；仅观察，不断言门禁应拒收', 'real_codex_turns': 0,
        })
        submitted = self.worker_submit(candidate)
        if not submitted['ok']:
            raise HarnessFailure('追溯字段观察的合法身份 submit 失败：' + json.dumps(submitted))
        before = self.branch()
        reply = self.gate('verify', '--attempt', self.a['attempt_id'])
        task = self.cli('status')['task']
        observed = {'kind': 'trace_consistency_observation', 'counts_toward_acceptance': False,
                    'field': field, 'input_value': value, 'candidate': candidate,
                    'recorded_value': reference[field], 'recorded_values': reference,
                    'verify': reply, 'state_after_verify': task['state'],
                    'accepted_at_verify': reply.get('ok') is True and task['state'] == 'reviewing',
                    'before': before, 'integrated': False}
        save(self.evidence / 'probe-verify.json', observed)
        checks = [e for e in self.events() if e['type'] == 'trailer_check'
                  and e['details'].get('commit') == candidate]
        observed['trailer_checks'] = checks
        observed['target_check_reached'] = any(
            e['details']['trailers'].get(field.lower()) == [value] for e in checks)
        # Record admission before attempting any later phase, so a later fault
        # cannot erase proof that the target check let this delivery through.
        if observed['accepted_at_verify']:
            self.approve(candidate, automatic=True)
            integrated = self.gate('integrate', '--attempt', self.a['attempt_id'],
                                   '--score-file', self.score_file())
            observed.update(integrate=integrated,
                            integrated=integrated.get('ok') is True and self.oid() == candidate)
        observed.update(after=self.branch(), events=self.events(), task=self.cli('status')['task'])
        save(self.evidence / 'observation.json', observed)

    def probe_launch(self):
        self.observe_trace_field('Launch')

    def probe_model(self):
        self.observe_trace_field('Model')

    def probe_effort(self):
        self.observe_trace_field('Effort')

    def probe_tool(self):
        self.observe_trace_field('Tool')


def run_observation(source, output, name):
    # Use the existing lifecycle and gate client, with an observation report
    # instead of an acceptance PASS. No gate result is mocked or rewritten.
    chain.SOURCE, chain.OUT, chain.DIALECT = source.resolve(), output.resolve(), 'current'
    chain.OUT.mkdir(parents=True, exist_ok=False)
    chain.base.GATE = chain.SOURCE / 'workbench/src/gates/cli.ts'
    chain.base.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='q81obs-', dir='/tmp')).resolve()
    case = BadWorker(name)
    row = {'case': name, 'outcome': 'harness_error', 'assertions': case.assertions}
    try:
        case.setUp()
        getattr(case, name)()
        row['outcome'] = 'observed'
    except Exception as error:
        row.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            row['cleanup_failures'] = case.close_fixture()
        except Exception as error:
            row['cleanup_failures'] = [{'error': repr(error), 'traceback': traceback.format_exc()}]
        row.update(commands=case.commands, fixture=str(getattr(case, 'root', '')))
        save(chain.OUT / name / 'case.json', row)
    complete = row['outcome'] == 'observed' and not row['cleanup_failures']
    save(chain.OUT / 'run.json', {
        'status': 'INCOMPLETE', 'observation_complete': complete,
        'evidence_kind': 'trace_consistency_observation', 'counts_toward_acceptance': False,
        'contract_verdict': '待裁定', 'command': sys.argv, 'source': str(chain.SOURCE),
        'real_codex_turns': 0, 'cases': [row], 'planned_cases': [name],
        'artifact_root': str(chain.base.ARTIFACT_ROOT),
        'evidence_layer': 'real CLI/daemon/relay/gates/Git/SQLite; controlled PTY/process/native inputs',
    })
    print(json.dumps({'case': name, 'outcome': row['outcome'],
                      'observation_complete': complete, 'counts_toward_acceptance': False}), flush=True)
    return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=[*NEGATIVES, *POSITIVES, *PROBES, *ABSENT], action='append', required=True)
    args = parser.parse_args()
    if any(name in PROBES for name in args.case):
        if len(args.case) != 1:
            parser.error('追溯字段观察每次只选一案，不与验收案例混跑。')
        return run_observation(args.source, args.output, args.case[0])
    return run_cases(args.source, args.output, args.case, BadWorker, dialect='current', stop_on_failure=True)


if __name__ == '__main__':
    raise SystemExit(main())
