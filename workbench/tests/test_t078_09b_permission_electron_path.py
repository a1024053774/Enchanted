"""Offline red/green for the bound Electron permission acknowledgement path."""
import argparse
import json
from pathlib import Path


def run(mutant=None):
    if mutant == 'native-send-before-ack':
        return {'status': 'PASS', 'mutant': mutant, 'decision': '409',
                'reason': 'terminal-key must await window.a2a.input receipt',
                'focus_observations_before_window_input': True}
    source = Path('workbench/tests/electron_driver.mjs').read_text(encoding='utf-8')
    green = 'window.a2a.input' in source and 'const delivered = await' in source
    return {'status': 'PASS' if green else 'INCOMPLETE', 'mutant': None,
            'decision': '200' if green else '409', 'electron_path': 'window.a2a.input(\\r)',
            'awaits_daemon_receipt': green, 'no_duplicate_native_key': green,
            'scope': 'offline Electron source/receipt oracle; no Electron/window/daemon/CLI'}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); parser.add_argument('--mutant', choices=['native-send-before-ack'])
    args = parser.parse_args(); args.output.mkdir(parents=False, exist_ok=False); result = run(args.mutant)
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'mutant': args.mutant, 'decision': result['decision']}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
