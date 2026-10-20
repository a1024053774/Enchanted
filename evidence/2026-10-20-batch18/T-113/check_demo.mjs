// T-113 产品页的真实浏览器检查：用本机 Google Chrome（无头、隔离的临时 profile）经 CDP 打开页面，
// 逐项点击演示交互，读控制台与异常，桌面和手机宽度各跑一遍；截图只写到 --shots 目录，供自查。
// 用法：node check_demo.mjs --url http://127.0.0.1:8613/ --shots /private/tmp/t113-shots [--only tracer]
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, list) =>
  value.startsWith('--') ? [...pairs, [value.slice(2), list[index + 1]]] : pairs, []));
const url = args.url ?? 'http://127.0.0.1:8613/';
const shots = args.shots ?? null;
const chromePath = args.chrome ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if (shots) mkdirSync(shots, { recursive: true });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// 每个视口用一个新的 Chrome 进程和临时 profile。同一进程里先跑桌面再跑手机时，手机一轮反复在中途停住：
// CDP 调用超时，Debugger.pause 也停不下来（渲染进程没有在执行 JS）；手机单独跑则稳定通过。根因未查明，见 flaky-runs.txt。
let profile, chrome;
function launchChrome() {
  profile = mkdtempSync('/private/tmp/t113-chrome-');
  chrome = spawn(chromePath, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
}
async function stopChrome() {
  if (!chrome) return;
  const exited = new Promise(resolve => chrome.exitCode !== null ? resolve() : chrome.once('exit', resolve));
  chrome.kill('SIGTERM');
  await Promise.race([exited, sleep(10000)]);
  rmSync(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
  chrome = null;
}

async function devtoolsPort() {
  const file = join(profile, 'DevToolsActivePort');
  for (let i = 0; i < 300; i++) {
    if (chrome.exitCode !== null) throw new Error('Chrome exited during startup: ' + chrome.exitCode);
    if (existsSync(file)) { const port = readFileSync(file, 'utf8').split('\n')[0]; if (port) return port; }
    await sleep(100);
  }
  throw new Error('Chrome DevTools port not found');
}

class Page {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.problems = []; this.handlers = [];
    ws.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id); this.pending.delete(message.id);
        message.error ? reject(new Error(message.error.message)) : resolve(message.result);
      } else if (message.method) this.handlers.forEach(handler => handler(message));
    });
    ws.addEventListener('close', () => { for (const { reject } of this.pending.values()) reject(new Error('DevTools connection closed')); this.pending.clear(); });
    this.handlers.push(({ method, params }) => {
      if (method === 'Runtime.exceptionThrown') this.problems.push('exception: ' + (params.exceptionDetails.exception?.description ?? params.exceptionDetails.text));
      if (method === 'Runtime.consoleAPICalled' && ['error', 'warning', 'assert'].includes(params.type))
        this.problems.push(`console.${params.type}: ` + params.args.map(arg => arg.value ?? arg.description).join(' '));
      if (method === 'Log.entryAdded' && ['error', 'warning'].includes(params.entry.level))
        this.problems.push(`log.${params.entry.level}: ${params.entry.text} ${params.entry.url ?? ''}`);
    });
  }
  send(method, params = {}) { const id = ++this.id; this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`CDP ${method} timed out`)); }, 20000);
      this.pending.set(id, { resolve: value => { clearTimeout(timer); resolve(value); }, reject: error => { clearTimeout(timer); reject(error); } });
    }); }
  async eval(expression) {
    const result = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error('eval failed: ' + (result.exceptionDetails.exception?.description ?? result.exceptionDetails.text));
    return result.result.value;
  }
  async load(target) {
    let handler;
    const loaded = new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('load timed out: ' + target)), 20000);
      handler = ({ method }) => { if (method === 'Page.loadEventFired') { clearTimeout(timer); resolve(); } };
      this.handlers.push(handler);
    });
    loaded.catch(() => {}); // 由下面的 await 报告；避免导航命令先失败时留下未处理的拒绝
    try { await this.send('Page.navigate', { url: target }); await loaded; }
    finally { this.handlers.splice(this.handlers.indexOf(handler), 1); }
    await sleep(150);
  }
  async center(selector) {
    const box = await this.eval(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) return null;
      el.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' }); const r = el.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; })()`);
    if (!box || !box.w) throw new Error('not visible: ' + selector);
    return box;
  }
  async click(selector, button = 'left') {
    const { x, y } = await this.center(selector);
    for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased'])
      await this.send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseMoved' ? 'none' : button, clickCount: type === 'mouseMoved' ? 0 : 1 });
    await sleep(60);
  }
  async tap(selector) {
    const { x, y } = await this.center(selector);
    await this.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
    await this.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await sleep(350); // 间隔短于双击判定时，浏览器会把两次轻点当成双击而不派发 click
  }
  async key(key, code = key, keyCode = 0, modifiers = 0) {
    const text = key === 'Enter' ? '\r' : key.length === 1 ? key : undefined;
    await this.send('Input.dispatchKeyEvent', { type: text ? 'keyDown' : 'rawKeyDown', key, code, windowsVirtualKeyCode: keyCode, modifiers, text, unmodifiedText: text });
    await this.send('Input.dispatchKeyEvent', { type: 'keyUp', key, code, windowsVirtualKeyCode: keyCode, modifiers });
    await sleep(40);
  }
  async type(text) { await this.send('Input.insertText', { text }); await sleep(40); }
  async shot(name) {
    if (!shots) return;
    const { data } = await this.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    writeFileSync(join(shots, name + '.png'), Buffer.from(data, 'base64'));
  }
}

