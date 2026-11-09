#!/bin/bash
# T-249：由主控在沙箱外运行（沙箱里起不了 Electron）。
#   1. 无界面验收：python3 acceptance/T-249/check_git_graph.py
#   2. 真实 Electron 绿态及五个变异（断开面板／详情／diff、父提交颠倒、排序颠倒），必须命中指定断言
#   3. 打出 Enchanted Test（--variant test，独立 bundle id 与数据目录），只保留这个包给 Codex 验收
#   4. 清理：测试构建目录、夹具、临时复制的 node_modules；前后各记一次正在运行的 Enchanted 进程，核对未受影响
# 不替换、不启动 /Applications/Enchanted.app，不连接它的后台与 hc core。
# 用法：bash workbench/app/RUN-OUTSIDE-T249.sh [包的 slot 名，默认 t249-时间戳]
set -euo pipefail
cd "$(dirname "$0")/../.."
export PATH="/opt/homebrew/bin:$PATH"
python3 - "$@" <<'PY'
import datetime, json, os, pathlib, re, shutil, subprocess, sys, tempfile

root = pathlib.Path.cwd()
stamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
slot = sys.argv[1] if len(sys.argv) > 1 else 't249-' + stamp
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', slot), 'Invalid slot'
evidence = root / f'evidence/2026-11-07-batch33/T-249/attempt-fence4/outside-{stamp}'
evidence.mkdir(parents=True)
shots = pathlib.Path(f'/private/tmp/t249-shots-{stamp}')
log = []

def note(line):
    print(line, flush=True)
    log.append(line)

def enchanted():
    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,lstart=,command='], text=True).splitlines()
    return sorted(' '.join(r.split()) for r in rows if '/Applications/Enchanted.app/' in r)

before = enchanted()
note('正在运行的 Enchanted（前）：' + json.dumps(before, ensure_ascii=False))

workbench = root / 'workbench'
copied = False
owned_tmp = pathlib.Path(tempfile.mkdtemp(prefix='t249-outside-', dir='/private/tmp'))
package_ok, cleanup_safe = False, True

env = dict(os.environ)
for key in ['npm_config_cache', 'electron_config_cache', 'ELECTRON_OVERRIDE_DIST_PATH', 'ELECTRON_RUN_AS_NODE']:
    env.pop(key, None)
env.update(TMPDIR=str(owned_tmp), TMP=str(owned_tmp), TEMP=str(owned_tmp),
           npm_config_cache=str(owned_tmp / 'npm-cache'), electron_config_cache=str(owned_tmp / 'electron-cache'))
hc_cache = pathlib.Path('/Users/luckye/Documents/Code/hc-cache')
if 'ENCHANTED_HC_CACHE_DIR' not in env and not (root.parent / 'hc-cache').is_dir() and hc_cache.is_dir():
    env['ENCHANTED_HC_CACHE_DIR'] = str(hc_cache)

results = {}
def run(name, argv, expect_zero, cwd=root, extra=None):
    global cleanup_safe
    p = subprocess.run(argv, cwd=cwd, env=dict(env, **(extra or {})), text=True, capture_output=True)
    (evidence / f'{name}.log').write_text('$ ' + ' '.join(argv) + '\n' + p.stdout + p.stderr, encoding='utf-8')
    ok = (p.returncode == 0) == expect_zero
    if name.startswith('e2e-'):
        report_path = pathlib.Path(argv[argv.index('--output') + 1]) / 'run.json'
        report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
        cleaned = report.get('cleanup') == 'PASS' and report.get('fixture_removed') is True
        cleanup_safe = cleanup_safe and cleaned
        expected_failure = {'e2e-red-no-panel': '侧边面板存在',
                            'e2e-red-no-details': '点击提交后详情可见',
                            'e2e-red-no-diff': '点击文件后单文件 diff 可见',
                            'e2e-red-parents': '每行父提交与 git rev-list --parents 一致',
                            'e2e-red-order': '提交顺序与 git rev-list --date-order --all 一致'}.get(name)
        verdict = report.get('status') == 'PASS' if expect_zero else (
            report.get('status') == 'FAIL' and any(c.get('what') == expected_failure and c.get('ok') is False for c in report.get('checks', [])))
        ok = ok and verdict and cleaned and report.get('user_core_unchanged') is True
    results[name] = dict(exit=p.returncode, expected='0' if expect_zero else '非 0', ok=ok)
    note(f'{name}: exit {p.returncode}（期望{"0" if expect_zero else "非 0"}）{"OK" if ok else "不符"}')
    return p

