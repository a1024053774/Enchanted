"""Preserve the T-078 handoff, then rebase onto the fixed T-082 main revision."""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE = Path(__file__).resolve().parent
EVIDENCE = 'evidence/2026-10-11-batch13/T-078'
STAGE_PATHS = [
    EVIDENCE + '/RESULTS.md',
    EVIDENCE + '/09b-a14-cleanup-owner.json',
    EVIDENCE + '/redact-a14-scene.py',
    EVIDENCE + '/09b-startup-receipt-entry-01',
    EVIDENCE + '/rebase-main-3',
]
DIRECTORIES = {STAGE_PATHS[3], STAGE_PATHS[4]}
ROUTING = ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
           'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def verify_main(expected):
    subprocess.run(['git', 'merge-base', '--is-ancestor', expected['target'], 'main'], cwd=ROOT, check=True)
    protected = ['workbench/', 'acceptance/', 'scripts/']
    assert not git('log', '--format=%H', expected['target'] + '..main', '--', *protected), 'Code changed after fixed target'
    assert not git('diff', expected['target'] + '..main', '--', *protected), 'Code differs from fixed target'
    return git('rev-parse', 'main')


def owned(path):
    return any(path == item or (item in DIRECTORIES and path.startswith(item + '/')) for item in STAGE_PATHS)


def preflight():
    assert BASE == ROOT / EVIDENCE / 'rebase-main-3'
    expected = json.loads((BASE / 'expected.json').read_bytes())
    assert expected['root'] == str(ROOT) and expected['branch'] == 'exec/t078'
    assert git('branch', '--show-current') == expected['branch']
    assert git('rev-parse', 'HEAD') == expected['head'], 'HEAD changed; no mutation'
    main = verify_main(expected)
    assert git('merge-base', expected['head'], expected['target']) == expected['merge_base']
    assert not any(name in os.environ for name in ROUTING), 'Unexpected Git routing environment'
    for name, value in expected['startup_identity'].items():
        assert os.environ.get(name) == value, ('Original worker startup identity required', name)
    for name in ['rebase-merge', 'rebase-apply']:
        assert not Path(git('rev-parse', '--git-path', name)).exists(), ('Rebase already active', name)
    assert not git('diff', '--cached', '--name-only'), 'Index must be empty before handoff'
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    rows = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT).decode('utf-8').split('\0')
    dirty = []
    for row in rows:
        if not row:
            continue
        assert row[:2] in ['??', ' M'], ('Unexpected change type; no mutation', row)
        path = row[3:]
        assert owned(path), ('Unowned work; no mutation', path)
        dirty.append({'status': row[:2], 'path': path})
    assert dirty, 'No handoff changes'
    for path in STAGE_PATHS:
        full = ROOT / path
        assert full.exists() and not full.is_symlink(), ('Missing git add path', path)
        assert full.is_dir() == (path in DIRECTORIES), ('Unexpected git add path type', path)
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', path], cwd=ROOT)
        assert ignored.returncode == 1, ('Ignored git add path', path)
    # These are the exact paths passed to git add; no file is generated in the
    # worktree after this commit. Runtime logs live in a new /private/tmp root.
    remaining = [row['path'] for row in dirty if not owned(row['path'])]
    assert not remaining, ('Simulated final worktree is not clean', remaining)
    proof = json.loads((ROOT / EVIDENCE / '09b-startup-receipt-entry-01/result.json').read_bytes())
    assert proof['status'] == 'PASS' and proof['suite'] == 'entry'
    candidate = next(run for run in proof['runs'] if run['mode'] == 'candidate')
    mutant = next(run for run in proof['runs'] if run['mode'] == 'm5')
    assert candidate['checks'] == 14 and candidate['pre_release_refreshes'] == 6
    assert mutant['failure']['step'] == 'approved startup keys keep the pending inbox queued'
    assert mutant['failure']['observed'] == 'delivered' and mutant['failure']['expected'] == 'queued'
    owner = json.loads((ROOT / EVIDENCE / '09b-a14-cleanup-owner.json').read_bytes())
    assert owner['root'] == '/private/tmp/t078-2-09b-run-gbxz0tyb'
    for path in [BASE / 'prepare-and-rebase.py', BASE / 'rebase.py', ROOT / EVIDENCE / 'redact-a14-scene.py']:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    results = (ROOT / EVIDENCE / 'RESULTS.md').read_text(encoding='utf-8')
    assert '## 主控 #316：先变基 T-082，再回收 A-14／准备 A-15' in results
    return expected, {'status': 'PASS', 'mode': 'check-only', 'HEAD': expected['head'],
        'target': expected['target'], 'main': main, 'merge_base': expected['merge_base'],
        'dirty_paths': len(dirty), 'git_add_paths': STAGE_PATHS,
        'simulated_remaining_paths': remaining, 'index_empty': True,
        'syntax': 'PASS', 'preserved_entry_candidate_checks': 14,
        'scope': 'Read-only Git, identity, evidence, ownership and syntax checks; no commit/rebase/services'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    expected, report = preflight()
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    if args.check_only:
        return 0
    subprocess.run(['git', 'add', '--', *STAGE_PATHS], cwd=ROOT, check=True)
    staged = git('diff', '--cached', '--name-only', '-z').split('\0')
    assert staged and all(owned(path) for path in staged if path), 'Unexpected staged path'
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    subprocess.run(['git', 'diff', '--cached', '--stat'], cwd=ROOT, check=True)
    subprocess.run(['git', 'commit', '-m', 'docs(T-078): preserve startup receipts and third main rebase handoff'], cwd=ROOT, check=True)
    before = git('rev-parse', 'HEAD')
    assert git('rev-parse', 'HEAD^') == expected['head']
    assert not git('status', '--porcelain=v1', '--untracked-files=all'), 'Worktree must be clean after handoff commit'
    log = Path(tempfile.mkdtemp(prefix='t078-rebase-main-3-', dir='/private/tmp'))
    inputs = {**expected, 'before': before, 'backup_ref': 'backup/t078-before-main-3-' + before[:12]}
    (log / 'inputs.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    relative = str((BASE / 'rebase.py').relative_to(ROOT))
    (log / 'rebase.py').write_bytes(subprocess.check_output(['git', 'show', before + ':' + relative], cwd=ROOT))
    dropped = [name for name in os.environ if name.startswith('A2A_') or name == 'CODEX_THREAD_ID'
        or name in ['GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS'] or name.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_'))]
    child = {name: value for name, value in os.environ.items() if name not in dropped}
    (log / 'removed-session-env-names.json').write_text(json.dumps(sorted(dropped), indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'phase': 'handoff-commit', 'revision': before,
        'log': str(log), 'next': 'fixed-target rebase; stop at every conflict'}, ensure_ascii=False), flush=True)
    return subprocess.run([sys.executable, '-B', str(log / 'rebase.py'), '--inputs', str(log / 'inputs.json')], cwd=ROOT, env=child).returncode


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'BLOCKED', 'error': repr(error), 'traceback': traceback.format_exc(),
            'scope': 'Preserve Git state; no automatic retry/abort'}, ensure_ascii=False))
        raise SystemExit(1)
