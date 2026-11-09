"""T-249：由主控在 worker 沙箱外执行；新建隔离夹具，不打包、不操作正式应用。

python3 /绝对/worktree/evidence/2026-11-08-batch34/T-249/worker-untracked/run_windows.py --output /绝对/持久结果目录
一次运行旧 C、完整候选、限定变异和旧窗口回归。启动失败不是业务红态。
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--preflight', action='store_true', help='只读核对路径与依赖归属，不创建目录或启动进程')
args = parser.parse_args()
output = args.output.resolve()
assert (ROOT / '.git').is_file() and (ROOT / 'workbench/app/gitHost.ts').is_file(), 'ROOT 不是本任务 worktree：' + str(ROOT)
assert not output.exists() and not output.is_symlink(), '输出目录必须全新：' + str(output)
modules = ROOT / 'workbench/node_modules'
assert not modules.is_symlink(), '依赖目录是链接，不由本脚本接管：' + str(modules)
assert not modules.exists() or modules.is_dir(), '依赖目录不是目录：' + str(modules)
preflight = dict(root=str(ROOT), modules=str(modules), modules_exist=modules.exists(),
    modules_ownership='已有目录；本脚本不删除' if modules.exists() else '本次创建副本；确认清理安全后删除',
    output=str(output), output_is_new=True)
if args.preflight:
    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    sys.exit(0)
output.mkdir(parents=True, exist_ok=False)
owned = Path(tempfile.mkdtemp(prefix='t249-untracked-outside-'))
copied = False
safe = True
results = []
env = dict(os.environ, TMPDIR=str(owned), TMP=str(owned), TEMP=str(owned), PYTHONDONTWRITEBYTECODE='1')
env['PATH'] = '/opt/homebrew/Cellar/node/26.5.0/bin:/opt/homebrew/bin:' + env.get('PATH', '')
for key in ('ELECTRON_RUN_AS_NODE', 'ELECTRON_OVERRIDE_DIST_PATH'):
    env.pop(key, None)
env.setdefault('ENCHANTED_HC_CACHE_DIR', '/Users/luckye/Documents/Code/hc-cache')


def save():
    (output / 'summary.json').write_text(json.dumps(dict(root=str(ROOT), command=[sys.executable, *sys.argv],
        preflight=preflight, results=results, cleanup_safe=safe), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


cases = [
    ('old-C', ['--baseline-c'], '未提交 未跟踪文本 diff 与原始文件及独立 Git 一致：untracked.txt'),
    ('candidate', [], None),
    ('no-untracked', ['--mutant', 'no-untracked'], '未提交 未跟踪文本 diff 与原始文件及独立 Git 一致：untracked.txt'),
    ('no-resize', ['--mutant', 'no-resize'], '真实鼠标拖动改变可见日期列宽'),
    ('no-reset', ['--mutant', 'no-reset'], '真实鼠标双击恢复可见日期列宽'),
    ('deferred-candidate', ['--deferred-diff'], None),
    ('stale-diff', ['--deferred-diff', '--mutant', 'stale-diff'], '关闭 diff 后迟到内容不能重开'),
    ('no-panel', ['--mutant', 'no-panel'], '侧边面板存在'),
    ('no-details', ['--mutant', 'no-details'], '点击提交后详情可见'),
    ('no-diff', ['--mutant', 'no-diff'], '点击文件后单文件 diff 可见'),
    ('parents', ['--mutant', 'parents'], '每行父提交与 git rev-list --parents 一致'),
    ('order', ['--mutant', 'order'], '提交顺序与 git rev-list --date-order --all 一致'),
]
try:
    if not modules.exists():
        source = Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules')
        assert source.is_dir(), str(source)
        copied = True
        subprocess.run(['/usr/bin/ditto', str(source), str(modules)], check=True)
    for name, options, expected in cases:
        command = ['/usr/bin/python3', str(ROOT / 'workbench/tests/test_t249_git_graph_e2e.py'),
                   '--output', str(output / name), '--shots', str(owned / 'shots' / name), *options]
        print(name, flush=True)
        run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, start_new_session=True)
        (output / (name + '.txt')).write_text('$ ' + repr(command) + '\n' + run.stdout + run.stderr, encoding='utf-8')
        report_path = output / name / 'run.json'
        report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
        clean = report.get('cleanup') == 'PASS' and report.get('fixture_removed') is True
        safe = safe and clean
        business = (run.returncode == 0 and report.get('status') == 'PASS') if expected is None else (
            run.returncode != 0 and report.get('status') == 'FAIL'
            and any(c.get('ok') is False and c.get('what') == expected for c in report.get('checks', [])))
        results.append(dict(name=name, command=command, exit=run.returncode, expected_failure=expected,
            status=report.get('status', 'INCOMPLETE'), failed_checks=[c for c in report.get('checks', []) if not c['ok']],
            ok=business and clean and report.get('user_core_unchanged') is True))
        save()
        if not results[-1]['ok']:
            # Preserve the first anomalous run; don't repeat builds or run dependent mutants.
            break
finally:
    sizes = [p.stat().st_size for p in owned.rglob('*') if not p.is_symlink() and p.is_file()]
    cleanup = dict(directory=str(owned), time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   files=len(sizes), bytes=sum(sizes), safe=safe, modules_copied=copied)
    (output / 'cleanup.json').write_text(json.dumps(cleanup, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if safe:
        shutil.rmtree(owned)
        if copied:
            shutil.rmtree(modules)
    cleanup.update(removed=not owned.exists(), copied_modules_removed=copied and not modules.exists())
    (output / 'cleanup.json').write_text(json.dumps(cleanup, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save()
passed = len(results) == len(cases) and all(r['ok'] for r in results)
print('PASS' if passed else 'INCOMPLETE', output)
sys.exit(0 if passed else 1)
