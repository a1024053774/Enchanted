#!/bin/sh
# 由执行主控运行：每次独立启动，只到首屏；探针只关闭自建 pane。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t094
label=${1:-busy-01}
count=${2:-8}
case "$count" in 5|6|7|8|9|10) ;; *) echo '启动次数必须为 5～10' >&2; exit 2 ;; esac
python3 -B evidence/2026-10-16-batch16/T-094/probe-start.py \
  --label "$label" --count "$count" --cwd "$PWD" --launcher scripts/launch-worker \
  --expect-diagnostics --expect-busy-foreground
python3 -B - "$label" <<'PY'
import json
from pathlib import Path
import shutil
import sys
disk = Path('/Volumes/WD-Elements')
if not disk.is_mount():
    raise SystemExit('外置盘未挂载')
label = sys.argv[1]
base = disk / 'a2a-evidence/2026-10-16-batch16/T-094'
run = json.loads((base / label / 'run.json').read_text(encoding='utf-8'))
for a in run['attempts']:
    row = a['launch_record']
    print(json.dumps(dict(number=a['number'], pane=row['pane'], exit_code=a['launch']['returncode'],
                         error_code=row.get('error_code'), busy_foreground=row.get('busy_foreground')),
                     ensure_ascii=False))
source = Path('/tmp/t094-busy-details-01')
target = base / (label + '-contract-details')
shutil.copytree(source, target)
def size(root):
    files = [p for p in root.rglob('*') if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)
if size(source) != size(target):
    raise SystemExit('归档文件数或字节数不一致，两边原件都保留')
for original, archive, name, replay in (
    ('（probe-start.py 直接写入外置盘）', base / label, label,
     'sh evidence/2026-10-16-batch16/T-094/outside-busy.sh <新label> 8'),
    (str(source), target, label + '-contract-details',
     'python3 -B scripts/test_launch_worker_failure.py --report <新文件> -v'),
):
    files, byte_count = size(archive)
    manifest = dict(original=original, archive=str(archive), files=files, bytes=byte_count, replay=replay)
    path = Path('evidence/2026-10-16-batch16/T-094') / (name + '.archive.json')
    with path.open('x', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')
PY
