"""隔离检查打包脚本的两个失败方式：环境失败冒充变异红态；通配清理误删旧运行。

只执行脚本自己的 run / finally 段，子进程替换为启动失败，清理限制在测试自己创建的哨兵目录。
这不替代 Electron 端到端或真实打包验证。
"""
import ast
import glob
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'app/RUN-OUTSIDE-T249.sh'
CODE = SCRIPT.read_text(encoding='utf-8').split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
TREE = ast.parse(CODE)
E2E = SCRIPT.parents[1] / 'tests/test_t249_git_graph_e2e.py'
E2E_TREE = ast.parse(E2E.read_text(encoding='utf-8'))


class OutsideSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='t249-safety-')
        self.root = Path(self.temp.name)
        self.owned = self.root / 'owned'
        self.owned.mkdir()
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        self.ns = dict(root=self.root, evidence=self.evidence, env={}, results={}, log=[],
                       note=lambda line: None, json=json, pathlib=__import__('pathlib'),
                       os=os, shutil=shutil, slot='candidate', copied=False, workbench=self.root,
                       before=[], enchanted=lambda: [], shots=self.root / 'shots',
                       owned_tmp=self.owned, package_ok=False, cleanup_safe=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_environment_failure_is_not_mutant_red(self):
        self.ns['subprocess'] = SimpleNamespace(run=lambda *a, **k: SimpleNamespace(returncode=1, stdout='', stderr='startup error'))
        run = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
        exec(compile(ast.Module(body=[run], type_ignores=[]), str(SCRIPT), 'exec'), self.ns)
        for mutant in ('parents', 'order', 'no-panel', 'no-details', 'no-diff'):
            with self.subTest(mutant=mutant):
                name = 'e2e-red-' + mutant
                output = self.evidence / name
                output.mkdir()
                (output / 'run.json').write_text(json.dumps(dict(status='INCOMPLETE', error='Electron failed to start',
                    checks=[], cleanup='PASS', fixture_removed=True, user_core_unchanged=True)), encoding='utf-8')
                self.ns['run'](name, ['python3', 'test.py', '--output', str(output)], False)
                self.assertFalse(self.ns['results'][name]['ok'])

    def test_disconnected_ui_requires_its_specific_business_assertion(self):
        self.ns['subprocess'] = SimpleNamespace(run=lambda *a, **k: SimpleNamespace(returncode=1, stdout='', stderr=''))
        run = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
        exec(compile(ast.Module(body=[run], type_ignores=[]), str(SCRIPT), 'exec'), self.ns)
        required = {'no-panel': '侧边面板存在', 'no-details': '点击提交后详情可见',
                    'no-diff': '点击文件后单文件 diff 可见'}
        for mutant, business_assertion in required.items():
            name = 'e2e-red-' + mutant
            output = self.evidence / name
            output.mkdir()
            for assertion, expected in [(business_assertion, True), ('别的断言失败', False)]:
                with self.subTest(mutant=mutant, assertion=assertion):
                    (output / 'run.json').write_text(json.dumps(dict(status='FAIL',
                        checks=[dict(what=assertion, ok=False)], cleanup='PASS', fixture_removed=True,
                        user_core_unchanged=True)), encoding='utf-8')
                    self.ns['run'](name, ['python3', 'test.py', '--output', str(output)], False)
                    self.assertEqual(self.ns['results'][name]['ok'], expected)

    def test_disconnected_ui_mutations_are_required(self):
        assignments = [n for n in E2E_TREE.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id in ('MODEL', 'MUTANTS') for t in n.targets)]
        ns = {}
        exec(compile(ast.Module(body=assignments, type_ignores=[]), str(E2E), 'exec'), ns)
        loop = next(n for n in ast.walk(TREE) if isinstance(n, ast.For)
                    and isinstance(n.target, ast.Name) and n.target.id == 'mutant')
        for mutant in ('no-panel', 'no-details', 'no-diff'):
            with self.subTest(mutant=mutant):
                self.assertIn(mutant, ns['MUTANTS'])
                path, before, after = ns['MUTANTS'][mutant]
                # 这里只核对必跑登记；真实 source_tree 保证变异定位唯一，窗口业务断言负责判红。
                # 不靠产品源码里仍有某个字符串来证明组件或点击接线可用。
                self.assertTrue(path and before)
                self.assertNotEqual(before, after)
                self.assertIn(mutant, ast.literal_eval(loop.iter))

    def test_detail_probe_distinguishes_absence_from_transport_failure(self):
        probe = next((n for n in E2E_TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'check_dom'), None)
        self.assertIsNotNone(probe, '详情与 diff 缺少能记录业务失败的 DOM 观察点')
        ns = dict(time=time)
        exec(compile(ast.Module(body=[probe], type_ignores=[]), str(E2E), 'exec'), ns)
        for what in ('点击提交后详情可见', '点击文件后单文件 diff 可见'):
            for scenario in ('present', 'absent', 'transport-failure'):
                with self.subTest(what=what, scenario=scenario):
                    checks = []

                    def check(ok, message):
                        checks.append((ok, message))
                        assert ok, message

                    def evaluate(expression):
                        if scenario == 'transport-failure':
                            raise AssertionError('CDP connection lost')
                        return {'visible': True} if scenario == 'present' else None

                    electron = SimpleNamespace(evaluate=evaluate)
                    if scenario == 'present':
                        self.assertEqual(ns['check_dom'](electron, check, 'DOM probe', what, seconds=.01), {'visible': True})
                        self.assertEqual(checks, [(True, what)])
                    else:
                        with self.assertRaisesRegex(AssertionError, 'CDP connection lost' if scenario == 'transport-failure' else what):
                            ns['check_dom'](electron, check, 'DOM probe', what, seconds=.01)
                        self.assertEqual(checks, [] if scenario == 'transport-failure' else [(False, what)])

    def test_panel_assertion_distinguishes_absence_from_transport_failure(self):
        probe = next((n for n in E2E_TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'check_panel_present'), None)
        self.assertIsNotNone(probe, '端到端测试缺少面板存在的独立断言')
        ns = dict(time=time)
        exec(compile(ast.Module(body=[probe], type_ignores=[]), str(E2E), 'exec'), ns)
        for scenario in ('present', 'absent', 'transport-failure'):
            with self.subTest(scenario=scenario):
                checks = []

                def check(ok, what):
                    checks.append((ok, what))
                    assert ok, what

                def evaluate(expression):
                    if scenario == 'transport-failure':
                        raise AssertionError('CDP connection lost')
                    return scenario == 'present'

                electron = SimpleNamespace(until=lambda *a: True, evaluate=evaluate)
                if scenario == 'present':
                    ns['check_panel_present'](electron, check, seconds=.01)
                    self.assertEqual(checks, [(True, '侧边面板存在')])
                else:
                    with self.assertRaisesRegex(AssertionError, 'CDP connection lost' if scenario == 'transport-failure' else '侧边面板存在'):
                        ns['check_panel_present'](electron, check, seconds=.01)
                    self.assertEqual(checks, [] if scenario == 'transport-failure' else [(False, '侧边面板存在')])

    def test_cleanup_preserves_prior_runs_and_symlink_target(self):
        sentinel = self.root / 't249-prior-run'
        sentinel.mkdir()
        (sentinel / 'evidence.txt').write_text('preserve', encoding='utf-8')
        (self.owned / 'external-link').symlink_to(sentinel, target_is_directory=True)
        self.ns['glob'] = SimpleNamespace(glob=lambda pattern: [str(sentinel)] if 't249-*' in pattern else [])
        cleanup = next(n for n in TREE.body if isinstance(n, ast.Try) and n.finalbody).finalbody
        exec(compile(ast.Module(body=cleanup, type_ignores=[]), str(SCRIPT), 'exec'), self.ns)
        self.assertEqual((sentinel / 'evidence.txt').read_text(encoding='utf-8'), 'preserve')


if __name__ == '__main__':
    unittest.main()
