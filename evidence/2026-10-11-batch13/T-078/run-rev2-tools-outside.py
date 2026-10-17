"""主控沙箱外串行排练；不启动原生角色 CLI、Electron 或模型。"""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
import time

SOURCE = Path(__file__).resolve().parents[3]
TESTS = SOURCE / 'workbench/tests'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    suites = [
        ('contracts', 'test_t078_rev2_tools.py', [], 30),
        ('metadata-atomic', 'test_t078_rev2_meta_atomic.py', [], 10),
        ('C-handler', 'test_t078_rev2_rehearsal.py', ['--offline'], 30),
        ('B-captured-HTTP', 'test_t078_09b_fake_api_http_claude.py', [], 30),
        ('C-real-HTTP-clock', 'test_t078_rev2_rehearsal.py', [], 230),
        ('API-SIGTERM', 'test_t078_09b_fake_api_stop.py', ['--expect', 'green'], 15),
    ]
    record = {'status': 'INCOMPLETE', 'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
              'role_CLIs': 0, 'models': 0, 'Electron': 0, 'suites': []}
    for name, file, extra, timeout in suites:
        script = TESTS / file
        assert script.is_file(), script
        ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
        command = [sys.executable, '-B', str(script), '--output', str(out / name), *extra]
        row = {'name': name, 'command': command, 'timeout_seconds': timeout}; record['suites'].append(row)
        if args.check_only: continue
        start = time.monotonic()
        value = subprocess.run(command, cwd=SOURCE, capture_output=True, timeout=timeout, start_new_session=True)
        (out / (name + '.stdout.bin')).write_bytes(value.stdout); (out / (name + '.stderr.bin')).write_bytes(value.stderr)
        row.update(exit_code=value.returncode, elapsed_seconds=time.monotonic() - start)
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if value.returncode:
            print(json.dumps({'status': 'INCOMPLETE', 'stopped_at': name, 'no_retry': True})); return 1
    record['status'] = 'PASS'
    record['scope'] = 'path/AST checks only' if args.check_only else 'test tools only: deterministic files/windows/rows; actual loopback and system clocks'
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False)); return 0


if __name__ == '__main__': raise SystemExit(main())
