"""Worker 可运行的小检查：不启动 Electron、后台或 ps；文本结果不覆盖旧运行。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
NODE = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
C = '18c108fcaed1c4ecf51831f2272578a3b09427be'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--tmp-root', type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
owned = Path(tempfile.mkdtemp(prefix='t249-local-', dir=args.tmp_root))
env = dict(os.environ, TMPDIR=str(owned), PYTHONDONTWRITEBYTECODE='1')
env['PATH'] = str(Path(NODE).parent) + ':' + env.get('PATH', '')
results = []


def run(name, command, cwd=ROOT, expected=None):
    p = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    (output / (name + '.txt')).write_text('$ ' + repr(command) + '\n' + p.stdout + p.stderr, encoding='utf-8')
    ok = p.returncode == 0 if expected is None else (p.returncode != 0 and expected in p.stdout + p.stderr)
    results.append(dict(name=name, command=command, cwd=str(cwd), exit=p.returncode, expected_failure=expected, ok=ok))
    print(name, 'PASS' if ok else 'INCOMPLETE', flush=True)


try:
    run('host', [NODE, '--test', 'workbench/tests/test_t249_git_host.mjs'])
    run('acceptance', ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py'])
    run('outside-safety', ['/usr/bin/python3', 'workbench/tests/test_t249_outside_safety.py'])
    for name, expected, pattern in [
        ('old-C', 'untracked content missing:', 'untracked content diff'),
        ('empty-binary-C', 'Invalid diff base', 'untracked empty and binary'),
        ('unsafe-options', 'Missing expected rejection', 'no-index boundary rejects every extra'),
        ('unsafe-paths', 'Missing expected rejection', 'no-index boundary rejects directories'),
        ('force-text', 'non-text file manufactured text hunks', 'untracked empty and binary'),
    ]:
        source = owned / name
        paths = ['workbench/app/gitHost.ts', 'workbench/app/panels/gitGraphModel.ts', 'workbench/tests/test_t249_git_host.mjs']
        for path in paths:
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        if name.endswith('-C'):
            for path in paths[:2]:
                (source / path).write_bytes(subprocess.check_output(['git', 'show', C + ':' + path], cwd=ROOT))
        else:
            host = source / paths[0]
            text = host.read_text(encoding='utf-8')
            old, new = {
                'unsafe-options': ("  if (!readAllowed(argv)) throw", "  if (argv[0] === 'diff' && argv[1] === '--no-index' && argv.some(a => a.startsWith('--out'))) return { code: 0, stdout: '', stderr: '' };\n  if (!readAllowed(argv)) throw"),
                'unsafe-paths': ('  if (noIndex) {', '  if (false && noIndex) {'),
                'force-text': ('...noPrograms, ...argv.slice(1)', "...noPrograms, ...(noIndex ? ['--text'] : []), ...argv.slice(1)"),
            }[name]
            assert text.count(old) == 1
            host.write_text(text.replace(old, new), encoding='utf-8')
            (output / (name + '-mutation.json')).write_text(json.dumps(dict(path=paths[0], before=old, after=new), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        run(name, [NODE, '--test', '--test-name-pattern=' + pattern, 'workbench/tests/test_t249_git_host.mjs'], cwd=source, expected=expected)
finally:
    sizes = [p.stat().st_size for p in owned.rglob('*') if p.is_file() and not p.is_symlink()]
    report = dict(results=results, versions=dict(node=subprocess.check_output([NODE, '--version'], text=True).strip(),
        git=subprocess.check_output(['git', '--version'], text=True).strip()), cleanup=dict(directory=str(owned),
        time=datetime.datetime.now(datetime.timezone.utc).isoformat(), files=len(sizes), bytes=sum(sizes)))
    (output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.rmtree(owned)
    report['cleanup']['removed'] = not owned.exists()
    (output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
raise SystemExit(0 if all(r['ok'] for r in results) else 1)
