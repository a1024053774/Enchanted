"""主控在沙箱外归档本票本地夹具探针；核对文件数/字节数，不计算校验值。"""
import json
import os
from pathlib import Path
import shutil
import sys

folder = Path(__file__).resolve().parent
assert os.path.ismount('/Volumes/WD-Elements'), '外置盘未挂载，不归档'
label = sys.argv[1]
assert label and all(c.isalnum() or c in '-_' for c in label)
archive = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104') / label
assert not archive.exists(), '保留旧归档，改用新编号'
archive.mkdir(parents=True)
paths = set()
for name in ['regressions-original-01.json', 'regressions-fixtures-02.json']:
    report = json.loads((folder/name).read_text(encoding='utf-8'))
    paths.add(Path(report['fixture']))
    for row in report['runs']:
        result = json.loads(row['stdout'])
        if 'root' in result:
            paths.add(Path(result['root']))
        if '--output' in row['argv']:
            saved = json.loads(Path(row['argv'][row['argv'].index('--output')+1]).read_text(encoding='utf-8'))
            paths.add(Path(saved['root']))

def inventory(root):
    files = [p for p in root.rglob('*') if p.is_file() or p.is_symlink()]
    return len(files), sum(p.lstat().st_size for p in files)

manifest = []
for original in sorted(paths):
    actual = original.resolve()
    assert str(actual).startswith('/private/tmp/') and actual.name.startswith(('t104-regressions-', 'a2a-pane-state-', 's3-pane-'))
    assert actual.is_dir() and not original.is_symlink()
    target = archive/actual.name
    shutil.copytree(actual,target,symlinks=True)
    assert inventory(actual)==inventory(target), '核对不一致，保留原目录'
    count,size = inventory(actual)
    manifest.append(dict(original=str(actual),archive=str(target),files=count,bytes=size,
                         replay='python3 evidence/2026-10-19-batch17/T-104/PROBE-REGRESSIONS.py 新摘要路径.json'))
    shutil.rmtree(actual)
with (folder/f'{label}.archive.json').open('x',encoding='utf-8') as output:
    json.dump(manifest,output,ensure_ascii=False,indent=2)
    output.write('\n')
print(json.dumps(manifest,ensure_ascii=False))
