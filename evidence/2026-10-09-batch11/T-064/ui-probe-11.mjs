import {createRequire} from 'node:module';
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
const fork='/Users/luckye/Documents/Code/synara',out='/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-064';
const label=process.argv[2];
const outputLabel=process.argv[3]??label;
const launch=JSON.parse(readFileSync(join(out,'server-'+label+'-launch.json'),'utf8'));
const root=launch.root,web=JSON.parse(readFileSync(join(root,'web-ready.json'),'utf8')).origin;
const {chromium}=createRequire(join(fork,'apps/web/package.json'))('playwright');
const context=await chromium.launchPersistentContext(join(root,'browser-'+outputLabel),{executablePath:'/Volumes/WD-Elements/dev-cache/synara/playwright-t063/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell',headless:true,viewport:{width:1280,height:900}});
const page=context.pages()[0];const observations=[];
function assert(value,message){if(!value)throw new Error(message)}
try{
  await page.goto(web+'/settings?section=role-permissions',{waitUntil:'domcontentloaded'});
  await page.getByRole('heading',{name:'角色权限',exact:true}).waitFor({timeout:60000});
  for(let i=0;i<10;i++){
    const importer=page.getByRole('button',{name:'Not now',exact:true});
    if(await importer.isVisible().catch(()=>false))await importer.click();
    const tour=page.getByRole('button',{name:'Skip tour',exact:true});
    if(await tour.isVisible().catch(()=>false)){await tour.click();break}
    await page.waitForTimeout(250);
  }
  const expected={executor:['a2a:operate','a2a:read','a2a:inbox'],ideation:['a2a:read','a2a:inbox','a2a:stop'],worker:['a2a:submit','a2a:raise'],reviewer:['a2a:raise'],monitor:['a2a:raise']};
  const labels={executor:'执行主控',ideation:'构思主控',worker:'worker',reviewer:'reviewer',monitor:'monitor'};
  const allCaps=['a2a:operate','a2a:read','a2a:inbox','a2a:stop','a2a:submit','a2a:raise'];
  for(const role of Object.keys(expected)){
    await page.getByRole('radio',{name:labels[role],exact:true}).click();
    const selected=[];
    for(const cap of allCaps)if(await page.getByRole('switch',{name:labels[role]+' '+cap,exact:true}).getAttribute('aria-checked')==='true')selected.push(cap);
    assert(JSON.stringify([...selected].sort())===JSON.stringify([...expected[role]].sort()),'wrong default switches for '+role);
    assert(await page.getByText('目前对 Codex、Claude 会话生效。',{exact:false}).isVisible(),'provider scope missing');
    await page.screenshot({path:join(out,outputLabel+'-ui-'+role+'.png'),fullPage:true});
    observations.push({role,expected:expected[role],observed:selected});
  }
  await page.getByRole('radio',{name:'worker',exact:true}).click();
  await page.getByRole('switch',{name:'worker 自定义免确认',exact:true}).click();
  await page.getByRole('switch',{name:'worker a2a_raise 免确认',exact:true}).click();
  await page.getByRole('button',{name:'保存角色权限',exact:true}).click();
  await page.getByText('worker · 能力已自定义',{exact:false}).waitFor();
  const backend=JSON.parse(readFileSync(join(root,'ready.json'),'utf8')).origin;
  let settings=await(await fetch(backend+'/api/a2a/role-permissions')).json();
  const worker=settings.roles.find(row=>row.role==='worker');
  assert(JSON.stringify(worker.effective.autoApproveTools)==='["a2a_raise"]','UI choice was not saved');
  assert(settings.changes[0].role==='worker'&&settings.changes[0].command==='save','UI action audit missing');
  await page.screenshot({path:join(out,outputLabel+'-ui-custom.png'),fullPage:true});
  await page.getByRole('button',{name:'恢复该角色默认',exact:true}).click();
  await page.getByText('worker · 能力沿用默认',{exact:false}).waitFor();
  settings=await(await fetch(backend+'/api/a2a/role-permissions')).json();
  assert(settings.roles.find(row=>row.role==='worker').custom===null,'UI reset did not clear custom');
  assert(settings.changes[0].command==='reset','reset audit missing');
  await page.screenshot({path:join(out,outputLabel+'-ui-reset.png'),fullPage:true});
  writeFileSync(join(out,outputLabel+'-ui-oracle.json'),JSON.stringify({status:'PASS',source_revision:launch.source_revision,observations,save_and_reset_read_back:true,screenshots_only_visual_approval_pending:true},null,2)+'\n',{flag:'wx'});
  console.log('PASS real settings UI: five spec defaults, custom save, server readback and reset');
}catch(error){await page.screenshot({path:join(out,outputLabel+'-ui-failure.png'),fullPage:true});throw error}
finally{await context.close()}
