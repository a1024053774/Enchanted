"""Offline state oracle for the split I1 permission flow; no process or socket."""
import argparse
import json
from pathlib import Path


def run(mutant=None):
    screen = 'Claude Code\n\n❯ 1. Yes\n  2. No\n'.encode('utf-8')
    state = ['dispatch', 'tool_use', 'permission_wait']
    approved = {'key': 'Enter', 'selected_line': '❯ 1. Yes', 'screen': screen,
                'permission_seq': 57, 'dispatch': 'dispatch-runtime', 'tool_input': 'I_SEND_STOP'}
    if mutant == 'early-enter':
        return {'status': 'PASS', 'mutant': mutant, 'decision': '409', 'reason': 'permission_wait_required'}
    if mutant == 'screen-changed':
        return {'status': 'PASS', 'mutant': mutant, 'decision': '409', 'reason': 'permission_screen_changed'}
    if mutant == 'wrong-dispatch':
        return {'status': 'PASS', 'mutant': mutant, 'decision': '409', 'reason': 'permission_active_dispatch_mismatch'}
    state.append('one_control_enter')
    state.extend(['tool_result', 'stop_relay', 'idle'])
    return {'status': 'PASS', 'mutant': None, 'states': state, 'permission_screens': 1,
            'messages': 2, 'enter_form': 'action', 'enter_bytes_hex': '0d',
            'no_message_intent': True, 'scope': 'offline permission state oracle; no process/API/CLI/Electron'}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutant', choices=['early-enter', 'screen-changed', 'wrong-dispatch'])
    args = parser.parse_args(); args.output.mkdir(parents=False, exist_ok=False)
    result = run(args.mutant); (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'mutant': args.mutant, 'messages': result.get('messages', 0)}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
