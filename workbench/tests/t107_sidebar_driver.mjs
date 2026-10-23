// Real Electron/DOM/IPC observer. No product data, signal, or handler replacement.
import { app } from 'electron';
import { readFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
  ['build', 'state', 'task', 'user-data', 'output'].map(key => [key, { type: 'string' }])) });
const log = value => appendFileSync(join(values.output, 'driver.ndjson'), JSON.stringify(value) + '\n');
const reply = value => new Promise((resolve, reject) => process.stdout.write(JSON.stringify(value) + '\n', error => error ? reject(error) : resolve()));
const build = JSON.parse(readFileSync(join(values.build, 'build.json'), 'utf8'));
const { run } = await import(pathToFileURL(build.main).href);
void run({ state: values.state, task: values.task, userData: values['user-data'] }).then(async window => {
  const inspect = () => window.webContents.executeJavaScript(`({
    text: document.body.innerText, bridge: Object.keys(window.a2a), node: typeof window.require,
    projects: [...document.querySelectorAll('[data-project-id]')].map(n=>({id:n.dataset.projectId,text:n.innerText,state:n.dataset.projectState,selected:n.getAttribute('aria-current'),disabled:n.disabled})),
    agents: [...document.querySelectorAll('[data-agent-launch]')].map(n=>({id:n.dataset.agentLaunch,parent:n.dataset.agentParent,level:Number(n.dataset.agentLevel),state:n.dataset.agentState,text:n.innerText,x:n.getBoundingClientRect().x, overflow:n.scrollWidth>n.clientWidth,disabled:n.disabled,visible:n.getClientRects().length>0})),
    summaries: [...document.querySelectorAll('[data-agent-summary]')].map(n=>({id:n.dataset.agentSummary,text:n.innerText,visible:n.getClientRects().length>0})),
    panes: [...document.querySelectorAll('section.pane')].map(n=>({key:n.dataset.paneKey,launch:n.dataset.launchId,input:n.dataset.inputEnabled,
      alerts:[...n.querySelectorAll('[role=alert]')].map(a=>a.textContent)})),
    focusedLaunch: document.activeElement?.closest('section.pane')?.dataset.launchId,
    active: (e=>e&&[e.tagName,e.className,e.closest('section.pane')?'in-pane':'',e.closest('[data-pane-key]')?.dataset.paneKey||''].join('|'))(document.activeElement), hasFocus: document.hasFocus(),
    task: document.querySelector('.task-header .eyebrow')?.textContent,
    alerts:[...document.querySelectorAll('[role=alert]')].map(n=>n.textContent),
    notificationChecked: document.querySelector('.sidebar-settings input')?.checked,
    unassigned: document.querySelector('.unassigned-agents')?.innerText
  })`);
  await reply({ ready: true, pid: process.pid, electron_executable: process.execPath, electron_version: process.versions.electron });
  let pending = Promise.resolve();
  createInterface({ input: process.stdin }).on('line', line => {
    pending = pending.then(async () => {
      const request = JSON.parse(line); log({ request });
      try {
        let value;
        if (request.command === 'inspect') value = await inspect();
        else if (request.command === 'sidebar') value = await window.webContents.executeJavaScript('window.a2a.sidebar()');
        else if (['project', 'agent'].includes(request.command)) {
          const attribute = request.command === 'project' ? 'data-project-id' : 'data-agent-launch';
          value = await window.webContents.executeJavaScript(`(()=>{
            const n=[...document.querySelectorAll('button[${attribute}]')].find(n=>n.getAttribute('${attribute}')===${JSON.stringify(request.target)});
            if(!n||n.disabled) throw new Error('Unavailable sidebar target'); n.click(); return {clicked:true}; })()`);
        } else if (['toggle', 'toggle-keyboard'].includes(request.command)) {
          if (request.command === 'toggle-keyboard') {
            // A background macOS app can retain activeElement without owning
            // native keyboard focus. Activate this test app once, then observe
            // the window event before selecting the DOM keyboard target.
            await new Promise((resolve, reject) => {
              const focused = () => { clearTimeout(timer); window.removeListener('focus', focused); resolve(); };
              const timer = setTimeout(() => {
                window.removeListener('focus', focused);
                log({ stage: 'disclosure-native-focus-timeout', target: request.target,
                  windowFocused: window.isFocused(), contentsFocused: window.webContents.isFocused() });
                reject(new Error('Disclosure button does not have keyboard focus: test window activation timed out'));
              }, 3000);
              window.once('focus', focused);
              app.focus({ steal: true });
              window.focus();
              if (window.isFocused()) focused();
            });
          }
          value = await window.webContents.executeJavaScript(`(()=>{
            const n=[...document.querySelectorAll('button[data-agent-toggle]')].find(n=>n.dataset.agentToggle===${JSON.stringify(request.target)});
            if(!n||n.disabled||!n.getClientRects().length) throw new Error('Unavailable disclosure');
            ${request.command === 'toggle' ? 'n.click()' : 'n.focus()'};
            return {target:document.activeElement?.dataset.agentToggle,documentFocused:document.hasFocus(),
              tabIndex:n.tabIndex,expanded:n.getAttribute('aria-expanded')==='true'}; })()`);
          if (request.command === 'toggle-keyboard') {
            const focus = { ...value, windowFocused: window.isFocused(), contentsFocused: window.webContents.isFocused() };
            log({ stage: 'disclosure-keyboard-target', target: request.target, focus });
            if (focus.target !== request.target || focus.tabIndex < 0 || !focus.documentFocused || !focus.windowFocused || !focus.contentsFocused) {
              throw new Error('Disclosure button does not have keyboard focus');
            }
            window.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'Enter' });
            // Match T-103: native HTML button activation requires the CR char.
            window.webContents.sendInputEvent({ type: 'char', keyCode: '\r' });
            window.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'Enter' });
            value = { attempted: true, target: request.target, focus };
          }
        } else if (request.command === 'resize') { window.setSize(request.width, request.height); value = { resized: true }; }
        else if (request.command === 'notifications') value = await window.webContents.executeJavaScript(`(()=>{
          const details=document.querySelector('.sidebar-settings'); details.open=true;
          document.querySelector('.sidebar-settings input').click(); return {clicked:true}; })()`);
        else if (request.command === 'bridge') value = await window.webContents.executeJavaScript(`(async()=>{
          try { return {value:await window.a2a.selectAgent(${JSON.stringify(request.target)})}; }
          catch(error) { return {rejected:true,error:String(error)}; } })()`);
        else if (request.command === 'close') { await reply({ id: request.id, ok: true }); window.close(); return; }
        else throw new Error('Unknown sidebar driver command');
        await reply({ id: request.id, ok: true, value });
      } catch (error) { await reply({ id: request.id, ok: false, error: String(error) }); }
    }).catch(error => { log({ fatal: String(error) }); app.exit(1); });
  });
}).catch(async error => { log({ startup_error: String(error) }); await reply({ startup_error: String(error) }); app.exit(1); });
