"""恢复检查：只核对源码、语法和参数；不运行产品、构建或 ps。"""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

root = Path.cwd()
source = root / 'workbench/tests/test_t262_records_e2e.py'
old = Path('/private/tmp/t262-a1-checkpoint-20261108/workbench/tests/test_t262_records_e2e.py')
current_tree = ast.parse(source.read_text(encoding='utf-8'))
old_tree = ast.parse(old.read_text(encoding='utf-8'))
checks = []
for tree in [current_tree, old_tree]:
    tree.body[0] = ast.Pass()
    fixture = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Fixture')
    fixture.body = [n for n in fixture.body if not (isinstance(n, ast.FunctionDef) and n.name == 'choose')]
assert ast.dump(current_tree) == ast.dump(old_tree), '除 docstring / choose 外测试行为发生变化'
checks.append('除 docstring 与 choose 外，完整测试 AST 与旧检查点一致：业务期望、Enter、入口及清理未改')
for name in ['RecordsPage.tsx', 'records.css']:
    assert (root / 'workbench/app' / name).read_bytes() == (old.parents[1] / 'app' / name).read_bytes()
checks.append('两个产品文件与旧检查点逐字节一致')
tree = ast.parse(source.read_text(encoding='utf-8'))
mutants = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'MUTANTS' for t in n.targets))
page = (root / 'workbench/app/RecordsPage.tsx').read_text(encoding='utf-8')
assert len(mutants) == 4 and all(page.count(before) == 1 for before, after in mutants.values())
checks.append('四个既有变异均唯一匹配候选，未执行变异')
fixture = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Fixture')
choose = next(n for n in fixture.body if isinstance(n, ast.FunctionDef) and n.name == 'choose')
call = next(n.value for n in choose.body if isinstance(n, ast.Assign) and
            any(isinstance(t, ast.Name) and t.id == 'interaction' for t in n.targets))
expression = eval(compile(ast.Expression(call.args[0]), str(source), 'eval'),
                  {'J': lambda x: json.dumps(x, ensure_ascii=False), 'index': 0, 'value': 'alpha+T-1'})
checked = subprocess.run(['node', '--check', '--input-type=module'], input=expression,
                         text=True, capture_output=True, cwd=root)
assert checked.returncode == 0, checked.stderr
checks.append('标准表单驱动 JavaScript 语法通过（没有执行 DOM 交互）')
help_run = subprocess.run(['/usr/bin/python3', str(source), '--help'], text=True, capture_output=True, cwd=root)
assert help_run.returncode == 0, help_run.stderr
checks.append('--help 正常退出；默认完整场景与 revision / summary / smoke / mutant 参数保留')
diff = subprocess.run(['git', 'diff', '--check'], text=True, capture_output=True, cwd=root)
assert diff.returncode == 0, diff.stdout + diff.stderr
checks.append('git diff --check 通过')
print(json.dumps(dict(status='PASS', scope='静态恢复与驱动语法检查，不是产品验收',
    time=datetime.now(timezone.utc).isoformat(), checks=checks,
    help_stdout=help_run.stdout, node_check_stderr=checked.stderr, diff_check_output=diff.stdout+diff.stderr,
    applications_started=False, ps_executed=False, builds_run=0), ensure_ascii=False, indent=2))
