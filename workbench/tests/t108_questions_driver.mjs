// Real Electron DOM/IPC. Only inspect, fixture prompt and answer controls.
import { app } from 'electron';
import { readFileSync, appendFileSync, renameSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';
import { DatabaseSync } from 'node:sqlite';
import { firstAnswerReceipt } from './t108_answer_receipt.mjs';
const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
  ['build','state','task','user-data','output'].map(key => [key,{type:'string'}])) });
const build=JSON.parse(readFileSync(join(values.build,'build.json'),'utf8'));
const manifest=JSON.parse(readFileSync(join(values.state,'../manifest.json'),'utf8'));
const { run }=await import(pathToFileURL(build.main));
const reply=value=>process.stdout.write(JSON.stringify(value)+'\n');
void run({state:values.state,task:values.task,launch:manifest.launch,userData:values['user-data']}).then(window=>{
  const rendererConsole=[];
  let disconnectedSocket = null;
  window.webContents.on('console-message', details => {
    const entry={level:details.level,message:details.message,line:details.lineNumber,source:details.sourceId};
    rendererConsole.push(entry);appendFileSync(join(values.output,'renderer-console.jsonl'),JSON.stringify(entry)+'\n');
  });
  reply({ready:true,pid:process.pid,electron_executable:process.execPath,electron_version:process.versions.electron});
  let queue=Promise.resolve();
  createInterface({input:process.stdin}).on('line',line=>{queue=queue.then(async()=>{
    const request=JSON.parse(line);
    try {
      let value;
      if(request.command==='inspect') value=await window.webContents.executeJavaScript(`({
        text:document.body.innerText, panes:[...document.querySelectorAll('section.pane')].map(n=>({key:n.dataset.paneKey,launch:n.dataset.launchId,input:n.dataset.inputEnabled})),
        questions:[...document.querySelectorAll('[data-question-id]')].map(n=>({id:n.dataset.questionId,text:n.innerText})),
        notices:[...document.querySelectorAll('[data-notice-id]')].map(n=>({id:n.dataset.noticeId,launch:n.dataset.noticeLaunch,text:n.innerText})),
        notice_additions:window.t110NoticeAdditions??0,
        agents:[...document.querySelectorAll('[data-agent-launch]')].map(n=>({id:n.dataset.agentLaunch,project:document.querySelector('[data-project-id][aria-current=page]')?.dataset.projectId??null,state:n.dataset.agentState,background:getComputedStyle(n).backgroundColor})),
        projects:[...document.querySelectorAll('[data-project-id]')].map(n=>({id:n.dataset.projectId,state:n.dataset.projectState,background:getComputedStyle(n).backgroundColor})),
        selected_project:document.querySelector('[data-project-id][aria-current=page]')?.dataset.projectId??null,
        focused_agent:document.querySelector('[data-agent-launch][aria-current=true]')?.dataset.agentLaunch??null,
        focused_launch:document.activeElement?.closest('section.pane')?.dataset.launchId??null,
        terminal_hidden:document.querySelector('.terminal-page')?.hidden??null,
        sidebar_error:document.querySelector('.catalog-error')?.textContent??null,
        notification_settings:Object.fromEntries([...document.querySelectorAll('[data-notification-setting]')].map(n=>[n.dataset.notificationSetting,n.checked])),
        alerts:[...document.querySelectorAll('[role=alert]')].map(n=>n.textContent)
      })`);
      else if(request.command==='watch-notices') value=await window.webContents.executeJavaScript(`(()=>{window.t110NoticeAdditions=0;new MutationObserver(rows=>{for(const row of rows) for(const n of row.addedNodes) if(n.nodeType===1)window.t110NoticeAdditions+=(n.matches('[data-notice-id]')?1:0)+n.querySelectorAll('[data-notice-id]').length;}).observe(document.querySelector('.app-notifications'),{childList:true,subtree:true});return true;})()`);
      else if(request.command==='notification-setting') value=await window.webContents.executeJavaScript(`(()=>{const n=document.querySelector('[data-notification-setting='+${JSON.stringify(request.preference)}+']');if(!n)throw new Error('Setting control missing');document.querySelector('.sidebar-settings').open=true;if(n.checked!==${Boolean(request.enabled)})n.click();return true;})()`);
      else if(request.command==='reload-window'){await new Promise(resolve=>{window.webContents.once('did-finish-load',resolve);window.webContents.reload();});value=true;}
      else if(request.command==='refresh-list')value=await window.webContents.executeJavaScript(`(()=>{const n=[...document.querySelectorAll('button')].find(n=>n.textContent==='刷新列表');if(!n||n.disabled)throw new Error('Refresh control unavailable');n.click();return true;})()`);
      else if(request.command==='disconnect-sidebar'){
        const socket=join(values.state,'control.sock'), info=statSync(socket);
        if(!info.isSocket()||disconnectedSocket)throw new Error('Expected the fixture live socket');
        disconnectedSocket={ino:info.ino,pid:readFileSync(join(values.state,'daemon.pid'),'utf8').trim()};
        renameSync(socket,join(values.state,'control.sock.t110-off'));value=disconnectedSocket;
      }
      else if(request.command==='reconnect-sidebar'){
        const socket=join(values.state,'control.sock');
        renameSync(join(values.state,'control.sock.t110-off'),socket);
        const info=statSync(socket),pid=readFileSync(join(values.state,'daemon.pid'),'utf8').trim();
        if(!info.isSocket()||info.ino!==disconnectedSocket.ino||pid!==disconnectedSocket.pid)throw new Error('Fixture daemon or socket identity changed');
        value={socket:{ino:info.ino,pid},...await window.webContents.executeJavaScript(`(async()=>({sidebar:await window.a2a.sidebar(),selection:await window.a2a.selection()}))()`)};
        disconnectedSocket=null;
      }
      else if(request.command==='offline-resize')value=await window.webContents.executeJavaScript(`(async()=>{
        try{await window.a2a.resize(${JSON.stringify(request.pane)},120,40);return {rejected:false};}
        catch(error){return {rejected:true,error:String(error)};}
      })()`);
      else if(request.command==='reconnect-pane')value=await window.webContents.executeJavaScript(`(()=>{
        const pane=[...document.querySelectorAll('section.pane')].find(n=>n.dataset.paneKey===${JSON.stringify(request.pane)});
        if(!pane)throw new Error('Original pane binding missing');
        const button=[...pane.querySelectorAll('.connection-error button')].find(n=>n.textContent==='重新连接');
        if(!button||button.disabled)throw new Error('Reconnect control unavailable');button.click();return true;
      })()`);
      else if(request.command==='background'){app.hide();value=true;}
      else if(request.command==='foreground'){window.show();app.focus({steal:true});window.focus();value=true;}
      else if(request.command==='flow-page')value=await window.webContents.executeJavaScript(`(()=>{document.querySelector('[data-flow-tab]').click();return true;})()`);
      else if(request.command==='click-notice')value=await window.webContents.executeJavaScript(`(()=>{const n=document.querySelector('[data-notice-id]');if(!n||n.disabled)throw new Error('Notice unavailable');n.click();return true;})()`);
      else if(request.command==='prompt') value=await window.webContents.executeJavaScript(`(async()=>{
        const key=document.querySelector('section.pane').dataset.paneKey;
        await window.a2a.input(key,${JSON.stringify('\x1b[200~Please ask the region question.\x1b[201~')});
        await new Promise(r=>setTimeout(r,150)); await window.a2a.input(key,${JSON.stringify('\r')}); return {sent:true}; })()`);
      else if(request.command==='answer') {
        const db=new DatabaseSync(join(values.state,'state.sqlite3'),{readOnly:true});
        try {
          const after=db.prepare('SELECT coalesce(max(seq),0) AS seq FROM orchestration_events').get().seq;
          const clicked=await window.webContents.executeJavaScript(`(()=>{
        const form=document.querySelector('[data-question-id]');
        const option=[...form.querySelectorAll('.question-options button')].find(n=>n.textContent.startsWith('西区'));
        if(!option||option.disabled)throw new Error('Question option unavailable');option.click();
        return new Promise(resolve=>setTimeout(()=>{form.requestSubmit();resolve({clicked:true});},0)); })()`);
          value={...clicked,...await firstAnswerReceipt(db,after,manifest.launch)};
        } finally {db.close();}
      }
      else if(request.command==='followup') value=await window.webContents.executeJavaScript(`(async()=>{
        const key=document.querySelector('section.pane').dataset.paneKey;
        return await window.a2a.input(key,${JSON.stringify('\x1b[200~'+request.text+'\x1b[201~')}); })()`);
      else if(request.command==='duplicate') value=await window.webContents.executeJavaScript(`(async()=>{
        try {await window.a2a.answer(document.querySelector('section.pane').dataset.paneKey,${JSON.stringify(request.question)},['西区']);return {rejected:false};}
        catch(error){return {rejected:true,error:String(error)};} })()`);
      else if(request.command==='close'){reply({id:request.id,ok:true});window.close();return;}
      else throw new Error('Unknown driver command');
      if(request.command==='inspect') value.badge=Number(app.dock.getBadge() || '0');
      reply({id:request.id,ok:true,value});
    }catch(error){reply({id:request.id,ok:false,error:String(error),stack:error?.stack,renderer_console:rendererConsole.slice(-20)});}
  }).catch(error=>{reply({fatal:String(error)});app.exit(1);});});
}).catch(error=>{reply({startup_error:String(error)});app.exit(1);});
