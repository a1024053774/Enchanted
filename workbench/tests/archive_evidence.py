#!/usr/bin/env python3
"""归档静止的证据目录；有期限的准备阶段完成后，单独回收原件。"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

VOLUME = Path('/Volumes/WD-Elements')


class ReclaimIncomplete(RuntimeError):
    def __init__(self, entries, reason, state):
        self.entries = entries
        self.reason = reason
        self.remaining = state['remaining_originals']
        self.unverified = state['unverified_originals']
        super().__init__('归档已完成并核对、原件回收未完成；剩余原件：'
                         + json.dumps(self.remaining, ensure_ascii=False) + '；无法核对的原件：'
                         + json.dumps(self.unverified, ensure_ascii=False) + '；原因：' + reason)


def walk_error(error):
    raise error


def regular_tree(path):
    """Return relative file sizes. Reject links and special files before copying."""
    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        return {'': path.stat().st_size}
    if not stat.S_ISDIR(mode):
        raise ValueError('拒绝链接或特殊文件：' + str(path))
    result = {}
    for parent, dirs, files in os.walk(path, followlinks=False, onerror=walk_error):
        for name in dirs + files:
            child = Path(parent) / name
            kind = child.lstat().st_mode
            if not (stat.S_ISDIR(kind) or stat.S_ISREG(kind)):
                raise ValueError('拒绝链接或特殊文件：' + str(child))
            if stat.S_ISREG(kind):
                result[str(child.relative_to(path))] = child.stat().st_size
    return result


def no_links(path):
    for parent in [path, *path.parents]:
        if parent.is_symlink():
            raise ValueError('拒绝路径中的符号链接：' + str(parent))


def is_category(path):
    name = path.name.lower()
    if path.is_dir():
        return (name in ('run', 'fixtures') or name.startswith(('run-', 'run_', 'fixtures-', 'fixtures_'))
                or (path / 'run.json').is_file())
    return (name.endswith(('.tar.gz', '.bin', '.sqlite', '.sqlite3', '.sqlite-wal', '.sqlite3-wal'))
            or ('monitor' in name and name.endswith(('.log', '.jsonl', '.txt'))))


def select_paths(source, keep, minimum_bytes):
    selected = []
    for parent, dirs, files in os.walk(source, followlinks=False, onerror=walk_error):
        dirs.sort()
        for name in sorted(dirs + files):
            path = Path(parent) / name
            if any(path == item or path in item.parents or item in path.parents for item in keep):
                if name in dirs and (path in keep or is_category(path)):
                    dirs.remove(name)
                continue
            if minimum_bytes is None:
                matches = is_category(path)
            else:
                matches = path.is_file() and path.stat().st_size > minimum_bytes
            if matches:
                selected.append(path)
                if name in dirs:
                    dirs.remove(name)
    return sorted(selected)


def copy_verified(source, target):
    """Use exclusive creation, fsync and the existing S3 byte comparison rule."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as left, target.open('xb') as right:
        shutil.copyfileobj(left, right)
        right.flush()
        os.fsync(right.fileno())


def verify(source, target, expected):
    if regular_tree(source) != expected or regular_tree(target) != expected:
        raise ValueError('文件数或字节数不一致：' + str(source))
    for name in expected:
        left_path = source / name if name else source
        right_path = target / name if name else target
        with left_path.open('rb') as left, right_path.open('rb') as right:
            while True:
                a, b = left.read(1024 * 1024), right.read(1024 * 1024)
                if a != b:
                    raise ValueError('归档与原件逐字节比较不一致：' + str(source))
                if not a:
                    break


