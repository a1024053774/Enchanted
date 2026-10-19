// Observe real Electron/DOM/IPC/xterm. No replacement of product responses.
import { app, ipcMain } from 'electron';
import { appendFileSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
  ['build', 'state', 'task', 'user-data', 'output'].map(key => [key, { type: 'string' }])) });
const log = value => appendFileSync(join(values.output, 'driver.ndjson'), JSON.stringify(value) + '\n');
const reply = value => new Promise((resolve, reject) => process.stdout.write(JSON.stringify(value) + '\n', error => error ? reject(error) : resolve()));
const channels = [];
const originalHandle = ipcMain.handle.bind(ipcMain);
ipcMain.handle = (name, handler) => { channels.push(name); return originalHandle(name, handler); };
const build = JSON.parse(readFileSync(join(values.build, 'build.json'), 'utf8'));
async function main() {
  const { run } = await import(pathToFileURL(build.main).href);
  // Keep module evaluation unblocked so Electron can emit app.ready.
  void run({ state: values.state, task: values.task, userData: values['user-data'] }).then(async window => {
    const inspect = async () => ({ channels, ...await window.webContents.executeJavaScript(`({
      text: document.body.innerText, bridge: Object.keys(window.a2a), node: typeof window.require,
      tasks: [...document.querySelectorAll('[data-task-option]')].map(n => ({id:n.dataset.taskOption,current:n.getAttribute('aria-current')})),
      newTerminal: (() => { const n=[...document.querySelectorAll('button')].find(n=>n.textContent==='新建终端'); return n?{disabled:n.disabled}:null; })(),
      alerts: [...document.querySelectorAll('[role="alert"]')].map(n=>n.textContent),
      panes: [...document.querySelectorAll('section.pane')].map(n=>({
        key:n.dataset.paneKey, launch:n.dataset.launchId, role:n.dataset.role, task:n.dataset.taskId,
        input:n.dataset.inputEnabled==='true', text:n.innerText,
        alerts:[...n.querySelectorAll('[role="alert"]')].map(a=>a.textContent),
        lifecycle:n.querySelector('[data-lifecycle]')?.dataset.lifecycle,
        terminal:[...n.querySelectorAll('.xterm-accessibility-tree [role="listitem"]')].map(r=>r.textContent).join('\\n')
      }))
    })`) });
    const paneScript = (key, body) => `(async()=>{
      const pane=[...document.querySelectorAll('section.pane')].find(n=>n.dataset.paneKey===${JSON.stringify(key)});
      if(!pane)throw new Error('Pane unavailable'); ${body}
    })()`;
    await reply({ ready: true, pid: process.pid, electron_executable: process.execPath, electron_version: process.versions.electron });
    let pending = Promise.resolve();
    createInterface({ input: process.stdin }).on('line', line => {
      pending = pending.then(async () => {
        const request = JSON.parse(line);
        log({ request });
        try {
          let value;
          if (request.command === 'inspect') value = await inspect();
          else if (request.command === 'select') value = await window.webContents.executeJavaScript(`(()=>{
            const n=[...document.querySelectorAll('[data-task-option]')].find(n=>n.dataset.taskOption===${JSON.stringify(request.task)});
            if(!n||n.disabled)throw new Error('Task unavailable');n.click();return {clicked:true};})()`);
          else if (request.command === 'new-terminal') value = await window.webContents.executeJavaScript(`(()=>{
            const n=[...document.querySelectorAll('button')].find(n=>n.textContent==='新建终端');
            if(!n||n.disabled)throw new Error('New terminal unavailable');n.click();return {clicked:true};})()`);
          else if (request.command === 'terminal-input') {
            if (typeof request.text !== 'string' || request.text.length > 4096) throw new Error('Invalid fixture input');
            window.focus();
            await window.webContents.executeJavaScript(paneScript(request.key, `
              const textarea=pane.querySelector('.xterm-helper-textarea');textarea.focus();
              const data=new DataTransfer();data.setData('text/plain',${JSON.stringify(request.text)});
              textarea.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true}));`));
            window.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'Enter' });
            window.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'Enter' });
            value = { sent: true };
          } else if (request.command === 'close-pane') value = await window.webContents.executeJavaScript(paneScript(request.key, `
            const n=[...pane.querySelectorAll('button')].find(n=>n.textContent==='关闭窗格');
            if(!n||n.disabled)throw new Error('Close pane unavailable');n.click();return {clicked:true};`));
          else if (request.command === 'bridge') {
            if (!['snapshot', 'input', 'newTerminal'].includes(request.operation)) throw new Error('Unsupported bridge probe');
            value = await window.webContents.executeJavaScript(`(async()=>{
              try{return {resolved:true,value:await window.a2a[${JSON.stringify(request.operation)}](...${JSON.stringify(request.args??[])})};}
              catch(error){return {rejected:true,error:String(error)};}})()`);
          } else if (request.command === 'capture') {
            if (!/^[a-z0-9-]+$/.test(request.name)) throw new Error('Invalid capture name');
            await window.webContents.executeJavaScript('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');
            writeFileSync(join(values.output, request.name + '.png'), (await window.webContents.capturePage()).toPNG(), { flag: 'wx' });
            value = await inspect();
            writeFileSync(join(values.output, request.name + '.json'), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
          } else if (request.command === 'close') { await reply({ id: request.id, ok: true }); window.close(); return; }
          else throw new Error('Unknown driver command');
          log({ response: value });
          await reply({ id: request.id, ok: true, value });
        } catch (error) { await reply({ id: request.id, ok: false, error: String(error) }); }
      }).catch(failed);
    });
  }).catch(failed);
}
async function failed(error) {
  log({ fatal: String(error) });
  await reply({ startup_error: String(error), electron_executable: process.execPath, electron_version: process.versions.electron });
  app.exit(1);
}
await main().catch(failed);
