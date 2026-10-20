"""Execute the actual fixture setup up to daemon launch; no CLI/model/process starts."""
import argparse
import ast
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
assert not args.summary.exists()
module = ast.parse((args.source / 'workbench/tests/run_t112_native.py').read_text())
main = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
start = next(node for node in ast.walk(main) if isinstance(node, ast.FunctionDef) and node.name == 'start')
wrapper = ast.parse('def setup():\n active = None\n return start\n').body[0]
wrapper.body.insert(1, start)
code = compile(ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[])), '<actual native start>', 'exec')
report = dict(status='INCOMPLETE', scope='Actual worker fixture setup; daemon boundary intercepted, no native CLI evidence', cases=[])
class Captured(Exception):
    pass
with tempfile.TemporaryDirectory(prefix='t112-worker-startup-', dir='/private/tmp') as directory:
    root = Path(directory)
    for label in ('factory', 'ui-settings', 'override'):
        captured = {}
        def call(command, *fields):
            assert command == 'daemon_start'
            config = json.loads(Path(fields[1]).read_text())
            captured['config'] = (Path(config['codex_home']) / 'config.toml').read_text()
            raise Captured()
        namespace = dict(Path=Path, json=json, root=root, env={}, server=SimpleNamespace(server_port=12345),
                         args=SimpleNamespace(codex=Path('/fixture/codex')), report={'source_head': 'fixture'}, call=call)
        exec(code, namespace)
        try:
            namespace['setup']()(root / 'tree', label)
        except Captured:
            pass
        expected = '[projects.' + json.dumps(str(root / label / 'repo')) + ']\ntrust_level = "trusted"'
        report['cases'].append(dict(label=label, expected_trust=expected, isolated_config=captured['config'],
                                    exact_repo_trusted=expected in captured['config']))
report['status'] = 'PASS' if all(case['exact_repo_trusted'] for case in report['cases']) else 'INCOMPLETE'
args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(report['status'])
raise SystemExit(0 if report['status'] == 'PASS' else 1)
