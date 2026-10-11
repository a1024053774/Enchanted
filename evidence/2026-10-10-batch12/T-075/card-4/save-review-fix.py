"""Freeze the three-file review fix and preserve checks for controller approval."""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
evidence = Path(__file__).resolve().parent
root = evidence.parents[3]
before = evidence / 'review-candidate-01'
output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(root / 'workbench/tests'))
from command_evidence import CommandLog

def files(directory):
    return {str(path.relative_to(directory)): path.read_bytes() for path in (directory / 'workbench').rglob('*')
            if path.is_file() and not any(part in {'node_modules', '__pycache__', '.DS_Store'} for part in path.parts)}

old, new = files(before), files(root)
changed = sorted(name for name in old.keys() | new.keys() if old.get(name) != new.get(name))
assert changed == ['workbench/README.md', 'workbench/check-cache.mjs', 'workbench/tests/test_install_cache.mjs'], changed
patch = []
for name in changed:
    previous = old.get(name, b'').decode('utf-8').splitlines(keepends=True)
    current = new[name].decode('utf-8').splitlines(keepends=True)
    patch.extend(difflib.unified_diff(previous, current, fromfile='a/' + name if name in old else '/dev/null', tofile='b/' + name))
    target = output / 'files' / name; target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / name, target)
(output / 'changes.diff').write_text(''.join(patch), encoding='utf-8')
commands = CommandLog(output)
for argv in [['git', 'diff', '--check'], ['node', '--check', 'workbench/check-cache.mjs'],
             ['node', '--check', 'workbench/tests/test_install_cache.mjs'],
             ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.']]:
    result = commands.run(argv, cwd=root)
    assert result.returncode == 0, result.evidence
value = {'status': 'INCOMPLETE', 'reason': '待主控审修复 diff 后提交', 'review_status': 'FAIL',
         'changed_workbench_files': changed, 'other_workbench_files_unchanged': True,
         'fix_validation': 'review-cache-green-01/probe/results.json: 4/4 PASS',
         'model_turns_total': 3, 'model_turns_added': 0, 'commands': commands.entries,
         'regenerate_argv': [sys.executable, '-B', str(Path(__file__).resolve()), '--output', str(output) + '-new']}
(output / 'receipt.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': value['status'], 'changed': changed, 'checks': 'PASS', 'receipt': str(output / 'receipt.json')}, ensure_ascii=False))
