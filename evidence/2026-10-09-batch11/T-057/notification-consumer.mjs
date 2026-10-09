import { createRequire } from "node:module";
import { readFileSync,writeFileSync,existsSync } from "node:fs";
import { join } from "node:path";
const {chromium,expect}=createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json")("playwright/test");
const [out,root,label]=process.argv.slice(2);
if(existsSync(join(out,label+".json")))throw new Error("Evidence label exists");
const seed=JSON.parse(readFileSync(join(root,"seed.json"),"utf8"));
const origin=JSON.parse(readFileSync(join(root,"ready.json"),"utf8")).origin;
const browser=await chromium.launch({executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}});
const receipts=[];let failure,calls;
async function needs(index){const response=await page.request.post(origin+"/api/a2a",{data:{command:"disposition",task:"t057",issue:seed.issues[index].id,action:"needs-user"}});const result=await response.json();receipts.push(result);expect(result.ok).toBe(true);}
try{
 await page.goto("http://localhost:7968/a2a");
 await page.getByRole("main",{name:"任务窗口",exact:true}).waitFor({timeout:60000});
 await page.waitForTimeout(2000);
 await page.evaluate(()=>{
   window.t057Calls=[];
   window.desktopBridge={notifications:{isSupported:async()=>true,show:async input=>{window.t057Calls.push(input);return true;}}};
   Object.defineProperty(document,"visibilityState",{configurable:true,get:()=>"hidden"});
   Object.defineProperty(document,"hasFocus",{configurable:true,value:()=>false});
   document.dispatchEvent(new Event("visibilitychange"));
 });
 await needs(2);await needs(3);
 await page.waitForTimeout(4000);
 calls=await page.evaluate(()=>window.t057Calls);
 expect(calls).toHaveLength(1);
 expect(calls[0]).toMatchObject({title:"2 个问题等你决定",silent:true,suppressWhenForeground:true});
}catch(error){failure=String(error.stack??error);}
finally{writeFileSync(join(out,label+".json"),JSON.stringify({argv:process.argv.slice(1),failure,calls,receipts,
 limitation:"Real application, HTTP and query library; document foreground state and desktopBridge sink are controlled. This proves caller behavior, not native OS display or permission."},null,2)+"\n");await browser.close();}
if(failure)throw new Error(failure);
