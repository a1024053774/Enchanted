#!/bin/sh
set -eu
exec python3 -B - "$(dirname "$0")" <<'PY'
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, sys.argv[1])
from slim_history import ARCHIVES, HERE, REL, disk_tree, mounted, no_links, read, require, save
mounted()
for report in sorted(HERE.glob('*checks-*.json')):
    data = read(report)
    if 'artifact_root' not in data:
        continue
    source = Path(data['artifact_root'])
    require(source.is_relative_to(Path('/private/tmp')) and source.name.startswith('a2a-t101-'), '不是本票隔离产物')
    target = ARCHIVES / 'local-preparation' / report.stem
    no_links(source)
    no_links(target)
    manifest = report.with_suffix('.archive.json')
    require(not target.exists() and not manifest.exists(), '归档或清单已存在；保留，不覆盖')
    expected = disk_tree(source)
    require(all(row[0] == 'file' for row in expected.values()), '夹具中有链接或特殊类型，停止')
    shutil.copytree(source, target, symlinks=True)
    require(expected == disk_tree(source) == disk_tree(target), '文件数/字节数不一致')
    if report.name.startswith('local-checks-'):
        replay = ['python3', '-B', str(REL / 'run_local_checks.py'), '--report', 'NEW_REPORT.json']
        other = []
    else:
        replay = data['checks'][0]['argv'][:-1] + ['NEW_ARTIFACT_DIRECTORY']
        other = [row['argv'][:-1] + ['NEW_ARTIFACT_DIRECTORY'] for row in data['checks'][1:]]
    save(manifest, {'original': str(source), 'archive': str(target),
                    'bytes': sum(row[1] for row in expected.values()), 'files': len(expected),
                    'replay': replay, 'additional_replay': other,
                    'environment': '现有套件重放只在子进程移除继承的 GIT_CONFIG_*；见 RESULTS.md',
                    'note': '保留 /tmp 原件；目录复制核对完成，未删除原件'})
print('PASS 本票隔离产物已归档；新生成 *.archive.json 尚须主控审查并入库')
PY
