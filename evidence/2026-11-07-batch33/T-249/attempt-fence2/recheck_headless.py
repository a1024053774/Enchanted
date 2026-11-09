"""从仓库根运行：TMPDIR=$A2A_REQUEST_DIR python3 此脚本。
在临时源码副本中复跑冻结验收和两个已知坏变异，不改原验收或工作区实现。
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).parent / ('headless-' + datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
OUTPUT.mkdir()
mutants = {
    'green': None,
    'parents': ("parents: parents ? parents.split(' ') : [],", "parents: parents ? parents.split(' ').reverse() : [],"),
    'order': ('  return commits;', '  return commits.reverse();'),
}
results = {}
for name, patch in mutants.items():
    with tempfile.TemporaryDirectory(prefix='t249-counterfactual-') as directory:
        source = Path(directory)
        for path in ['workbench/package.json', 'workbench/app/gitHost.ts', 'workbench/app/panels/gitGraphModel.ts',
                     'workbench/app/panels/gitGraphCli.ts', 'acceptance/T-249/check_git_graph.py']:
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        if patch:
            target = source / 'workbench/app/panels/gitGraphModel.ts'
            text = target.read_text(encoding='utf-8')
            assert text.count(patch[0]) == 1
            target.write_text(text.replace(*patch), encoding='utf-8')
        command = ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py']
        run = subprocess.run(command, cwd=source, text=True, capture_output=True)
        (OUTPUT / (name + '.txt')).write_text('$ ' + ' '.join(command) + '\n' + run.stdout + run.stderr +
            f'\nexit={run.returncode}\n', encoding='utf-8')
        expected = '每行父提交' if name == 'parents' else '提交顺序'
        valid = run.returncode == 0 if not patch else run.returncode == 1 and any(
            line.startswith('FAIL') and expected in line for line in run.stdout.splitlines())
        results[name] = dict(exit=run.returncode, expected_result=valid)
        files = [p.stat().st_size for p in source.rglob('*') if p.is_file()]
        (OUTPUT / (name + '-cleanup.json')).write_text(json.dumps(dict(directory=directory, files=len(files),
            bytes=sum(files), result=results[name]), indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, ensure_ascii=False))
assert all(r['expected_result'] for r in results.values())
