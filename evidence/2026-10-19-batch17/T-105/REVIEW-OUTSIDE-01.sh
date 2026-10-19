#!/bin/bash
# T-105 第一轮独立审查复验；执行主控在沙箱外运行，默认含真实 Electron。
# 仅写新的 /private/tmp 目录；冻结候选用 git archive，不建 worktree，不调用模型。
# --isolated-only 只运行隔离检查和三个单处变异。
# --chooser 另补原生目录选择（不重复三场 Electron）；默认 --electron 全部运行。
# 出现“目录选择待操作”后，执行主控只操作本脚本启动的 Electron 原生目录对话框，
# 选择打印的隔离目录；不需要系统设置、登录、密码或截图。取消或超时记 INCOMPLETE。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t105
python3 - "$@" <<'PY_REVIEW'
import json, os, pathlib, shutil, subprocess, sys, tempfile
REPO=pathlib.Path.cwd()
REV='395492c8fea315c3f2419699d890fd8292e3fed4'
BASE='37c8a9e77c7c0a0e7426accbec077f0e33946bf4'
assert sys.argv[1:] in ([], ['--electron'], ['--chooser'], ['--isolated-only'])
ELECTRON=sys.argv[1:] != ['--isolated-only']
FULL_ELECTRON=sys.argv[1:] in ([], ['--electron'])
DEPENDENCIES_SAFE=True
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='t105-independent-r01-',dir='/private/tmp'))
print('审查原件目录：'+str(ROOT),flush=True)
ISOLATED_JS='// 独立审查：真实 daemon 请求处理、Panes 和 SQLite；socket/PTY 为可控边界。\nimport vm from \'node:vm\';\nimport { stripTypeScriptTypes } from \'node:module\';\nimport { EventEmitter } from \'node:events\';\nimport { readFileSync, writeFileSync, mkdirSync } from \'node:fs\';\nimport { join, resolve } from \'node:path\';\nimport { pathToFileURL } from \'node:url\';\nimport { randomUUID } from \'node:crypto\';\nimport assert from \'node:assert/strict\';\nconst [sourceArg, output, scenario=\'all\'] = process.argv.slice(2);\nconst source=resolve(sourceArg), root=join(output,\'state\'); mkdirSync(root,{recursive:true});\nconst report={status:\'INCOMPLETE\',scenario,source,argv:process.argv,checks:[],boundaries:\'socket与PTY替身；真实daemon、Panes、gate和SQLite；无CLI或模型\',model_calls:0};\nconst srcURL=pathToFileURL(source+\'/\');\nconst actualPanes=await import(new URL(\'workbench/src/panes.ts\',srcURL));\nconst {A2AGates}=await import(new URL(\'workbench/src/gates/core.ts\',srcURL));\nconst creds=await import(new URL(\'workbench/src/credentials.ts\',srcURL));\nprocess.env.A2A_OPERATOR_CREDENTIAL=join(output,\'operator.json\');creds.createOperatorCredential(root);\nconst operator=creds.readOperatorCredential(root);\nlet accept, panes, gates;\nconst server=new EventEmitter();server.listen=(path,cb)=>{writeFileSync(path,\'socket-boundary\');cb();};\nserver.close=cb=>cb?.();\nconst fakeNet={createServer:fn=>{accept=fn;return server;}};\nconst context=vm.createContext({process,console,Buffer,setTimeout,clearTimeout});\nconst module=new vm.SourceTextModule(stripTypeScriptTypes(readFileSync(join(source,\'workbench/src/daemon.ts\'),\'utf8\')),{context,initializeImportMeta:m=>m.url=new URL(\'workbench/src/daemon.ts\',srcURL).href});\nawait module.link(async spec=>{\n  const exports=spec===\'node:net\'?fakeNet:spec===\'./panes.ts\'?{...actualPanes,spawnHelper:()=>\'/fixture/spawn-helper\'}:\n    await import(spec.startsWith(\'.\')?new URL(spec,new URL(\'workbench/src/daemon.ts\',srcURL)).href:spec);\n  return new vm.SyntheticModule(Object.keys(exports),function(){for(const [k,v]of Object.entries(exports))this.setExport(k,v);},{context});\n});\nawait module.evaluate();\nfunction send(input,identity=operator){return new Promise((resolve,reject)=>{\n const connection=new EventEmitter();connection.setEncoding=()=>{};connection.end=text=>resolve(JSON.parse(text));\n accept(connection);connection.emit(\'data\',JSON.stringify({id:randomUUID(),input,identity})+\'\\n\');\n});}\nfunction check(label){report.checks.push(label);}\ntry {\n await module.namespace.serve(root,{},(root,p)=>{panes=p;gates=new A2AGates(root,p);return gates;});\n await new Promise(resolve=>setImmediate(resolve));\n const attempt={attempt_id:\'review-a1\',session_id:\'review-session\',thread_id:\'review-thread\',fence:7,spec_rev:3,reclaimed:false};\n const task={task_id:\'review-task\',project_id:\'review-project\',title:\'独立人工介入探针\',repo:output,state:\'claimed\',spec_rev:3,current_attempt:attempt,candidate_commit:null,verification:null,integration_intent:null};\n gates.db.prepare(\'INSERT INTO tasks VALUES (?,?)\').run(task.task_id,JSON.stringify(task));\n gates.db.prepare(\'INSERT INTO attempts VALUES (?,?)\').run(attempt.attempt_id,JSON.stringify(attempt));\n const writes=[], kills=[], sizes=[];\n const makePane=(role)=>{\n  const worker=role===\'worker\';\n  const record={id:\'review-\'+role,thread:worker?attempt.thread_id:\'shell-thread\',role,project:worker?task.project_id:null,task:worker?task.task_id:null,attempt:worker?attempt.attempt_id:null,session:worker?attempt.session_id:null,fence:worker?7:null,spec_rev:worker?3:null,cli:\'Codex\',env:{CODEX_HOME:join(output,\'empty-codex\')},worktree:output};\n  const pane={record,task:worker?task:null,attempt:worker?attempt:null,token:randomUUID(),pty:{pid:998877,write:data=>writes.push({role,data:String(data)}),resize:(cols,rows)=>sizes.push({role,cols,rows}),kill:()=>kills.push(role)},\n   state:\'busy\',stopped:false,archived:false,failed:null,leader:998878,native:null,turn:null,nativeEnded:false,active:null,queue:[],writing:false,stopInProgress:false,writes:Promise.resolve(),pendingInputs:0,userDraft:false,interrupted:false,sending:null,inputGeneration:0,interruption:null,offsets:new Map(),model:\'fixture\',effort:\'fixture\',terminalBuffer:\'\'};\n  panes.store.launch(record);panes.panes.set(record.thread,pane);\n  panes.store.event(\'pane_layout_opened\',{position:worker?0:1,native_session:null,resume_argv:null},record);\n  return pane;\n };\n if(scenario===\'restart\') {\n  const shell=makePane(\'shell\');panes.panes.delete(shell.record.thread);let starts=0;\n  panes.startShell=()=>{starts++;return {};};\n  await panes.recover(\'independent-restart\');\n  assert.equal(starts,0,\'普通终端重启不得调用startShell\');check(\'普通终端恢复不重新启动shell\');\n } else {\n  const worker=makePane(\'worker\'),shell=makePane(\'shell\');\n  const workerOpen=await send({command:\'window_open\',task:task.task_id,launch:worker.record.id});assert.equal(workerOpen.ok,true,JSON.stringify(workerOpen));\n  const shellOpen=await send({command:\'window_open\',project:null,launch:shell.record.id});assert.equal(shellOpen.ok,true);\n  const input=async(pane,identity,sequence,data)=>send({command:\'window_input\',sequence,request_id:randomUUID(),data},identity);\n  const nonce=\'独立输入-\'+randomUUID();\n  const written=await input(worker,workerOpen.identity,1,nonce);assert.equal(written.ok,true,JSON.stringify(written));\n  assert.equal(writes.at(-1).data,nonce);\n  const inputs=gates.db.prepare(\'SELECT data FROM user_inputs\').all().map(r=>JSON.parse(r.data));\n  assert.equal(inputs.length,1,\'worker输入应有一条独立用户输入\');assert.equal(inputs[0].text,nonce);\n  assert.equal(inputs[0].target.attempt,attempt.attempt_id);assert.equal(inputs[0].channel,\'terminal-window\');\n  const interventions=gates.db.prepare("SELECT details FROM events WHERE type=\'human_intervention\'").all().map(r=>JSON.parse(r.details));\n  assert.equal(interventions.length,1,\'活跃worker输入应派生人工介入\');\n  assert.equal(interventions[0].text,nonce);assert.equal(interventions[0].session_id,attempt.session_id);assert.equal(interventions[0].fence,7);\n  check(\'活跃worker输入经daemon→Panes→真实SQLite派生绑定attempt/session/fence的人工介入\');\n  const secret=\'private-\'+randomUUID();const beforeSeq=panes.store.read().at(-1).seq;\n  const plain=await input(shell,shellOpen.identity,1,secret);assert.equal(plain.ok,true,JSON.stringify(plain));\n  assert.equal(writes.at(-1).data,secret);\n  const events=panes.store.read().filter(e=>e.seq>beforeSeq);\n  assert.equal(events.length,0,\'普通终端逐次输入不得写入事件或元数据\');\n  assert.equal(gates.db.prepare(\'SELECT count(*) AS n FROM user_inputs\').get().n,1);\n  assert.equal(gates.db.prepare(\'SELECT count(*) AS n FROM user_input_ingress\').get().n,0);\n  check(\'普通终端输入写入PTY，无正文、逐次事件、请求元数据或agent输入记录\');\n  const beforeTask=gates.db.prepare(\'SELECT data FROM tasks WHERE id=?\').get(task.task_id).data;\n  const beforeAttempt=gates.db.prepare(\'SELECT data FROM attempts WHERE id=?\').get(attempt.attempt_id).data;\n  const close=await send({command:\'pane_layout_close\',task:task.task_id,launch:worker.record.id});assert.equal(close.ok,true,JSON.stringify(close));\n  assert.equal(kills.length,0,\'关闭worker视图不得直接杀进程\');assert.equal(worker.stopped,false);assert.equal(worker.archived,false);\n  assert.equal(gates.db.prepare(\'SELECT data FROM tasks WHERE id=?\').get(task.task_id).data,beforeTask);\n  assert.equal(gates.db.prepare(\'SELECT data FROM attempts WHERE id=?\').get(attempt.attempt_id).data,beforeAttempt);\n  assert.equal(panes.store.openPanes().some(p=>p.launch===worker.record.id),false);\n  check(\'活跃worker关闭只移除视图，进程未杀，task/attempt未回收或改写\');\n  task.current_attempt={...attempt,attempt_id:\'replacement\'};gates.db.prepare(\'UPDATE tasks SET data=? WHERE id=?\').run(JSON.stringify(task),task.task_id);\n  const before=writes.length;const stale=await input(worker,workerOpen.identity,2,\'stale-input\');\n  assert.equal(stale.ok,false);assert.equal(stale.error,\'stale_attempt\');assert.equal(writes.length,before);\n  check(\'旧attempt输入被拒绝，未写PTY\');\n }\n report.status=\'PASS\';\n}catch(error){report.error=String(error);report.stack=error.stack;}\nfinally {panes?.store.close();gates?.close();writeFileSync(join(output,\'result.json\'),JSON.stringify(report,null,2)+\'\\n\',{flag:\'wx\'});}\nconsole.log(JSON.stringify(report));process.exitCode=report.status===\'PASS\'?0:1;\n'
DIRECTORY_JS="// Execute the actual main IPC entry with supplied Electron/transport boundaries.\n// Requirement oracle: a new window with no project can create a home terminal.\nimport vm from 'node:vm';\nimport { stripTypeScriptTypes } from 'node:module';\nimport { EventEmitter } from 'node:events';\nimport { readFileSync } from 'node:fs';\nimport { homedir } from 'node:os';\nimport assert from 'node:assert/strict';\nconst source = process.argv[2] ?? new URL('../app/main.ts', import.meta.url);\nconst handlers = new Map(), records = new Map();\nlet arrangement = null, selectedDirectory = homedir(), dialogCalls = 0, canceled = true;\nconst request = async (_, input) => {\n  if(input.command==='pane_layout') return {ok:true,saved:true,panes:[...records.values()].map((r,i)=>({launch:r.id,position:i})),arrangement};\n  if(input.command==='shell_start') {\n    assert.equal(input.cwd,selectedDirectory); assert.equal(input.project,null);\n    const launch={id:'shell-'+records.size,role:'shell',worktree:input.cwd,project:null,task:null,attempt:null,session:null,fence:null};\n    records.set(launch.id,launch);return {ok:true,launch};\n  }\n  if(input.command==='workbench_snapshot')return {ok:true,task:null,launch:records.get(input.launch),pane:{lifecycle:'running'}};\n  if(input.command==='pane_layout_save'){arrangement=input.arrangement;return {ok:true};}\n  if(input.command==='pane_layout_close'){records.delete(input.launch);return {ok:true};}\n  throw new Error('Unexpected request '+JSON.stringify(input));\n};\nclass Window extends EventEmitter {\n  constructor(options){super();this.options=options;this.webContents={id:1,mainFrame:{},on(){},setWindowOpenHandler(){}};}\n  async loadFile(){} isDestroyed(){return false;}\n}\nconst app=Object.assign(new EventEmitter(),{whenReady:async()=>{},setPath(){},quit(){}});\nconst electron={app,BrowserWindow:Window,ipcMain:{handle:(name,fn)=>handlers.set(name,fn)},dialog:{showOpenDialog:async(parent,options)=>{assert.equal(parent,reopened);assert.deepEqual([...options.properties],['openDirectory']);dialogCalls++;return {canceled,filePaths:[selectedDirectory]};}}};\nconst ctx=vm.createContext({process,console,Buffer});\nconst module=new vm.SourceTextModule(stripTypeScriptTypes(readFileSync(source,'utf8')),{context:ctx,initializeImportMeta:m=>m.url=new URL('../app/main.ts',import.meta.url).href});\nawait module.link(async spec=>{\n  const exports=spec==='electron'?electron:spec==='../src/transport.ts'?{request}:spec==='../src/credentials.ts'?{readOperatorCredential:()=>({kind:'operator'})}:spec==='node:fs'?{mkdirSync(){}}:await import(spec);\n  return new vm.SyntheticModule(Object.keys(exports),function(){for(const [k,v]of Object.entries(exports))this.setExport(k,v);},{context:ctx});\n});\nawait module.evaluate();\nconst win=await module.namespace.run({state:'/fixture/state',userData:'/fixture/ui'});\nlet event={sender:win.webContents,senderFrame:win.webContents.mainFrame};\nconst invoke=(name,...args)=>Promise.resolve().then(()=>handlers.get('a2a:'+name)(event,...args));\nconst created=await invoke('new-terminal');\nassert.equal(created.paneKeys.length,1,'Empty workspace must create a terminal');\nconst split=await invoke('pane-action',created.paneKeys[0],{type:'split',direction:'right'});\nassert.equal(split.paneKeys.length,2);\nassert.equal(split.layout.direction,'right');\nawait invoke('pane-action',split.paneKeys[0],{type:'rename',name:'我的终端'});\nconst reopened=await module.namespace.run({state:'/fixture/state',userData:'/fixture/ui'});\nevent={sender:reopened.webContents,senderFrame:reopened.webContents.mainFrame};\nconst selected=await invoke('selection');\nassert.equal(selected.paneKeys.length,2);\nassert.equal(selected.layout.direction,'right');\nassert.equal(selected.names[selected.paneKeys[0]],'我的终端');\nawait assert.rejects(()=>invoke('pane-action','unknown',{type:'split',direction:'right'}));\nconsole.log('PASS: empty workspace → home terminal → split right → rename → reopen');\n\nconst count = records.size;\nfor (const bad of ['/tmp/renderer-path', {cwd:'/tmp/renderer-path'}, ['choose'], null]) {\n  await assert.rejects(()=>invoke('new-terminal',bad), /Invalid terminal directory source/);\n}\nassert.equal(records.size,count,'非法renderer路径不得创建终端');\nassert.equal(dialogCalls,0,'非法来源不得打开目录对话框');\nawait invoke('new-terminal','choose');\nassert.equal(dialogCalls,1);assert.equal(records.size,count,'取消目录选择不得创建终端');\ncanceled=false;selectedDirectory='/tmp/独立用户选择 space';\nconst chosen=await invoke('new-terminal','choose');\nassert.equal(records.size,count+1);\nassert.equal(records.get('shell-'+count).worktree,selectedDirectory,'只能使用主进程对话框返回的目录');\nconsole.log('PASS: 原生目录对话框来源、取消、中文含空格目录；renderer任意路径/对象/数组/null均被拒绝');\n"

