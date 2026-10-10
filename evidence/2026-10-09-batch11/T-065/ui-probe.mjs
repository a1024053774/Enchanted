import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
const fork = '/Users/luckye/Documents/Code/synara';
const { chromium } = createRequire(join(fork, 'apps/web/package.json'))('playwright');
const [out, root, label, mode = 'matrix'] = process.argv.slice(2);
if (existsSync(join(out, label+'.json'))) throw Error('Evidence label exists');
const seed = JSON.parse(readFileSync(join(root,'seed.json'),'utf8'));
const web = JSON.parse(readFileSync(join(root,'web-ready.json'),'utf8')).origin;
const binary = '/Volumes/WD-Elements/dev-cache/synara/playwright-t063/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const records=[], failures=[];
const revision = execFileSync('git',['-C',fork,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const diff = execFileSync('git',['-C',fork,'diff','HEAD'],{encoding:'utf8'});
const context = await chromium.launchPersistentContext(join(root,'browser-'+label), { executablePath:binary, headless:true, viewport:{width:1280,height:900}, reducedMotion:'reduce', colorScheme:'light' });
const page = context.pages()[0];
page.on('pageerror',error=>failures.push('pageerror: '+error));
let pane, panel;
async function geometry(stage) {
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const result = await pane.evaluate(pane=>{
    const heading=pane.querySelector('[data-testid="empty-landing-heading"]');
    const logo=pane.querySelector('svg[aria-label="Synara logo"]');
    const banner=pane.querySelector('[data-testid="project-import-landing-banner"]');
    const composer=pane.querySelector('[data-empty-landing-composer-block="true"]');
    const landing=heading.closest('.chat-pane-enter');
    const rect=n=>{const r=n.getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height};};
    const within=(r,p)=>r.left>=p.left-.5 && r.top>=p.top-.5 && r.right<=p.right+.5 && r.bottom<=p.bottom+.5;
    const bounds=rect(landing), viewport={left:0,top:0,right:innerWidth,bottom:innerHeight};
    const parts=Object.fromEntries(Object.entries({banner,logo,heading,composer}).map(([key,node])=>{
      const r=rect(node), visible=r.width>0 && r.height>0 && getComputedStyle(node).visibility!=='hidden';
      const texts=[...node.querySelectorAll('span')].filter(n=>n.childElementCount===0);
      return [key,{rect:r,visible,fullyVisible:!visible || (within(r,bounds)&&within(r,viewport)),text:node.textContent,
        clipped:visible && [node,...texts].some(n=>n.scrollWidth>n.clientWidth+1 || n.scrollHeight>n.clientHeight+1)}];
    }));
    const overlaps={};const names=Object.keys(parts);
    for(let i=0;i<names.length;i++)for(let j=i+1;j<names.length;j++){
      const a=parts[names[i]],b=parts[names[j]],r=a.rect,s=b.rect;
      overlaps[names[i]+'-'+names[j]]=a.visible&&b.visible ? Math.max(0,Math.min(r.right,s.right)-Math.max(r.left,s.left))*Math.max(0,Math.min(r.bottom,s.bottom)-Math.max(r.top,s.top)):0;
    }
    const editor=composer.querySelector('[contenteditable="true"]');
    const e=editor && rect(editor);
    const hit=e && document.elementFromPoint(e.left+Math.min(20,e.width/2),e.top+Math.min(20,e.height/2));
    const issueList=pane.querySelector('[data-a2a-issue-list]');
    return {parts,overlaps,landing:bounds,scrollTop:landing.scrollTop,scrollHeight:landing.scrollHeight,clientHeight:landing.clientHeight,
      editorHit:!!hit && editor.contains(hit),viewport:{width:innerWidth,height:innerHeight},dpr:devicePixelRatio,
      issues:issueList?{clientHeight:issueList.clientHeight,scrollHeight:issueList.scrollHeight,scrollTop:issueList.scrollTop,count:issueList.querySelectorAll('article').length}:null};
  });
  result.stage=stage;records.push(result);
  if(!result.parts.composer.visible || !result.parts.composer.fullyVisible) failures.push(stage+': composer outside first screen');
  if(result.scrollTop!==0)failures.push(stage+': landing scrolled');
  if(!result.editorHit)failures.push(stage+': editor cannot be clicked in place');
  if(Object.values(result.overlaps).some(x=>x>0))failures.push(stage+': elements overlap');
  for(const [name,p] of Object.entries(result.parts))if(name!=='composer' && p.visible && (!p.fullyVisible||p.clipped))failures.push(stage+': '+name+' text/shape is clipped');
  // Click by coordinate so Playwright cannot scroll an off-screen input into view.
  if(result.editorHit){
    const editor=pane.locator('[data-empty-landing-composer-block="true"] [contenteditable="true"]').first();
    const b=await editor.boundingBox();await page.mouse.click(b.x+20,b.y+20);
    await page.keyboard.type('T065 input sentinel');
    result.typed=await editor.innerText();
    if(!result.typed.includes('T065 input sentinel'))failures.push(stage+': typing failed');
    await page.keyboard.press('Meta+A');await page.keyboard.press('Backspace');
    result.scrollAfterInput=await pane.locator('.chat-pane-enter').evaluate(n=>n.scrollTop);
    if(result.scrollAfterInput!==0)failures.push(stage+': input caused scroll');
  }
  await page.screenshot({path:join(out,label+'-'+stage+'.png')});
}
async function toggle(open){
  if(open !== (mode !== 'no-panel')) throw Error('Panel state must come from fixture data');
}
try{
  await page.goto(web+'/a2a',{waitUntil:'domcontentloaded',timeout:60000});
  const main=page.getByRole('main',{name:'任务窗口',exact:true});await main.waitFor({timeout:60000});
  await page.getByRole('button',{name:'Not now',exact:true}).click({timeout:30000});
  await page.getByRole('button',{name:'Skip tour',exact:true}).click({timeout:30000});
  await main.getByRole('button',{name:'T057 问题面板',exact:true}).click();
  pane=main.locator(`[data-a2a-pane='${seed.dispatched.attempt.thread_id}']`);
  panel=pane.getByRole('complementary',{name:'问题上报',exact:true});
  if(mode!=='no-panel') await panel.locator('article').nth(2).waitFor({timeout:30000});
  await pane.getByTestId('empty-landing-heading').waitFor({state:'attached',timeout:30000});
  await pane.getByRole('button',{name:'Dismiss provider status'}).click();
  await page.getByText('See running tasks, completed work, and anything that needs your attention.',{exact:true}).waitFor({state:'hidden',timeout:15000});
  await geometry('1280x900-'+(mode==='no-panel'?'closed':'open'));
  if(mode!=='red'){
    for(const size of [{width:1600,height:1050},{width:1280,height:900},{width:1280,height:720}]){
      await page.setViewportSize(size);
      for(const open of [mode!=='no-panel']){await toggle(open);await geometry(`${size.width}x${size.height}-${open?'open':'closed'}`);}
    }
    // Longer Chinese text is an external presentation input; no locale switch exists.
    await pane.getByTestId('project-import-landing-banner').evaluate(n=>{
      n.lastElementChild.firstElementChild.textContent='导入你在 Claude Code 和 Codex 中的项目、历史对话与开发工作记录，以便继续当前的协作';
      n.lastElementChild.lastElementChild.textContent='将已有项目和历史记录带到 Synara 中继续处理。';
    });
    await pane.getByTestId('empty-landing-heading').evaluate(n=>n.textContent='我们接下来要在这个名称较长的协作项目中完成哪一项工作？');
    for(const size of [{width:1600,height:1050},{width:1280,height:900},{width:1280,height:720},{width:1600,height:1050}]){
      await page.setViewportSize(size);for(const open of [mode!=='no-panel']){await toggle(open);await geometry(`中文-${size.width}x${size.height}-${open?'open':'closed'}-${records.length}`);}
    }
    // Constrain the actual pane width, as a neighbouring agent column would.
    await pane.evaluate(n=>{n.style.flex='0 0 400px';n.style.minWidth='0';});
    await geometry('narrow-pane-400-open');
    await pane.evaluate(n=>{n.style.removeProperty('flex');n.style.removeProperty('min-width');});
    if(mode!=='no-panel'){
      const list=panel.locator('[data-a2a-issue-list]');
      await list.evaluate(n=>n.scrollTop=n.scrollHeight);await geometry('many-issues-panel-scrolled');
    }
    // 125% browser zoom uses a 0.8 CSS viewport and DPR 1.25; Ctrl/Cmd zoom is
    // not implemented by Headless Shell. This is browser device-metrics zoom.
    const cdp=await context.newCDPSession(page);
    for(const open of [mode!=='no-panel']){
      await toggle(open);
      await cdp.send('Emulation.setDeviceMetricsOverride',{width:1024,height:576,deviceScaleFactor:1.25,mobile:false});
      await geometry(`125percent-1280x720-${open?'open':'closed'}`);
      await cdp.send('Emulation.clearDeviceMetricsOverride');
    }
  }
}catch(error){failures.push(String(error.stack??error));await page.screenshot({path:join(out,label+'-failure.png')});}
finally{await context.close();writeFileSync(join(out,label+'.json'),JSON.stringify({argv:process.argv.slice(1),revision,diff,binary,source:mode==='red'?'e94a0efc3':'working tree',modelCalls:0,records,failures},null,2)+'\n',{flag:'wx'});}
console.log(JSON.stringify({label,cases:records.length,failures},null,2));if(failures.length)process.exitCode=1;
