#!/bin/sh
# 由主控归档本地无模型验收原件；不启动 Herdr 或 Codex。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t094
python3 -B - <<'PY'
import json
from pathlib import Path
import shutil
disk = Path('/Volumes/WD-Elements')
if not disk.is_mount():
    raise SystemExit('外置盘未挂载')
source = Path('/tmp/t094-revised-acceptance-01')
run = json.loads((source / 'run.json').read_text(encoding='utf-8'))
if len(run['steps']) != 18:
    raise SystemExit('测试步骤未完成，保留原件，不归档成完整运行')
target = disk / 'a2a-evidence/2026-10-16-batch16/T-094/revised-acceptance-01'
shutil.copytree(source, target)
def size(root):
    files = [p for p in root.rglob('*') if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)
files, byte_count = size(source)
if (files, byte_count) != size(target):
    raise SystemExit('归档文件数或字节数不一致，两边原件都保留')
manifest = dict(original=str(source), archive=str(target), files=files, bytes=byte_count,
                replay='python3 -B evidence/2026-10-16-batch16/T-094/run-revised-acceptance.py（重放换用全新 OUT 目录）')
path = Path('evidence/2026-10-16-batch16/T-094/revised-acceptance-01.archive.json')
with path.open('x', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps(dict(status=run['status'], archive=str(target), files=files, bytes=byte_count), ensure_ascii=False))
PY
