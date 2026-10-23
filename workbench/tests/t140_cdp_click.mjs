// Real browser input events for the isolated T-140 window. No HTMLElement.click().
// Failure modes: events are synthetic; clicks miss the intended controls; saving
// after removal observes an old draft; a rapid second Save submits another event.
const [port] = process.argv.slice(2);
const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(target => target.type === 'page');
if (!page) throw new Error('no page target');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let id = 0;
const pending = new Map();
ws.onmessage = event => {
  const message = JSON.parse(event.data);
  pending.get(message.id)?.(message); pending.delete(message.id);
};
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const n = ++id;
  const timer = setTimeout(() => reject(new Error('CDP timeout: ' + method)), 15000);
  pending.set(n, message => {
    clearTimeout(timer);
    message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
  });
  ws.send(JSON.stringify({ id: n, method, params }));
});
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function point(selector) {
  const box = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e||e.disabled)throw Error('control unavailable');const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
  return { ...box, button: 'left' };
}
try {
  await evaluate(`window.__t140Clicks=[];window.__t140PointerDowns=[];
  document.addEventListener('pointerdown',e=>window.__t140PointerDowns.push({trusted:e.isTrusted,x:e.clientX,y:e.clientY}),{capture:true});
  document.addEventListener('click',e=>{
    const action=e.target.closest('[data-project-save]')?'save':e.target.closest('[data-extra-directory] button')?'remove':null;
    if(action)window.__t140Clicks.push({action,trusted:e.isTrusted,detail:e.detail,draft:document.querySelectorAll('.project-settings [data-extra-directory]').length});
  },{capture:true});`);
  const remove = await point('[data-extra-directory] button');
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', ...remove, clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...remove, clickCount: 1 });
  const save = await point('[data-project-save]');
  // Queue both clicks without a test-inserted delay. The browser processes real
  // input events, so React can commit between the intentional clicks.
  await Promise.all([1, 2].flatMap(clickCount => [
    send('Input.dispatchMouseEvent', { type: 'mousePressed', ...save, clickCount }),
    send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...save, clickCount }),
  ]));
  process.stdout.write(JSON.stringify({ clicks: await evaluate('window.__t140Clicks'),
    pointerdowns: await evaluate('window.__t140PointerDowns'), save_clicks_dispatched: 2 }));
} finally { ws.close(); }
