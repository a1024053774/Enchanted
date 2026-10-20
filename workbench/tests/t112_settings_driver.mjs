// Real Electron DOM/IPC. This driver changes only the fixture's model settings.
import { app } from 'electron';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline';
import { parseArgs } from 'node:util';
const { values } = parseArgs({ args: process.argv.slice(2), options: Object.fromEntries(
  ['build', 'state', 'task', 'user-data', 'output'].map(key => [key, { type: 'string' }])) });
const build = JSON.parse(readFileSync(join(values.build, 'build.json'), 'utf8'));
const { run } = await import(pathToFileURL(build.main));
const reply = value => process.stdout.write(JSON.stringify(value) + '\n');
void run({ state: values.state, userData: values['user-data'] }).then(window => {
  reply({ ready: true, pid: process.pid, electron_executable: process.execPath, electron_version: process.versions.electron });
  let queue = Promise.resolve();
  createInterface({ input: process.stdin }).on('line', line => { queue = queue.then(async () => {
    const request = JSON.parse(line);
    try {
      let value;
      if (request.command === 'inspect') value = await window.webContents.executeJavaScript(`(async () => ({
        ready: !!document.querySelector('.execution-settings input:not(:disabled)'),
        message: document.querySelector('.execution-settings [role=status]')?.textContent,
        form: {
          role: document.querySelector('.execution-settings select')?.value,
          model: document.querySelectorAll('.execution-settings input:not([type=checkbox])')[0]?.value,
          effort: document.querySelectorAll('.execution-settings input:not([type=checkbox])')[1]?.value,
          fast: document.querySelector('.execution-settings input[type=checkbox]')?.checked,
        },
        settings: await window.a2a.executionSettings()
      }))()`);
      else if (request.command === 'save') value = await window.webContents.executeJavaScript(`(async () => {
        const form = document.querySelector('.execution-settings');
        document.querySelector('.sidebar-settings').open = true;
        const select = form.querySelector('select');
        Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(select, ${JSON.stringify(request.role)});
        select.dispatchEvent(new Event('change', {bubbles: true}));
        await new Promise(resolve => setTimeout(resolve, 50));
        const inputs = form.querySelectorAll('input:not([type=checkbox])');
        for (const [i, value] of [${JSON.stringify(request.model)}, ${JSON.stringify(request.effort)}].entries()) {
          Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(inputs[i], value);
          inputs[i].dispatchEvent(new Event('input', {bubbles: true}));
          await new Promise(resolve => setTimeout(resolve, 0));
        }
        await new Promise(resolve => setTimeout(resolve, 50));
        const fast = form.querySelector('input[type=checkbox]');
        if (fast.checked !== ${JSON.stringify(request.fast)}) fast.click();
        await new Promise(resolve => setTimeout(resolve, 50));
        form.requestSubmit(); return {submitted: true};
      })()`);
      else if (request.command === 'close') { reply({id: request.id, ok: true}); window.close(); return; }
      else throw new Error('Unknown driver command');
      reply({id: request.id, ok: true, value});
    } catch (error) { reply({id: request.id, ok: false, error: String(error)}); }
  }).catch(error => { reply({fatal: String(error)}); app.exit(1); }); });
}).catch(error => { reply({startup_error: String(error)}); app.exit(1); });
