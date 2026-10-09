import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const {chromium}=createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright");
const out=process.argv[2];
const browser=await chromium.launch({executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless:true});
const page=await browser.newPage();
const events=[];
page.on("console",x=>{if(x.type()==="error")events.push({console:x.text()});});
page.on("pageerror",x=>events.push({pageerror:String(x)}));
page.on("response",r=>{if(r.url().includes(":5828"))events.push({response:r.url(),status:r.status()});});
page.on("websocket",ws=>{
 events.push({websocket:ws.url()});
 ws.on("framesent",f=>events.push({sent:String(f.payload).slice(0,1800)}));
 ws.on("framereceived",f=>events.push({received:String(f.payload).slice(0,1800)}));
 ws.on("socketerror",e=>events.push({socketerror:e}));
});
try {
 await page.goto("http://localhost:7788/a2a");
 for(let i=0;i<6;i++){
  await new Promise(r=>setTimeout(r,1000));
  events.push({text:await page.locator("body").innerText()});
  writeFileSync(out,JSON.stringify(events,null,2));
 }
}catch(error){events.push({failure:String(error)});writeFileSync(out,JSON.stringify(events,null,2));}
finally{await browser.close();}
