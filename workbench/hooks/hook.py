#!/usr/bin/env python3
"""Add session environment facts. The delivery channel is pending decision 02."""
import os
from pathlib import Path
import subprocess
import sys


def add_trailers():
    env = os.environ
    trailers = {'A2A-Task': env['A2A_TASK'], 'A2A-Attempt': env['A2A_ATTEMPT'],
                'A2A-Session': env['A2A_SESSION'], 'A2A-Role': env['A2A_ROLE'],
                'A2A-Tool': env['A2A_TOOL'], 'A2A-Model': env.get('A2A_MODEL', 'unknown'),
                'A2A-Effort': env.get('A2A_EFFORT', 'unknown'), 'A2A-Native-Session': env['CODEX_THREAD_ID'],
                'A2A-Launch': env['A2A_LAUNCH']}
    # Validate before any edit. Requested launch settings are not observed turn facts.
    for key, content in trailers.items():
        if not content or '\n' in content or '\r' in content:
            raise ValueError('尾注值不合法：' + key)
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
    if original_env.get('GIT_CONFIG_COUNT') != '1' or original_env.get('GIT_CONFIG_KEY_0') != 'core.hooksPath':
        raise ValueError('会话 Git 配置改变')
    for key in ('GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_0', 'GIT_CONFIG_VALUE_0'):
        original_env.pop(key)
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
