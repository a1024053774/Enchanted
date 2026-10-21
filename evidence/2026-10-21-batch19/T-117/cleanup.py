"""Archive owned failure/rollback artifacts, then remove only this build's copies."""
import json
import os
from pathlib import Path
import shutil
import subprocess

archive = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-21-batch19/T-117')
assert archive.is_dir() and archive.stat().st_dev != Path('/Volumes').stat().st_dev
report = {'status': 'INCOMPLETE', 'before': subprocess.check_output(['df', '-h', '/'], text=True),
          'archived': [], 'removed': []}

def inventory(root):
    return {str(p.relative_to(root)): p.lstat().st_size for p in root.rglob('*')
            if p.is_symlink() or p.is_file()}

try:
    for original, destination in [
        (Path('/private/tmp/t117-build-01'), archive / 'failure-build-01'),
        (Path('/private/tmp/t117-previous-Enchanted-0.1.0.app'), archive / 'previous-Enchanted-0.1.0.app'),
    ]:
        assert original.is_dir() and not original.is_symlink() and not destination.exists()
        before = inventory(original)
        shutil.copytree(original, destination, symlinks=True)
        assert inventory(destination) == before, 'Archive file count or byte count mismatch; original preserved'
        report['archived'].append({'original': str(original), 'archive': str(destination),
                                   'files': len(before), 'bytes': sum(before.values())})
        shutil.rmtree(original)
    # All output was accepted and the installed app / Downloads zip are retained.
    for original in [Path('/private/tmp/t117-build-02'), Path('/private/tmp/a2a-build-t117-02'),
                     Path('/private/tmp/t117-tools')]:
        assert original.is_dir() and not original.is_symlink()
        shutil.rmtree(original)
        report['removed'].append(str(original))
    server = json.loads((archive / 'server.json').read_text(encoding='utf-8'))
    process = subprocess.check_output(['ps', '-p', str(server['pid']), '-o', 'command='], text=True)
    assert 'http.server 8617 --bind 127.0.0.1 --directory docs' in process
    os.kill(server['pid'], 15)
    report['status'] = 'PASS'
finally:
    report['after'] = subprocess.check_output(['df', '-h', '/'], text=True)
    (archive / 'cleanup.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report), flush=True)
