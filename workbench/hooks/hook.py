#!/usr/bin/env python3
"""prepare-commit-msg: add managed identity and the latest root native turn's observed facts."""
import json
import os
from pathlib import Path
import subprocess
import sys


def claude_turn_facts(env):
    # A Claude Code worker (T-130): its transcript records, for every reply, the model that answered and the
    # effort. The reply running this commit is already written, so the latest real reply is this turn's.
    native = env['A2A_NATIVE_SESSION']
    config = Path(env.get('CLAUDE_CONFIG_DIR') or Path(env['HOME']) / '.claude').resolve()
    projects = config / 'projects'
    files = list(projects.glob('*/' + native + '.jsonl')) if projects.is_dir() else []
    if not files:
        return 'unknown', 'unknown'
    if len(files) != 1 or projects not in files[0].resolve().parents:
        raise ValueError('原生会话记录不唯一或路径越界')
    latest = None
    with files[0].open('r', encoding='utf-8') as stream:
        for line in stream:
            if not line.endswith('\n'):
                break  # An incomplete append cannot provide current-turn facts.
            record = json.loads(line)
            if not isinstance(record, dict) or record.get('type') != 'assistant':
                continue
            if record.get('sessionId') != native:
                raise ValueError('原生记录不是本会话')
            model = (record.get('message') or {}).get('model')
            # "<synthetic>" marks a reply Claude Code wrote itself (an API error or an interruption).
            if isinstance(model, str) and model and model != '<synthetic>':
                latest = record
    if latest is None:
        return 'unknown', 'unknown'
    # Claude Code versions write effort, perTurnEffort or both; where both are written they have always agreed.
    efforts = {value for value in (latest.get('effort'), latest.get('perTurnEffort')) if value}
    if len(efforts) > 1:
        raise ValueError('原生记录的强度字段不一致')
    return latest['message']['model'], efforts.pop() if efforts else 'unknown'


def latest_turn_facts(env):
    # agy and opencode (T-187) report turns only to the terminal and keep no record this hook can read.
    if env.get('A2A_TURNS') == 'osc7501':
        return 'unknown', 'unknown'
    home = env.get('CODEX_HOME')
    if not home:
        return claude_turn_facts(env)
    native = env['CODEX_THREAD_ID']
    sessions = Path(home).resolve() / 'sessions'
    files = [path for path in sessions.rglob('*.jsonl') if path.name.endswith(native + '.jsonl')]
    if not files:
        return 'unknown', 'unknown'
    if len(files) != 1 or sessions not in files[0].resolve().parents:
        raise ValueError('原生会话记录不唯一或路径越界')
    turn, context, bound = None, None, False
    with files[0].open('r', encoding='utf-8') as stream:
        for line in stream:
            if not line.endswith('\n'):
                break  # An incomplete append cannot provide current-turn facts.
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError('原生记录不是 JSON 对象')
            payload = record.get('payload', {})
            if record.get('type') in ('session_meta', 'event_msg', 'turn_context') and not isinstance(payload, dict):
                raise ValueError('原生身份或回合记录的 payload 不合法')
            if record.get('type') == 'session_meta':
                if payload.get('id') != native or payload.get('source') != 'cli':
                    raise ValueError('原生记录不是本根 CLI 会话')
                bound = True
            elif record.get('type') == 'event_msg' and payload.get('type') == 'task_started':
                turn, context = payload.get('turn_id'), None
            elif record.get('type') == 'turn_context' and turn and payload.get('turn_id') == turn:
                context = payload
    if not bound:
        raise ValueError('原生记录缺少根会话身份')
    if context is None:
        return 'unknown', 'unknown'
    return context.get('model') or 'unknown', context.get('effort') or context.get('reasoning_effort') or 'unknown'


def add_trailers():
    env = os.environ
    trailers = {'A2A-Task': env['A2A_TASK'], 'A2A-Attempt': env['A2A_ATTEMPT'],
                'A2A-Session': env['A2A_SESSION'], 'A2A-Role': env['A2A_ROLE'],
                'A2A-Tool': env['A2A_TOOL'], 'A2A-Model': 'unknown',
                'A2A-Effort': 'unknown', 'A2A-Native-Session': env.get('CODEX_THREAD_ID') or env['A2A_NATIVE_SESSION'],
                'A2A-Launch': env['A2A_LAUNCH']}
    # Validate before any edit. Requested launch settings are not observed turn facts.
    for key, content in trailers.items():
        if not isinstance(content, str) or not content or '\n' in content or '\r' in content:
            raise ValueError('尾注值不合法：' + key)
    trailers['A2A-Model'], trailers['A2A-Effort'] = latest_turn_facts(env)
    for key in ('A2A-Model', 'A2A-Effort'):
        value = trailers[key]
        if not isinstance(value, str) or not value or '\n' in value or '\r' in value:
            raise ValueError('原生回合尾注值不合法：' + key)
    message = sys.argv[1]
    parsed = subprocess.check_output(['git', 'interpret-trailers', '--parse', '--no-divider', message], text=True)
    counts = {key.lower(): 0 for key in trailers}
    for line in parsed.splitlines():
        key = line.partition(':')[0].strip().lower()
        if key in counts:
            counts[key] += 1
    for _ in range(max(counts.values(), default=0)):
        clear = ['git', 'interpret-trailers', '--in-place', '--no-divider', '--trim-empty',
                 '--if-exists', 'replace', '--if-missing', 'doNothing']
        for key in trailers:
            clear += ['--trailer', key + ': ']
        subprocess.run([*clear, message], check=True)
    argv = ['git', 'interpret-trailers', '--in-place', '--no-divider', '--if-exists', 'replace']
    for key, content in trailers.items():
        argv += ['--trailer', key + ': ' + content]
    subprocess.run([*argv, message], check=True)


if __name__ == '__main__':
    try:
        # The only hook: a managed session's commit runs outside its sandbox, so the project's own
        # hooks, whose code the worker can edit, are not run (user ruling 2026-10-21, T-122
        # review 03); the gate records which ones were skipped.
        add_trailers()
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError) as error:
        print('a2a 提交钩子拒绝：' + str(error), file=sys.stderr)
        sys.exit(1)
