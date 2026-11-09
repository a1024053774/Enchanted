#!/usr/bin/env python3
"""重跑卡内三项条件；输出目录须不存在，保留命令、退出码与本次夹具清理状态。"""
import argparse, datetime, json, os, pathlib, shutil, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[5]
p = argparse.ArgumentParser(); p.add_argument('--output', type=pathlib.Path, required=True); args = p.parse_args()
out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
owned = pathlib.Path(tempfile.mkdtemp(prefix='t249-v9-checks-', dir=os.environ['A2A_REQUEST_DIR']))
node = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
env = dict(os.environ, TMPDIR=str(owned), PYTHONDONTWRITEBYTECODE='1')
env['PATH'] = str(pathlib.Path(node).parent) + ':' + env.get('PATH', '')
rows = []
try:
    for name, command in [('acceptance',['/usr/bin/python3','acceptance/T-249/check_git_graph.py']),
      ('host',[node,'--test','workbench/tests/test_t249_git_host.mjs']),
      ('outside-safety',['/usr/bin/python3','workbench/tests/test_t249_outside_safety.py'])]:
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        (out/(name+'.txt')).write_bytes(result.stdout+result.stderr)
        rows.append(dict(name=name, command=command, cwd=str(ROOT), start=started, exit=result.returncode))
        print(name, 'PASS' if result.returncode==0 else 'INCOMPLETE', flush=True)
finally:
    sizes = [x.stat().st_size for x in owned.rglob('*') if x.is_file() and not x.is_symlink()]
    report = dict(results=rows, environment=dict(TMPDIR=str(owned), PYTHONDONTWRITEBYTECODE='1',
      PATH_prefix=str(pathlib.Path(node).parent)), versions=dict(node=subprocess.check_output([node,'--version'],text=True).strip(),
      git=subprocess.check_output(['git','--version'],text=True).strip()),
      cleanup=dict(directory=str(owned), time=datetime.datetime.now(datetime.timezone.utc).isoformat(), files=len(sizes), bytes=sum(sizes)))
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.rmtree(owned)
    report['cleanup']['removed'] = not owned.exists()
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if len(rows)==3 and all(row['exit']==0 for row in rows) else 1)
