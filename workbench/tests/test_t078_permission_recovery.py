"""Prove reference append/binding guards without reading a live scene."""
import argparse
import ast
import base64
import json
from pathlib import Path
import tempfile
import uuid

import recover_t078_permission_screen as recovery


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--omit-prefix-check', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    if args.omit_prefix_check:
        source = Path(recovery.__file__).read_text(encoding='utf-8'); tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'recover')
        guard = next(node for node in function.body if isinstance(node, ast.If)
                     and any(isinstance(item, ast.Constant) and item.value == 'original_screen_not_strict_prefix' for item in ast.walk(node)))
        guard.test = ast.Constant(False)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), 'omit-prefix-check-mutant', 'exec'), recovery.__dict__)
        (args.output / 'mutant.txt').write_text('Only the original_screen_not_strict_prefix guard is disabled in this test process.\n')
    results = []
    for fault in ['good', 'prefix', 'incomplete', 'binding', 'existing-output']:
        with tempfile.TemporaryDirectory(prefix='t078-reference-recovery-', dir='/tmp') as tmp:
            root = Path(tmp); p1 = root / 'p1'; p1.mkdir(); screen = root / 'screen'; screen.mkdir()
            payload = (('independent-' + uuid.uuid4().hex).encode() * 4000)[:90137]
            launch, session, thread = [str(uuid.uuid4()) for _ in range(3)]
            inp = {'root': str(root), 'launch': launch, 'session': session, 'thread': thread,
                   'preset': 'executor', 'code_revision': 'isolated-fixture-business-revision'}
            (p1 / 'input.json').write_text(json.dumps(inp))
            old = root / 'old-screen.bin'; prefix = payload[:65536]
            if fault == 'prefix': prefix = b'wrong' + prefix[5:]
            old.write_bytes(prefix)
            original = {'status': 'READY_FOR_PERMISSION', 'stage': 'E4',
                        'dispatch': {'id': str(uuid.uuid4()), 'seq': 29, 'role': 'executor',
                                     'tool_use': {'input': {'command': 'echo fixture'}}},
                        'permission_event': {'seq': 91, 'launch': launch, 'data': {'session_id': session, 'tool_input': {'command': 'echo fixture'}}},
                        'permission_screen': str(old), 'phase_plan': str(root / 'not-read-plan.json')}
            original_file = root / 'original.json'; original_file.write_text(json.dumps(original)); original_bytes = original_file.read_bytes()
            (screen / 'screen.bin').write_bytes(payload); (screen / 'result.json').write_text('{}')
            pages = [{'start_offset': 0, 'next_offset': 65536, 'total_bytes': len(payload), 'bytes': 65536},
                     {'start_offset': 65536, 'next_offset': len(payload), 'total_bytes': len(payload), 'bytes': len(payload) - 65536},
                     {'start_offset': len(payload), 'next_offset': len(payload), 'total_bytes': len(payload), 'bytes': 0}]
            meta = {'launch': launch, 'session': session, 'directory': str(root / 'repo'),
                    'capture': {'complete': fault != 'incomplete', 'start_offset': 0, 'next_offset': len(payload), 'total_bytes': len(payload), 'pages': pages},
                    'output': {'launch': launch, 'start_offset': 0, 'next_offset': len(payload), 'total_bytes': len(payload), 'data_base64': base64.b64encode(payload).decode()}}
            if fault == 'binding': meta['launch'] = str(uuid.uuid4())
            (screen / 'screen.json').write_text(json.dumps(meta))
            output = root / 'recovery'; approval = root / 'permission-02.json'
            if fault == 'existing-output': output.mkdir(); (output / 'sentinel').write_text('preserve')
            error = None
            try:
                receipt = recovery.recover(p1, original_file, screen, output, approval)
            except ValueError as caught:
                error = str(caught)
            if fault == 'good':
                value = json.loads((output / 'result.json').read_bytes()); ap = json.loads(approval.read_bytes())
                passed = (error is None and Path(value['permission_screen']).read_bytes() == payload
                          and value['dispatch'] == original['dispatch'] and value['permission_event'] == original['permission_event']
                          and ap['approved_by'] is None and ap['approval_ref'] is None and ap['permission_seq'] == 91
                          and ap['screen_file'] == value['permission_screen'] and receipt['original_prefix_matches'])
            else:
                expected = {'prefix': 'original_screen_not_strict_prefix', 'incomplete': 'incomplete_output_capture',
                            'binding': 'recovery_screen_binding_mismatch', 'existing-output': 'recovery_output_exists'}[fault]
                passed = error == expected and not approval.exists() and (not output.exists() or fault == 'existing-output')
            passed = passed and old.read_bytes() == prefix and original_file.read_bytes() == original_bytes
            results.append({'fault': fault, 'status': 'PASS' if passed else 'INCOMPLETE', 'error': error})
        assert not root.exists()
    report = {'status': 'PASS' if all(row['status'] == 'PASS' for row in results) else 'INCOMPLETE',
              'mutant': args.omit_prefix_check, 'cases': results, 'scene_actions': 0, 'scratch_removed': True}
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report)); return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
