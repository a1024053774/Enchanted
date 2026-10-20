"""Record repository search commands and complete output; do not infer a verdict."""
import argparse
import json
import os
from pathlib import Path
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, type=Path)
parser.add_argument('--summary', required=True, type=Path)
args = parser.parse_args()
assert not args.summary.exists(), 'Preserve earlier search results'
source = args.source.resolve()
env = {key: value for key, value in os.environ.items() if key not in ('GIT_DIR', 'GIT_WORK_TREE')}
env['LC_ALL'] = 'C'
commands = [
    ['rg', '--hidden', '-n', '-i',
     r'worker_executor_mismatch|(?:effort|model|reasoning)[^\n]{0,120}(?:===|!==|choices|includes|Literals)|(?:choices|Literals)[^\n]{0,120}(?:EFFORT|MODEL|THINKING)',
     '.', '--glob', '!.git', '--glob', '!**/node_modules/**', '--glob', '!evidence/**', '--glob', '!**/package-lock.json'],
    ['rg', '-n', 'choices|effort|model', 'scripts/launch-worker'],
    ['rg', '--hidden', '-n', 'xhigh|默认见设置|默认见角色设置',
     'workbench/README.md', '.project-map/roles', 'AGENTS.md'],
]
records = []
for argv in commands:
    result = subprocess.run(argv, cwd=source, env=env, capture_output=True, text=True)
    records.append(dict(argv=argv, cwd=str(source), exit=result.returncode,
                        stdout=result.stdout, stderr=result.stderr))
    assert result.returncode in (0, 1), records[-1]
report = dict(status='RECORDED', source=str(source), commands=records,
              limitation='Text matches require source inspection; historical decisions and identity comparisons are not fixed-value rejection policies')
args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], summary=str(args.summary))))
