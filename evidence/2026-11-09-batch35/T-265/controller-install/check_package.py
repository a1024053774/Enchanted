"""用包内 Electron 和产品源码运行已审查的 T-265 材料检查。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--app', type=Path, required=True)
parser.add_argument('--revision', required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists(), '保留旧证据，输出必须是新文件'
product = args.app / 'Contents/Resources/app'
manifest = json.loads((product / 'package.json').read_text(encoding='utf-8'))
assert manifest['a2a']['revision'] == args.revision
assert manifest['productName'] == 'Enchanted'
assert (args.source / 'workbench/src/panes.ts').read_bytes() == (product / 'src/panes.ts').read_bytes()
signature = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(args.app)],
                           text=True, capture_output=True)
assert signature.returncode == 0, signature.stderr
fixture = Path(tempfile.mkdtemp(prefix='t265-package-input-', dir='/private/tmp'))
(fixture / 'tests').mkdir()
# This is a disposable test input directory, never a build output directory.
# rmtree removes the link itself; no build command touches this directory.
(fixture / 'src').symlink_to(product / 'src', target_is_directory=True)
test = fixture / 'tests/test_t265_review_materials.mjs'
original = args.source / 'workbench/tests/test_t265_review_materials.mjs'
shutil.copy2(original, test)
assert test.read_bytes() == original.read_bytes()
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'COOP_', 'T265_'))}
env.update(ELECTRON_RUN_AS_NODE='1', A2A_REQUEST_DIR=str(fixture / 'fixtures'))
command = [str(args.app / 'Contents/MacOS/Enchanted'), '--test', str(test)]
run = subprocess.run(command, cwd=fixture, env=env, text=True, capture_output=True, timeout=180)
record = dict(status='PASS' if run.returncode == 0 else 'INCOMPLETE', revision=args.revision,
              app=str(args.app), command=command, cwd=str(fixture), test_copy_byte_equal=True,
              packaged_panes_byte_equal=True, exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr,
              signature=dict(exit_code=signature.returncode, stderr=signature.stderr),
              scope='包内 Electron 与产品源码的材料检查；不替代原生 CLI 或完整审查生命周期',
              cleanup=dict(directory=str(fixture), removed=False))
args.out.parent.mkdir(parents=True, exist_ok=True)
with args.out.open('x', encoding='utf-8') as out:
    json.dump(record, out, ensure_ascii=False, indent=2)
    out.write('\n')
shutil.rmtree(fixture)
with args.out.with_name(args.out.stem + '-cleanup.json').open('x', encoding='utf-8') as out:
    json.dump(dict(directory=str(fixture), removed=not fixture.exists()), out, indent=2)
print(json.dumps(dict(status=record['status'], revision=args.revision)))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
