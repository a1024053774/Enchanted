"""Controller-only: archive and remove the exact 09A-2 slot after reboot.

Never use the lost /tmp fixture as evidence. Never signal processes or remove
other paths. An unknown check preserves the slot and reports BLOCKED.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import traceback

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parents[2]
M = BASE / 'p1-materials-09a2'
LAUNCH = 'd2d9c666-5621-4467-bbe4-d99450bd5503'
OLD_ROOT = Path('/private/tmp/t078-2-p1-09a2-sm_du7jo')
VOLUME = Path('/Volumes/WD-Elements')
SLOT = VOLUME / 'a2a-workbench' / ('t078-09-' + LAUNCH)
LABEL = 'slot-after-reboot-09a2-01'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def inventory(root):
    """Use lstat and scandir; do not descend into a symlink."""
    rows = {}

    def visit(path):
        info = path.lstat()
        name = str(path.relative_to(root))
        if stat.S_ISLNK(info.st_mode):
            kind = 'link'
        elif stat.S_ISDIR(info.st_mode):
            kind = 'directory'
        elif stat.S_ISREG(info.st_mode):
            kind = 'file'
        else:
            raise RuntimeError('Unexpected slot member: ' + str(path))
        rows[name] = {'kind': kind, 'bytes': info.st_size,
                      'device': info.st_dev, 'inode': info.st_ino,
                      'mtime_ns': info.st_mtime_ns,
                      'link': os.readlink(path) if kind == 'link' else None}
        if kind == 'directory':
            with os.scandir(path) as entries:
                children = sorted(Path(entry.path) for entry in entries)
            for child in children:
                visit(child)

    visit(root)
    return rows


def archive_and_verify(root, archive):
    before = inventory(root)
    with tarfile.open(archive, 'x:gz', dereference=False) as stream:
        stream.add(root, arcname=root.name)
    with archive.open('rb') as stream:
        os.fsync(stream.fileno())
    with tarfile.open(archive) as stream:
        names = {root.name if name == '.' else root.name + '/' + name for name in before}
        require(set(stream.getnames()) == names and len(stream.getmembers()) == len(names),
                'Archive member set differs')
        for name, info in before.items():
            member = stream.getmember(root.name if name == '.' else root.name + '/' + name)
            if info['kind'] == 'link':
                require(member.issym() and member.linkname == info['link'], 'Symlink differs: ' + name)
            elif info['kind'] == 'directory':
                require(member.isdir(), 'Directory differs: ' + name)
            else:
                require(member.isfile() or member.islnk(), 'File type differs: ' + name)
                descriptor = os.open(root / name, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(descriptor, 'rb') as original, stream.extractfile(member) as saved:
                    while True:
                        a, b = original.read(1024 * 1024), saved.read(1024 * 1024)
                        require(a == b, 'Archive byte readback differs: ' + name)
                        if not a:
                            break
    require(inventory(root) == before, 'Slot changed during archival')
    return before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval-ref', required=True)
    args = parser.parse_args()
    require(args.approval_ref.strip(), 'Approval reference required')
    out = BASE / LABEL
    out.mkdir()  # A second run cannot overwrite a failed result.
    report = {'status': 'BLOCKED', 'product_status': 'INCOMPLETE', 'argv': sys.argv,
              'approval_ref': args.approval_ref, 'signals_sent': 0,
              'vendor_cli_starts': 0, 'removed': [], 'slot': str(SLOT),
              'lost_root': str(OLD_ROOT), 'evidence_gap': 'Unarchived /tmp originals were lost at reboot'}

    def save():
        (out / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, key):
        command = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        # Do not save unrelated user process command lines.
        visible = command.stdout
        if argv[0] == '/bin/ps':
            visible = '\n'.join(line for line in visible.splitlines()
                                if str(SLOT) in line or str(OLD_ROOT) in line or LAUNCH in line)
        report[key] = {'argv': argv, 'exit_code': command.returncode,
                       'stdout': visible, 'stderr': command.stderr}
        save()
        return command

    def no_current_users(key):
        processes = run(['/bin/ps', '-axo', 'pid=,command='], key + '_ps')
        require(processes.returncode == 0 and not processes.stderr, 'Process inventory unavailable')
        matching = [line for line in processes.stdout.splitlines()
                    if str(SLOT) in line or str(OLD_ROOT) in line or LAUNCH in line]
        require(not matching, 'A process still references this slot/root/launch: ' + repr(matching))
        opened = run(['/usr/sbin/lsof', '-nP', '-F', 'p', '+D', str(SLOT)], key + '_lsof')
        require(opened.returncode == 1 and not opened.stdout.strip() and not opened.stderr.strip(),
                'Slot has open files or current use cannot be verified')

    save()
    try:
        require(SOURCE == Path('/Users/luckye/Documents/Code/a2a-wt-t078'), 'Script checkout differs')
        require(not os.path.lexists(OLD_ROOT), 'Old root exists; this post-reboot procedure does not apply')
        require(os.path.ismount(VOLUME), 'External volume is not mounted')
        require(VOLUME.resolve(strict=True) == VOLUME and SLOT.resolve(strict=True) == SLOT,
                'Slot or a parent is a symlink')
        require(SLOT.is_dir(), 'Exact slot missing')
        approval = json.loads((M / 'approval.json').read_text(encoding='utf-8'))
        continuation = json.loads((M / 'continue-esc/result.json').read_text(encoding='utf-8'))
        require(approval['input']['launch'] == LAUNCH and approval['input']['root'] == str(OLD_ROOT),
                'Approval ownership mismatch')
        require(continuation['input']['launch'] == LAUNCH and continuation['electron_build'] == str(SLOT / 'dist'),
                'Actual continuation ownership mismatch')
        drivers = [json.loads(line) for line in (M / 'continue-esc/electron-driver.jsonl').read_text(encoding='utf-8').splitlines()]
        electron = next(row for row in drivers if 'argv' in row and 'pid' in row)
        argv = electron['argv']
        require(argv[argv.index('--build') + 1] == str(SLOT / 'dist') and
                argv[argv.index('--launch') + 1] == LAUNCH, 'Actual Electron ownership mismatch')
        require((SLOT / 'dist/build.json').resolve(strict=True) == SLOT / 'dist/build.json',
                'Build manifest is linked')
        build = json.loads((SLOT / 'dist/build.json').read_text(encoding='utf-8'))
        require(build['source'] == str(SOURCE / 'workbench/app') and build['out'] == str(SLOT / 'dist'),
                'Build source/out mismatch')
        report.update(build_manifest=build, actual_electron={'pid': electron['pid'], 'argv': argv})
        # Reboot retires the old processes. It does not turn cleanup into PASS.
        boot = run(['/usr/sbin/sysctl', '-n', 'kern.boottime'], 'boot')
        match = re.search(r'\bsec\s*=\s*(\d+)', boot.stdout)
        require(boot.returncode == 0 and not boot.stderr and match, 'Current boot time unavailable')
        archived = json.loads((BASE / 'external-archive-93611737c0674a7aa55d1fcf3863a0b0.json').read_text(encoding='utf-8'))
        last_record = datetime.datetime.fromisoformat(archived['created_at']).timestamp()
        require(int(match.group(1)) > last_record, 'No independently verified reboot after old run')
        no_current_users('before_archive')
        external = VOLUME / 'a2a-evidence/2026-10-11-batch13/T-078' / LABEL
        require(external.parent.resolve(strict=True) == external.parent, 'Archive parent linked or missing')
        external.mkdir()
        archive = external / 'slot.tar.gz'
        rows = archive_and_verify(SLOT, archive)
        report.update(archive=str(archive), archive_bytes=archive.stat().st_size,
                      byte_readback='PASS', inventory=rows)
        shutil.copyfile(Path(__file__).resolve(), out / 'executed-script.py')
        save()
        no_current_users('before_remove')
        require(SLOT.resolve(strict=True) == SLOT and inventory(SLOT) == rows, 'Slot changed before removal')
        shutil.rmtree(SLOT)  # Fixed owned directory only; shutil does not follow symlinks.
        require(not os.path.lexists(SLOT), 'Slot removal not confirmed')
        report.update(status='PASS', removed=[str(SLOT)],
                      completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    save()
    print(json.dumps({key: report.get(key) for key in
                      ['status', 'product_status', 'archive', 'byte_readback', 'removed', 'error']}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
