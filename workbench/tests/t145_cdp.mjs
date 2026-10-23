// Test-only CDP input driver. Uses native browser input, never calls a2a.input.
const [port, method, parameters] = process.argv.slice(2);
const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p => p.type === 'page');
if (!page) throw new Error('No page target');
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
const timer = setTimeout(() => { throw new Error('CDP input timeout'); }, 15000);
const response = await new Promise((resolve, reject) => {
  socket.onmessage = event => { const value = JSON.parse(event.data); if (value.id === 1) value.error ? reject(new Error(JSON.stringify(value.error))) : resolve(value.result); };
  socket.send(JSON.stringify({ id: 1, method, params: JSON.parse(parameters) }));
});
clearTimeout(timer); socket.close(); console.log(JSON.stringify(response));
