"""Replay the saved failed rehearsal at CScene.review_permission; no live I/O."""
import argparse
import base64
import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import traceback
from contextlib import closing
from unittest.mock import patch

import test_t078_a14_rehearsal as old
import test_t078_09c_real_chain as chain


def load(path):
    return json.loads(path.read_bytes())


def recorded(recording):
    flow = recording / 'flow'
    commands = sorted(flow.glob('command-*.json'))
    output = next(load(p) for p in commands if 'pane_output' in load(p)['argv'])
    page = json.loads(output['stdout'])
    raw = base64.b64decode(page['data_base64'], validate=True)
    assert page['start_offset'] == 0 and page['next_offset'] == page['total_bytes'] == len(raw)
    # This is the closed, consistent backup, not the live database. Immutable
    # reads also leave its diagnostic WAL/SHM sidecars untouched.
    with closing(sqlite3.connect('file:' + str(flow / 'sqlite/state.sqlite3') + '?mode=ro&immutable=1', uri=True)) as db:
        db.row_factory = sqlite3.Row
        events = [dict(r) for r in db.execute("SELECT * FROM orchestration_events WHERE type='permission_wait'")]
    assert len(events) == 1
    for event in events:
        event['data'] = json.loads(event['data'])
    assert events[0]['launch'] == page['launch']
    command = events[0]['data']['tool_input']['command']
    # The independent oracle is the actual PermissionRequest command, not a
    # command synthesized from the candidate's screen parser.
    assert command not in raw.decode('utf-8') and raw.count('│'.encode()) > 1
    assert '❯ 1. Yes' in raw.decode('utf-8')
    return raw, events, page


def replay(out, original, events, case, entry):
    out.mkdir()
    scene = chain.CScene.__new__(chain.CScene)
    scene.output = out
    scene.events = lambda: copy.deepcopy(events)
    inp = {'launch': events[0]['launch']}
    raw = original
    if case == 'wrong-command':
        raw = raw.replace(b'--from executor', b'--from ideation', 1)
    if case == 'missing-Yes':
        raw = raw.replace('❯ 1. Yes'.encode(), '  1. Yes'.encode())
    calls, attempts, deadlines = [], [], []

    def gate(command, *args):
        assert command == 'pane_output', 'read-only gate contract'
        args = dict(zip(args[::2], args[1::2]))
        assert args['--launch'] == inp['launch']
        offset = int(args['--offset'])
        calls.append(offset)
        data = raw
        if case == 'render-in-progress' and len(attempts) == 1:
            data = raw.split(b'This command requires approval')[0]
        size = 37 if case in ('paged-box', 'total-changed') else len(data)
        fragment = data[offset:offset + size]
        total = len(data)
        if case == 'truncated':
            total += 1  # The declared remaining byte never arrives.
        if case == 'total-changed' and offset:
            total += 1
        if case == 'zero-progress':
            fragment = b''
        return {'launch': 'different-launch' if case == 'wrong-launch' else inp['launch'],
                'start_offset': offset, 'next_offset': offset + len(fragment),
                'total_bytes': total, 'data_base64': base64.b64encode(fragment).decode('ascii')}

    def observe_without_sleep(step, observe, seconds):
        # Replay only the observation predicate. The real runner still uses
        # its unchanged 15-second wall deadline; this is not timing evidence.
        deadlines.append(seconds)
        for number in range(2):
            attempts.append(number)
            value = observe()
            if value:
                return value
        raise TimeoutError({'step': step, 'deadline_seconds': seconds})

    scene.gate = gate
    expected = {'wrapped-box': None, 'paged-box': None, 'render-in-progress': None,
                'wrong-command': 'rehearsal_permission_command_mismatch',
                'missing-Yes': 'TimeoutError', 'truncated': 'output_zero_progress',
                'total-changed': 'output_total_changed', 'zero-progress': 'output_zero_progress',
                'wrong-launch': 'output_launch_mismatch'}[case]
    error = None
    try:
        with patch.object(old, 'wait_for', observe_without_sleep), patch.object(chain, 'wait_for', observe_without_sleep):
            path = Path(entry(scene, inp, 'C-I1'))
        assert path.read_bytes() == raw, 'all observed bytes retained'
        receipt = load(path.with_suffix('.json'))
        assert receipt['permission_event'] == events[0]
        assert receipt['command'] == events[0]['data']['tool_input']['command']
        assert receipt['screen_capture']['complete'] is True
        assert receipt['screen_capture']['next_offset'] == len(raw)
        assert receipt['screen_capture']['pages'][-1]['bytes'] == 0
    except Exception as caught:
        error = type(caught).__name__ + ': ' + str(caught)
    passed = (error is None) if expected is None else (error is not None and expected in error)
    assert deadlines == [15], 'do not lengthen the render deadline'
    return {'case': case, 'status': 'PASS' if passed else 'INCOMPLETE', 'expected_error': expected,
            'observed_error': error, 'page_offsets': calls, 'observation_attempts': len(attempts),
            'deadline_seconds': deadlines[0], 'key_writes': 0, 'process_starts': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recording', type=Path, default=chain.BASE / '09c-fix-01/real-chain-outside-01')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--known-bad-revision')
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'INCOMPLETE', 'scope': __doc__, 'recording': str(args.recording.resolve())}
    try:
        entry = chain.CScene.review_permission
        if args.known_bad_revision:
            path = 'workbench/tests/test_t078_09c_real_chain.py'
            source = subprocess.check_output(['git', 'show', args.known_bad_revision + ':' + path], cwd=chain.SOURCE)
            (out / 'known-bad-real-chain.py').write_bytes(source)
            namespace = {'__file__': str(chain.SOURCE / path), '__name__': 'recorded_known_bad_chain'}
            exec(compile(source, str(chain.SOURCE / path), 'exec'), namespace)
            entry = namespace['CScene'].review_permission
            result['known_bad_revision'] = args.known_bad_revision
        raw, events, page = recorded(args.recording.resolve())
        result['source_screen_bytes'] = len(raw)
        result['source_permission_seq'] = events[0]['seq']
        result['source_page'] = {k: v for k, v in page.items() if k != 'data_base64'}
        cases = ['wrapped-box', 'paged-box', 'render-in-progress', 'wrong-command', 'missing-Yes',
                 'truncated', 'total-changed', 'zero-progress', 'wrong-launch']
        result['cases'] = [replay(out / case, raw, events, case, entry) for case in cases]
        result['status'] = 'PASS' if all(r['status'] == 'PASS' for r in result['cases']) else 'INCOMPLETE'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    chain.save(out / 'result.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
