"""用安装包自带 Electron、源码与原生模块验证停止回收和归档中断恢复。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/a2a-t259-repair-20261108')
REVISION = '2083f72e4f43d6bc84be2ef57b5fef49f65e1bcb'
package = json.loads((OUT / 'package-02.log').read_text(encoding='utf-8').strip().splitlines()[-1])
app = Path(package['app'])
product = app / 'Contents/Resources/app'
manifest = json.loads((product / 'package.json').read_text(encoding='utf-8'))
assert manifest['a2a']['revision'] == REVISION
assert manifest['productName'] == 'Enchanted'
assert not (Path(package['slot']) / 'work').exists(), 'standard package must clean its build cache'
assert (SOURCE / 'workbench/src/gates/core.ts').read_bytes() == (product / 'src/gates/core.ts').read_bytes()
proxy = Path(tempfile.mkdtemp(prefix='t259-package-input-', dir='/private/tmp'))
# 只在本测试输入目录建只读入口，不在安装包或构建输出中加链接。
(proxy / 'workbench').symlink_to(product, target_is_directory=True)
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'COOP_'))}
env['ELECTRON_RUN_AS_NODE'] = '1'
env['ENCHANTED_HC_CACHE_DIR'] = '/Users/luckye/Documents/Code/hc-cache'
results = []
try:
    for scenario in ['stopped', 'resume-after-archive', 'resume-dirty']:
        summary = OUT / ('package-' + scenario + '-01.json')
        assert not summary.exists(), 'preserve earlier evidence'
        command = [str(app / 'Contents/MacOS/Enchanted'), str(SOURCE / 'workbench/tests/test_t259_preparing_reclaim.ts'),
                   str(proxy), str(summary), scenario]
        run = subprocess.run(command, cwd=proxy, env=env, text=True, capture_output=True, timeout=180)
        results.append(dict(command=command, exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr,
                            summary=str(summary)))
        if run.returncode:
            break
finally:
    record = dict(status='PASS' if len(results) == 3 and all(x['exit_code'] == 0 for x in results) else 'INCOMPLETE',
                  revision=REVISION, app=str(app), package=package, results=results,
                  boundary='packaged Electron runtime, packaged product code and node-pty; no GUI or model call',
                  cleanup=dict(directory=str(proxy), files=1, bytes=0, action='remove temporary input symlink and directory'))
    with (OUT / 'package-runtime-01.json').open('x', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write('\n')
    shutil.rmtree(proxy)
print(json.dumps({'status':record['status'], 'revision':REVISION, 'results':[x['exit_code'] for x in results]}))
raise SystemExit(0 if record['status']=='PASS' else 1)
