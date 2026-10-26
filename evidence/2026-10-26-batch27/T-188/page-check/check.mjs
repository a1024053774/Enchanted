// T-182 page checks. Usage: node check.mjs <out-dir>; PAGE_CHECK_URL picks the page (default the local server on 8765).
// Part 1 ports the 16 checks of evidence/2026-10-23-batch24/T-173/page-check/check.mjs that still have an object after
// T-182 rev 2 split the single wheel-stepped tour into per-feature demos. The 35 wheel/touch/drift checks of that tour are
// retired by the user's decision (inbox 20261025T045006Z-ideation-answer-001, option A); the list is in RESULTS.md.
// Part 2 adds the T-182 checks. Expected values come from the ticket (T-182 rev 3) and the user's words quoted there.
import { createRequire } from 'node:module';
const require = createRequire('/Users/luckye/Documents/Code/a1024053774.github.io/package.json');
const { chromium } = require('playwright-core');
const out = process.argv[2]; const fs = await import('node:fs'); fs.mkdirSync(out, { recursive: true });
const URL = process.env.PAGE_CHECK_URL ?? 'http://127.0.0.1:8765/';
const browser = await chromium.launch({ executablePath: process.env.PAGE_CHECK_CHROME ?? (process.env.HOME + '/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing') });
const report = { url: URL, errors: [], checks: [] };
const check = (name, ok, detail) => { report.checks.push({ name, ok: !!ok, detail }); };
async function open(options = {}, label = 'page') {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, ...options });
  const page = await context.newPage();
  page.on('pageerror', e => report.errors.push(label + ': ' + e.message));
  page.on('console', m => { if (m.type() === 'error') report.errors.push(label + ' console: ' + m.text()); });
  await page.goto(URL); await page.waitForTimeout(700);
  return { context, page };
}
const toShow = async (page, key) => { await page.locator(`[data-show="${key}"]`).scrollIntoViewIfNeeded(); await page.waitForTimeout(600); };
// A missing element in one block is recorded as that block's failure and the run goes on (a red run reports every block).
const guard = async (name, body) => { try { await body(); } catch (error) { check(name + ' (block failed)', false, String(error).slice(0, 300)); } };
const step = async (page, show, n) => { // click next/prev until step n (1-based) of that show
  for (let i = 0; i < 6; i++) {
    const at = Number(await page.$eval(`[data-show="${show}"] [data-show-index]`, e => e.textContent));
    if (at === n) return;
    await page.click(`[data-show="${show}"] [data-show-${at < n ? 'next' : 'prev'}]`); await page.waitForTimeout(350);
  }
};

