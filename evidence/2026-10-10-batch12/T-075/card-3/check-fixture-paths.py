#!/usr/bin/env python3
"""Read-only fixture-code check; allocate paths without Git, sockets, or models."""
import argparse
import ast
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
root = Path(__file__).resolve().parents[4]
tests = root / 'workbench/tests'
sys.path.insert(0, str(tests))
import test_daemon_gates_e2e as daemon_tests

source = ast.parse((tests / 'test_daemon_gates_e2e.py').read_text(encoding='utf-8'))
main = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
allocation = next(node for node in main.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Attribute) and target.attr == 'ARTIFACT_ROOT' for target in node.targets))
namespace = {'Path': Path, 'tempfile': tempfile, 'previous': daemon_tests.previous}
exec(compile(ast.Module(body=[allocation], type_ignores=[]), '<actual artifact-root allocation>', 'exec'), namespace)
parent = ast.parse((tests / 'test_task_cards_e2e.py').read_text(encoding='utf-8'))
case_class = next(node for node in parent.body if isinstance(node, ast.ClassDef) and node.name == 'TaskCardsCLI')
setup = next(node for node in case_class.body if isinstance(node, ast.FunctionDef) and node.name == 'setUp')
namespace['ARTIFACT_ROOT'] = daemon_tests.previous.ARTIFACT_ROOT
rows = []
for name in unittest.defaultTestLoader.getTestCaseNames(daemon_tests.DaemonCards):
    namespace['self'] = SimpleNamespace(_testMethodName=name)
    exec(compile(ast.Module(body=setup.body[:1], type_ignores=[]), '<actual case-root allocation>', 'exec'), namespace)
    socket_path = namespace['self'].root.resolve() / 'state/control.sock'
    rows.append({'test': name, 'socket_path': str(socket_path), 'utf8_bytes': len(str(socket_path).encode('utf-8'))})
failed = [row for row in rows if row['utf8_bytes'] > 103]
record = {'status': 'PASS' if not failed else 'INCOMPLETE', 'scope': 'path allocation only; no daemon or acceptance run',
          'command': sys.argv, 'limit_bytes': 103, 'failed': len(failed), 'cases': rows}
(args.output / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': record['status'], 'cases': len(rows), 'failed': len(failed),
                  'maximum_bytes': max(row['utf8_bytes'] for row in rows)}, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
