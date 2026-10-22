#!/usr/bin/env python3
"""T-084：尾注 Launch/Tool/Model/Effort 必须等于本 attempt 的启动记录。

期望来自用户决定和启动记录本身，不读门禁实现的输出。
启动记录是受控宿主在 dispatch 时写入的 worker-creations.jsonl
（id、cli_version、model、effort）。本票在 dispatch 前写入
observed-facts.json，让记录的 model/effort 与任务卡不同；缺这个文件时
宿主仍抄任务卡。正例取记录值。反例取任务卡值，或把 Effort 写成 unknown
而记录 effort 仍是 xhigh。伪造值是脚本里的常量。

门禁在 submit 时把同一份事实放进 attempt.delivery
（launch_id、cli、model、effort）。本脚本先核对 delivery 与启动记录一致；
不一致就以缺口退出，不把尾注或别的提交当成记录。

claim-forged 只 claim、不 dispatch，四项尾注用上面的伪造常量。没有
attempt.delivery 时，带 A2A 尾注的交付必须在尾注检查拒收，码为
trailer_launch_record_missing，事件原因是缺启动记录。claim-none
完全不写尾注，仍只记一次「推断：缺尾注」。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / 'workbench/src/gates/cli.ts'
HOST = Path(__file__).with_name('daemon_acceptance_host.ts')
CORE = ROOT / 'workbench/src/gates/core.ts'
CARD_MODEL = 'gpt-6.1-sol'
CARD_EFFORT = 'xhigh'
RECORD_MODEL = 'observed-not-card'
RECORD_EFFORT = 'observed-not-xhigh'
FORGED = {
    'launch': 'not-this-attempt-launch',
    'tool': 'not-the-recorded-cli',
    'model': 'not-the-recorded-model',
    'effort': 'not-the-recorded-effort',
}
MISMATCHES = ('launch', 'tool', 'model', 'effort')
CARD_CASES = ('model-card', 'effort-card')
REJECTIONS = (*MISMATCHES, *CARD_CASES, 'effort-unknown')
POSITIVES = ('match', 'unknown', 'none')
CLAIM_MODES = ('claim-forged', 'claim-none')
LAUNCH_MISSING = 'trailer_launch_record_missing'
LAUNCH_MISSING_REASON = '缺启动记录'
MISSING_LABEL = '推断：缺尾注'
NEEDLES = {
    'launch': '          if (trailers.launch![0] !== attempt.delivery.launch_id) error = "trailer_identity_mismatch";\n',
    'tool': '          else if (trailers.tool![0] !== attempt.delivery.cli) error = "trailer_identity_mismatch";\n',
    'model': '          else if (trailers.model![0] !== "unknown" && trailers.model![0] !== attempt.delivery.model) error = "trailer_identity_mismatch";\n',
    # Since T-122 the effort comparison spans two lines: a Claude Code launch may leave Effort unknown.
    'effort': '          else if (trailers.effort![0] !== attempt.delivery.effort &&\n'
              '            !(trailers.effort![0] === "unknown" && this.launchRecordCli(attempt.delivery.launch_id) === "Claude Code")) error = "trailer_identity_mismatch";\n',
}
CLAUDE_EFFORT_EXEMPTION = 'this.launchRecordCli(attempt.delivery.launch_id) === "Claude Code"'


def git_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'A2A_'))}
    env.update({
        'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
        'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
        'GIT_CONFIG_VALUE_0': os.devnull, 'GIT_CONFIG_KEY_1': 'commit.gpgsign',
        'GIT_CONFIG_VALUE_1': 'false', 'GIT_AUTHOR_NAME': 'Independent fixture',
        'GIT_AUTHOR_EMAIL': 'fixture@example.invalid', 'GIT_COMMITTER_NAME': 'Independent fixture',
        'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
    })
    return env


class Gate:
    def __init__(self, state, env, commands):
        self.state, self.env, self.commands = state, env, commands

    def __call__(self, task, command, *args, timeout=120):
        argv = ['node', str(GATE), '--state', str(self.state), command, '--task', task, *map(str, args)]
        p = subprocess.run(argv, cwd=str(ROOT), env=self.env, capture_output=True, text=True, timeout=timeout)
        record = {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
        self.commands.append(record)
        if p.returncode not in (0, 1) or not p.stdout:
            raise RuntimeError('gate cli failed: ' + json.dumps(record, ensure_ascii=False))
        value = json.loads(p.stdout)
        record['ok'] = value.get('ok')
        record['error'] = value.get('error')
        return value


def init_repo(root, env):
    repo = root / 'repo'
    repo.mkdir(parents=True)
    (repo / 'src').mkdir()
    (repo / 'src/value.txt').write_text('base\n', encoding='utf-8')
    acceptance = repo / 'acceptance'
    acceptance.mkdir()
    (acceptance / 'criterion.py').write_text(
        "from pathlib import Path\nassert Path('src/value.txt').read_text() == 'worker\\n'\n", encoding='utf-8')

    def git(*args):
        p = subprocess.run(['git', '-C', str(repo), *args], env=env, capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            raise RuntimeError(p.stderr or p.stdout)
        return p.stdout.strip()

    git('init', '-b', 'main')
    git('add', '.')
    git('commit', '-m', 'Independent baseline')
    return repo, git


def trailers_for(attempt, record, mode):
    if mode == 'none':
        return None
    values = {
        'Task': attempt['task_id'], 'Attempt': attempt['attempt_id'],
        'Session': attempt['session_id'], 'Role': 'worker',
        'Tool': record['cli_version'], 'Model': record['model'], 'Effort': record['effort'],
        'Native-Session': 'native-turn:' + attempt['thread_id'], 'Launch': record['id'],
    }
    if mode == 'unknown':
        values['Model'] = 'unknown'
    elif mode == 'effort-unknown':
        values['Effort'] = 'unknown'
    elif mode == 'model-card':
        values['Model'] = CARD_MODEL
    elif mode == 'effort-card':
        values['Effort'] = CARD_EFFORT
    elif mode in FORGED:
        key = {'launch': 'Launch', 'tool': 'Tool', 'model': 'Model', 'effort': 'Effort'}[mode]
        values[key] = FORGED[mode]
    return values


def claim_trailers(attempt, mode):
    if mode == 'claim-none':
        return None
    return {
        'Task': attempt['task_id'], 'Attempt': attempt['attempt_id'],
        'Session': attempt['session_id'], 'Role': 'worker',
        'Tool': FORGED['tool'], 'Model': FORGED['model'], 'Effort': FORGED['effort'],
        'Native-Session': 'native-turn:no-thread', 'Launch': FORGED['launch'],
    }


def commit_candidate(repo, env, attempt, values):
    workspace = Path(attempt['workspace'])
    (workspace / 'src/value.txt').write_text('worker\n', encoding='utf-8')
    message = 'Independent fixture commit'
    if values:
        message += '\n\n' + '\n'.join('A2A-' + key + ': ' + value for key, value in values.items())
    subprocess.run(['git', '-C', str(workspace), 'add', '.'], env=env, check=True, capture_output=True, text=True)
    subprocess.run(['git', '-C', str(workspace), 'commit', '-m', message], env=env, check=True, capture_output=True, text=True)
    oid = subprocess.run(['git', '-C', str(workspace), 'rev-parse', 'HEAD'], env=env, check=True, capture_output=True, text=True).stdout.strip()
    body = subprocess.run(['git', '-C', str(workspace), 'show', '-s', '--format=%B', 'HEAD'], env=env, check=True, capture_output=True, text=True).stdout
    base = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], env=env, check=True, capture_output=True, text=True).stdout.strip()
    return oid, body, base


def start_daemon(state, boundary, review, core, env, logs):
    ready = state.parent / 'daemon-ready.json'
    if ready.exists():
        ready.unlink()
    stdout = (logs / 'host.stdout').open('xb')
    stderr = (logs / 'host.stderr').open('xb')
    argv = ['node', str(HOST), str(state), str(boundary), str(ready), str(core), str(review)]
    host = subprocess.Popen(argv, cwd=str(ROOT), env=env, stdout=stdout, stderr=stderr, start_new_session=True)
    deadline = time.monotonic() + 20
    while not ready.exists():
        if host.poll() is not None or time.monotonic() >= deadline:
            stdout.close(); stderr.close()
            raise RuntimeError('daemon did not start: ' + (logs / 'host.stderr').read_text(encoding='utf-8')[-4000:])
        time.sleep(0.05)
    return host, stdout, stderr, argv


def stop_daemon(host, state, env, stdout, stderr):
    try:
        subprocess.run(['node', str(GATE), '--state', str(state), 'daemon_stop'], cwd=str(ROOT), env=env,
                       capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        pass
    deadline = time.monotonic() + 10
    while host.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    if host.poll() is None:
        os.killpg(host.pid, 15)
        try:
            host.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(host.pid, 9)
            host.wait(timeout=5)
    stdout.close(); stderr.close()


def observed_for(mode):
    # effort-unknown keeps the recorded effort at xhigh. Every other case separates both fields from the card.
    if mode == 'effort-unknown':
        return RECORD_MODEL, CARD_EFFORT
    return RECORD_MODEL, RECORD_EFFORT


def run_cases(phase, core, out, modes):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from legacy_quality_driver import prepare_review_control
    out.mkdir(parents=True, exist_ok=False)
    env = git_env()
    artifact = Path(tempfile.mkdtemp(prefix='t084-', dir='/tmp'))
    # The daemon writes its bootstrap operator credential here; gate CLI calls read it (T-109 on).
    env['A2A_OPERATOR_CREDENTIAL'] = str(artifact / 'operator.json')
    state = artifact / 's'
    state.mkdir()
    boundary = artifact / 'worker'
    boundary.mkdir()
    (boundary / 'store.json').write_text(json.dumps({
        'threads': {}, 'next': 0, 'scenario': 'done-no-submit', 'prompts': [], 'closes': [], 'archived': {},
    }) + '\n', encoding='utf-8')
    review = prepare_review_control(artifact, count=8)
    logs = out / 'daemon'
    logs.mkdir()
    commands = []
    host, stdout, stderr, host_argv = start_daemon(state, boundary, review, core, env, logs)
    results = []
    gap = None
    try:
        gate = Gate(state, env, commands)
        for mode in modes:
            case = out / mode
            case.mkdir()
            task = 't084-' + mode
            repo, _git = init_repo(artifact / mode, env)
            card = {
                'id': task, 'source': None, 'goal': '把 src/value.txt 写成 worker',
                'non_goals': ['不改验收文件'], 'paths': {'allow': ['src/'], 'deny': ['src/private/']},
                'oracle_paths': ['acceptance/criterion.py'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c',
                    "from pathlib import Path; import runpy; runpy.run_path('acceptance/criterion.py')"]}],
                'red_commands': [], 'task_type': '后端逻辑', 'repair_target': None, 'complexity': 'S',
                'executor': {'cli': 'Codex', 'model': CARD_MODEL, 'effort': CARD_EFFORT},
                'base_commit': None, 'writer': None,
            }
            card_file = case / 'card.json'
            card_file.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
            gate(task, 'card_save', '--card', card_file, '--expected-version', '0')
            gate(task, 'create', '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')
            if mode in CLAIM_MODES:
                attempt = gate(task, 'claim', '--owner', 'independent-check')['attempt']
                record = None
                (case / 'launch-record.json').write_text('null\n', encoding='utf-8')
                if attempt.get('thread_id'):
                    gap = {'mode': mode, 'reason': 'claim-only case received a worker thread', 'attempt': attempt['attempt_id']}
                    break
                values = claim_trailers(attempt, mode)
            else:
                want_model, want_effort = observed_for(mode)
                (boundary / 'observed-facts.json').write_text(
                    json.dumps({'model': want_model, 'effort': want_effort}) + '\n', encoding='utf-8')
                attempt = gate(task, 'dispatch', '--runtime-mode', 'approval-required')['attempt']
                rows = [json.loads(line) for line in (boundary / 'worker-creations.jsonl').read_text(encoding='utf-8').splitlines()]
                record = next(row for row in rows if row['attempt'] == attempt['attempt_id'])
                (case / 'launch-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                if record['model'] != want_model or record['effort'] != want_effort or not record['id'] or not record['cli_version']:
                    gap = {'mode': mode, 'reason': 'launch record does not match the observed facts requested for this case',
                           'record': record, 'wanted': {'model': want_model, 'effort': want_effort}}
                    break
                if record['model'] == CARD_MODEL or (mode == 'effort-unknown' and record['effort'] != CARD_EFFORT) or (
                        mode != 'effort-unknown' and record['effort'] == CARD_EFFORT):
                    gap = {'mode': mode, 'reason': 'launch record model/effort is not separated from the card as this case requires',
                           'record': record, 'card': {'model': CARD_MODEL, 'effort': CARD_EFFORT}}
                    break
                if any(record[{'launch': 'id', 'tool': 'cli_version', 'model': 'model', 'effort': 'effort'}[name]] == FORGED[name] for name in MISMATCHES):
                    gap = {'mode': mode, 'reason': 'forged constant collided with the launch record', 'record': record}
                    break
                values = trailers_for(attempt, record, mode)
            oid, body, base = commit_candidate(repo, env, attempt, values)
            (case / 'commit-message.txt').write_text(body, encoding='utf-8')
            submitted = gate(task, 'submit', '--attempt', attempt['attempt_id'], '--session', attempt['session_id'],
                             '--fence', attempt['fence'], '--spec-rev', attempt['spec_rev'], '--commit', oid)
            if not submitted.get('ok'):
                gap = {'mode': mode, 'reason': 'submit failed before trailer check', 'submit': submitted}
                break
            status = gate(task, 'status')
            delivery = status['task']['current_attempt'].get('delivery')
            identity = status['task']['current_attempt'].get('runtime_identity') or {}
            held = {
                'launch_id': None if not delivery else delivery.get('launch_id'),
                'cli': None if not delivery else delivery.get('cli'),
                'model': None if not delivery else delivery.get('model'),
                'effort': None if not delivery else delivery.get('effort'),
                'runtime_launch': identity.get('launch'),
            }
            (case / 'delivery.json').write_text(json.dumps(held, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            if mode in CLAIM_MODES:
                if delivery is not None:
                    gap = {'mode': mode, 'reason': 'claim-only attempt has a delivery; this case cannot show a missing launch record',
                           'delivery': delivery}
                    break
            elif held != {
                'launch_id': record['id'], 'cli': record['cli_version'], 'model': record['model'],
                'effort': record['effort'], 'runtime_launch': record['id'],
            }:
                gap = {'mode': mode, 'reason': 'gate does not hold this attempt launch record tool/model/effort',
                       'held': held, 'record': {'id': record['id'], 'cli_version': record['cli_version'],
                                                'model': record['model'], 'effort': record['effort']}}
                break
            verified = gate(task, 'verify')
            (case / 'verify.json').write_text(json.dumps(verified, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            events = gate(task, 'events')['events']
            (case / 'events.json').write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            checks = [event for event in events if event['type'] == 'trailer_check' and event['details'].get('commit') == oid]
            interventions = [event for event in events if event['type'] == 'human_intervention']
            inputs = status_inputs(gate, task)
            main = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], env=env, check=True, capture_output=True, text=True).stdout.strip()
            results.append({
                'mode': mode, 'verify_ok': verified.get('ok'), 'verify_error': verified.get('error'),
                'trailer_passed': [event['details'].get('passed') for event in checks],
                'trailer_error': [event['details'].get('error') for event in checks],
                'trailer_reason': [event['details'].get('reason') for event in checks],
                'interventions': len(interventions),
                'user_inputs': len(inputs),
                'input_labels': [item.get('source_ref', {}).get('label') for item in inputs],
                'main_unchanged': main == base, 'commit': oid,
            })
    finally:
        stop_daemon(host, state, env, stdout, stderr)
        (out / 'commands.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in commands), encoding='utf-8')
        (out / 'host-argv.json').write_text(json.dumps(host_argv) + '\n', encoding='utf-8')
    if gap:
        (out / 'GAP.json').write_text(json.dumps(gap, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return {'status': 'GAP', 'phase': phase, 'gap': gap, 'results': results, 'core': str(core)}
    return {'status': judge(phase, results), 'phase': phase, 'results': results, 'core': str(core), 'artifact': str(artifact)}


def status_inputs(gate, task):
    return gate(task, 'status')['user_inputs']


def judge(phase, results):
    by_mode = {row['mode']: row for row in results}
    removed = phase.split('-', 1)[1] if phase.startswith('mutant-') else None
    for mode in REJECTIONS:
        if mode not in by_mode:
            continue
        row = by_mode[mode]
        accept = phase == 'red' or mode == removed
        if accept:
            if not (row['verify_ok'] and row['trailer_passed'] == [True] and row['trailer_error'] == [None] and row['interventions'] == 0):
                return 'INCOMPLETE'
        else:
            if not (row['verify_ok'] is False and row['verify_error'] == 'trailer_identity_mismatch'
                    and row['trailer_passed'] == [False] and row['trailer_error'] == ['trailer_identity_mismatch']
                    and row['interventions'] == 0 and row['main_unchanged']):
                return 'INCOMPLETE'
    for mode in ('match', 'unknown', 'none'):
        if mode not in by_mode:
            continue
        row = by_mode[mode]
        if not row['verify_ok'] or row['trailer_passed'] != [True]:
            return 'INCOMPLETE'
        if mode == 'none':
            if row['interventions'] != 1 or row['user_inputs'] != 1 or row['input_labels'] != ['推断：缺尾注']:
                return 'INCOMPLETE'
        elif row['interventions'] != 0 or row['trailer_error'] != [None]:
            return 'INCOMPLETE'
    if 'claim-forged' in by_mode:
        forged = by_mode['claim-forged']
        if phase in ('red', 'red-03'):
            if not row_accepted(forged):
                return 'INCOMPLETE'
        elif not row_missing_record(forged):
            return 'INCOMPLETE'
    if 'claim-none' in by_mode and not row_plain_missing(by_mode['claim-none']):
        return 'INCOMPLETE'
    if phase.startswith('mutant-'):
        field = phase.split('-', 1)[1]
        if field not in by_mode:
            return 'INCOMPLETE'
    return 'PASS'


def install_core(directory, text):
    src = directory / 'src'
    shutil.copytree(ROOT / 'workbench/src', src, symlinks=True)
    target = src / 'gates/core.ts'
    target.write_text(text, encoding='utf-8')
    (directory / 'node_modules').symlink_to(ROOT / 'workbench/node_modules')
    return target


def mutant_core(field, directory):
    text = CORE.read_text(encoding='utf-8')
    needle = NEEDLES[field]
    if text.count(needle) != 1:
        raise RuntimeError('comparison line for ' + field + ' is not unique')
    return install_core(directory, text.replace(needle, '', 1))


def replace_needles(directory, pairs):
    text = CORE.read_text(encoding='utf-8')
    for old, new in pairs:
        if text.count(old) != 1:
            raise RuntimeError('comparison line is not unique')
        text = text.replace(old, new, 1)
    return install_core(directory, text)


def row_accepted(row):
    return row['verify_ok'] is True and row['trailer_passed'] == [True] and row['trailer_error'] == [None] and row['interventions'] == 0


def row_rejected(row):
    return (row['verify_ok'] is False and row['verify_error'] == 'trailer_identity_mismatch'
            and row['trailer_passed'] == [False] and row['trailer_error'] == ['trailer_identity_mismatch']
            and row['interventions'] == 0 and row['main_unchanged'])


def row_missing_record(row):
    return (row['verify_ok'] is False and row['verify_error'] == LAUNCH_MISSING
            and row['trailer_passed'] == [False] and row['trailer_error'] == [LAUNCH_MISSING]
            and row['trailer_reason'] == [LAUNCH_MISSING_REASON]
            and row['interventions'] == 0 and row['main_unchanged'])


def row_plain_missing(row):
    return (row['verify_ok'] is True and row['trailer_passed'] == [True] and row['trailer_error'] == [None]
            and row['interventions'] == 1 and row['user_inputs'] == 1 and row['input_labels'] == [MISSING_LABEL])


def detection(kind, results):
    by_mode = {row['mode']: row for row in results}
    if kind in ('effort-unknown-exemption', 'claude-effort-exemption-any-cli'):
        flipped = ['effort-unknown']
        still = [mode for mode in REJECTIONS if mode != 'effort-unknown']
        positives = ('match', 'unknown')
    elif kind == 'compare-model-to-card':
        flipped = ['model-card']
        still = [mode for mode in REJECTIONS if mode != 'model-card'] + ['match']
        positives = ('unknown',)
    elif kind == 'compare-effort-to-card':
        # Effort is the record value on the Model=unknown positive, so that positive is rejected too.
        flipped = ['effort-card']
        still = [mode for mode in REJECTIONS if mode != 'effort-card'] + ['match', 'unknown']
        positives = ()
    else:
        raise RuntimeError(kind)
    ok = all(mode in by_mode and row_accepted(by_mode[mode]) for mode in flipped)
    ok = ok and all(mode in by_mode and row_rejected(by_mode[mode]) for mode in still)
    ok = ok and all(mode in by_mode and row_accepted(by_mode[mode]) for mode in positives)
    none = by_mode.get('none')
    ok = ok and none is not None and none['verify_ok'] is True and none['trailer_passed'] == [True] and none['interventions'] == 1 and none['user_inputs'] == 1 and none['input_labels'] == ['推断：缺尾注']
    return ok


def detection_missing_record(results):
    by_mode = {row['mode']: row for row in results}
    needed = ('claim-forged', 'claim-none', 'match', 'launch', 'none')
    if any(mode not in by_mode for mode in needed):
        return False
    return (row_accepted(by_mode['claim-forged']) and row_plain_missing(by_mode['claim-none'])
            and row_accepted(by_mode['match']) and row_rejected(by_mode['launch'])
            and row_plain_missing(by_mode['none']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['red', 'green', 'mutants', 'green-02', 'mutants-02', 'red-03', 'green-03', 'mutants-03', 'green-04', 'mutants-04', 'green-05', 'mutants-05'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.phase == 'red-03':
        summary = run_cases('red-03', CORE, output / 'red-03', list(CLAIM_MODES))
        (output / 'red-03' / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': summary['status'], 'phase': args.phase}, ensure_ascii=False))
        return 0 if summary['status'] == 'PASS' else 2 if summary['status'] == 'GAP' else 1
    if args.phase in ('green-03', 'green-04', 'green-05'):
        summary = run_cases(args.phase, CORE, output / args.phase, [*REJECTIONS, *POSITIVES, *CLAIM_MODES])
        (output / args.phase / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': summary['status'], 'phase': args.phase}, ensure_ascii=False))
        return 0 if summary['status'] == 'PASS' else 2 if summary['status'] == 'GAP' else 1
    if args.phase == 'mutants-03':
        needle = '} else error = "trailer_launch_record_missing";\n'
        scratch = Path(tempfile.mkdtemp(prefix='t084m-', dir='/tmp'))
        core = replace_needles(scratch, ((needle, '}\n'),))
        modes = ['claim-forged', 'claim-none', 'match', 'launch', 'none']
        report = run_cases('green', core, output / 'mutants-03' / 'delete-launch-record-rejection', modes)
        report['kind'] = 'delete-launch-record-rejection'
        report['green_judge'] = report['status']
        caught = report['status'] != 'PASS' and detection_missing_record(report['results'])
        report['status'] = 'DETECTED' if caught else 'INCOMPLETE'
        summary = {'status': report['status'], 'phase': 'mutants-03', 'reports': [report]}
        dest = output / 'mutants-03'
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': summary['status'], 'phase': args.phase}, ensure_ascii=False))
        return 0 if summary['status'] == 'DETECTED' else 2 if summary['status'] == 'GAP' else 1
    if args.phase == 'green-02':
        summary = run_cases('green-02', CORE, output / 'green-02', [*REJECTIONS, *POSITIVES])
        (output / 'green-02' / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': summary['status'], 'phase': args.phase}, ensure_ascii=False))
        return 0 if summary['status'] == 'PASS' else 2 if summary['status'] == 'GAP' else 1
    if args.phase in ('mutants-02', 'mutants-04', 'mutants-05'):
        green_modes = [*REJECTIONS, *POSITIVES]
        specs = [
            ('effort-unknown-exemption', (
                (NEEDLES['effort'],
                 '          else if (trailers.effort![0] !== "unknown" && trailers.effort![0] !== attempt.delivery.effort) error = "trailer_identity_mismatch";\n'),
            ), detection),
            ('compare-model-to-card', (
                (NEEDLES['model'],
                 '          else if (trailers.model![0] !== "unknown" && trailers.model![0] !== task.card.executor.model) error = "trailer_identity_mismatch";\n'),
            ), detection),
            ('compare-effort-to-card', (
                (NEEDLES['effort'],
                 '          else if (trailers.effort![0] !== task.card.executor.effort) error = "trailer_identity_mismatch";\n'),
            ), detection),
        ]
        if args.phase == 'mutants-05':
            # T-122 review 02 N6: the Claude Code exemption must not reach a Codex delivery.
            specs.append(('claude-effort-exemption-any-cli', ((CLAUDE_EFFORT_EXEMPTION, 'true'),), detection))
        if args.phase in ('mutants-04', 'mutants-05'):
            specs.append(('delete-launch-record-rejection', (
                ('} else error = "trailer_launch_record_missing";\n', '}\n'),
            ), detection_missing_record))
        reports = []
        for kind, pairs, detect in specs:
            scratch = Path(tempfile.mkdtemp(prefix='t084m-', dir='/tmp'))
            core = replace_needles(scratch, pairs)
            modes = ['claim-forged', 'claim-none', 'match', 'launch', 'none'] if kind == 'delete-launch-record-rejection' else green_modes
            report = run_cases('green', core, output / args.phase / kind, modes)
            report['kind'] = kind
            report['green_judge'] = report['status']
            caught = report['status'] != 'PASS' and detect(kind, report['results']) if detect is detection else report['status'] != 'PASS' and detect(report['results'])
            report['status'] = 'DETECTED' if caught else 'INCOMPLETE'
            reports.append(report)
            if report['status'] != 'DETECTED':
                break
        status = 'DETECTED' if reports and all(row['status'] == 'DETECTED' for row in reports) else reports[-1]['status']
        summary = {'status': status, 'phase': args.phase, 'reports': reports}
        dest = output / args.phase
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': summary['status'], 'phase': args.phase}, ensure_ascii=False))
        return 0 if summary['status'] == 'DETECTED' else 2 if summary['status'] == 'GAP' else 1
    if args.phase == 'mutants':
        reports = []
        for field in MISMATCHES:
            scratch = Path(tempfile.mkdtemp(prefix='t084m-', dir='/tmp'))
            core = mutant_core(field, scratch)
            # The removed comparison must let its own case through and still reject the other three.
            report = run_cases('mutant-' + field, core, output / field, MISMATCHES)
            report['removed'] = field
            reports.append(report)
            if report['status'] != 'PASS':
                break
        status = 'PASS' if reports and all(row['status'] == 'PASS' for row in reports) else reports[-1]['status']
        summary = {'status': status, 'phase': 'mutants', 'reports': reports}
    else:
        modes = [*MISMATCHES, 'match', 'unknown', 'none']
        summary = run_cases(args.phase, CORE, output / args.phase, modes)
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': summary['status'], 'phase': args.phase}, ensure_ascii=False))
    return 0 if summary['status'] == 'PASS' else 2 if summary['status'] == 'GAP' else 1


if __name__ == '__main__':
    raise SystemExit(main())
