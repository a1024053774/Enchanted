#!/usr/bin/env python3
"""T-077 S3 contracts through the daemon CLI and independent Git/SQLite reads.

The initial batch uses manual claims and the existing controlled thread boundary.
It does not launch Codex. A business-red receipt never means product acceptance.
"""
import argparse
from contextlib import closing
import gzip
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest

import test_task_cards_e2e as cards
from test_daemon_gates_e2e import DaemonCards
import daemon_acceptance_adapter as old


ROOT = Path(__file__).resolve().parents[2]
BASE = '14b57d22a84bcaebfa91c5051b9909b53a570fac'
CONTRACTS = []
CONFLICT_TARGET_IDS = {
    'test_conflict_active_worker_reworks_and_integrates': 'CONFLICT-ACTIVE-WRITEBACK',
    'test_conflict_ended_session_gets_new_attempt': 'CONFLICT-ENDED-NEW-ATTEMPT',
    'test_conflict_unknown_session_preserves_scene_and_reports': 'CONFLICT-UNKNOWN-SESSION-REPORT',
    'test_conflict_unknown_delivery_does_not_resend': 'CONFLICT-UNKNOWN-DELIVERY-ONCE',
    'test_merge_command_error_is_not_text_conflict': 'CONFLICT-GIT-ERROR-CLASSIFICATION',
    'test_conflict_rework_still_rejects_forbidden_path': 'CONFLICT-REWORK-FORBIDDEN-PATH',
    'test_conflict_rework_still_rejects_foreign_trailer': 'CONFLICT-REWORK-FOREIGN-TRAILER',
}
# Controller #123: each target requires its own earlier scenario facts.
# Delivery/resubmission/target verify are prerequisites of the rework guards.
CONFLICT_REQUIRED_FACTS = {
    'test_conflict_active_worker_reworks_and_integrates': (
        'scenario_prepared', 'worker_session_input_available', 'text_conflict_observed', 'conflict_handling_entered'),
    'test_conflict_ended_session_gets_new_attempt': (
        'scenario_prepared', 'ended_session_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    'test_conflict_unknown_session_preserves_scene_and_reports': (
        'scenario_prepared', 'unknown_session_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    'test_conflict_unknown_delivery_does_not_resend': (
        'scenario_prepared', 'delivery_unknown_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    'test_merge_command_error_is_not_text_conflict': (
        'scenario_prepared', 'git_io_failure_observed', 'target_verify_executed'),
    'test_conflict_rework_still_rejects_forbidden_path': (
        'scenario_prepared', 'text_conflict_observed', 'conflict_handling_entered',
        'conflict_delivered', 'explicit_resubmitted', 'target_verify_executed'),
    'test_conflict_rework_still_rejects_foreign_trailer': (
        'scenario_prepared', 'text_conflict_observed', 'conflict_handling_entered',
        'conflict_delivered', 'explicit_resubmitted', 'target_verify_executed'),
}


