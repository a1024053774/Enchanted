"""Bind an unsigned A16 cleanup draft to the owner's actual nine process receipts."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load(path): return json.loads(Path(path).read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['owner', 'archive', 'output']: parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    ready = load(BASE / '09b-a16-stage-a-01/readiness.json')
    owner = load(args.owner)
    assert owner['scene'] == 'A16' and owner['root'] == ready['root'] and owner['source_revision'] == ready['source_revision']
    assert owner['claim_binding'] == ready['target_binding']
    expected = {label: identity['pid'] for label, identity in ready['original_processes'].items()}
    for role in ['ideation', 'executor']:
        p1 = BASE / ('09b-a16-b1-' + role + '-p1-01')
        binding = load(p1 / 'launch-binding.json'); manifest = load(binding['process_manifest'])
        expected[role + '_shell'] = manifest['shell_pid']; expected[role + '_cli'] = manifest['cli']['pid']
        assert owner['roles'][role]['manifest'] == binding['process_manifest']
        assert owner['processes'][role + '_cli']['started'] == manifest['cli']['started']
    assert {label: identity['pid'] for label, identity in owner['processes'].items()} == expected
    for identity in owner['processes'].values():
        assert identity['started'] and identity['command']
    original = load(owner['identity_receipt'])
    assert original['root'] == owner['root'] and original['processes'] == owner['processes']
    assert args.archive.is_absolute() and args.archive.is_relative_to(Path('/Volumes/WD-Elements/a2a-evidence'))
    value = {key: owner[key] for key in ['scene', 'root', 'source_revision', 'target_binding', 'processes']}
    value.update(approved_by=None, approval_ref=None, archive=str(args.archive),
                 retain_failed_scene=False,
                 actions=['Authenticated daemon_stop/panes.shutdown closes owned controllers and target',
                          'One SIGTERM per original API PID after full identity checks',
                          'Verify all nine absent; verify archive/files without SQLite; remove unchanged root'],
                 prerequisite='Byte-verified raw archive and signed independent tar readback, before any stop')
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'output': str(args.output), 'signatures': 'empty', 'signals_sent': []}))


if __name__ == '__main__': main()
