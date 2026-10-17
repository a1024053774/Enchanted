"""Compare ASTs outside the explicitly approved read-only changes."""
import ast
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE.parents[2]
OLD = BASE / '09b-a15-e4-screen-diagnosis-01'


def normalize(tree, kind):
    tree.body = [node for node in tree.body if not
                 (isinstance(node, ast.ImportFrom) and node.module == 'p1_output') and not
                 (isinstance(node, ast.Import) and any(item.name == 'base64' for item in node.names) and kind != 'run_t078_p1.py')]
    if kind == 'run_t078_p1.py':
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'snapshot': node.body = [ast.Pass()]
    elif kind == 't078_09b_phase_driver.py':
        function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'execute')
        for node in ast.walk(function):
            if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'permission': node.body = [ast.Pass()]
    else:
        function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'main')
        keep = []
        for node in function.body:
            if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id in ['observed', 'verified_capture'] for x in node.targets): continue
            if isinstance(node, ast.If) and any(isinstance(x, ast.Constant) and x.value == 'permission_screen_changed' for x in ast.walk(node)): continue
            if isinstance(node, ast.If) and isinstance(node.test, ast.Attribute) and node.test.attr == 'check_only': continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and node.value.args and isinstance(node.value.args[0], ast.Constant) and node.value.args[0].value == '--check-only': continue
            keep.append(node)
        function.body = keep
        for node in ast.walk(function):
            if isinstance(node, ast.Dict):
                pairs = [(key, value) for key, value in zip(node.keys, node.values)
                         if not isinstance(key, ast.Constant) or key.value != 'permission_screen_verified_capture']
                node.keys, node.values = [x[0] for x in pairs], [x[1] for x in pairs]
    return ast.dump(tree, include_attributes=False)


def main():
    rows = []
    for name in ['run_t078_p1.py', 't078_09b_phase_driver.py', 't078_09b_i1_permission.py']:
        before = ast.parse((OLD / name).read_text(encoding='utf-8'))
        after = ast.parse((SOURCE / 'workbench/tests' / name).read_text(encoding='utf-8'))
        equal = normalize(before, name) == normalize(after, name)
        rows.append({'file': name, 'outside_approved_reader_changes_equal': equal})
    report = {'status': 'PASS' if all(x['outside_approved_reader_changes_equal'] for x in rows) else 'INCOMPLETE',
              'checks': rows, 'scope': 'AST comparison of old callers; not an independent behavioral review'}
    out = BASE / '09b-a15-reader-fix-01/readonly-scope-check.json'
    with out.open('x', encoding='utf-8') as stream: stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report)); return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
