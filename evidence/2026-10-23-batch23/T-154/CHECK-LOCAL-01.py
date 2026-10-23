"""T-154 注释、解析与离线导入检查；不运行历史原生验收。"""
import argparse
import ast
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = 'b058e3a7585ccc85df190e90c01b52756c9d076e'
FILES = ('test_t112_execution.mjs', 'test_quality_tracer_e2e.py',
         'run_pane_lifecycle.py', 'test_t122_claude_worker_e2e.py',
         'run_t112_native.py', 'test_t108_questions.mjs')
IMPORTS = ('test_quality_tracer_e2e', 'run_pane_lifecycle',
           'test_t122_claude_worker_e2e', 'run_t112_native',
           'test_t112_closed_fixture', 'test_bad_worker_e2e',
           'test_protected_acceptance_e2e', 'test_quality_legacy_e2e',
           'test_quality_widen_e2e', 'test_review_worktree_lifecycle_e2e',
           'test_s3_quality_joint_e2e', 'test_t082_parent_launch_e2e',
           'test_t082_review_boundary_e2e', 'test_t090_review_worker_boundary_e2e',
           'run_t076_quality_green')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    args = parser.parse_args()
    assert not args.summary.exists(), '请选择新证据路径'
    report = dict(status='INCOMPLETE', base_revision=BASE, python=sys.version,
                  scope='仅注释、解析、离线导入与链接；不证明产品行为', checks=[])
    try:
        tests = ROOT / 'workbench/tests'
        for name in FILES:
            path = tests / name
            before = subprocess.check_output(['git', 'show', BASE + ':workbench/tests/' + name], cwd=ROOT)
            after = path.read_bytes()
            header, body = after.split(b'\n', 1)
            assert body == before, name + ' 改了文件头以外的字节'
            text = header.decode('utf-8')
            assert '历史测试：只针对 ' in text and '当前 main 不跑；当前无人守护：' in text, name
            assert not after.startswith(b'\xef\xbb\xbf') and b'\r\n' not in after, name
            if name.endswith('.py'):
                assert ast.dump(ast.parse(after)) == ast.dump(ast.parse(before)), name
            else:
                subprocess.run(['node', '--check', str(path)], check=True, capture_output=True, text=True)
            report['checks'].append(name + ': 仅新增一行注释；解析通过')
        # 反事实是原始文件没有所要求的历史标记；不把它叫作产品红态。
        report['parent_missing_markers'] = [name for name in FILES if '历史测试：只针对 '.encode() not in
            subprocess.check_output(['git', 'show', BASE + ':workbench/tests/' + name], cwd=ROOT)]
        assert report['parent_missing_markers'] == list(FILES)
        sys.path.insert(0, str(tests))
        for name in IMPORTS:
            importlib.import_module(name)
        report['imports'] = list(IMPORTS)
        for name in ('test_t112_counterfactuals.py', 'run_t082_boundary.py'):
            ast.parse((tests / name).read_bytes())
        index = tests / 'HISTORICAL.md'
        tracked = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], cwd=ROOT, text=True).splitlines())
        links = re.findall(r'\]\(([^)]+)\)', index.read_text(encoding='utf-8'))
        for link in links:
            target = (index.parent / link).resolve().relative_to(ROOT).as_posix()
            assert target in tracked, target
        report['links_checked'] = len(links)
        report['node'] = subprocess.check_output(['node', '--version'], text=True).strip()
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = repr(error)
    with args.summary.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
