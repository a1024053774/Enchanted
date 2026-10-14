"""主控运行：将唯一超限文件迁至外置盘，逐字节读回后留指针。"""
import json
import os
from pathlib import Path
import stat
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'evidence/2026-10-14-batch14/T-081/capability-run-02/commands.jsonl'
VOLUME = Path('/Volumes/WD-Elements')
DEST = VOLUME / 'a2a-evidence/2026-10-14-batch14/T-081/capability-run-02/commands.jsonl'


def archive_file(source, destination, pointer, expected_bytes):
    before = source.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != expected_bytes:
        raise RuntimeError('源文件类型或字节数不符；不移动。')
    if destination.exists() or destination.is_symlink() or pointer.exists() or pointer.is_symlink():
        raise RuntimeError('目标或指针已存在；不覆盖，不自动重试。')
    for parent in destination.parents:
        if parent.is_symlink():
            raise RuntimeError('外置路径含符号链接；不移动。')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, destination.open('xb') as dst:
        while True:
            data = src.read(131072)
            if not data:
                break
            dst.write(data)
        dst.flush()
        os.fsync(dst.fileno())
    count = 0
    with source.open('rb') as src, destination.open('rb') as dst:
        while True:
            data = src.read(131072)
            if dst.read(len(data) or 1) != data:
                raise RuntimeError('外置字节读回不一致；保留本地原件及外置现场。')
            count += len(data)
            if not data:
                break
    after = source.lstat()
    if (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns) != (before.st_ino, before.st_dev, before.st_size, before.st_mtime_ns) or count != expected_bytes:
        raise RuntimeError('复制期间源文件变化；保留两处现场。')
    os.chmod(destination, 0o444)
    receipt = {'status': 'PASS', 'source': str(source), 'archive': str(destination),
               'bytes': count, 'verification': '完整顺序逐字节读回一致；未使用摘要',
               'verified_at': datetime.now(timezone.utc).isoformat(),
               'local_source_disposition': '指针持久化后仅删除已经验证一致的本地副本；失败保留现场'}
    with pointer.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    for directory in (destination.parent, pointer.parent):
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    # The caller explicitly requested external archival of this exact file.
    # All other run-02 evidence remains in place.
    source.unlink()
    descriptor = os.open(source.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return receipt


def main():
    if not os.path.ismount(VOLUME) or VOLUME.is_symlink():
        raise RuntimeError('外置盘未真实挂载；不回退、不移动。')
    receipt = archive_file(SOURCE, DEST, SOURCE.with_name('commands.jsonl.external.json'), 5_027_291)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
