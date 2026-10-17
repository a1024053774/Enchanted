#!/usr/bin/env python3
"""主控同意组合基线后运行；只把旧函数的硬编码目的地注入本票新测试目录。"""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
BASE = 'c544b29049861998e11eeb7344b457103fab3c98'
OLD_ARCHIVE = '/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077'
EXTERNAL = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['baseline', 'candidate'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not os.path.ismount('/Volumes/WD-Elements'):
        raise RuntimeError('外置盘未挂载')
    target = EXTERNAL / ('s3-archive-' + args.phase + '-' + uuid.uuid4().hex[:8])
    target.mkdir(parents=True, exist_ok=False)
    source = Path(tempfile.mkdtemp(prefix='t089-s3-archive-', dir='/tmp')).resolve()
    # Independent threshold oracle: exactly 5 MiB stays; 5 MiB + 17 moves,
    # even though the extension is outside the new category-based CLI policy.
    expected = b'T089-sentinel-xyz' + bytes(range(256)) * 20480
    assert len(expected) == 5 * 1024 * 1024 + 17
    (source / 'large.txt').write_bytes(expected)
    small = b'x' * (5 * 1024 * 1024)
    (source / 'boundary.bin').write_bytes(small)
    replay = ['python3', '-B', str(ROOT / 'workbench/tests/run_s3_regression.py'), '--suite', 'cas']
    if args.phase == 'baseline':
        text = subprocess.check_output(['git', 'show', BASE + ':workbench/tests/run_s3_regression.py'], cwd=ROOT, text=True)
        function = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == 'archive_large_files')
        import shutil
        def destination(value):
            return target if str(value) == OLD_ARCHIVE else Path(value)
        def write_new(path, value):
            with path.open('x', encoding='utf-8') as handle:
                json.dump(value, handle, ensure_ascii=False)
        namespace = dict(Path=destination, ROOT=ROOT, sys=type('Args', (), {'argv': ['runner', '--suite', 'cas']}),
                         os=os, shutil=shutil, write_new=write_new)
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<unchanged-baseline-archive_large_files>', 'exec'), namespace)
        entries = namespace['archive_large_files'](source)
    else:
        sys.path.insert(0, str(ROOT / 'workbench/tests'))
        from archive_evidence import archive_large_files
        entries = archive_large_files(source, archive_root=target / source.name,
                                      replay=replay, minimum_bytes=5 * 1024 * 1024)
    assert not (source / 'large.txt').exists()
    assert (source / 'boundary.bin').read_bytes() == small
    assert (target / source.name / 'large.txt').read_bytes() == expected
    manifest = json.loads((source / 'large.txt.archive.json').read_text(encoding='utf-8'))
    assert manifest['bytes'] == len(expected) and manifest['replay'] == replay
    assert set(manifest) == ({'original', 'archive', 'bytes', 'replay'} if args.phase == 'baseline'
                             else {'original', 'archive', 'bytes', 'replay', 'files'})
    args.output.write_text(json.dumps({'status': 'PASS', 'phase': args.phase, 'base': BASE,
                          'source': str(source), 'external': str(target), 'entries': entries,
                          'original_function_unchanged': args.phase == 'baseline',
                          'injection': '仅将旧硬编码目的地映射到本票目录；原函数 AST 不改',
                          'argv': sys.argv}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
