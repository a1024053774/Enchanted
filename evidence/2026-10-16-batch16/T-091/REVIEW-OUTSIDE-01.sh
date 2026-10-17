#!/bin/bash
# T-091 fresh-context 独立审查。只由执行主控运行，不请求沙箱升级。
# 冻结候选 e4dcb2739af449396a3c6982e9826326d64a4369；不修改 checkout。
# 新 git archive 副本位于 /private/tmp；原证据只读，不重开历史 WAL 库。
# 输出只写外置盘 T-091 下全新 review-outside-01-* 目录；无盘即报错。
# 预算：真实 Claude=0、真实 Codex=0、模型 API=0、新 agent=0。
# Electron 总计最多 3 次串行、同时最多 1 个进程实例；不采集新屏幕。
# 候选 UI 的第二个隔离 BrowserWindow 只检验跨窗口 key，仍属同一 Electron。
# CLI 版本检查只运行自编译 C 夹具；正例最多 2 个受控 PTY，变异最多 1 个。
# daemon 为生产 serve，测试宿主提供 task status；不证明真实门禁或模型。
# 不运行会做夹具 commit/submit/integration 的计时套件；缺口保持 INCOMPLETE。
# 每段保留 argv/退出码/耗时/stdout/stderr，单命令硬期限与 32MiB 上限。
# 服务正常收尾；硬期限只信号本脚本拥有且身份仍一致的子进程/测试服务。
# 不 checkout、reset、commit、submit、push，不改全局设置，不操作用户应用。
set -uo pipefail
review_tools=$(mktemp -d /private/tmp/t091-review-tools-01-XXXXXX)
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
const root = mkdtempSync('/private/tmp/t091-ui-');
const state = join(root, 's'); mkdirSync(state);
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
await new Promise(resolve=>server.listen(join(state,'control.sock'),resolve));
const deadline=setTimeout(()=>{save('hard-timeout.json',{status:'INCOMPLETE',checks}); app.exit(124);},45000);
let error, hardCleanup=false;
try{
  const {run}=await import(pathToFileURL(join(build,'main.mjs')).href);
  const options={state,task,userData:join(root,'ui')};
  const first=await run({...options,launch:[launches[2],launches[1],launches[0]]});
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

T091_REVIEW_FILE_EOF
cat > "$review_tools/version-entry.py" <<'T091_REVIEW_FILE_EOF'
"""真实 CLI→daemon→startController→exec/PTY；注入任务状态，只运行自编译 C 夹具。"""
import json,os,pathlib,subprocess,sys,tempfile,time,uuid,traceback
source,out=map(pathlib.Path,sys.argv[1:3])
root=pathlib.Path(tempfile.mkdtemp(prefix='t078-2-review-',dir='/private/tmp')).resolve()
for n in ['repo','state','home','tmp','roles/ideation','roles/executor']:(root/n).mkdir(parents=True,exist_ok=True)
env={k:os.environ[k] for k in ['PATH','USER','LOGNAME'] if k in os.environ}
env.update(HOME=str(root/'home'),TMPDIR=str(root/'tmp'),LANG='en_US.UTF-8',LC_ALL='C',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,A2A_OPERATOR_CREDENTIAL=str(root/'operator.json'),GIT_AUTHOR_NAME='Review fixture',GIT_AUTHOR_EMAIL='review@example.invalid',GIT_COMMITTER_NAME='Review fixture',GIT_COMMITTER_EMAIL='review@example.invalid')
log=[];checks=[];started=False;failure=None;pid=None;owned=[];host_process=None
def save(name,data):
    with (out/name).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
def run(argv,limit=20):
    argv=list(map(str,argv));t=time.monotonic();i=len(log)
    with (out/('%03d.stdout'%i)).open('xb') as o,(out/('%03d.stderr'%i)).open('xb') as e:
        p=subprocess.run(argv,cwd=source,env=env,stdout=o,stderr=e,timeout=limit,start_new_session=True)
    row=dict(argv=argv,exit=p.returncode,elapsed=time.monotonic()-t);log.append(row)
    (out/'commands.ndjson').open('a',encoding='utf-8').write(json.dumps(row)+'\n')
    return p.returncode,(out/('%03d.stdout'%i)).read_text(encoding='utf-8')
cli=['node',source/'workbench/src/gates/cli.ts','--state',root/'state']
def call(command,*args):
    rc,text=run([*cli,command,*args]);return rc,json.loads(text)
def good(command,*args):
    rc,value=call(command,*args);assert rc==0 and value['ok'],(command,rc,value);return value
def check(name,value):
    checks.append(dict(name=name,pass_value=bool(value)));assert value,name
save('fixture-start.json',dict(root=str(root)))
try:
    c=root/'fixture.c';c.write_text('#include <stdio.h>\n#include <string.h>\n#include <unistd.h>\nint main(int c,char**v){if(c==2&&!strcmp(v[1],"--version")){puts("2.1.302 (Claude Code)");return 0;}puts("REVIEW_C_FIXTURE_NO_MODEL");fflush(stdout);for(;;)pause();}\n',encoding='utf-8')
    executable=root/'fixture-cli';assert run(['/usr/bin/clang','-Wall','-Werror',c,'-o',executable])[0]==0
    task='review-'+uuid.uuid4().hex
    gate_task=dict(task_id=task,project_id='review',repo=str(root/'repo'),spec_rev=1,base_commit='0'*40,current_attempt=None)
    host=root/'version-host.mjs'
    host.write_text("import {serve} from "+json.dumps((source/'workbench/src/daemon.ts').as_uri())+";\nimport {createOperatorCredential} from "+json.dumps((source/'workbench/src/credentials.ts').as_uri())+";\nimport{writeFileSync}from'node:fs';\nconst root="+json.dumps(str(root/'state'))+";const task="+json.dumps(gate_task)+";\ncreateOperatorCredential(root);\nawait serve(root,{},()=>({setUserInputObserverStatus(){},recoverReviews(){},registerController(){},async resumeControllerInbox(){},beginShutdown(){},close(){},async call(q){if(q.command!=='status'||q.task!==task.task_id)throw Error('outside version scope');return {ok:true,task};}}));\nwriteFileSync("+json.dumps(str(root/'ready.json'))+",JSON.stringify({pid:process.pid}));\n",encoding='utf-8')
    host_stdout=(out/'host.stdout').open('xb');host_stderr=(out/'host.stderr').open('xb')
    host_argv=['node',str(host),str(source),str(root/'state')]
    host_process=subprocess.Popen(host_argv,env=env,stdout=host_stdout,stderr=host_stderr,start_new_session=True)
    pid=host_process.pid;started=True
    deadline=time.monotonic()+12
    while not (root/'ready.json').exists():
        assert host_process.poll() is None,'version_host_exited_before_ready'
        assert time.monotonic()<deadline,'version_host_ready_timeout'
        time.sleep(.1)
    save('host.json',dict(argv=host_argv,pid=pid,task_state=gate_task,boundary='真实生产 daemon，门禁 status/注册/恢复为测试宿主提供，不证明门禁任务生命周期'))
    for preset in ['ideation','executor']:
        folder=root/'roles'/preset
        for d in ['home','claude','tmp','shell','requests','hooks','user-data']:(folder/d).mkdir()
        (folder/'role.md').write_text('受控 C 夹具，不运行任何模型。\n',encoding='utf-8')
    base=dict(schema=1,root=str(root),state=str(root/'state'),task=task,preset='ideation',launch=str(uuid.uuid4()),session=str(uuid.uuid4()),thread=str(uuid.uuid4()),executable=str(executable),version='2.1.302',role_file=str(root/'roles/ideation/role.md'),code_revision='e4dcb2739af449396a3c6982e9826326d64a4369',source_snapshot=str(source),api_url='http://127.0.0.1:23456/',turn_limit=1)
    for name,change,expected in [('missing',dict(executable=str(root/'missing-cli')),'controller_executable_missing'),('mismatch',dict(version='8.7.6'),'controller_version_mismatch')]:
        path=root/(name+'.json');path.write_text(json.dumps(dict(base,**change)),encoding='utf-8')
        before=good('orchestration_events')['events']
        rc,value=call('controller_start','--task',task,'--manifest',path);save(name+'.json',value)
        check(name+'_refused',rc==1 and value.get('ok') is False and value.get('error')==expected)
        after=good('orchestration_events')['events']
        check(name+'_before_launch_and_pty',len([r for r in before if r['type']=='pane_started'])==len([r for r in after if r['type']=='pane_started']))
    for preset in ['ideation','executor']:
        manifest=dict(base,preset=preset,role_file=str(root/'roles'/preset/'role.md'),launch=str(uuid.uuid4()),session=str(uuid.uuid4()),thread=str(uuid.uuid4()))
        path=root/(preset+'.json');path.write_text(json.dumps(manifest),encoding='utf-8')
        value=good('controller_start','--task',task,'--manifest',path);save(preset+'.json',value)
        record=value['launch'];check(preset+'_configured_version',record['cli_version']==record['cli_version_expected']=='2.1.302 (Claude Code)' and record['version_probe']['argv']==[str(executable),'--version'] and record['env'].get('DISABLE_AUTOUPDATER') is None)
    save('events.json',good('orchestration_events'))
except Exception as e:failure=dict(error=repr(e),traceback=traceback.format_exc())
finally:
    cleanup=False
    if started:
        try:
            # 正常关停只针对本夹具 daemon；不触碰其他实例。
            save('before-stop.json',good('daemon_status'));good('daemon_stop')
            if host_process is not None:host_process.wait(timeout=12)
            end=time.monotonic()+12
            while time.monotonic()<end:
                p=subprocess.run(['/bin/ps','-p',str(pid),'-o','pid=,command='],capture_output=True,text=True,timeout=4)
                if p.returncode==1 and not p.stdout.strip():cleanup=True;break
                time.sleep(.1)
        except Exception as e:
            failure=dict(previous=failure,cleanup_error=repr(e))
            if host_process is not None and host_process.poll() is None:
                host_process.terminate()
                try:host_process.wait(timeout=3)
                except subprocess.TimeoutExpired:host_process.kill();host_process.wait(timeout=3)
    else:cleanup=True
    save('result.json',dict(status='PASS' if failure is None and cleanup else 'INCOMPLETE',checks=checks,failure=failure,cleanup_confirmed=cleanup,fixture=str(root),daemon_pid=pid,real_claude=0,real_codex=0,electron=0,commands=log,boundary='真实 daemon/auth/controller_start/exec/PTY；任务状态由独立宿主注入，无 Git 或任务门禁状态变更'))
sys.exit(0 if failure is None and cleanup else 1)

T091_REVIEW_FILE_EOF
cat > "$review_tools/archive-audit.py" <<'T091_REVIEW_FILE_EOF'
"""只读核对已归档的真实边界；结果值来自 ticket 与原始独立输入。"""
import base64,json,pathlib,sys,struct,shutil,traceback
base,out,tmp=map(pathlib.Path,sys.argv[1:4]);green=base/'green-02'
checks=[];materials={};errors=[]
def read(path):
    value=json.loads(path.read_text(encoding='utf-8'));materials[str(path)]=value;return value
def check(name,value):checks.append(dict(name=name,pass_value=bool(value)))
try:
    expected=read(green/'expected.json');panes=expected['panes'];task=expected['task']
    check('expected_roles',[(r['role'],r['preset']) for r in panes]==[('controller','ideation'),('controller','executor'),('worker',None)])
    for row in panes:
        label=row['preset'] or 'worker';snap=read(green/(label+'.snapshot.json'));proc=read(green/(label+'.process.json'))
        check(label+'_snapshot',snap['task']['task_id']==task and all(snap['launch'][k]==row['launch' if k=='id' else k] for k in ['id','task','role','preset','thread','attempt','session']))
        check(label+'_process',proc['leader']==row['leader'] and proc['native_session']==row['session'] and not proc.get('failed') and proc['shell_pid']!=proc['leader'])
        leaders=[p for p in proc['processes'] if p['pid']==proc['leader']]
        check(label+'_foreground_group',len(leaders)==1 and leaders[0]['pid']==leaders[0]['pgid']==leaders[0]['tpgid'] and any(p['pid']==proc['shell_pid'] for p in proc['processes']))
        if label!='worker':
            record=read(green/(label+'.launch.json'))
            check(label+'_real_version',record['cli_version']==record['cli_version_expected']=='2.1.302 (Claude Code)' and record['version_probe']['argv']==[record['argv'][0],'--version'] and record['version_probe']['stdout'].strip()=='2.1.302 (Claude Code)' and 'DISABLE_AUTOUPDATER' not in record['env'])
            check(label+'_executable_identity',leaders[0]['command']==record['argv'][0])
    original=read(green/'view-initial.json');ids=[r['window_id'] for r in original['panes']]
    check('distinct_window_ids',len(set(ids))==3)
    for path in sorted(green.glob('view-*.json')):
        v=read(path)
        if 'panes' not in v:continue
        check(path.name+'_same_bindings',[r['launch'] for r in v['panes']]==[r['launch'] for r in panes] and [r['window_id'] for r in v['panes']]==ids)
        if 'viewport' in v:
            w,h=v['viewport']['width'],v['viewport']['height']
            check(path.name+'_all_visible',len(v['panes'])==3 and all(r['bounds']['width']>0 and r['bounds']['height']>0 and r['bounds']['x']>=0 and r['bounds']['y']>=0 and r['bounds']['x']+r['bounds']['width']<=w+.1 and r['bounds']['y']+r['bounds']['height']<=h+.1 and r['terminal_bounds']['height']>0 for r in v['panes']))
    for name,reason in [('wrong-task','Error: launch_task_mismatch'),('old-launch','Error: Pane is not a current running session')]:
        r=read(green/(name+'.refusal.json'));check(name+'_prewindow',r['rejected'] and r['error']==reason and r['windows_before']==r['windows_after'] and len(r['windows_before'])==1)
    events=read(green/'orchestration-before-close.json');opened=[r for r in events if r['type']=='window_opened']
    check('only_three_credentials',len(opened)==3)
    after=read(green/'orchestration-after-window.json')
    check('three_credentials_revoked',sorted(r['data']['window_id'] for r in after if r['type']=='window_closed')==sorted(ids))
    chunks=[json.loads(line) for line in (green/'window/received.ndjson').read_text(encoding='utf-8').splitlines()]
    nonce=read(green/'output-oracle.json')['nonce']
    for row in panes:
        label=row['preset'] or 'worker';raw=(green/(label+'.first-screen.bin')).read_bytes()
        stream=b''.join(base64.b64decode(r['data_base64']) for r in chunks if r['launch']==row['launch'])
        check(label+'_own_stream',stream.startswith(raw) and (nonce.encode() in raw)==(label=='worker'))
    for label,window in zip(['ideation','executor','worker'],ids):
        requests=[r['data'] for r in events if r['type']=='window_request_admitted' and r['data']['window_id']==window]
        check(label+'_sequence',[r['sequence'] for r in requests]==list(range(1,len(requests)+1)) and len(requests)>=2)
    for name,reason in [('missing-cli','controller_executable_missing'),('version-mismatch','controller_version_mismatch')]:
        r=read(green/(name+'.refusal.json'));check(name,r.get('ok') is False and r['error']==reason)
    captures=[]
    for p in sorted(green.glob('*.capture.json')):
        r=read(p);captures.append(r)
        q=pathlib.Path(r['original_single_frame']);raw=q.read_bytes();size=struct.unpack('>II',raw[16:24])
        check(p.name+'_native_single_window',raw[:8]==b'\x89PNG\r\n\x1a\n' and list(size)==r['pixels'] and '-l' in r['argv'] and r['argv'][r['argv'].index('-l')+1]==str(r['owner']['window_number']))
        shutil.copyfile(q,tmp/q.name)
    check('three_raw_frames',len(captures)==3)
    for name in ['owned-processes.json','electron-command.json','old.snapshot.json','input-records.json','input-oracle.json','output-oracle.json']:
        read(green/name)
    red=base/'red-02'
    for name in ['expected.json','view.json','capture.json']:
        if (red/name).exists():read(red/name)
    if (red/'baseline-original.png').exists():shutil.copyfile(red/'baseline-original.png',tmp/'baseline-original.png')
    regression=[]
    for case,count in [('window-regression-02',4),('runtime-regression-02',12),('input-failures-regression-02',11),('worker-inbox-regression-02',14)]:
        name='verdict.json' if case.startswith('window') else 'results.json'
        r=read(base/case/'original-test'/name)
        check(case+'_original_assertions',r.get('status')=='PASS' and len(r['checks'])==count and all(c['status']=='PASS' for c in r['checks']))
        if not case.startswith('window'):check(case+'_cleanup',r.get('cleanup_complete') is True)
    core=base/'core-regression-04'
    classifier=read(core/'classifier-preflight.json')
    check('core_classifier_preflight',classifier.get('status')=='PASS' and classifier.get('known_bad',{}).get('rejected') is True and classifier.get('weak_classifier_mutant',{}).get('rejected') is True)
    for suite,count in [('coop',8),('recovery',9),('run',18),('cas',1)]:
        r=read(core/suite/'run.json')
        check('core_'+suite,r.get('status')=='PASS' and r.get('tests_run')==count and r.get('failures')==r.get('errors')==r.get('skipped')==0)
    for name in ['fence','cas','lock']:
        r=read(core/('mutant-'+name)/'run.json')
        check('core_mutant_'+name+'_assertion_failure',r.get('exit_code')==1 and r.get('tests_run')==1 and r.get('failures')==1 and r.get('errors')==r.get('skipped')==0 and bool(r.get('failure_text')))
        if name=='fence':
            attempts=[json.loads(c['stdout'])['attempt'] for c in r['commands'] if c.get('label')=='coop:claim' and c.get('exit_code')==0]
            wrong_accepted=False
            for c in r['commands']:
                if c.get('label')!='coop:submit' or c.get('exit_code')!=0:continue
                argv=c['argv'];reply=json.loads(c['stdout'])
                if '--fence' in argv and '--session' in argv:
                    wrong_accepted|=reply.get('ok') is True and any(int(argv[argv.index('--fence')+1])==a['fence']+31 and argv[argv.index('--session')+1]==a['session_id'] for a in attempts)
            check('fence_wrong_generation_accepted',wrong_accepted)
        if name=='lock':
            check('lock_actual_contract_violated',any(a.get('pass') is False and a['claim'] in ['Live operation excludes concurrent verify','Live operation excludes concurrent integrate','Busy commands never start a second oracle'] for a in r['assertions']))
        if name=='cas':
            claims=[a for a in r['assertions'] if a.get('pass') is False]
            check('cas_all_three_violations',any(a['claim']=='CAS revalidation binds the new G and unchanged C' for a in claims) and any(a['claim'].startswith('CAS integration preserves ancestor ') for a in claims) and any(a['claim']=='CAS revalidation executes the oracle again' for a in claims))
    for case in ['window-regression-02','runtime-regression-02','input-failures-regression-02','worker-inbox-regression-02','core-regression-04']:
        folder=base/case
        # 不进入 fixture，不重开已停止的 WAL 库，不跟随归档符号链接。
        files=list(folder.glob('*/run.json'))+list(folder.glob('*.business-counterexample.json'))+list(folder.glob('run.json'))
        for p in files:
            if p.parent.name.startswith('fixture'):continue
            r=read(p)
            regression.append(dict(file=str(p),status=r.get('status'),exit=r.get('exit_code',r.get('exit')),tests=r.get('tests_run'),failures=r.get('failures'),errors=r.get('errors'),skipped=r.get('skipped'),checks=r.get('checks'),business=r.get('business_evidence'),contract=r.get('contract_checks')))
    materials['regression_index']=regression
    materials['green_top_files']=[p.name for p in sorted(green.iterdir())]
except Exception as e:errors.append(dict(error=repr(e),traceback=traceback.format_exc()))
for name,value in [('materials.json',materials),('result.json',dict(status='PASS' if not errors and all(c['pass_value'] for c in checks) else 'INCOMPLETE',checks=checks,errors=errors,original_frame_copies=str(tmp),note='自动结构核对不替代原帧视觉审查；历史进程身份不作今天存活证明。'))]:
    with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
sys.exit(0 if not errors and all(c['pass_value'] for c in checks) else 1)

T091_REVIEW_FILE_EOF
cat > "$review_tools/outside.py" <<'T091_REVIEW_FILE_EOF'
import datetime,io,json,os,pathlib,shutil,signal,subprocess,sys,tarfile,tempfile,time,traceback
REPO=pathlib.Path('/Users/luckye/Documents/Code/a2a-wt-t091')
SHA='e4dcb2739af449396a3c6982e9826326d64a4369'
BASE='44bbb7828459d81fab0d46069a19d3dd515a7732'
VOLUME=pathlib.Path('/Volumes/WD-Elements')
assert os.path.ismount(VOLUME),'外置盘未挂载；停止，不回退'
store=VOLUME/'a2a-evidence/2026-10-16-batch16/T-091'
out=store/('review-outside-01-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(exist_ok=False)
tmp=pathlib.Path(tempfile.mkdtemp(prefix='t091-outside-01-',dir='/private/tmp')).resolve()
tools=pathlib.Path(__file__).parent
for p in tools.iterdir():
    if p.suffix in ['.py','.mjs']:shutil.copyfile(p,out/p.name)
records=[];failed=False;cleanup_failed=False
env={k:os.environ[k] for k in ['PATH','USER','LOGNAME'] if k in os.environ}
for n in ['home','tmp']:(tmp/n).mkdir()
env.update(HOME=str(tmp/'home'),TMPDIR=str(tmp/'tmp'),LANG='en_US.UTF-8',LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
def save(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def ps(pid):
    p=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,lstart=,command='],capture_output=True,text=True,timeout=5)
    return (p.returncode,p.stdout.strip(),p.stderr.strip())
def run(name,argv,limit=60,cwd=REPO):
    global failed
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
def extract(revision,dest):
    dest.mkdir()
    data=subprocess.check_output(['git','archive',revision,'workbench','acceptance','fixtures'],cwd=REPO,timeout=30)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():assert not member.name.startswith('/') and '..' not in pathlib.PurePosixPath(member.name).parts
        archive.extractall(dest)
    (dest/'workbench/node_modules').symlink_to(REPO/'workbench/node_modules',target_is_directory=True)
def cleanup_daemons(folder,source):
    global cleanup_failed
    start=folder/'fixture-start.json'
    if not start.exists():return
    root=pathlib.Path(json.loads(start.read_text(encoding='utf-8'))['root'])
    assert str(root).startswith(('/private/tmp/t078-2-review-','/private/tmp/r91t-'))
    for path in root.rglob('daemon.pid'):
        pid=int(path.read_text(encoding='utf-8').strip());identity=ps(pid)
        if identity[0]==1:continue
        if identity[0]!=0 or str(source) not in identity[1] or str(path.parent) not in identity[1]:
            cleanup_failed=True;continue
        found=None
        for credential in [root/'operator.json',*root.rglob('*.credential.json')]:
            if credential.is_file():
                try:v=json.loads(credential.read_text(encoding='utf-8'))
                except ValueError:continue
                if v.get('state')==str(path.parent):found=credential;break
        if found:
            stop_env=dict(env,A2A_OPERATOR_CREDENTIAL=str(found))
            with (folder/('cleanup-'+str(pid)+'.txt')).open('x',encoding='utf-8') as f:
                try:subprocess.run(['node',str(source/'workbench/src/gates/cli.ts'),'--state',str(path.parent),'daemon_stop'],env=stop_env,stdout=f,stderr=f,timeout=15)
                except subprocess.TimeoutExpired:f.write('正常关停期限已到\n')
        end=time.monotonic()+10
        while ps(pid)[0]==0 and time.monotonic()<end:time.sleep(.1)
        if ps(pid)[0]==0 and ps(pid)==identity:
            # 只处理本脚本新建、source/state/启动时间均匹配的测试服务。
            os.kill(pid,signal.SIGTERM);time.sleep(.5)
        if ps(pid)[0]==0:cleanup_failed=True
try:
    save(out/'identity.json',dict(candidate=SHA,baseline=BASE,repository=str(REPO),temporary=str(tmp),original_frames_copy=str(tmp/'original-frames'),real_claude_starts=0,real_codex_starts=0,model_calls=0,electron_total_budget=3,electron_peak_budget=1,reviewer_sessions_opened=0))
    # 源码一律从冻结 commit 解包；没有 Git worktree，也没有 checkout/reset。
    candidate=tmp/'candidate';extract(SHA,candidate)
    baseline=tmp/'baseline';extract(BASE,baseline)
    mutants=[]
    edits=[('m1-key','workbench/app/main.ts',"const pane = typeof key === 'string' ? context.panes.get(key) : undefined;","const pane = context.panes.values().next().value;"),('m2-preflight','workbench/app/main.ts','      requireCurrentPane(options.task, launch!, value);','      // independent review mutant: omit selection check'),('m3-version','workbench/src/panes.ts','if (version !== expectedVersion) throw new Refusal("controller_version_mismatch", { expected: expectedVersion, observed: version });','// independent review mutant: omit version comparison')]
    for label,file,before,after in edits:
        dest=tmp/label;shutil.copytree(candidate,dest,symlinks=True);f=dest/file;s=f.read_text(encoding='utf-8');assert s.count(before)==1;f.write_text(s.replace(before,after),encoding='utf-8');mutants.append(dict(name=label,path=str(dest),file=file,before=before,after=after))
    save(out/'mutations.json',mutants)
    frames=tmp/'original-frames';frames.mkdir()
    audit=out/'archive-materials';audit.mkdir()
    row,_=run('归档证据核对',['python3',tools/'archive-audit.py',store,audit,frames],60)
    failed|=row['exit']!=0
    for label,source in [('candidate-version',candidate),('m3-version',tmp/'m3-version')]:
        result=out/(label+'-results');result.mkdir()
        row,folder=run(label,['python3',tools/'version-entry.py',source,result],120)
        cleanup_daemons(result,source)
        if label=='candidate-version':
            version_good=row['exit']==0;failed|=not version_good
        else:
            data=json.loads((result/'result.json').read_text(encoding='utf-8')) if (result/'result.json').exists() else {}
            killed=row['exit']==1 and data.get('failure',{}).get('error')=="AssertionError('mismatch_refused')" and data.get('cleanup_confirmed') is True
            save(result/'mutation-verdict.json',dict(rejected_by_business_assertion=killed))
            failed|=not killed
        if cleanup_failed:raise RuntimeError('daemon 收尾未确认；停止后续运行')
        if label=='candidate-version' and not version_good:raise RuntimeError('候选版本入口未通过；不执行后续变异')
    # 原计时套件会做夹具 commit/submit/integrate；本次禁止，缺口照实保留。
    save(out/'timing-not-run.json',dict(status='INCOMPLETE',baseline_same_method_executed=False,reason='本次只读审查明确禁止 commit/submit/integration，未执行会触发这些动作的原方法；缺计时不能补称 PASS。'))
    executable=subprocess.check_output(['node','--input-type=module','-e',"import{createRequire}from'node:module';console.log(createRequire(process.argv[1])('electron'))",str(REPO/'workbench/package.json')],env=env,text=True,timeout=10).strip()
    for label,source in [('candidate-ui',candidate),('m1-key',tmp/'m1-key'),('m2-preflight',tmp/'m2-preflight')]:
        active=subprocess.check_output(['/bin/ps','-axo','pid=,command='],text=True,timeout=5)
        if any(line.strip().split(maxsplit=1)[-1].startswith(executable) for line in active.splitlines() if line.strip()):raise RuntimeError('已有同一 Electron executable 在运行；不并发启动')
        slot='r091-'+tmp.name.rsplit('-',1)[-1]+'-'+label
        row,folder=run(label+'-build',['node',source/'workbench/app/build.mjs','--slot',slot],180,cwd=source)
        if row['exit']:raise RuntimeError('标准构建失败；保留输出并停止 Electron 段')
        lines=(folder/'stdout.txt').read_text(encoding='utf-8').splitlines();build=json.loads(lines[-1])['out']
        result=out/(label+'-results');result.mkdir()
        row,_=run(label,[executable,tools/'ui-entry.mjs',build,result],65,cwd=source)
        data=json.loads((result/'result.json').read_text(encoding='utf-8')) if (result/'result.json').exists() else {}
        if label=='candidate-ui':
            failed|=row['exit']!=0
            if row['exit']!=0:raise RuntimeError('候选真实 UI 入口未通过；不执行 UI 变异')
        else:
            expected='unknown_key_refused' if label=='m1-key' else 'third_stale_refused_before_window_and_credential'
            killed=row['exit']==1 and data.get('error',{}).get('message')==expected and data.get('cleanup_confirmed') is True
            save(result/'mutation-verdict.json',dict(expected_assertion=expected,rejected_by_business_assertion=killed));failed|=not killed
        if not data.get('cleanup_confirmed'):raise RuntimeError('Electron 收尾未确认；停止后续实例')
except Exception as e:
    failed=True;save(out/'error.json',dict(error=repr(e),traceback=traceback.format_exc()))
finally:
    save(out/'summary.json',dict(status='INCOMPLETE' if failed or cleanup_failed else 'PASS',candidate=SHA,output=str(out),temporary=str(tmp),cleanup_failed=cleanup_failed,commands=records,note='PASS 仅指脚本预设检查；审查总判断待原帧视觉核对与计时证据解释。变异通过须命中业务断言，未把环境错误算作杀死。'))
    print('OUTPUT='+str(out),flush=True);print('TEMP='+str(tmp),flush=True);print('EXIT='+str(1 if failed or cleanup_failed else 0),flush=True)
sys.exit(1 if failed or cleanup_failed else 0)

T091_REVIEW_FILE_EOF
python3 "$review_tools/outside.py"
review_exit=$?
printf "OUTSIDE-01 退出码=%s\n" "$review_exit"
exit "$review_exit"
