"""仅验证获准修改的 ask() 夹具经真实后台得到 running；不替代完整 T-137 Electron 回归。
直接执行测试文件里的函数，避免另写一份夹具。预期 running 来自主控 #5 和原有断言。
"""
import ast
import json
from pathlib import Path
import shutil
import socket
import sys
import uuid

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'workbench/tests'))
from scripted_claude import Fixture

output = Path(sys.argv[1])
assert not output.exists(), '保留既有证据'
report = dict(status='INCOMPLETE', observed={})
fixture = None
try:
    fixture = Fixture('t146-t137-helper-', lambda body: ('unused', [], 'ok'))
    report['fixture'] = str(fixture.dir)
    fixture.start(shutil.which('claude') or str(Path.home() / '.local/bin/claude'), {'README.md': 'fixture\n'})
    assert fixture.request('role_release', fixture.terminal)['ok']
    path = root / 'workbench/tests/test_t137_reflect_e2e.py'
    main = next(n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    helper = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'ask')
    namespace = dict(fixture=fixture, report=report, uuid=uuid, socket=socket, json=json)
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(path), 'exec'), namespace)
    role = namespace['ask'](fixture.terminal, 'executor')
    report['sidebar'] = fixture.request('sidebar_snapshot')
    report['reflect'] = fixture.request('reflect_tree', project='demo')
    agent = next(a for a in report['sidebar']['agents'] if a['id'] == fixture.terminal_launch)
    node = next(n for n in report['reflect']['nodes'] if n['id'] == role)
    assert agent['state'] == node['state'] == 'running', (agent, node)
    report['status'] = 'PASS'
except BaseException as error:
    report['error'] = f'{type(error).__name__}: {error}'
    raise
finally:
    try:
        if fixture:
            fixture.stop()
    finally:
        with output.open('x', encoding='utf-8') as f:
            f.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
