#!/bin/sh
# T-113 第一轮独立复验。仓库根目录执行：
# sh evidence/2026-10-20-batch18/T-113/REVIEW-OUTSIDE-01.sh
# --static-only 只运行无浏览器的补充探针；不能代替真实浏览器验收。
# 全量模式使用本机 Google Chrome、临时 profile，无截图、不调用模型。
set -eu
export LC_ALL=C
cd "$(dirname "$0")/../../.."
python3 - "$@" <<'PY'
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

root = Path.cwd()
evidence = root / 'evidence/2026-10-20-batch18/T-113'
expected = '28b2ab19bcd2fe500125fdb9be1540e07f8ad0fc'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
if head != expected:
    raise SystemExit('INCOMPLETE: 候选已经变化，请重新冻结后审查')
if subprocess.check_output(['git', 'diff', '--name-only', expected, '--', 'docs', str(evidence)], text=True).strip():
    raise SystemExit('INCOMPLETE: 被审查文件存在受控改动')
print('候选 ' + head, flush=True)
failed = False

def run(args, timeout=240):
    global failed
    try:
        result = subprocess.run(args, cwd=str(root), text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout)
        print(result.stdout, end='', flush=True)
        return result.returncode, result.stdout
    except subprocess.TimeoutExpired:
        print('INCOMPLETE: 命令超时 ' + args[0], flush=True)
        failed = True
        return 2, ''