(ROOT/'isolated-review.mjs').write_text(ISOLATED_JS,encoding='utf-8')
env=dict(os.environ)
for key in list(env):
 if key.startswith(('A2A_','CODEX_','CLAUDE_','ANTHROPIC_','GIT_')) or key in ('NODE_OPTIONS','ELECTRON_RUN_AS_NODE'):
  env.pop(key,None)
env.update(TMPDIR='/private/tmp',TMP='/private/tmp',TEMP='/private/tmp')
report=dict(status='INCOMPLETE',candidate=REV,baseline=BASE,argv=sys.argv,root=str(ROOT),model_calls=0,
            scope='隔离检查、三变异'+('及真实Electron复验' if ELECTRON else '；未启动Electron'),runs=[])
def command(argv,label,expected=0):
 run=subprocess.run(list(map(str,argv)),cwd=REPO,env=env,capture_output=True,text=True,timeout=300)
 (ROOT/(label+'.stdout.txt')).write_text(run.stdout,encoding='utf-8')
 (ROOT/(label+'.stderr.txt')).write_text(run.stderr,encoding='utf-8')
 report['runs'].append(dict(label=label,argv=list(map(str,argv)),exit=run.returncode,expected_exit=expected))
 assert run.returncode==expected, (label,run.returncode,run.stdout[-2000:],run.stderr[-2000:])
 return run

