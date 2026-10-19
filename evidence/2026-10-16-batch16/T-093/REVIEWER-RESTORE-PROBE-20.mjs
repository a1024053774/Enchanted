import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync, mkdtempSync, realpathSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';

const base = '/private/tmp/t093-r03-uj4pu1e0';
const source = process.argv[2], output = process.argv[3];
const generatedInput = process.argv[4] ? JSON.parse(readFileSync(process.argv[4],'utf8')) : null;
const moduleURL = new URL('file://' + base + '/candidate/workbench/src/panes.ts');
const { OrchestrationStore } = await import(new URL('./store.ts', moduleURL));
const operations = [], spawned = new Map(), cases = [];
const root = mkdtempSync(base + '/t/independent-');
const store = new OrchestrationStore(root);
const executable = '/usr/bin/true', canonical = realpathSync(executable);
const processStub = { execPath: process.execPath, env: {}, kill() { throw Object.assign(new Error('fixture absent'), {code:'ESRCH'}); } };
const context = vm.createContext({ console, process:processStub, Buffer, URL, TextDecoder, setTimeout, clearTimeout });
const mod = new vm.SourceTextModule(stripTypeScriptTypes(readFileSync(source,'utf8')), { context,
  initializeImportMeta(meta) { meta.url = moduleURL.href; } });
await mod.link(async name => {
  let values;
  if (name === 'node:module') values = { createRequire: () => name => {
    if (name !== 'node-pty') throw new Error('unexpected require');
    return { spawn(shell,args,options) {
      const label = options.env.REVIEW_CASE;
      const pid = 51000 + spawned.size;
      operations.push({label,kind:'pty-spawn',shell,argv:[...args]});
      const terminal = {pid,onData(){},onExit(){},kill(){},write(){throw new Error('input prohibited');}};
      spawned.set(pid,{label,terminal}); return terminal;
    }};
  }};
  else if (name === 'node:child_process') {
    const execFile = (file,args,options,callback) => {
      if (file === executable) {
        operations.push({label:options.env.REVIEW_CASE,kind:'cli-version',argv:[file,...args]});
        callback(null,'2.1.302 (Claude Code)\n','');
      } else if (file === '/usr/bin/python3') {
        const pid=Number(args.at(-1)), owned=spawned.get(pid), leader=pid+1000;
        if (!owned) throw new Error('unowned query');
        operations.push({label:owned.label,kind:'process-query'});
        callback(null,JSON.stringify({schema:1,root_pid:pid,method:'macOS libproc',rows:[
          {pid,ppid:1,pgid:pid,tpgid:leader,command:'/bin/zsh'},
          {pid:leader,ppid:pid,pgid:leader,tpgid:leader,command:canonical}]}),'');
      } else throw new Error('unexpected executable boundary');
    };
    execFile[Symbol.for('nodejs.util.promisify.custom')] = (file,args,options) => new Promise((resolve,reject) =>
      execFile(file,args,options,(error,stdout,stderr)=>error?reject(error):resolve({stdout,stderr})));
    values={execFile};
  } else if (name.startsWith('node:')) values=await import(name);
  else values=await import(new URL(name,moduleURL));
  return new vm.SyntheticModule(Object.keys(values),function(){ for(const key of Object.keys(values)) this.setExport(key,values[key]); },{context});
});
await mod.evaluate();
store.db.exec('CREATE TABLE tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL)');
store.db.prepare('INSERT INTO tasks VALUES (?,?)').run('review-task',JSON.stringify({task_id:'review-task',project_id:'review-project',spec_rev:1,repo:root}));
const records=[];
for (const label of ['normal','normal-auth-missing','fake','legacy-fake']) {
  const normal=label.startsWith('normal'),session=generatedInput && label==='normal-auth-missing'?generatedInput.session:randomUUID(),config=generatedInput && label==='normal-auth-missing'?generatedInput.env.CLAUDE_CONFIG_DIR:join(root,label,'.claude');
  mkdirSync(join(config,'projects','fixture'),{recursive:true});
  writeFileSync(join(config,'projects','fixture',session+'.jsonl'),JSON.stringify({type:'user',sessionId:session,cwd:generatedInput && label==='normal-auth-missing'?generatedInput.worktree:root})+'\n');
  let record={id:randomUUID(),project:'review-project',task:'review-task',attempt:null,role:'controller',preset:'ideation',session,
    thread:randomUUID(),spec_rev:1,cli:'Claude Code',cli_version:'2.1.302 (Claude Code)',executable_path:canonical,
    argv:[executable,'--session-id',session,'--model','sentinel-'+randomUUID(),'--settings','{"hooks":{},"sentinel":"a b"}'],
    shell:'/bin/zsh',worktree:root,execution_state:'started',
    role_card_revision:normal?'T-093/normal-login/2.1.302':'T-078-2/P1',
    env:{HOME:join(root,label),CLAUDE_CONFIG_DIR:config,REVIEW_CASE:label,ANTHROPIC_BASE_URL:'http://127.0.0.1:49187',
      ...(normal?{NODE_OPTIONS:'--import=file:///private/tmp/synthetic-trace.ts',A2A_PROFILE_PROCESS_LOG:join(root,'C-processes.jsonl')}:{ANTHROPIC_AUTH_TOKEN:'a2a-fixture-key-not-a-secret'})},
    ...(normal?{login_audit_directory:join(root,'login-audits'),login_preflight_file:join(root,'login-audits/preflight.json')}:{}),
    ...(['normal','fake'].includes(label)?{authentication:normal?'isolated normal login':'isolated fake API only'}:{})};
  record.shell_argv=['-f','-i','-c',(normal?'exec ':'')+'synthetic recorded original argv'];
  if(generatedInput && label==='normal-auth-missing') {
    record=structuredClone(generatedInput);
    delete record.authentication;
    record.env.REVIEW_CASE=label;
  }
  records.push({label,record});
  mkdirSync(join(root,'traces',record.id),{recursive:true});writeFileSync(join(root,'traces',record.id,'pty.raw'),'history\n');
  store.launch(record);store.event('pane_started',{shell_pid:7},record);
  const resume=[...record.argv];resume[1]='--resume';
  store.event('pane_layout_opened',{position:records.length-1,native_session:session,resume_argv:resume},record);
}
try {
  const panes=new mod.namespace.Panes(root,store,{},()=>{});
  await panes.recover('independent-review-03');
  for (const {label,record} of records) {
    const op=operations.filter(x=>x.label===label), event=store.lastEvent(record.id,['pane_restored','pane_restore_failed']);
    const history_unchanged=JSON.stringify(store.launchRecord(record.id))===JSON.stringify(record);
    cases.push({label,operations:op,event:event?.type,error:event?.data.error??null,history_unchanged,
      cli_calls:op.filter(x=>x.kind==='cli-version').length,pty_calls:op.filter(x=>x.kind==='pty-spawn').length,
      contract_pass:history_unchanged&&(label.startsWith('normal')?
        op.length===0&&event?.data.error==='normal_login_restore_requires_protected_start':event?.type==='pane_restored')});
  }
} finally {store.close();}
const report={status:cases.every(x=>x.contract_pass)?'PASS':'FAIL',scope:'actual Panes.recover/store/native file; supplied subprocess and PTY; no CLI/auth/OS execution',cases};
writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,cases:cases.map(({label,cli_calls,pty_calls,error,contract_pass})=>({label,cli_calls,pty_calls,error,contract_pass}))}));
process.exitCode=report.status==='PASS'?0:2;
