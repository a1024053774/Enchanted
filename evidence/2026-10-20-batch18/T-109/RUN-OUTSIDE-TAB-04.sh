#!/bin/zsh
# Replay the reviewer's native Tab journey against the newly committed candidate.
# This is an author rerun, not a new independent review verdict.
set -euo pipefail
TASK_ROOT=/Users/luckye/Documents/Code/a2a-wt-t109
TASK_DIST=${T109_ELECTRON_DIST:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
python3 - "$TASK_ROOT" "$TASK_DIST" <<'PYTHON'
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback

repo, dist = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
output = repo / 'evidence/2026-10-20-batch18/T-109/outside-tab-04.json'
assert not output.exists(), 'Use a new numbered summary; preserve the previous run'
root = Path(tempfile.mkdtemp(prefix='t109-tab04-', dir='/private/tmp')).resolve()
tree = root / 'candidate'
env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
    env.pop(key, None)
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
report = dict(status='INCOMPLETE', task='T-109', attempt='a1', model_calls=0, commands=[],
              scope='New committed product and formal tests; private driver adds the reviewer native-Tab journey')

def run(argv, cwd=tree, timeout=180):
    value = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    report['commands'].append(dict(argv=list(map(str, argv)), exit=value.returncode))
    assert value.returncode == 0, (argv, value.stdout[-2500:], value.stderr[-2000:])
    return value.stdout

try:
    candidate = run(['git', 'rev-parse', 'HEAD'], cwd=repo).strip()
    assert not run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'workbench', 'scripts'], cwd=repo).strip(), 'Commit the acceptance fix before this rerun'
    report['candidate'] = candidate
    tree.mkdir()
    archive = subprocess.check_output(['git', 'archive', candidate, 'workbench', 'scripts'], cwd=repo, env=env)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree)
    shutil.copytree(repo / 'workbench/node_modules', tree / 'workbench/node_modules', symlinks=False)
    # Private repository only; all inherited Git routing has been removed.
    run(['git', '-c', 'core.hooksPath=/dev/null', 'init', str(tree)])
    run(['git', 'fetch', '--depth=1', '--no-tags', str(repo), candidate, '6411bdff8482ba47da207efa6a295a12666222aa'])
    run(['git', 'update-ref', 'HEAD', candidate])
    run(['git', 'read-tree', candidate])
    driver = tree / 'workbench/tests/t107_sidebar_driver.mjs'
    original = driver.read_text(encoding='utf-8')
    marker = "          value = await window.webContents.executeJavaScript(`(()=>{\n            const n=[...document.querySelectorAll('button[data-agent-toggle]')]"
    assert original.count(marker) == 1
    # Same bounded native Tab traversal as REVIEW-OUTSIDE-01.sh. It reaches
    # the real product button before the existing focus and Enter checks.
    tab = """          if (request.command === 'toggle-keyboard') {
            await window.webContents.executeJavaScript('document.activeElement?.blur()');
            let reached = false;
            for (let step = 0; step < 160; step++) {
              window.webContents.sendInputEvent({type:'keyDown',keyCode:'Tab'});
              window.webContents.sendInputEvent({type:'keyUp',keyCode:'Tab'});
              await new Promise(resolve => setTimeout(resolve, 20));
              const target = await window.webContents.executeJavaScript('document.activeElement?.dataset.agentToggle');
              if (target === request.target) { reached = true; log({stage:'independent-native-tab',target,steps:step+1}); break; }
            }
            if (!reached) throw new Error('Independent Tab traversal did not reach the product disclosure');
          }
"""
    driver.write_text(original.replace(marker, tab + marker), encoding='utf-8')
    run(['git', 'diff', '--exit-code', candidate, '--', 'workbench/src', 'workbench/app', 'scripts'])
    run(['python3', 'workbench/tests/run_t109_hierarchy.py', '--source', tree, '--electron-dist', dist,
         '--summary', root / 'electron-tab.json'], timeout=900)
    observed = json.loads((root / 'electron-tab.json').read_text(encoding='utf-8'))
    assert observed['status'] == 'PASS' and observed['title_invariance']['status'] == 'PASS', observed
    assert observed['source_head'] == candidate and observed['source_changes'] == [' M workbench/tests/t107_sidebar_driver.mjs'], observed
    report.update(status='PASS', electron=observed)
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc(), retained_fixture=str(root))
if report['status'] == 'PASS':
    shutil.rmtree(root)
with output.open('x', encoding='utf-8') as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
    file.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
PYTHON
