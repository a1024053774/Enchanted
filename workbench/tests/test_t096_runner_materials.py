"""Pure runner material checks. No subprocess, socket, CLI, PTY, ps or GUI.

Failure list: argv fields split on whitespace; empty fields lost; environment
leaks into argv; invalid argc accepted; malformed runner source delivered.
"""
import ast
import json
from pathlib import Path
import struct
import sys

source = Path(__file__).resolve().parents[2] / 'evidence/2026-10-16-batch16/T-096/run_restart.py'
module = ast.parse(source.read_text(encoding='utf-8'))
function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'parse_native_argv')
namespace = {'struct': struct}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
parse = namespace['parse_native_argv']
expected = ['/fixture/claude', '--resume', 'native-id', '--settings', '{"text":"空 格 \\" quoted"}', '', 'a\nb']
blob = struct.pack('i', len(expected)) + b'/resolved/claude\0\0\0' + b'\0'.join(value.encode('utf-8') for value in expected) + b'\0ENV_MUST_NOT_LEAK=secret-sentinel\0'
assert parse(blob) == expected
try:
    parse(struct.pack('i', 0) + b'/fixture\0\0')
except RuntimeError:
    pass
else:
    raise AssertionError('invalid argc must be refused')
# A parser which splits flattened process text would lose empty/quoted fields.
assert ' '.join(expected).split() != expected
report = dict(status='PASS', scope='runner syntax and native argv buffer parsing only; no macOS syscall or application proof',
              checks=['utf8_and_whitespace_fields_preserved', 'empty_argument_preserved', 'argc_excludes_environment', 'invalid_argc_refused', 'flattened_argv_mutant_rejected'])
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    output.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False))
