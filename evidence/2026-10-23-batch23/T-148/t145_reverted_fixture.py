"""Run unchanged T-145 E2E against HEAD with only its original product fix reverted.

Keep T-141 startup semantics: an older whole-tree revision would reject the new
receiver's native ready packet before the mouse assertions can run.
"""
import json
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
import scripted_claude

original_source_tree = scripted_claude.source_tree
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
revert_command = ['git', 'diff', '7494d167c^', '7494d167c', '--', 'workbench/src/panes.ts']
patch = subprocess.check_output(revert_command, cwd=ROOT, text=True)
summary = Path(sys.argv[sys.argv.index('--summary') + 1])


def reverted_source_tree(fixture, revision=None, patches=()):
    if revision or patches:
        raise ValueError('Full T-145 reversal cannot be combined with another source variant')
    source = original_source_tree(fixture, revision=candidate)
    result = subprocess.run(['git', 'apply', '--reverse', '--verbose', '-'], cwd=source,
                            input=patch, text=True, capture_output=True)
    metadata = dict(candidate=candidate, reverted_commit='7494d167c', source=str(source),
                    patch_command=revert_command, apply_exit=result.returncode,
                    stdout=result.stdout, stderr=result.stderr)
    summary.with_suffix('.revert.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary.with_suffix('.revert.patch').write_text(patch, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('T-145 reversal failed: ' + result.stderr)
    return source


scripted_claude.source_tree = reverted_source_tree
runpy.run_path(str(ROOT / 'workbench/tests/test_t145_mouse_reports_e2e.py'), run_name='__main__')
