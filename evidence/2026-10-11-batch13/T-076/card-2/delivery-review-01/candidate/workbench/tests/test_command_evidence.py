"""Check the live-02 fixture diagnosis without Electron, a daemon, or models."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import traceback

from command_evidence import CommandLog, command_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    log = CommandLog(output)
    verdict = {'status': 'INCOMPLETE', 'argv': sys.argv, 'model_turns': 0, 'electron_started': False}
    try:
        original_path = root / 'evidence/2026-10-10-batch12/T-075/card-4/outside-live-02/offline-trace'
        rows = [json.loads(line) for line in (original_path / 'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        failed = rows[12]
        assert failed['argv'][-2:] == ['--offset', '-1'] and failed['exit'] == 2 and failed['stdout'] == ''
        assert 'ERR_PARSE_ARGS_INVALID_OPTION_VALUE' in failed['stderr']
        assert not (original_path / 'window').exists()
        assert (original_path / 'expected-trace.bin').read_bytes() == (original_path / 'cli-trace.bin').read_bytes()
        (output / 'original-failure.json').write_text(json.dumps({'row': 13, **failed}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Same native Node parser and string option type as the CLI, with no
        # socket access. Only the argument spelling changes between cases.
        parser_code = """import { parseArgs } from 'node:util';
try {
  const value = parseArgs({args: process.argv.slice(1), options: {offset: {type: 'string'}}});
  process.stdout.write(JSON.stringify(value.values));
} catch(error) { process.stderr.write(String(error)); process.exitCode = 2; }
"""
        old = log.run(['node', '--input-type=module', '-e', parser_code, '--', '--offset', '-1'], cwd=root)
        assert old.returncode == 2 and old.stdout == '' and 'ERR_PARSE_ARGS_INVALID_OPTION_VALUE' in old.stderr
        fixed = log.run(['node', '--input-type=module', '-e', parser_code, '--', '--offset=-1'], cwd=root)
        assert fixed.returncode == 0 and command_json(fixed) == {'offset': '-1'}
        try:
            command_json(old)
        except RuntimeError as error:
            assert str(old.evidence['stdout_file']) in str(error) and 'command_id' in str(error)
            verdict['parse_diagnostic'] = str(error)
        else:
            raise AssertionError('Empty output must fail JSON parsing with command context')
        # The bytes must exist even when the text decoder cannot read them.
        try:
            log.run([sys.executable, '-B', '-c', "import os; os.write(1,b'raw\\r\\n'); os.write(2,b'\\xff\\x00')"], cwd=root)
        except UnicodeDecodeError:
            entry = log.entries[-1]
            assert Path(entry['stdout_file']).read_bytes() == b'raw\r\n'
            assert Path(entry['stderr_file']).read_bytes() == b'\xff\x00'
        else:
            raise AssertionError('Invalid UTF-8 must remain visible as a decoding failure')
        try:
            log.run([sys.executable, '-B', '-c',
                     "import os,time; os.write(1,b'partial-out'); os.write(2,b'partial-err'); time.sleep(30)"], cwd=root, timeout=1)
        except subprocess.TimeoutExpired:
            entry = log.entries[-1]
            assert Path(entry['stdout_file']).read_bytes() == b'partial-out'
            assert Path(entry['stderr_file']).read_bytes() == b'partial-err'
            assert 'TimeoutExpired' in entry['error'] and entry['traceback']
        else:
            raise AssertionError('The local child must stop at the timeout')
        try:
            log.run([output / 'absent-executable'], cwd=root)
        except FileNotFoundError:
            entry = log.entries[-1]
            assert Path(entry['stdout_file']).read_bytes() == Path(entry['stderr_file']).read_bytes() == b''
            assert entry['traceback']
        else:
            raise AssertionError('A missing executable must fail without hiding its evidence')
        valid = log.run([sys.executable, '-B', '-c', 'print(\'{"text":"中文"}\')'], cwd=root)
        assert command_json(valid) == {'text': '中文'}
        raw_events = [json.loads(line) for line in (output / 'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(raw_events) == 2 * len(log.entries)
        for index, entry in enumerate(log.entries):
            assert raw_events[2 * index]['phase'] == 'started' and raw_events[2 * index]['id'] == entry['id']
            assert raw_events[2 * index + 1]['phase'] == 'finished' and raw_events[2 * index + 1]['id'] == entry['id']
            assert Path(entry['stdout_file']).is_file() and Path(entry['stderr_file']).is_file()
        verdict.update(status='PASS', known_bad='ambiguous CLI argument reproduced',
                       corrected_argument='negative value preserved',
                       raw_output='nonzero exit, UTF-8 decode error, timeout, spawn failure and valid JSON preserved',
                       limitation='Full daemon rejection and Electron check require the controller run')
    except Exception as error:
        verdict.update(error=repr(error), traceback=traceback.format_exc())
    (output / 'results.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
