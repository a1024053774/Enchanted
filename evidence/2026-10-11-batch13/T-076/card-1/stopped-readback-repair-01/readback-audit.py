"""Emit the readback repair diff and verify product bytes stayed unchanged."""
import difflib
import json
from pathlib import Path
import sys
import tarfile

archive_path, source, output = map(Path, sys.argv[1:])
output.mkdir(parents=True, exist_ok=False)
paths = ['tests/fixture_artifacts.py', 'tests/test_startup_shutdown_e2e.py',
         'tests/run_t076_real.py', 'tests/test_stopped_readback.py', 'README.md']
with tarfile.open(archive_path, 'r:gz') as archive:
    members = {member.name: member for member in archive.getmembers() if member.isfile() or member.issym()}
    chunks = []
    for rel in paths:
        member = members.get('workbench/' + rel)
        old = archive.extractfile(member).read().decode('utf-8') if member is not None else ''
        new = (source / 'workbench' / rel).read_text(encoding='utf-8')
        chunks += difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile='failed-green/workbench/' + rel if member is not None else '/dev/null',
            tofile='candidate/workbench/' + rel)
    before = {name: ('link', member.linkname) if member.issym() else ('file', archive.extractfile(member).read()) for name, member in members.items()
              if name.startswith(('workbench/src/', 'workbench/hooks/'))}
    after = {'workbench/' + str(path.relative_to(source / 'workbench')):
             ('link', str(path.readlink())) if path.is_symlink() else ('file', path.read_bytes())
             for part in ('src', 'hooks') for path in (source / 'workbench' / part).rglob('*') if path.is_file() or path.is_symlink()}
same = before == after
with (output / 'readback-only.diff').open('x', encoding='utf-8') as stream: stream.write(''.join(chunks))
record = {'status': 'PASS' if same else 'INCOMPLETE', 'argv': sys.argv,
          'product_src_hooks_unchanged': same, 'product_files': len(before), 'real_codex_turns': 0}
with (output / 'scope.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(record))
raise SystemExit(0 if same else 1)
