// Contract: packaged startup reuses one authenticated daemon or starts exactly one.
// Failure list: GUI imports wait on app.ready; startup skips the daemon; a protocol
// refusal triggers a new daemon; credentials are exposed/replaced; reconnect starts
// a second daemon; stale/unknown endpoints bypass transport's ownership checks.
// Supplied OS/Electron boundaries only. Real packaging and PTY require the .app run.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync, writeFileSync } from 'node:fs';
import { EventEmitter } from 'node:events';

const report = { task: 'T-102', attempt: 'a2', status: 'INCOMPLETE', checks: [], scope: 'desktop bootstrap with supplied boundaries, no real GUI/daemon proof' };
const path = new URL('../app/desktop.mjs', import.meta.url);
async function exercise(source, scenario) {
  const files = new Map();
  if (scenario !== 'fresh') files.set('/fixture/state/desktop-connection.json', JSON.stringify({ credential: '/fixture/state/desktop-operator-00000000-0000-4000-8000-000000000001.json' }));
  let starts = 0, requests = 0, opened = 0, exited;
  const app = Object.assign(new EventEmitter(), { isPackaged: true, getAppPath: () => '/fixture/app', setPath() {},
    requestSingleInstanceLock: () => true, quit() {}, exit(code) { exited = code; } });
  const env = {};
  const context = vm.createContext({ URL, console, process: { argv: ['/fixture/a2a', '--state', '/fixture/state'], env } });
  const module = new vm.SourceTextModule(source, { context, initializeImportMeta(meta) { meta.url = 'file:///fixture/app/desktop.mjs'; } });
  await module.link(async name => {
    let values;
    if (name === 'electron') values = { app, BrowserWindow: { getAllWindows: () => [] }, dialog: { showErrorBox() {} } };
    else if (name.endsWith('/transport.ts')) values = {
      async startDaemon(root, options) { starts++; assert.equal(root, '/fixture/state'); assert.deepEqual(JSON.parse(JSON.stringify(options)), {}); return {ok:true}; },
      async request(root, input, identity) { requests++; assert.equal(input.command, 'daemon_status'); assert.equal(identity.token, 'private-fixture');
        if (scenario === 'dead') throw Object.assign(new Error('fixture absent'), {code:'ECONNREFUSED'});
        return scenario === 'refused' ? {ok:false,error:'operator_identity_rejected'} : {ok:true,pid:4321}; },
    };
    else if (name.endsWith('/credentials.ts')) values = { readOperatorCredential() { return {token:'private-fixture'}; } };
    else if (name === './ui/main.mjs') values = { async run() { opened++; return {}; } };
    else if (name === 'node:fs') values = { existsSync: p => files.has(p), mkdirSync() {}, realpathSync: p => p,
      readFileSync: p => files.get(p), writeFileSync(p, value, options) { assert.equal(options.mode, 0o600); files.set(p,value); },
      renameSync(a,b) { files.set(b,files.get(a)); files.delete(a); } };
    else values = await import(name);
    return new vm.SyntheticModule(Object.keys(values), function() { for (const [key,value] of Object.entries(values)) this.setExport(key,value); }, {context});
  });
  await module.evaluate();
  // The entry must finish module evaluation before asynchronous app readiness.
  await new Promise(resolve => setImmediate(resolve));
  if (scenario === 'refused') { assert.equal(starts,0); assert.equal(opened,0); assert.equal(exited,1); }
  else { assert.equal(opened,1,'Packaged entry must open the picker after connecting the daemon'); assert.equal(exited,undefined);
    assert.equal(starts,scenario === 'live' ? 0 : 1); }
  assert.equal(requests,scenario === 'fresh' ? 0 : 1);
  assert.ok(![...files.values()].some(v=>v.includes('private-fixture')), 'Credential contents must not enter the connection descriptor');
}
try {
  const source = readFileSync(path,'utf8');
  for (const scenario of ['fresh','live','dead','refused']) { await exercise(source,scenario); report.checks.push(scenario); }
  const bad = source.replace('await startDaemon(state, {});', '/* mutant omits daemon startup */');
  assert.notEqual(bad,source,'Startup mutation must apply');
  await assert.rejects(exercise(bad,'fresh'), assert.AssertionError);
  report.known_bad = 'omitting startup is rejected';
  report.status = 'PASS';
} catch (error) { report.error=String(error); report.stack=error.stack; }
writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));
process.exitCode=report.status === 'PASS' ? 0 : 1;
