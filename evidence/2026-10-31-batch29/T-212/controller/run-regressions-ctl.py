"""T-212 回归驱动：只清理本次测试新建夹具里的 enchanted core；敏感运行目录留在私有夹具。"""
import json,os,pathlib,pwd,shutil,subprocess,sys,tempfile,time
ROOT=pathlib.Path('/Users/luckye/Documents/Code/a2a-worktrees/T-212')
OUT=pathlib.Path('/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller')
DRIVER=pathlib.Path(tempfile.mkdtemp(prefix='t212-regression-',dir='/private/tmp'))
TESTS=[
 ('t118','t118-', ['workbench/tests/test_t118_shell_env_e2e.py','--summary']),
 ('t126','t126-', ['workbench/tests/test_t126_terminal_socket_e2e.py','--summary']),
 ('t121','t121-', ['workbench/tests/test_t121_role_request_e2e.py','--summary']),
 ('t107','t107-', ['workbench/tests/test_t107_live_sidebar_e2e.py','--summary']),
 ('t184','t184-', ['workbench/tests/test_t184_unwired_cli_e2e.py','--summary']),
 ('t195','t195-', ['workbench/tests/test_t195_native_link_e2e.py','--summary']),
 ('t133','t133t-', ['workbench/tests/test_t133_t107_terminal_controller_e2e.py','--summary']),
 ('t133codex','t133c-', ['workbench/tests/test_t133_codex_terminal_controller_e2e.py','--summary']),
 ('t142','t142-', ['workbench/tests/test_t142_terminal_open_e2e.py','--summary']),
 ('recovery','a4r-', ['workbench/tests/test_daemon_recovery_e2e.py','--output']),
 ('electron','a2a4-', ['workbench/tests/test_electron_e2e.py','--source',str(ROOT),'--stage','window','--output']),
]
if len(sys.argv)>1: TESTS=[x for x in TESTS if x[0] in sys.argv[1:]]
realhome=pathlib.Path(pwd.getpwuid(os.getuid()).pw_dir)
def manifests(fixture):
 for directory,subdirs,files in os.walk(fixture):
  subdirs[:]=[x for x in subdirs if x not in ('home','source','out','node_modules','.git')]
  if 'hc-runtime.json' in files: yield pathlib.Path(directory)/'hc-runtime.json'
def inventory():
 p=realhome/'.local/state/herdr-core'
 return sorted(str(x.relative_to(p)) for x in p.rglob('*')) if p.exists() else []
before=inventory()
sys.path.insert(0,str(ROOT/'workbench/tests'))
from hc_evidence import assert_public_evidence,user_core_snapshot
user_before=user_core_snapshot()
results=[]
for name,prefix,args in TESTS:
 target=OUT/(name+'-ctl-01')
 if target.exists(): raise SystemExit('Existing evidence: '+str(target))
 target.mkdir()
 prior=set(pathlib.Path('/private/tmp').glob(prefix+'*'))
 raw=DRIVER/name
 raw.mkdir()
 destination=raw/('summary.json' if args[-1]=='--summary' else 'output')
 argv=[sys.executable,*args,str(destination)]
 cores={}; secrets=set()
 with (raw/'stdout.log').open('xb') as log:
  process=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  end=time.monotonic()+1800
  while process.poll() is None and time.monotonic()<end:
   for fixture in set(pathlib.Path('/private/tmp').glob(prefix+'*'))-prior:
    for manifest in manifests(fixture):
     try:
      state=manifest.parent
      if state in cores: continue
      identity=json.loads(manifest.read_text())
      assert identity['session'].startswith('enchanted-')
      binary=state/'hc/bin/herdr-core'
      if not binary.exists() or not pathlib.Path(identity['socket']).exists(): continue
      saved=raw/(identity['session']+'-herdr-core')
      shutil.copy2(binary,saved)
      cores[state]=(identity,saved)
     except (FileNotFoundError,json.JSONDecodeError): pass
    # Terminal bearer tokens exist only in hc's private restart env and some legacy test out files.
    for reg in fixture.glob('state/hc/state/herdr-core/*/terminals.json'):
     try:
      data=json.loads(reg.read_text())
      for term in data.get('terminals',{}).values():
       token=term.get('restart_env',{}).get('A2A_TERMINAL_TOKEN')
       if token: secrets.add(token)
     except (FileNotFoundError,json.JSONDecodeError,AttributeError): pass
   time.sleep(.1)
  if process.poll() is None:
   process.terminate(); process.wait(timeout=30)
  code=process.returncode
  (raw/'process.json').write_text(json.dumps(dict(pid=process.pid,exit=code)))
 cleanup=[]
 for state,(identity,binary) in cores.items():
  env=dict(os.environ,HC_SESSION=identity['session'],HC_SOCKET=identity['socket'],XDG_STATE_HOME=str(state/'hc/state'),XDG_CONFIG_HOME=str(state/'hc/config'))
  # server stop requires an existing core; it never auto-starts one.
  run=subprocess.run([str(binary),'server','stop'],env=env,capture_output=True,text=True,timeout=30,start_new_session=True)
  cleanup.append(dict(state=str(state),session=identity['session'],exit=run.returncode,stdout=run.stdout,stderr=run.stderr))
 def redacted(text):
  for secret in secrets: text=text.replace(secret,'<terminal-token-redacted>')
  return text
 (target/'stdout.log').write_text(redacted((raw/'stdout.log').read_text(errors='replace')),encoding='utf-8')
 for file in raw.rglob('*.json'):
  relative=file.relative_to(raw)
  dest=target/relative
  dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_text(redacted(file.read_text(errors='replace')),encoding='utf-8')
 result=dict(name=name,argv=argv,exit=code,raw_private_fixture=str(raw),core_cleanup=cleanup,user_core_directory_unchanged=before==inventory())
 (target/'driver.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 result['user_core_processes_unchanged']=user_before['processes']==user_core_snapshot()['processes']
 result['evidence_boundary']=assert_public_evidence(target,secrets)
 (target/'driver.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 results.append(result)
 print(json.dumps(dict(name=name,exit=code,cores=len(cores),cleanup=[x['exit'] for x in cleanup]),ensure_ascii=False),flush=True)
(OUT/('regression-driver-'+DRIVER.name+'.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
