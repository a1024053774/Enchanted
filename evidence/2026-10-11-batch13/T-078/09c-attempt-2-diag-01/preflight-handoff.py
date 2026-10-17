"""Read-only ownership and syntax checks before the worker's direct commit."""
import argparse
import json
from pathlib import Path
import subprocess

SOURCE = Path(__file__).resolve().parents[4]
BASE = 'evidence/2026-10-11-batch13/T-078/'
OWNED = [BASE + name for name in [
    'RESULTS.md', '09c-attempt-2-materials-02/stage-a-approval.json',
    '09c-attempt-2-materials-02/owner.json', '09c-attempt-2-materials-02/owner-identity.json',
    '09c-stage-a-02', '09c-c2-b1-ideation-01-dry-run', '09c-c2-b1-ideation-01',
    '09c-c2-b1-ideation-p1-01', '09c-c2-b1-executor-01-dry-run',
    '09c-c2-b1-executor-01', '09c-c2-b1-executor-p1-01',
    '09c-c2-preparation-01', '09c-attempt-2-diag-01', '09c-attempt-2-closeout-materials-01']]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE)


def owns(path):
    return any(path == root or path.startswith(root + '/') for root in OWNED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), args.output
    assert owns(str(args.output.resolve().relative_to(SOURCE)))
    head = git('rev-parse', 'HEAD').decode().strip()
    assert head == '8226f35951b31a98ee9df07593b61b77edd2d294', head
    assert not git('diff', '--cached', '--name-only'), 'staged work must be empty before this preflight'
    subprocess.run(['git', 'diff', '--check'], cwd=SOURCE, check=True)
    for path in OWNED: assert (SOURCE / path).exists(), path
    rows = git('status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0')
    paths = []
    for row in rows:
        if not row: continue
        status = row[:2].decode(); path = row[3:].decode()
        assert status in [' M', '??'], (status, path)
        assert owns(path), ('Unowned work; no mutation', path)
        item = SOURCE / path
        assert item.is_file() and not item.is_symlink(), path
        assert item.stat().st_size <= 5 * 1024 * 1024, ('external archive required', path)
        assert item.name not in ['auth.json', 'credentials.json', 'operator.json'] and not item.name.startswith('state.sqlite3'), path
        paths.append(path)
    assert not git('diff', head, '--', 'workbench', 'acceptance', 'scripts')
    result = {'status':'PASS','HEAD':head,'staged_before':[], 'allowlist':OWNED,
              'owned_paths':paths,'owned_count_before_output':len(paths),
              'output_is_owned':True,'simulated_final_status':[],
              'simulation':'all status paths plus this new output are covered by the exact directory/file git-add list; no git mutation',
              'product_and_runtime_changes':0,'process_classification':'UNKNOWN','parity_green':'INCOMPLETE'}
    with args.output.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','HEAD':head,'owned_count_before_output':len(paths),
          'staged_before':[],'simulated_final_status':[],'actual_git_mutations':0}))


if __name__ == '__main__': main()
