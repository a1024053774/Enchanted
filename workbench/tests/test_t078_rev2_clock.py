"""Observe >120 seconds with system clocks and a deterministic window only."""
import argparse
import json
from pathlib import Path
import signal
import time
import traceback
from t078_09c_driver import Clock, conditional_enter
from t078_rev2_tools_cases import permission_fixture, check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    def deadline(*_): raise TimeoutError('system_clock_fixture_hard_deadline_145_seconds')
    previous = signal.signal(signal.SIGALRM, deadline); signal.alarm(145)
    record = {'status': 'INCOMPLETE', 'clock': 'system time.time and time.monotonic; no fast-forward',
              'window': 'deterministic spy; no Electron/CLI/daemon/API/model', 'model_turns': 0}
    wall, mono = time.time(), time.monotonic()
    try:
        template, window, origin, _ = permission_fixture(out / 'fixture', Clock())
        result = conditional_enter(template, window, origin, out / 'enter')
        check(result['status'] == 'PASS' and window.keys == [b'\r'], 'one conditional Enter')
        check(time.monotonic() - mono > 120 and time.time() - wall > 120, 'independent real elapsed >120 seconds')
        record.update(status='PASS', elapsed_wall_seconds=time.time() - wall, elapsed_monotonic_seconds=time.monotonic() - mono,
                      enter_at=result['enter_at'], key_count=len(window.keys))
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        signal.alarm(0); signal.signal(signal.SIGALRM, previous)
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False)); return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
