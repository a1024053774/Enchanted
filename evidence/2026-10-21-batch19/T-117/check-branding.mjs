// Real Chrome / Electron renderer probe. Expected asset names come from T-117.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

export const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
export async function until(read, message) {
  const end = Date.now() + 30_000;
  while (Date.now() < end) {
    const value = await read();
    if (value) return value;
    await sleep(100);
  }
  throw new Error(message);
}
export class CDP {
  constructor(ws) {
    this.ws = ws; this.next = 0; this.pending = new Map(); this.errors = [];
    ws.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.method === 'Debugger.paused') this.paused = message.params;
      if (message.method === 'Runtime.exceptionThrown') this.errors.push(message.params.exceptionDetails);
      const entry = this.pending.get(message.id);
      if (!entry) return;
      clearTimeout(entry.timer); this.pending.delete(message.id);
      message.error ? entry.reject(new Error(JSON.stringify(message.error))) : entry.resolve(message.result);
    });
  }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((resolve, reject) => {
      ws.addEventListener('open', resolve, { once: true });
      ws.addEventListener('error', reject, { once: true });
    });
    return new CDP(ws);
  }
  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.next;
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 15000);
      this.pending.set(id, { resolve, reject, timer });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const result = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
  async capture(path) {
    const { data } = await this.send('Page.captureScreenshot');
    writeFileSync(path, Buffer.from(data, 'base64'), { flag: 'wx' });
  }
}

async function checkSite(url, output) {
  const originals = { light: readFileSync(process.argv[4]), dark: readFileSync(process.argv[5]) };
  mkdirSync(output); // Preserve all earlier runs.
  const report = { status: 'INCOMPLETE', url, checks: [], argv: process.argv };
  const profile = join(output, 'chrome-profile');
  const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    ['--headless=new', '--remote-debugging-port=0', '--user-data-dir=' + profile,
      '--no-first-run', '--no-default-browser-check', 'about:blank'], { detached: true, stdio: 'ignore' });
  let page;
  const checkedAssets = new Set();
  try {
    const port = await until(() => existsSync(join(profile, 'DevToolsActivePort')) &&
      readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0], 'Chrome did not start');
    const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
    page = await CDP.connect(target.webSocketDebuggerUrl);
    await page.send('Runtime.enable');
    await page.send('Page.enable');
    await page.send('Page.navigate', { url });
    await until(() => page.evaluate('document.readyState === "complete" && !!document.querySelector("[data-theme-toggle]")'), 'Page not ready');
    for (const width of [1280, 390]) {
      await page.send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
      for (const system of ['light', 'dark']) {
        await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: system }] });
        for (const selected of ['system', 'light', 'dark']) {
          await page.evaluate(`(() => { const button = document.querySelector('[data-theme-toggle]');
            for (let i = 0; i < 3 && (document.documentElement.dataset.theme || 'system') !== ${JSON.stringify(selected)}; i++) button.click(); })()`);
          const theme = selected === 'system' ? system : selected;
          const result = await page.evaluate(`(async () => {
            await Promise.all([...document.images].map(image => image.decode()));
            const visible = [...document.querySelectorAll('.wordmark img')].filter(image => image.getBoundingClientRect().width > 0 && getComputedStyle(image).display !== 'none');
            return { images: visible.map(image => ({ src: image.currentSrc, width: image.naturalWidth })),
              favicon: document.querySelector('link[rel="icon"]:not([media])')?.href,
              overflow: document.documentElement.scrollWidth > innerWidth,
              demo: [...document.querySelectorAll('.wb .brand img')].map(image => ({ src: image.currentSrc, width: image.naturalWidth })) };
          })()`);
          assert.equal(result.images.length, 1, 'Exactly one header logo must be visible');
          assert.ok(result.images[0].src.endsWith(`/assets/brand/logo-on-${theme}.png`), `Wrong logo: ${JSON.stringify(result)}`);
          assert.ok(result.images[0].width > 0);
          if (!checkedAssets.has(result.images[0].src)) {
            const image = await fetch(result.images[0].src);
            assert.ok(image.ok);
            assert.ok(Buffer.from(await image.arrayBuffer()).equals(originals[theme]), 'Loaded logo must match the external original input');
            checkedAssets.add(result.images[0].src);
          }
          assert.ok(result.favicon?.endsWith(`/assets/brand/logo-on-${theme}.png`), 'Favicon must follow actual selected theme');
          assert.equal(result.overflow, false, 'Page must fit viewport');
          assert.equal(result.demo.length, 1);
          assert.ok(result.demo[0].width > 0 && result.demo[0].src.endsWith('/assets/brand/logo-on-dark.png'), 'Demo remains dark');
          report.checks.push({ width, system, selected, theme, ...result });
          if (selected === 'system') await page.capture(join(output, `${width}-${system}.png`));
        }
      }
    }
    assert.deepEqual(page.errors, []);
    report.status = 'PASS';
  } catch (error) {
    report.status = 'NO_GO'; report.error = String(error);
    throw error;
  } finally {
    page?.ws.close();
    const exited = new Promise(resolve => chrome.exitCode !== null ? resolve() : chrome.once('exit', resolve));
    chrome.kill('SIGTERM');
    await Promise.race([exited, sleep(5000)]);
    writeFileSync(join(output, 'result.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
    console.log(JSON.stringify({ status: report.status, checks: report.checks.length, error: report.error }));
  }
}
if (process.argv[1]?.endsWith('/check-branding.mjs')) await checkSite(process.argv[2], process.argv[3]);
