import { createRequire } from 'node:module';
const require = createRequire('/Users/luckye/Documents/Code/a1024053774.github.io/package.json');
const { chromium } = require('playwright-core');
const [url, out] = process.argv.slice(2); const fs = await import('node:fs'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url); await page.waitForTimeout(600);
await page.click('[data-dot="4"]');
for (const t of [1000, 1600, 2400]) { await page.waitForTimeout(t); await page.screenshot({ path: `${out}/flow-${t}.png` }); }
console.log(await page.evaluate(() => [document.querySelector('.wb .flow-scroll').scrollLeft, document.querySelector('.wb .flow-page').scrollTop, scrollY]));
await browser.close();
