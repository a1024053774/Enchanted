"""Rebase the fixed T-078 handoff and retain all conflicts for manual resolution."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import traceback

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inputs', type=Path, required=True)
args = parser.parse_args()
expected = json.loads(args.inputs.read_bytes())
root = Path(expected['root'])
log = args.inputs.parent
record = {'status': 'INCOMPLETE', 'inputs': expected,
          'scope': 'Git rebase only; no automatic conflict resolution, retry, abort or services'}


def git(*argv):
    return subprocess.check_output(['git', *argv], cwd=root, text=True).strip()


def verify_main():
    subprocess.run(['git', 'merge-base', '--is-ancestor', expected['target'], 'main'], cwd=root, check=True)
    protected = ['workbench/', 'acceptance/', 'scripts/']
    assert not git('log', '--format=%H', expected['target'] + '..main', '--', *protected), 'Code changed after fixed target'
    assert not git('diff', expected['target'] + '..main', '--', *protected), 'Code differs from fixed target'
    return git('rev-parse', 'main')


def save():
    (log / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


save()
try:
    assert root == Path('/Users/luckye/Documents/Code/a2a-wt-t078')
    assert expected['target'] == '0e6c2b833f6da64243f71d670ea45bb9116fda4d'
    assert git('branch', '--show-current') == expected['branch'] == 'exec/t078'
    assert git('rev-parse', 'HEAD') == expected['before']
    assert git('rev-parse', 'HEAD^') == expected['head']
    assert git('merge-base', expected['before'], expected['target']) == expected['merge_base']
    assert expected['backup_ref'] == 'backup/t078-before-main-3-' + expected['before'][:12]
    assert not git('status', '--porcelain=v1', '--untracked-files=all'), 'Dirty worktree; no automatic workaround'
    for name in ['rebase-merge', 'rebase-apply']:
        assert not Path(git('rev-parse', '--git-path', name)).exists(), 'Rebase already active'
    assert not any(name.startswith('A2A_') or name == 'CODEX_THREAD_ID'
        or name in ['GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS']
        or name.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')) for name in os.environ)
    assert not any(name in os.environ for name in ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE',
        'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES'])
    record['main_before_rebase'] = verify_main()
    assert subprocess.run(['git', 'show-ref', '--verify', '--quiet', 'refs/heads/' + expected['backup_ref']], cwd=root).returncode == 1, 'Backup already exists'
    subprocess.run(['git', 'branch', expected['backup_ref'], expected['before']], cwd=root, check=True)
    (log / 'before-commits.txt').write_text(git('log', '--reverse', '--format=%H %s', expected['merge_base'] + '..' + expected['before']) + '\n', encoding='utf-8')
    record['main_at_rebase_command'] = verify_main()
    with (log / 'rebase.stdout.txt').open('xb') as stdout, (log / 'rebase.stderr.txt').open('xb') as stderr:
        completed = subprocess.run(['git', '-c', 'core.editor=true', '-c', 'sequence.editor=true', 'rebase', expected['target']], cwd=root, stdout=stdout, stderr=stderr)
    conflicts = git('diff', '--name-only', '--diff-filter=U').splitlines()
    record.update(exit_code=completed.returncode, HEAD=git('rev-parse', 'HEAD'), conflicts=conflicts,
                  worktree_status=git('status', '--porcelain=v1', '--untracked-files=all'))
    (log / 'conflicts.txt').write_text('\n'.join(conflicts) + '\n', encoding='utf-8')
    (log / 'worktree-status.txt').write_text(record['worktree_status'] + '\n', encoding='utf-8')
    if completed.returncode == 0:
        assert not conflicts and not record['worktree_status']
        subprocess.run(['git', 'merge-base', '--is-ancestor', expected['target'], 'HEAD'], cwd=root, check=True)
        record['status'] = 'PASS'
        (log / 'after-commits.txt').write_text(git('log', '--reverse', '--format=%H %s', expected['target'] + '..HEAD') + '\n', encoding='utf-8')
    else:
        stopped = subprocess.run(['git', 'rev-parse', 'REBASE_HEAD'], cwd=root, capture_output=True, text=True)
        record['REBASE_HEAD'] = stopped.stdout.strip() if stopped.returncode == 0 else None
except Exception as error:
    record.update(status='BLOCKED', error=repr(error), traceback=traceback.format_exc())
finally:
    save()
print(json.dumps({'status': record['status'], 'HEAD': record.get('HEAD'),
    'REBASE_HEAD': record.get('REBASE_HEAD'), 'conflicts': record.get('conflicts'),
    'log': str(log), 'backup_ref': expected['backup_ref'], 'error': record.get('error')}, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
