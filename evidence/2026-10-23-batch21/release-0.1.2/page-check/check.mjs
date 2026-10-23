import { createRequire } from 'node:module';
const require = createRequire('/Users/luckye/Documents/Code/a1024053774.github.io/package.json');
const { chromium } = require('playwright-core');
const out = process.argv[2]; const fs = await import('node:fs'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.HOME + '/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' });
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
  } catch (error) { check('light interactions', false, String(error).slice(0, 400)); }
  await page.close();
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
