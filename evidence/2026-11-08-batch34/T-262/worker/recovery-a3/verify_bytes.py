"""只读核对恢复来源与补证副本；不运行应用、构建或业务测试。"""
from pathlib import Path
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
manifest = json.loads((HERE / 'provenance.json').read_text(encoding='utf-8'))
source = manifest['source_candidate']
products = [item['path'] for item in manifest['green04_snapshot_comparisons']]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


assert not git('diff', '--name-only', manifest['common_ancestor'], manifest['base'], '--', *products)
for item in manifest['restored']:
    actual = (ROOT / item['path']).read_bytes()
    assert actual == git('show', source + ':' + item['path']), item['path']
    assert len(actual) == item['bytes'], item['path']
for item in manifest['copied']:
    actual = (ROOT / item['copy']).read_bytes()
    assert actual == Path(item['source']).read_bytes(), item['source']
    assert len(actual) == item['bytes'], item['source']
for item in manifest['green04_snapshot_comparisons']:
    assert (ROOT / item['path']).read_bytes() == Path(item['snapshot']).read_bytes(), item['path']
assert (HERE / 'sources/review-01/RecordsPage.original.tsx').read_bytes() == (ROOT / products[0]).read_bytes()

allowed = set(products)
prefix = 'evidence/2026-11-08-batch34/T-262/worker/'
changed = git('diff', '--name-only', manifest['base']).decode().splitlines()
untracked = git('ls-files', '--others', '--exclude-standard').decode().splitlines()
assert all(path in allowed or path.startswith(prefix) for path in changed + untracked)
print(json.dumps({
    'status': 'PASS',
    'claim': '恢复文件及补证副本逐字节一致，三个路径相对 B 无他人变更，改动均在卡内',
    'restored_files': len(manifest['restored']),
    'copied_text_files': len(manifest['copied']),
    'product_test_run': False,
    'overall_acceptance': 'INCOMPLETE',
}, ensure_ascii=False, indent=2))
