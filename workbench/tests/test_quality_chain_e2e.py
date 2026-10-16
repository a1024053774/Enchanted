"""T-076-2 contract evidence through the real CLI and daemon.

Expected answers come from T-076/spec and controller decision 01. Only typed
ContractFailure instances count as business red; setup/usage/IO failures do not.
The controlled host replaces PTY/process observations, never a gate result.
"""
import argparse
from contextlib import closing
import datetime
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback

import test_task_cards_e2e as base

SOURCE = None
OUT = None
DIALECT = 'legacy'


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


class ContractFailure(AssertionError):
    pass


class HarnessFailure(RuntimeError):
    pass


class QualityCase(base.TaskCardsCLI):
    def __init__(self, case):
        super().__init__('runTest')
        self.case = case
        self.assertions = []
        self.commands = []
        self.host = None
        self.host_generation = 0
        self.run_child = None
        self.streams = []

    def id(self):
        return 'T-076-2.' + self.case

    def check(self, name, condition, expected, actual):
        row = {'id': name, 'passed': bool(condition), 'expected': expected, 'actual': actual}
        self.assertions.append(row)
        if not condition:
            raise ContractFailure(name)

    def process(self, argv, cwd=None, *, env=None, stdin=None):
        argv = list(map(str, argv))
        directory = getattr(self, 'evidence', OUT / self.case)
        directory.mkdir(exist_ok=True)
        number = len(self.commands) + 1
        prefix = directory / ('command-%04d' % number)
        record = {'id': number, 'argv': argv, 'cwd': str(cwd or self.root),
                  'stdout': str(prefix.with_suffix('.stdout.bin')),
                  'stderr': str(prefix.with_suffix('.stderr.bin'))}
        if stdin is not None:
            path = prefix.with_suffix('.stdin.json')
            with path.open('x', encoding='utf-8') as stream:
                stream.write(stdin)
            record['stdin'] = str(path)
        self.commands.append(record)
        with (directory / 'commands.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'phase': 'started', **record}) + '\n')
        try:
            with Path(record['stdout']).open('xb') as out, Path(record['stderr']).open('xb') as err:
                p = subprocess.run(argv, cwd=cwd or self.root, env=env or self.env,
                                   input=stdin.encode('utf-8') if stdin is not None else None,
                                   stdout=out, stderr=err, timeout=45)
            record['exit'] = p.returncode
            p.stdout = Path(record['stdout']).read_text(encoding='utf-8')
            p.stderr = Path(record['stderr']).read_text(encoding='utf-8')
            base.COMMANDS.append({'test': self.id(), 'argv': argv, 'cwd': record['cwd'],
                                  'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
            return p
        except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
            record['error'] = repr(error)
            raise HarnessFailure(str(error)) from error
        finally:
            with (directory / 'commands.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'phase': 'finished', **record}) + '\n')

    def setUp(self):
        self.evidence = OUT / self.case
        self.evidence.mkdir()
        super().setUp()
        for key in list(self.env):
            if key.startswith(('CODEX_', 'ELECTRON_')):
                del self.env[key]
        self.card['executor'] = {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}
        self.card['paths']['allow'].extend(['tests/', '.a2a/quality.json'])
        self.control = self.root / 'control'
        self.control.mkdir()
        home = self.control / 'empty-codex-home'
        home.mkdir()
        executable = self.control / 'fixture-version'
        executable.write_text('#!/bin/sh\n[ "$#" = 1 ] && [ "$1" = --version ] || exit 93\nprintf "codex-cli 0.162.1\\n"\n', encoding='utf-8')
        executable.chmod(0o755)
        role = self.control / 'role.txt'
        role.write_text('Controlled test input. No model executes this role.\n', encoding='utf-8')
        reviewers = []
        for index in range(3):
            reviewer_home = self.control / ('reviewer-home-%d' % index)
            reviewer_home.mkdir()
            reviewers.append({'codex_home': str(reviewer_home), 'role_card': str(role),
                              'role_card_revision': 'controlled-reviewer', 'hook_authorization': 'no-real-hooks-installed'})
        save(self.control / 'process-facts.json', {})
        config = {'codex_bin': str(executable), 'codex_home': str(home),
             'role_card': str(role), 'role_card_revision': 'test-fixture-not-a-provider',
             'code_revision': 'frozen-source-manifest', 'hook_authorization': 'no-real-hooks-installed',
             'turn_limit': 10, 'turn_authorization': 'controlled-turns-only', 'reviewers': reviewers}
        self.configure_host(config)
        save(self.control / 'config.json', config)
        self.start_host()
        save(self.evidence / 'fixture.json', {'root': str(self.root), 'source': str(SOURCE),
             'initial_fixture_commit': self.base, 'host': self.ready, 'card_dialect': DIALECT,
             'real_codex_turns': 0, 'native_records_are_synthetic': True})

    def configure_host(self, config):
        """Subclasses may configure their isolated external fault boundary."""

    def start_host(self):
        if self.host is not None and self.host.poll() is None:
            raise HarnessFailure('The fixture already owns a live host.')
        self.host_generation += 1
        prefix = 'host-%02d' % self.host_generation
        ready = self.root / (prefix + '.ready.json')
        stdout = (self.evidence / (prefix + '.stdout.bin')).open('xb')
        stderr = (self.evidence / (prefix + '.stderr.bin')).open('xb')
        self.streams.extend([stdout, stderr])
        argv = ['node', Path(__file__).with_name('quality_chain_host.ts'), SOURCE, self.state, self.control, ready]
        save(self.evidence / (prefix + '.start.json'), {'argv': list(map(str, argv)), 'cwd': str(self.root),
             'start_new_session': True, 'real_codex_turns': 0})
        self.host = subprocess.Popen(list(map(str, argv)), cwd=self.root, env=self.env,
                                     stdout=stdout, stderr=stderr, start_new_session=True)
        deadline = time.monotonic() + 10
        while not ready.exists():
            if self.host.poll() is not None or time.monotonic() >= deadline:
                raise HarnessFailure('Controlled host startup failed; inspect host stderr.')
            time.sleep(0.02)
        self.ready = json.loads(ready.read_text(encoding='utf-8'))
        if self.ready['pid'] != self.host.pid or self.ready['root'] != str(self.state):
            raise HarnessFailure('Host readiness identity mismatch.')
        info = self.gate('daemon_status', task=False)
        if info.get('pid') != self.host.pid:
            raise HarnessFailure('CLI and owned host PID disagree.')
        observed = self.process(['/bin/ps', '-p', str(self.host.pid), '-o', 'pid=,ppid=,pgid=,command='])
        group = {'pid': self.host.pid, 'pgid': os.getpgid(self.host.pid), 'sid': os.getsid(self.host.pid),
                 'caller_pgid': os.getpgrp(), 'ps_exit': observed.returncode, 'ps_stdout': observed.stdout}
        save(self.evidence / (prefix + '.process.json'), group)
        if observed.returncode or not (group['pid'] == group['pgid'] == group['sid']) or group['caller_pgid'] == group['pgid']:
            raise HarnessFailure('Owned daemon is not detached from the invoking process group.')

    def gate(self, command, *args, task=True, env=None, stdin=None):
        argv = ['node', base.GATE, '--state', self.state, command]
        if task:
            argv.extend(['--task', self.task])
        p = self.process([*argv, *args], env=env, stdin=stdin)
        if p.returncode not in (0, 1):
            raise HarnessFailure('CLI usage or process failure is not business evidence: ' + str(argv))
        try:
            value = json.loads(p.stdout)
        except ValueError as error:
            raise HarnessFailure('CLI did not return a JSON result.') from error
        # The product CLI deliberately returns {} to a successful native hook.
        # Keep the raw output above; this is an established wire shape, not a
        # substitute verdict for submit/verify/integrate or a failed hook.
        if command == 'signal' and p.returncode == 0 and value == {}:
            return {'ok': True, 'hook_stdout': value}
        if not isinstance(value, dict) or value.get('ok') is not (p.returncode == 0):
            raise HarnessFailure('CLI exit and result disagree.')
        if value.get('error') in ('daemon_call_failed', 'orchestration_failed', 'gate_failure'):
            raise HarnessFailure('Unexpected infrastructure failure: ' + json.dumps(value))
        return value

    def registered(self):
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main',
                 '--card-version', '1', '--project', 'fixture')

    def commit(self, attempt, files=None, trailers=True, foreign=None):
        if not attempt['thread_id']:
            return super().commit(attempt, files, trailers, foreign)
        workspace = Path(attempt['workspace'])
        for name, value in (files or {'src/value.txt': 'worker\n'}).items():
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value, encoding='utf-8')
        message = 'Controlled worker fixture commit'
        if trailers:
            values = {'Task': foreign or self.task, 'Attempt': attempt['attempt_id'], 'Session': attempt['session_id'],
                      'Role': 'worker', 'Tool': 'codex-cli 0.162.1', 'Model': 'gpt-6.1-sol', 'Effort': 'xhigh',
                      'Native-Session': self.native['native'], 'Launch': self.launch}
            message += '\n\n' + '\n'.join('A2A-' + key + ': ' + value for key, value in values.items())
        self.git('add', '.', cwd=workspace)
        self.git('commit', '-m', message, cwd=workspace)
        return self.oid(workspace)

    def start_worker(self):
        self.registered()
        a = self.cli('dispatch', '--runtime-mode', 'workspace-write')['attempt']
        self.release_worker(a)
        return a

    def release_worker(self, a):
        self.a = a
        launch = self.gate('pane_status', '--thread', a['thread_id'], task=False)['launch']
        self.launch = launch
        self.native = json.loads((self.control / (launch + '.json')).read_text(encoding='utf-8'))
        value = self.gate('pane_release', '--thread', a['thread_id'], '--reason', 'explicit controlled-fixture release', task=False)
        if not value['ok']:
            raise HarnessFailure('Controlled initial release failed.')
        self.wait_pane(lambda p: p['state'] == 'busy' and p['turn'] == 'fixture-turn-1')

    def wait_pane(self, predicate):
        deadline = time.monotonic() + 5
        while True:
            p = self.gate('pane_status', '--thread', self.a['thread_id'], task=False)
            if predicate(p):
                return p
            if time.monotonic() >= deadline:
                raise HarnessFailure('Controlled pane did not reach its expected boundary: ' + json.dumps(p))
            time.sleep(0.03)

    def worker_env(self):
        return {**self.env, **self.native['env']}

    def stop_turn(self, *, turn=None):
        pane = self.gate('pane_status', '--thread', self.a['thread_id'], task=False)
        raw = {'session_id': self.native['native'], 'turn_id': turn or pane['turn'],
               'hook_event_name': 'Stop', 'last_assistant_message': 'controlled worker finished'}
        return self.gate('signal', '--launch', self.launch, task=False,
                         env=self.worker_env(), stdin=json.dumps(raw))

    def worker_submit(self, commit, request_id='delivery-1', settle=True):
        a = self.a
        before = self.gate('pane_status', '--thread', a['thread_id'], task=False)
        ack_turn = 'fixture-turn-' + str(int(before['turn'].removeprefix('fixture-turn-')) + 1)
        result = self.gate('submit', '--attempt', a['attempt_id'], '--session', a['session_id'],
                           '--fence', str(a['fence']), '--spec-rev', str(a['spec_rev']),
                           '--commit', commit, '--request-id', request_id, env=self.worker_env())
        if not result.get('queued'):
            raise HarnessFailure('Worker request did not queue through the real CLI.')
        self.stop_turn()
        if settle:
            ack = self.wait_pane(lambda p: p['state'] == 'busy' and p['turn'] == ack_turn)
            stopped = self.stop_turn(turn=ack_turn)
            # The daemon can drain a queued repair as soon as ACK Stop returns.
            # Its durable end event proves the boundary even after turn-3 starts.
            ended = [event for event in self.orchestration()
                     if event['type'] == 'pane_idle' and event['launch'] == self.launch
                     and event['attempt'] == a['attempt_id'] and event['task'] == self.task
                     and event['data'].get('submission') == ack['active']['id']
                     and event['data'].get('stop', {}).get('session_id') == self.native['native']
                     and event['data'].get('stop', {}).get('turn_id') == ack_turn]
            save(self.evidence / ('submit-ack-%04d.json' % len(self.commands)), {
                'request_id': request_id, 'ack': ack, 'stop_reply': stopped, 'matched_end_events': ended})
            if not stopped['ok'] or len(ended) != 1:
                raise HarnessFailure('未读回绑定本次 ACK 身份的唯一结束事件。')
        return self.relay_result(request_id)

    def relay_result(self, request_id):
        with closing(sqlite3.connect((self.state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            row = db.execute('SELECT r.data FROM relay_results r JOIN relay_requests q ON q.key=r.key '
                             'WHERE q.launch=? AND q.request_id=?', (self.launch, request_id)).fetchone()
        if row is None:
            raise HarnessFailure('No durable relay result for the controlled request.')
        return json.loads(row[0])

    def orchestration(self):
        return self.gate('orchestration_events', '--task', self.task, task=False)['events']

    def gate_messages(self):
        with closing(sqlite3.connect((self.state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            return [{'seq': row[0], 'id': row[1], 'launch': row[2], 'data': json.loads(row[3])}
                    for row in db.execute('SELECT seq,id,launch,data FROM dispatch_records ORDER BY seq')
                    if json.loads(row[3]).get('source') == 'gate']

    def red_command(self, code):
        argv = [sys.executable, '-I', '-B', 'tests/red.py']
        item = {'argv': argv}
        if DIALECT == 'current':
            item['test_paths'] = ['tests/red.py']
        self.card['red_commands'] = [item]
        self.red_source = code

    def write_rule_config(self, code):
        target = self.repo / '.a2a/quality.json'
        target.parent.mkdir()
        value = {'schema': 1, 'rule_checks': [{'id': 'independent-rule',
                  'argv': [sys.executable, '-I', '-B', '-c', code]}]}
        target.write_text(json.dumps(value) + '\n', encoding='utf-8')
        self.git('add', '.a2a/quality.json')
        self.git('commit', '-m', 'Freeze independently supplied project rule')
        self.base = self.oid()

    def manual_candidate(self, files=None, trailers=True):
        a = self.create()
        c = self.commit(a, files, trailers=trailers)
        self.submit(a, c)
        return a, c

    def verify_must_refuse(self, name):
        before = self.oid(ref='refs/heads/main')
        reply = self.gate('verify')
        self.check(name, not reply['ok'], 'quality verification refuses this independently invalid candidate', reply)
        self.check(name + '.no-integration', self.oid(ref='refs/heads/main') == before, before, self.oid())
        rejected = [e for e in self.events() if e['type'] == 'rejected']
        self.check(name + '.event', bool(rejected), 'durable gate rejection event', rejected)

    def red_manifest_missing(self):
        self.card['red_commands'] = [{'argv': [sys.executable, '-c', 'raise AssertionError("baseline")']}]
        self.card_file.write_text(json.dumps(self.card), encoding='utf-8')
        reply = self.gate('card_validate', '--card', self.card_file)
        self.check('RED-MANIFEST', not reply['ok'], 'nonempty red command requires explicit test_paths', reply)

    def red_base_not_failing(self):
        self.red_command('print("this test incorrectly passes on both revisions")\n')
        a, _ = self.manual_candidate({'src/value.txt': 'worker\n', 'tests/red.py': self.red_source})
        probe = self.root / 'base-with-tests'
        self.git('worktree', 'add', '--detach', str(probe), a['base_commit'])
        (probe / 'tests').mkdir()
        (probe / 'tests/red.py').write_text(self.red_source, encoding='utf-8')
        for directory in (probe, Path(a['workspace'])):
            result = self.process([sys.executable, '-I', '-B', 'tests/red.py'], cwd=directory)
            if result.returncode != 0:
                raise HarnessFailure('Independent baseline/candidate setup did not both pass.')
        self.verify_must_refuse('RED-BASE-PASSES')

    def red_candidate_fails(self):
        self.red_command('from pathlib import Path\nassert Path("src/value.txt").read_text() == "unattained\\n", "independent business assertion"\n')
        a, _ = self.manual_candidate({'src/value.txt': 'worker\n', 'tests/red.py': self.red_source})
        check = self.process([sys.executable, '-I', '-B', 'tests/red.py'], cwd=Path(a['workspace']))
        if check.returncode != 1:
            raise HarnessFailure('Independent red test did not fail on its explicit assertion.')
        self.verify_must_refuse('RED-CANDIDATE-FAILS')

    def red_rules_failing(self):
        self.write_rule_config('raise AssertionError("independent project rule")')
        self.manual_candidate()
        self.verify_must_refuse('RED-RULES')

    def red_rules_frozen(self):
        self.write_rule_config('raise AssertionError("registered project rule cannot be erased by candidate")')
        self.manual_candidate({'src/value.txt': 'worker\n', '.a2a/quality.json': '{"schema":1,"rule_checks":[]}\n'})
        self.verify_must_refuse('RED-RULES-FROZEN')

    def rejected_worker(self):
        a = self.start_worker()
        c = self.commit(a, {'src/value.txt': 'not-the-required-result\n'})
        reply = self.worker_submit(c)
        if not reply['ok']:
            raise HarnessFailure('Valid controlled worker submission failed: ' + json.dumps(reply))
        before = self.gate_messages()
        result = self.gate('verify', '--attempt', a['attempt_id'])
        if result.get('error') != 'oracle_failed':
            raise HarnessFailure('Expected completion oracle did not reject the fixture.')
        return a, c, before

    def red_feedback_idle(self):
        a, c, before = self.rejected_worker()
        messages = self.gate_messages()[len(before):]
        self.check('RED-FEEDBACK', len(messages) == 1 and messages[0]['launch'] == self.launch,
                   'one registered gate repair message for the original worker launch', messages)
        current_attempt = self.cli('status')['task']['current_attempt']
        self.check('RED-FEEDBACK.identity', isinstance(current_attempt, dict) and current_attempt['attempt_id'] == a['attempt_id'],
                   a['attempt_id'], current_attempt)
        self.check('RED-FEEDBACK.ref', self.oid() == self.base, self.base, self.oid())

    def red_repair_resubmit(self):
        a, c, _ = self.rejected_worker()
        # The actor is supplied by this fixture, not inferred from screen text.
        # If product feedback is missing, explicitly supply an executor message
        # so this case isolates authorization to replace rejected C and turn.
        pane = self.gate('pane_status', '--thread', a['thread_id'], task=False)
        if pane['state'] == 'idle':
            body = self.root / 'repair.txt'
            body.write_text('Controlled actor repairs after the recorded oracle failure.\n', encoding='utf-8')
            self.gate('pane_dispatch', '--thread', a['thread_id'], '--body-file', body, task=False)
        self.wait_pane(lambda p: p['state'] == 'busy' and p['turn'] == 'fixture-turn-3')
        c2 = self.commit(a)
        result = self.worker_submit(c2, request_id='delivery-2', settle=False)
        self.check('RED-RESUBMIT', result['ok'], 'same native owner may explicitly resubmit C2 after recorded rejection', result)
        current = self.cli('status')['task']
        current_attempt = current['current_attempt']
        self.check('RED-RESUBMIT.binding', current['candidate_commit'] == c2 and isinstance(current_attempt, dict)
                   and current_attempt['attempt_id'] == a['attempt_id'],
                   {'attempt': a['attempt_id'], 'C2': c2}, current)

    def red_review_required(self):
        # Claim has no launch record. Trailers stop at the trailer check, so this review case omits them.
        self.manual_candidate(trailers=False)
        # The baseline reaches mechanical success. A candidate with this new
        # interface may pause while creating a reviewer; neither path may
        # report verified before an independent verdict.
        reply = self.gate('verify')
        current = self.cli('status')['task']
        launches = self.rows('launch_records')
        self.check('RED-REVIEW', current['state'] != 'verified' and any(json.loads(r['data']).get('role') == 'reviewer' for r in launches),
                   'mechanical completion requests a fresh reviewer and is not yet verified',
                   {'reply': reply, 'state': current['state'], 'launches': launches})

    def red_terminal_prerequisites(self):
        # Claim has no launch record. Trailers stop at the trailer check, so this integrate case omits them.
        self.manual_candidate(trailers=False)
        self.cli('verify')
        before = self.oid()
        reply = self.gate('integrate')
        self.check('RED-FINAL-PREREQUISITES', not reply['ok'] and self.oid() == before,
                   'no review and no executor score: refuse integration without Git write', {'reply': reply, 'ref': self.oid(), 'before': before})

    def start_run(self, wait_seconds=8):
        self.registered()
        argv = ['node', base.GATE, '--state', self.state, 'run', '--task', self.task,
                '--runtime-mode', 'workspace-write', '--wait-seconds', str(wait_seconds)]
        out = (self.evidence / 'run.stdout.bin').open('xb')
        err = (self.evidence / 'run.stderr.bin').open('xb')
        self.streams.extend([out, err])
        save(self.evidence / 'run-start.json', {'argv': list(map(str, argv)), 'cwd': str(self.root),
             'start_new_session': True, 'real_codex_turns': 0})
        self.run_child = subprocess.Popen(list(map(str, argv)), cwd=self.root, env=self.env,
                                          stdout=out, stderr=err, start_new_session=True)
        end = time.monotonic() + 6
        while True:
            current = self.cli('status')['task']
            if current['state'] == 'claimed':
                self.release_worker(current['current_attempt'])
                return current['current_attempt']
            if self.run_child.poll() is not None or time.monotonic() >= end:
                raise HarnessFailure('Run did not reach its original claimed attempt.')
            time.sleep(0.03)

    def finish_run(self):
        try:
            self.run_child.wait(timeout=20)
        except subprocess.TimeoutExpired as error:
            raise HarnessFailure('Run ignored its explicit finite deadline.') from error
        value = json.loads((self.evidence / 'run.stdout.bin').read_text(encoding='utf-8'))
        save(self.evidence / 'run-result.json', {'exit': self.run_child.returncode, 'reply': value})
        return value

    def red_run_reject_preserves_worker(self):
        a = self.start_run()
        c = self.commit(a, {'src/value.txt': 'not-the-required-result\n'})
        result = self.worker_submit(c)
        if not result['ok']:
            raise HarnessFailure('Controlled run submit failed.')
        reply = self.finish_run()
        current = self.cli('status')['task']
        current_attempt = current['current_attempt']
        reference = self.oid()
        history = [json.loads(row['data']) for row in self.rows('attempts') if row['id'] == a['attempt_id']]
        actual = {'reply': reply, 'current': current, 'ref': reference,
                  'expected_attempt_id': a['attempt_id'], 'original_attempt_history': history}
        save(self.evidence / 'run-repair-readback.json', actual)
        self.check('RED-RUN-REPAIR', isinstance(current_attempt, dict)
                   and current_attempt['attempt_id'] == a['attempt_id']
                   and current_attempt['reclaimed'] is False and reference == self.base,
                   'rejected delivery retains its worker for repair and never integrates', actual)

    def red_run_waits_for_executor(self):
        a = self.start_run()
        c = self.commit(a)
        result = self.worker_submit(c)
        if not result['ok']:
            raise HarnessFailure('Controlled run submit failed.')
        reply = self.finish_run()
        self.check('RED-RUN-FINALIZE', self.oid() == self.base and self.cli('status')['task']['state'] != 'accepted',
                   'run cannot finalize without reviewer and explicit executor score', {'reply': reply, 'ref': self.oid()})

    def control_completion(self):
        self.manual_candidate({'src/value.txt': 'bad\n'})
        self.verify_must_refuse('CONTROL-COMPLETION')

    def control_paths(self):
        self.manual_candidate({'src/value.txt': 'worker\n', 'src/private/secret.txt': 'forbidden\n'})
        self.verify_must_refuse('CONTROL-PATH')

    def control_frozen_candidate(self):
        a, c = self.manual_candidate()
        c2 = self.commit(a, {'src/value.txt': 'bad-later-candidate\n'})
        reply = self.gate('submit', '--attempt', a['attempt_id'], '--session', a['session_id'],
                          '--fence', str(a['fence']), '--spec-rev', str(a['spec_rev']), '--commit', c2)
        self.check('CONTROL-FROZEN', not reply['ok'] and self.cli('status')['task']['candidate_commit'] == c,
                   'without a rejection the frozen C cannot be replaced', reply)

    def control_fence(self):
        a = self.create()
        c = self.commit(a)
        reply = self.gate('submit', '--attempt', a['attempt_id'], '--session', a['session_id'],
                          '--fence', str(a['fence'] + 1), '--spec-rev', str(a['spec_rev']), '--commit', c)
        self.check('CONTROL-FENCE', not reply['ok'] and self.cli('status')['task']['candidate_commit'] is None,
                   'wrong fence has no submission effect', reply)
        self.check('CONTROL-FENCE.event', any(e['type'] == 'rejected' and e['details'].get('error') == 'stale_fence' for e in self.events()),
                   'stale_fence refusal event', self.events())

    def control_stop_without_request(self):
        a = self.start_worker()
        self.commit(a)
        self.stop_turn()
        current = self.cli('status')['task']
        self.check('CONTROL-EXPLICIT', current['state'] == 'claimed' and current['candidate_commit'] is None,
                   'Stop alone does not submit a committed candidate', current)

    def control_relay_invalid(self):
        a = self.start_worker()
        c = self.commit(a)
        request = {'schema': 1, 'command': 'submit', 'task': self.task, 'attempt': a['attempt_id'],
                   'session': a['session_id'], 'fence': a['fence'], 'spec_rev': a['spec_rev'], 'commit': c}
        directory = Path(self.native['env']['A2A_REQUEST_DIR'])
        wrong = {**request, 'request_id': 'wrong-session', 'session': 'another-session'}
        incomplete = {**request, 'request_id': 'missing-commit'}
        del incomplete['commit']
        save(directory / 'wrong-session.json', wrong)
        save(directory / 'missing-commit.json', incomplete)
        self.stop_turn()
        actual = {key: self.relay_result(key) for key in ('wrong-session', 'missing-commit')}
        self.check('CONTROL-RELAY-INVALID', actual['wrong-session'].get('error') == 'relay_identity_mismatch'
                   and actual['missing-commit'].get('error') == 'invalid_relay_request',
                   'wrong identity and incomplete request rejected by real relay', actual)
        self.check('CONTROL-RELAY-INVALID.no-submit', self.cli('status')['task']['candidate_commit'] is None,
                   'neither invalid request reaches submit', self.cli('status')['task'])

    def control_relay_duplicate(self):
        a = self.start_worker()
        c = self.commit(a)
        result = self.worker_submit(c)
        if not result['ok']:
            raise HarnessFailure('Valid relay control failed before duplicate observation.')
        events = self.events()
        submissions = [e for e in events if e['type'] == 'submitted']
        replayed = [e for e in self.orchestration() if e['type'] == 'relay_replayed']
        self.check('CONTROL-RELAY-ONCE', len(submissions) == 1 and bool(replayed),
                   'original request executed once; same file on ACK Stop is a recorded replay',
                   {'submissions': submissions, 'replayed': replayed})

    def control_busy_queue(self):
        a = self.start_worker()
        body = self.root / 'queued.txt'
        body.write_text('Second controlled executor input.\n', encoding='utf-8')
        before = self.read_lines(self.control / 'writes.jsonl')
        result = self.gate('pane_dispatch', '--thread', a['thread_id'], '--body-file', body, task=False)
        after = self.read_lines(self.control / 'writes.jsonl')
        pane = self.gate('pane_status', '--thread', a['thread_id'], task=False)
        self.check('CONTROL-BUSY-QUEUE', result['ok'] and before == after and len(pane['queued']) == 1,
                   'busy pane registers/queues without writing PTY bytes', {'pane': pane, 'writes_before': len(before), 'writes_after': len(after)})
        self.stop_turn()
        self.wait_pane(lambda p: p['state'] == 'busy' and p['turn'] == 'fixture-turn-2')
        writes = self.read_lines(self.control / 'writes.jsonl')
        paste, cr = writes[-2:]
        self.check('CONTROL-BUSY-ORDER', paste['data'].startswith('\x1b[200~⟦主控 #') and cr['data'] == '\r'
                   and len(paste['registered']) == 2 and len(cr['intents']) == 2,
                   'registered bracketed paste followed by CR with durable submit intent', writes[-2:])

    @staticmethod
    def read_lines(path):
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []

    def rows(self, table):
        with closing(sqlite3.connect((self.state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM "' + table + '"')]

    def close_fixture(self):
        failures = []
        if self.host is not None and self.host.poll() is None:
            try:
                database = self.state / 'state.sqlite3'
                if database.is_file():
                    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
                        db.row_factory = sqlite3.Row
                        db.execute('BEGIN')
                        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                        tables = {name: [dict(row) for row in db.execute('SELECT * FROM "' + name.replace('"', '""') + '"')] for name in names}
                        save(self.evidence / 'database-readback.json', {'phase': 'before-host-stop', 'tables': tables})
                save(self.evidence / 'git-readback.json', {'refs': self.git('show-ref'),
                     'worktrees': self.git('worktree', 'list', '--porcelain'),
                     'status': self.git('status', '--porcelain=v1', '--untracked-files=all')})
                request_copies = self.evidence / 'requests'
                for launch in self.rows('launch_records'):
                    record = json.loads(launch['data'])
                    source = Path(record['request_dir'])
                    if not source.is_dir() or not source.name.startswith('a2a-requests-') or source.parent != Path('/tmp').resolve():
                        raise HarnessFailure('Unexpected controlled launch request directory.')
                    destination = request_copies / record['id']
                    destination.mkdir(parents=True)
                    for request in source.iterdir():
                        if request.is_symlink() or not request.is_file():
                            raise HarnessFailure('Unexpected non-regular request evidence.')
                        with (destination / request.name).open('xb') as stream:
                            stream.write(request.read_bytes())
            except Exception as error:
                failures.append({'phase': 'capture', 'error': repr(error)})
            try:
                status = self.gate('daemon_status', task=False)
                if status.get('pid') != self.host.pid:
                    raise HarnessFailure('Refuse to stop a different daemon PID.')
                stopped = self.gate('daemon_stop', task=False)
                if not stopped['ok']:
                    raise HarnessFailure('Owned daemon_stop was refused.')
                self.host.wait(timeout=12)
                if self.host.returncode != 0:
                    raise HarnessFailure('Owned host shutdown returned nonzero.')
            except Exception as error:
                # Retain the owned process and its explicit PID for controller
                # handling. Do not kill an unconfirmed server or retry stop.
                failures.append({'phase': 'stop', 'error': repr(error), 'pid': self.host.pid})
        if self.run_child is not None:
            try:
                self.run_child.wait(timeout=5)
            except subprocess.TimeoutExpired as error:
                failures.append({'phase': 'run-exit', 'error': repr(error), 'pid': self.run_child.pid})
        for stream in self.streams:
            stream.close()
        save(self.evidence / 'cleanup.json', {'failures': failures,
             'host_exit': self.host.poll() if self.host else None, 'preserved_fixture': str(getattr(self, 'root', ''))})
        return failures


RED_CASES = {
    'red_manifest_missing': 'RED-MANIFEST',
    'red_base_not_failing': 'RED-BASE-PASSES',
    'red_candidate_fails': 'RED-CANDIDATE-FAILS',
    'red_rules_failing': 'RED-RULES',
    'red_rules_frozen': 'RED-RULES-FROZEN',
    'red_feedback_idle': 'RED-FEEDBACK',
    'red_repair_resubmit': 'RED-RESUBMIT',
    'red_review_required': 'RED-REVIEW',
    'red_terminal_prerequisites': 'RED-FINAL-PREREQUISITES',
    'red_run_reject_preserves_worker': 'RED-RUN-REPAIR',
    'red_run_waits_for_executor': 'RED-RUN-FINALIZE',
}
CONTROL_CASES = ['control_completion', 'control_paths', 'control_frozen_candidate', 'control_fence',
                 'control_stop_without_request', 'control_relay_invalid', 'control_relay_duplicate', 'control_busy_queue']


def run_cases(source, output, names, case_type=QualityCase, dialect='legacy', stop_on_failure=False):
    global SOURCE, OUT, DIALECT
    SOURCE, OUT, DIALECT = source.resolve(), output.resolve(), dialect
    OUT.mkdir(parents=True, exist_ok=False)
    base.GATE = SOURCE / 'workbench/src/gates/cli.ts'
    # New controlled runs can select the external fixture disk explicitly;
    # this setting belongs to the test process and is not passed to the gate.
    base.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='q76-', dir=os.environ.get('A2A_TEST_ARTIFACT_PARENT', '/tmp'))).resolve()
    records = []
    try:
        for name in names:
            case = case_type(name)
            row = {'case': name, 'outcome': 'harness_error', 'assertions': case.assertions}
            records.append(row)
            try:
                case.setUp()
                getattr(case, name)()
                row['outcome'] = 'passed'
            except ContractFailure as error:
                row.update(outcome='contract_failure', failure_id=str(error), traceback=traceback.format_exc())
            except Exception as error:
                row.update(error=repr(error), traceback=traceback.format_exc())
            finally:
                try:
                    row['cleanup_failures'] = case.close_fixture()
                except Exception as error:
                    row['cleanup_failures'] = [{'error': repr(error), 'traceback': traceback.format_exc()}]
                row.update(commands=case.commands, fixture=str(getattr(case, 'root', '')))
                save(OUT / name / 'case.json', row)
            print(json.dumps({'case': name, 'outcome': row['outcome'], 'failure_id': row.get('failure_id')}, ensure_ascii=False), flush=True)
            if row['outcome'] == 'harness_error' or row['cleanup_failures'] or stop_on_failure and row['outcome'] != 'passed':
                break
    finally:
        passed = len(records) == len(names) and all(r['outcome'] == 'passed' and not r['cleanup_failures'] for r in records)
        record = {'status': 'PASS' if passed else 'INCOMPLETE', 'command': sys.argv, 'source': str(SOURCE),
                  'real_codex_turns': 0, 'cases': records, 'planned_cases': names,
                  'evidence_layer': 'real CLI/daemon/relay/gates/Git/SQLite; controlled PTY/process/native inputs',
                  'artifact_root': str(base.ARTIFACT_ROOT), 'card_dialect': DIALECT}
        save(OUT / 'run.json', record)
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group', choices=['red', 'controls'], required=True)
    parser.add_argument('--case', choices=[*RED_CASES, *CONTROL_CASES], action='append')
    parser.add_argument('--card-dialect', choices=['legacy', 'current'], default='legacy')
    args = parser.parse_args()
    names = args.case or (list(RED_CASES) if args.group == 'red' else CONTROL_CASES)
    return run_cases(args.source, args.output, names, dialect=args.card_dialect)


if __name__ == '__main__':
    raise SystemExit(main())
