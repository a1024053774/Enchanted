"""Exercise the C-I2 clock check across fresh Python processes; no scene or keys."""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

import t078_09c_driver as c
import t078_09b_i1_permission as permission


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def worker(args):
    out = args.output
    if args.worker == 'origin':
        # Let this process acquire a different lifetime from the reader.
        # This is real waiting, not an injected business clock.
        time.sleep(1.25)
        stop = {'id': 'clock-only-stop', 'request_id': 'clock-only-request',
                'created_at': datetime.now(timezone.utc).isoformat()}
        value = c.origin(stop, c.Clock())
        write(out / 'clock-origin.json', value)
        write(out / 'writer.json', {'pid': os.getpid(), 'python': sys.version,
              'executable': sys.executable, 'origin': value,
              'stdlib_monotonic_info': vars(time.get_clock_info('monotonic'))})
        return 0
    start = json.loads((out / 'clock-origin.json').read_bytes())
    reads = {}
    clock = c.Clock()
    class Tracked:
        def wall(self): reads['wall_ms'] = clock.wall(); return reads['wall_ms']
        def mono(self): reads['mono_ms'] = clock.mono(); return reads['mono_ms']
    plan = {'scene': '09C', 'clock_origin_file': str(out / 'clock-origin.json')}
    # Only the already-covered business binding lookup is a fixture. The
    # permission entry, both Clock calls, origin file and process boundary are real.
    error = None; details = None
    with patch.object(c, 'Clock', Tracked), patch.object(c, 'original_send',
            return_value=(start['stop'], {'request_id': start['stop']['request_id']}, None)):
        try: permission.check_early_C_permission(plan, 'C-I2')
        except ValueError as caught:
            error = str(caught); details = caught.args[0]
    wall_elapsed = reads['wall_ms'] - start['wall_ms']
    mono_elapsed = reads['mono_ms'] - start['mono_ms']
    result = {'status': 'PASS' if error is None else 'INCOMPLETE', 'pid': os.getpid(),
              'python': sys.version, 'executable': sys.executable, 'origin': start, 'reads': reads,
              'wall_elapsed_ms': wall_elapsed, 'monotonic_elapsed_ms': mono_elapsed,
              'difference_ms': wall_elapsed - mono_elapsed, 'error': error, 'details': details,
              'key_writes': 0, 'scene_process_starts': 0}
    write(out / 'reader.json', result)
    return 0 if error is None else 1


def boundaries(out):
    # Independent acceptance values: <=1000ms difference, nonnegative elapsed,
    # a 150000ms scene maximum, and the <90s early harness cutoff.
    start = {'wall_ms': 1800000000000, 'mono_ms': 7000000,
             'stop': {'id': 'clock-only-stop', 'request_id': 'clock-only-request',
                      'created_at': datetime.fromtimestamp(1800000000, timezone.utc).isoformat()}}
    cases = [('normal', 10000, 10000, None), ('positive-1000', 11000, 10000, None),
             ('negative-1000', 9000, 10000, None),
             ('forward-1001', 11001, 10000, 'clock_discontinuity'),
             ('backward-1001', 8999, 10000, 'clock_discontinuity'),
             ('mono-reversed', 1, -1, 'clock_discontinuity'),
             ('past-150s', 150001, 150001, 'scenario_deadline_150_seconds')]
    results = []
    for label, wall_delta, mono_delta, expected in cases:
        class Fixed:
            def wall(self): return start['wall_ms'] + wall_delta
            def mono(self): return start['mono_ms'] + mono_delta
        error = None
        try: c.timing(start, Fixed())
        except ValueError as caught: error = str(caught)
        assert (error is None) if expected is None else (error and expected in error), (label, error)
        results.append({'case': label, 'status': 'PASS', 'error': error, 'key_writes': 0})
    # A changed stop must still be rejected before the clock is used.
    write(out / 'bound-clock.json', start)
    plan = {'scene': '09C', 'clock_origin_file': str(out / 'bound-clock.json')}
    other = copy.deepcopy(start['stop']); other['id'] = 'different-stop'
    with patch.object(c, 'original_send', return_value=(other, {'request_id': other['request_id']}, None)), \
         patch.object(c, 'Clock', side_effect=AssertionError('clock must not be used before binding')):
        try: permission.check_early_C_permission(plan, 'C-I2')
        except ValueError as error: assert str(error) == 'C_original_clock_stop_mismatch'
        else: raise AssertionError('wrong clock stop accepted')
    results.append({'case': 'wrong-stop-before-clock', 'status': 'PASS', 'key_writes': 0})
    return results


def retain_origin(out):
    from test_t078_09c_real_chain import CScene
    scene = CScene.__new__(CScene)
    output = out / 'cleanup'; output.mkdir()
    with tempfile.TemporaryDirectory(prefix='t078-clock-retention-', dir='/private/tmp') as temporary:
        scene.root = Path(temporary) / 'owned-root'; scene.root.mkdir()
        scene.output = output; scene.state = scene.root / 'state'
        scene.children = []; scene.ready = None; scene.request_dir = None
        raw = (out / 'clock-origin.json').read_bytes()
        (scene.root / 'clock-origin.json').write_bytes(raw)
        result = scene.cleanup()
        assert result['status'] == 'PASS' and not scene.root.exists()
        assert (output / 'clock-origin.json').read_bytes() == raw
        assert result['post_stop_SQLite_reads'] == 0
    return {'status': 'PASS', 'byte_readback': True, 'scene_process_starts': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', choices=['origin', 'reader'])
    parser.add_argument('--known-bad-revision')
    args = parser.parse_args(); args.output = args.output.resolve()
    if args.known_bad_revision:
        filename = 'workbench/tests/t078_09c_driver.py'
        source = subprocess.check_output(['git', 'show', args.known_bad_revision + ':' + filename], cwd=Path(__file__).resolve().parents[2])
        # Load the exact old clock/entry code in this process only. Never
        # revert or replace the worktree's candidate.
        exec(compile(source, str(Path(__file__).parent / 't078_09c_driver.py'), 'exec'), c.__dict__)
    if args.worker: return worker(args)
    out = args.output; out.mkdir(parents=True, exist_ok=False)
    if args.known_bad_revision: (out / 'known-bad-driver.py').write_bytes(source)
    processes = []
    for mode in ['origin', 'reader']:
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', mode, '--output', str(out)]
        if args.known_bad_revision: argv += ['--known-bad-revision', args.known_bad_revision]
        child = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        value = {'argv': argv, 'exit_code': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr}
        write(out / (mode + '-process.json'), value); processes.append(value)
        if mode == 'origin': assert child.returncode == 0, value
    writer = json.loads((out / 'writer.json').read_bytes()); reader = json.loads((out / 'reader.json').read_bytes())
    assert writer['pid'] != reader['pid']
    checks = boundaries(out)
    retention = retain_origin(out)
    status = 'PASS' if reader['status'] == 'PASS' else 'INCOMPLETE'
    result = {'status': status, 'scope': __doc__, 'cross_process': reader, 'boundaries': checks, 'origin_retention': retention,
              'auxiliary_python_processes': 2, 'all_children_exited': True, 'ports': 0,
              'vendor_CLIs': 0, 'model_turns': 0, 'key_writes': 0}
    write(out / 'result.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
