#!/usr/bin/env python3
"""仅核对 RED-02 的 Python 3.9 解包；不启动 daemon 或写 Git 元数据。"""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('t080_red_runner', HERE / 'run_red_outside.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
fixture = Path(tempfile.mkdtemp(prefix='t80unpack-', dir='/tmp')).resolve()
checks = []
report = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'scope': '仅解包验证',
          'command': [sys.executable, '-B', str(Path(__file__).resolve())],
          'python': sys.version, 'fixture': str(fixture), 'checks': checks}
receipt_before = (HERE / 'red-01/receipt.json').read_bytes()


def archive(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as stream:
        for name, kind, data in entries:
            item = tarfile.TarInfo(name)
            item.type, item.mode = kind, 0o755
            if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                item.linkname = '/outside'
            item.size = len(data) if kind == tarfile.REGTYPE else 0
            stream.addfile(item, io.BytesIO(data) if item.size else None)
    buffer.seek(0)
    return tarfile.open(fileobj=buffer, mode='r')


try:
    assert sys.version_info[:2] == (3, 9), '必须使用本机 Python 3.9'
    old_target = fixture / 'old-api'
    old_target.mkdir()
    with archive([('file', tarfile.REGTYPE, b'expected\n')]) as stream:
        try:
            stream.extractall(old_target, filter='data')
        except TypeError as error:
            assert "unexpected keyword argument 'filter'" in str(error)
            checks.append({'case': 'known-bad-filter-api', 'expected': 'TypeError', 'observed': str(error)})
        else:
            raise AssertionError('未重现原解包 API 失败')
    with tarfile.open(HERE / 'red-01/baseline-source.tar.gz', 'r:gz') as stream:
        target = fixture / 'old-archive-links'
        target.mkdir()
        try:
            runner.unpack_source(stream, target)
        except RuntimeError as error:
            assert '链接或特殊成员' in str(error) and not list(target.iterdir())
            checks.append({'case': 'old-archive-links', 'observed': str(error), 'no_partial_writes': True})
        else:
            raise AssertionError('旧归档中的 hook 符号链接必须拒绝')
    cases = [(name, [('first', tarfile.REGTYPE, b'preserve\n'), (bad, kind, b'bad\n')])
             for name, bad, kind in [
                 ('absolute', '/outside', tarfile.REGTYPE), ('parent', '../outside', tarfile.REGTYPE),
                 ('nested-parent', 'dir/../outside', tarfile.REGTYPE), ('dot', './file', tarfile.REGTYPE),
                 ('empty-component', 'dir//file', tarfile.REGTYPE), ('backslash', 'dir\\file', tarfile.REGTYPE),
                 ('symlink', 'link', tarfile.SYMTYPE), ('hardlink', 'link', tarfile.LNKTYPE),
                 ('fifo', 'pipe', tarfile.FIFOTYPE), ('character-device', 'device', tarfile.CHRTYPE),
                 ('block-device', 'device', tarfile.BLKTYPE), ('duplicate', 'first', tarfile.REGTYPE)]]
    for name, entries in cases:
        target = fixture / name
        target.mkdir()
        with archive(entries) as stream:
            try:
                runner.unpack_source(stream, target)
            except RuntimeError as error:
                assert not list(target.iterdir()), '拒绝前不应写出任何成员'
                checks.append({'case': name, 'observed': str(error), 'no_partial_writes': True})
            else:
                raise AssertionError('应拒绝归档：' + name)
    paths = ['workbench/src', 'workbench/tests', 'workbench/hooks/hook.py',
             'workbench/package.json', 'workbench/package-lock.json',
             'workbench/LICENSE.synara', 'acceptance/entry/a2a_gates.py']
    packed = fixture / 'red02-source.tar.gz'
    argv = ['git', 'archive', '--format=tar.gz', '--output', str(packed), runner.REVISION, *paths]
    result = subprocess.run(argv, cwd=runner.ROOT, env=runner.ENV, capture_output=True, text=True)
    report['archive_command'] = {'argv': argv, 'exit': result.returncode, 'stderr': result.stderr}
    assert result.returncode == 0 and packed.stat().st_size < 5_000_000
    target = fixture / 'source'
    target.mkdir()
    with tarfile.open(packed, 'r:gz') as stream:
        runner.unpack_source(stream, target)
        files = [item for item in stream.getmembers() if item.isfile()]
        for item in files:
            with stream.extractfile(item) as expected:
                assert (target / item.name).read_bytes() == expected.read(), item.name
            assert (target / item.name).stat().st_mode & 0o777 == item.mode & 0o777, item.name
    checks.append({'case': 'red02-frozen-source', 'files': len(files), 'bytes_and_modes_match': True})
    assert (HERE / 'red-01/receipt.json').read_bytes() == receipt_before
    report['status'] = 'PASS'
finally:
    with (HERE / 'red02-unpack-checks.json').open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps({'status': report['status'], 'scope': report['scope'], 'checks': len(checks),
                      'report': str(HERE / 'red02-unpack-checks.json')}, ensure_ascii=False))
