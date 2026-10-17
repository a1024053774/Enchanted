"""Isolated wait/reap diagnosis. No scene, API, model, signal or gate command."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

SOURCE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from t078_raw_retention import NativeRuntime, require, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    def timeout(*_): raise TimeoutError('diagnostic_hard_timeout_20_seconds')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(20)
    result = {'status': 'INCOMPLETE', 'signals_sent': [], 'scene_processes_started': 0,
              'purpose': 'test unreaped direct child hypothesis, not reconstruct historical PID evidence'}
    child = None
    def ps(tag):
        probe = subprocess.run(['/bin/ps', '-ww', '-p', str(child.pid), '-o',
                                'pid=,ppid=,pgid=,stat=,lstart=,command='],
                               capture_output=True, text=True, timeout=3, env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
        save(out / (tag + '.json'), {'exit': probe.returncode, 'stdout': probe.stdout, 'stderr': probe.stderr})
        require(not probe.stderr.strip() and probe.returncode in (0, 1), 'ps_failed')
        return probe
    try:
        # Only this original Popen handle can reap the diagnostic child.
        child = subprocess.Popen([sys.executable, '-I', '-B', '-c', 'import os,time; time.sleep(.2); os._exit(0)'],
                                 start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result.update(harness_pid=os.getpid(), child_pid=child.pid, owned_test_children_started=1)
        until = time.monotonic() + 3; index = 0
        while True:
            observation = ps('before-reap-' + str(index)); index += 1
            cells = observation.stdout.strip().split(None, 9)
            if len(cells) == 10 and 'Z' in cells[3]:
                require(int(cells[1]) == os.getpid(), 'zombie_not_direct_owned_child'); break
            require(time.monotonic() < until, 'no_zombie_observed'); time.sleep(.05)
        runtime = NativeRuntime({'processes': {'daemon': {'pid': child.pid}}})
        try: runtime.wait_absent(['daemon'], .3)
        except ValueError as error:
            require(str(error) == 'owned_process_exit_unconfirmed', 'unexpected_red_reason')
            result['red'] = {'status': 'EXPECTED_RED', 'error': repr(error), 'actual_ps_state': cells[3]}
        else: raise ValueError('known_bad_wait_did_not_fail')
        # Reap only our known child; still require real ps absence afterward.
        result['child_exit_code'] = child.wait(timeout=2)
        require(result['child_exit_code'] == 0, 'diagnostic_child_nonzero')
        runtime.wait_absent(['daemon'], 1)
        final = ps('after-reap'); require(final.returncode == 1 and not final.stdout.strip(), 'PID_not_absent_after_reap')
        result.update(status='PASS', green='known child reaped, then unchanged wait_absent confirms ps absence',
                      historical_failed_PID='INCOMPLETE; this controlled test does not identify it')
    except Exception as error: result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        if child is not None:
            try: child.wait(timeout=3)
            except subprocess.TimeoutExpired: result.update(status='INCOMPLETE', cleanup='diagnostic child exit unconfirmed; no signal')
        signal.alarm(0)
        save(out / 'result.json', result)
    print(json.dumps(result, ensure_ascii=False)); return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