def classify_conflict_red(case, contracts, evidence, *, tests_run, failures, errors, skipped):
    target = CONFLICT_TARGET_IDS[case]
    required = CONFLICT_REQUIRED_FACTS[case]
    steps = evidence['steps']
    targets = [(index, step) for index, step in enumerate(steps)
               if step['kind'] == 'target' and step['id'] == target]
    checks = [row for row in contracts if row['assertion_id'] == target]
    target_unique = len(targets) == len(checks) == 1
    target_failed = target_unique and targets[0][1]['passed'] is False and checks[0]['pass'] is False
    target_passed = target_unique and targets[0][1]['passed'] is True and checks[0]['pass'] is True
    missing = []
    for name in required:
        facts = [(index, step) for index, step in enumerate(steps)
                 if step['kind'] == 'precondition' and step['id'] == name]
        if (not target_unique or len(facts) != 1 or facts[0][0] >= targets[0][0]
                or facts[0][1]['passed'] is not True or not facts[0][1]['details']):
            missing.append(name)
    issues = []
    if not target_unique: issues.append('target_not_reached_exactly_once')
    if tests_run != 1: issues.append('wrong_test_count')
    if errors: issues.append('errors')
    if skipped: issues.append('skipped')
    if evidence['cleanup_failures']: issues.append('cleanup_failures')
    if target_failed and not failures: issues.append('target_failure_not_reported')
    if failures and not target_failed: issues.append('non_target_assertion_failure')
    coverage = ('NOT_COVERED' if missing or issues else
                'TARGET_FAILED' if target_failed else 'TARGET_PASSED' if target_passed else 'NOT_COVERED')
    return {'target_assertion_id': target, 'target_failed': bool(target_failed), 'target_passed': bool(target_passed),
            'required_preconditions': list(required), 'missing_preconditions': missing,
            'classification_issues': issues, 'target_coverage': coverage,
            'business_red': coverage == 'TARGET_FAILED', 'conflict_evidence': evidence,
            'cleanup_failures': evidence['cleanup_failures']}


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def write_gzip(path, value):
    with gzip.open(path, 'xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


class ContractChecks:
    def contract(self, name, condition, expected, actual, *, assertion_id=None):
        CONTRACTS.append({'test': self.id(), 'claim': name, 'pass': bool(condition),
                          'expected': expected, 'actual': actual, 'assertion_id': assertion_id})
        self.assertTrue(condition, 'S3 contract: ' + name + '\n' + repr(CONTRACTS[-1]))


class WorktreeContracts(ContractChecks, DaemonCards):
    def create(self):
        # Integration requires actual managed delivery provenance in T-076-2.
        if self._testMethodName in {'test_dirty_integration_reports_without_mutation',
                'test_r8_revalidates_on_new_head', 'test_r8_stops_at_fourth_cas_miss',
                'test_r8_missing_trailer_is_not_recorded_twice'}:
            return self.create_managed()
        return super().create()

    def setUp(self):
        super().setUp()
        # Registered last, so SQLite is read while the owning daemon is alive.
        self.addCleanup(self.capture_readback)

    def capture_readback(self):
        with closing(sqlite3.connect(self.state.resolve().joinpath('state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            tables = {}
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                name = row[0]
                quoted = '"' + name.replace('"', '""') + '"'
                tables[name] = [dict(item) for item in db.execute('SELECT * FROM ' + quoted)]
        write_gzip(self.root / 's3-state-readback.json.gz', {'task': self.task, 'tables': tables})

    def ref_or_none(self, ref):
        p = self.process(['git', '-C', self.repo, 'rev-parse', '--verify', '--quiet', ref])
        self.assertIn(p.returncode, (0, 1), p.stderr)
        return p.stdout.strip() if p.returncode == 0 else None

    def request(self, command, *args):
        if command == 'integrate' and self.integration_score and '--score-file' not in args:
            args = (*args, '--score-file', self.integration_score)
        p = self.process(['node', cards.GATE, '--state', self.state, command, '--task', self.task, *args])
        self.assertIn(p.returncode, (0, 1), 'Entry/setup failure: ' + p.stderr)
        reply = json.loads(p.stdout)
        self.assertIs(type(reply.get('ok')), bool)
        self.assertEqual(reply['ok'], p.returncode == 0)
        return reply

    def system_issues(self, attempt):
        result = self.cli('issues')
        return [view['issue'] for view in result['issues']
                if view['issue']['from'] == 'system' and
                view['issue']['attempt_id'] == attempt['attempt_id']]

    def test_worker_name(self):
        a = self.create()
        expected = str((self.state / 'worktrees' / 'fixture' / (self.task + '-a1')).resolve())
        branch = self.process(['git', '-C', a['workspace'], 'symbolic-ref', '--quiet', 'HEAD'])
        with self.subTest(field='workspace'):
            self.contract('W16 worker project/task/ordinal path', a['workspace'] == expected, expected, a['workspace'])
        with self.subTest(field='branch'):
            expected_ref = 'refs/heads/a2a/' + self.task + '-a1'
            self.contract('W16 named worker branch', branch.returncode == 0 and branch.stdout.strip() == expected_ref,
                          expected_ref, {'exit': branch.returncode, 'stdout': branch.stdout})

    def test_clean_revoke(self):
        a = self.create()
        # Claim has no launch record. Trailers would be rejected before this cleanup can run.
        c = self.commit(a, trailers=False)
        self.submit(a, c)
        self.cli('verify')
        self.cli('revoke', '--reason', 'S3 independent clean revoke')
        self.assertEqual(self.oid(), self.base)
        with self.subTest(field='directory'):
            self.contract('W02 clean revoked directory removed', not Path(a['workspace']).exists(), False,
                          Path(a['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W02 revoked candidate hidden reference', actual == c, c, actual)

    def test_clean_revise(self):
        a = self.create()
        c = self.commit(a)
        self.submit(a, c)
        self.cli('revise', '--spec-rev', '2')
        self.submit(a, c, ok=False, error='stale_attempt')
        with self.subTest(field='directory'):
            self.contract('W10 revised clean directory removed', not Path(a['workspace']).exists(), False,
                          Path(a['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W10 revised candidate remains readable', actual == c, c, actual)

    def test_verification_name(self):
        marker = self.root / 'verification-observation.json'
        source = ('import json,os,subprocess\n'
                  'p=subprocess.run(["git","symbolic-ref","--quiet","HEAD"],capture_output=True,text=True)\n'
                  'with open(' + repr(str(marker)) + ',"x",encoding="utf-8") as f:\n'
                  ' json.dump({"cwd":os.getcwd(),"ref_exit":p.returncode,"ref":p.stdout},f)\n')
        self.card['completion_conditions'].append({'argv': [sys.executable, '-I', '-B', '-c', source]})
        a = self.create()
        # Claim has no launch record. Trailers would be rejected before the oracle observation is kept.
        self.submit(a, self.commit(a, trailers=False))
        self.cli('verify')
        observed = json.loads(marker.read_text(encoding='utf-8'))
        self.assertEqual(observed['ref_exit'], 1, 'Verification must be detached while the oracle runs')
        expected = str((self.state / 'worktrees' / 'fixture' / (self.task + '-a1-verify-1')).resolve())
        self.contract('W14 verification project/task/purpose/ordinal path', observed['cwd'] == expected, expected, observed)

    def test_completed_verification_cleanup(self):
        a = self.create()
        # Claim has no launch record. Trailers would be rejected before a passed verification exists.
        c = self.commit(a, trailers=False)
        self.submit(a, c)
        v = self.cli('verify')['verification']
        self.assertEqual(v['state'], 'passed')
        self.assertEqual(self.oid(), self.base, 'verify does not integrate')
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            stored = json.loads(db.execute('SELECT data FROM verifications WHERE id=?', (v['verification_id'],)).fetchone()[0])
        self.assertEqual(stored, v)
        with self.subTest(field='directory'):
            self.contract('W08 completed verification directory removed', not Path(v['workspace']).exists(), False,
                          Path(v['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/verifications/' + self.task + '/a1/v1')
            self.contract('W08 verified M retained independently of worktree', actual == c, c, actual)

    def test_overlap_without_reason(self):
        first = self.create()
        other = self.task + '-other'
        self.task = other
        self.card = {**self.card, 'id': other}
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')
        reply = self.request('claim', '--owner', 'second-writer')
        self.contract('W12/W13 overlapping active attempts require explicit reason', reply['ok'] is False,
                      {'ok': False, 'first_attempt': first['attempt_id']}, reply)
        status = self.cli('status')['task']
        self.assertIsNone(status['current_attempt'], 'Rejected overlap cannot reserve a second writer')

    def test_dirty_revoke_keeps_scene_and_reports(self):
        a = self.create()
        c = self.commit(a)
        path = Path(a['workspace']) / 'src/value.txt'
        path.write_bytes(b'Uncommitted work must remain exactly as written.\n')
        before = path.read_bytes()
        self.cli('revoke', '--reason', 'Independent dirty cleanup probe')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.oid(Path(a['workspace'])), c)
        issues = self.system_issues(a)
        self.contract('dirty cleanup appends system issue for original attempt', bool(issues), 'at least one bound system issue', issues)

    def test_unknown_cleanup_keeps_scene_and_reports(self):
        a = self.create()
        c = self.commit(a)
        # This router is owned by the pre-existing fixture, not a product branch.
        fault = self.root / 'wrapped-git'
        fault.mkdir()
        git = shutil.which('git', path=self.env['PATH'])
        wrapper = fault / 'git'
        wrapper.write_text('#!' + sys.executable + '\nimport os,sys\n'
                           'if "status" in sys.argv[1:]:\n'
                           ' sys.stderr.write("fixture: worktree status unavailable\\n"); sys.exit(73)\n'
                           'os.execv(' + repr(git) + ',[' + repr(git) + ']+sys.argv[1:])\n', encoding='utf-8')
        wrapper.chmod(0o755)
        reply = self.request('revoke', '--reason', 'Independent unknown cleanup probe')
        self.assertTrue(Path(a['workspace']).is_dir(), reply)
        self.assertEqual(self.oid(Path(a['workspace'])), c)
        issues = self.system_issues(a)
        self.contract('unknown cleanup appends system issue without deleting scene', bool(issues), 'bound system issue', issues)

    def test_dirty_integration_reports_without_mutation(self):
        a = self.create()
        self.submit(a, self.commit(a))
        self.cli('verify')
        path = self.repo / 'src/value.txt'
        path.write_bytes(b'User staged value\n')
        self.git('add', 'src/value.txt')
        path.write_bytes(b'User unstaged value\n')
        before = path.read_bytes()
        index = Path(self.git('rev-parse', '--git-path', 'index'))
        if not index.is_absolute():
            index = self.repo / index
        index_before = index.read_bytes()
        self.cli('integrate', ok=False, error='dirty_integration_worktree')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(index.read_bytes(), index_before)
        self.assertEqual(self.oid(), self.base)
        issues = self.system_issues(a)
        self.contract('dirty integration appends system issue', bool(issues), 'bound system issue', issues)

    def test_r8_revalidates_on_new_head(self):
        marker = self.root / 'oracle-runs.jsonl'
        source = ('from pathlib import Path\nimport json,os\n'
                  'assert Path("src/value.txt").read_text()=="worker\\n"\n'
                  'with open(' + repr(str(marker)) + ',"a",encoding="utf-8") as f:\n'
                  ' f.write(json.dumps({"cwd":os.getcwd(),"host":Path("host.txt").read_text()})+"\\n")\n')
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', '-c', source]}]
        a = self.create()
        c = self.commit(a)
        self.submit(a, c)
        original = self.cli('verify')['verification']
        (self.repo / 'host.txt').write_text('External G1 must survive.\n', encoding='utf-8')
        self.git('add', 'host.txt')
        self.git('commit', '-m', 'Independent external G1')
        g1 = self.oid()
        reply = self.request('integrate')
        self.contract('W01 R8 retries verification after one known head change', reply['ok'] is True, True, reply)
        v = self.cli('status')['task']['verification']
        self.assertNotEqual(v['verification_id'], original['verification_id'])
        self.assertEqual(v['G'], g1)
        self.assertEqual(v['C'], c)
        self.assertEqual(self.oid(), v['M'])
        for ancestor in (g1, c):
            self.git('merge-base', '--is-ancestor', ancestor, self.oid())
        rows = [json.loads(line) for line in marker.read_text(encoding='utf-8').splitlines()]
        self.assertEqual([row['host'] for row in rows], ['base host\n', 'External G1 must survive.\n'])
        self.assertEqual((self.repo / 'host.txt').read_text(encoding='utf-8'), 'External G1 must survive.\n')

    def test_r8_stops_at_fourth_cas_miss(self):
        counter = self.root / 'independent-writes.txt'
        source = ('from pathlib import Path\nimport os,subprocess\n'
                  'assert Path("src/value.txt").read_text()=="worker\\n"\n'
                  'counter=Path(' + repr(str(counter)) + ')\n'
                  'n=int(counter.read_text())+1 if counter.exists() else 1\n'
                  # A faulty unbounded retry cannot keep this fixture alive forever.
                  'assert n<=5,"independent writer budget exceeded"\n'
                  'counter.write_text(str(n),encoding="utf-8")\n'
                  'repo=Path(' + repr(str(self.repo)) + ')\n'
                  '(repo/"host.txt").write_text("External revision "+str(n)+"\\n",encoding="utf-8")\n'
                  'for args in (["add","host.txt"],["commit","-m","Independent concurrent revision "+str(n)]):\n'
                  ' subprocess.run(["git","-C",str(repo),*args],check=True,capture_output=True,text=True)\n')
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', '-c', source]}]
        a = self.create()
        self.submit(a, self.commit(a))
        self.cli('verify')
        self.assertEqual(counter.read_text(encoding='utf-8'), '1')
        reply = self.request('integrate')
        self.assertFalse(reply['ok'], 'Fourth lost CAS cannot be accepted')
        self.assertNotEqual(self.cli('status')['task']['state'], 'accepted')
        self.assertEqual((self.repo / 'src/value.txt').read_text(encoding='utf-8'), 'base\n')
        with self.subTest(field='budget'):
            actual = int(counter.read_text(encoding='utf-8'))
            self.contract('R8 runs exactly three automatic reverifications before fourth miss', actual == 4, 4, actual)
        with self.subTest(field='issue'):
            issues = self.system_issues(a)
            self.contract('R8 fourth miss escalates with a bound system issue', bool(issues), 'bound system issue', issues)
        status = self.cli('status')['task']
        with self.subTest(field='persisted-count'):
            misses = status['current_attempt'].get('revalidation', {}).get('misses')
            self.contract('R8 persists the four misses on the original attempt', misses == 4, 4, misses)
        issues_before = self.system_issues(a)
        writes_before = counter.read_bytes()
        replay = self.request('integrate')
        self.assertFalse(replay['ok'])
        self.assertEqual(counter.read_bytes(), writes_before, 'A repeated request cannot reset the automatic retry budget')
        self.assertEqual(self.system_issues(a), issues_before, 'A rejected replay cannot manufacture another escalation')

    def test_r8_missing_trailer_is_not_recorded_twice(self):
        a = self.create()
        c = self.commit(a, trailers=False)
        self.submit(a, c)
        self.cli('verify')
        before = self.cli('status')['user_inputs']
        self.assertEqual(len(before), 1)
        (self.repo / 'host.txt').write_text('External head for missing-trailer revalidation\n', encoding='utf-8')
        self.git('add', 'host.txt')
        self.git('commit', '-m', 'Independent missing-trailer case writer')
        reply = self.request('integrate')
        self.contract('W09 automatic revalidation succeeds for unchanged missing-trailer C', reply['ok'] is True, True, reply)
        self.assertEqual(self.cli('status')['user_inputs'], before)
        self.assertEqual(len([event for event in self.events() if event['type'] == 'human_intervention']), 1)
        self.assertEqual((self.repo / 'host.txt').read_text(encoding='utf-8'),
                         'External head for missing-trailer revalidation\n')


class RunCleanupContracts(ContractChecks, old.DaemonRun):
    def ref_or_none(self, ref):
        result = self.process(['git', '-C', self.repo, 'rev-parse', '--verify', '--quiet', ref])
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.stdout.strip() if result.returncode == 0 else None

    def test_integrated_run_cleanup(self):
        self.create()
        handle = self.start_run(seconds=20)
        thread = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=True)
        expected = Path(attempt['workspace'], 'pager.py').read_bytes()
        self.submit(attempt, candidate)
        self.drive_executor_finalize(handle, attempt, candidate)
        self.new_result(self.complete(handle), 'run')
        self.assertEqual(self.ref(), candidate)
        self.assertEqual((self.repo / 'pager.py').read_bytes(), expected)
        self.only_own_close(thread)
        self.finish_checks()
        with self.subTest(field='directory'):
            self.contract('W03 integrated run removes clean worker worktree', not Path(attempt['workspace']).exists(), False,
                          Path(attempt['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W03 integrated run retains candidate hidden reference', actual == candidate, candidate, actual)

    def test_timeout_cleanup_retains_unsubmitted_commit(self):
        self.create()
        handle = self.start_run(seconds=5)
        thread = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=True)
        self.failed_run(self.complete(handle), error='run_deadline')
        self.assertIsNone(self.status()['candidate_commit'])
        self.assertEqual(self.ref(), self.base)
        self.only_own_close(thread)
        self.finish_checks()
        with self.subTest(field='directory'):
            self.contract('W04 timeout removes ended clean worker directory', not Path(attempt['workspace']).exists(), False,
                          Path(attempt['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W04 unsubmitted commit survives under hidden reference', actual == candidate, candidate, actual)

    def test_rejected_run_cleanup(self):
        self.create()
        handle = self.start_run(seconds=8)
        thread = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=False)
        self.submit(attempt, candidate)
        self.failed_run(self.complete(handle))
        # First quality rejection retains the worker for repair. Explicitly end
        # that owned attempt before exercising S3's rejected/ended cleanup row.
        self.only_own_close()
        self.assertTrue(Path(attempt['workspace']).is_dir())
        self.cli('reclaim', '--task', self.task, '--attempt', attempt['attempt_id'])
        self.only_own_close(thread)
        self.finish_checks()
        with self.subTest(field='directory'):
            self.contract('W06 rejected and ended clean attempt directory removed', not Path(attempt['workspace']).exists(), False,
                          Path(attempt['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W06 rejected candidate retained under hidden reference', actual == candidate, candidate, actual)

    def test_superseded_run_retains_only_new_workspace(self):
        # The existing scenario proves original-attempt ownership and preserves
        # its own assertions. This adds the S3 terminal cleanup requirement.
        old.orchestration.RunCLI.test_replacement_attempt_is_not_verified_integrated_or_closed_by_old_run(self)
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            attempts = [json.loads(row[0]) for row in db.execute('SELECT data FROM attempts')]
        original = next(a for a in attempts if a['task_id'] == self.task and a['fence'] == 1)
        current = next(a for a in attempts if a['task_id'] == self.task and a['fence'] == 2)
        self.assertTrue(Path(current['workspace']).is_dir())
        with self.subTest(field='directory'):
            self.contract('W05 original reclaimed workspace is removed', not Path(original['workspace']).exists(), False,
                          Path(original['workspace']).exists())
        with self.subTest(field='reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W05 original attempt base survives under hidden reference', actual == self.base, self.base, actual)

    def test_historical_cleanup_leaves_current_and_foreign_untouched(self):
        self.create()
        card = json.loads(self.card_source.read_text(encoding='utf-8'))
        card['paths'] = {'allow': ['pager.py'], 'deny': []}
        self.card_source.write_text(json.dumps(card), encoding='utf-8')
        self.cli('card_save', '--task', self.task, '--card', self.card_source, '--expected-version', '1')
        self.cli('revise', '--task', self.task, '--spec-rev', '2', '--card-version', '2')
        previous = self.cli('dispatch', '--task', self.task, '--runtime-mode', 'approval-required')['attempt']
        old_thread = previous['thread_id']
        # Disjoint declared paths allow this lifecycle probe on both versions
        # without giving the old CLI an unsupported overlap flag.
        card['paths'] = {'allow': ['CONTRACT.md'], 'deny': []}
        self.card_source.write_text(json.dumps(card), encoding='utf-8')
        self.cli('card_save', '--task', self.task, '--card', self.card_source, '--expected-version', '2')
        self.cli('revise', '--task', self.task, '--spec-rev', '3', '--card-version', '3')
        current = self.cli('claim', '--task', self.task, '--owner', 'current-writer')['attempt']
        document = Path(current['workspace']) / 'CONTRACT.md'
        document.write_bytes(document.read_bytes() + b'\nIndependent current attempt artifact.\n')
        self.git('add', 'CONTRACT.md', cwd=current['workspace'])
        self.git('commit', '-m', 'Independent current attempt', cwd=current['workspace'])
        candidate = self.git('rev-parse', 'HEAD', cwd=current['workspace']).stdout.strip()
        self.submit(current, candidate)
        foreign_task = self.task + '-foreign'
        self.create(task=foreign_task)
        foreign_card = json.loads(self.card_source.read_text(encoding='utf-8'))
        foreign_card['paths'] = {'allow': ['foreign.txt'], 'deny': []}
        self.card_source.write_text(json.dumps(foreign_card), encoding='utf-8')
        self.cli('card_save', '--task', foreign_task, '--card', self.card_source, '--expected-version', '1')
        self.cli('revise', '--task', foreign_task, '--spec-rev', '2', '--card-version', '2')
        foreign = self.cli('dispatch', '--task', foreign_task, '--runtime-mode', 'approval-required')['attempt']
        before = self.status()
        self.guard('reclaim', previous['attempt_id'])
        self.assertEqual(self.status(), before)
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=current['workspace']).stdout.strip(), candidate)
        self.assertTrue(Path(foreign['workspace']).is_dir())
        self.assertIn(foreign['thread_id'], self.store()['threads'])
        self.only_own_close(old_thread)
        self.finish_checks()
        with self.subTest(field='old-directory'):
            self.contract('W07 only the reclaimed historical directory is removed', not Path(previous['workspace']).exists(), False,
                          Path(previous['workspace']).exists())
        with self.subTest(field='old-reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a1')
            self.contract('W07 historical reference preserves its own tip', actual == self.base, self.base, actual)
        self.cli('revoke', '--task', self.task, '--reason', 'End the clean unbound current writer')
        with self.subTest(field='current-directory'):
            self.contract('W07 revoked unbound current directory is removed', not Path(current['workspace']).exists(), False,
                          Path(current['workspace']).exists())
        with self.subTest(field='current-reference'):
            actual = self.ref_or_none('refs/a2a/attempts/' + self.task + '/a2')
            self.contract('W07 current reference preserves the separate current tip', actual == candidate, candidate, actual)
        self.assertTrue(Path(foreign['workspace']).is_dir())


class CASContracts(ContractChecks, old.DaemonCAS):
    def test_cas_write_race_revalidates(self):
        self.create()
        attempt = self.dispatch_candidate_attempt()
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        (self.oracle_control / 'release-all').write_text('continue', encoding='utf-8')
        first = self.cli('verify', '--task', self.task)['verification']
        control = self.install_git_wrapper('before')
        original = self.start_cli('integrate', '--task', self.task)
        barrier = self.wait_barrier(control, original)
        (self.repo / 'external.txt').write_bytes(b'Independent CAS writer must survive.\n')
        self.git('add', 'external.txt')
        self.git('commit', '-m', 'Independent concurrent CAS writer')
        external = self.git('rev-parse', 'HEAD').stdout.strip()
        # The first wrapper is already running. Route later Git invocations
        # directly to Git; release-all aborts unclaimed wrapper invocations.
        restored = self.git_route.with_suffix('.unwrapped.json')
        old.recovery.write_new(restored, {'executable': old.recovery.REAL_GIT})
        restored.replace(self.git_route)
        self.release(barrier)
        reply = self.parse_cli(self.complete(original))
        self.contract('W11 lost prepared comparison triggers fresh verification', reply['ok'] is True, True, reply)
        current = self.status()
        v = current['verification']
        self.assertEqual(current['state'], 'accepted')
        self.assertNotEqual(v['verification_id'], first['verification_id'])
        self.contract('W11 revalidation uses the independent writer head', v['G'] == external, external, v['G'])
        self.assertEqual(v['C'], candidate)
        for commit in (candidate, external):
            relation = self.process(['git', '-C', self.repo, 'merge-base', '--is-ancestor', commit, self.ref()])
            self.contract('W11 integrated history retains ancestor ' + commit, relation.returncode == 0, 0, relation.returncode)
        self.assertEqual((self.repo / 'external.txt').read_bytes(), b'Independent CAS writer must survive.\n')
        self.assertEqual(len(self.entries(self.oracle_control)), 2)


class ConflictContracts(ContractChecks, old.DaemonRun):
    """Real CLI/Git conflicts; only the native session boundary is controlled."""

    def setUp(self):
        self.conflict_evidence = {'steps': [], 'cleanup_failures': []}
        previous_host = old.HOST
        old.HOST = ROOT / 'workbench/tests/conflict_acceptance_host.ts'
        # Restore only after the inherited owned-daemon cleanup has completed.
        self.addCleanup(setattr, old, 'HOST', previous_host)
        super().setUp()
        (self.repo / 'src').mkdir()
        (self.repo / 'src/settings.json').write_text('{"worker":"base","host":"base"}\n', encoding='utf-8')
        (self.repo / 'host.txt').write_text('original host file\n', encoding='utf-8')
        self.git('add', 'src/settings.json', 'host.txt')
        self.git('commit', '-m', 'Independent conflict baseline')
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()
        self.artifact['conflict_base_commit'] = self.base
        self.oracle_runs = self.root / 'conflict-oracle.jsonl'
        source = ('import json,os\nfrom pathlib import Path\n'
                  'actual=json.loads(Path("src/settings.json").read_text())\n'
                  'assert actual=={"worker":"ready","host":"ready"},actual\n'
                  'assert Path("host.txt").read_text()=="integrated host file\\n"\n'
                  'with open(' + repr(str(self.oracle_runs)) + ',"a",encoding="utf-8") as out:\n'
                  ' out.write(json.dumps({"cwd":os.getcwd(),"actual":actual})+"\\n")\n')
        card = {'id': self.task, 'source': None,
                'goal': '设置 worker=ready；保留工作分支上的 host 设置和 host.txt。',
                'non_goals': ['不修改 host.txt 或 src/private/'],
                'paths': {'allow': ['src/'], 'deny': ['src/private/']},
                'oracle_paths': ['acceptance/criterion.py', 'CONTRACT.md'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c', source]}],
                'red_commands': [], 'task_type': '后端逻辑', 'repair_target': None, 'complexity': 'L',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'},
                'base_commit': None, 'writer': None}
        self.card_source = self.root / 'conflict-card.json'
        self.card_source.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
        self.cli('card_save', '--task', self.task, '--card', self.card_source, '--expected-version', '0')
        self.cli('create', '--task', self.task, '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1')

    def evidence(self, name, passed, details):
        self.conflict_evidence['steps'].append({'kind': 'precondition', 'id': name,
                                               'passed': bool(passed), 'details': details})

    def target_contract(self, name, condition, expected, actual):
        assertion_id = CONFLICT_TARGET_IDS[self._testMethodName]
        self.conflict_evidence['steps'].append({'kind': 'target', 'id': assertion_id, 'passed': bool(condition)})
        self.contract(name, condition, expected, actual, assertion_id=assertion_id)

    def _callCleanup(self, function, *args, **kwargs):
        # unittest also classifies cleanup AssertionError as a failure. Keep
        # its origin explicit so it can never count as a target counterfactual.
        try:
            return super()._callCleanup(function, *args, **kwargs)
        except Exception as error:
            self.conflict_evidence['cleanup_failures'].append({
                'callback_type': type(function).__name__, 'error': repr(error)})
            raise

    def request(self, command, *args):
        if command == 'integrate' and '--score-file' not in args:
            attempt = self.status()['current_attempt']
            args = (*args, '--score-file', self.quality.score_file(attempt))
        return self.parse_cli(self.process(self.cli_argv(command, '--task', self.task, *args)))

    def cli(self, command, *args, **kwargs):
        if command == 'integrate' and '--score-file' not in args:
            attempt = self.status()['current_attempt']
            args = (*args, '--score-file', self.quality.score_file(attempt))
        return super().cli(command, *args, **kwargs)

    def submit_request(self, attempt, commit):
        return self.request('submit', '--attempt', attempt['attempt_id'], '--session', attempt['session_id'],
                            '--fence', attempt['fence'], '--spec-rev', attempt['spec_rev'], '--commit', commit)

    def launch_record(self, attempt):
        # Same object sessionFacts returns; written at createThread, before submit copies it to attempt.delivery.
        rows = [json.loads(line) for line in (self.boundary / 'worker-creations.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        matches = [row for row in rows if row.get('attempt') == attempt['attempt_id']]
        if len(matches) != 1:
            raise AssertionError('expected one launch record for ' + attempt['attempt_id'])
        row = matches[0]
        delivery = attempt.get('delivery') or {}
        if delivery and any(delivery.get(key) != row[field] for key, field in (
                ('launch_id', 'id'), ('cli', 'cli_version'), ('model', 'model'), ('effort', 'effort'))):
            raise AssertionError('attempt.delivery disagrees with worker-creations.jsonl')
        return row

    def commit_worker(self, attempt, value, extra=None, foreign=False):
        workspace = Path(attempt['workspace'])
        (workspace / 'src/settings.json').write_text(value, encoding='utf-8')
        for name, contents in (extra or {}).items():
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding='utf-8')
        self.git('add', '.', cwd=workspace)
        row = self.launch_record(attempt)
        trailers = {'Task': 'foreign-task' if foreign else self.task, 'Attempt': attempt['attempt_id'],
                    'Session': attempt['session_id'], 'Role': 'worker', 'Tool': row['cli_version'],
                    'Model': row['model'], 'Effort': row['effort'], 'Native-Session': attempt['thread_id'],
                    'Launch': row['id']}
        message = 'Independent worker change\n\n' + '\n'.join('A2A-' + k + ': ' + v for k, v in trailers.items())
        self.git('commit', '-m', message, cwd=workspace)
        return self.git('rev-parse', 'HEAD', cwd=workspace).stdout.strip()

    def prepare_conflict(self):
        a = self.cli('dispatch', '--task', self.task, '--runtime-mode', 'approval-required')['attempt']
        c = self.commit_worker(a, '{"worker":"ready","host":"base"}\n')
        self.submit(a, c)
        (self.repo / 'src/settings.json').write_text('{"worker":"base","host":"ready"}\n', encoding='utf-8')
        (self.repo / 'host.txt').write_text('integrated host file\n', encoding='utf-8')
        self.git('add', 'src/settings.json', 'host.txt')
        self.git('commit', '-m', 'Other task integrated independently\n\nA2A-Task: foreign-task')
        g = self.git('rev-parse', 'HEAD').stdout.strip()
        self.artifact['conflict_inputs'] = {'attempt': a, 'C1': c, 'G': g,
                                           'worker_path': 'src/settings.json', 'foreign_path': 'host.txt'}
        self.evidence('scenario_prepared', c != g, self.artifact['conflict_inputs'])
        live = self.store()['threads'][a['thread_id']]
        self.evidence('worker_session_input_available', live['thread_id'] == a['thread_id']
                      and not live['stopped'] and not live['archived'],
                      {'attempt': a['attempt_id'], 'thread': a['thread_id'], 'controlled_session': live})
        return a, c, g

    def feedback(self):
        path = self.boundary / 'gate-feedback.jsonl'
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []

    def mode(self, **value):
        write_new(self.boundary / 'conflict-mode.json', value)
        readback = json.loads((self.boundary / 'conflict-mode.json').read_text(encoding='utf-8'))
        return readback

    def system_issues(self, attempt):
        return [view['issue'] for view in self.cli('issues', '--task', self.task)['issues']
                if view['issue']['from'] == 'system' and view['issue']['attempt_id'] == attempt['attempt_id']]

    def observe_conflict(self, a, c, g, verification):
        observed = bool(verification and verification['attempt']['attempt_id'] == a['attempt_id']
                        and (verification['C'], verification['G'], verification['M']) == (c, g, None)
                        and verification.get('conflict', {}).get('files') == ['src/settings.json'])
        details = {'attempt': a['attempt_id'], 'C1': c, 'G': g, 'verification': verification}
        self.evidence('text_conflict_observed', observed, details)
        entered = [event for event in self.events() if event['type'] == 'verification_conflict'
                   and verification and event['details']['verification_id'] == verification['verification_id']
                   and event['details']['attempt']['attempt_id'] == a['attempt_id']
                   and (event['details']['C'], event['details']['G'], event['details']['M']) == (c, g, None)]
        self.evidence('conflict_handling_entered', observed and len(entered) == 1,
                      {'attempt': a['attempt_id'], 'C1': c, 'G': g, 'events': entered})
        if self._testMethodName in (
                'test_conflict_active_worker_reworks_and_integrates', 'test_conflict_ended_session_gets_new_attempt',
                'test_conflict_unknown_session_preserves_scene_and_reports', 'test_conflict_unknown_delivery_does_not_resend'):
            self.evidence('target_verify_executed', observed, details)

    def observe_delivery(self, a, verification):
        feedback = self.feedback()
        prompts = self.store()['prompts']
        events = [event for event in self.events() if event['type'] == 'conflict_feedback_delivered'
                  and event['details']['repair']['verification_id'] == verification['verification_id']]
        delivered = (len(feedback) == 1 and feedback[0]['thread'] == a['thread_id'] and len(events) == 1
                     and events[0]['details']['repair']['message_id'] == feedback[0]['message_id']
                     and any(prompt['thread_id'] == a['thread_id'] and prompt['text'] == feedback[0]['text'] for prompt in prompts))
        self.evidence('conflict_delivered', delivered,
                      {'attempt': a['attempt_id'], 'verification': verification['verification_id'],
                       'feedback': feedback, 'transport_prompts': prompts, 'events': events})

    def verify_rework(self, candidate, check_type):
        reply = self.request('verify')
        verification = self.status()['verification']
        events = [event for event in self.events() if event['type'] == check_type
                  and verification and event['details']['verification_id'] == verification['verification_id']]
        if check_type == 'trailer_check':
            events = [event for event in events if event['details']['commit'] == candidate]
        self.evidence('target_verify_executed',
                      bool(verification and verification['C'] == candidate and events),
                      {'candidate': candidate, 'reply': reply, 'verification': verification, 'events': events})
        return reply

    def conflict(self, a, c, g):
        reply = self.request('verify', '--attempt', a['attempt_id'])
        self.assertFalse(reply['ok'], reply)
        self.assertEqual(reply['error'], 'merge_conflict', reply)
        with sqlite3.connect(self.state.resolve().joinpath('state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
            records = [json.loads(row[0]) for row in db.execute('SELECT data FROM verifications')]
        matches = [v for v in records if v['C'] == c and v['G'] == g and
                   v['attempt']['attempt_id'] == a['attempt_id']]
        self.assertEqual(len(matches), 1, records)
        v = matches[0]
        # Facts preceding the new behavior: a real same-line conflict with no M.
        self.assertEqual((v['G'], v['C'], v['M']), (g, c, None))
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), g)
        if Path(a['workspace']).exists():
            self.assertEqual(self.git('rev-parse', 'HEAD', cwd=a['workspace']).stdout.strip(), c)
            self.assertEqual(Path(a['workspace'], 'src/settings.json').read_text(), '{"worker":"ready","host":"base"}\n')
        self.assertFalse(self.oracle_runs.exists(), 'A conflicted tree cannot reach the completion oracle')
        self.observe_conflict(a, c, g, v)
        self.observe_delivery(a, v)
        return v

    def repair(self, a, g, extra=None, foreign=False):
        # Simulated worker action on its own fixture worktree. The gate must not
        # perform this reset or select either side of the conflict itself.
        self.git('reset', '--hard', g, cwd=a['workspace'])
        c2 = self.commit_worker(a, '{"worker":"ready","host":"ready"}\n', extra, foreign)
        reply = self.submit_request(a, c2)
        current = self.status()
        events = [event for event in self.events() if event['type'] == 'conflict_rework_submitted'
                  and event['details']['attempt'] == a['attempt_id'] and event['details']['candidate'] == c2]
        self.evidence('explicit_resubmitted', reply['ok'] is True and current['candidate_commit'] == c2
                      and current['current_attempt']['attempt_id'] == a['attempt_id'] and len(events) == 1,
                      {'candidate': c2, 'reply': reply, 'task': current, 'events': events})
        self.contract('Conflict rework accepts a new explicit candidate from its bound worker',
                      reply['ok'], True, reply)
        return c2

    def test_conflict_active_worker_reworks_and_integrates(self):
        a, c1, g = self.prepare_conflict()
        v1 = self.conflict(a, c1, g)
        with self.subTest(stage='writeback'):
            feedback = self.feedback()
            self.target_contract('Text conflict is written once to the original active worker',
                          len(feedback) == 1 and feedback[0]['thread'] == a['thread_id'],
                          {'count': 1, 'thread': a['thread_id']}, feedback)
        # Repeat the request while the worker has not resubmitted. No new send,
        # verifier, attempt or implicit candidate may be created.
        self.request('verify', '--attempt', a['attempt_id'])
        self.assertEqual(self.status()['current_attempt']['attempt_id'], a['attempt_id'])
        with self.subTest(stage='writeback-replay'):
            self.contract('Repeated verification does not resend the conflict message',
                          len(self.feedback()) == 1, 1, self.feedback())
        c2 = self.repair(a, g)
        current = self.status()['current_attempt']
        self.assertEqual(current['base_commit'], self.base, 'Claim base remains an immutable identity fact')
        self.assertNotEqual(current['turn_id'], a['turn_id'], 'Repair occurs in a new turn of the same native session')
        c3 = self.commit_worker(a, '{"worker":"unauthorized","host":"ready"}\n')
        denied = self.submit_request(a, c3)
        self.assertFalse(denied['ok'], denied)
        self.assertEqual(denied['error'], 'candidate_conflict')
        self.assertEqual(self.status()['candidate_commit'], c2)
        self.git('reset', '--hard', c2, cwd=a['workspace'])
        v2 = self.cli('verify', '--task', self.task)['verification']
        self.assertNotEqual(v1['verification_id'], v2['verification_id'])
        self.assertEqual((v2['G'], v2['C'], v2['M'], v2['state']), (g, c2, c2, 'passed'))
        events = self.events()
        paths = [e['details'] for e in events if e['type'] == 'path_check' and
                 e['details']['verification_id'] == v2['verification_id']]
        self.assertEqual(len(paths), 1)
        self.assertEqual(set(paths[0]['paths']), {'src/settings.json'})
        trailers = [e['details']['commit'] for e in events if e['type'] == 'trailer_check' and
                    e['details']['verification_id'] == v2['verification_id']]
        self.assertEqual(trailers, [c2], 'Already integrated foreign commits are not attributed to this worker')
        self.assertEqual(len(self.oracle_runs.read_text(encoding='utf-8').splitlines()), 1)
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            saved = json.loads(db.execute('SELECT data FROM verifications WHERE id=?', (v1['verification_id'],)).fetchone()[0])
        self.assertEqual((saved['C'], saved['G'], saved['M']), (c1, g, None))
        self.cli('integrate', '--task', self.task)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), c2)
        self.assertEqual((self.repo / 'host.txt').read_text(), 'integrated host file\n')
        self.assertEqual(json.loads((self.repo / 'src/settings.json').read_text()), {'worker': 'ready', 'host': 'ready'})

    def test_conflict_ended_session_gets_new_attempt(self):
        a, c1, g = self.prepare_conflict()
        selected = self.mode(thread=a['thread_id'], observation={'stopped': True, 'running': False})
        self.evidence('ended_session_input_configured',
                      selected == {'thread': a['thread_id'], 'observation': {'stopped': True, 'running': False}}, selected)
        self.conflict(a, c1, g)
        new = self.status()['current_attempt']
        self.target_contract('Confirmed ended worker is replaced by one new attempt',
                      new['attempt_id'] != a['attempt_id'] and new['fence'] == a['fence'] + 1,
                      {'different_attempt': True, 'fence': 2}, new)
        for key in ('session_id', 'thread_id', 'workspace'):
            self.assertNotEqual(new[key], a[key])
        self.assertEqual(new['base_commit'], g)
        self.assertEqual(len(self.store()['prompts']), 2)
        self.assertEqual(self.feedback(), [], 'The ended thread must not receive a new turn')
        self.assertEqual(self.git('rev-parse', 'refs/a2a/attempts/' + self.task + '/a1').stdout.strip(), c1)
        self.assertFalse(Path(a['workspace']).exists())
        before = self.status()
        stale = self.submit_request(a, c1)
        self.assertFalse(stale['ok'], stale)
        self.assertEqual(stale['error'], 'stale_attempt')
        self.request('verify', '--attempt', a['attempt_id'])
        self.assertEqual(self.status(), before)
        self.assertEqual(len(self.store()['prompts']), 2)
        c2 = self.commit_worker(new, '{"worker":"ready","host":"ready"}\n')
        self.submit(new, c2)
        self.cli('verify', '--task', self.task)
        self.cli('integrate', '--task', self.task)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), c2)

    def test_conflict_unknown_session_preserves_scene_and_reports(self):
        a, c1, g = self.prepare_conflict()
        selected = self.mode(thread=a['thread_id'], observation={'error': {'providerPresent': False, 'activeTurn': None}})
        self.evidence('unknown_session_input_configured', selected == {
            'thread': a['thread_id'], 'observation': {'error': {'providerPresent': False, 'activeTurn': None}}}, selected)
        self.request('verify', '--attempt', a['attempt_id'])
        self.observe_conflict(a, c1, g, self.status()['verification'])
        self.assertEqual(self.status()['current_attempt']['attempt_id'], a['attempt_id'])
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=a['workspace']).stdout.strip(), c1)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), g)
        self.assertEqual(len(self.store()['prompts']), 1)
        self.assertEqual(self.feedback(), [])
        issues = self.system_issues(a)
        self.target_contract('Unknown native session keeps the conflict scene and reports to the executor',
                      bool(issues), 'system issue bound to original attempt', issues)

    def test_conflict_unknown_delivery_does_not_resend(self):
        a, c1, g = self.prepare_conflict()
        selected = self.mode(delivery_unknown=True)
        self.evidence('delivery_unknown_input_configured', selected == {'delivery_unknown': True}, selected)
        first = self.request('verify', '--attempt', a['attempt_id'])
        self.assertFalse(first['ok'], first)
        self.observe_conflict(a, c1, g, self.status()['verification'])
        self.target_contract('Unknown writeback has exactly one recorded delivery attempt',
                      len(self.feedback()) == 1, 1, self.feedback())
        self.request('verify', '--attempt', a['attempt_id'])
        self.assertEqual(len(self.feedback()), 1)
        self.assertEqual(self.status()['current_attempt']['attempt_id'], a['attempt_id'])
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=a['workspace']).stdout.strip(), c1)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), g)
        self.assertTrue(self.system_issues(a))

    def test_merge_command_error_is_not_text_conflict(self):
        a, c1, g = self.prepare_conflict()
        fault = self.root / 'merge-error-git'
        fault.write_text('#!' + sys.executable + '\nimport os,sys\n'
                         'if "merge" in sys.argv[1:]:\n'
                         ' sys.stderr.write("fixture: merge I/O unavailable\\n");sys.exit(73)\n'
                         'os.execv(' + repr(old.recovery.REAL_GIT) + ',[' + repr(old.recovery.REAL_GIT) + ']+sys.argv[1:])\n',
                         encoding='utf-8')
        fault.chmod(0o755)
        selected = self.git_route.with_suffix('.merge-error.json')
        write_new(selected, {'executable': str(fault)})
        selected.replace(self.git_route)
        reply = self.request('verify', '--attempt', a['attempt_id'])
        self.assertFalse(reply['ok'], reply)
        v = self.status()['verification']
        unmerged = self.git('ls-files', '--unmerged', '-z', cwd=v['workspace']).stdout
        self.assertEqual(unmerged, '')
        self.assertEqual(v['result']['returncode'], 73)
        self.assertEqual(self.feedback(), [])
        self.assertEqual(self.status()['current_attempt']['attempt_id'], a['attempt_id'])
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), g)
        self.evidence('git_io_failure_observed', v['result']['returncode'] == 73 and unmerged == '',
                      {'verification': v, 'reply': reply, 'unmerged': unmerged, 'exit': v['result']['returncode']})
        self.evidence('target_verify_executed', v['C'] == c1 and v['G'] == g and
                      v['attempt']['attempt_id'] == a['attempt_id'], {'verification': v, 'reply': reply})
        self.target_contract('Git failure without unmerged index entries is not a repairable text conflict',
                      reply['error'] == 'git_failed', 'git_failed', reply)

    def test_conflict_rework_still_rejects_forbidden_path(self):
        a, c1, g = self.prepare_conflict()
        self.conflict(a, c1, g)
        c2 = self.repair(a, g, extra={'src/private/secret.txt': 'worker-created forbidden data\n'})
        reply = self.verify_rework(c2, 'path_check')
        self.target_contract('Conflict rework still rejects the forbidden path at verify',
                             reply['ok'] is False and reply.get('error') == 'path_boundary_failed',
                             {'ok': False, 'error': 'path_boundary_failed'}, reply)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), g)
        self.assertFalse(self.oracle_runs.exists())

    def test_conflict_rework_still_rejects_foreign_trailer(self):
        a, c1, g = self.prepare_conflict()
        self.conflict(a, c1, g)
        c2 = self.repair(a, g, foreign=True)
        reply = self.verify_rework(c2, 'trailer_check')
        self.target_contract('Conflict rework still rejects the foreign trailer at verify',
                             reply['ok'] is False and reply.get('error') == 'trailer_task_mismatch',
                             {'ok': False, 'error': 'trailer_task_mismatch'}, reply)
        checks = [e['details'] for e in self.events() if e['type'] == 'trailer_check' and e['details']['commit'] == c2]
        self.assertEqual(len(checks), 1)
        self.assertFalse(checks[0]['passed'])
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), g)


