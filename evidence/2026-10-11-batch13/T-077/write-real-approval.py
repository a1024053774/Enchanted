#!/usr/bin/env python3
"""Render the readable approval packet from the frozen argv plan."""
import json
from pathlib import Path

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077')
plan = json.loads((ROOT / 'real-plan-01.json').read_text(encoding='utf-8'))
template = (ROOT / 'real-approval.template.md').read_text(encoding='utf-8')


def quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


blocks = []
for item in plan['launches']:
    blocks.extend(['## Launch ' + str(item['fence']), '',
                   '`' + item['launch'] + '`', '', 'Worktree: `' + item['workspace'] + '`', '',
                   'Codex argv:', '', '```sh', ' '.join(map(quote, item['argv'])), '```', '',
                   'UserPromptSubmit / Stop / PermissionRequest (each timeout=10):', '',
                   '```sh', item['hooks']['Stop'], '```', '', 'Git hook environment:', '', '```text',
                   'GIT_CONFIG_COUNT=1', 'GIT_CONFIG_KEY_0=core.hooksPath',
                   'GIT_CONFIG_VALUE_0=' + item['checked_env']['GIT_CONFIG_VALUE_0'], '```', '',
                   'Git prepare-commit-msg (git commit -m):', '', '```sh',
                   ' '.join(map(quote, [item['git_hook']['path'], item['git_hook']['message_path'], 'message'])),
                   '```', '', 'Hook source: `' + item['git_hook']['resolved_path'] + '`', ''])
assert template.count('<!-- EXACT-LAUNCHES -->') == 1
with (ROOT / 'REAL-APPROVAL-01.md').open('x', encoding='utf-8') as output:
    output.write(template.replace('<!-- EXACT-LAUNCHES -->', '\n'.join(blocks)))