with tempfile.TemporaryDirectory(prefix='t113-review01-', dir='/private/tmp') as tmp:
    work = Path(tmp)
    # 补充探针只检查确定性的演示数据分支；它不是浏览器证据。
    probe = work / 'static-probe.mjs'
    probe.write_text(r'''
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync(process.argv[2], 'utf8');
let failures = 0;
function fixture() {
  const handlers = {}, timers = [];
  const root = { innerHTML: '', dataset: {}, contains: () => true,
    querySelectorAll: () => [], querySelector: () => null,
    addEventListener: (name, fn) => { handlers[name] = fn; } };
  vm.runInNewContext(source, { document: { activeElement: null, getElementById: () => root,
    querySelectorAll: () => [] }, setTimeout: fn => { timers.push(fn); return timers.length; }, clearTimeout() {} });
  const click = dataset => handlers.click({ target: { closest: () => ({ dataset }) } });
  const answer = (id, launch, value) => {
    click({ action: 'agent', agentLaunch: launch });
    click({ action: 'option', question: id, option: value });
    handlers.submit({ preventDefault() {}, target: { dataset: { questionId: id } } });
    timers.shift()();
    return root.innerHTML;
  };
  return { root, handlers, answer };
}
function check(name, ok) { console.log((ok ? 'PASS ' : 'FAIL ') + name); if (!ok) failures++; }
let f = fixture();
check('补充逻辑探针：选择不包含的基准分支', f.answer('q-1', 'launch-41c7', '不包含').includes('默认不包含已归档条目'));
f = fixture();
const opposite = f.answer('q-1', 'launch-41c7', '包含');
check('补充逻辑探针：选择包含后不得宣称默认不包含', !opposite.includes('默认不包含已归档条目'));
f = fixture();
const keep = f.answer('q-2', 'launch-e7b4', '保留一个版本');
check('补充逻辑探针：选择保留后不得宣称删除迁移代码', !keep.includes('按答复继续：删除 0.8 迁移代码'));
f = fixture();
f.handlers.change({ target: { dataset: { setting: 'notifications' }, checked: false } });
check('补充逻辑探针：关闭通知后清空', !f.root.innerHTML.includes('data-notice-launch='));
f.handlers.change({ target: { dataset: { setting: 'notifications' }, checked: true } });
check('补充逻辑探针：重新启用不得重放同一问题（T-110）', !f.root.innerHTML.includes('data-notice-launch='));
process.exit(failures ? 1 : 0);
''', encoding='utf-8')
    rc, output = run(['node', str(probe), str(root / 'docs/assets/demo.js')])
    failed = failed or rc != 0
    if '--static-only' in sys.argv:
        raise SystemExit(1 if failed else 0)

    extra = work / 'independent-scenarios.mjs'
    extra.write_text(r'''
export default [{ name: 'R01 独立输入与通知反例', async run({page, url, check, sleep}) {
  await page.load(url);
  await page.click('[data-question-id="q-1"] [data-option="包含"]');
  await page.click('[data-question-id="q-1"] > button');
  await sleep(1300);
  const lines = await page.eval(`document.querySelector('.pane[data-launch-id="launch-41c7"] .terminal-lines').textContent`);
  check('选择包含后写回所选答案', lines.includes('› 包含'));
  check('选择包含后不得追加相反的决定', !lines.includes('默认不包含已归档条目'));
  check('非默认答案作答后状态回落', await page.eval(`document.querySelector('[data-agent-launch="launch-41c7"]').dataset.agentState`) === 'running');
  await page.load(url);
  await page.click('[data-agent-launch="launch-e7b4"]');
  await page.click('[data-question-id="q-2"] [data-option="保留一个版本"]');
  await page.click('[data-question-id="q-2"] > button');
  await sleep(1300);
  const kept = await page.eval(`document.querySelector('.pane[data-launch-id="launch-e7b4"] .terminal-lines').textContent`);
  check('选择保留后不得追加删除迁移代码的决定', !kept.includes('按答复继续：删除 0.8 迁移代码'));
  await page.load(url);
  await page.click('.sidebar-settings summary');
  await page.click('[data-setting="notifications"]');
  await page.click('[data-setting="notifications"]');
  check('重新启用通知不重放同一问题', await page.eval(`document.querySelectorAll('[data-notice-launch]').length`) === 0);
}}];
''', encoding='utf-8')

    def browser(site, options):
        global failed
        # 服务器脱离调用者进程组；只回收本脚本启动的进程。
        log = (work / 'http.log').open('w', encoding='utf-8')
        server = subprocess.Popen(['python3', '-u', '-m', 'http.server', '0', '--bind', '127.0.0.1',
                                   '--directory', str(site)], stdout=log, stderr=log, start_new_session=True)
        try:
            port = None
            import re
            for _ in range(100):
                match = re.search(r'port (\d+)', (work / 'http.log').read_text(encoding='utf-8'))
                if match:
                    port = match.group(1)
                    break
                if server.poll() is not None:
                    break
                time.sleep(0.05)
            if not port:
                print('INCOMPLETE: 临时服务器没有启动', flush=True)
                return 2, ''
            return run(['node', str(evidence / 'check_demo.mjs'), '--url',
                        'http://127.0.0.1:' + port + '/', *options])
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
            log.close()

    # 作者驱动自行新建 Chrome profile 并在 finally 删除；不使用用户 profile。
    print('真实 Chrome：当前候选的完整桌面与手机模拟检查', flush=True)
    rc, output = browser(root / 'docs', [])
    failed = failed or rc != 0
    print('真实 Chrome：独立选择相反答案及通知开关往返', flush=True)
    rc, output = browser(root / 'docs', ['--viewport', 'desktop', '--scenarios', extra.as_uri()])
    failed = failed or rc != 0

    mutations = [
        ('answer-keeps-waiting', '03', "      agent.state = 'running';", '      agent.state = agent.state;', '构思主控回落为运行中'),
        ('more-count-wrong', '05', 'list.length - 4', 'list.length - 3', '超过四个时先显示四个'),
    ]
    for name, scenario, old, new, assertion in mutations:
        site = work / name
        shutil.copytree(root / 'docs', site)
        source = site / 'assets/demo.js'
        text = source.read_text(encoding='utf-8')
        if text.count(old) != 1:
            raise SystemExit('INCOMPLETE: 变异锚点不是唯一一处')
        source.write_text(text.replace(old, new), encoding='utf-8')
        print('真实 Chrome 变异：' + name, flush=True)
        rc, output = browser(site, ['--only', scenario])
        rejected = rc == 1 and any(line.startswith('FAIL') and assertion in line for line in output.splitlines())
        print(('PASS 已被目标断言拒绝：' if rejected else 'FAIL 未取得目标拒收证据：') + name, flush=True)
        failed = failed or not rejected

print('T-113 独立复验 ' + ('NO_GO' if failed else 'PASS'), flush=True)
raise SystemExit(1 if failed else 0)
PY
