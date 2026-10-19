// Execute the actual main IPC entry with supplied Electron/transport boundaries.
// Requirement oracle: a new window with no project can create a home terminal.
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import assert from 'node:assert/strict';
const source = process.argv[2] ?? new URL('../app/main.ts', import.meta.url);
const handlers = new Map(), records = new Map();
let arrangement = null;
const request = async (_, input) => {
  if(input.command==='pane_layout') return {ok:true,saved:true,panes:[...records.values()].map((r,i)=>({launch:r.id,position:i})),arrangement};
  if(input.command==='shell_start') {
    assert.equal(input.cwd,homedir()); assert.equal(input.project,null);
    const launch={id:'shell-'+records.size,role:'shell',worktree:homedir(),project:null,task:null,attempt:null,session:null,fence:null};
    records.set(launch.id,launch);return {ok:true,launch};
  }
  if(input.command==='workbench_snapshot')return {ok:true,task:null,launch:records.get(input.launch),pane:{lifecycle:'running'}};
  if(input.command==='pane_layout_save'){arrangement=input.arrangement;return {ok:true};}
  if(input.command==='pane_layout_close'){records.delete(input.launch);return {ok:true};}
  throw new Error('Unexpected request '+JSON.stringify(input));
};
class Window extends EventEmitter {
  constructor(options){super();this.options=options;this.webContents={id:1,mainFrame:{},on(){},setWindowOpenHandler(){}};}
  async loadFile(){} isDestroyed(){return false;}
}
const app=Object.assign(new EventEmitter(),{whenReady:async()=>{},setPath(){},quit(){}});
const electron={app,BrowserWindow:Window,ipcMain:{handle:(name,fn)=>handlers.set(name,fn)},dialog:{showOpenDialog:async()=>({canceled:true,filePaths:[]})}};
const ctx=vm.createContext({process,console,Buffer});
const module=new vm.SourceTextModule(stripTypeScriptTypes(readFileSync(source,'utf8')),{context:ctx,initializeImportMeta:m=>m.url=new URL('../app/main.ts',import.meta.url).href});
await module.link(async spec=>{
  const exports=spec==='electron'?electron:spec==='../src/transport.ts'?{request}:spec==='../src/credentials.ts'?{readOperatorCredential:()=>({kind:'operator'})}:spec==='node:fs'?{...await import('node:fs'),mkdirSync(){}}:await import(spec);
  return new vm.SyntheticModule(Object.keys(exports),function(){for(const [k,v]of Object.entries(exports))this.setExport(k,v);},{context:ctx});
});
await module.evaluate();
const win=await module.namespace.run({state:'/fixture/state',userData:'/fixture/ui'});
let event={sender:win.webContents,senderFrame:win.webContents.mainFrame};
const invoke=(name,...args)=>Promise.resolve().then(()=>handlers.get('a2a:'+name)(event,...args));
const created=await invoke('new-terminal');
assert.equal(created.paneKeys.length,1,'Empty workspace must create a terminal');
const split=await invoke('pane-action',created.paneKeys[0],{type:'split',direction:'right'});
assert.equal(split.paneKeys.length,2);
assert.equal(split.layout.direction,'right');
await invoke('pane-action',split.paneKeys[0],{type:'rename',name:'我的终端'});
const reopened=await module.namespace.run({state:'/fixture/state',userData:'/fixture/ui'});
event={sender:reopened.webContents,senderFrame:reopened.webContents.mainFrame};
const selected=await invoke('selection');
assert.equal(selected.paneKeys.length,2);
assert.equal(selected.layout.direction,'right');
assert.equal(selected.names[selected.paneKeys[0]],'我的终端');
await assert.rejects(()=>invoke('pane-action','unknown',{type:'split',direction:'right'}));
console.log('PASS: empty workspace → home terminal → split right → rename → reopen');
