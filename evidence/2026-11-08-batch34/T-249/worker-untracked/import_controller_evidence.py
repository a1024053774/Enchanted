"""只读核对主控窗口结果，并按原始字节归入本票；不运行产品、不覆盖不同的旧证据。"""
from pathlib import Path
import datetime
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[4]
E = Path(__file__).resolve().parent
S = Path('/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-249/controller/untracked-window-01')
D = E / 'controller-window-01'
summary = json.loads((S / 'summary.json').read_text(encoding='utf-8'))
cleanup = json.loads((S / 'cleanup.json').read_text(encoding='utf-8'))
expected = {
    'old-C': '未提交 未跟踪文本 diff 与原始文件及独立 Git 一致：untracked.txt',
    'candidate': None,
    'no-untracked': '未提交 未跟踪文本 diff 与原始文件及独立 Git 一致：untracked.txt',
    'no-resize': '真实鼠标拖动改变可见日期列宽',
    'no-reset': '真实鼠标双击恢复可见日期列宽',
    'deferred-candidate': None,
    'stale-diff': '关闭 diff 后迟到内容不能重开',
    'no-panel': '侧边面板存在',
    'no-details': '点击提交后详情可见',
    'no-diff': '点击文件后单文件 diff 可见',
    'parents': '每行父提交与 git rev-list --parents 一致',
    'order': '提交顺序与 git rev-list --date-order --all 一致',
}
assert summary['root'] == str(ROOT) and {r['name'] for r in summary['results']} == set(expected)
assert len(summary['results']) == 12 and summary['cleanup_safe']
assert cleanup['safe'] and cleanup['removed'] and cleanup['copied_modules_removed']
rows = []
for result in summary['results']:
    name = result['name']
    run = json.loads((S / name / 'run.json').read_text(encoding='utf-8'))
    target = expected[name]
    failed = [c['what'] for c in run['checks'] if not c['ok']]
    assert result['ok'] and result['expected_failure'] == target
    assert run['cleanup'] == 'PASS' and run['fixture_removed'] and run['user_core_unchanged']
    if target is None:
        assert run['status'] == 'PASS' and result['exit'] == 0 and not failed
    else:
        assert run['status'] == 'FAIL' and result['exit'] == 1 and failed == [target]
    # macOS records the actual Xcode interpreter in sys.executable; all source/option argv must match.
    assert run['command'][1:] == result['command'][1:]
    assert run['command'][1] == str(ROOT / 'workbench/tests/test_t249_git_graph_e2e.py')
    rows.append(dict(name=name, status=run['status'], exit=result['exit'], check_count=len(run['checks']),
                     failed_assertions=failed, expected_result_met=True, versions=run['versions']))
local = json.loads((E / 'local-01/summary.json').read_text(encoding='utf-8'))
assert len(local['results']) == 8 and all(r['ok'] for r in local['results'])
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == '5ca17101d350e54582cb301d4f8c9166d63338b5'
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', head, '--', 'workbench', 'acceptance/T-249'], cwd=ROOT, text=True).splitlines()
checked = []
for name in paths:
    path = ROOT / name
    if not path.exists() and not path.is_symlink():
        continue  # Sparse-checkout files absent from this task remain absent.
    raw = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
    assert raw == subprocess.check_output(['git', 'show', head + ':' + name], cwd=ROOT), name
    checked.append(name)
stable = subprocess.check_output(['git', 'diff', '--name-only', 'a6718ffa5f4ffccb75bb9bcd801c0cb57c280994', head,
                                 '--', 'workbench', 'acceptance/T-249'], cwd=ROOT, text=True).splitlines()
assert stable == []
copied = []
inputs = [(p, D / p.relative_to(S)) for p in sorted(S.rglob('*')) if p.is_file()]
inputs.append((S.parent / 'untracked-window-01.stdout.log', D / 'wrapper.stdout.txt'))
for src, dest in inputs:
    assert src.suffix in ('.json', '.txt', '.log')
    raw = src.read_bytes()
    raw.decode('utf-8')
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert dest.read_bytes() == raw, '既有证据不同，拒绝覆盖：' + str(dest)
    else:
        dest.write_bytes(raw)
    assert dest.read_bytes() == src.read_bytes()
    copied.append(dict(source=str(src), destination=str(dest.relative_to(ROOT)), bytes=len(raw), equal_raw_bytes=True))
binding = dict(
    source_directory=str(S), executed_by='主控（沙箱外）；worker 只读核对及归入',
    controller_message='主控 #116：12/12 达到预期；wrapper exit 0；绑定当前已测源码',
    current_source_commit=head, same_workbench_and_frozen_acceptance_as='a6718ffa5f4ffccb75bb9bcd801c0cb57c280994',
    product_and_test_diff_since_checkpoint=stable, present_tracked_inputs_checked=checked,
    binding_boundary='运行报告记录本 worktree 真实入口，未内嵌 Git commit 字段。源码归属依据主控 #116、受管会话源码变更记录，以及当前工作区与提交逐字节核对；没有改动产品/测试后复用结果。',
    wrapper_boundary='实跑 summary 未包含后来添加的 preflight 字段；新增预检的独立证据在 driver-preflight-01.json，不冒称本次窗口组经过它。',
    copied=copied, copied_file_count=len(copied), copied_bytes=sum(c['bytes'] for c in copied), results=rows,
    local_results=local['results'], time=datetime.datetime.now(datetime.timezone.utc).isoformat())
(E / 'controller-evidence-import.json').write_text(json.dumps(binding, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(imported_files=len(copied), bytes=binding['copied_bytes'], source_commit=head,
                     checked_inputs=len(checked), window_expected=12, local_expected=8), ensure_ascii=False))
