#!/bin/sh
# 由执行主控在已核对的 Herdr shell 中运行；不发送模型提示。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t094
python3 -B evidence/2026-10-16-batch16/T-094/probe-start.py \
  --label green-01 --count 5 --cwd "$PWD" --launcher scripts/launch-worker --expect-diagnostics
python3 -B evidence/2026-10-16-batch16/T-094/probe-start.py \
  --label unregistered-01 --count 1 --cwd "$PWD" --launcher scripts/launch-worker \
  --unregistered --expect-diagnostics
python3 -B - <<'PY'
import json
from pathlib import Path
import shutil
disk = Path('/Volumes/WD-Elements')
if not disk.is_mount():
    raise SystemExit('外置盘未挂载')
source = Path('/tmp/t094-existing-launcher-contract-01')
summary = json.loads((source / 'summary.json').read_text(encoding='utf-8'))
if summary['failures'] or summary['errors'] or summary['tests'] != 6:
    raise SystemExit('已有入口测试未通过，保留原件，不归档成通过证据')
def size(root):
    files = [p for p in root.rglob('*') if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)
for source, label, replay in (
    (source, 'existing-contract-01', 'python3 -B acceptance/test_launcher_shell_ready_e2e.py --artifacts <新目录>'),
    (Path('/tmp/t094-contract-details-01'), 'contract-details-01',
     'python3 -B scripts/test_launch_worker_failure.py --report <新文件> -v；旧实现另加 --launcher evidence/2026-10-16-batch16/T-094/launch-worker.parent'),
):
    target = disk / 'a2a-evidence/2026-10-16-batch16/T-094' / label
    shutil.copytree(source, target)
    files, byte_count = size(source)
    if (files, byte_count) != size(target):
        raise SystemExit('归档文件数或字节数不一致；两边原件都保留')
    manifest = dict(original=str(source), archive=str(target), files=files, bytes=byte_count, replay=replay)
    with Path('evidence/2026-10-16-batch16/T-094', label + '.archive.json').open('x', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(dict(archive=str(target), files=files, bytes=byte_count), ensure_ascii=False))
PY