CASES = [(WorktreeContracts, name) for name in (
    'test_worker_name', 'test_clean_revoke', 'test_clean_revise', 'test_verification_name',
    'test_completed_verification_cleanup', 'test_overlap_without_reason',
    'test_dirty_revoke_keeps_scene_and_reports', 'test_unknown_cleanup_keeps_scene_and_reports',
    'test_dirty_integration_reports_without_mutation', 'test_r8_revalidates_on_new_head',
    'test_r8_stops_at_fourth_cas_miss',
    'test_r8_missing_trailer_is_not_recorded_twice',
)] + [(RunCleanupContracts, name) for name in (
    'test_integrated_run_cleanup', 'test_timeout_cleanup_retains_unsubmitted_commit', 'test_rejected_run_cleanup',
    'test_superseded_run_retains_only_new_workspace', 'test_historical_cleanup_leaves_current_and_foreign_untouched',
)] + [(CASContracts, 'test_cas_write_race_revalidates')] + [(ConflictContracts, name) for name in (
    'test_conflict_active_worker_reworks_and_integrates',
    'test_conflict_ended_session_gets_new_attempt',
    'test_conflict_unknown_session_preserves_scene_and_reports',
    'test_conflict_unknown_delivery_does_not_resend',
    'test_merge_command_error_is_not_text_conflict',
    'test_conflict_rework_still_rejects_forbidden_path',
    'test_conflict_rework_still_rejects_foreign_trailer',
)]


