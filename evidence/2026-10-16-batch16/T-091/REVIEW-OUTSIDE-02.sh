#!/bin/bash
# T-091 独立审查 OUTSIDE-02，仅由执行主控在沙箱外运行。
# 候选 e4dcb2739af449396a3c6982e9826326d64a4369；不修改 checkout。
# 保留 OUTSIDE-01 全部失败现场；新 git archive、新构建槽、新外置 review 目录。
# 修复审查脚本 ESM 顶层 await run()/app.whenReady 的等待环；不改业务断言或期限。
# 新增阶段日志；隔离路径在入口模块完成前同步设置；void main() 允许 Electron ready。
# 只补真实 Electron/生产 main/preload/renderer/IPC/transport 入口及 M1/M2 单处变异。
# socket 对端为独立夹具，不冒称真实 daemon/PTY 或真实模型端到端。
# 上限：3 次串行 Electron，峰值 1 个；候选最多两个隔离 BrowserWindow 检验跨窗口 key。
# 真实 Claude=0、真实 Codex=0、模型 API=0、daemon=0、PTY=0、新 agent=0。
# 不运行夹具 commit/submit/integration，不重跑已通过的归档与版本部分。
# 进程脱离调用者进程组；45s 应用内硬期限、65s 外部硬期限、32MiB 输出限额。
# 每段打印名称、输出目录、退出码；只清理本脚本拥有且身份仍一致的测试进程。
# 结果只写 /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/review-outside-02-*。
# 缺盘即报错；不回退，不改全局配置，不操作用户应用，不请求升级。
set -u
set -o pipefail
review_tools=$(mktemp -d /private/tmp/t091-review-tools-02-XXXXXX)
export PYTHONDONTWRITEBYTECODE=1
cat > "$review_tools/ui-entry.mjs" <<'T091_REVIEW_FILE_EOF'
// 独立输入来自 ticket：同任务三格、凭据/序号分离、无效选择建窗前拒绝。
// 真实 Electron + production run/preload/renderer + Unix transport。
// socket 对端是独立夹具；本检查不声称证明真实 daemon/PTY。
import { app, BrowserWindow } from 'electron';
import { createServer } from 'node:net';
import { mkdtempSync, mkdirSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';

const [build, output] = process.argv.slice(2);
let finishing=false;
app.on('before-quit',event=>{if(!finishing)event.preventDefault();});
const root = mkdtempSync('/private/tmp/t091-ui-02-');
const state = join(root, 's'); mkdirSync(state);
// Fix all Electron paths before the entry module releases app readiness.
const userData=join(root,'ui');
for(const path of [userData,join(userData,'session'),join(userData,'logs'),join(userData,'crashes')])mkdirSync(path,{recursive:true});
for(const [key,path] of [['userData',userData],['sessionData',join(userData,'session')],['logs',join(userData,'logs')],['crashDumps',join(userData,'crashes')]])app.setPath(key,path);
process.env.A2A_OPERATOR_CREDENTIAL = join(root, 'operator.json');
writeFileSync(process.env.A2A_OPERATOR_CREDENTIAL, JSON.stringify({kind:'operator',state,epoch:'review',token:'fixture-only'}), {mode:0o600});
const task = 'task-' + randomUUID(), attempt = 'attempt-' + randomUUID();
const launches = ['ideation','executor','worker'].map(x => x + '-' + randomUUID());
const records = Object.fromEntries(launches.map((id,i) => [id, {id,task,role:i===2?'worker':'controller',preset:i===2?null:['ideation','executor'][i],attempt:i===2?attempt:null,thread:randomUUID(),session:randomUUID(),cli_version:'fixture',model_requested:'fixture'}]));
records.foreign = {...records[launches[2]],id:'foreign',task:task+'-other'};
records.stale = {...records[launches[2]],id:'stale',attempt:'old-attempt'};
const credentials = new Map(), calls = [], checks = [];
const save = (name,value) => writeFileSync(join(output,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const check = (name, value) => { checks.push({name,pass:Boolean(value)}); assert.ok(value,name); };
let latestStage='module_loaded';
function stage(name, detail={}) {
  latestStage=name;
  appendFileSync(join(output,'stages.ndjson'),JSON.stringify({name,time:new Date().toISOString(),pid:process.pid,app_ready:app.isReady(),...detail})+'\n');
}
stage('module_loaded',{electron:process.versions.electron,argv:process.argv,root,state,userData});
app.on('ready',()=>stage('app_ready'));
app.on('browser-window-created',(_event,window)=>{
  stage('browser_window_created',{window:window.id});
  window.webContents.on('did-finish-load',()=>stage('load_finished',{window:window.id}));
  window.webContents.on('did-fail-load',(_e,code,description)=>stage('load_failed',{window:window.id,code,description}));
  window.webContents.on('render-process-gone',(_e,detail)=>stage('renderer_gone',{window:window.id,detail}));
});
const originalWhenReady=app.whenReady.bind(app);
app.whenReady=(...args)=>{
  stage('when_ready_called');
  const promise=originalWhenReady(...args);
  void promise.then(()=>stage('when_ready_resolved'));
  return promise;
};

save('oracle.json',{task,attempt,launches,records,layer:'真实 UI 与 transport；独立 socket 夹具，无真实 agent/daemon/PTY'});
const server = createServer(socket => {
  let text=''; socket.setEncoding('utf8');
  socket.on('error',()=>{});
  socket.on('data',chunk=>{
    text+=chunk; if(!text.includes('\n'))return;
    const packet=JSON.parse(text.slice(0,text.indexOf('\n'))), q=packet.input;
    calls.push({command:q.command,input:q,window:packet.identity?.window??null});
    appendFileSync(join(output,'transport.ndjson'),JSON.stringify(calls.at(-1))+'\n');
    let result;
    if(q.command==='workbench_snapshot') result={ok:true,daemon:'fixture',task:{task_id:task,project_id:'review',repo:root,title:'独立审查夹具',state:'claimed',current_attempt:{attempt_id:attempt}},launch:records[q.launch],pane:{lifecycle:'running',state:'unknown',failed:null,interrupted:true,interruption:7,input_generation:0}};
    else if(q.command==='window_open'){
      const identity={kind:'window',window:randomUUID(),token:'fixture-only'};
      credentials.set(identity.window,{launch:q.launch,sequence:0}); result={ok:true,identity};
    }else if(q.command==='pane_output'){
      const bytes=Buffer.from('独立输出 '+q.launch+'\r\n'); const data=bytes.subarray(q.offset);
      result={ok:true,launch:q.launch,start_offset:q.offset,next_offset:bytes.length,total_bytes:bytes.length,data_base64:data.toString('base64')};
    }else{
      const c=credentials.get(packet.identity?.window);
      if(!c) result={ok:false,error:'unknown_fixture_credential'};
      else if(q.command==='window_close'){credentials.delete(packet.identity.window);result={ok:true};}
      else if(q.sequence!==c.sequence+1) result={ok:false,error:'sequence_not_independent'};
      else {c.sequence=q.sequence;result={ok:true};}
    }
    socket.end(JSON.stringify(result)+'\n');
  });
});
async function main() {
  stage('socket_listen_started');
await new Promise(resolve=>server.listen(join(state,'control.sock'),resolve));
  stage('socket_listen_completed');
const deadline=setTimeout(()=>{const stalledAt=latestStage;stage('hard_timeout',{stalledAt}); save('hard-timeout.json',{status:'INCOMPLETE',checks,stalledAt,transport_requests:calls.length,windows:app.isReady()?BrowserWindow.getAllWindows().map(w=>w.id):[]}); app.exit(124);},45000);
let error, hardCleanup=false;
try{
  stage('product_import_started');
  const {run}=await import(pathToFileURL(join(build,'main.mjs')).href);
  stage('product_import_completed');
  const options={state,task,userData:join(root,'ui')};
  stage('product_run_started');
  const first=await run({...options,launch:[launches[2],launches[1],launches[0]]});
  stage('product_run_completed',{window:first.id});
  const js=code=>first.webContents.executeJavaScript(code);
  const invoke=(operation,key,...args)=>js(`window.a2a[${JSON.stringify(operation)}](${[key,...args].map(v=>JSON.stringify(v)).join(',')})`);
  const keys=await js('[...window.a2a.paneKeys]');
  const snapshots=await Promise.all(keys.map(key=>invoke('snapshot',key)));
  check('same_window_three_launches',keys.length===3 && snapshots.every((s,i)=>s.launch.id===launches[i] && s.task.task_id===task));
  check('distinct_credentials',new Set(snapshots.map(s=>s.window_id)).size===3);
  let denied=false;try{await invoke('snapshot','unknown-'+randomUUID());}catch{denied=true;}
  check('unknown_key_refused',denied);
  for(let i=0;i<3;i++)await invoke('input',keys[i],'sentinel-'+i);
  const inputs=calls.filter(c=>c.command==='window_input');
  check('per_pane_sequence_and_target',inputs.length===3 && inputs.every((r,i)=>r.input.sequence===1 && r.window===snapshots[i].window_id && r.input.data==='sentinel-'+i));
  for(let i=0;i<3;i++)await invoke('releaseQueue',keys[i],{statement:'用户声明输入框已空',launch:launches[i],window_id:snapshots[i].window_id,interruption:7,input_generation:0});
  const releases=calls.filter(c=>c.command==='window_release');
  check('per_pane_release_declarations',releases.length===3 && releases.every((r,i)=>r.window===snapshots[i].window_id && r.input.declaration.window_id===r.window && r.input.declaration.launch===launches[i]));
  for(const invalid of ['stale','foreign']){
    const beforeWindows=BrowserWindow.getAllWindows().length,beforeOpened=calls.filter(c=>c.command==='window_open').length;
    let rejected=false;try{await run({...options,launch:[launches[0],launches[1],invalid]});}catch{rejected=true;}
    check('third_'+invalid+'_refused_before_window_and_credential',rejected && BrowserWindow.getAllWindows().length===beforeWindows && calls.filter(c=>c.command==='window_open').length===beforeOpened);
  }
  const second=await run({...options,launch:launches[0]});
  const otherKey=await second.webContents.executeJavaScript('window.a2a.paneKeys[0]');
  let cross=false;try{await invoke('snapshot',otherKey);}catch{cross=true;}
  check('other_window_key_refused',cross);
  save('snapshots.json',snapshots);
}catch(e){error={name:e.name,message:e.message,stack:e.stack};}
finally{
  for(const window of BrowserWindow.getAllWindows())window.close();
  const until=Date.now()+4000;
  while(BrowserWindow.getAllWindows().length && Date.now()<until)await new Promise(r=>setTimeout(r,25));
  if(BrowserWindow.getAllWindows().length){hardCleanup=true;for(const window of BrowserWindow.getAllWindows())window.destroy();}
  clearTimeout(deadline);server.close();
  const clean=!hardCleanup && credentials.size===0;
  save('result.json',{status:!error&&clean?'PASS':'INCOMPLETE',error,checks,cleanup_confirmed:clean,real_claude:0,real_codex:0,electron_processes:1,max_electron:1});
  finishing=true;
  app.exit(!error&&clean?0:1);
}


}
// Do not top-level await main(): Electron readiness requires entry evaluation to finish.
void main().catch(error=>{stage('harness_fatal',{error:String(error),stack:error.stack});app.exit(1);});
stage('entry_evaluation_complete');

T091_REVIEW_FILE_EOF
cat > "$review_tools/outside.py" <<'T091_REVIEW_FILE_EOF'
import datetime,io,json,os,pathlib,shutil,signal,subprocess,sys,tarfile,tempfile,time,traceback
REPO=pathlib.Path('/Users/luckye/Documents/Code/a2a-wt-t091')
SHA='e4dcb2739af449396a3c6982e9826326d64a4369'
VOLUME=pathlib.Path('/Volumes/WD-Elements')
assert os.path.ismount(VOLUME),'外置盘未挂载；停止，不回退'
store=VOLUME/'a2a-evidence/2026-10-16-batch16/T-091'
out=store/('review-outside-02-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(exist_ok=False)
tmp=pathlib.Path(tempfile.mkdtemp(prefix='t091-outside-02-',dir='/private/tmp')).resolve()
tools=pathlib.Path(__file__).parent
for name in ['outside.py','ui-entry.mjs']:shutil.copyfile(tools/name,out/name)
records=[];verdicts=[];failed=False;electron_attempts=0
env={k:os.environ[k] for k in ['PATH','USER','LOGNAME'] if k in os.environ}
for n in ['home','tmp']:(tmp/n).mkdir()
env.update(HOME=str(tmp/'home'),TMPDIR=str(tmp/'tmp'),LANG='en_US.UTF-8',LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
def save(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def ps(pid):
    p=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,lstart=,command='],capture_output=True,text=True,timeout=5)
    return (p.returncode,p.stdout.strip(),p.stderr.strip())
def run(name,argv,limit,cwd):
    folder=out/name;folder.mkdir(exist_ok=False)
    print('段名='+name+' 输出目录='+str(folder),flush=True)
    args=list(map(str,argv));start=time.monotonic();row=dict(name=name,argv=args,cwd=str(cwd),timeout_seconds=limit)
    with (folder/'stdout.txt').open('xb') as o,(folder/'stderr.txt').open('xb') as e:
        process=subprocess.Popen(args,cwd=cwd,env=env,stdout=o,stderr=e,start_new_session=True)
        owner=ps(process.pid);row.update(pid=process.pid,owner=owner)
        deadline=time.monotonic()+limit
        while process.poll() is None:
            if time.monotonic()>deadline or o.tell()+e.tell()>32*1024*1024:
                row['hard_timeout_or_output_limit']=True
                if ps(process.pid)==owner and os.getpgid(process.pid)==process.pid:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=3)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL)
                else:raise RuntimeError('无法核对超时子进程身份；停止后续运行')
                break
            time.sleep(.1)
        row.update(exit=process.wait(timeout=8),elapsed_seconds=round(time.monotonic()-start,3))
    records.append(row);save(folder/'command.json',row)
    print('退出码='+str(row['exit']),flush=True)
    return row,folder
def live_electron(executable):
    text=subprocess.check_output(['/bin/ps','-axo','pid=,command='],text=True,timeout=5)
    return [line.strip() for line in text.splitlines() if line.strip() and line.strip().split(maxsplit=1)[-1].startswith(executable)]
try:
    save(out/'identity.json',dict(candidate=SHA,repository=str(REPO),temporary=str(tmp),prior_run=str(store/'review-outside-01-20261017T160603Z'),repair='入口从顶层 await 改为未等待的 async main，先同步设置隔离路径；增加阶段日志；原断言和 45s/65s 硬期限不改。',real_claude_starts=0,real_codex_starts=0,daemon_starts=0,pty_starts=0,model_calls=0,electron_total_budget=3,electron_peak_budget=1,reviewer_sessions_opened=0))
    candidate=tmp/'candidate';candidate.mkdir()
    archive=subprocess.check_output(['git','archive',SHA,'workbench'],cwd=REPO,timeout=30)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():assert not member.name.startswith('/') and '..' not in pathlib.PurePosixPath(member.name).parts
        tar.extractall(candidate)
    (candidate/'workbench/node_modules').symlink_to(REPO/'workbench/node_modules',target_is_directory=True)
    edits=[('m1-key','workbench/app/main.ts',"const pane = typeof key === 'string' ? context.panes.get(key) : undefined;","const pane = context.panes.values().next().value;"),('m2-preflight','workbench/app/main.ts','      requireCurrentPane(options.task, launch!, value);','      // independent review mutant: omit selection check')]
    mutants=[]
    for label,file,before,after in edits:
        dest=tmp/label;shutil.copytree(candidate,dest,symlinks=True)
        f=dest/file;s=f.read_text(encoding='utf-8');assert s.count(before)==1;f.write_text(s.replace(before,after),encoding='utf-8')
        mutants.append(dict(name=label,path=str(dest),file=file,before=before,after=after))
    save(out/'mutations.json',mutants)
    executable=subprocess.check_output(['node','--input-type=module','-e',"import{createRequire}from'node:module';console.log(createRequire(process.argv[1])('electron'))",str(REPO/'workbench/package.json')],env=env,text=True,timeout=10).strip()
    for label,source in [('candidate-ui',candidate),('m1-key',tmp/'m1-key'),('m2-preflight',tmp/'m2-preflight')]:
        active=live_electron(executable)
        if active:save(out/'preexisting-electron.json',active);raise RuntimeError('已有相同 Electron executable 在运行；不并发启动')
        slot='r091-02-'+tmp.name.rsplit('-',1)[-1]+'-'+label
        row,folder=run(label+'-build',['node',source/'workbench/app/build.mjs','--slot',slot],180,source)
        if row['exit']:raise RuntimeError('标准构建失败；保留输出并停止 Electron 段')
        lines=(folder/'stdout.txt').read_text(encoding='utf-8').splitlines();build=json.loads(lines[-1])['out']
        result=out/(label+'-results');result.mkdir()
        electron_attempts+=1
        row,_=run(label,[executable,tools/'ui-entry.mjs',build,result],65,source)
        alive=live_electron(executable);save(result/'after-processes.json',dict(remaining=alive,exit_confirmed=not alive))
        data=json.loads((result/'result.json').read_text(encoding='utf-8')) if (result/'result.json').exists() else {}
        if label=='candidate-ui':
            passed=row['exit']==0 and data.get('status')=='PASS' and len(data.get('checks',[]))==8 and all(r['pass'] is True for r in data['checks'])
            verdicts.append(dict(name=label,candidate_passed=passed))
            if not passed:raise RuntimeError('候选真实 UI 入口未通过；不执行 UI 变异')
        else:
            expected='unknown_key_refused' if label=='m1-key' else 'third_stale_refused_before_window_and_credential'
            killed=row['exit']==1 and (data.get('error') or {}).get('message')==expected and data.get('cleanup_confirmed') is True and not alive
            verdict=dict(name=label,expected_assertion=expected,rejected_by_business_assertion=killed)
            save(result/'mutation-verdict.json',verdict);verdicts.append(verdict);failed|=not killed
        if not data.get('cleanup_confirmed') or alive:raise RuntimeError('Electron 收尾未确认；停止后续实例')
except Exception as e:
    failed=True;save(out/'error.json',dict(error=repr(e),traceback=traceback.format_exc()))
finally:
    save(out/'summary.json',dict(status='INCOMPLETE' if failed else 'PASS',candidate=SHA,output=str(out),temporary=str(tmp),commands=records,verdicts=verdicts,electron_attempts=electron_attempts,real_claude=0,real_codex=0,daemon=0,pty=0,model_calls=0,note='独立真实 Electron/IPC/transport 入口；socket 对端为夹具。仅补 OUTSIDE-01 未执行的 UI 两个变异，版本与归档证据不重跑。'))
    print('OUTPUT='+str(out),flush=True);print('TEMP='+str(tmp),flush=True);print('EXIT='+str(1 if failed else 0),flush=True)
sys.exit(1 if failed else 0)

T091_REVIEW_FILE_EOF
python3 "$review_tools/outside.py"
review_exit=$?
printf "OUTSIDE-02 退出码=%s\n" "$review_exit"
exit "$review_exit"
