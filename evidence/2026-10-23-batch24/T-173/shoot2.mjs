import { createRequire } from 'node:module';
const require = createRequire('/Users/luckye/Documents/Code/a1024053774.github.io/package.json');
const { chromium } = require('playwright-core');
const [url, out] = process.argv.slice(2); const fs = await import('node:fs'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
for (const [name, scheme, motion] of [['light','light','no-preference'],['dark','dark','no-preference'],['calm','light','reduce']]) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: scheme, reducedMotion: motion });
  await page.goto(url); await page.waitForTimeout(600);
  await page.click('[data-dot="3"]'); await page.waitForTimeout(motion === 'reduce' ? 300 : 2600);
  await page.screenshot({ path: `${out}/${name}-views.png` });
  console.log(name, await page.evaluate(() => [document.querySelectorAll('.wb .pane-slot').length, !!document.querySelector('.wb .project-task-grid'), document.querySelector('.wb .header-title h1').textContent]));
  await page.click('[data-dot="0"]'); await page.waitForTimeout(400); await page.click('[data-dot="4"]'); await page.waitForTimeout(900);
  await page.screenshot({ path: `${out}/${name}-flow.png` });
  await page.close();
}
await browser.close();
