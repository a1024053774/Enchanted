import { createRequire } from 'node:module';
const require = createRequire('/Users/luckye/Documents/Code/a1024053774.github.io/package.json');
const { chromium } = require('playwright-core');
const [url, out] = process.argv.slice(2); const fs = await import('node:fs'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
for (const [name, w, h, scheme] of [['desk-light',1440,900,'light'],['desk-dark',1440,900,'dark'],['phone-light',390,844,'light']]) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, colorScheme: scheme, deviceScaleFactor: 1 });
  await page.goto(url); await page.waitForTimeout(800);
  await page.screenshot({ path: `${out}/${name}-full.png`, fullPage: true });
  await page.screenshot({ path: `${out}/${name}-0.png` });
  if (w > 800) for (const i of [1,4,5,9]) { await page.evaluate(n => { const d = document.querySelectorAll('[data-tour-dots] button')[n-1]; d?.click(); }, i); await page.waitForTimeout(900); await page.screenshot({ path: `${out}/${name}-step${i}.png` }); }
  const ov = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); console.log(name, 'overflowX', ov);
  await page.close();
}
await browser.close();
