import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync, renameSync } from "node:fs";
import { join } from "node:path";
const { chromium, expect } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label = "panel-send", mode = "send"] = process.argv.slice(2);
if (existsSync(join(out,label+".json"))) throw new Error("Evidence label exists");
const attempt=JSON.parse(readFileSync(join(out,"real-dispatch.json"),"utf8")).attempt;
const browser=await chromium.launch({executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless:true});
const context=await browser.newContext({viewport:{width:1600,height:1050},reducedMotion:"reduce",colorScheme:"light"});
const page=await context.newPage();
const diagnostics=[];
page.on("pageerror",error=>diagnostics.push({type:"pageerror",message:String(error)}));
page.on("requestfailed",request=>diagnostics.push({type:"requestfailed",url:request.url(),error:request.failure()}));
let failure,structure,response;
try {
  await page.goto("http://localhost:7788/a2a");
  await page.getByRole("main",{name:"任务窗口",exact:true}).waitFor({timeout:60000});
  await expect(page.getByText("Loading projects...",{exact:true})).not.toBeVisible({timeout:60000});
  for (const name of ["Not now"]) {
    const button=page.getByRole("button",{name,exact:true});
    if (await button.isVisible()) await button.click();
  }
  await page.getByRole("button",{name:"Skip tour",exact:true}).click({timeout:20000});
  const main=page.getByRole("main",{name:"任务窗口",exact:true});
  writeFileSync(join(out,label+"-initial.txt"),await page.locator("body").innerText());
  await page.screenshot({path:join(out,label+"-initial.png")});
  await main.getByRole("button",{name:"T055 问题答复",exact:true}).click({timeout:30000});
  const pane=main.locator(`[data-a2a-pane='${attempt.thread_id}']`);
  const panel=pane.getByRole("complementary",{name:"问题上报",exact:true});
  await expect(panel.locator("article")).toHaveCount(mode === "send" ? 1 : 2,{timeout:30000});
  const first=panel.locator("article").first();
  await expect(first.getByRole("heading",{name:"问题 1：oracle 漏了空页",exact:true})).toBeVisible();
  await expect(first.getByText("分页夹具没有覆盖最后一页为空的情况。",{exact:true})).toBeVisible();
  await expect(first.getByText("blocking",{exact:true})).toBeVisible();
  await expect(first.getByRole("button",{name:"发送答复",exact:true})).toBeVisible();
  structure=await panel.locator("article").evaluateAll(nodes=>nodes.map(n=>({heading:n.querySelector("h5")?.textContent,text:n.textContent})));
  await page.screenshot({path:join(out,label+"-before-send.png")});
  if (mode === "send") {
  // Requirement-written input and expected text, independent of production helpers.
  await first.getByRole("textbox",{name:"答复问题 1",exact:true}).fill("补上，并在 RESULTS 里写明。   \n");
  const sent=page.waitForResponse(r=>r.url().endsWith("/api/a2a") && r.request().method()==="POST" && r.request().postDataJSON()?.command==="answer_issue");
  await first.getByRole("button",{name:"发送答复",exact:true}).click();
  response=await (await sent).json();
  expect(response.ok).toBe(true);
  writeFileSync(join(out,label+"-answer-receipt.json.part"),JSON.stringify(response));
  renameSync(join(out,label+"-answer-receipt.json.part"),join(out,label+"-answer-receipt.json"));
  await expect(first.getByText("已送达",{exact:true})).toBeVisible({timeout:30000});
  await expect(first.getByText("用户答复：补上，并在 RESULTS 里写明。",{exact:true})).toBeVisible();
  await expect(panel.locator("article")).toHaveCount(3,{timeout:30000});
  const headings=await panel.locator("h5").allTextContents();
  expect(headings.map(x=>x.trim())).toEqual(["问题 1：oracle 漏了空页","问题 3：独立阻塞哨兵","问题 2：独立哨兵：引号 \" 与换行"]);
  structure=await panel.locator("article").evaluateAll(nodes=>nodes.map(n=>({heading:n.querySelector("h5")?.textContent,text:n.textContent})));
  await page.screenshot({path:join(out,label+"-after-send.png")});
  }
} catch (error) {
  failure=String(error.stack??error);
  if (!page.isClosed()) await page.screenshot({path:join(out,label+"-failure.png")});
} finally {
  writeFileSync(join(out,label+".json"),JSON.stringify({argv:process.argv.slice(1),failure,structure,response,diagnostics,pageClosed:page.isClosed(),browserConnected:browser.isConnected(),text:page.isClosed()?"":await page.locator("body").innerText()},null,2)+"\n");
  await browser.close();
}
if (failure) throw new Error(failure);
