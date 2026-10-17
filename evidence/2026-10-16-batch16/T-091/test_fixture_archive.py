#!/usr/bin/env python3
"""Local filesystem contract: links are entries, never archive traversal edges.

Failure cases: rejecting links; copying target bytes/directories; dangling or
cyclic links; losing a raw target; same-byte-length target substitution; wrong
file/byte totals; hiding targets outside the original or copied fixture.
No Electron/CLI/PTY/ps/AppKit or external-volume writes. Git is read-only.
Only newly created local test data is deleted on PASS; unexpected failures retain it.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import run_red

BAD = '2f29e666c76d1581ea554b9c5d7595cb5a13639e'
SOURCE_PATH = 'evidence/2026-10-16-batch16/T-091/run_red.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().parent != Path(__file__).resolve().parent or args.output.exists():
        raise RuntimeError('new_local_text_report_required')
    group = Path(tempfile.mkdtemp(prefix='.archive-check-', dir=args.output.resolve().parent))
    result = {'status': 'INCOMPLETE', 'scope': 'real local file/symlink copy only; no original fixture mutation',
              'known_bad': BAD, 'temporary': str(group), 'checks': [], 'keys': [], 'model_turns': 0}
    try:
        fixture, outside = group / 'fixture', group / 'outside'
        fixture.mkdir(); outside.mkdir()
        (fixture / 'dir').mkdir(); (fixture / 'empty').mkdir()
        (fixture / 'real.txt').write_bytes(b'ABC')
        (fixture / 'dir/文本.txt').write_bytes(b'12345')
        (outside / 'sentinel').write_bytes(b'X' * 65536)
        targets = {'internal-file': 'real.txt', 'absolute-internal': str(fixture / 'real.txt'),
                   'internal-dir': 'dir', 'relative-external': '../outside/sentinel',
                   'absolute-external': str(outside / 'sentinel'), 'external-dir': '../outside',
                   'dangling': 'missing.txt', 'external-dangling': '../outside/missing.txt',
                   'cycle': 'cycle', 'unicode-relative': 'dir/文本.txt'}
        for name, target in targets.items():
            os.symlink(target, fixture / name)
        result['inputs'] = {'regular_payload_bytes': 8, 'targets': targets, 'outside_sentinel_bytes': 65536}
        old_source = subprocess.check_output(['git', 'show', f'{BAD}:{SOURCE_PATH}'], text=True)
        old = next(node for node in ast.parse(old_source).body if isinstance(node, ast.FunctionDef) and node.name == 'inventory')
        namespace = {}
        exec(compile(ast.Module(body=[old], type_ignores=[]), '<known-bad inventory>', 'exec'), namespace)
        try:
            namespace['inventory'](fixture)
        except RuntimeError as error:
            assert str(error) == 'fixture_archive_contains_symlink', error
            result['checks'].append({'name': 'known_bad_rejects_valid_links', 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('known-bad inventory unexpectedly accepted the required linked fixture')
        copied = group / 'copied'
        manifest = run_red.archive_fixture(fixture, copied)
        expected_link_bytes = sum(len(os.fsencode(target)) for target in targets.values())
        assert manifest['regular_files'] == 2 and manifest['regular_bytes'] == 8, manifest
        assert manifest['files'] == 12 and manifest['symlink_count'] == 10 and manifest['directories'] == 2, manifest
        assert manifest['bytes'] == 8 + expected_link_bytes and manifest['symlink_bytes'] == expected_link_bytes, manifest
        assert (copied / 'real.txt').read_bytes() == b'ABC' and (copied / 'dir/文本.txt').read_bytes() == b'12345'
        assert (outside / 'sentinel').stat().st_size == 65536
        links = {row['path']: row for row in manifest['symlinks']}
        external = {'relative-external', 'absolute-external', 'external-dir', 'external-dangling'}
        for name, target in targets.items():
            assert (copied / name).is_symlink() and os.readlink(copied / name) == target
            assert links[name]['target'] == target and links[name]['outside_fixture'] == (name in external), links[name]
            assert links[name]['outside_archive_fixture'] == (name in external or name == 'absolute-internal'), links[name]
        result['checks'].append({'name': 'real_copy_preserves_10_link_entries_and_targets', 'status': 'PASS', 'manifest': manifest})
        real_copy = shutil.copytree

        def wrong_target(source, destination, **options):
            real_copy(source, destination, **options)
            link = Path(destination) / 'internal-file'
            link.unlink()
            os.symlink('else.txt', link)  # Same encoded length as real.txt; totals alone cannot detect this.

        with patch.object(run_red, 'shutil', SimpleNamespace(copytree=wrong_target)):
            try:
                run_red.archive_fixture(fixture, group / 'wrong-target-copy')
            except RuntimeError as error:
                assert str(error) == 'archive_file_count_bytes_or_link_target_mismatch', error
                result['checks'].append({'name': 'same_length_wrong_target_rejected', 'rejected': True})
            else:
                raise AssertionError('same-length changed symlink target passed comparison')
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    run_red.write_json(args.output, result)
    if result['status'] == 'PASS':
        shutil.rmtree(group)  # Only this invocation's newly generated test data.
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