def observe(argv):
    p = subprocess.run([str(arg) for arg in argv], cwd=ROOT, capture_output=True, text=True)
    return {'argv': [str(arg) for arg in argv], 'cwd': str(ROOT), 'exit_code': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr}


def snapshot_source(out, product_root):
    names = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'workbench/src').rglob('*.ts'))
    names += [str(p.relative_to(ROOT)) for p in (ROOT / 'workbench/tests').glob('*.py')]
    names += [str(p.relative_to(ROOT)) for p in (ROOT / 'workbench/tests').glob('*.ts')]
    names += ['workbench/package.json', 'workbench/package-lock.json',
              '.project-map/tickets/T-077-worktree-lifecycle-conflicts.md',
              '.project-map/specs/native-cli-orchestration-2026-10-10.md',
              'evidence/2026-10-11-batch13/T-077/PLAN.md',
              'evidence/2026-10-11-batch13/T-077/controller-decision-01.md',
              'evidence/2026-10-11-batch13/T-077/controller-decision-02.md',
              'evidence/2026-10-11-batch13/T-077/outside-sandbox.sh']
    for folder in ('acceptance', 'fixtures/pagination'):
        names += [str(p.relative_to(ROOT)) for p in (ROOT / folder).rglob('*')
                  if p.is_file() and p.suffix in ('.py', '.ts', '.md') and '__pycache__' not in p.parts]
    with tarfile.open(out / 'sources.tar.gz', 'x:gz') as archive:
        for name in sorted(set(names)):
            source_root = product_root if name.startswith(('workbench/src/', 'acceptance/entry/')) or name in (
                'workbench/package.json', 'workbench/package-lock.json', 'workbench/tests/daemon_acceptance_host.ts') else ROOT
            archive.add(source_root / name, arcname=name, recursive=False)
    write_new(out / 'source-files.json', sorted(set(names)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--case', action='append', choices=[name for _, name in CASES])
    parser.add_argument('--baseline-product', type=Path)
    parser.add_argument('--mutant-product', type=Path,
                        help='Isolated known-bad product; selected baseline cases only')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output.resolve()
    # Never let this worker's capability, hook configuration or CODEX_HOME leak
    # into the fixture clients. No auth file or real CLI is needed in this batch.
    for key in list(os.environ):
        if key.startswith(('A2A_', 'CODEX_', 'GIT_')):
            del os.environ[key]
    preflight = {'head': observe(['git', 'rev-parse', 'HEAD']),
                 'source_diff': observe(['git', 'diff', 'HEAD', '--', 'workbench/src']),
                 'node': observe(['node', '--version']), 'git': observe(['git', '--version']),
                 'volume_mounted': os.path.ismount('/Volumes/WD-Elements')}
    write_new(out / 'preflight.json', preflight)
    if not preflight['volume_mounted'] or not preflight['node']['stdout'].startswith('v26.5.'):
        raise RuntimeError('Required external volume or Node 26.5 is unavailable')
    product_root = ROOT
    if args.mutant_product:
        if args.phase != 'baseline' or not args.case or args.baseline_product:
            raise RuntimeError('A mutant requires selected baseline cases and no original baseline product')
        product_root = args.mutant_product.resolve(strict=True)
    if args.baseline_product:
        if args.phase != 'baseline' or not args.case:
            raise RuntimeError('A frozen product requires explicitly selected baseline cases')
        product_root = args.baseline_product.resolve(strict=True)
        archive_path = ROOT / 'evidence/2026-10-11-batch13/T-077/outside-red-01/sources.tar.gz'
        verified = []
        with tarfile.open(archive_path, 'r:gz') as archive:
            for member in archive.getmembers():
                if member.isfile() and (member.name.startswith(('workbench/src/', 'acceptance/entry/')) or member.name in (
                        'workbench/package.json', 'workbench/package-lock.json', 'workbench/tests/daemon_acceptance_host.ts')):
                    with archive.extractfile(member) as source:
                        if (product_root / member.name).read_bytes() != source.read():
                            raise RuntimeError('Frozen product differs from the confirmed red-01 source: ' + member.name)
                    verified.append(member.name)
        if not verified:
            raise RuntimeError('Confirmed baseline archive has no product source')
        cards.GATE = product_root / 'workbench/src/gates/cli.ts'
        old.ROOT = product_root
        old.CLI = cards.GATE
        old.ENTRY = product_root / 'acceptance/entry/a2a_gates.py'
        old.DAEMON = product_root / 'workbench/src/daemon.ts'
        old.HOST = product_root / 'workbench/tests/daemon_acceptance_host.ts'
        old.delivery.SCRIPT = old.ENTRY
        os.environ['COOP_SCRIPT'] = str(old.ENTRY)
        os.environ['COOP_NATIVE_ENTRY'] = str(old.CLI)
        write_new(out / 'baseline-binding.json', {'archive': str(archive_path), 'product_root': str(product_root),
                    'source_commit': BASE, 'byte_equal_files': verified, 'case_source_root': str(ROOT)})
    if args.mutant_product:
        cards.GATE = product_root / 'workbench/src/gates/cli.ts'
        old.ROOT = product_root
        old.CLI = cards.GATE
        old.ENTRY = product_root / 'acceptance/entry/a2a_gates.py'
        old.DAEMON = product_root / 'workbench/src/daemon.ts'
        old.HOST = product_root / 'workbench/tests/daemon_acceptance_host.ts'
        old.delivery.SCRIPT = old.ENTRY
        os.environ['COOP_SCRIPT'] = str(old.ENTRY)
        os.environ['COOP_NATIVE_ENTRY'] = str(old.CLI)
        write_new(out / 'mutant-binding.json', {'kind': 'isolated_known_bad_product',
                   'product_root': str(product_root), 'harness_root': str(ROOT), 'selected': args.case})
    if args.phase == 'baseline' and not args.baseline_product and not args.mutant_product and (preflight['head']['stdout'].strip() != BASE or preflight['source_diff']['stdout']):
        raise RuntimeError('Baseline must run unchanged product source at the assigned starting commit')
    if any(v.get('exit_code') != 0 for v in preflight.values() if isinstance(v, dict)):
        raise RuntimeError('Preflight command failed')
    # Preserve candidate source plus the parent's exact mutation recipe.
    # Do not put temporary mutant source into the committed evidence archive.
    snapshot_source(out, ROOT if args.mutant_product else product_root)
    fixture_root = Path(tempfile.mkdtemp(prefix='s3-', dir='/tmp'))
    cards.ARTIFACT_ROOT = fixture_root
    os.environ['COOP_E2E_ARTIFACT_ROOT'] = str(fixture_root)
    os.environ['COOP_E2E_READBACK_ROOT'] = str(out / 'readbacks')
    (out / 'readbacks').mkdir()
    selected = [(cls, name) for cls, name in CASES if not args.case or name in args.case]
    receipts = []
    for number, (cls, name) in enumerate(selected, 1):
        target = out / f'{number:02d}-{name}'
        target.mkdir()
        start = (len(cards.COMMANDS), len(old.delivery.COMMANDS), len(CONTRACTS), len(old.recovery.ASSERTIONS))
        stream = io.StringIO()
        test = cls(name)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite([test]))
        with (target / 'unittest.txt').open('x', encoding='utf-8') as handle:
            handle.write(stream.getvalue())
        contracts = CONTRACTS[start[2]:]
        record = {'case': name, 'phase': args.phase, 'tests_run': result.testsRun,
                  'exit_code': 0 if result.wasSuccessful() else 1,
                  'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
                  'business_red': bool(result.failures and not result.errors and any(not c['pass'] for c in contracts)),
                  'contracts': contracts, 'inherited_assertions': old.recovery.ASSERTIONS[start[3]:],
                  'evidence_layer': 'controlled-thread' if cls in (RunCleanupContracts, ConflictContracts) else 'default-daemon-manual-claim'}
        if cls is ConflictContracts:
            record.update(classify_conflict_red(name, contracts, test.conflict_evidence,
                tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped)))
        write_new(target / 'result.json', record)
        write_gzip(target / 'commands.json.gz', cards.COMMANDS[start[0]:] + old.delivery.COMMANDS[start[1]:])
        receipts.append(record)
        print(json.dumps({'case': name, 'failures': record['failures'], 'errors': record['errors'],
                          'business_red': record['business_red']}, ensure_ascii=False), flush=True)
    with tarfile.open(out / 'fixtures.tar.gz', 'x:gz') as archive:
        archive.add(fixture_root, arcname=fixture_root.name)
    red_confirmed = bool(receipts) and all(r['business_red'] and not r['skipped'] for r in receipts)
    green = bool(receipts) and all(r['exit_code'] == 0 and r['tests_run'] == 1 and not r['skipped']
        and not r.get('cleanup_failures') and r.get('target_passed', True) for r in receipts)
    record = {'status': 'PASS' if args.phase == 'candidate' and green else 'INCOMPLETE',
              'scope': 'S3 initial focused contracts only; not full T-077 acceptance',
              'phase': args.phase, 'red_confirmed': red_confirmed if args.phase == 'baseline' else None,
              'argv': sys.argv, 'cwd': str(ROOT), 'fixture_root': str(fixture_root),
              'real_codex_turns': 0, 'cases': receipts}
    write_new(out / 'run.json', record)
    print(json.dumps({k: record[k] for k in ('status', 'phase', 'red_confirmed', 'real_codex_turns')}, ensure_ascii=False))
    return 0 if (red_confirmed if args.phase == 'baseline' else green) else 1


if __name__ == '__main__':
    raise SystemExit(main())
