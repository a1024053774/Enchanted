"""核对 T-258 包内版本，并用包内 Electron 与产品源码运行身份边界测试。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/a2a-t258-package-20261108')
REVISION = '66e88ffe2251ea045a398c9003fef1795c8a2af8'
APP = Path('/private/tmp/a2a-build-t258-reviewed-20261108-01/Enchanted.app')
product = APP / 'Contents/Resources/app'
manifest = json.loads((product / 'package.json').read_text(encoding='utf-8'))
assert manifest['a2a']['revision'] == REVISION
assert manifest['productName'] == 'Enchanted'
assert not (APP.parent / 'work').exists()
assert (SOURCE / 'workbench/src/panes.ts').read_bytes() == (product / 'src/panes.ts').read_bytes()
summary = OUT / 'package-module-01.json'
record_path = OUT / 'package-runtime-01.json'
assert not summary.exists() and not record_path.exists(), '保留原有证据'
signature = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(APP)],
                           text=True, capture_output=True)
assert signature.returncode == 0, signature.stderr
proxy = Path(tempfile.mkdtemp(prefix='t258-package-input-', dir='/private/tmp'))
(proxy / 'workbench').symlink_to(product, target_is_directory=True)
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'COOP_'))}
env.update(ELECTRON_RUN_AS_NODE='1', T258_SOURCE_ROOT=str(proxy), T258_SUMMARY=str(summary))
command = [str(APP / 'Contents/MacOS/Enchanted'), '--test',
           str(SOURCE / 'workbench/tests/test_t258_codex_late_start.ts')]
run = subprocess.run(command, cwd=proxy, env=env, text=True, capture_output=True, timeout=180)
result = json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else None
record = dict(status='PASS' if run.returncode == 0 and result and result['status'] == 'PASS' else 'INCOMPLETE',
              revision=REVISION, app=str(APP), command=command, cwd=str(proxy),
              exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr,
              signature=dict(exit_code=signature.returncode, stderr=signature.stderr),
              boundary='包内 Electron 与产品代码的身份边界测试；真实 CLI 证据另存，不把本测试当作真实 CLI',
              summary=str(summary), cleanup=dict(directory=str(proxy), action='删除本次临时输入链接及空证据目录'))
with record_path.open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
shutil.rmtree(proxy)
print(json.dumps(dict(status=record['status'], revision=REVISION, result=result), ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
