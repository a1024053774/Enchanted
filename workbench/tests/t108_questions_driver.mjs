// Real Electron DOM/IPC. Only inspect, fixture prompt and answer controls.
import { app } from 'electron';
import { readFileSync, appendFileSync } from 'node:fs';
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
        alerts:[...document.querySelectorAll('[role=alert]')].map(n=>n.textContent)
      })`);
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
      reply({id:request.id,ok:true,value});
    }catch(error){reply({id:request.id,ok:false,error:String(error),stack:error?.stack,renderer_console:rendererConsole.slice(-20)});}
  }).catch(error=>{reply({fatal:String(error)});app.exit(1);});});
}).catch(error=>{reply({startup_error:String(error)});app.exit(1);});