// ---------- Part 1: ported T-173 checks ----------
try {
  const { context, page } = await open({}, 'ported');
  await toShow(page, 'approve');
  const approve = await (await page.$('#wb-approve [data-fk="rr-approve"]')).boundingBox();
  const before = await page.$eval('#show-approve', n => n.getBoundingClientRect().top);
  await page.mouse.move(approve.x + approve.width / 2, approve.y + approve.height / 2); await page.mouse.down();
  const during = await page.$eval('#show-approve', n => n.getBoundingClientRect().top);
  await page.mouse.up(); await page.waitForTimeout(250);
  check('t182 a press in a feature demo does not move the page under the pointer', Math.abs(during - before) < 1, { before, during });
  const tree = await page.evaluate(() => [...document.querySelectorAll('#wb-approve [data-agent-launch="launch-c4e8"]')].map(n => n.dataset.agentLevel));
  check('approve puts executor under ideation (level 1)', tree.join() === '1', tree);
  await page.screenshot({ path: `${out}/light-role-approved.png` });
  await page.evaluate(() => scrollTo(0, 0)); await page.waitForTimeout(300);
  await step(page, 'views', 3); await page.waitForSelector('#wb-views .pane .terminal-scroll'); await page.waitForTimeout(900);
  const box = await (await page.$('#wb-views .pane .terminal-scroll')).boundingBox();
  await page.mouse.click(box.x + 40, box.y + 40, { button: 'right' }); await page.waitForTimeout(250);
  const menu = await page.$eval('#wb-views .pane-menu', n => n.getBoundingClientRect().toJSON());
  check('context menu opens at the pointer under scaling', Math.abs(menu.left - (box.x + 40)) < 6 && Math.abs(menu.top - (box.y + 40)) < 6, { menu, pointer: [box.x + 40, box.y + 40] });
  await page.screenshot({ path: `${out}/light-menu.png` });
  await page.keyboard.press('Escape');
  await toShow(page, 'records');
  check('records page has task and session filters (RecordsPage.tsx)', await page.$$eval('#wb-records .user-input-page .record-filter select', n => n.length) === 2);
  await step(page, 'records', 2);
  const area = await (await page.$('#wb-records .metrics-page')).boundingBox();
  await page.mouse.move(area.x + area.width / 2, area.y + area.height / 2);
  await page.mouse.wheel(0, 100); await page.waitForTimeout(500);
  const st = await page.$eval('#wb-records .metrics-page', n => [n.scrollTop, n.scrollHeight, n.clientHeight]);
  const recordsStep = await page.$eval('[data-show="records"] [data-show-index]', e => e.textContent);
  check('wheel over overflowing metrics page scrolls it, not the step', recordsStep === '2' && (st[0] > 0 || st[1] <= st[2] + 1), { recordsStep, st });
  const heads = await page.$$eval('#wb-records [data-metric="model-use"] table thead', n => n.map(h => h.textContent));
  check('metrics model use has summary and per-session tables (MetricsPage.tsx)', heads.length === 2 && heads[1].includes('角色'), heads);
  check('metrics page has a date range (MetricsPage.tsx)', await page.$$eval('#wb-records .metrics-page input[type=date]', n => n.length) === 2);
  await toShow(page, 'reflect'); await step(page, 'reflect', 2); await page.waitForTimeout(300);
  await page.focus('#wb-reflect .settings-dialog button');
  for (let i = 0; i < 40; i++) await page.keyboard.press('Tab');
  check('Tab stays inside the settings dialog', await page.evaluate(() => !!document.activeElement.closest('#wb-reflect .settings-dialog')));
  await context.close();
} catch (error) { check('ported interactions', false, String(error).slice(0, 400)); }
for (const [w, h] of [[390, 844], [820, 1180]]) { await guard(`w${w}`, async () => {
  const { context, page } = await open({ viewport: { width: w, height: h }, hasTouch: true, isMobile: w < 500 }, 'w' + w);
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  let worst = -1;
  for (let y = 0; y < H; y += h) { await page.evaluate(y => scrollTo(0, y), y); await page.waitForTimeout(250); worst = Math.max(worst, await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)); }
  check(`w${w} no horizontal page scroll`, worst <= 0, worst);
  await context.close();
}); }
for (const motion of ['no-preference', 'reduce']) { await guard('t173 ' + motion, async () => {
  const { context, page } = await open({ reducedMotion: motion }, 't173 ' + motion);
  const views = () => page.evaluate(() => ({ grid: [...document.querySelectorAll('#wb-views .project-task-tile')].map(n => n.dataset.taskTile).join(),
    panes: [...document.querySelectorAll('#wb-views .pane-slot .pane')].map(n => n.getAttribute('aria-label')).join(),
    gate: document.querySelector('#wb-views .gate strong')?.textContent ?? null }));
  const settled = { grid: '', panes: '受管 worker交互终端,独立审查交互终端,普通终端交互终端', gate: '已交付' };
  if (motion === 'no-preference') {
    await step(page, 'views', 2);
    const grid = await views();
    check('t173 views: project step shows the task grid', grid.grid === 'T-12,T-11,T-14,T-09' && grid.panes === '', grid);
    await step(page, 'views', 3); await page.waitForTimeout(900);
    const panes = await views();
    check('t173 views: task step shows T-11 worker, review and an ordinary terminal with the gate', JSON.stringify(panes) === JSON.stringify(settled), panes);
  } else {
    await step(page, 'views', 3);
    const first = await views();
    check('t173 reduced motion shows the settled task view at once', JSON.stringify(first) === JSON.stringify(settled), first);
    const moving = await page.evaluate(() => document.getAnimations().filter(a => a.playState === 'running' && !String(a.animationName ?? '').includes('spin')).map(a => a.animationName ?? a.transitionProperty ?? a.constructor.name));
    check('t173 reduced motion leaves nothing animating', moving.length === 0, moving);
  }
  await toShow(page, 'flow'); await page.waitForTimeout(400);
  check('t173 ' + motion + ' notification does not cover the flow demo', await page.$$eval('#wb-flow .app-notifications button', n => n.length) === 0);
  await context.close();
}); }
await guard('edges', async () => {
  const { context, page } = await open({}, 'edges');
  const edges = await page.evaluate(() => ['.wordmark', '.intro h1', '#show-flow .station-head h2', '#download h2'].map(q => Math.round(document.querySelector(q).getBoundingClientRect().left)));
  check('t173 header, hero, a left-side feature heading and download share one left edge', Math.max(...edges) - Math.min(...edges) <= 2, edges);
  await context.close();
});

