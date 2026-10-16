"""Append a complete read-only reference for an existing permission event."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from p1_output import validate_capture

SOURCE = Path(__file__).resolve().parents[2]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'


def recover(p1, original_result, screen_dir, output, approval_output):
    if output.exists() or approval_output.exists():
        raise ValueError('recovery_output_exists')
    inp = json.loads((p1 / 'input.json').read_bytes())
    original = json.loads(original_result.read_bytes())
    meta = json.loads((screen_dir / 'screen.json').read_bytes())
    raw = (screen_dir / 'screen.bin').read_bytes()
    if original['status'] != 'READY_FOR_PERMISSION':
        raise ValueError('original_permission_required')
    if any(meta.get(key) != inp[key] for key in ['launch', 'session']) or meta.get('directory') != str(Path(inp['root']) / 'repo'):
        raise ValueError('recovery_screen_binding_mismatch')
    validate_capture(raw, meta['capture'])
    observed = meta['output']
    if (observed['launch'] != inp['launch'] or observed['start_offset'] != 0
            or observed['next_offset'] != observed['total_bytes'] or observed['total_bytes'] != len(raw)
            or base64.b64decode(observed['data_base64'], validate=True) != raw):
        raise ValueError('recovery_output_incomplete')
    old_screen = Path(original['permission_screen'])
    prefix = old_screen.read_bytes()
    if len(prefix) >= len(raw) or not raw.startswith(prefix):
        raise ValueError('original_screen_not_strict_prefix')
    event = original['permission_event']
    if (event.get('launch') != inp['launch'] or event['data'].get('session_id') != inp['session']
            or original['dispatch'].get('role') != inp['preset']
            or original['dispatch']['tool_use']['input'] != {'command': event['data']['tool_input']['command']}):
        raise ValueError('original_permission_binding_mismatch')
    output.mkdir(parents=False)
    with (output / 'permission-screen.bin').open('xb') as stream:
        stream.write(raw)
    value = dict(original)
    value.update(permission_screen=str((output / 'permission-screen.bin').resolve()), permission_screen_capture=meta['capture'],
                 permission_screen_original=str(old_screen), screen_recovery=str((output / 'recovery.json').resolve()))
    with (output / 'result.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    spec = importlib.util.spec_from_file_location('t078_permission_materials', BASE / 'prepare-a14.py')
    prepare = importlib.util.module_from_spec(spec); spec.loader.exec_module(prepare)
    prepare.permission(SimpleNamespace(result=output / 'result.json', p1=p1, output=approval_output))
    receipt = {'status': 'PASS', 'scope': 'Reference recovery only; no dispatch or live state observation',
               'original_result': str(original_result), 'original_screen': str(old_screen),
               'screen_result': str(screen_dir / 'result.json'), 'new_screen': value['permission_screen'],
               'source_complete_screen': str(screen_dir / 'screen.bin'),
               'original_prefix_bytes': len(prefix), 'complete_bytes': len(raw), 'original_prefix_matches': True,
               'dispatch_preserved': value['dispatch'] == original['dispatch'],
               'permission_event_preserved': value['permission_event'] == event,
               'approval_output': str(approval_output), 'approval_unsigned': True,
               'business_revision': inp['code_revision'], 'live_actions': 0}
    with (output / 'recovery.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser()
    for name in ['p1', 'original-result', 'screen-dir', 'output', 'approval-output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = recover(args.p1.resolve(), args.original_result.resolve(), args.screen_dir.resolve(),
                     args.output.resolve(), args.approval_output.resolve())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
