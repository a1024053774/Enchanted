// Replays a recorded pty.raw through the focus-safe writer the way the pane view does
// (65,536-byte chunks, streaming UTF-8 decode) and times it. Usage:
//   Electron replay-trace.mjs <writer.mjs> <pty.raw> <result.json>
import { app, BrowserWindow } from 'electron';
import { readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const [writer, trace, result] = process.argv.slice(2);
const xterm = new URL('../../../workbench/node_modules/@xterm/xterm/', import.meta.url);
app.whenReady().then(async () => {
  const window = new BrowserWindow({ width: 1000, height: 640, show: false, webPreferences: { contextIsolation: true, sandbox: false, webSecurity: false } });
  await window.loadURL('data:text/html,' + encodeURIComponent(`<!doctype html><link rel="stylesheet" href="${xterm}css/xterm.css"><div id="t" style="width:900px;height:460px"></div>
<script src="${xterm}lib/xterm.js"></script><script type="module">
import { createFocusSafeWriter } from '${pathToFileURL(writer)}';
const term = new Terminal({cols:120,rows:40}); term.open(document.querySelector('#t'));
window.write = createFocusSafeWriter(term, () => {}); window.ready = true;
</script>`));
  while (!await window.webContents.executeJavaScript('window.ready === true')) await new Promise(r => setTimeout(r, 50));
  const bytes = readFileSync(trace);
  const chunks = [];
  for (let at = 0; at < bytes.length; at += 65536) chunks.push(bytes.subarray(at, at + 65536).toString('base64'));
  const ms = await window.webContents.executeJavaScript(`(async () => {
    const decoder = new TextDecoder('utf-8'); const started = performance.now();
    for (const chunk of ${JSON.stringify(chunks)}) await window.write(decoder.decode(Uint8Array.from(atob(chunk), c => c.charCodeAt(0)), { stream: true }));
    return performance.now() - started; })()`);
  writeFileSync(result, JSON.stringify({ writer, trace, bytes: bytes.length, chunks: chunks.length, replay_ms: Math.round(ms) }, null, 2) + '\n');
  app.exit(0);
}, error => { console.error(error); app.exit(1); });
