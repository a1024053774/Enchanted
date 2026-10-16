"""Explicit external reviewer/executor actions for approved legacy fixtures.

No product state is written. Every action goes through the real CLI/B relay.
The separate command log labels all runtime inputs as controlled fixture facts.
"""
import json
import os
from pathlib import Path
import subprocess
import time


def prepare_review_control(root, count=8):
    # Panes passes realpath(CODEX_HOME). Fix the fixture's configured spelling
    # before creation; keep the PTY boundary's exact home/shell checks intact.
    control = Path(root).resolve(strict=True) / 'quality-control'; control.mkdir()
    home = control / 'unused-worker-home'; home.mkdir()
    role = control / 'role.txt'; role.write_text('受控测试审查输入，无模型执行。\n', encoding='utf-8')
    executable = control / 'fixture-version'
    executable.write_text('#!/bin/sh\n[ "$#" = 1 ] && [ "$1" = --version ] || exit 93\nprintf "codex-cli 0.162.1\\n"\n', encoding='utf-8')
    executable.chmod(0o755)
    reviewers = []
    for index in range(count):
        target = control / ('review-home-%d' % index); target.mkdir()
        reviewers.append(dict(codex_home=str(target), role_card=str(role), role_card_revision='controlled-reviewer',
                              hook_authorization='no-real-hooks-installed'))
    config = dict(codex_bin=str(executable), codex_home=str(home), role_card=str(role),
                  role_card_revision='controlled-fixture', code_revision='frozen-source',
                  hook_authorization='no-real-hooks-installed', turn_limit=10,
                  turn_authorization='controlled-turns-only', reviewers=reviewers)
    (control / 'config.json').write_text(json.dumps(config) + '\n', encoding='utf-8')
    (control / 'process-facts.json').write_text('{}\n', encoding='utf-8')
    return control


