// Copied from evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs for 0.1.3; only the browser path may be
// given by PAGE_CHECK_CHROME (the Playwright Chromium cache was cleaned). Checks unchanged.
import { createRequire } from 'node:module';
const require = createRequire('/Users/luckye/Documents/Code/a1024053774.github.io/package.json');
const { chromium } = require('playwright-core');
const out = process.argv[2]; const fs = await import('node:fs'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.PAGE_CHECK_CHROME ?? (process.env.HOME + '/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing') });
const report = { errors: [], checks: [] };
const check = (name, ok, detail) => { report.checks.push({ name, ok, detail }); };
for (const scheme of ['light', 'dark']) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: scheme });
  page.on('pageerror', e => report.errors.push(scheme + ': ' + e.message));
  page.on('console', m => { if (m.type() === 'error') report.errors.push(scheme + ' console: ' + m.text()); });
  await page.goto('http://127.0.0.1:8765/'); await page.waitForTimeout(500);
  await page.screenshot({ path: `${out}/${scheme}-0-intro.png` });
  const state = () => page.evaluate(() => ({ y: Math.round(scrollY), tourTop: Math.round(document.querySelector('.tour').getBoundingClientRect().top),
    step: document.querySelector('[data-tour-index]').textContent, page: document.querySelector('.wb .workspace-pages [aria-current]')?.textContent }));
  await page.mouse.move(700, 450);
  await page.mouse.wheel(0, 100); await page.waitForTimeout(1200);
  let s = await state(); check(scheme + ' first wheel enters tour at step 1', s.tourTop === 0 && s.step === '1', s);
  for (let i = 2; i <= 10; i++) {
    await page.mouse.move(150, 450); // 在左侧说明区上滚动
    await page.mouse.wheel(0, 100); await page.waitForTimeout(500);
    s = await state(); check(`${scheme} one notch -> step ${i}`, s.step === String(i) && s.tourTop === 0, s);
    if (scheme === 'light' || i === 6 || i === 9) await page.screenshot({ path: `${out}/${scheme}-${i}.png` });
  }
  // 快速连滚三格（间隔 40ms）只算一步
  await page.mouse.wheel(0, -100); await page.waitForTimeout(40); await page.mouse.wheel(0, -100); await page.waitForTimeout(40); await page.mouse.wheel(0, -100);
  await page.waitForTimeout(500); s = await state(); check(scheme + ' fast burst of 3 notches = one step back', s.step === '9', s);
  await page.mouse.wheel(0, 100); await page.waitForTimeout(500);
  await page.mouse.wheel(0, 100); await page.waitForTimeout(1200);
  s = await state(); const max = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight); check(scheme + ' past last step leaves tour downward to page end', s.y >= max - 2 && s.tourTop < 0, { s, max });
  await page.screenshot({ path: `${out}/${scheme}-11-download.png` });
  await page.mouse.wheel(0, -100); await page.waitForTimeout(1200);
  s = await state(); check(scheme + ' wheel up from download returns to last step', s.tourTop === 0 && s.step === '10', s);
  if (scheme === 'light') try {
    // 演示内交互：第 2 步批准角色申请
    await page.click('[data-dot="1"]'); await page.waitForTimeout(400);
    await page.click('.wb [data-fk="rr-approve"]'); await page.waitForTimeout(200);
    const tree = await page.evaluate(() => [...document.querySelectorAll('.wb [data-agent-launch="launch-c4e8"]')].map(n => n.dataset.agentLevel));
    check('approve puts executor under ideation (level 1)', tree.join() === '1', tree);
    await page.screenshot({ path: `${out}/light-role-approved.png` });
    // 窗格菜单在缩放后的位置
    await page.click('[data-dot="3"]'); await page.waitForTimeout(400);
    const pane = await page.$('.wb .pane .terminal-scroll'); const box = await pane.boundingBox();
    await page.mouse.click(box.x + 40, box.y + 40, { button: 'right' }); await page.waitForTimeout(200);
    const menu = await page.$eval('.wb .pane-menu', n => n.getBoundingClientRect().toJSON());
    check('context menu opens at the pointer under scaling', Math.abs(menu.left - (box.x + 40)) < 6 && Math.abs(menu.top - (box.y + 40)) < 6, { menu, pointer: [box.x + 40, box.y + 40] });
    await page.screenshot({ path: `${out}/light-menu.png` });
    await page.keyboard.press('Escape');
    // 演示内可滚动区域先滚自己：指标页
    await page.click('[data-dot="7"]'); await page.waitForTimeout(400);
    const area = await (await page.$('.wb .metrics-page')).boundingBox();
    await page.mouse.move(area.x + area.width / 2, area.y + area.height / 2);
    await page.mouse.wheel(0, 100); await page.waitForTimeout(500);
    s = await state(); const st = await page.$eval('.wb .metrics-page', n => [n.scrollTop, n.scrollHeight, n.clientHeight]);
    check('wheel over overflowing metrics page scrolls it, not the step', s.step === '8' && st[0] > 0 || st[1] <= st[2] + 1, { s, st });
    // 与真实页面源码对照：记录页有任务、会话两个筛选；指标页模型使用有汇总表和逐会话表；设置弹窗里 Tab 不跑出去。
    await page.click('[data-dot="6"]'); await page.waitForTimeout(300);
    check('records page has task and session filters (RecordsPage.tsx)', await page.$$eval('.wb .user-input-page .record-filter select', n => n.length) === 2);
    await page.click('[data-dot="7"]'); await page.waitForTimeout(300);
    const heads = await page.$$eval('.wb [data-metric="model-use"] table thead', n => n.map(h => h.textContent));
    check('metrics model use has summary and per-session tables (MetricsPage.tsx)', heads.length === 2 && heads[1].includes('角色'), heads);
    check('metrics page has a date range (MetricsPage.tsx)', await page.$$eval('.wb .metrics-page input[type=date]', n => n.length) === 2);
    await page.click('[data-dot="9"]'); await page.waitForTimeout(300);
    for (let i = 0; i < 40; i++) await page.keyboard.press('Tab');
    check('Tab stays inside the settings dialog', await page.evaluate(() => !!document.activeElement.closest('.wb .settings-dialog')));
  } catch (error) { check('light interactions', false, String(error).slice(0, 400)); }
  await page.close();
}
// review-01 的边界：停在离顶部几像素时往上滚、键盘、焦点在演示里时按方向键、在演示窗口上滚动、触摸。
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on('pageerror', e => report.errors.push('edge: ' + e.message));
  await page.goto('http://127.0.0.1:8765/'); await page.waitForTimeout(500);
  const state = () => page.evaluate(() => ({ tourTop: Math.round(document.querySelector('.tour').getBoundingClientRect().top), step: document.querySelector('[data-tour-index]').textContent }));
  await page.mouse.move(150, 450); await page.mouse.wheel(0, 100); await page.waitForTimeout(1200);
  for (let i = 0; i < 4; i++) { await page.mouse.wheel(0, 100); await page.waitForTimeout(500); }
  let s = await state(); check('edge: at step 5 before drift', s.step === '5' && s.tourTop === 0, s);
  await page.evaluate(() => scrollBy(0, 5)); await page.waitForTimeout(100);
  await page.mouse.wheel(0, -100); await page.waitForTimeout(1200);
  s = await state(); check('edge: 5px drift then wheel up goes to step 4, not the last step', s.step === '4' && s.tourTop === 0, s);
  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press('ArrowDown'); await page.waitForTimeout(300);
  s = await state(); check('edge: ArrowDown moves one step', s.step === '5', s);
  await page.keyboard.press('ArrowUp'); await page.waitForTimeout(300);
  s = await state(); check('edge: ArrowUp moves one step back', s.step === '4', s);
  await page.focus('.wb .workspace-pages button'); await page.keyboard.press('ArrowDown'); await page.waitForTimeout(300);
  s = await state(); check('edge: arrow keys with focus inside the demo stay in the demo', s.step === '4', s);
  const tabs = await (await page.$('.wb .workspace-pages')).boundingBox();
  await page.mouse.move(tabs.x + 20, tabs.y + 5); await page.mouse.wheel(0, 100); await page.waitForTimeout(500);
  s = await state(); check('edge: wheel over the demo window header moves one step', s.step === '5' && s.tourTop === 0, s);
  await page.close();
}
{
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const page = await context.newPage();
  page.on('pageerror', e => report.errors.push('touch: ' + e.message));
  await page.goto('http://127.0.0.1:8765/'); await page.waitForTimeout(500);
  const cdp = await context.newCDPSession(page);
  const swipe = async (from, to) => {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 195, y: from }] });
    for (let i = 1; i <= 6; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 195, y: from + (to - from) * i / 6 }] });
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await page.waitForTimeout(1200);
  };
  const state = () => page.evaluate(() => ({ tourTop: Math.round(document.querySelector('.tour').getBoundingClientRect().top), step: document.querySelector('[data-tour-index]').textContent }));
  await swipe(700, 300);
  let s = await state(); check('touch: one swipe up from the intro lands on the tour at step 1', s.tourTop === 0 && s.step === '1', s);
  await swipe(600, 300);
  s = await state(); check('touch: swipe up on the tour moves one step', s.step === '2' && s.tourTop === 0, s);
  await swipe(300, 600);
  s = await state(); check('touch: swipe down moves one step back', s.step === '1' && s.tourTop === 0, s);
  await context.close();
}
for (const [w, h] of [[390, 844], [820, 1180]]) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, hasTouch: true, isMobile: w < 500 });
  page.on('pageerror', e => report.errors.push(w + ': ' + e.message));
  await page.goto('http://127.0.0.1:8765/'); await page.waitForTimeout(500);
  await page.screenshot({ path: `${out}/w${w}-intro.png` });
  await page.evaluate(() => scrollTo(0, document.querySelector('.tour').offsetTop)); await page.waitForTimeout(400);
  await page.screenshot({ path: `${out}/w${w}-tour.png` });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  check(`w${w} no horizontal page scroll`, overflow <= 0, overflow);
  await page.close();
}
await browser.close();
report.status = report.errors.length || report.checks.some(c => !c.ok) ? 'INCOMPLETE' : 'PASS';
fs.writeFileSync(out + '/report.json', JSON.stringify(report, null, 1));
console.log(JSON.stringify(report, null, 1));
