#!/usr/bin/env python3
"""Exercise the actual runner extraction blocks without starting a daemon.

Expected archive handling is controller #115: ordinary safe files plus only
same-directory hook.py symlinks directly under workbench/hooks. Every other
symlink, hardlink, absolute path and parent traversal remains forbidden.
"""
import ast
import io
import json
import os
from pathlib import Path
import stat
import tarfile
import tempfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
E = ROOT / 'evidence/2026-10-11-batch13/T-077'
OUT = E / 'preimage-archive-check-03'
OUT.mkdir(exist_ok=False)
workspace = Path(tempfile.mkdtemp(prefix='t077-archive-03-', dir='/tmp'))


def extraction_block(path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    blocks = [node for node in ast.walk(tree) if isinstance(node, ast.With) and any(
        isinstance(item.context_expr, ast.Call) and item.context_expr.args and
        isinstance(item.context_expr.args[0], ast.Name) and item.context_expr.args[0].id == 'archive_path'
        for item in node.items)]
    if len(blocks) != 1: raise RuntimeError('The actual runner archive block is not unique')
    return compile(ast.Module(body=blocks, type_ignores=[]), str(path) + '#archive-block-only', 'exec')


def run_block(block, archive_path, target):
    target.mkdir(parents=True)
    exec(block, {'archive_path': archive_path, 'preimage': target, 'tarfile': tarfile, 'Path': Path})


log = [json.loads(line) for line in (E / 'outside-rebase-final-02/commands.jsonl').read_text(encoding='utf-8').splitlines()]
row = next(row for row in log if row['phase'] == 'finished' and row['argv'][:2] == ['git', 'archive'])
archive_path = Path(row['stdout_file'])
with tarfile.open(archive_path, 'r:') as archive:
    members = archive.getmembers()
links = [member for member in members if member.issym()]
if len(links) != 26 or any(Path(m.name).parent != Path('workbench/hooks') or m.linkname != 'hook.py' for m in links):
    raise RuntimeError('Original failed archive differs from the controller diagnosis')
old = extraction_block(E / 'run-rebase-final-02.py')
new = extraction_block(E / 'run-rebase-final-03.py')
before = None
try:
    run_block(old, archive_path, workspace / 'before')
except RuntimeError as error:
    before = str(error)
if before != 'Unexpected preimage archive entry': raise AssertionError('Original runner must reproduce its archive refusal')

target = workspace / 'after'
target.mkdir(); hooks = target / 'workbench/hooks'; hooks.mkdir(parents=True)
# The phase first clones current source. Rebuild existing symlinks, not regular
# files or their targets, when overlaying the committed preimage archive.
for member in links: (target / member.name).symlink_to('hook.py')
exec(new, {'archive_path': archive_path, 'preimage': target, 'tarfile': tarfile, 'Path': Path})
with tarfile.open(archive_path, 'r:') as archive:
    for member in archive.getmembers():
        path = target / member.name
        if member.issym():
            assert path.is_symlink() and os.readlink(path) == 'hook.py', member.name
        elif member.isfile():
            assert path.read_bytes() == archive.extractfile(member).read(), member.name
            assert stat.S_IMODE(path.stat().st_mode) == member.mode, member.name

bad = [
    ('outside-hooks', 'workbench/src/link', tarfile.SYMTYPE, 'hook.py'),
    ('nested-hook-directory', 'workbench/hooks/nested/link', tarfile.SYMTYPE, 'hook.py'),
    ('parent-target', 'workbench/hooks/link', tarfile.SYMTYPE, '../hook.py'),
    ('absolute-target', 'workbench/hooks/link', tarfile.SYMTYPE, '/tmp/hook.py'),
    ('different-target', 'workbench/hooks/link', tarfile.SYMTYPE, 'other.py'),
    ('dot-target', 'workbench/hooks/link', tarfile.SYMTYPE, './hook.py'),
    ('hard-link', 'workbench/hooks/link', tarfile.LNKTYPE, 'hook.py'),
    ('absolute-member', '/outside.py', tarfile.REGTYPE, ''),
    ('parent-member', '../outside.py', tarfile.REGTYPE, ''),
]
rejected = []
for name, member_name, kind, linkname in bad:
    path = workspace / (name + '.tar')
    with tarfile.open(path, 'w') as archive:
        member = tarfile.TarInfo(member_name); member.type = kind; member.linkname = linkname
        archive.addfile(member)
    error = None
    try: run_block(new, path, workspace / name)
    except RuntimeError as caught: error = str(caught)
    assert error == 'Unexpected preimage archive entry', name
    rejected.append(name)

report = {'status': 'PASS', 'scope': 'actual runner archive blocks only; not product acceptance',
    'original_archive': str(archive_path), 'git_archive_command': row['argv'], 'visible_members': len(members),
    'visible_pax_global_headers': [m.name for m in members if m.type == b'g'],
    'before': {'error': before, 'reproduced': True}, 'after': {'same_directory_hook_symlinks': len(links),
    'regular_file_bytes_and_modes_preserved': True, 'rejected': rejected},
    'temporary_outputs': str(workspace), 'real_codex_turns': 0}
with (OUT / 'run.json').open('x', encoding='utf-8') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps(report, ensure_ascii=False))
