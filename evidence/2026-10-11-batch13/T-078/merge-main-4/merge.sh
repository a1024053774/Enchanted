#!/bin/sh
# 主控 #340：只开始固定目标合并；不提交、不测试、不启动现场。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -B - <<'PY'
import subprocess
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
assert git('rev-parse', 'HEAD') == 'acf8b8a3f695b38ddd8e424fce2078d256180e9c'
assert git('branch', '--show-current') == 'exec/t078'
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
assert subprocess.run(['git', 'rev-parse', '-q', '--verify', 'MERGE_HEAD'], capture_output=True).returncode != 0
assert git('rev-parse', '6d85482ff') == '6d85482ff6f34b55d0b6fb1dd3dc5c020608d783'
paths = git('ls-files', '--others', '--exclude-standard').splitlines()
prefix = 'evidence/2026-10-11-batch13/T-078/'
assert all(path.startswith((prefix + 'merge-main-4/', prefix + 'rev2-tools-outside-01/')) for path in paths), paths
print('PASS: fixed HEAD/target/branch; tracked and staged clean; all untracked paths preserved')
PY
execution=evidence/2026-10-11-batch13/T-078/merge-main-4/execution-01
mkdir "$execution"
if git merge --no-ff --no-commit 6d85482ff6f34b55d0b6fb1dd3dc5c020608d783 >"$execution/stdout.txt" 2>"$execution/stderr.txt"; then
  code=0
else
  code=$?
fi
cat "$execution/stdout.txt"
cat "$execution/stderr.txt"
python3 -B - "$execution" "$code" <<'PY'
import json, subprocess, sys
from pathlib import Path
def git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    return {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
result = {'status': 'MERGE_PENDING_WORKER_COMMIT' if sys.argv[2] == '0' else 'INCOMPLETE',
          'merge_exit_code': int(sys.argv[2]), 'HEAD': git('rev-parse', 'HEAD'),
          'MERGE_HEAD': git('rev-parse', '-q', '--verify', 'MERGE_HEAD'),
          'conflicts': git('diff', '--name-only', '--diff-filter=U'),
          'worktree': git('status', '--short'), 'commit_performed': False,
          'tests_run': False, 'scene_started': False,
          'next': 'Worker resolves any conflicts, uses direct git add/git commit with original identity, then binds materials.'}
(Path(sys.argv[1]) / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'worktree'}, ensure_ascii=False))
PY
exit "$code"
