#!/usr/bin/env python3
"""本次修复的三条完成条件；只创建并清理本 attempt 请求目录里的自有临时根。"""
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
NODE = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
CHECKS = [('acceptance', ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py']),
          ('host', [NODE, '--test', 'workbench/tests/test_t249_git_host.mjs']),
          ('outside-safety', ['/usr/bin/python3', 'workbench/tests/test_t249_outside_safety.py'])]


def run(item):
    name, argv = item
    with (OUT / (name + '-green.txt')).open('x', encoding='utf-8') as log:
        tmp = Path(tempfile.mkdtemp(prefix='t249-details-' + name + '-', dir=os.environ['A2A_REQUEST_DIR']))
        env = dict(os.environ, TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp), PYTHONDONTWRITEBYTECODE='1',
                   PATH=str(Path(NODE).parent) + os.pathsep + os.environ['PATH'])
        log.write('cwd: ' + str(ROOT) + '\nTMPDIR: ' + str(tmp) + '\nargv: ' + json.dumps(argv) + '\n')
        log.flush()
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        log.write('\nexit: ' + str(result.returncode) + '\n')
    sizes = [p.stat().st_size for p in tmp.rglob('*') if p.is_file() and not p.is_symlink()]
    summary = dict(name=name, argv=argv, exit=result.returncode, directory=str(tmp),
                   time=datetime.datetime.now(datetime.timezone.utc).isoformat(), files=len(sizes), bytes=sum(sizes))
    with (OUT / (name + '-cleanup.json')).open('x', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write('\n')
    shutil.rmtree(tmp)
    print(name + ': exit=' + str(result.returncode) + ', temporary_directory_removed=' + str(not tmp.exists()), flush=True)
    return result.returncode


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, CHECKS))
    raise SystemExit(0 if all(code == 0 for code in results) else 1)
