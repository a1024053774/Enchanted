"""Copy evidence directories to the external archive and verify them (T-088).

Usage: archive_evidence.py MANIFEST_OUT REPLAY SRC=DST [SRC=DST ...]

Regular files and symlinks are copied as they are (links are never followed).
Sockets and other special files are not copied; they are counted in the manifest.
A copy is accepted only when the archive has the same number of files and bytes
as the source (lstat sizes). Nothing is deleted here.
"""
import json, os, shutil, stat, sys
from pathlib import Path


def inventory(root: Path):
    files = size = special = 0
    for directory, subdirs, names in os.walk(root, followlinks=False):
        for name in names + [d for d in subdirs if (Path(directory) / d).is_symlink()]:
            info = (Path(directory) / name).lstat()
            if stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                files += 1; size += info.st_size
            else:
                special += 1
    return files, size, special


def copy(src: Path, dst: Path):
    if dst.exists():
        raise SystemExit(f'archive target exists, refusing to overwrite: {dst}')
    for directory, subdirs, names in os.walk(src, followlinks=False):
        rel = Path(directory).relative_to(src)
        target = dst / rel
        target.mkdir(parents=True, exist_ok=True)
        for name in subdirs + names:
            path = Path(directory) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                os.symlink(os.readlink(path), target / name)
            elif stat.S_ISREG(info.st_mode):
                shutil.copy2(path, target / name, follow_symlinks=False)
        subdirs[:] = [d for d in subdirs if not (Path(directory) / d).is_symlink()]


def main():
    manifest_out, replay, pairs = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
    entries = []
    for pair in pairs:
        src, dst = (Path(x) for x in pair.split('=', 1))
        before = inventory(src)
        copy(src, dst)
        after = inventory(dst)
        ok = before[:2] == after[:2]
        entries.append(dict(original=str(src), archive=str(dst), files=before[0], bytes=before[1],
                            special_files_not_copied=before[2], archive_files=after[0], archive_bytes=after[1], verified=ok))
        print(json.dumps(entries[-1], ensure_ascii=False), flush=True)
        if not ok:
            raise SystemExit(f'archive mismatch for {src}')
    body = entries[0] if len(entries) == 1 else entries
    if isinstance(body, dict): body['replay'] = replay
    else: body = dict(replay=replay, entries=entries)
    manifest_out.write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
