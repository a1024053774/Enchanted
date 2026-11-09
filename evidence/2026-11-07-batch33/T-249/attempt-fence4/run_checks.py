#!/usr/bin/env python3
"""复验本卡三条机械条件；仅在当前 attempt 已授权的请求目录创建临时夹具。"""
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
REQUEST = Path(os.environ['A2A_REQUEST_DIR']).resolve(strict=True)
NODE = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
CHECKS = {
    'acceptance': ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py'],
    'host': [NODE, '--test', 'workbench/tests/test_t249_git_host.mjs'],
    'outside-safety': ['/usr/bin/python3', 'workbench/tests/test_t249_outside_safety.py'],
}


def run(name, argv):
    # x 模式防止重放时覆盖首次结果；重放前须另存完整证据目录。
    with (OUT / (name + '.txt')).open('x', encoding='utf-8') as log:
        tmp = Path(tempfile.mkdtemp(prefix='t249-fence4-' + name + '-', dir=REQUEST))
        env = dict(os.environ, TMPDIR=str(tmp), TMP=str(tmp), TEMP=str(tmp),
                   PATH=str(Path(NODE).parent) + os.pathsep + os.environ['PATH'],
                   PYTHONDONTWRITEBYTECODE='1')
        log.write('cwd: ' + str(ROOT) + '\nTMPDIR: ' + str(tmp) + '\n$ ' + shlex.join(argv) + '\n')
        log.flush()
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        log.write('\nexit: ' + str(result.returncode) + '\n')
    files = [p for p in tmp.rglob('*') if p.is_file() and not p.is_symlink()]
    cleanup = dict(directory=str(tmp), time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   files=len(files), bytes=sum(p.stat().st_size for p in files), exit=result.returncode,
                   result='PASS' if result.returncode == 0 else 'INCOMPLETE')
    with (OUT / (name + '-cleanup.json')).open('x', encoding='utf-8') as f:
        json.dump(cleanup, f, ensure_ascii=False, indent=2)
        f.write('\n')
    shutil.rmtree(tmp)
    print(name + ': exit=' + str(result.returncode) + ', temporary_directory_removed=' + str(not tmp.exists()), flush=True)
    return result.returncode


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda item: run(*item), CHECKS.items()))
    raise SystemExit(0 if all(code == 0 for code in results) else 1)
