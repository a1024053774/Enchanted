import { createRequire } from "node:module";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
const webRequire=createRequire("/Users/luckye/Documents/Code/synara/apps/web/package.json");
const desktopRequire=createRequire("/Users/luckye/Documents/Code/synara/apps/desktop/package.json");
const { _electron:electron, expect }=webRequire("playwright/test");
const [out, root, label]=process.argv.slice(2);
if(existsSync(join(out,label+".json")))throw new Error("Evidence label exists");
const fork="/Users/luckye/Documents/Code/synara";
const home=mkdtempSync("/tmp/a2a-t057-notification-");
for(const name of ["dev","userdata","os-home","codex-empty","claude-empty","electron-profile"])mkdirSync(join(home,name));
const { DEFAULT_SERVER_SETTINGS }=await import(join(fork,"packages/contracts/src/settings.ts"));
const settings=structuredClone(DEFAULT_SERVER_SETTINGS);settings.enableProviderUpdateChecks=false;
for(const provider of Object.values(settings.providers))provider.enabled=false;
writeFileSync(join(home,"dev/settings.json"),JSON.stringify({revision:0,migrationVersion:0,settings}));
writeFileSync(join(home,"userdata/settings.json"),JSON.stringify({revision:0,migrationVersion:0,settings}));
const seed=JSON.parse(readFileSync(join(root,"seed.json"),"utf8"));
const origin=JSON.parse(readFileSync(join(root,"ready.json"),"utf8")).origin;
const env={...process.env,HOME:join(home,"os-home"),CODEX_HOME:join(home,"codex-empty"),CLAUDE_CONFIG_DIR:join(home,"claude-empty"),
  SYNARA_HOME:home,SYNARA_DESKTOP_SMOKE_USER_DATA:join(home,"electron-profile"),SYNARA_SOURCE_DESKTOP_BUILD_MARKER:"synara-source-desktop-build-v2",
  SYNARA_DESKTOP_FLAVOR:"cua",SYNARA_DISABLE_AUTO_UPDATE:"1",VITE_DEV_SERVER_URL:"http://localhost:7968"};
delete env.ELECTRON_RUN_AS_NODE;
let app,page,failure,telemetry,background;
const receipts=[];
async function gate(issue,action){const response=await fetch(origin+"/api/a2a",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({command:"disposition",task:"t057",issue,action})});const result=await response.json();receipts.push({issue,action,result});expect(result.ok).toBe(true);}
try{
  app=await electron.launch({executablePath:desktopRequire("electron"),args:[join(fork,"apps/desktop/dist-electron/main.js")],cwd:join(fork,"apps/desktop"),env,timeout:45000});
  writeFileSync(join(out,label+"-pid.json"),JSON.stringify({pid:app.process().pid,home,entry:join(fork,"apps/desktop/dist-electron/main.js")}));
  await app.context().route("**/api/a2a**",async route=>{
    const original=new URL(route.request().url()),target=new URL(original.pathname,origin);
    for(const [key,value] of original.searchParams)if(key!=="token")target.searchParams.append(key,value);
    const headers={...route.request().headers()};delete headers.authorization;delete headers.cookie;
    await route.fulfill({response:await route.fetch({url:target.toString(),headers})});
  });
  page=await app.firstWindow();
  const selected=await app.browserWindow(page);
  await selected.evaluate(window=>{window.setBounds({width:1400,height:1000});window.show();window.focus();});
  await app.evaluate(({app})=>app.focus({steal:true}));
  await app.evaluate(({Notification,ipcMain})=>{
    globalThis.t057Telemetry={ipc:[],native:[],events:[]};
    const handler=ipcMain._invokeHandlers.get("desktop:notifications-show");
    ipcMain._invokeHandlers.set("desktop:notifications-show",async(event,input)=>{globalThis.t057Telemetry.ipc.push(input);return handler(event,input);});
    const show=Notification.prototype.show;
    Notification.prototype.show=function(){globalThis.t057Telemetry.native.push({title:this.title,body:this.body,silent:this.silent});
      this.once("show",()=>globalThis.t057Telemetry.events.push({type:"show",title:this.title}));
      this.once("failed",(_event,error)=>globalThis.t057Telemetry.events.push({type:"failed",error:String(error)}));
      return show.call(this);};
  });
  await page.goto("http://localhost:7968/a2a");
  await page.getByRole("main",{name:"任务窗口",exact:true}).waitFor({state:"attached",timeout:45000});
  await app.evaluate(({BrowserWindow,app})=>{const window=BrowserWindow.getAllWindows()[0];window.show();window.focus();app.focus({steal:true});});
  await expect.poll(()=>page.evaluate(()=>document.hasFocus())).toBe(true);
  await page.waitForTimeout(1500);
  await gate(seed.issues[1].id,"needs-user");
  await page.waitForTimeout(2500);
  expect((await app.evaluate(()=>globalThis.t057Telemetry)).ipc).toHaveLength(0);
  await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].minimize());
  await expect.poll(()=>page.evaluate(()=>document.visibilityState)).toBe("hidden");
  background=await page.evaluate(()=>({visibility:document.visibilityState,focus:document.hasFocus()}));
  await gate(seed.issues[2].id,"needs-user");await gate(seed.issues[3].id,"needs-user");
  await page.waitForTimeout(5000);
  telemetry=await app.evaluate(()=>globalThis.t057Telemetry);
  expect(telemetry.ipc).toHaveLength(1);
  expect(telemetry.ipc[0]).toMatchObject({title:"2 个问题等你决定",silent:true,suppressWhenForeground:true});
  expect(telemetry.native).toHaveLength(1);
  expect(telemetry.native[0].silent).toBe(true);
  expect(telemetry.events.some(event=>event.type==="show")).toBe(true);
}catch(error){failure=String(error.stack??error);if(app)telemetry=await app.evaluate(({BrowserWindow})=>({...globalThis.t057Telemetry,windows:BrowserWindow.getAllWindows().map(w=>({id:w.id,bounds:w.getBounds(),visible:w.isVisible(),minimized:w.isMinimized()}))})).catch(()=>undefined);}
finally{
  writeFileSync(join(out,label+".json"),JSON.stringify({argv:process.argv.slice(1),home,executable:desktopRequire("electron"),
    entry:join(fork,"apps/desktop/dist-electron/main.js"),failure,background,telemetry,receipts,
    boundary:"real existing Electron main/preload/IPC and native Notification; only a2a HTTP reads/writes routed to the isolated candidate server; no system permission granted"},null,2)+"\n");
  await app?.close();
}
if(failure)throw new Error(failure);
