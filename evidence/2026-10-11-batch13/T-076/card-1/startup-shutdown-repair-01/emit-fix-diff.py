"""Emit the focused repair diff against the frozen red source archive."""
import difflib
from pathlib import Path
import sys
import tarfile

archive_path, source, output = map(Path, sys.argv[1:])
paths = ['src/daemon.ts', 'src/gates/core.ts', 'README.md', 'tests/run_t076_real.py',
    'tests/startup_shutdown_host.ts', 'tests/test_startup_shutdown_e2e.py', 'tests/run_t076_startup_shutdown.py']
chunks = []
with tarfile.open(archive_path, 'r:gz') as archive:
    for rel in paths:
        old = archive.extractfile('workbench/' + rel).read().decode('utf-8')
        new = (source / 'workbench' / rel).read_text(encoding='utf-8')
        chunks += difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile='red/workbench/' + rel, tofile='candidate/workbench/' + rel)
with output.open('x', encoding='utf-8') as stream: stream.write(''.join(chunks))
print(str(output))
