#!/usr/bin/env python3
"""Add managed identity and the latest root native turn's observed facts."""
import json
import os
from pathlib import Path
import subprocess
import sys


def latest_turn_facts(env):
    home = env.get('CODEX_HOME')
    if not home:
        # A Claude Code worker: its transcript records no per-turn effort, so the
        # launch's requested effort is the only effort known.
        return 'unknown', env['A2A_EFFORT_REQUESTED'] if env.get('A2A_NATIVE_SESSION') else 'unknown'
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


def forward():
    # Run the repository's existing hook without writing its config.
    name = Path(sys.argv[0]).name
    original_env = dict(os.environ)
    # Entry 0 is the session's hooks path. Claude Code's shell sandbox appends safe.directory
    # entries for the worktree and repository (T-122 probe); nothing else may follow, since a
    # later entry would override the hooks path.
    count = original_env.get('GIT_CONFIG_COUNT', '')
    if not count.isdigit() or int(count) < 1 or original_env.get('GIT_CONFIG_KEY_0') != 'core.hooksPath' or \
            any(original_env.get(f'GIT_CONFIG_KEY_{index}') != 'safe.directory' for index in range(1, int(count))):
        raise ValueError('会话 Git 配置改变')
    for key in ('GIT_CONFIG_COUNT', *(f'GIT_CONFIG_{part}_{index}' for index in range(int(count)) for part in ('KEY', 'VALUE'))):
        original_env.pop(key, None)
    original = Path(subprocess.check_output(['git', 'rev-parse', '--git-path', 'hooks/' + name],
                                          env=original_env, text=True).strip()).resolve()
    if original == Path(__file__).resolve():
        raise ValueError('原钩子递归')
    if original.is_file() and os.access(original, os.X_OK):
        subprocess.run([str(original), *sys.argv[1:]], check=True)


if __name__ == '__main__':
    try:
        if Path(sys.argv[0]).name == 'prepare-commit-msg':
            add_trailers()
        forward()
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError) as error:
        print('a2a 提交钩子拒绝：' + str(error), file=sys.stderr)
        sys.exit(1)
