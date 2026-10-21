#!/bin/sh
# 第二轮独立复验；从仓库根目录运行本脚本。默认包含真实 Chrome。
# --static-only 只运行逻辑反事实，不能关闭浏览器缺口。
# 固定候选；全部副本、Chrome profile、服务器日志在新建 /tmp 目录，退出时清理。
set -eu
export LC_ALL=C
cd "$(dirname "$0")/../../.."
python3 - "$@" <<'PY'
import io
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

root = Path.cwd()
candidate = '8341208d7ce67c435d84e8259786fdfb9a4646de'
baseline = '28b2ab19bcd2fe500125fdb9be1540e07f8ad0fc'
ev = 'evidence/2026-10-20-batch18/T-113/'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=str(root))
if git('rev-parse', 'HEAD').decode().strip() != candidate:
    raise SystemExit('INCOMPLETE：候选已经变化')
if git('diff', '--name-only', candidate, '--', 'docs', ev).strip():
    raise SystemExit('INCOMPLETE：被审查文件有受控改动')
print('候选 ' + candidate + '；修前 ' + baseline, flush=True)
failed = False
incomplete = False

with tempfile.TemporaryDirectory(prefix='t113-review02-', dir='/tmp') as tmp:
    work = Path(tmp)
    def export(rev, destination):
        destination.mkdir()
        data = git('archive', rev, 'docs')
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                if not (member.isfile() or member.isdir()) or '..' in Path(member.name).parts or member.name.startswith('/'):
                    raise SystemExit('INCOMPLETE：归档含非普通文件或异常路径')
            archive.extractall(str(destination))
        return destination / 'docs'
    oldsite = export(baseline, work / 'before')
    newsite = export(candidate, work / 'after')

    # 独立预期来自派发、QuestionsPanel 与 NotificationCenter，不导入页面的回复常量。
    # 这里用最小 DOM 替身驱动原始事件处理与定时回调，只证明确定性逻辑。
    probe = work / 'logic.mjs'
    probe.write_text(r'''
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync(process.argv[2] + '/assets/demo.js', 'utf8');
let failures = 0;
function check(name, ok, detail = '') {
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' — ' + detail : ''));
  if (!ok) failures++;
}
function fixture() {
  const handlers = {}, timers = [];
  const root = { innerHTML: '', dataset: {}, contains: () => true, querySelectorAll: () => [], querySelector: () => null,
    addEventListener: (name, fn) => { handlers[name] = fn; } };
  vm.runInNewContext(source, { document: { activeElement: null, getElementById: () => root, querySelectorAll: () => [] },
    setTimeout: fn => { timers.push(fn); return timers.length; }, clearTimeout() {} });
  const click = dataset => handlers.click({ target: { closest: () => ({ dataset }) } });
  return { root, handlers, answer(id, launch, value, free = false) {
    click({ action: 'agent', agentLaunch: launch });
    if (free) handlers.input({ target: { dataset: { answer: id }, value,
      closest: () => ({ querySelectorAll: () => [], querySelector: () => ({ disabled: false }) }) } });
    else click({ action: 'option', question: id, option: value });
    handlers.submit({ preventDefault() {}, target: { dataset: { questionId: id } } });
    timers.shift()();
    return root.innerHTML;
  } };
}
if (process.argv[3] === 'sentinel') {
  for (const [id, launch] of [['q-1', 'launch-41c7'], ['q-2', 'launch-e7b4']]) {
    for (const value of ['constructor', '__proto__', 'toString']) {
      try {
        const html = fixture().answer(id, launch, value, true);
        check('自由答复原型同名 ' + id + ' ' + value, html.includes('› ' + value) && html.includes('原文继续'));
      } catch (e) { check('自由答复原型同名 ' + id + ' ' + value, false, String(e)); }
    }
  }
} else {
  for (const [id, launch, value, yes, no] of [
    ['q-1', 'launch-41c7', '不包含', '默认不包含已归档条目', '默认包含已归档条目'],
    ['q-1', 'launch-41c7', '包含', '默认包含已归档条目', '默认不包含已归档条目'],
    ['q-2', 'launch-e7b4', '不再支持', '删除 0.8 迁移代码', '保留 0.8 迁移代码'],
    ['q-2', 'launch-e7b4', '保留一个版本', '保留 0.8 迁移代码', '删除 0.8 迁移代码']]) {
    try {
      const html = fixture().answer(id, launch, value);
      check('选项对应 ' + value, html.includes('› ' + value) && html.includes(yes) && !html.includes(no));
    } catch (e) { check('选项对应 ' + value, false, String(e)); }
  }
  for (const [id, launch] of [['q-1', 'launch-41c7'], ['q-2', 'launch-e7b4']]) {
    const sentinel = 'R02-74 先确认维护边界 <待定>';
    try {
      const html = fixture().answer(id, launch, sentinel, true);
      check('自由答复仅确认 ' + id, html.includes('R02-74 先确认维护边界 &lt;待定&gt;') && html.includes('原文继续') &&
        !html.includes('默认不包含已归档条目') && !html.includes('默认包含已归档条目') &&
        !html.includes('删除 0.8 迁移代码') && !html.includes('保留 0.8 迁移代码'));
    } catch (e) { check('自由答复仅确认 ' + id, false, String(e)); }
  }
  const f = fixture();
  check('初始通知存在', f.root.innerHTML.includes('data-notice-launch='));
  f.handlers.change({ target: { dataset: { setting: 'notifications' }, checked: false } });
  check('关闭清空通知', !f.root.innerHTML.includes('data-notice-launch='));
  f.handlers.change({ target: { dataset: { setting: 'notifications' }, checked: true } });
  check('开启不重放通知', !f.root.innerHTML.includes('data-notice-launch='));
  const html = fs.readFileSync(process.argv[2] + '/index.html', 'utf8');
  check('Dock 前后台限制说明', html.includes('窗口在前台时角标为零') && html.includes('演示不模拟前后台切换'));
}
console.log('逻辑失败数 ' + failures);
process.exit(failures ? 1 : 0);
''', encoding='utf-8')

    def run(args, timeout=180):
        process = subprocess.Popen(args, cwd=str(work), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, start_new_session=True)
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
            print(output, end='', flush=True)
            print('INCOMPLETE：命令超时', flush=True)
            return 2, output
        print(output, end='', flush=True)
        return process.returncode, output

    print('独立逻辑：修前反事实', flush=True)
    rc, out = run(['node', str(probe), str(oldsite)])
    red = rc == 1 and all('FAIL ' + label in out for label in ['选项对应 包含', '选项对应 保留一个版本', '自由答复仅确认 q-2', '开启不重放通知', 'Dock 前后台限制说明'])
    print(('PASS' if red else 'FAIL') + ' 修前按目标缺陷拒绝', flush=True)
    failed |= not red
    print('独立逻辑：修后普通路径', flush=True)
    rc, _ = run(['node', str(probe), str(newsite)])
    failed |= rc != 0
    print('独立逻辑：未预设的自由答复（当前发现，不纳入变异拒收判断）', flush=True)
    rc, _ = run(['node', str(probe), str(newsite), 'sentinel'])
    failed |= rc != 0

    # 两项定向变异；只用普通路径里的指定断言判拒收，崩溃不算。
    mutations = [
        ('固定首选回复', 'question.replies[value] ?? question.freeReply;', 'Object.values(question.replies)[0];', '选项对应 包含'),
        ('重放已见通知', 'if (ui.notifications && !ui.noticeSeen.has(id))', 'if (ui.notifications)', '开启不重放通知'),
    ]
    mutant_sites = []
    for index, (name, old, new, label) in enumerate(mutations):
        site = work / ('mutant-' + str(index))
        shutil.copytree(newsite, site)
        path = site / 'assets/demo.js'
        source = path.read_text(encoding='utf-8')
        if source.count(old) != 1:
            raise SystemExit('INCOMPLETE：变异锚点不唯一')
        path.write_text(source.replace(old, new), encoding='utf-8')
        rc, out = run(['node', str(probe), str(site)])
        rejected = rc == 1 and ('FAIL ' + label) in out and 'TypeError' not in out
        print(('PASS' if rejected else 'FAIL') + ' 定向变异被业务断言拒绝：' + name, flush=True)
        failed |= not rejected
        mutant_sites.append((name, site, label))

    if '--static-only' in sys.argv:
        print('INCOMPLETE：按参数跳过真实浏览器；逻辑结果 ' + ('NO_GO' if failed else 'PASS'), flush=True)
        raise SystemExit(1 if failed else 2)

    # 只复用冻结候选的 CDP 传输驱动；独立场景如下。作者场景仅用于核对新检查的红绿。
    driver = work / 'check_demo.mjs'
    source = git('show', candidate + ':' + ev + 'check_demo.mjs').decode('utf-8')
    source = source.replace("mkdtempSync('/private/tmp/t113-chrome-')", 'mkdtempSync(' + repr(str(work / 'chrome-')) + ')')
    driver.write_text(source, encoding='utf-8')
    (work / 'scenarios.mjs').write_bytes(git('show', candidate + ':' + ev + 'scenarios.mjs'))

    independent = work / 'independent.mjs'
    independent.write_text(r'''
const q = JSON.stringify;
const val = (p, sel) => p.eval(`document.querySelector(${q(sel)})?.textContent ?? ''`);
const focus = (p, sel) => p.eval(`document.querySelector(${q(sel)}).focus()`);
const noX = p => p.eval('document.documentElement.scrollWidth <= innerWidth && document.body.scrollWidth <= innerWidth');
export default [
  { name: 'R02A 选项与通知独立输入', async run({page:p, url, check, sleep}) {
    for (const [id, launch, choice, yes, no] of [
      ['q-1','launch-41c7','不包含','默认不包含已归档条目','默认包含已归档条目'],
      ['q-1','launch-41c7','包含','默认包含已归档条目','默认不包含已归档条目'],
      ['q-2','launch-e7b4','不再支持','删除 0.8 迁移代码','保留 0.8 迁移代码'],
      ['q-2','launch-e7b4','保留一个版本','保留 0.8 迁移代码','删除 0.8 迁移代码']]) {
      await p.load(url); await p.click(`[data-agent-launch="${launch}"]`);
      await p.click(`[data-question-id="${id}"] [data-option="${choice}"]`);
      await p.click(`[data-question-id="${id}"] > button`); await sleep(1300);
      const text = await val(p, `.pane[data-launch-id="${launch}"] .terminal-lines`);
      check('选项对应 ' + choice, text.includes('› ' + choice) && text.includes(yes) && !text.includes(no));
    }
    await p.load(url); await p.click('.sidebar-settings summary');
    check('初始提醒一次', await p.eval('document.querySelectorAll("[data-notice-launch]").length') === 1);
    await p.click('[data-setting="notifications"]');
    check('关闭清空通知', await p.eval('document.querySelectorAll("[data-notice-launch]").length') === 0);
    await p.click('[data-setting="notifications"]');
    check('开启不重放通知', await p.eval('document.querySelectorAll("[data-notice-launch]").length') === 0);
    check('仍有独立 Dock 待答数', (await val(p,'[data-dock] b')) === '1');
  } },
  { name: 'R02B 自由答复与原型同名', async run({page:p, url, check, sleep}) {
    for (const [id, launch] of [['q-1','launch-41c7'],['q-2','launch-e7b4']]) {
      for (const answer of ['R02-74 请先确认 <范围>', 'constructor', '__proto__', 'toString']) {
        await p.load(url); await p.click(`[data-agent-launch="${launch}"]`);
        await p.click(`[data-question-id="${id}"] input`); await p.type(answer);
        await p.click(`[data-question-id="${id}"] > button`); await sleep(1300);
        const text = await val(p, `.pane[data-launch-id="${launch}"] .terminal-lines`);
        check('仅确认原文 ' + id + ' ' + answer, text.includes('› ' + answer) && text.includes('原文继续') &&
          !text.includes('默认不包含已归档条目') && !text.includes('默认包含已归档条目') &&
          !text.includes('删除 0.8 迁移代码') && !text.includes('保留 0.8 迁移代码'));
        check('作答完成后面板退出 ' + id + ' ' + answer, await p.eval(`!document.querySelector('[data-question-id="${id}"]')`));
      }
    }
  } },
  { name: 'R02C 浏览器缺口', async run({page:p, url, viewport, check, sleep}) {
    await p.load(url);
    await p.eval("localStorage.removeItem('enchanted-theme')");
    for (const [theme, background] of [['dark','rgb(17, 17, 17)'],['light','rgb(246, 246, 244)']]) {
      await p.send('Emulation.setEmulatedMedia', {features:[{name:'prefers-color-scheme',value:theme}]});
      await p.load(url);
      check('系统主题 ' + theme, await p.eval('getComputedStyle(document.body).backgroundColor') === background);
      check('终端页没有横向页面滚动 ' + theme, await noX(p));
      await p.click('[data-flow-tab]');
      check('流程页没有横向页面滚动 ' + theme, await noX(p));
    }
    if (viewport === 'phone') {
      check('窄屏滚动限演示画布', await p.eval(`(() => {const c=document.querySelector('.demo-canvas');c.scrollLeft=100;
        return c.scrollWidth>c.clientWidth && c.scrollLeft>0 && scrollX===0;})()`));
    }
    await p.load(url);
    await focus(p,'[data-theme-toggle]'); await p.key('Enter','Enter',13);
    check('Enter 手动切浅色', await p.eval("document.documentElement.dataset.theme === 'light'"));
    await p.key(' ','Space',32);
    check('Space 手动切深色', await p.eval("document.documentElement.dataset.theme === 'dark'"));
    await p.load(url);
    check('主题刷新后保留', await p.eval("document.documentElement.dataset.theme === 'dark'"));
    for (const theme of ['light','dark']) {
      await p.eval(`document.documentElement.dataset.theme=${q(theme)}`);
      await focus(p,'[data-project-id="inkwell"]');
      await p.key('Tab','Tab',9);
      check('Tab 按项目顺序 ' + theme, await p.eval("document.activeElement.dataset.projectId === 'tidepool'"));
      check('焦点可见 ' + theme, await p.eval(`(() => {const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();
        return e.matches(':focus-visible') && s.outlineStyle!=='none' && parseFloat(s.outlineWidth)>=2 && s.outlineColor!=='rgba(0, 0, 0, 0)' && r.width>0 && r.height>0 && r.right>0 && r.left<innerWidth;})()`));
    }
    await p.key('Enter','Enter',13);
    check('Enter 切换项目并保留焦点', await p.eval("document.activeElement.dataset.projectId === 'tidepool' && document.activeElement.getAttribute('aria-current') === 'page'"));
    await p.key('Tab','Tab',9,8); // Shift+Tab
    check('Shift+Tab 可回退', await p.eval("document.activeElement.dataset.projectId === 'inkwell'"));
    await focus(p,'[data-demo-go="question"]'); await p.key('Enter','Enter',13);
    check('引导键盘到提问', await p.eval("document.activeElement.dataset.action === 'option'"));
    await p.key(' ','Space',32);
    check('空格选中选项', await p.eval("document.activeElement.getAttribute('aria-pressed') === 'true'"));
    await p.key('Tab','Tab',9); await p.key('Tab','Tab',9); await p.key('Tab','Tab',9);
    check('自然 Tab 到发送按钮', await p.eval("document.activeElement.dataset.fk === 'send:q-1'"));
    await p.key('Enter','Enter',13); await sleep(1300);
    check('键盘完成发送', await p.eval("!document.querySelector('[data-question-id=\"q-1\"]')"));
    await focus(p,'[data-demo-go="menu"]'); await p.key('Enter','Enter',13);
    check('引导到菜单按钮', await p.eval("document.activeElement.classList.contains('pane-menu-trigger')"));
    await p.key('Enter','Enter',13);
    check('键盘打开菜单', await p.eval("document.activeElement.closest('.pane-menu') !== null"));
    await p.key('ArrowDown','ArrowDown',40); await p.key('Escape','Escape',27);
    check('Esc 关闭并还焦点', await p.eval("!document.querySelector('.pane-menu') && document.activeElement.classList.contains('pane-menu-trigger')"));
    await focus(p,'[data-demo-go="flow"]'); await p.key('Enter','Enter',13);
    check('键盘进入流程页', await p.eval("document.querySelector('[data-flow-tab]').getAttribute('aria-current') === 'page'"));
    await focus(p,'[data-demo-go="reset"]'); await p.key(' ','Space',32);
    check('键盘重置演示', await p.eval("document.querySelectorAll('[data-notice-launch]').length === 1"));
    await p.send('Emulation.setScriptExecutionDisabled',{value:true});
    try {
      await p.load(url);
      const text=await p.eval('document.body.innerText');
      for (const phrase of ['让 Claude Code 和 Codex','为什么要门禁','一张票怎么走完','两层主控','现在能用的','已知限制','路线图','未做','下载与安装','GPL-3.0','可点击的演示需要 JavaScript。'])
        check('禁 JS 可读 ' + phrase, text.includes(phrase));
      check('禁 JS 隐藏交互引导', await p.eval(`[...document.querySelectorAll('[data-tour],[data-demo-go="reset"],[data-theme-toggle]')].every(e=>e.getClientRects().length===0)`));
      check('禁 JS 没有页面横滚', await noX(p));
    } finally { await p.send('Emulation.setScriptExecutionDisabled',{value:false}); }
  } },
];
''', encoding='utf-8')

    def browser(site, options):
        logpath = work / 'http.log'
        with logpath.open('w', encoding='utf-8') as log:
            server = subprocess.Popen(['python3', '-u', '-m', 'http.server', '0', '--bind', '127.0.0.1', '--directory', str(site)],
                                      stdout=log, stderr=log, start_new_session=True)
            try:
                port = None
                for _ in range(100):
                    match = re.search(r'port (\d+)', logpath.read_text(encoding='utf-8'))
                    if match:
                        port = match.group(1)
                        break
                    if server.poll() is not None:
                        break
                    time.sleep(0.05)
                if not port:
                    print('INCOMPLETE：服务器启动失败 ' + logpath.read_text(encoding='utf-8')[-600:], flush=True)
                    return 2, ''
                return run(['node', str(driver), '--url', 'http://127.0.0.1:' + port + '/', *options], timeout=240)
            finally:
                if server.poll() is None:
                    server.terminate()
                    try:
                        server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()

    # Chrome 预探针：无网络、不写用户 profile，失败时不把环境错误当红态。
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    print('Chrome 启动探针', flush=True)
    rc, out = run([chrome, '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-extensions',
                   '--user-data-dir=' + str(work / 'preflight-profile'), '--dump-dom', 'about:blank'], timeout=25)
    if rc != 0 or '<html' not in out:
        print('INCOMPLETE：Chrome 启动失败，退出码 ' + str(rc) + '；浏览器检查未执行', flush=True)
        incomplete = True
    else:
        print('新增作者检查在 git archive 修前 docs 上应红、修后应绿', flush=True)
        rc, out = browser(oldsite, ['--only','03b'])
        wanted = ['选“包含”后终端说的是包含','选“保留一个版本”后终端说的是保留','自由答复只确认收到，不套用预设决定','重新开启后不重放同一问题']
        red = rc == 1 and all(any(line.startswith('FAIL') and label in line for line in out.splitlines()) for label in wanted) and '运行  —' not in out
        print(('PASS' if red else 'FAIL') + ' 新增检查取得修前目标红态', flush=True)
        failed |= not red
        rc, out = browser(newsite, ['--only','03b'])
        failed |= rc != 0
        incomplete |= not re.search(r'\d+/\d+ PASS', out)
        print('独立真实 Chrome 场景：四选项、自由答复、窄屏、主题、键盘、禁 JS、控制台', flush=True)
        rc, out = browser(newsite, ['--scenarios', independent.as_uri()])
        failed |= rc != 0
        incomplete |= not re.search(r'\d+/\d+ PASS', out)
        for name, site, label in mutant_sites:
            rc, out = browser(site, ['--scenarios', independent.as_uri(), '--only','R02A','--viewport','desktop'])
            rejected = rc == 1 and any(line.startswith('FAIL') and label in line for line in out.splitlines()) and 'TypeError' not in out
            print(('PASS' if rejected else 'FAIL') + ' Chrome 定向变异拒收：' + name, flush=True)
            failed |= not rejected

print('逻辑与行为结论 ' + ('NO_GO' if failed else 'PASS') + '；浏览器证据 ' + ('INCOMPLETE' if incomplete else '已执行'), flush=True)
raise SystemExit(1 if failed else 2 if incomplete else 0)
PY
