"""复现独立审查的单一缺陷：详情完全断开，三条机械检查仍通过。只改临时副本。"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = Path('/Users/luckye/Documents/Code/a2a')
CANDIDATE = '1e1e5ef7bfb1faa8a0af8df064ac6834e2579a93'
OUT = Path(__file__).resolve().parent / 'no-details-reproduction'
OUT.mkdir(exist_ok=False)
FIXTURE = Path(tempfile.mkdtemp(prefix='t249-no-details-repro-', dir='/private/tmp'))
COMMANDS = [
    ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py'],
    ['/opt/homebrew/Cellar/node/26.5.0/bin/node', '--test', 'workbench/tests/test_t249_git_host.mjs'],
    ['/usr/bin/python3', 'workbench/tests/test_t249_outside_safety.py'],
]
report = {'candidate': CANDIDATE, 'fixture': str(FIXTURE), 'status': 'INCOMPLETE', 'runs': [],
          'requirement': 'T-249 要做的第3条：点击提交打开详情，点击文件看 diff；删除整个详情路径应被必经验收拒绝。'}
try:
    archive = subprocess.Popen(['git', '-C', str(REPO), 'archive', CANDIDATE,
                                'workbench/app', 'workbench/tests', 'acceptance/T-249'], stdout=subprocess.PIPE)
    extract = subprocess.run(['tar', '-x', '-C', str(FIXTURE)], stdin=archive.stdout)
    archive.stdout.close()
    assert archive.wait() == 0 and extract.returncode == 0
    temp = FIXTURE / 'tmp'
    temp.mkdir()
    env = dict(os.environ, TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp), PYTHONDONTWRITEBYTECODE='1',
               PATH='/opt/homebrew/Cellar/node/26.5.0/bin:' + os.environ.get('PATH', ''))
    target = FIXTURE / 'workbench/app/panels/GitGraphPanel.tsx'
    original = target.read_text()
    before = '{selectedCommit && <CommitDetails'
    after = '{false && selectedCommit && <CommitDetails'
    assert original.count(before) == 1
    report['mutation'] = {'path': str(target.relative_to(FIXTURE)), 'before': before, 'after': after}
    for variant in ('baseline', 'no-details'):
        if variant == 'no-details':
            target.write_text(original.replace(before, after))
        for index, argv in enumerate(COMMANDS, 1):
            p = subprocess.run(argv, cwd=FIXTURE, env=env, capture_output=True, text=True, timeout=120)
            record = {'variant': variant, 'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
            (OUT / f'{variant}-{index}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
            report['runs'].append({'variant': variant, 'check': index, 'exit': p.returncode})
            assert p.returncode == 0, f'本次未复现审查结果：{variant}/{index} exit={p.returncode}'
    target.write_text(original)
    report['status'] = 'PASS（审查反例已复现）；FAIL（现有检查的详情覆盖）'
    report['observation'] = '未变异与 no-details 的三条机械检查均退出0；未运行真实窗口，不声称原候选详情实际失效。'
finally:
    files = [p for p in FIXTURE.rglob('*') if p.is_file() and not p.is_symlink()]
    report['cleanup'] = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'directory': str(FIXTURE),
                         'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}
    (OUT / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    shutil.rmtree(FIXTURE)
    report['cleanup']['removed'] = not FIXTURE.exists()
    (OUT / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