try:
    if not (workbench / 'node_modules').exists():
        main_modules = pathlib.Path(os.environ.get('A2A_MAIN_NODE_MODULES', '/Users/luckye/Documents/Code/a2a/workbench/node_modules'))
        assert main_modules.is_dir(), f'没有 node_modules：{main_modules}'
        # 真复制；从创建开始记录所有权，失败时也只清理这一份。
        copied = True
        subprocess.run(['/usr/bin/ditto', str(main_modules), str(workbench / 'node_modules')], check=True)
        note(f'临时复制 node_modules：{main_modules}')
    run('acceptance', ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py'], True)
    test = 'workbench/tests/test_t249_git_graph_e2e.py'
    run('e2e-green', ['/usr/bin/python3', test, '--output', str(evidence / 'e2e-green'), '--shots', str(shots / 'green')], True)
    for mutant in ('no-panel', 'no-details', 'no-diff', 'parents', 'order'):
        run(f'e2e-red-{mutant}', ['/usr/bin/python3', test, '--output', str(evidence / f'e2e-red-{mutant}'), '--mutant', mutant,
                                  '--shots', str(shots / f'red-{mutant}')], False)
    p = run('package', ['npm', 'run', 'package:mac', '--', '--variant', 'test', '--slot', slot], True, cwd=workbench)
    if p.returncode == 0:
        built = json.loads(p.stdout.strip().splitlines()[-1])
        app = owned_tmp / f'a2a-build-{slot}' / 'Enchanted Test.app'
        assert pathlib.Path(built['app']) == app and app.is_dir(), built['app']
        left = sorted(x.name for x in app.parent.iterdir())
        assert left == ['Enchanted Test.app'], f'构建目录仍有中间产物：{left}'
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)], check=True)
        bundle = subprocess.check_output(['/usr/libexec/PlistBuddy', '-c', 'Print :CFBundleIdentifier', str(app / 'Contents/Info.plist')], text=True).strip()
        assert bundle == 'org.a2a.workbench.test', bundle
        package_ok = True
        note(f'待验收的包：{app}（bundle id {bundle}，数据目录 ~/Library/Application Support/a2a-orchestrator-test）')
finally:
    # 只清理 mkdtemp 刚创建的本次目录；不扫描其他运行。先保存体量和状态。
    sizes = [p.stat().st_size for p in owned_tmp.rglob('*') if not p.is_symlink() and p.is_file()]
    (evidence / 'cleanup.json').write_text(json.dumps(dict(directory=str(owned_tmp), files=len(sizes),
        bytes=sum(sizes), cleanup_safe=cleanup_safe, package_ok=package_ok), indent=2) + '\n', encoding='utf-8')
    if cleanup_safe:
        for path in owned_tmp.iterdir():
            if package_ok and path.name == f'a2a-build-{slot}':
                continue
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
        if not package_ok:
            owned_tmp.rmdir()
        note(f'已清理本次临时目录（待验收的包除外）：{owned_tmp}')
    else:
        note(f'进程清理未证实完成，保留本次目录：{owned_tmp}')
    if copied and cleanup_safe:
        shutil.rmtree(workbench / 'node_modules')
        note('删除临时复制的 node_modules')
    after = enchanted()
    note('正在运行的 Enchanted（后）：' + json.dumps(after, ensure_ascii=False))
    note('Enchanted 前后一致：' + ('是' if before == after else '否'))
    results['enchanted_unchanged'] = before == after
    note(f'截图（本机临时目录，不进仓库）：{shots}')
    (evidence / 'summary.json').write_text(json.dumps(dict(results=results, log=log), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
ok = all(v['ok'] for k, v in results.items() if isinstance(v, dict)) and results.get('enchanted_unchanged')
print('PASS' if ok else 'FAIL', evidence)
sys.exit(0 if ok else 1)
PY
