"""导航修订的静态保真检查；不启动 Electron、后台、模型、ps 或构建。"""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

root = Path.cwd()
evidence = root / 'evidence/2026-11-08-batch34/T-262/worker'
source = root / 'workbench/tests/test_t262_records_e2e.py'
before = ast.parse((evidence / 'test-before-navigation-07.py').read_text(encoding='utf-8'))
after = ast.parse(source.read_text(encoding='utf-8'))
checks = []
def named(tree, kind, name):
    return next(n for n in tree.body if isinstance(n, kind) and n.name == name)
def constants(tree):
    return {n.targets[0].id:ast.dump(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and isinstance(n.targets[0], ast.Name)}
assert constants(before) == constants(after)
checks.append('原始场景、四个 mutant、真实窗口和表单驱动常量均未改')
old_main = named(before, ast.FunctionDef, 'main')
new_main = named(after, ast.FunctionDef, 'main')
class NavigationOnly(ast.NodeTransformer):
    def visit_Expr(self, node):
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == 'fixture':
            if call.func.attr == 'open_records':
                return None
            if call.func.attr == 'click' and ast.literal_eval(call.args[0]) in [
                '[data-project-id="alpha"]', '[data-project-id="beta"]', '[data-project-id="empty"]',
                '.free-terminals', '[data-records-tab]']:
                return None
        return node
assert ast.dump(NavigationOnly().visit(old_main)) == ast.dump(NavigationOnly().visit(new_main))
checks.append('main 除导航动作替换外完全一致；业务断言、超时、延迟响应的释放顺序及后续流程保留')
old_fixture = named(before, ast.ClassDef, 'Fixture')
new_fixture = named(after, ast.ClassDef, 'Fixture')
for method in old_fixture.body:
    if isinstance(method, ast.FunctionDef) and method.name != 'diagnostics':
        assert ast.dump(method) == ast.dump(named(new_fixture, ast.FunctionDef, method.name)), method.name
checks.append('已有 Fixture 方法除 diagnostics 外不变；新增 open_records 和只读页面快照')
method = named(new_fixture, ast.FunctionDef, 'open_records')
variables = {'J':lambda v:json.dumps(v,ensure_ascii=False), 'selector':'[data-project-id="beta"]', 'heading':'beta'}
identity = next(n.value for n in method.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'identity' for t in n.targets))
variables['identity'] = eval(compile(ast.Expression(identity), str(source), 'eval'), variables)
expressions = [variables['identity']]
for n in ast.walk(method):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'until':
        expressions.append(eval(compile(ast.Expression(n.args[0]), str(source), 'eval'), variables))
page = named(new_fixture, ast.FunctionDef, 'page_snapshot')
expressions.append(ast.literal_eval(next(n.value.args[0] for n in page.body if isinstance(n, ast.Return))))
for expression in expressions:
    r = subprocess.run(['node','--check','--input-type=module'],input=expression,text=True,capture_output=True,cwd=root)
    assert r.returncode == 0, r.stderr
checks.append('导航就绪条件和只读页面诊断 JavaScript 语法通过，未执行 DOM 操作')
r = subprocess.run(['/usr/bin/python3',str(source),'--help'],text=True,capture_output=True,cwd=root)
assert r.returncode == 0, r.stderr
checks.append('Python AST / --help 通过；未进入测试场景')
r = subprocess.run(['git','diff','--check'],text=True,capture_output=True,cwd=root)
assert r.returncode == 0, r.stdout+r.stderr
checks.append('git diff --check 通过')
print(json.dumps(dict(status='PASS',scope='静态保真与语法检查，不是修订后真实页面验证',
    time=datetime.now(timezone.utc).isoformat(),checks=checks,applications_started=False,builds_run=0,ps_executed=False),ensure_ascii=False,indent=2))
