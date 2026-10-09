import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
import { join } from "node:path";
const { chromium } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label, profile] = process.argv.slice(2);
const context = await chromium.launchPersistentContext(join(root, profile), {
  executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless:true,
  viewport:{width:1600,height:1050},reducedMotion:"reduce",colorScheme:"light",
});
const page = await context.newPage();
const records = [], errors = [];
page.on("pageerror", e => errors.push(String(e)));
try {
  await page.goto("http://localhost:7978/a2a");
  for (let i=0; i<6; i++) {
    await page.waitForTimeout(2000);
    records.push({ at:new Date().toISOString(), url:page.url(), text:await page.locator("body").innerText(),
      storage:await page.evaluate(() => Object.entries(localStorage).filter(([key]) => key.startsWith("synara:") && (key.includes("tour") || key.includes("onboarding") || key.includes("announcement")))) });
    await page.screenshot({path:join(out,label+"-"+i+".png")});
  }
} finally {
  writeFileSync(join(out,label+".json"),JSON.stringify({argv:process.argv.slice(1),records,errors},null,2)+"\n",{flag:"wx"});
  await context.close();
}
