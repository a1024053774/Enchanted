"""Protocol-only checkpoint checks; no Electron, daemon, PTY, or model."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import traceback

from electron_client import ElectronClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--known-bad', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'INCOMPLETE', 'argv': sys.argv, 'model_turns': 0, 'electron_started': False,
              'limitation': 'Local protocol simulation checks the wait condition; it does not prove rendering'}
    try:
        responses = [json.loads(row['response']) for row in map(json.loads, args.recorded.read_text(encoding='utf-8').splitlines()) if 'response' in row]
        views = [row['value'] for row in responses if 'value' in row]
        assert [view['offset'] for view in views] == [0, 18661]
        assert not views[-1]['terminal'].strip()
        old_class = runpy.run_path(str(args.known_bad))['ElectronClient']
        old = old_class.__new__(old_class)
        old_views = iter(views)
        old.call = lambda *_args, **_values: next(old_views)
        admitted = old.wait(lambda view: view['offset'] >= 17358)
        assert admitted['offset'] == 18661 and not admitted['terminal'].strip()
        result['known_bad'] = 'Saved empty screen passes the old cursor-only wait'

        highwater = 18661
        events = []
        def client_for(observations):
            client = ElectronClient.__new__(ElectronClient)
            index = 0
            def call(command, **values):
                nonlocal index
                events.append({'command': command, **values})
                if command == 'output-checkpoint':
                    return {'highwater': highwater, 'minimum': values['minimum']}
                if command == 'resume-output':
                    return {'resumed_after': highwater}
                assert command == 'inspect'
                value = observations[min(index, len(observations) - 1)]
                index += 1
                return value
            client.call = call
            return client

        ready = {**views[-1], 'terminal': '[protocol simulation] active screen'}
        client = client_for([*views, ready])
        with client.output_checkpoint(17358) as checkpoint:
            assert checkpoint['highwater'] == highwater
            assert checkpoint['view']['terminal'] == ready['terminal']
            assert events[-1]['command'] == 'inspect'
        assert events[-1]['command'] == 'resume-output'
        assert sum(event['command'] == 'inspect' for event in events) == 3
        result['candidate'] = 'Waits through the saved empty screen until text and the fixed cursor both match'

        for label, observation in [('empty', views[-1]), ('overshoot', {**ready, 'offset': highwater + 1})]:
            client = client_for([observation])
            try:
                with client.output_checkpoint(17358, timeout=0):
                    raise RuntimeError('An invalid checkpoint observation was accepted')
            except AssertionError:
                assert events[-1]['command'] == 'resume-output'
            else:
                raise AssertionError(label + ' must fail and release the checkpoint')
        client = client_for([ready])
        try:
            with client.output_checkpoint(17358):
                raise ValueError('injected comparison failure')
        except ValueError:
            assert events[-1]['command'] == 'resume-output'
        (args.output / 'protocol.json').write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result.update(status='PASS', rejected=['empty screen', 'cursor past fixed highwater'],
                      release='normal completion, timeout, and comparison failure')
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