const viewports = {
  desktop: { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false },
  phone: { width: 390, height: 844, deviceScaleFactor: 2, mobile: true },
};

const results = [];
const here = new URL('.', import.meta.url);
const relative = value => String(value).replaceAll(here.href, './').replaceAll(here.pathname, './');
function check(viewport, name, ok, detail = '') { results.push({ viewport, name, ok: Boolean(ok), detail: relative(detail) }); }

const scenarios = (await import(args.scenarios ?? './scenarios.mjs')).default;

try {
  for (const [viewport, metrics] of Object.entries(viewports)) {
    if (args.viewport && args.viewport !== viewport) continue;
    await stopChrome();
    launchChrome();
    const port = await devtoolsPort();
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.addEventListener('open', resolve); ws.addEventListener('error', reject); });
    const page = new Page(ws);
    await page.send('Page.enable'); await page.send('Runtime.enable'); await page.send('Log.enable'); await page.send('Performance.enable');
    await page.send('Emulation.setDeviceMetricsOverride', metrics);
    if (metrics.mobile) await page.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
    for (const scenario of scenarios) {
      if (args.only && !scenario.name.startsWith(args.only)) continue;
      if (scenario.viewports && !scenario.viewports.includes(viewport)) continue;
      const before = page.problems.length;
      console.error(`… [${viewport}] ${scenario.name}`);
      try { await scenario.run({ page, url, viewport, check: (name, ok, detail) => check(viewport, `${scenario.name}: ${name}`, ok, detail), sleep }); }
      catch (error) { check(viewport, `${scenario.name}: 运行`, false, String(error.stack ?? error)); }
      check(viewport, `${scenario.name}: 控制台无报错`, page.problems.length === before, page.problems.slice(before).join(' | '));
      if (args.metrics) {
        const { metrics: values } = await page.send('Performance.getMetrics').catch(() => ({ metrics: [] }));
        const pick = name => values.find(item => item.name === name)?.value;
        console.error(`   nodes=${pick('Nodes')} heap=${Math.round((pick('JSHeapUsedSize') ?? 0) / 1e6)}MB listeners=${pick('JSEventListeners')}`);
      }
    }
    ws.close();
  }
} finally {
  await stopChrome();
}

let failed = 0;
for (const row of results) { if (!row.ok) failed++; console.log(`${row.ok ? 'PASS' : 'FAIL'}  [${row.viewport}] ${row.name}${row.detail ? '  — ' + row.detail : ''}`); }
console.log(`\n${results.length - failed}/${results.length} PASS`);
process.exit(failed ? 1 : 0);
