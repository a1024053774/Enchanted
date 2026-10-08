import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara-t038/apps/web/package.json")("playwright/test");
const root = dirname(fileURLToPath(import.meta.url)), [variant,label] = process.argv.slice(2);
if (!["baseline","candidate"].includes(variant) || existsSync(join(root,label+".json"))) throw new Error("Variant and new evidence label required");
const checkout="/Users/luckye/Documents/Code/"+(variant==="baseline"?"synara-t038-baseline":"synara-t038");
const browser=await chromium.launch({executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless:false});
const page=await browser.newPage({viewport:{width:1600,height:1000},reducedMotion:"reduce"});
let phase="root",failure; const messages=[],responses=[],steps=[];
page.on("console",m=>{if(["error","warning"].includes(m.type()))messages.push({phase,type:m.type(),text:m.text()});});
page.on("pageerror",e=>messages.push({phase,type:"pageerror",text:String(e)}));
page.on("response",r=>{if(r.status()>=400)responses.push({phase,status:r.status(),url:r.url()});});
try {
 await page.goto("http://localhost:7771/");
 await expect(page.getByText("R6 路由对照空会话",{exact:true})).toBeVisible({timeout:45000});
 await page.screenshot({path:join(root,label+"-root.png"),fullPage:true});
 phase="dismiss-announcements";
 const notNow=page.getByRole("button",{name:"Not now",exact:true});
 if(await notNow.isVisible())await notNow.click();
 await page.keyboard.press("Escape");
 const skip=page.getByRole("button",{name:"Skip tour",exact:true});
 try {await skip.waitFor({state:"visible",timeout:5000});await skip.click();}catch(e){steps.push({phase,optionalTour:String(e)});}
 await page.keyboard.press("Escape");
 steps.push({phase,dialogs:await page.getByRole("dialog").count(),links:await page.getByRole("link").evaluateAll(nodes=>nodes.map(n=>({text:n.textContent,href:n.getAttribute("href")})))});
 phase="common-thread-hover";
 const thread=page.getByText("R6 路由对照空会话",{exact:true}).first();await thread.hover({timeout:10000});await page.waitForTimeout(1200);
 phase="common-thread-navigation";await thread.click({timeout:10000});
 await expect(page).toHaveURL(/\/t038-r6-thread/,{timeout:15000});await page.waitForTimeout(1200);
 await page.screenshot({path:join(root,label+"-thread.png"),fullPage:true});
 if(variant==="candidate"){
  phase="task-entry-hover";const link=page.getByRole("link",{name:"任务窗口",exact:true});await link.hover({timeout:10000});await page.waitForTimeout(1500);
  phase="task-entry-navigation";await link.click({timeout:10000});await expect(page.getByRole("main",{name:"任务窗口",exact:true})).toBeVisible({timeout:15000});await page.waitForTimeout(1200);
  await page.screenshot({path:join(root,label+"-task.png"),fullPage:true});
 }
}catch(e){failure=String(e.stack??e);}
finally{
 let captureFailure,text;
 try{await page.screenshot({path:join(root,label+"-final.png"),fullPage:true});text=await page.locator("body").innerText();}catch(e){captureFailure=String(e);}
 writeFileSync(join(root,label+".json"),JSON.stringify({argv:process.argv.slice(1),variant,candidate:execFileSync("git",["rev-parse","HEAD"],{cwd:checkout,encoding:"utf8"}).trim(),phase,failure,captureFailure,messages,responses,steps,text,surface:"fresh owned dev Chrome; real server; no model turn or response interception"},null,2)+"\n","utf8");
 await browser.close();
}
if(failure)process.exitCode=1;
