// Test-only DevTools client for the workbench window: `cdp.mjs PORT eval EXPRESSION` prints the JSON value;
// `cdp.mjs PORT shot FILE` writes a PNG screenshot. One connection per call.
import { writeFileSync } from 'node:fs';
const [port, action, argument] = process.argv.slice(2);
const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(target => target.type === 'page');
if (!page) throw new Error('no page target');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let id = 0;
const pending = new Map();
ws.onmessage = event => { const message = JSON.parse(event.data); pending.get(message.id)?.(message); pending.delete(message.id); };
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const n = ++id;
  const timer = setTimeout(() => reject(new Error('CDP timeout: ' + method)), 15000);
  pending.set(n, message => { clearTimeout(timer); message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result); });
  ws.send(JSON.stringify({ id: n, method, params }));
});
if (action === 'eval') {
  const result = await send('Runtime.evaluate', { expression: argument, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  process.stdout.write(JSON.stringify(result.result.value ?? null));
} else if (action === 'shot') {
  const result = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(argument, Buffer.from(result.data, 'base64'));
} else throw new Error('unknown action ' + action);
ws.close();
