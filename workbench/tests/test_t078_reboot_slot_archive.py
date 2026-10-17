"""Local archive safety check. No external slot, ps, lsof, signal or removal.

Failure modes: link traversal copies an outside member; archive omits a file;
archive bytes differ; source mutation occurs before readback. This focused
check proves link and byte preservation; it does not prove actual cleanup.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tarfile
import tempfile

SOURCE = Path(__file__).resolve().parents[2]
SCRIPT = SOURCE / 'evidence/2026-10-11-batch13/T-078/cleanup-slot-after-reboot-09a2.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    spec = importlib.util.spec_from_file_location('slot_cleanup', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = Path(tempfile.mkdtemp(prefix='t078-slot-archive-'))
    slot = root / 'owned-slot'
    slot.mkdir()
    (slot / 'dist').mkdir()
    expected = b'Independent slot fixture\x00\xff\n'
    (slot / 'dist/main.mjs').write_bytes(expected)
    outside = root / 'outside'
    outside.mkdir()
    (outside / 'never-copy.txt').write_text('Outside target must remain outside\n', encoding='utf-8')
    (slot / 'linked-directory').symlink_to(outside, target_is_directory=True)
    (slot / 'broken-link').symlink_to(root / 'missing')
    checks = []
    archive = root / 'positive.tar.gz'
    module.archive_and_verify(slot, archive)
    with tarfile.open(archive) as stream:
        if stream.extractfile('owned-slot/dist/main.mjs').read() != expected:
            raise RuntimeError('Independent file oracle differs')
        if not stream.getmember('owned-slot/linked-directory').issym():
            raise RuntimeError('Link was not preserved')
        if 'owned-slot/linked-directory/never-copy.txt' in stream.getnames():
            raise RuntimeError('Outside target was archived')
    checks.append({'name': 'exact_bytes_and_links', 'status': 'PASS'})
    # Known-bad implementation: follow live links and omit the broken link.
    (slot / 'broken-link').unlink()
    original = module.tarfile.open

    def follow_links(*values, **options):
        if options.get('dereference') is False:
            options['dereference'] = True
        return original(*values, **options)

    module.tarfile.open = follow_links
    caught = None
    try:
        module.archive_and_verify(slot, root / 'mutant.tar.gz')
    except RuntimeError as error:
        caught = str(error)
    finally:
        module.tarfile.open = original
    if caught != 'Archive member set differs':
        raise RuntimeError('Known-bad link traversal was not rejected: ' + repr(caught))
    with tarfile.open(root / 'mutant.tar.gz') as stream:
        if stream.extractfile('owned-slot/linked-directory/never-copy.txt').read() != b'Outside target must remain outside\n':
            raise RuntimeError('Mutation did not actually traverse the link')
    checks.append({'name': 'known_bad_follow_links_rejected', 'status': 'PASS', 'diagnostic': caught})
    result = {'status': 'PASS', 'argv': sys.argv, 'checks': checks, 'fixture': str(root),
              'scope': 'Local archive helper only; actual slot cleanup remains unexecuted',
              'external_writes': 0, 'process_signals': 0, 'vendor_cli_starts': 0}
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
