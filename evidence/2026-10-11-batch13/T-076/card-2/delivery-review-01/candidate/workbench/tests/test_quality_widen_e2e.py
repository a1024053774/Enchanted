"""Widened quality contracts and explicit reviewer fault probes.

Only the owned daemon is signalled. Git fault windows reuse the independent
recovery fixture's wrapper, read as source data without changing its assertions.
"""
import argparse
import ast
import copy
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import time

import test_quality_chain_e2e as q
from test_quality_chain_e2e import HarnessFailure, save, run_cases
from test_quality_tracer_e2e import Tracer


class Widen(Tracer):
    def configure_host(self, config):
        self.git_control = self.root / 'git-control'
        self.git_control.mkdir()
        (self.git_control / 'phase').write_text('record-only', encoding='utf-8')
        self.real_git = shutil.which('git', path=self.env['PATH'])
        tree = ast.parse((q.SOURCE / 'acceptance/test_recovery_e2e.py').read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'GIT_BARRIER' for t in n.targets))
        wrapper_source = ast.literal_eval(node.value)
        executable = self.git_control / 'git'
        executable.write_text('#!' + sys.executable + '\nCONTROL = ' + repr(str(self.git_control))
                              + '\nREAL_GIT = ' + repr(self.real_git) + '\n' + wrapper_source, encoding='utf-8')
        executable.chmod(0o755)
        self.env['PATH'] = str(self.git_control) + os.pathsep + self.env['PATH']
        self.fault_clients = []

    def set_fault(self, **changes):
        path = self.control / 'process-facts.json'
        values = json.loads(path.read_text(encoding='utf-8')); values.update(changes)
        with (self.evidence / 'fault-inputs.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'values': values}) + '\n')
        path.write_text(json.dumps(values) + '\n', encoding='utf-8')

    def verify_must_refuse(self, name):
        expected = {'RED-BASE-PASSES': 'red_state_failed', 'RED-CANDIDATE-FAILS': 'red_state_failed',
                    'RED-RULES': 'rule_check_failed', 'RED-RULES-FROZEN': 'rule_check_failed'}[name]
        before = self.oid()
        value = self.gate('verify')
        task = self.cli('status')['task']
        expected_check = 'rule_checks' if expected == 'rule_check_failed' else 'red_state'
        self.check(name, value.get('error') == expected and self.oid() == before and task['state'] == 'submitted'
                   and task.get('repair', {}).get('check') == expected_check,
                   {'error': expected, 'unchanged_ref': before}, value)
        self.check(name + '.event', any(e['type'] == 'rejected' and e['details'].get('error') == expected for e in self.events()),
                   'specific check rejection is durable', self.events())

    def widen_red_rules_success(self):
        self.write_rule_config('from pathlib import Path; assert Path("src/value.txt").read_text(encoding="utf-8") == "worker\\n"')
        self.red_command('from pathlib import Path\nassert Path("src/value.txt").read_text(encoding="utf-8") == "worker\\n", "required behavior absent"\n')
        a = self.start_worker()
        c = self.commit(a, {'src/value.txt': 'worker\n', 'tests/red.py': self.red_source})
        if not self.worker_submit(c)['ok']:
            raise HarnessFailure('Valid controlled candidate could not submit.')
        self.approve(c)
        v = self.cli('status')['task']['verification']
        red = v['quality']['red']
        self.check('WIDE-RED-PAIR', len(red) == 1 and red[0]['base_result']['returncode'] == 1
                   and red[0]['candidate_result']['returncode'] == 0 and red[0]['B'] == a['base_commit'] and red[0]['C'] == c,
                   'new tests fail on B and pass on C with explicit frozen bindings', red)
        self.check('WIDE-RED-ISOLATION', (Path(red[0]['base_workspace']) / 'src/value.txt').read_text(encoding="utf-8") == 'base\n'
                   and (Path(red[0]['candidate_workspace']) / 'src/value.txt').read_text(encoding="utf-8") == 'worker\n'
                   and self.oid(Path(red[0]['base_workspace'])) == a['base_commit']
                   and len({red[0]['base_workspace'], red[0]['candidate_workspace'], v['workspace']}) == 3,
                   'only declared test files reach the separate B checkout', red)
        types = [e['type'] for e in self.events()]
        order = ['path_check', 'completion_check', 'red_check', 'rule_check', 'trailer_check', 'review_requested']
        self.check('WIDE-CHECK-ORDER', [types.index(t) for t in order] == sorted(types.index(t) for t in order), order, types)
        self.integrate_scored(c, rounds=1)

    def widen_red_manifest_paths(self):
        for index, paths in enumerate([['../outside.py'], ['/tmp/outside.py'], ['.git/config'], ['tests/'], ['tests/a.py', 'tests/a.py']]):
            self.card['red_commands'] = [{'argv': [sys.executable, '-c', 'pass'], 'test_paths': paths}]
            self.card_file.write_text(json.dumps(self.card), encoding='utf-8')
            reply = self.gate('card_validate', '--card', self.card_file)
            self.check('WIDE-MANIFEST-PATH', reply.get('error') == 'invalid_task_card',
                       {'invalid_test_paths': paths}, {'index': index, 'reply': reply})

    def widen_red_symlink(self):
        self.red_command('unused')
        a = self.create()
        tests = Path(a['workspace']) / 'tests'; tests.mkdir()
        (tests / 'red.py').symlink_to('../src/value.txt')
        c = self.commit(a)
        self.submit(a, c)
        reply = self.gate('verify')
        self.check('WIDE-RED-SYMLINK', reply.get('error') == 'red_test_file_invalid' and self.oid() == self.base,
                   'a tracked symlink is not a test blob to transplant', reply)

    def widen_bad_project_config(self):
        folder = self.repo / '.a2a'; folder.mkdir()
        (folder / 'quality.json').write_text('{"schema":1,"rule_checks":', encoding='utf-8')
        self.git('add', '.a2a/quality.json'); self.git('commit', '-m', 'Deliberately malformed project configuration')
        self.base = self.oid()
        self.save_card()
        reply = self.gate('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')
        self.check('WIDE-CONFIG-INVALID', reply.get('error') == 'invalid_project_quality' and not self.rows('tasks'),
                   'malformed committed configuration refuses registration instead of disabling checks', reply)

    def finish_with_score(self, result):
        a = self.start_worker()
        self.stop_turn(); self.wait_pane(lambda p: p['state'] == 'idle')
        missing = self.gate('abandon', '--attempt', a['attempt_id'])
        self.check('WIDE-END-SCORE-REQUIRED', missing.get('error') == 'score_required'
                   and self.cli('status')['task']['state'] == 'claimed', 'missing score does not terminate', missing)
        if result == '放弃':
            data = {'result': result, 'reason': '独立夹具明确终止，不评价工程分'}
        else:
            data = {'result': result, 'boundary_discipline': 3, 'boundary_reason': '遵守边界',
                    'engineering_taste': 1, 'engineering_reason': '由更强执行器继续', 'notes': ''}
        path = self.root / 'ending-score.json'; save(path, data)
        reply = self.gate('abandon', '--attempt', a['attempt_id'], '--score-file', path)
        expected_state = 'abandoned' if result == '放弃' else 'upgraded'
        scores = [e['details'] for e in self.events() if e['type'] == 'score_recorded']
        self.check('WIDE-END-SCORE', reply['ok'] and reply['task']['state'] == expected_state
                   and len(scores) == 1 and scores[0]['data'] == data and scores[0]['launch_id'] == self.launch
                   and ('facts' not in scores[0] if result == '放弃' else scores[0]['facts']['delivery_rounds'] == 0)
                   and self.oid() == self.base, 'terminal result and one score, with no Git integration', {'reply': reply, 'scores': scores})
        save(self.evidence / 'score-payload.json', scores[0])
        replay = self.gate('abandon', '--attempt', a['attempt_id'], '--score-file', path)
        self.check('WIDE-END-REPLAY', replay['ok'] and len([e for e in self.events() if e['type'] == 'score_recorded']) == 1,
                   'identical termination has exactly one score', replay)
        self.cli('reclaim', '--attempt', a['attempt_id'])
        self.check('WIDE-END-PRESERVED', self.cli('status')['task']['state'] == expected_state,
                   'reclaim does not turn the terminal result into revoke', self.cli('status')['task'])

    def widen_abandon(self):
        self.finish_with_score('放弃')

    def widen_upgrade(self):
        self.finish_with_score('升级')

    def widen_ending_invalid_fields(self):
        a = self.start_worker(); self.stop_turn(); self.wait_pane(lambda p: p['state'] == 'idle')
        values = [{'result': '放弃', 'reason': ''}, {'result': '放弃', 'reason': 'stop', 'notes': ''},
                  {'result': '通过', 'boundary_discipline': 3, 'boundary_reason': 'x', 'engineering_taste': 2, 'engineering_reason': 'y', 'notes': ''},
                  {'result': '升级', 'boundary_discipline': True, 'boundary_reason': 'x', 'engineering_taste': 2, 'engineering_reason': 'y', 'notes': ''}]
        for index, data in enumerate(values):
            path = self.root / ('invalid-ending-%d.json' % index); save(path, data)
            reply = self.gate('abandon', '--attempt', a['attempt_id'], '--score-file', path)
            self.check('WIDE-END-FIELDS', reply.get('error') == 'invalid_score' and self.cli('status')['task']['state'] == 'claimed',
                       {'reject': data}, reply)

    def widen_scores_roundtrip(self):
        _, c = self.good_submission(); self.approve(c); self.integrate_scored(c, rounds=1)
        backend = json.loads((self.evidence / 'score-payload.json').read_text(encoding="utf-8"))
        legacy = self.root / 'legacy'; records = legacy / 'records'; records.mkdir(parents=True)
        context = dict(schema=1, launch_id='legacy-fixture', created_at='2026-10-11T00:00:00Z', project='fixture',
                       task='legacy-task', attempt='legacy-attempt', session='legacy-session', role='worker', cli='Codex',
                       cli_version='fixture-only', model='fixture-model', effort='medium', service_tier_requested='fast',
                       cwd=str(self.repo), project_commit=self.base, launcher_commit='fixture', role_card='fixture',
                       role_card_version='fixture', argv=['fixture-only'], native_session='unknown')
        (records / 'launches.jsonl').write_text(''.join(json.dumps({**context, 'phase': phase}) + '\n' for phase in ['prepared', 'started']), encoding='utf-8')
        facts = self.root / 'legacy-facts.json'
        save(facts, {'task_type': '后端逻辑', 'complexity': 'L', 'delivery_rounds': 2, 'elapsed_seconds': 4,
                     'human_interventions': 0, 'rejections': dict.fromkeys(['identity_version', 'path_boundary', 'completion', 'red_state', 'rule_checks', 'independent_review', 'commit_trailers'], 0)})
        score = q.SOURCE / 'scripts/score'
        flags = ['--boundary-discipline', '3', '--boundary-reason', 'fixture', '--engineering-taste', '2', '--engineering-reason', 'fixture', '--notes', '']
        generated = self.process([sys.executable, '-B', score, '--root', legacy, '--launch', 'legacy-fixture', '--facts', facts, '--result', '通过', *flags])
        if generated.returncode:
            raise HarnessFailure('Canonical score command did not generate its isolated fixture row.')
        original = json.loads(generated.stdout)
        user = self.process([sys.executable, '-B', score, '--root', legacy, '--source', 'user', '--score-of', original['score_id'], *flags])
        if user.returncode:
            raise HarnessFailure('Canonical user score command failed.')
        valid = self.root / 'all-scores.jsonl'
        rows = [backend, original, json.loads(user.stdout)]
        valid.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
        before = valid.read_bytes()
        result = self.gate('scores_validate', '--file', valid, task=False)
        self.check('WIDE-FORMAT-IMPORT', result['ok'] and result['records'] == 3 and result['imported'] is False and valid.read_bytes() == before,
                   'backend validates native and legacy/user records without rewriting/importing', result)
        validator = 'import json,runpy,sys; sys.path.insert(0,sys.argv[1]); m=runpy.run_path(sys.argv[1]+"/score",run_name="validator"); m["validate_scores"]([json.loads(l) for l in open(sys.argv[2],encoding="utf-8")])'
        reference = self.process([sys.executable, '-B', '-c', validator, q.SOURCE / 'scripts', valid])
        self.check('WIDE-FORMAT-EXPORT', reference.returncode == 0, 'canonical validator accepts backend payload', reference.stderr)
        bad_rows = []
        duplicate = copy.deepcopy(rows); duplicate.append({**original, 'score_id': 'duplicate-executor'})
        bad_rows.append(duplicate)
        incomplete = copy.deepcopy(rows); del incomplete[0]['facts']['rejections']['red_state']; bad_rows.append(incomplete)
        wrong_user = copy.deepcopy(rows); wrong_user[2]['model'] = 'wrong-origin'; bad_rows.append(wrong_user)
        abandoned = copy.deepcopy(rows); abandoned[0]['data'] = {'result': '放弃', 'reason': 'fixture'}; bad_rows.append(abandoned)
        for index, values in enumerate(bad_rows):
            path = self.root / ('bad-scores-%d.jsonl' % index)
            path.write_text(''.join(json.dumps(row) + '\n' for row in values), encoding='utf-8')
            ours = self.gate('scores_validate', '--file', path, task=False)
            theirs = self.process([sys.executable, '-B', '-c', validator, q.SOURCE / 'scripts', path])
            self.check('WIDE-FORMAT-REJECT-%d' % index, ours.get('error') == 'invalid_scores' and theirs.returncode != 0,
                       'both validators reject this independently invalid stream', {'case': index, 'ours': ours, 'canonical_exit': theirs.returncode})
        tail = self.root / 'missing-final-newline.jsonl'; tail.write_bytes(before[:-1])
        ours = self.gate('scores_validate', '--file', tail, task=False)
        theirs = self.process([sys.executable, '-B', '-c',
                               'import sys; sys.path.insert(0,sys.argv[1]); from record_io import read_records; read_records(__import__("pathlib").Path(sys.argv[2]))',
                               q.SOURCE / 'scripts', tail])
        self.check('WIDE-FORMAT-TAIL', ours.get('error') == 'invalid_scores' and theirs.returncode != 0 and tail.read_bytes() == before[:-1],
                   'an unterminated final record is refused and preserved', {'ours': ours, 'canonical_exit': theirs.returncode})

    def score_cas_recovery(self, phase):
        a, c = self.good_submission(); self.approve(c)
        (self.git_control / 'phase').write_text(phase, encoding='utf-8')
        stdout = (self.evidence / 'interrupted-integrate.stdout').open('xb')
        stderr = (self.evidence / 'interrupted-integrate.stderr').open('xb'); self.streams.extend([stdout, stderr])
        argv = ['node', q.base.GATE, '--state', self.state, 'integrate', '--task', self.task,
                '--attempt', a['attempt_id'], '--score-file', self.score_file()]
        client = subprocess.Popen(list(map(str, argv)), cwd=self.root, env=self.env, stdout=stdout, stderr=stderr, start_new_session=True)
        self.fault_clients.append(client)
        save(self.evidence / 'interrupted-integrate.argv.json', {'argv': list(map(str, argv)), 'pid': client.pid})
        def entries():
            return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in self.git_control.glob('*.entry.json')]
        values = self.wait_for(entries, lambda rows: any(row['phase'] == phase and row['ppid'] == self.host.pid for _, row in rows))
        path, barrier = next((p, row) for p, row in values if row['phase'] == phase and row['ppid'] == self.host.pid)
        before = self.cli('status')['task']; intent = before['integration_intent']
        expected_ref = self.base if phase == 'before' else c
        if self.oid() != expected_ref or phase == 'after' and not (barrier.get('executed_real_git') and barrier.get('exit_code') == 0):
            raise HarnessFailure('Real Git did not reach the declared CAS window.')
        save(self.evidence / 'cas-before-kill.json', {'task': before, 'barrier': barrier, 'ref': self.oid(), 'events': self.events()})
        self.check('WIDE-SCORE-PENDING', not any(e['type'] == 'score_recorded' for e in self.events()),
                   'intent is not a final score before gate bookkeeping', self.events())
        status = self.gate('daemon_status', task=False)
        observation = self.process(['/bin/ps', '-p', str(self.host.pid), '-o', 'pid=,ppid=,command='])
        endpoint = self.state / 'control.sock'; endpoint_stat = endpoint.lstat()
        if status['pid'] != self.host.pid or self.host.poll() is not None or observation.returncode or str(self.state) not in observation.stdout or not stat.S_ISSOCK(endpoint_stat.st_mode):
            raise HarnessFailure('Owned daemon signal target cannot be confirmed.')
        save(self.evidence / 'signal.json', {'target': 'owned-daemon', 'pid': self.host.pid, 'signal': 'SIGKILL',
                                           'status': status, 'ps': observation.stdout, 'barrier': barrier})
        self.host.send_signal(signal.SIGKILL); self.host.wait(timeout=10); client.wait(timeout=10)
        if self.host.returncode != -signal.SIGKILL or client.returncode == 0:
            raise HarnessFailure('Owned daemon interruption did not occur.')
        disconnected = json.loads((self.evidence / 'interrupted-integrate.stdout').read_text(encoding='utf-8'))
        if disconnected.get('error') != 'daemon_call_failed':
            raise HarnessFailure('The interrupted client did not report an unknown daemon call outcome.')
        if int((self.state / 'daemon.pid').read_text(encoding="utf-8")) != self.host.pid or endpoint.lstat().st_ino != endpoint_stat.st_ino:
            raise HarnessFailure('Do not remove a changed daemon endpoint.')
        endpoint.unlink(); (self.state / 'daemon.pid').unlink()
        (self.git_control / 'phase').write_text('record-only', encoding='utf-8')
        Path(barrier['release']).write_text('abort', encoding='utf-8')
        done = path.with_name(path.name.removesuffix('.entry.json') + '.done.json')
        self.wait_for(lambda: done.exists(), bool)
        self.start_host()
        wrong = self.root / 'changed-recovery-score.json'
        data = json.loads(self.score_file().read_text(encoding="utf-8")); data['notes'] = 'must not replace original score'; save(wrong, data)
        refused = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', wrong)
        self.check('WIDE-SCORE-RECOVERY-BINDING', refused.get('error') == 'score_replay_mismatch' and self.oid() == expected_ref,
                   'recovery cannot change the pending score or Git reference', refused)
        log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        recovered = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', self.score_file())
        scores = [e['details'] for e in self.events() if e['type'] == 'score_recorded']
        after_log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        self.check('WIDE-SCORE-RECOVERY-ONCE', recovered['ok'] and self.oid() == c and len(scores) == 1
                   and scores[0]['score_id'] == intent['score']['score_id'] and scores[0]['data'] == intent['score']['data']
                   and len(after_log.splitlines()) - len(log.splitlines()) == (1 if phase == 'before' else 0),
                   'recover original intent; exactly one final score and only the missing Git effect', {'reply': recovered, 'scores': scores})
        again = self.gate('integrate', '--attempt', a['attempt_id'], '--score-file', self.score_file())
        self.check('WIDE-SCORE-RECOVERY-REPLAY', again['ok'] and len([e for e in self.events() if e['type'] == 'score_recorded']) == 1
                   and self.git('reflog', 'show', '--format=%H', 'refs/heads/main') == after_log,
                   'post-recovery replay has no extra score or Git write', again)

    def widen_score_before_cas(self):
        self.score_cas_recovery('before')

    def widen_score_after_cas(self):
        self.score_cas_recovery('after')

    def reviewer_create_red(self):
        _, c = self.good_submission(); self.set_fault(fail_review_spawn=True)
        p = self.process(['node', q.base.GATE, '--state', self.state, 'verify', '--task', self.task, '--attempt', self.a['attempt_id']])
        # This error is deliberately injected at the external spawn boundary,
        # not an unexpected harness exception to relabel as business red.
        result = json.loads(p.stdout)
        current = self.cli('status')['task']; events = self.events()
        self.check('REVIEW-CREATE-PAUSE', not result['ok'] and current['state'] == 'paused'
                   and current['review']['state'] == 'unknown' and any(e['type'] == 'issue_issue' for e in events),
                   'failed reviewer creation persists unknown/pause plus an executor issue', {'reply': result, 'current': current, 'events': events})

    def reviewer_restart_red(self):
        _, c = self.good_submission(); review, _ = self.start_review(c)
        self.gate('daemon_stop', task=False); self.host.wait(timeout=12)
        if self.host.returncode:
            raise HarnessFailure('Controlled graceful stop failed.')
        self.start_host()
        current = self.cli('status')['task']; events = self.events()
        self.check('REVIEW-RESTART-PAUSE', current['state'] == 'paused' and current['review']['state'] == 'unknown'
                   and current['review']['review_id'] == review['review_id'] and any(e['type'] == 'issue_issue' for e in events),
                   'restart never adopts/recreates the old reviewer or leaves it apparently reviewing', {'current': current, 'events': events})

    def reviewer_reclaim_red(self):
        _, c = self.good_submission(); review, record = self.start_review(c)
        self.set_fault(drop_reviewer_exit=True)
        self.send_review(review, record, self.review_packet(review, c))
        deadline = time.monotonic() + 10
        while True:
            observed = self.orchestration()
            if any(e['type'] == 'queue_stopped' for e in observed): break
            if time.monotonic() >= deadline:
                raise HarnessFailure('The controlled exit-not-confirmed fault was not observed.')
            time.sleep(0.05)
        current = self.cli('status')['task']; events = self.events()
        self.check('REVIEW-RECLAIM-PAUSE', current['state'] == 'paused' and any(e['type'] == 'issue_issue' for e in events)
                   and not any(e['type'] == 'review_reclaimed' for e in events),
                   'unknown reviewer exit pauses and reports; it is not a successful reclaim', {'current': current, 'events': events})

    def close_fixture(self):
        if hasattr(self, 'control') and (self.control / 'process-facts.json').exists():
            self.set_fault(fail_review_spawn=False, drop_reviewer_exit=False)
        if hasattr(self, 'git_control'):
            (self.git_control / 'release-all').write_text('abort', encoding='utf-8')
        failures = super().close_fixture()
        clients = []
        for client in getattr(self, 'fault_clients', []):
            try: client.wait(timeout=5)
            except subprocess.TimeoutExpired as error:
                failures.append({'phase': 'fault-client-exit', 'pid': client.pid, 'error': repr(error)})
            clients.append({'pid': client.pid, 'exit': client.poll()})
        save(self.evidence / 'fault-client-cleanup.json', {'clients': clients, 'failures': failures})
        return failures


WIDE_CASES = ['widen_red_rules_success', 'red_manifest_missing', 'red_base_not_failing', 'red_candidate_fails',
              'red_rules_failing', 'red_rules_frozen', 'widen_red_manifest_paths', 'widen_red_symlink',
              'widen_bad_project_config', 'widen_abandon', 'widen_upgrade', 'widen_ending_invalid_fields',
              'widen_scores_roundtrip', 'widen_score_before_cas', 'widen_score_after_cas']
REVIEW_RED = {'reviewer_create_red': 'REVIEW-CREATE-PAUSE', 'reviewer_restart_red': 'REVIEW-RESTART-PAUSE',
              'reviewer_reclaim_red': 'REVIEW-RECLAIM-PAUSE'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group', choices=['wide', 'review-red'], required=True)
    parser.add_argument('--case', choices=[*WIDE_CASES, *REVIEW_RED], action='append')
    args = parser.parse_args()
    return run_cases(args.source, args.output, args.case or (WIDE_CASES if args.group == 'wide' else list(REVIEW_RED)),
                     Widen, dialect='current', stop_on_failure=args.group == 'wide')


if __name__ == '__main__':
    raise SystemExit(main())
