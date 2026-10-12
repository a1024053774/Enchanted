#!/usr/bin/env python3
"""Render exact approval argv without starting Codex or copying credentials."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import uuid

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--launches-from', type=Path)
args = parser.parse_args()
OUT = args.output


def quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    fixture = Path('/private/tmp/t077-cf-20261012-r2')
    if fixture.exists():
        raise FileExistsError(fixture)
    node = str(Path(shutil.which('node')).resolve(strict=True))
    codex = str(Path(shutil.which('codex')).resolve(strict=True))
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    role_revision = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', '.project-map/roles/worker.md'], cwd=ROOT, text=True).strip()
    state, home = fixture / 'state', fixture / 'codex-home'
    cli = str(ROOT / 'workbench/src/gates/cli.ts')
    plan = {'product_revision': revision, 'node': node, 'codex': codex, 'cli_version': 'codex-cli 0.162.1',
            'fixture': str(fixture), 'repo': str(fixture / 'repo'), 'state': str(state), 'home': str(home),
            'task': 'T-077-11', 'project': 'T077-real-r2', 'cli': cli,
            'role_card': str(ROOT / '.project-map/roles/worker.md'), 'role_card_revision': role_revision,
            'trust_root': str(fixture / 'repo'), 'budget_authorization': '20261012T015257Z-ideation-answer-001',
            'run_root': 'real-conflict-02', 'budget_ledger': 'real-turn-budget-02.jsonl',
            'prior_turns_consumed': 4, 'requested_service_tier': None, 'turn_limit': 4, 'turns_per_attempt': 2,
            'rules': ['prefix_rule(pattern=["git", "add"], decision="allow")',
                      'prefix_rule(pattern=["git", "commit"], decision="allow")'],
            'launches': []}
    for fence in (1, 2):
        launch = json.loads(args.launches_from.read_text(encoding='utf-8'))['launches'][fence - 1]['launch'] if args.launches_from else str(uuid.uuid4())
        workspace = state / 'worktrees/T077-real-r2' / ('T-077-11-a' + str(fence))
        signal = ' '.join(map(quote, [node, cli, '--state', str(state), 'signal', '--launch', launch]))
        hook = '[{hooks=[{type="command",command=' + json.dumps(signal) + ',timeout=10}]}]'
        argv = [codex, '--no-daemon', '--no-alt-screen', '-C', str(workspace), '-a', 'never', '--sandbox',
                'workspace-write', '-m', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="xhigh"',
                '-c', 'check_for_update_on_startup=false', '-c', 'tui.notifications=false',
                '-c', 'sandbox_workspace_write.network_access=false', '-c', 'features.network_proxy=false']
        for event in ('UserPromptSubmit', 'Stop', 'PermissionRequest'):
            argv.extend(['-c', 'hooks.' + event + '=' + hook])
        argv.append('--dangerously-bypass-hook-trust')
        plan['launches'].append({'fence': fence, 'launch': launch, 'workspace': str(workspace), 'argv': argv,
            'shell': '/bin/zsh', 'shell_argv': ['-f', '-i', '-c', ' '.join(map(quote, argv)) + '; exec /bin/zsh -f -i'],
            'hooks': {event: signal for event in ('UserPromptSubmit', 'Stop', 'PermissionRequest')},
            'git_hook': {'path': str(ROOT / 'workbench/hooks/prepare-commit-msg'),
                         'resolved_path': str((ROOT / 'workbench/hooks/prepare-commit-msg').resolve()),
                         'message_path': str(fixture / 'repo/.git/worktrees' / ('T-077-11-a' + str(fence)) / 'COMMIT_EDITMSG'),
                         'source_argument': 'message'},
            'checked_env': {'CODEX_HOME': str(home), 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
                            'GIT_CONFIG_VALUE_0': str(ROOT / 'workbench/hooks') + '/',
                            'A2A_TASK': 'T-077-11', 'A2A_FENCE': str(fence), 'A2A_LAUNCH': launch,
                            'A2A_MODEL_REQUESTED': 'gpt-6.1-sol', 'A2A_EFFORT_REQUESTED': 'xhigh'}})
    with OUT.open('x', encoding='utf-8') as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps({'plan': str(OUT), 'revision': revision, 'launches': [v['launch'] for v in plan['launches']], 'real_turns': 0}))


if __name__ == '__main__':
    main()
