import { createRequire } from "node:module";
import { writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
const { chromium } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label, profile, cache = "normal"] = process.argv.slice(2);
if (existsSync(join(out,label+".json"))) throw new Error("Evidence exists");
const record = { argv:process.argv.slice(1), cache, snapshots:[], errors:[], responses:{}, sockets:[], modelCalls:0 };
const context = await chromium.launchPersistentContext(join(root,profile), {
  executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless:true,
  viewport:{width:1600,height:1050}, reducedMotion:"reduce", colorScheme:"light",
});
record.pagesAtLaunch = context.pages().map(p => p.url());
const page = cache === "single-page" ? context.pages()[0] : await context.newPage();
const cdp = await context.newCDPSession(page);
await cdp.send("Network.enable");
if (cache === "disabled") await cdp.send("Network.setCacheDisabled", { cacheDisabled:true });
cdp.on("Network.responseReceived", event => { const key = `${event.response.status}-${event.response.fromDiskCache ? "disk" : "network"}`; record.responses[key] = (record.responses[key] ?? 0)+1; });
page.on("pageerror", error => record.errors.push(String(error)));
page.on("crash", () => record.errors.push("renderer crash"));
context.on("close", () => record.closedAt = new Date().toISOString());
page.on("websocket", socket => record.sockets.push(new URL(socket.url()).origin));
const start = Date.now();
try {
  await page.goto("http://localhost:8078/a2a", { waitUntil:"domcontentloaded" });
  const main = page.getByRole("main", {name:"任务窗口",exact:true});
  for (let i=0;i<12;i++) {
    try { await main.waitFor({timeout:5000}); } catch (error) { record.errors.push(String(error)); }
    const snap = {elapsedMs:Date.now()-start, mainVisible:await main.isVisible(), boot:await page.locator(".app-boot-splash").count(), text:(await page.locator("body").innerText()).slice(0,500), responses:{...record.responses}};
    record.snapshots.push(snap);
    writeFileSync(join(out,label+"-live.json"),JSON.stringify(record,null,2)+"\n");
    if (i===1 || snap.mainVisible) await page.screenshot({path:join(out,`${label}-${i}.png`)});
    if (snap.mainVisible) { record.pass = true; break; }
  }
} catch (error) { record.failure=String(error.stack ?? error); }
finally {
  await context.close();
  writeFileSync(join(out,label+".json"),JSON.stringify(record,null,2)+"\n",{flag:"wx"});
}
console.log(JSON.stringify(record,null,2));
if (!record.pass) process.exitCode=1;
