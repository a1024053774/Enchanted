"""Run bounded pending-delivery checks; runtime suite is handed to the controller."""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['local', 'runtime'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists() and out.parent.is_dir()
    out.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'suite': args.suite, 'checks': [], 'real_model_turns': 0,
              'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    if args.suite == 'local':
        tests = [('pending', 'test_t078_a13_rehearsal.ts', ['--recipient-offline']),
                 ('online', 'test_t078_a13_rehearsal.ts', []),
                 ('ambiguous', 'test_t078_a13_rehearsal.ts', ['--recipient-ambiguous']),
                 ('controller-relay', 'test_t078_controller_relay.ts', []),
                 ('controller-entry', 'test_t078_controller_inbox_entry.ts', []),
                 ('inbox-domain', 'test_t078_inbox_domain.ts', []),
                 ('permission', 'test_t078_permission_accounting.ts', []),
                 ('epochs', 'test_t078_claude_epochs.ts', [str(SOURCE / 'evidence/2026-10-11-batch13/T-078/hook-payloads-08e')]),
                 ('empty-declaration', 'test_t078_empty_declaration_entry.ts', []),
                 ('pane-runtime', 'test_t078_pane_runtime.ts', [])]
        commands = [(name, ['node', str(SOURCE / 'workbench/tests' / test), str(out / name), *extra], 110 if name == 'pending' else 45)
                    for name, test, extra in tests]
        commands.append(('inbox-entry', [sys.executable, '-B', str(SOURCE / 'workbench/tests/test_t078_inbox_entry.py'), '--output', str(out / 'inbox-entry')], 60))
    else:
        commands = [('worker-inbox', [sys.executable, '-B', str(SOURCE / 'workbench/tests/test_t078_input_entry.py'),
                                     '--source', str(SOURCE), '--output', str(out / 'worker-inbox'), '--worker-inbox'], 180)]
    save()
    try:
        for name, command, timeout in commands:
            for token in command:
                if str(token).endswith(('.ts', '.py')):
                    assert Path(token).is_file(), ('missing_command_path', token)
            item = {'name': name, 'command': command, 'timeout_seconds': timeout, 'status': 'INCOMPLETE'}
            record['checks'].append(item); save(); started = time.monotonic()
            with (out / (name + '.stdout.bin')).open('xb') as stdout, (out / (name + '.stderr.bin')).open('xb') as stderr:
                response = subprocess.run(command, cwd=SOURCE, env=env, stdout=stdout, stderr=stderr,
                                          timeout=timeout, start_new_session=True)
            item.update(exit_code=response.returncode, elapsed_seconds=round(time.monotonic() - started, 3)); save()
            assert response.returncode == 0, ('check_failed_no_retry', name, response.returncode)
            result_paths = [out / name / file for file in ['results.json', 'result.json']]
            result_path = next(path for path in result_paths if path.is_file())
            value = json.loads(result_path.read_bytes())
            assert value['status'] == 'PASS', (name, value)
            if 'checks' in value:
                assert all(check['status'] == 'PASS' for check in value['checks'])
                item['assertions'] = len(value['checks'])
            item['status'] = 'PASS'; save()
            print(json.dumps({'check': name, 'status': 'PASS', 'assertions': item.get('assertions')}, ensure_ascii=False), flush=True)
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        save()
    print(json.dumps({'status': record['status'], 'output': str(out), 'error': record.get('error')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
