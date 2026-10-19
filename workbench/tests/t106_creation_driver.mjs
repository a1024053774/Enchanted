// Observe the real product DOM and IPC. Native directory dialogs are operated
// by the controller; no dialog result, gate response, or database is replaced.
import { app } from 'electron';
import { appendFileSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
  ['build', 'state', 'task', 'user-data', 'output'].map(key => [key, { type: 'string' }])) });
const log = value => appendFileSync(join(values.output, 'driver.ndjson'), JSON.stringify(value) + '\n');
const reply = value => new Promise((resolve, reject) => process.stdout.write(JSON.stringify(value) + '\n', error => error ? reject(error) : resolve()));
async function main() {
  const build = JSON.parse(readFileSync(join(values.build, 'build.json'), 'utf8'));
  const { run } = await import(pathToFileURL(build.main).href);
  // Finish entry-module evaluation before the product awaits Electron ready.
  void run({ state: values.state, userData: values['user-data'] }).then(async window => {
    const inspect = () => window.webContents.executeJavaScript(`({
      text: document.body.innerText, node: typeof window.require, bridge: Object.keys(window.a2a),
      busy: document.querySelector('nav[aria-busy]')?.getAttribute('aria-busy'),
      form: !!document.querySelector('.creation-dialog[open]'),
      formValid: [...document.querySelectorAll('[data-creation-field]')].every(n=>n.validity.valid),
      invalidFields: [...document.querySelectorAll('[data-creation-field]')].filter(n=>!n.validity.valid).map(n=>({field:n.dataset.creationField,reason:n.validationMessage})),
      fields: Object.fromEntries([...document.querySelectorAll('[data-creation-field]')].map(n=>[n.dataset.creationField,n.value])),
      repo: document.querySelector('[data-creation-repo]')?.textContent,
      alerts: [...document.querySelectorAll('[role=alert]')].map(n=>n.textContent),
      projects: [...document.querySelectorAll('[data-project-id]')].map(n=>n.dataset.projectId),
      tasks: [...document.querySelectorAll('[data-task-option]')].map(n=>({id:n.dataset.taskOption,text:n.textContent})),
      buttons: [...document.querySelectorAll('button')].map(n=>({text:n.textContent,disabled:n.disabled}))
    })`);
    await reply({ ready: true, pid: process.pid, electron_executable: process.execPath, electron_version: process.versions.electron });
    let pending = Promise.resolve();
    createInterface({ input: process.stdin }).on('line', line => {
      pending = pending.then(async () => {
        const request = JSON.parse(line); log({ request });
        try {
          let value;
          if (request.command === 'inspect') value = await inspect();
          else if (request.command === 'click') value = await window.webContents.executeJavaScript(`(()=>{
            const n=[...document.querySelectorAll('button')].find(n=>n.textContent===${JSON.stringify(request.text)});
            if(!n||n.disabled)throw new Error('Button unavailable');n.click();return {clicked:true};})()`);
          else if (request.command === 'fill') value = await window.webContents.executeJavaScript(`(()=>{
            const n=[...document.querySelectorAll('[data-creation-field]')].find(n=>n.dataset.creationField===${JSON.stringify(request.field)});
            if(!n||n.disabled||n.closest('fieldset')?.disabled)throw new Error('Field unavailable');
            const proto=n.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
            Object.getOwnPropertyDescriptor(proto,'value').set.call(n,${JSON.stringify(request.value)});
            n.dispatchEvent(new Event('input',{bubbles:true}));return {entered:true};})()`);
          else if (request.command === 'submit') value = await window.webContents.executeJavaScript(`(()=>{
            const n=document.querySelector('.creation-form');if(!n)throw new Error('Form unavailable');
            n.requestSubmit();return {submitted:true};})()`);
          else if (request.command === 'bridge') {
            if (request.operation !== 'creationSubmit') throw new Error('Unsupported probe');
            value = await window.webContents.executeJavaScript(`(async()=>{
              try { return {resolved:true,value:await window.a2a.creationSubmit(${JSON.stringify(request.input)})}; }
              catch(error) { return {rejected:true,error:String(error)}; }
            })()`);
          } else if (request.command === 'resize') { window.setSize(request.width, request.height); value = { resized: true }; }
          else if (request.command === 'close') { await reply({ id: request.id, ok: true }); window.close(); return; }
          else throw new Error('Unknown driver command');
          log({ response: value }); await reply({ id: request.id, ok: true, value });
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
