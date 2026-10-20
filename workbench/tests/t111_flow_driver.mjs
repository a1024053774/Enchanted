// Observe the real Electron DOM and bridge; do not replace product data or IPC.
import { app } from 'electron';
import { readFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';
const { values } = parseArgs({ options: Object.fromEntries(['build','state','user-data','output','task'].map(key=>[key,{type:'string'}])) });
const reply = value => new Promise(resolve=>process.stdout.write(JSON.stringify(value)+'\n',resolve));
const build = JSON.parse(readFileSync(join(values.build,'build.json'),'utf8'));
const { run } = await import(pathToFileURL(build.main));
void run({state:values.state,userData:values['user-data']}).then(async window=>{
  const js = code=>window.webContents.executeJavaScript(code);
  const inspect = ()=>js(`({
    tabs:[...document.querySelectorAll('[data-flow-tab]')].map(n=>({text:n.innerText,selected:n.getAttribute('aria-current')})),
    text:document.querySelector('.flow-page')?.innerText,
    lanes:[...document.querySelectorAll('[data-flow-task]')].map(n=>({task:n.dataset.flowTask,stage:n.dataset.flowStage,
      text:n.innerText,y:n.getBoundingClientRect().y,expanded:n.querySelector('[data-flow-toggle]').getAttribute('aria-expanded')==='true',
      columns:[...n.querySelectorAll('[data-flow-column]')].map(c=>({stage:c.dataset.flowColumn,current:c.getAttribute('aria-current'),x:c.getBoundingClientRect().x,y:c.getBoundingClientRect().y,width:c.getBoundingClientRect().width,
        agents:[...c.querySelectorAll('[data-flow-agent]')].map(a=>a.dataset.flowAgent)})),
      monitors:[...n.querySelectorAll('.flow-monitors [data-flow-agent]')].map(a=>a.dataset.flowAgent),
      returnLabel:n.querySelector('.flow-returns')?.getAttribute('aria-label'),returnText:n.querySelector('.flow-returns')?.innerText,
      returnLinesVisible:[...n.querySelectorAll('[data-flow-return]')].map(a=>a.getClientRects().length>0&&a.getBoundingClientRect().width>0&&a.getBoundingClientRect().height>0),
      returns:[...n.querySelectorAll('[data-flow-return]')].map(a=>({from:a.dataset.flowReturn,count:Number(a.dataset.returnCount)}))})),
    unassigned:[...document.querySelectorAll('.flow-unassigned [data-flow-agent]')].map(a=>a.dataset.flowAgent),
    more:[...document.querySelectorAll('[data-flow-more]')].map(n=>({id:n.dataset.flowMore,text:n.innerText,expanded:n.getAttribute('aria-expanded')})),
    scroll:(()=>{const n=document.querySelector('.flow-scroll');return n&&{width:n.clientWidth,total:n.scrollWidth,left:n.scrollLeft}})(),
    bodyOverflow:document.documentElement.scrollWidth>document.documentElement.clientWidth,
    alerts:[...document.querySelectorAll('[role=alert]')].map(n=>n.innerText)
  })`);
  await reply({ready:true,pid:process.pid,electron_executable:process.execPath,electron_version:process.versions.electron});
  let pending=Promise.resolve();
  createInterface({input:process.stdin}).on('line',line=>{pending=pending.then(async()=>{
    const request=JSON.parse(line); appendFileSync(join(values.output,'driver.ndjson'),JSON.stringify(request)+'\n');
    try {
      let value;
      if(request.command==='inspect') value=await inspect();
      else if(request.command==='flow') value=await js('window.a2a.flow()');
      else if(request.command==='resize'){ window.setSize(request.width,request.height);value=true; }
      else if(request.command==='scroll') value=await js(`(()=>{const n=document.querySelector('.flow-scroll');n.scrollLeft=n.scrollWidth;return n.scrollLeft})()`);
      else if(['tab','more','toggle'].includes(request.command)) {
        const attribute={tab:'data-flow-tab',more:'data-flow-more',toggle:'data-flow-toggle'}[request.command];
        value=await js(`(()=>{const n=[...document.querySelectorAll('[${attribute}]')].find(n=>${request.command==='tab'?'true':`n.getAttribute('${attribute}')===${JSON.stringify(request.target)}`});if(!n||n.disabled)throw Error('Unavailable flow control');n.click();return true})()`);
      } else if(request.command==='close'){await reply({id:request.id,ok:true});window.close();return;}
      else throw Error('Unknown flow command');
      await reply({id:request.id,ok:true,value});
    }catch(error){await reply({id:request.id,ok:false,error:String(error)});}
  }).catch(async error=>{await reply({fatal:String(error)});app.exit(1)});});
}).catch(async error=>{await reply({startup_error:String(error)});app.exit(1)});
