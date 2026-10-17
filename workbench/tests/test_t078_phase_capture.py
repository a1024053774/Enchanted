"""Run the actual phase permission-capture branch with only output I/O replaced."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import uuid

SOURCE = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--module', type=Path, default=SOURCE / 'workbench/tests/t078_09b_phase_driver.py')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('phase_capture_candidate', args.module)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    payload = (('outside-source-' + uuid.uuid4().hex + '\n').encode() * 4000)[:155701]
    with tempfile.TemporaryDirectory(prefix='t078-phase-capture-', dir='/tmp') as tmp:
        root = Path(tmp); p1 = root / 'p1'; p1.mkdir(); role = root / 'roles/executor'; role.mkdir(parents=True)
        launch, session, dispatch, prompt = [str(uuid.uuid4()) for _ in range(4)]
        inp = {'root': str(root), 'preset': 'executor', 'launch': launch, 'session': session}
        (p1 / 'input.json').write_text(json.dumps(inp))
        approval = root / 'approval.json'; approval.write_text(json.dumps({'role': 'executor', 'stage': 'E5', 'p1_materials': str(p1)}))
        (role / ('bound-' + dispatch + '.json')).write_text(json.dumps({'id': dispatch, 'seq': 29, 'text': 'independent registered input'}))
        event = {'seq': 71, 'type': 'permission_wait', 'data': {'prompt_id': prompt}}
        offsets = []
        def output_gate(_root, command, *argv):
            assert command == 'pane_output'
            offset = int(argv[argv.index('--offset') + 1]); offsets.append(offset)
            raw = payload[offset:offset + 65536]
            return {'launch': launch, 'start_offset': offset, 'next_offset': offset + len(raw),
                    'total_bytes': len(payload), 'data_base64': base64.b64encode(raw).decode()}
        with patch.object(module, 'context', return_value=({'root': str(root)}, inp)), \
             patch.object(module, 'accepted', return_value=[{'phase': 'E5', 'dispatch_id': dispatch}]), \
             patch.object(module, 'phase_events', return_value=([event], {}, prompt)), \
             patch('t078_09b_i1_driver.gate', side_effect=output_gate):
            result = module.execute(p1, root, approval, root / 'capture', 'E5', 'dispatch')
        actual = Path(result['permission_screen']).read_bytes()
        passed = (actual == payload and result.get('permission_screen_capture', {}).get('complete') is True
                  and offsets[-1] == len(payload) and result['permission_event'] == event)
        (args.output / 'expected.bin').write_bytes(payload); (args.output / 'actual.bin').write_bytes(actual)
        report = {'status': 'PASS' if passed else 'INCOMPLETE', 'entry': str(args.module), 'offsets': offsets,
                  'expected_bytes': len(payload), 'actual_bytes': len(actual), 'capture': result.get('permission_screen_capture'),
                  'scope': 'Actual phase execute capture branch; identity/event/output transport fixtures only; no daemon/API/CLI/key'}
    assert not root.exists()
    (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'expected_bytes': len(payload), 'actual_bytes': len(actual)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
