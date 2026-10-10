import {createRequire} from 'node:module';import {readFileSync,writeFileSync} from 'node:fs';import {join} from 'node:path';
const fork='/Users/luckye/Documents/Code/synara',out='/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-065',root='/Volumes/WD-Elements/dev-cache/synara/instances/t065-toolbar-red01';
const {chromium}=createRequire(join(fork,'apps/web/package.json'))('playwright');
const seed=JSON.parse(readFileSync(join(root,'seed.json'),'utf8')),web=JSON.parse(readFileSync(join(root,'web-ready.json'),'utf8')).origin;
const context=await chromium.launchPersistentContext(join(root,'browser-toolbar-green01-ui'),{executablePath:'/Volumes/WD-Elements/dev-cache/synara/playwright-t063/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell',headless:true,viewport:{width:1600,height:1050}});
try{
 const page=context.pages()[0];await page.goto(web+'/a2a',{waitUntil:'domcontentloaded'});const main=page.getByRole('main',{name:'任务窗口',exact:true});await main.waitFor({timeout:60000});await main.getByRole('button',{name:'T057 问题面板',exact:true}).click();
 const pane=main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`);await pane.getByTestId('empty-landing-heading').waitFor({state:'attached'});
 const dismiss=pane.getByRole('button',{name:'Dismiss provider status'});if(await dismiss.count())await dismiss.click();await pane.evaluate(n=>{n.style.flex='0 0 400px';n.style.minWidth='0';});
 const record=await pane.evaluate(pane=>{
 const editor=pane.querySelector('[data-empty-landing-composer-block]'),bar=pane.querySelector('[data-empty-landing-controls]');
 const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};
 const detail=n=>{const s=getComputedStyle(n);return {tag:n.tagName,text:n.textContent,class:n.className,rect:rect(n),clientWidth:n.clientWidth,scrollWidth:n.scrollWidth,clientHeight:n.clientHeight,scrollHeight:n.scrollHeight,clip:s.clip,clipPath:s.clipPath,position:s.position,overflow:s.overflow,display:s.display};};
 return {clipped:[editor,...[...editor.querySelectorAll('span')].filter(n=>n.childElementCount===0)].filter(n=>n.scrollWidth>n.clientWidth+1||n.scrollHeight>n.clientHeight+1).map(detail),toolbar:detail(bar),buttons:[...bar.querySelectorAll('button')].map(detail)};
 });writeFileSync(join(out,'toolbar-diagnostic01.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(record,null,2));
}finally{await context.close();}
