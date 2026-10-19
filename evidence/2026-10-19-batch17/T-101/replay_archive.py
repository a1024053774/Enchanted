#!/usr/bin/env python3
"""把历史 blob 归档恢复到一个全新目录，不修改原仓库。"""
import json
import os
from pathlib import Path
import shutil
import sys

index_path, output = map(Path, sys.argv[1:])
volume = Path('/Volumes/WD-Elements')
if not os.path.ismount(volume) or volume.is_symlink() or volume.resolve() != volume:
    raise SystemExit('NO_GO 外置盘未挂载')
if not index_path.resolve().is_relative_to(volume / 'a2a-evidence'):
    raise SystemExit('NO_GO 索引不在外置盘归档根')
if output.exists() or not output.is_absolute():
    raise SystemExit('NO_GO 输出必须是尚不存在的绝对路径')
rows = json.loads(index_path.read_text(encoding='utf-8'))
for row in rows:
    rel = Path(row['file'])
    if rel.is_absolute() or '..' in rel.parts:
        raise SystemExit('NO_GO 归档路径越界')
    source = index_path.parent / 'versions' / rel
    if source.is_symlink() or not source.resolve().is_relative_to(index_path.parent.resolve()):
        raise SystemExit('NO_GO 拒绝链接或越界')
    if source.stat().st_size != row['bytes']:
        raise SystemExit('NO_GO 归档字节数不一致')
output.mkdir(parents=True)
for row in rows:
    target = output / row['file']
    target.parent.mkdir(parents=True, exist_ok=True)
    with (index_path.parent / 'versions' / row['file']).open('rb') as left, target.open('xb') as right:
        shutil.copyfileobj(left, right)
print('PASS 历史版本已恢复；目录以 Git blob id 区分版本，见原 index.json')
