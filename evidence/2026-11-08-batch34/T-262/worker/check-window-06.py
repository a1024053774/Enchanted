"""仅检查窗口驱动语法和本轮变更边界，不启动 Electron、后台或构建。"""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

root = Path.cwd()
evidence = root / 'evidence/2026-11-08-batch34/T-262/worker'
path = root / 'workbench/tests/test_t262_records_e2e.py'
before = ast.parse((evidence / 'test-before-window-06.py').read_text(encoding='utf-8'))
after = ast.parse(path.read_text(encoding='utf-8'))
checks = []
def named(tree, kind, name):
    return next(node for node in tree.body if isinstance(node, kind) and node.name == name)
def constants(tree):
    return {node.targets[0].id: node.value for node in tree.body if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)}
old_constants, new_constants = constants(before), constants(after)
for name, value in old_constants.items():
    assert ast.dump(value) == ast.dump(new_constants[name]), name
assert set(new_constants) - set(old_constants) == {'LAUNCHER'}
checks.append('原有所有常量（原始夹具、四个变异、CDP 页面驱动等）保持不变')
old_main, new_main = named(before, ast.FunctionDef, 'main'), named(after, ast.FunctionDef, 'main')
old_calls = [ast.dump(n) for n in ast.walk(old_main) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id in ['check', 'check_rows']]
new_calls = [ast.dump(n) for n in ast.walk(new_main) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id in ['check', 'check_rows']]
assert old_calls == new_calls
old_full = named(old_main, ast.FunctionDef, 'full_scenario')
new_full = named(new_main, ast.FunctionDef, 'full_scenario')
old_full.body = [n for n in old_full.body if not (
    isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'window' for t in n.targets)) and not (
    isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
    and n.value.func.attr == 'cdp' and n.value.args and isinstance(n.value.args[0], ast.Constant)
    and n.value.args[0].value == 'Browser.setWindowBounds')]
new_full.body = [n for n in new_full.body if not (
    isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
    and n.value.func.attr == 'read_window_bounds')]
assert ast.dump(old_main) == ast.dump(new_main)
checks.append('main 的唯一区别是两条 Browser CDP 调用换成尺寸读回；所有业务断言及后续流程不变')
old_fixture, new_fixture = named(before, ast.ClassDef, 'Fixture'), named(after, ast.ClassDef, 'Fixture')
for method in old_fixture.body:
    if isinstance(method, ast.FunctionDef) and method.name not in ['prepare', 'start', 'diagnostics']:
        assert ast.dump(method) == ast.dump(named(new_fixture, ast.FunctionDef, method.name)), method.name
checks.append('select/Enter 驱动、记录读写、等待和清理方法不变；准备/启动与诊断新增真实窗口尺寸采集')
for name, kind in [('LAUNCHER', 'commonjs'), ('DRIVER', 'module')]:
    checked = subprocess.run(['node', '--check', '--input-type=' + kind], input=ast.literal_eval(new_constants[name]),
                             text=True, capture_output=True, cwd=root)
    assert checked.returncode == 0, checked.stderr
checks.append('自有 CJS 启动器与原 CDP 驱动通过 node --check，未执行')
help_run = subprocess.run(['/usr/bin/python3', str(path), '--help'], text=True, capture_output=True, cwd=root)
assert help_run.returncode == 0, help_run.stderr
checks.append('Python AST 与 --help 通过，未进入场景')
diff = subprocess.run(['git', 'diff', '--check'], text=True, capture_output=True, cwd=root)
assert diff.returncode == 0, diff.stdout + diff.stderr
checks.append('git diff --check 通过')
print(json.dumps(dict(status='PASS', scope='仅静态驱动检查，不是窗口运行或完整业务验收',
    time=datetime.now(timezone.utc).isoformat(), checks=checks, help_stdout=help_run.stdout,
    applications_started=False, builds_run=0, ps_executed=False), ensure_ascii=False, indent=2))
