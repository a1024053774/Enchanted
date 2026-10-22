"""T-075-2：真实 CLI / Git / SQLite 的独立任务卡验收。"""
import argparse
import copy
import datetime
import json
import os
import shutil
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / 'workbench/src/gates/cli.ts'
OUT = None
ARTIFACT_ROOT = None
COMMANDS = []
ARTIFACTS = []
FIELDS = {'id', 'source', 'goal', 'non_goals', 'paths', 'oracle_paths', 'completion_conditions',
          'red_commands', 'task_type', 'repair_target', 'complexity', 'executor',
          'base_commit', 'writer'}


class TaskCardsCLI(unittest.TestCase):
    def setUp(self):
        # Full case IDs remain in ARTIFACTS/COMMANDS; directory names must fit
        # the daemon's Unix socket limit after /tmp resolves to /private/tmp.
        self.root = Path(tempfile.mkdtemp(prefix='c-', dir=str(ARTIFACT_ROOT)))
        self.repo = self.root / 'repo'
        self.state = self.root / 'state'
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'A2A_'))}
        self.env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                         'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
                         'GIT_CONFIG_VALUE_0': os.devnull, 'GIT_CONFIG_KEY_1': 'commit.gpgsign',
                         'GIT_CONFIG_VALUE_1': 'false', 'GIT_AUTHOR_NAME': 'Independent fixture',
                         'GIT_AUTHOR_EMAIL': 'fixture@example.invalid', 'GIT_COMMITTER_NAME': 'Independent fixture',
                         'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'})
        self.git('init', '-b', 'main')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/value.txt').write_text('base\n', encoding='utf-8')
        (self.repo / 'host.txt').write_text('base host\n', encoding='utf-8')
        (self.repo / 'acceptance').mkdir()
        (self.repo / 'acceptance/criterion.py').write_text(
            "from pathlib import Path\nassert Path('src/value.txt').read_text() == 'worker\\n'\n", encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-m', 'Independent baseline')
        self.base = self.oid()
        self.task = 'fixture-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d') + '-1'
        self.card = {
            'id': self.task, 'source': None, 'goal': '交付 src/value.txt 中的独立预期内容',
            'non_goals': ['不修改项目外的文件'], 'paths': {'allow': ['src/'], 'deny': ['src/private/']},
            'oracle_paths': ['acceptance/criterion.py'],
            'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c',
                "from pathlib import Path; import runpy; runpy.run_path('acceptance/criterion.py')"]}],
            'red_commands': [], 'task_type': '后端逻辑', 'repair_target': None, 'complexity': 'L',
            'executor': {'cli': 'Codex', 'model': 'gpt-6-astra', 'effort': 'xhigh'},
            'base_commit': None, 'writer': None,
        }
        self.card_file = self.root / 'card.json'
        ARTIFACTS.append({'test': self.id(), 'root': str(self.root), 'task': self.task, 'base': self.base})

    def process(self, argv, cwd=None):
        cwd = Path(cwd or self.root)
        p = subprocess.run([str(v) for v in argv], cwd=str(cwd), env=self.env,
                           capture_output=True, text=True, timeout=90)
        COMMANDS.append({'test': self.id(), 'argv': [str(v) for v in argv], 'cwd': str(cwd),
                         'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        return p

    def git(self, *args, cwd=None):
        p = self.process(['git', '-C', str(cwd or self.repo), *args])
        self.assertEqual(p.returncode, 0, COMMANDS[-1])
        return p.stdout.strip()

    def oid(self, cwd=None, ref='HEAD'):
        return self.git('rev-parse', ref, cwd=cwd)

    def cli(self, command, *args, ok=True, error=None):
        p = self.process(['node', GATE, '--state', self.state, command, '--task', self.task, *args])
        self.assertEqual(p.returncode, 0 if ok else 1, COMMANDS[-1])
        value = json.loads(p.stdout)
        self.assertEqual(value['ok'], ok, value)
        if error:
            self.assertEqual(value['error'], error, value)
        return value

    def save_card(self, expected=0, card=None):
        self.card_file.write_text(json.dumps(card or self.card, ensure_ascii=False), encoding='utf-8')
        return self.cli('card_save', '--card', self.card_file, '--expected-version', str(expected))

    def register_task(self):
        template = self.cli('card_template', '--repo', self.repo, '--project', 'fixture')['card']
        self.assertEqual(set(template), FIELDS)
        self.assertEqual(template['id'], self.task)
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')

    def create(self):
        self.register_task()
        return self.cli('claim', '--owner', 'independent-check')['attempt']

    def create_managed(self):
        self.register_task()
        return self.dispatch_candidate_attempt()

    def commit(self, attempt, files=None, trailers=True, foreign=None):
        workspace = Path(attempt['workspace'])
        for name, value in (files or {'src/value.txt': 'worker\n'}).items():
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value, encoding='utf-8')
        message = 'Independent fixture commit'
        if trailers:
            values = {'Task': foreign or self.task, 'Attempt': attempt['attempt_id'],
                      'Session': attempt['session_id'], 'Role': 'worker', 'Tool': 'Codex 0.162.1',
                      'Model': 'gpt-6-astra', 'Effort': 'xhigh', 'Native-Session': 'unknown',
                      'Launch': 'fixture-launch'}
            if attempt['thread_id']:
                values.update(self.managed_trailers(attempt))
            message += '\n\n' + '\n'.join('A2A-' + k + ': ' + v for k, v in values.items())
        self.git('add', '.', cwd=workspace)
        self.git('commit', '-m', message, cwd=workspace)
        return self.oid(workspace)

    def submit(self, a, commit, ok=True, error=None, **changes):
        identity = {'attempt': a['attempt_id'], 'session': a['session_id'], 'fence': a['fence'],
                    'spec-rev': a['spec_rev'], 'commit': commit}
        identity.update(changes)
        args = [value for key, item in identity.items() for value in ('--' + key, str(item))]
        return self.cli('submit', *args, ok=ok, error=error)

    def events(self):
        return self.cli('events')['events']

    def reject_verify(self, code):
        before = self.events()
        ref = self.oid(ref='refs/heads/main')
        self.cli('verify', ok=False, error=code)
        after = self.events()
        self.assertEqual(after[:len(before)], before)
        self.assertTrue(any(e['type'] == 'rejected' and e['details'].get('error') == code for e in after[len(before):]))
        self.assertEqual(self.oid(ref='refs/heads/main'), ref)
        self.assertNotEqual(self.cli('status')['task']['state'], 'accepted')
        self.cli('integrate', ok=False)

    def test_tracer_merges_G_and_C_and_integrates_once(self):
        self.card['completion_conditions'][0]['argv'][-1] += "; assert Path('host.txt').read_text() == 'host\\n'"
        a = self.create_managed()
        c = self.commit(a)
        (self.repo / 'host.txt').write_text('host\n', encoding='utf-8')
        self.git('add', 'host.txt')
        self.git('commit', '-m', 'Independent G advance')
        g = self.oid()
        self.submit(a, c)
        v = self.cli('verify')['verification']
        self.assertEqual(v['G'], g)
        self.assertEqual(v['C'], c)
        self.assertNotIn(v['M'], (g, c))
        self.assertEqual(self.oid(), g)
        self.assertFalse(Path(v['workspace']).exists())
        self.assertEqual(self.oid(ref='refs/a2a/verifications/' + self.task + '/a1/v1'), v['M'])
        self.assertEqual(self.git('rev-list', '--parents', '-n', '1', v['M']).split()[1:], [g, c])
        log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        self.cli('integrate')
        self.assertEqual(self.oid(), v['M'])
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual((self.repo / 'src/value.txt').read_text(), 'worker\n')
        self.assertEqual((self.repo / 'host.txt').read_text(), 'host\n')
        after = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        self.assertEqual(len(after.splitlines()), len(log.splitlines()) + 1)
        self.cli('integrate')
        self.assertEqual(self.git('reflog', 'show', '--format=%H', 'refs/heads/main'), after)
        types = [e['type'] for e in self.events()]
        for name in ('card_saved', 'created', 'claimed', 'submitted', 'path_check', 'completion_check', 'red_not_applicable', 'rules_not_applicable', 'trailer_check', 'review_result', 'score_recorded', 'integrated'):
            self.assertIn(name, types)
        self.assertNotIn('refs/a2a/integration', self.git('show-ref'))

    def test_forbidden_path_rejected(self):
        a = self.create()
        self.submit(a, self.commit(a, {'src/value.txt': 'worker\n', 'src/private/secret.txt': 'out of scope\n'}))
        self.reject_verify('path_boundary_failed')
        self.assertFalse(any(e['type'] == 'completion_check' for e in self.events()))

    def test_failing_command_rejected(self):
        self.card['completion_conditions'].extend([
            {'argv': [sys.executable, '-c', 'import sys; sys.exit(17)']},
            {'argv': [sys.executable, '-c', "raise AssertionError('must not run')"]}])
        a = self.create()
        self.submit(a, self.commit(a))
        self.reject_verify('oracle_failed')
        checks = [e['details'] for e in self.events() if e['type'] == 'completion_check']
        self.assertEqual([x['result']['returncode'] for x in checks], [0, 17])

    def test_foreign_middle_commit_rejected(self):
        a = self.create()
        bad = self.commit(a, foreign='another-task')
        c = self.commit(a, {'src/second.txt': 'a later correct commit\n'})
        self.submit(a, c)
        self.reject_verify('trailer_task_mismatch')
        self.assertTrue(any(e['type'] == 'trailer_check' and e['details']['commit'] == bad for e in self.events()))

    def test_missing_trailer_records_one_inferred_action_and_integrates(self):
        a = self.create_managed()
        missing = self.commit(a, trailers=False)
        c = self.commit(a, {'src/second.txt': 'correct trailer\n'})
        self.submit(a, c)
        self.cli('verify')
        status = self.cli('status')
        inputs = status['user_inputs']
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0]['form'], 'action')
        self.assertEqual(inputs[0]['certainty'], 'inferred')
        self.assertEqual(inputs[0]['source_ref']['label'], '推断：缺尾注')
        self.assertEqual(inputs[0]['source_ref']['commit'], missing)
        self.assertEqual(inputs[0]['target']['attempt'], a['attempt_id'])
        events = [e for e in self.events() if e['type'] == 'human_intervention']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['details']['input_id'], inputs[0]['id'])
        self.cli('integrate')
        self.cli('integrate')
        self.assertEqual(self.oid(), c)
        self.assertEqual(self.cli('status')['user_inputs'], inputs)

    def test_stale_fence_and_attempt_rejected(self):
        a = self.create()
        c = self.commit(a)
        self.submit(a, c, ok=False, error='stale_fence', fence=a['fence'] + 1)
        self.cli('revoke', '--reason', 'independent replacement')
        new = self.cli('claim', '--owner', 'new-owner')['attempt']
        self.submit(a, c, ok=False, error='stale_attempt')
        self.assertEqual(self.cli('status')['task']['current_attempt']['attempt_id'], new['attempt_id'])
        self.assertEqual(self.oid(), self.base)

    def test_dirty_target_rejects_without_losing_staged_unstaged_or_untracked(self):
        for mode in ('staged', 'unstaged', 'untracked'):
            with self.subTest(mode=mode):
                # Each mode gets an independent task/repo/state and saved scene.
                if mode != 'staged':
                    self.setUp()
                a = self.create_managed()
                self.submit(a, self.commit(a, {'src/value.txt': 'worker\n', 'src/new.txt': 'candidate\n'}))
                self.cli('verify')
                path = self.repo / ('src/new.txt' if mode == 'untracked' else 'src/value.txt')
                path.write_text('User content must survive\n', encoding='utf-8')
                if mode == 'staged':
                    self.git('add', str(path))
                index = self.git('ls-files', '--stage')
                log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
                reply = self.cli('integrate', ok=False)
                self.assertEqual(path.read_text(), 'User content must survive\n')
                self.assertEqual(self.git('ls-files', '--stage'), index)
                self.assertEqual(self.oid(), self.base)
                self.assertEqual(self.git('reflog', 'show', '--format=%H', 'refs/heads/main'), log)
                self.assertEqual(reply['error'], 'dirty_integration_worktree')

    def test_card_validation_versions_and_claim_snapshot(self):
        invalid = []
        for key in FIELDS:
            card = copy.deepcopy(self.card)
            del card[key]
            invalid.append(card)
        for key, value in [('non_goals', []), ('completion_conditions', 'tests pass'),
                           ('completion_conditions', [{'argv': []}]),
                           ('completion_conditions', [{'argv': ['/not/a/program']}]),
                           ('completion_conditions', [{'argv': [sys.executable, '{worktree}/invalid']}]),
                           ('task_type', 'unknown'), ('complexity', 'XL'),
                           ('executor', {'cli': 'codex', 'model': 'fixture', 'effort': 'xhigh'}),
                           ('paths', {'allow': [], 'deny': []}),
                           ('paths', {'allow': ['../outside'], 'deny': []})]:
            card = copy.deepcopy(self.card)
            card[key] = value
            invalid.append(card)
        card = copy.deepcopy(self.card)
        card['task_type'] = '缺陷修复'
        invalid.append(card)
        for index, card in enumerate(invalid):
            with self.subTest(index=index):
                self.card_file.write_text(json.dumps(card), encoding='utf-8')
                self.cli('card_save', '--card', self.card_file, '--expected-version', '0', ok=False, error='invalid_task_card')
        # T-122 gui-02: a controller sees only the refusal, so it must name the argv field the entry needs.
        for value in (['python3 check.py'], [{'id': 'C1', 'text': 'python3 check.py exits 0'}],
                      [{'command': 'python3 check.py'}], [{'argv': 'python3 check.py'}]):
            with self.subTest(completion_conditions=value):
                card = copy.deepcopy(self.card)
                card['completion_conditions'] = value
                self.card_file.write_text(json.dumps(card), encoding='utf-8')
                refused = self.cli('card_save', '--card', self.card_file, '--expected-version', '0', ok=False, error='invalid_task_card')
                self.assertIn('argv', refused['details']['reason'], refused)
        # T-122 gui-03: a controller that wrote a string source must learn that null is allowed.
        card = copy.deepcopy(self.card)
        card['source'] = 'user request'
        self.card_file.write_text(json.dumps(card), encoding='utf-8')
        refused = self.cli('card_save', '--card', self.card_file, '--expected-version', '0', ok=False, error='invalid_task_card')
        self.assertIn('null', refused['details']['reason'], refused)
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1')
        # Registration precedes the writer identity and the real claim baseline.
        (self.repo / 'host.txt').write_text('host changed before claim\n', encoding='utf-8')
        self.git('add', 'host.txt')
        self.git('commit', '-m', 'New claim baseline')
        g = self.oid()
        a = self.cli('claim', '--owner', 'independent-check')['attempt']
        self.assertEqual(a['base_commit'], g)
        before = self.cli('status')['task']
        v2 = copy.deepcopy(self.card)
        v2['goal'] = 'A new version must not change the registered contract'
        v2['completion_conditions'] = [{'argv': [sys.executable, '-c', 'import sys; sys.exit(23)']}]
        self.save_card(1, v2)
        self.assertEqual(self.cli('card_show', '--card-version', '1')['card']['goal'], self.card['goal'])
        self.assertEqual(self.cli('status')['task']['card_version'], 1)
        # Claim does not copy a launch record. A trailered commit is rejected; this snapshot case has no trailers.
        c = self.commit(a, trailers=False)
        self.submit(a, c)
        self.cli('verify')
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            rows = db.execute('SELECT id,data FROM task_card_snapshots').fetchall()
        snapshots = {row[0]: json.loads(row[1]) for row in rows}
        self.assertIsNone(snapshots[before['card_snapshot_id']]['base_commit'])
        self.assertEqual(snapshots[a['card_snapshot_id']]['base_commit'], g)
        self.assertEqual(snapshots[a['card_snapshot_id']]['writer']['session_id'], a['session_id'])
        self.cli('revise', '--spec-rev', '2', '--card-version', '2')
        self.assertFalse(Path(a['workspace']).exists())
        self.assertEqual(self.oid(ref='refs/a2a/attempts/' + self.task + '/a1'), c)
        self.submit(a, c, ok=False, error='stale_attempt')
        current = self.cli('claim', '--owner', 'replacement')['attempt']
        self.submit(current, self.commit(current))
        self.reject_verify('oracle_failed')
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            later = dict(db.execute('SELECT id,data FROM task_card_snapshots').fetchall())
        for snapshot_id, raw in rows:
            self.assertEqual(later[snapshot_id], raw)

    def test_path_prefix_rename_delete_and_whitespace(self):
        modes = ('prefix', 'rename-out', 'delete', 'leading-space')
        for index, mode in enumerate(modes):
            with self.subTest(mode=mode):
                if index:
                    self.setUp()
                if mode == 'leading-space':
                    self.card['paths'] = {'allow': ['.'], 'deny': [' private.txt']}
                a = self.create()
                workspace = Path(a['workspace'])
                if mode == 'rename-out':
                    (workspace / 'src/value.txt').rename(workspace / 'forbidden rename.txt')
                if mode == 'delete':
                    (workspace / 'host.txt').unlink()
                files = {'src/value.txt': 'worker\n'}
                if mode == 'prefix':
                    files['src-other/sentinel.txt'] = 'forbidden\n'
                if mode == 'leading-space':
                    files[' private.txt'] = 'forbidden\n'
                self.submit(a, self.commit(a, files))
                self.reject_verify('path_boundary_failed')

    def test_linked_and_unchecked_branch_and_nonconflicting_dirty_changes(self):
        for index, mode in enumerate(('linked', 'unchecked', 'dirty')):
            with self.subTest(mode=mode):
                if index:
                    self.setUp()
                if mode in ('linked', 'unchecked'):
                    self.git('switch', '--detach', self.base)
                target = self.repo
                if mode == 'linked':
                    target = self.root / 'linked main'
                    self.git('worktree', 'add', str(target), 'main')
                self.git('update-ref', 'refs/a2a/integration', self.base)
                a = self.create_managed()
                c = self.commit(a)
                self.submit(a, c)
                self.cli('verify')
                if mode == 'dirty':
                    (target / 'host.txt').write_text('User staged and unstaged\n', encoding='utf-8')
                    self.git('add', 'host.txt')
                    (target / 'host.txt').write_text('User unstaged after staging\n', encoding='utf-8')
                    (target / 'local.txt').write_text('untracked\n', encoding='utf-8')
                    staged = self.git('show', ':host.txt')
                self.cli('integrate')
                self.assertEqual(self.oid(ref='refs/heads/main'), c)
                self.assertEqual(self.oid(ref='refs/a2a/integration'), self.base)
                if mode != 'unchecked':
                    self.assertEqual(self.oid(target), c)
                    self.assertEqual((target / 'src/value.txt').read_text(), 'worker\n')
                if mode != 'dirty':
                    self.assertEqual((self.repo / 'src/value.txt').read_text(), 'base\n')
                else:
                    self.assertEqual(self.git('show', ':host.txt'), staged)
                    self.assertEqual((target / 'host.txt').read_text(), 'User unstaged after staging\n')
                    self.assertEqual((target / 'local.txt').read_text(), 'untracked\n')

    def test_malformed_and_old_identity_trailers_rejected(self):
        for index, mode in enumerate(('old-attempt', 'reviewer', 'partial', 'duplicate')):
            with self.subTest(mode=mode):
                if index:
                    self.setUp()
                a = self.create()
                self.commit(a)
                workspace = Path(a['workspace'])
                message = self.git('show', '-s', '--format=%B', 'HEAD', cwd=workspace)
                expected = 'trailer_identity_mismatch'
                if mode == 'old-attempt':
                    message = message.replace('A2A-Attempt: ' + a['attempt_id'], 'A2A-Attempt: old-attempt')
                elif mode == 'reviewer':
                    message = message.replace('A2A-Role: worker', 'A2A-Role: reviewer')
                elif mode == 'partial':
                    message = message.replace('A2A-Effort: xhigh\n', '')
                    expected = 'invalid_trailers'
                else:
                    message += '\nA2A-Session: ' + a['session_id']
                    expected = 'invalid_trailers'
                self.git('commit', '--amend', '-m', message, cwd=workspace)
                self.submit(a, self.oid(workspace))
                self.reject_verify(expected)

    def test_missing_trailer_reverification_deduplicates_action(self):
        a = self.create_managed()
        c = self.commit(a, trailers=False)
        self.submit(a, c)
        first = self.cli('verify')['verification']
        inputs = self.cli('status')['user_inputs']
        (self.repo / 'host.txt').write_text('new G\n', encoding='utf-8')
        self.git('add', 'host.txt')
        self.git('commit', '-m', 'External change requires new verification')
        g = self.oid()
        self.cli('integrate')
        v = self.cli('status')['task']['verification']
        self.assertNotEqual(v['verification_id'], first['verification_id'])
        self.assertEqual(v['C'], c)
        self.assertEqual(v['G'], g)
        self.assertEqual((self.repo / 'host.txt').read_text(), 'new G\n')
        self.assertEqual(self.cli('status')['user_inputs'], inputs)
        self.assertEqual(len([e for e in self.events() if e['type'] == 'human_intervention']), 1)
        self.cli('integrate')
        self.assertEqual(self.oid(), v['M'])
        self.assertEqual(len([e for e in self.events() if e['type'] == 'completion_check']), 2)

    def test_ticket_revision_and_template_source(self):
        self.task = 'T-990-1'
        self.card['id'] = self.task
        ticket = self.root / 'T-990.md'
        ticket.write_text('---\nid: T-990\nready: yes\nready_rev: 2\n---\n', encoding='utf-8')
        template = self.cli('card_template', '--repo', self.repo, '--ticket', ticket)['card']
        self.assertEqual(template['id'], 'T-990-1')
        self.assertEqual(template['source'], {'ticket': str(ticket.resolve()), 'ready_rev': 2})
        self.card['source'] = {'ticket': str(ticket), 'ready_rev': 1}
        self.card_file.write_text(json.dumps(self.card), encoding='utf-8')
        result = self.cli('card_save', '--card', self.card_file, '--expected-version', '0', ok=False, error='invalid_task_card')
        self.assertEqual(result['details']['field'], 'source.ready_rev')
        self.card['source']['ready_rev'] = 2
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1')
        ticket.write_text('---\nid: T-990\nready: yes\nready_rev: 3\n---\n', encoding='utf-8')
        a = self.dispatch_candidate_attempt()
        self.assertEqual(self.cli('status')['task']['card']['source']['ready_rev'], 2)
        self.submit(a, self.commit(a))
        self.cli('verify')
        self.cli('integrate')

    def test_non_fast_forward_git_result_cannot_integrate(self):
        self.card['paths'] = {'allow': ['.'], 'deny': []}
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-c', 'pass']}]
        a = self.create_managed()
        c = self.commit(a)
        (self.repo / 'host.txt').write_text('G contains external content\n', encoding='utf-8')
        self.git('add', 'host.txt')
        self.git('commit', '-m', 'Independent G')
        g = self.oid()
        self.submit(a, c)
        wrapper_dir = self.root / 'wrapped-git'
        wrapper_dir.mkdir()
        real = shutil.which('git')
        fault = self.root / 'git-fault.json'
        code = ('#!' + sys.executable + '\nimport json,os,subprocess,sys\n'
                'real=' + repr(real) + '\nargs=sys.argv[1:]\n'
                'if "commit-tree" not in args:\n os.execv(real,[real]+args)\n'
                'p=subprocess.run([real]+args,text=True,capture_output=True)\n'
                'with open(' + repr(str(fault)) + ',"x") as out:\n'
                ' json.dump({"argv":[real]+args,"exit":p.returncode,"actual_stdout":p.stdout,"fault_stdout":'
                + repr(self.base) + '},out)\n'
                'sys.stderr.write(p.stderr)\n'
                'sys.stdout.write(' + repr(self.base + '\n') + ' if p.returncode==0 else p.stdout)\n'
                'sys.exit(p.returncode)\n')
        wrapper = wrapper_dir / 'git'
        wrapper.write_text(code, encoding='utf-8')
        wrapper.chmod(0o755)
        self.env['PATH'] = str(wrapper_dir) + os.pathsep + self.env['PATH']
        v = self.cli('verify')['verification']
        self.assertEqual(v['M'], self.base)
        self.assertNotEqual(json.loads(fault.read_text())['actual_stdout'].strip(), self.base)
        self.cli('integrate', ok=False, error='integration_not_fast_forward')
        self.assertEqual(self.oid(), g)


