import { createRequire } from "node:module";
import { writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
const { chromium } = createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out, root, label, mode = "fresh"] = process.argv.slice(2);
if (existsSync(join(out, label + ".json"))) throw new Error("Evidence label exists");
const events = [], frames = [];
const options = { executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless:true };
let browser, context, page, failure, body;
function clean(value) { return value.replace(/\?token=[^\s"']+/g,"?token=[redacted]").replace(/[^\s"'<>]+@[^\s"'<>]+/g,"[email]"); }
function path(url) { const parsed = new URL(url); return parsed.origin + parsed.pathname; }
function frame(direction, payload) {
  try { const value=JSON.parse(String(payload)); frames.push({ direction, tag:value._tag, rpc:value.tag, id:value.id, requestId:value.requestId, exit:value.exit?._tag,
    error:value.exit?._tag==="Failure" ? clean(JSON.stringify(value.exit.cause).slice(0,500)) : undefined }); }
  catch { frames.push({ direction, parseable:false }); }
}
try {
  if (mode === "persistent") context = await chromium.launchPersistentContext(join(root,"browser-profile"), { ...options,viewport:{width:1600,height:1000} });
  else { browser = await chromium.launch(options); context=await browser.newContext({viewport:{width:1600,height:1000}}); }
  context.on("close",()=>events.push({type:"context-close",time:Date.now()}));
  page = await context.newPage();
  page.on("close",()=>events.push({type:"page-close",time:Date.now()}));
  page.on("console",message=>{if(["error","warning"].includes(message.type()))events.push({type:message.type(),text:clean(message.text())});});
  page.on("pageerror",error=>events.push({type:"pageerror",text:clean(String(error))}));
  page.on("requestfailed",request=>events.push({type:"requestfailed",path:path(request.url()),error:request.failure()}));
  page.on("response",response=>{if(response.status()>=400)events.push({type:"http",status:response.status(),path:path(response.url())});});
  page.on("websocket",socket=>{events.push({type:"ws",path:path(socket.url())});socket.on("framesent",event=>frame("send",event.payload));socket.on("framereceived",event=>frame("receive",event.payload));socket.on("close",()=>events.push({type:"ws-close"}));});
  await page.goto("http://localhost:7968/a2a");
  await page.waitForTimeout(15000);
  body=await page.locator("body").innerText();
  await page.screenshot({path:join(out,label+".png")});
} catch (error) { failure=clean(String(error)); }
finally {
  writeFileSync(join(out,label+".json"),JSON.stringify({argv:process.argv.slice(1),mode,body,failure,events,frames},null,2)+"\n");
  await context?.close();await browser?.close();
}
console.log(JSON.stringify({label,failure,body:body?.slice(0,300),events:events.length,frames:frames.length}));
