// Observe GitHub's actual rendered README in an isolated public browser session.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { CDP, sleep, until } from './check-branding.mjs';

const out = process.argv[2], inputs = process.argv[3];
mkdirSync(out);
const profile = join(out, 'profile');
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ['--headless=new', '--remote-debugging-port=0', '--user-data-dir=' + profile,
    '--no-first-run', '--no-default-browser-check', 'about:blank'], { detached: true, stdio: 'ignore' });
const report = { status: 'INCOMPLETE', url: 'https://github.com/a1024053774/Enchanted', checks: [] };
let page;
try {
  const port = await until(() => existsSync(join(profile, 'DevToolsActivePort')) &&
    readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0], 'Chrome not ready');
  const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
  page = await CDP.connect(target.webSocketDebuggerUrl);
  await page.send('Page.enable');
  await page.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await page.send('Page.navigate', { url: report.url });
  await until(() => page.evaluate(`!!document.querySelector('img[alt="Enchanted 标志"]')`), 'GitHub README logo missing');
  for (const theme of ['light', 'dark']) {
    await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: theme }] });
    await until(() => page.evaluate(`(() => { const image = document.querySelector('img[alt="Enchanted 标志"]');
      return image.currentSrc.endsWith('/logo-on-${theme}.png') && image.complete && image.naturalWidth > 0; })()`),
    'GitHub selected logo did not finish loading: ' + theme);
    const logo = await page.evaluate(`(async () => {
      const image = document.querySelector('img[alt="Enchanted 标志"]');
      await image.decode(); image.scrollIntoView({block:'center'});
      return { src: image.currentSrc, width: image.naturalWidth, picture: image.closest('picture') !== null };
    })()`);
    assert.ok(logo.width > 0 && logo.picture);
    const response = await fetch(logo.src);
    assert.ok(response.ok);
    assert.ok(Buffer.from(await response.arrayBuffer()).equals(readFileSync(join(inputs, `original-on-${theme}.png`))), 'GitHub logo differs from supplied original');
    report.checks.push({ theme, ...logo });
    await page.capture(join(out, theme + '.png'));
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); process.exitCode = 1; }
finally {
  page?.ws.close(); chrome.kill('SIGTERM'); await sleep(200);
  writeFileSync(join(out, 'result.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(report));
}