// ---------- Part 2: T-182 ----------
for (const [w, h, scheme] of [[1440, 900, 'light'], [1440, 900, 'dark'], [390, 844, 'light'], [390, 844, 'dark']]) { await guard(`t182 ${w} ${scheme}`, async () => {
  const { context, page } = await open({ viewport: { width: w, height: h }, colorScheme: scheme, hasTouch: w < 500, isMobile: w < 500 }, `t182 ${w} ${scheme}`);
  const first = await page.evaluate(() => {
    const top = q => document.querySelector(q)?.getBoundingClientRect().top ?? null;
    return { vh: innerHeight, wbReady: document.querySelector('#wb-views')?.dataset.ready ?? null, wbTop: top('#wb-views'), h1: top('.intro h1'), download: top('.button.primary'),
      bg: getComputedStyle(document.body).backgroundImage };
  });
  check(`t182 ${w} ${scheme}: demo, title and download are on the first screen`, first.wbReady === 'true' && first.wbTop !== null && first.wbTop < first.vh - 80 && first.h1 < first.vh && first.download < first.vh, first);
  check(`t182 ${w} ${scheme}: background is layered, not one flat color`, (first.bg.match(/radial-gradient/g) ?? []).length >= 2, first.bg.slice(0, 120));
  const stroke = await page.$eval('[data-thread-line]', n => getComputedStyle(n).stroke);
  const rgb = (stroke.match(/[\d.]+/g) ?? []).slice(0, 3).map(Number);
  const isPurple = rgb.length === 3 && rgb[2] > rgb[0] && rgb[0] > rgb[1] && rgb[2] - rgb[1] > 60;
  check(`t182 ${w} ${scheme}: connecting line is purple`, isPurple, stroke);
  await page.screenshot({ path: `${out}/t182-${w}-${scheme}-first.png` });
  await context.close();
}); }
await guard('t182 guide', async () => {
  const { context, page } = await open({}, 't182 guide');
  const guide = () => page.evaluate(() => ({ index: document.querySelector('[data-show="views"] [data-show-index]').textContent,
    prevDisabled: document.querySelector('[data-show="views"] [data-show-prev]').disabled, next: document.querySelector('[data-show="views"] [data-show-next]').textContent.trim(),
    current: document.querySelector('[data-show="views"] .show-steps li.is-current h3')?.textContent, hint: (h => !h.hidden && !h.hasAttribute('data-dismissed'))(document.querySelector('[data-show-first]')),
    tiles: document.querySelectorAll('#wb-views .project-task-tile').length }));
  let g = await guide();
  check('t182 guide: first visit shows step 1 of 3, previous disabled, a start hint', g.index === '1' && g.prevDisabled && g.hint && g.next === '下一步', g);
  await page.click('[data-show="views"] [data-show-next]'); await page.waitForTimeout(400);
  g = await guide();
  check('t182 guide: next moves to step 2 and the demo shows the task grid; the hint goes away', g.index === '2' && !g.prevDisabled && !g.hint && g.tiles === 4, g);
  await page.focus('[data-show="views"] [data-show-next]'); await page.keyboard.press('ArrowRight'); await page.waitForTimeout(400);
  g = await guide();
  check('t182 guide: ArrowRight in the guide moves one step; the last step offers the next feature', g.index === '3' && g.next === '下一个功能', g);
  await page.keyboard.press('ArrowLeft'); await page.waitForTimeout(300);
  check('t182 guide: ArrowLeft moves one step back', (await guide()).index === '2');
  await page.focus('#wb-views .workspace-pages button'); await page.keyboard.press('ArrowRight'); await page.waitForTimeout(300);
  check('t182 guide: arrow keys inside the demo window stay in the window', (await guide()).index === '2');
  await step(page, 'views', 3);
  await page.click('[data-show="views"] [data-show-next]'); await page.waitForTimeout(1400);
  const top = await page.$eval('#show-approve', n => Math.round(n.getBoundingClientRect().top));
  const pad = await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0);
  check('t182 guide: next feature scrolls to the second demo (stops at the page scroll-padding)', Math.abs(top - pad) <= 4, { top, pad });
  await page.reload(); await page.waitForTimeout(700);
  check('t182 guide: the start hint stays away after a reload', await page.$eval('[data-show-first]', n => n.hidden || n.hasAttribute('data-dismissed')));
  await context.close();
});
await guard('t182 demos', async () => {
  const { context, page } = await open({}, 't182 demos');
  const keys = await page.$$eval('.show', n => n.map(s => s.dataset.show));
  for (const key of keys) await toShow(page, key);
  const ready = await page.$$eval('.show .wb', n => n.map(w => w.id + ':' + (w.dataset.ready ?? 'no')));
  check('t182 six separate feature demos, each with its own window', keys.join() === 'views,approve,flow,issues,records,reflect' && ready.every(r => r.endsWith(':true')), { keys, ready });
  await step(page, 'records', 2);
  const pages = await page.evaluate(() => ['approve', 'records'].map(k => document.querySelector(`#wb-${k} .workspace-pages [aria-current]`)?.textContent));
  check('t182 demos are independent: a step in one does not move another', pages[0] === '终端' && pages[1] === '指标', pages);
  await context.close();
});
for (const motion of ['no-preference', 'reduce']) { await guard('t182 thread ' + motion, async () => {
  const { context, page } = await open({ reducedMotion: motion }, 't182 thread ' + motion);
  const thread = () => page.evaluate(() => {
    const line = document.querySelector('[data-thread-line]'), total = line.getTotalLength(), offset = parseFloat(line.style.strokeDashoffset);
    const head = total - offset, main = document.querySelector('main').getBoundingClientRect();
    return { total: Math.round(total), drawn: Math.round(head), headY: Math.round(line.getPointAtLength(Math.max(0, head)).y + main.top), half: innerHeight / 2,
      lit: [...document.querySelectorAll('[data-station-star]')].map(s => s.classList.contains('is-lit') ? 1 : 0).join('') };
  });
  const top = await thread();
  if (motion === 'no-preference') {
    check('t182 thread at the top: only the first station is lit, the line is not drawn past half the screen', top.lit === '100000' && top.drawn < top.total && top.headY <= top.half + 2, top);
    await toShow(page, 'issues');
    const mid = await thread();
    check('t182 thread mid-page: head stays at or above half the screen; stations above are lit', mid.headY <= mid.half + 2 && /^1111/.test(mid.lit), mid);
    await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight)); await page.waitForTimeout(600);
    const end = await thread();
    check('t182 thread at the end: all six stations lit', end.lit === '111111', end);
    await page.screenshot({ path: `${out}/t182-thread-end.png` });
  } else {
    check('t182 reduced motion: the line is drawn whole and every station lit without scrolling', top.drawn >= top.total - 1 && top.lit === '111111', top);
    const moving = await page.evaluate(() => document.getAnimations().filter(a => a.playState === 'running' && !String(a.animationName ?? '').includes('spin')).length);
    check('t182 reduced motion: nothing on the page animates', moving === 0, moving);
  }
  await context.close();
}); }
await browser.close();
report.passed = report.checks.filter(c => c.ok).length; report.total = report.checks.length;
report.status = report.errors.length || report.checks.some(c => !c.ok) ? 'INCOMPLETE' : 'PASS';
fs.writeFileSync(out + '/report.json', JSON.stringify(report, null, 1));
console.log(JSON.stringify({ status: report.status, passed: report.passed, total: report.total, failed: report.checks.filter(c => !c.ok).map(c => c.name), errors: report.errors }, null, 1));
