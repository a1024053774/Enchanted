"""独立核对能力命令属于调用者指定的本次 run；不从 policy 推导预期路径。"""
from pathlib import Path
import shlex


def check_command_paths(policy, role, first_turn, *, run_root, task, g, target):
    root = Path(run_root)
    repo, bare = str(root / 'repo'), str(root / 'local.git')
    expected = [['git', '-C', repo, 'update-ref', 'refs/heads/main', target, g],
                ['git', '-C', repo, 'push', bare, target + ':refs/heads/t081-probe']]
    def reject(where, actual):
        raise ValueError({'code': 'CAPABILITY_COMMAND_PATH_MISMATCH', 'where': where,
                          'run_root': str(root), 'expected_commands': expected, 'actual': actual})
    for field, value in {'run_root': str(root), 'repo': repo, 'bare_repo': bare,
                         'state': str(root / 'state'), 'task': task}.items():
        if policy.get(field) != value:
            reject('policy.' + field, policy.get(field))
    if policy.get('worker_commands') != expected:
        reject('policy.worker_commands', policy.get('worker_commands'))
    workspace = str(root / 'state/worktrees/t081-capability' / (task + '-a1'))
    argv = policy['argv']
    if argv[argv.index('-C') + 1] != workspace:
        reject('policy.argv.workspace', argv)
    checked = {}
    for label, body in [('ROLE-BODY', role), ('FIRST-TURN', first_turn)]:
        commands = [shlex.split(line.strip()) for line in body.splitlines()
                    if line.strip().startswith(("'git' ", 'git '))]
        if commands != expected:
            reject(label, commands)
        checked[label] = commands
    return {'status': 'PASS', 'run_root': str(root), 'task': task,
            'commands': expected, 'text_checks': checked,
            'oracle': '调用者固定 run_root/task；OID 来自原始独立夹具 fixture.json，预期不取自 policy'}