class QualityDriver:
    def __init__(self, cli, state, control, env):
        self.cli, self.state, self.control, self.env = Path(cli), Path(state), Path(control), env
        self.scores = {}

    def record(self, phase, **data):
        with (self.control / 'driver.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(phase=phase, evidence_layer='controlled-external-actors', **data), ensure_ascii=False) + '\n')

    def command(self, command, *args, env=None, stdin=None, timeout=45):
        argv = list(map(str, ['node', self.cli, '--state', self.state, command, *args]))
        self.record('command-intent', argv=argv, stdin=stdin, timeout=timeout)
        p = subprocess.run(argv, cwd=self.control, env=env or self.env, input=stdin,
                           text=True, capture_output=True, timeout=timeout)
        self.record('command', argv=argv, exit=p.returncode, stdout=p.stdout, stderr=p.stderr, stdin=stdin)
        if p.returncode not in (0, 1): raise RuntimeError('Quality driver CLI failed outside the gate.')
        value = json.loads(p.stdout)
        if p.returncode or value.get('ok') is False: raise RuntimeError('Quality driver action rejected: ' + p.stdout)
        return value

    def preparation(self, task, attempt, kind):
        self.record('preparation', task=task, attempt=attempt['attempt_id'], preparation=kind,
                    thread=attempt['thread_id'], runtime_facts='fixture, not actual provider/model execution')

    def score_file(self, attempt):
        key = attempt['attempt_id']
        if key not in self.scores:
            path = self.control / ('score-' + key + '.json')
            data = dict(result='通过', boundary_discipline=3, boundary_reason='受控测试在合同边界内',
                        engineering_taste=2, engineering_reason='独立夹具固定评分', notes='')
            with path.open('x', encoding='utf-8') as stream: json.dump(data, stream, ensure_ascii=False)
            self.record('executor-score-prepared', attempt=key, path=str(path), data=data)
            self.scores[key] = path
        return self.scores[key]

    def complete_review(self, task, attempt=None, candidate=None):
        current = self.command('status', '--task', task)['task']
        if attempt and current['current_attempt']['attempt_id'] != attempt['attempt_id']:
            raise RuntimeError('Reviewer driver cannot adopt a replacement attempt.')
        if candidate and current['candidate_commit'] != candidate:
            raise RuntimeError('Reviewer driver candidate changed.')
        review = current.get('review')
        if current['state'] == 'verified' and review and review['state'] == 'passed':
            self.record('existing-reviewed-candidate', task=task, review_id=review['review_id'])
            return current
        if current['state'] != 'reviewing' or not review or review['state'] != 'running':
            raise RuntimeError('Expected a running independent reviewer: ' + json.dumps(current))
        record = json.loads((self.control / (review['launch_id'] + '.json')).read_text(encoding='utf-8'))
        if record['env']['A2A_ROLE'] != 'reviewer': raise RuntimeError('Reviewer role is not independent.')
        self.command('pane_release', '--thread', review['thread_id'], '--reason', 'explicit controlled reviewer release')
        deadline = time.monotonic() + 8
        while True:
            pane = self.command('pane_status', '--thread', review['thread_id'])
            if pane['state'] == 'busy' and pane['turn'] == 'fixture-turn-1': break
            if time.monotonic() >= deadline: raise RuntimeError('Reviewer input did not reach its bounded turn.')
            time.sleep(0.03)
        packet = dict(schema=1, request_id='review-' + review['review_id'], command='review_submit', task=task,
                      attempt=review['attempt']['attempt_id'], session=review['session_id'], fence=review['attempt']['fence'],
                      spec_rev=review['spec_rev'], review_id=review['review_id'], candidate_commit=review['candidate_commit'],
                      verdict='可合并', findings=[],
                      review_requirements={'completion_conditions_sufficiency': True,
                        'mutation_checks': {'min': 2, 'max': 5, 'workspace': review['candidate_workspace'],
                                            'report_section': '完成条件与变异检查'}},
                      report={'完成条件与变异检查': '受控 reviewer 报告输入；不声称模型判断已验证'})
        stop = dict(session_id=record['native'], turn_id=pane['turn'], hook_event_name='Stop',
                    last_assistant_message=json.dumps(packet, ensure_ascii=False))
        self.command('signal', '--launch', review['launch_id'], env={**self.env, **record['env']}, stdin=json.dumps(stop))
        while True:
            events = self.command('events', '--task', task)['events']
            if any(e['type'] == 'review_reclaimed' and e['details']['review_id'] == review['review_id'] for e in events): break
            if time.monotonic() >= deadline: raise RuntimeError('Reviewer result/reclaim did not complete.')
            time.sleep(0.03)
        current = self.command('status', '--task', task)['task']
        if current['state'] != 'verified' or current['review']['review_id'] != review['review_id']:
            raise RuntimeError('Review did not verify this candidate.')
        return current

    def finalize_run(self, task, attempt, candidate):
        deadline = time.monotonic() + 12
        review_id = None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise RuntimeError('Run review readiness deadline exceeded.')
            current = self.command('status', '--task', task, timeout=remaining)['task']
            if time.monotonic() >= deadline: raise RuntimeError('Run review readiness deadline exceeded.')
            if not current.get('current_attempt') or current['current_attempt']['attempt_id'] != attempt['attempt_id']:
                raise RuntimeError('Executor driver cannot adopt replacement attempt.')
            if current['candidate_commit'] != candidate:
                raise RuntimeError('Executor driver candidate changed.')
            review = current.get('review')
            if current.get('repair') or current['state'] not in ('submitted', 'verifying', 'reviewing'):
                raise RuntimeError('Run did not reach valid independent review.')
            # Reviewing is observable while the completed verifier is cleaned
            # up, before review_requested creates its binding. Keep waiting in
            # the existing readiness deadline; validate every present record.
            if current['state'] == 'reviewing' and review is not None:
                if not review or review['candidate_commit'] != candidate or review['attempt']['attempt_id'] != attempt['attempt_id']:
                    raise RuntimeError('Run review binding differs from the submitted candidate.')
                if review_id is not None and review['review_id'] != review_id:
                    raise RuntimeError('Run reviewer changed while waiting for readiness.')
                review_id = review['review_id']
                if review['state'] == 'running':
                    if not review['launch_id'] or not review['runtime_identity']:
                        raise RuntimeError('Running reviewer is missing its launch identity.')
                    break
                if review['state'] != 'requested':
                    raise RuntimeError('Run reviewer failed or has an unknown outcome.')
            time.sleep(0.03)
        self.complete_review(task, attempt, candidate)
        self.command('integrate', '--task', task, '--attempt', attempt['attempt_id'], '--score-file', self.score_file(attempt))