def main():
    global GATE, OUT, ARTIFACT_ROOT
    p = argparse.ArgumentParser()
    p.add_argument('--gate', type=Path, default=GATE)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--case', action='append')
    args = p.parse_args()
    GATE = args.gate.resolve()
    OUT = args.output.resolve()
    OUT.mkdir(exist_ok=False)
    ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='a2a-card2-e2e-', dir='/tmp'))
    names = args.case or unittest.defaultTestLoader.getTestCaseNames(TaskCardsCLI)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(TaskCardsCLI(name) for name in names))
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'command': sys.argv,
              'gate': str(GATE), 'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped), 'commands': COMMANDS,
              'artifacts': ARTIFACTS, 'artifact_root': str(ARTIFACT_ROOT),
              'failure_text': [text for _, text in result.failures], 'error_text': [text for _, text in result.errors]}
    with (OUT / 'run.json').open('x', encoding='utf-8') as out:
        json.dump(record, out, ensure_ascii=False, indent=2)
        out.write('\n')
    with tarfile.open(OUT / 'artifacts.tar.gz', 'w:gz') as out:
        out.add(ARTIFACT_ROOT, arcname=ARTIFACT_ROOT.name)
    print(json.dumps({k: record[k] for k in ('status', 'tests_run', 'failures', 'errors', 'artifact_root')}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
