import {createRequire} from 'node:module';import {readFileSync} from 'node:fs';import {join} from 'node:path';
const fork='/Users/luckye/Documents/Code/synara',out='/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-064';
const root=JSON.parse(readFileSync(join(out,'server-final11-launch.json'),'utf8')).root;
const {chromium}=createRequire(join(fork,'apps/web/package.json'))('playwright');
const context=await chromium.launchPersistentContext(join(root,'browser-overview14'),{executablePath:'/Volumes/WD-Elements/dev-cache/synara/playwright-t063/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell',headless:true,viewport:{width:1600,height:1050}});
try{
 const page=context.pages()[0];await page.goto('http://localhost:8088/settings?section=role-permissions',{waitUntil:'domcontentloaded'});
 await page.getByRole('heading',{name:'角色权限',exact:true}).waitFor({timeout:60000});
 for(let i=0;i<10;i++){const notNow=page.getByRole('button',{name:'Not now',exact:true});if(await notNow.isVisible().catch(()=>false))await notNow.click();const skip=page.getByRole('button',{name:'Skip tour',exact:true});if(await skip.isVisible().catch(()=>false))await skip.click();await page.waitForTimeout(250)}
 await page.screenshot({path:join(out,'overview14.png'),fullPage:true});
 await page.getByRole('heading',{name:'最近变更',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:join(out,'audit14.png'),fullPage:true});
}finally{await context.close()}