def prepare(request):
    source = Path(request['source'])
    mount = Path(request['mount_point'])
    target_root = Path(request['archive_root'])
    if not os.path.ismount(mount):
        raise ValueError('外置盘未挂载；拒绝写入：' + str(mount))
    for path in (mount, source, target_root):
        no_links(path)
    if not source.is_dir() or target_root == mount or mount not in target_root.parents:
        raise ValueError('源目录或归档路径无效')
    if source == target_root or source in target_root.parents or target_root in source.parents:
        raise ValueError('源与归档目录不得包含彼此')
    keep = []
    for name in request['keep']:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('--keep 必须是源目录内的相对路径')
        item = source / relative
        no_links(item)
        if not item.exists():
            raise ValueError('--keep 文件不存在：' + str(item))
        keep.append(item)
    plan = []
    for path in select_paths(source, keep, request['minimum_bytes']):
        target = target_root / path.relative_to(source)
        manifest = path.with_name(path.name + '.archive.json')
        no_links(target)
        if target.exists() or manifest.exists():
            raise FileExistsError('目标或清单已存在：' + str(target))
        inventory = regular_tree(path)
        entry = {'original': str(path), 'archive': str(target), 'bytes': sum(inventory.values()),
                 'files': len(inventory), 'replay': request['replay']}
        plan.append((path, target, manifest, inventory, entry))
    # Preflight every destination before creating any copy. On failure keep all
    # originals and partial archives; reruns never overwrite that evidence.
    for path, target, _, inventory, _ in plan:
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=False)
            for parent, dirs, _ in os.walk(path, onerror=walk_error):
                for name in dirs:
                    (target / (Path(parent) / name).relative_to(path)).mkdir()
            for name in inventory:
                copy_verified(path / name, target / name)
        else:
            copy_verified(path, target)
    for path, target, _, inventory, _ in plan:
        verify(path, target, inventory)
    for _, _, manifest, _, entry in plan:
        with manifest.open('x', encoding='utf-8') as handle:
            json.dump(entry, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
    return [entry for _, _, _, _, entry in plan]


def reclaim(entries):
    for entry in entries:
        path = Path(entry['original'])
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def inspect_remaining(entries):
    state = {'remaining_originals': [], 'unverified_originals': {}}
    for entry in entries:
        path = entry['original']
        try:
            os.lstat(path)
        except FileNotFoundError:
            continue
        except OSError as error:
            state['unverified_originals'][path] = str(error)
        else:
            state['remaining_originals'].append(path)
    return state


def run_phase(phase, payload, timeout):
    child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).absolute()), '--' + phase],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, start_new_session=True)
    try:
        stdout, stderr = child.communicate(json.dumps(payload), timeout=timeout)
    except subprocess.TimeoutExpired:
        child.kill()
        # Do not wait indefinitely for a process stuck in kernel I/O.
        try:
            child.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        raise TimeoutError(phase + ' 阶段超时') from None
    if child.returncode:
        raise RuntimeError(stderr.strip() or phase + ' 子进程失败')
    return json.loads(stdout)


def archive_large_files(out, *, archive_root, replay, mount_point=VOLUME,
                        timeout=60, keep=(), minimum_bytes=None):
    """Prepare without deletion; reclaim only after the parent receives completion."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout 必须是有限正数')
    request = {'source': os.path.abspath(out), 'archive_root': os.path.abspath(archive_root),
               'mount_point': os.path.abspath(mount_point), 'replay': replay,
               'keep': list(keep), 'minimum_bytes': minimum_bytes}
    try:
        entries = run_phase('prepare', request, timeout)
    except TimeoutError:
        raise TimeoutError('归档准备读写超时；保留原件与已有副本') from None
    try:
        run_phase('reclaim', entries, timeout)
    except (OSError, ValueError, RuntimeError) as error:
        try:
            state = run_phase('remaining', entries, timeout)
        except (OSError, ValueError, RuntimeError) as inspection_error:
            state = {'remaining_originals': [], 'unverified_originals': {
                entry['original']: '状态核对失败：' + str(inspection_error) for entry in entries}}
        raise ReclaimIncomplete(entries, str(error), state) from error
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='evidence/<批次>/<ticket>；先停止证据生产者')
    parser.add_argument('--mount-point', type=Path, default=VOLUME)
    parser.add_argument('--archive-root', type=Path, help='默认 <挂载点>/a2a-evidence/<批次>/<ticket>')
    parser.add_argument('--timeout', type=float, default=60, help='准备、回收及失败后状态核对各自的期限（秒）')
    parser.add_argument('--keep', action='append', default=[], help='保留输入小文件的相对路径；其祖先 run/fixtures 也保留')
    parser.add_argument('--replay', nargs=argparse.REMAINDER, required=True, help='产生或重放此证据的命令 argv（放在参数末尾）')
    args = parser.parse_args()
    if not args.replay:
        parser.error('--replay 不得为空')
    target = args.archive_root or args.mount_point / 'a2a-evidence' / args.source.parent.name / args.source.name
    entries = archive_large_files(args.source, archive_root=target, mount_point=args.mount_point,
                                  timeout=args.timeout, keep=args.keep, replay=args.replay)
    print(json.dumps({'status': 'PASS', 'archives': entries}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--prepare']:
            print(json.dumps(prepare(json.load(sys.stdin)), ensure_ascii=False))
        elif sys.argv[1:] == ['--reclaim']:
            reclaim(json.load(sys.stdin))
            print('null')
        elif sys.argv[1:] == ['--remaining']:
            print(json.dumps(inspect_remaining(json.load(sys.stdin)), ensure_ascii=False))
        else:
            main()
    except ReclaimIncomplete as error:
        print(json.dumps({'status': 'INCOMPLETE', 'phase': 'reclaim', 'archive_verified': True,
                          'remaining_originals': error.remaining, 'unverified_originals': error.unverified,
                          'archives': error.entries,
                          'reason': error.reason, 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
    except (OSError, ValueError, RuntimeError) as error:
        print('归档失败：' + str(error), file=sys.stderr)
        raise SystemExit(1)