def extract(label,revision=REV):
 target=ROOT/label;target.mkdir();archive=ROOT/(label+'.tar')
 with archive.open('wb') as out:
  subprocess.run(['git','archive',revision,'workbench'],cwd=REPO,stdout=out,check=True)
 subprocess.run(['/usr/bin/tar','-xf',str(archive),'-C',str(target)],check=True)
 return target

def isolated(source,label,scenario='all',expected_error=None):
 out=ROOT/label
 command(['node','--experimental-vm-modules',ROOT/'isolated-review.mjs',source,out,scenario],label,1 if expected_error else 0)
 data=json.loads((out/'result.json').read_text(encoding='utf-8'))
 if expected_error:
  assert 'AssertionError' in data.get('error','') and expected_error in data['error'],data
  report['runs'][-1]['mutation_rejected']=expected_error
 else:assert data['status']=='PASS',data
 return data

try:
 candidate=extract('candidate')
 deps=pathlib.Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules')
 assert deps.is_dir(),'需本机已有依赖，不下载、不安装'
 if ELECTRON:
  shutil.copytree(deps,candidate/'workbench/node_modules',symlinks=True)
  helper=candidate/'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
  helper.chmod(0o755) # 只改隔离依赖副本。
 else:(candidate/'workbench/node_modules').symlink_to(deps,target_is_directory=True)
 command(['node','--experimental-vm-modules',candidate/'workbench/tests/test_t105_panes.mjs'],'candidate-main-ipc')
 command(['node','--experimental-vm-modules',candidate/'workbench/tests/test_t091_pane_ipc.mjs',ROOT/'ipc-contract.json','--source',candidate],'candidate-ipc-security')
 (candidate/'workbench/tests/review-directory.mjs').write_text(DIRECTORY_JS,encoding='utf-8')
 command(['node','--experimental-vm-modules',candidate/'workbench/tests/review-directory.mjs'],'candidate-directory')
 isolated(candidate,'candidate-live-worker')
 isolated(candidate,'candidate-restart','restart')
 mutations={
  'worker-kill':('workbench/src/daemon.ts','else panes.forgetOpen(input.launch);','else { panes.byLaunch(input.launch).pty.kill(); panes.forgetOpen(input.launch); }','all','关闭worker视图不得直接杀进程'),
  'shell-log':('workbench/src/daemon.ts','shellInput = isShellInput(envelope);','shellInput = isShellInput(envelope);\n        if (shellInput) store.event("review_bad_input", envelope.input);','all','普通终端逐次输入不得写入事件或元数据'),
  'shell-restart':('workbench/src/panes.ts',"// A user's terminal is never resumed or turned into an agent session.","// A user's terminal is never resumed or turned into an agent session.\n        this.startShell(record.project, record.worktree);",'restart','普通终端重启不得调用startShell')}
 sources={}
 for name,(file,old,new,scenario,error) in mutations.items():
  target=extract(name);sources[name]=target
  (target/'workbench/node_modules').symlink_to(candidate/'workbench/node_modules',target_is_directory=True)
  path=target/file;text=path.read_text(encoding='utf-8');assert text.count(old)==1
  path.write_text(text.replace(old,new),encoding='utf-8')
  isolated(target,'reject-'+name,scenario,error)
 if ELECTRON:
  runtime=pathlib.Path(os.environ.get('T105_ELECTRON_DIST',str(deps/'electron/dist'))).resolve(strict=True)
  assert '/Volumes/' not in str(runtime) and (runtime/'version').read_text().strip()=='43.4.1'
  baseline=extract('baseline',BASE)
  (baseline/'workbench/node_modules').symlink_to(candidate/'workbench/node_modules',target_is_directory=True)
  def electron(source,label,expected=0):
   global DEPENDENCIES_SAFE
   summary=ROOT/(label+'.json')
   DEPENDENCIES_SAFE=False
   command(['python3',candidate/'workbench/tests/run_t105_panes.py','--source',source,'--baseline',baseline,
            '--electron-dist',runtime,'--summary',summary],label,expected)
   data=json.loads(summary.read_text(encoding='utf-8'))
   assert data.get('cleanup_complete'),data
   DEPENDENCIES_SAFE=True
   if expected==0:assert data['status']=='PASS',data
   else:
    # 只把本合同断言失败计为拒绝；依赖/启动/构建失败不算变异证据。
    assert 'AssertionError' in data.get('error',''),data
    if label=='electron-shell-log':assert 'assert marker not in json.dumps(events)' in data.get('traceback',''),data
    if label=='electron-shell-restart':
     assert len(data['checks'])>=7 and ('UI condition not reached' in data.get('traceback','') or 'inventory()==before' in data.get('traceback','')),data
   return data
  if FULL_ELECTRON:
   electron(candidate,'electron-candidate')
   electron(sources['shell-log'],'electron-shell-log',1)
   electron(sources['shell-restart'],'electron-shell-restart',1)
  # 真实原生目录对话框：路径由执行主控在本脚本自建窗口里选择，程序不替换dialog响应。
  import time, uuid
  sys.path.insert(0,str(candidate/'workbench/tests'))
  from run_t103_picker import Window
  chooser_root=ROOT/'chooser';chooser_root.mkdir()
  chosen=chooser_root/'中文目录 space';chosen.mkdir()
  home=chooser_root/'home';home.mkdir();(home/'.zshrc').write_text("PS1='REVIEW% '\n",encoding='utf-8')
  state=chooser_root/'state';credential=chooser_root/'operator.json'
  chooser_env=dict(env,HOME=str(home),SHELL='/bin/zsh',ELECTRON_OVERRIDE_DIST_PATH=str(runtime),A2A_OPERATOR_CREDENTIAL=str(credential))
  cli=candidate/'workbench/src/gates/cli.ts'
  def cli_call(command,*args):
   argv=['node',str(cli),'--state',str(state),command]+list(map(str,args))
   run=subprocess.run(argv,env=chooser_env,capture_output=True,text=True,timeout=60)
   report['runs'].append(dict(label='chooser-'+command,argv=argv,exit=run.returncode,stdout=run.stdout,stderr=run.stderr))
   assert run.returncode==0,(argv,run.stdout,run.stderr)
   return json.loads(run.stdout)
  driver_source=(candidate/'workbench/tests/t105_panes_driver.mjs').read_text(encoding='utf-8')
  marker="else if (request.command === 'new-terminal')"
  assert driver_source.count(marker)==1
  inserted=r'''else if (request.command === 'directory-source') value = await window.webContents.executeJavaScript("(()=>{const select=document.querySelector('[aria-label=\"终端工作目录\"]');select.value='choose';select.dispatchEvent(new Event('change',{bubbles:true}));return {selected:select.value};})()");
          '''
  driver=candidate/'workbench/tests/review-chooser-driver.mjs';driver.write_text(driver_source.replace(marker,inserted+marker),encoding='utf-8')
  owners=[];win=None;daemon=None;build_root=None;DEPENDENCIES_SAFE=False
  try:
   daemon=cli_call('daemon_start')['pid']
   deadline=time.monotonic()+20
   while cli_call('pane_layout').get('recovering'):
    assert time.monotonic()<deadline,'后台恢复超时'
    time.sleep(.1)
   built=command(['node',candidate/'workbench/app/build.mjs','--slot','t105-review-chooser-'+uuid.uuid4().hex[:8]],'chooser-build')
   build=json.loads(built.stdout.splitlines()[-1]);build_root=pathlib.Path(build['out']).parent
   win=Window(candidate,driver,pathlib.Path(build['out']),state,chooser_root/'ui',chooser_root/'window',chooser_env,owners,
              dict(executable=str(runtime/'Electron.app/Contents/MacOS/Electron'),dist=str(runtime),version='43.4.1'),None,through_start=False)
   win.wait(lambda v:v['newTerminal'] and not v['newTerminal']['disabled'])
   assert win.call('directory-source')['selected']=='choose'
   time.sleep(.2)
   win.call('new-terminal')
   print('目录选择待操作：只在本脚本的 Electron 对话框选择 '+str(chosen),flush=True)
   print('隔离 Electron PID：'+str(win.ready['pid'])+'；目录选择等待上限180秒。',flush=True)
   deadline=time.monotonic()+180;view=None
   while time.monotonic()<deadline:
    view=win.call('inspect')
    if len(view['panes'])==1 and view['panes'][0]['input']:break
    assert not view['alerts'],view['alerts']
    time.sleep(.2)
   assert view and len(view['panes'])==1 and view['panes'][0]['input'],'目录选择未完成；取消或无人操作不算产品失败'
   pane=view['panes'][0];record=cli_call('launch_show','--launch',pane['launch'])['launch']
   assert record['worktree']==str(chosen.resolve()) and record['project'] is None,record
   sentinel='chooser-'+uuid.uuid4().hex
   win.call('terminal-input',key=pane['key'],text="printf '%s\\n' '"+sentinel+"'; pwd")
   win.wait(lambda v:sentinel in v['panes'][0]['terminal'] and str(chosen.resolve()) in v['panes'][0]['terminal'])
   win.call('close-pane',key=pane['key']);win.wait(lambda v:not v['panes'])
   report['native_directory']='PASS：真实工具栏→原生目录对话框→中文含空格目录→PTY pwd，与家目录不同'
  finally:
   for owner in owners:owner.close()
   if daemon is not None:
    cli_call('daemon_stop');deadline=time.monotonic()+20
    while True:
     status=subprocess.run(['/bin/ps','-p',str(daemon),'-o','stat='],capture_output=True,text=True,timeout=5)
     if not (state/'control.sock').exists() and (not status.stdout.strip() or status.stdout.strip().startswith('Z')):break
     assert time.monotonic()<deadline,'后台退出未确认，保留目录'
     time.sleep(.1)
   DEPENDENCIES_SAFE=True
   if build_root is not None:shutil.rmtree(build_root)
 report['status']='PASS'
except Exception as error:
 import traceback
 report.update(error=repr(error),traceback=traceback.format_exc())
finally:
 (ROOT/'review-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
 if ELECTRON and DEPENDENCIES_SAFE and (ROOT/'candidate/workbench/node_modules').is_dir():
  shutil.rmtree(ROOT/'candidate/workbench/node_modules')
  report['dependency_copy_cleaned']=True
  (ROOT/'review-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 # 原件保留在自建临时目录，不覆盖旧结果；Electron runner 自行确认进程退出并清理构建目录。
 # 所有新建fixture无用户数据；执行主控归档文本摘要后可回收本目录。
sys.exit(0 if report['status']=='PASS' else 1)
PY_REVIEW
