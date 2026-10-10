import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const {chromium} = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out,root,label] = process.argv.slice(2);
const seed=JSON.parse(readFileSync(join(root,"seed.json"),"utf8"));
const record={argv:process.argv.slice(1),errors:[],sockets:[],modelCalls:0};
const context=await chromium.launchPersistentContext(join(root,"browser-green03"),{
  executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless:true,
  viewport:{width:1600,height:1050},reducedMotion:"reduce",colorScheme:"light",
});
const page=context.pages()[0];
const cdp=await context.newCDPSession(page);
await cdp.send("Network.enable");
await cdp.send("Network.setCacheDisabled",{cacheDisabled:true});
page.on("pageerror",e=>record.errors.push(String(e)));
page.on("websocket",ws=>{ const item={origin:new URL(ws.url()).origin,at:Date.now()};record.sockets.push(item);ws.on("socketerror",e=>item.error=String(e));ws.on("close",()=>item.closed=Date.now()); });
const start=Date.now();
try {
  await page.goto("http://localhost:8078/a2a",{waitUntil:"domcontentloaded",timeout:60000});
  await page.waitForFunction(()=>!document.querySelector(".app-boot-splash"),{},{timeout:60000});
  await page.waitForTimeout(7500);
  record.beforeRestart={elapsedMs:Date.now()-start,text:(await page.locator("body").innerText()).slice(0,700)};
  await page.screenshot({path:join(out,label+"-not-ready.png")});
  writeFileSync(join(out,label+"-waiting.json"),JSON.stringify(record,null,2)+"\n",{flag:"wx"});
  const pane=page.getByRole("main",{name:"任务窗口",exact:true}).locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`);
  await pane.getByRole("heading",{name:"问题 1：oracle 漏了空页",exact:true}).waitFor({timeout:60000});
  await pane.getByTestId("empty-landing-heading").waitFor({timeout:30000});
  record.elapsedMs=Date.now()-start;
  record.articleCount=await pane.locator("article").count();
  record.projectHeading=await pane.getByTestId("empty-landing-heading").innerText();
  record.pass=record.articleCount===3 && record.projectHeading.includes("T063 隔离项目");
  await page.screenshot({path:join(out,label+"-ready.png")});
} catch(e) {record.failure=String(e.stack??e);}
finally {await context.close();writeFileSync(join(out,label+".json"),JSON.stringify(record,null,2)+"\n",{flag:"wx"});}
console.log(JSON.stringify(record,null,2));
if(!record.pass) process.exitCode=1;
