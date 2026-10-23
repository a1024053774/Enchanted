// Derived from the independent T-139 reviewer probe.
// Failure modes: a project layout query includes task agents; saving a project
// terminal must exclude them, preserve other terminal names and pass the real validator.
// Failure modes: task includes a project shell; agent selection includes its siblings;
// selecting the same launch again issues a second input credential; ended agent gets stdin.
// A single-agent rename/close must preserve the saved sibling layout and names.
// Runs the actual main.ts with supplied Electron/transport boundaries. This is not GUI evidence.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { OrchestrationStore } from '../src/store.ts';

const [out, revision] = process.argv.slice(2);
assert(out && !existsSync(out), 'New summary path required');
let store;
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [], scope: 'Actual main.ts, SQLite store and daemon arrangement validator; supplied Electron and remaining transport boundaries; no GUI/performance proof' };
try {
  const handlers = new Map(), opened = [], closed = [];
  const taskPanes = new Set(['worker-A', 'reviewer-A']);
  let arrangement = { tree: { direction: 'down', first: 'worker-A', second: 'reviewer-A' },
    names: { 'worker-A': 'A worker', 'reviewer-A': 'A review' } };
  const agents = [
    { id: 'worker-A', project: 'demo', task: 'demo+T-A', role: 'worker', attempt: 'a1' },
    { id: 'reviewer-A', project: 'demo', task: 'demo+T-A', role: 'reviewer', attempt: 'a1' },
    { id: 'ended-A', project: 'demo', task: 'demo+T-A', role: 'worker', attempt: 'old' },
    { id: 'worker-B', project: 'demo', task: 'demo+T-B', role: 'worker', attempt: 'b1' },
    { id: 'project-shell', project: 'demo', task: null, role: 'shell', terminal: true, attempt: null, session: null, fence: null },
    { id: 'project-shell-2', project: 'demo', task: null, role: 'shell', terminal: true, attempt: null, session: null, fence: null },
  ];
  const tasks = ['A', 'B'].map(x => ({ task_id: 'demo+T-' + x, project_id: 'demo', repo: '/fixture/demo', current_attempt: { attempt_id: x === 'A' ? 'a1' : 'b1' } }));
  report.fixture = mkdtempSync('/private/tmp/t139-layout-store-');
  store = new OrchestrationStore(report.fixture);
  for (const agent of agents) store.launch(agent);
  for (const id of ['worker-A','reviewer-A','project-shell','project-shell-2']) store.event('pane_layout_opened', {position: 0}, agents.find(a=>a.id===id));
  store.event('pane_arrangement_saved', {scope:'task:demo+T-A', arrangement});
  store.event('pane_arrangement_saved', {scope:'project:demo', arrangement:{ tree:{direction:'right',first:'project-shell',second:'project-shell-2'},
    names:{'project-shell':'shell one','project-shell-2':'shell two'} }});
  const daemonSource = readFileSync('workbench/src/daemon.ts','utf8');
  const validationSource = daemonSource.slice(daemonSource.indexOf('  const validateArrangement ='), daemonSource.indexOf('  // T-121: a CLI'));
  const validate = vm.runInNewContext(stripTypeScriptTypes(validationSource)+';validateArrangement', {
    store, gates:{call:async({task})=>({ok:true,task:tasks.find(t=>t.task_id===task)})},
    panes:{launchRecord:id=>store.launchRecord(id)}, Refusal:Error,
  });
  const request = async (_state, input, identity) => {
    if(input.command==='sidebar_snapshot') return {ok:true,projects:[{project_id:'demo',repo:'/fixture/demo',tasks}],agents};
    if(input.command==='pane_layout') {
      const scope=input.task?'task:'+input.task:input.project?'project:'+input.project:'free';
      return {ok:true,saved:true,panes:store.openPanes(input.task,input.project),arrangement:store.paneArrangement(scope)};
    }
    if(input.command==='workbench_snapshot') {
      const launch=agents.find(a=>a.id===(input.launch??'worker-A'));
      return {ok:true,task:input.project?null:tasks.find(t=>t.task_id===input.task),launch,pane:{lifecycle:'running',failed:null}};
    }
    if(input.command==='pane_layout_save') {const saved=await validate(input);store.event('pane_arrangement_saved',saved);return {ok:true};}
    if(input.command==='pane_layout_close') {
      const saved=await validate(input,input.layout_task,input.layout_task?undefined:input.project);
      store.event('pane_layout_closed',{},agents.find(a=>a.id===input.launch));store.event('pane_arrangement_saved',saved);return {ok:true};
    }
    if(input.command==='window_close') return {ok:true};
    if(input.command==='pane_layout_open') {store.event('pane_layout_opened',{position:input.position},agents.find(a=>a.id===input.launch));return {ok:true};}
    throw new Error('Unexpected boundary '+input.command);
  };
  const app = Object.assign(new EventEmitter(), { whenReady: async () => {}, setPath() {}, quit() {}, dock: { setIcon() {}, setBadge() {} } });
  class Window extends EventEmitter {
    static getFocusedWindow() { return null; }
    constructor(options) { super(); this.options = options; this.webContents = Object.assign(new EventEmitter(), { id: 1, mainFrame: {}, setWindowOpenHandler() {} }); }
    async loadFile() {}
  }
  const electron = { app, BrowserWindow: Window, ipcMain: { handle: (name, value) => handlers.set(name, value) }, dialog: {}, nativeTheme: new EventEmitter() };
  const context = vm.createContext({ console, process: { argv: [] }, setTimeout, clearTimeout, AggregateError });
  const url = pathToFileURL(resolve('workbench/app/main.ts'));
  const source = revision ? execFileSync('git', ['show', revision + ':workbench/app/main.ts'], { encoding: 'utf8' }) : readFileSync(url, 'utf8');
  const module = new vm.SourceTextModule(stripTypeScriptTypes(source), { context, initializeImportMeta(meta) { meta.url = url.href; } });
  await module.link(async name => {
    let values;
    if (name === 'electron') values = electron;
    else if (name === '../src/transport.ts') values = { request };
    else if (name === '../src/credentials.ts') values = { readOperatorCredential: () => ({ kind: 'operator' }) };
    else if (name === './notificationCenter.ts') values = { NotificationCenter: class {} };
    else if (name === 'node:fs') values = { mkdirSync() {} };
    else values = await import(name);
    return new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  const window = await module.namespace.run({ state: '/fixture/state', task: 'demo+T-A', userData: '/fixture/ui' });
  const event = { sender: window.webContents, senderFrame: window.webContents.mainFrame };
  const invoke = (name, ...args) => handlers.get('a2a:' + name)(event, ...args);
  const check = (name, condition, detail) => { assert(condition, name + ': ' + JSON.stringify(detail)); report.checks.push(name); };
  let selection=await invoke('select-agent','worker-A');
  await invoke('pane-action',selection.focusKey,{type:'rename',name:'independent worker rename'});
  const saved=store.paneArrangement('task:demo+T-A');
  check('actual_store_task_rename_keeps_tree',JSON.stringify(saved.tree)===JSON.stringify({direction:'down',first:'worker-A',second:'reviewer-A'}),saved);
  check('actual_store_task_rename_keeps_sibling_name',saved.names['reviewer-A']==='A review',saved);
  await invoke('close-pane',selection.focusKey);
  const savedAfterClose=store.paneArrangement('task:demo+T-A');
  check('actual_store_task_close_keeps_sibling',savedAfterClose.tree==='reviewer-A'&&savedAfterClose.names['reviewer-A']==='A review',savedAfterClose);
  selection=await invoke('select-agent','worker-A');
  check('explicit_inspect_reopens_in_actual_store',store.openPanes('demo+T-A').some(p=>p.launch==='worker-A'));
  await invoke('pane-action',selection.focusKey,{type:'rename',name:'reopened worker'});
  const reopened=store.paneArrangement('task:demo+T-A');
  check('reopened_agent_preserves_sibling_name',reopened.names['reviewer-A']==='A review'&&reopened.names['worker-A']==='reopened worker',reopened);
  selection=await invoke('select-agent','project-shell');
  report.observedProjectOpenSet=store.openPanes(undefined,'demo').map(p=>p.launch);
  await invoke('pane-action',selection.focusKey,{type:'rename',name:'independent shell rename'});
  check('actual_store_project_shell_rename_succeeds',store.paneArrangement('project:demo').names['project-shell']==='independent shell rename');
  const projectLayout=store.paneArrangement('project:demo');
  check('project_layout_excludes_task_agents',JSON.stringify(projectLayout.tree)===JSON.stringify({direction:'right',first:'project-shell',second:'project-shell-2'}),projectLayout);
  check('project_rename_keeps_other_terminal_name',projectLayout.names['project-shell-2']==='shell two',projectLayout);
  await invoke('close-pane',selection.focusKey);
  const projectAfterClose=store.paneArrangement('project:demo');
  check('project_close_keeps_other_terminal',projectAfterClose.tree==='project-shell-2'&&projectAfterClose.names['project-shell-2']==='shell two',projectAfterClose);
  check('project_close_does_not_close_task_agents',store.openPanes('demo+T-A').length===2);
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.status = 'NO_GO'; }
finally { store?.close(); }
writeFileSync(out, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
