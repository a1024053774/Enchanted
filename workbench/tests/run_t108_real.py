"""T-108 approved Claude root turn through T-093 normal login. Never retries input."""
import argparse, json, os, shutil, sqlite3, subprocess, sys, time, uuid
from pathlib import Path
from run_t103_picker import Window
from t108_cleanup import observe, stop_owned

p=argparse.ArgumentParser()
p.add_argument('--probe',type=Path,required=True);p.add_argument('--summary',type=Path,required=True)
p.add_argument('--claude',type=Path,required=True);p.add_argument('--electron-dist',type=Path,required=True)
a=p.parse_args();assert not a.summary.exists()
source=Path(__file__).resolve().parents[2]
probe=json.loads(a.probe.read_text());assert probe['status']=='PASS' and probe['isolated_home_removed'] and probe['credential_scan_hits']==0
assert probe['real_upstream_requests']==0 and probe['onboarding_state']['trusted_cwd']
root=Path('/private/tmp/t108-real-'+uuid.uuid4().hex[:10]);state=root/'state'
env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','A2A_','CLAUDE_','ANTHROPIC_','CODEX_')) and k not in ('NODE_OPTIONS','ELECTRON_RUN_AS_NODE')}
env.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',A2A_OPERATOR_CREDENTIAL=str(root/'operator.json'),ELECTRON_OVERRIDE_DIST_PATH=str(a.electron_dist.resolve()))
report={'status':'INCOMPLETE','task':'T-108','attempt':'a1','fixture':str(root),'approval':'主控 #13：Claude 1 根，失败不补发、不自动重跑',
        'root_inputs_attempted':0,'model_calls':None,'vendor_calls':None,'probe':str(a.probe),'commands':[]}
windows=[];daemon=None;owner=None;build=None;manifest=None
cli=['node',str(source/'workbench/src/gates/cli.ts'),'--state',str(state)]
def run(argv,timeout=90):
 r=subprocess.run(list(map(str,argv)),cwd=source,env=env,capture_output=True,text=True,timeout=timeout)
 report['commands'].append({'argv':list(map(str,argv)),'exit':r.returncode})
 assert r.returncode==0,'Command failed; see exit record and private bootstrap/daemon logs: '+str(argv[0])
 return r.stdout
def call(name,*args):
 v=json.loads(run([*cli,name,*args]));assert v.get('ok'),v.get('error');return v
def until(fn,label,timeout=120):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  value=fn()
  if value:return value
  time.sleep(.15)
 raise AssertionError(label)
def events():
 with sqlite3.connect('file:'+str(state/'state.sqlite3')+'?mode=ro',uri=True) as db:
  return [{'type':t,'data':json.loads(d)} for t,d in db.execute('SELECT type,data FROM orchestration_events ORDER BY seq')]
try:
 revision=run(['git','rev-parse','HEAD']).strip()
 run(['git','diff','--quiet','HEAD','--','workbench/src','workbench/tests','workbench/app'])
 run(['/usr/bin/python3','-B',source/'workbench/tests/prepare_t108_real.py','--root',root,'--claude',a.claude,'--revision',revision])
 env['HOME']=str(root/'manager-home')
 manifest=json.loads((root/'manifest.json').read_text());report['cli_version']=manifest['version'];report['source_revision']=revision
 assert probe['cli_version']==manifest['version']+' (Claude Code)','CLI changed since the successful version probe'
 net=json.loads((root/'network.json').read_text())
 argv=['/usr/bin/python3','-I','-S','-B',str(source/'workbench/src/claudeLoginSession.py'),'--manifest',str(root/'manifest.json'),'--repo',str(root/'repo'),
       '--forward-port',str(net['forward_port']),'--upstream-address',net['upstream_address'],'--lifetime-seconds','600']
 with (root/'bootstrap.stdout').open('xb') as out,(root/'bootstrap.stderr').open('xb') as err:
  daemon=subprocess.Popen(argv,cwd=source,env=env,stdout=out,stderr=err,start_new_session=True)
 report['bootstrap_pid']=daemon.pid
 until(lambda:(state/'daemon.pid').exists(),'Protected daemon readiness',40)
 owner=observe(daemon.pid);assert owner and str(state) in owner['command'] and str(source/'workbench/src/daemon.ts') in owner['command']
 call('daemon_status');call('card_save','--task','T108-real','--card',root/'card.json','--expected-version','0')
 call('create','--task','T108-real','--repo',root/'repo','--branch','refs/heads/main','--card-version','1','--project','T108-real')
 launch=call('controller_start','--task','T108-real','--manifest',root/'manifest.json')['launch']
 assert launch['cli_version']==probe['cli_version'];report['launch']=launch['id']
 until(lambda:call('pane_process_info','--thread',manifest['thread']).get('leader'),'Native CLI identity')
 preflight=json.loads(Path(launch['login_preflight_file']).read_text())
 assert preflight['credential_scan']['hits']==0 and preflight['credential_scan']['launch_record_hits']==0
 build=json.loads(run(['node',source/'workbench/app/build.mjs','--slot','t108-real-'+uuid.uuid4().hex[:8]]).splitlines()[-1])
 dist=a.electron_dist.resolve();binary=dist/'Electron.app/Contents/MacOS/Electron'
 assert not str(binary).startswith('/Volumes/') and (dist/'version').read_text().strip()=='43.4.1'
 w=Window(source,source/'workbench/tests/t108_questions_driver.mjs',Path(build['out']),state,root/'ui',root/'window',env,windows,
          {'executable':str(binary),'dist':str(dist),'version':'43.4.1'},task='T108-real',through_start=False)
 until(lambda:any(p['input']=='true' for p in w.call('inspect')['panes']),'Writable Claude pane')
 report['root_inputs_attempted']=1;w.call('prompt')  # Exactly once, including failure/timeout.
 view=until(lambda:(lambda v:v if v['questions'] else None)(w.call('inspect')),'Native question in Electron')
 q=view['questions'][0];assert '选择部署区域？' in q['text'] and '西区' in q['text'] and '东区' in q['text'] and '等待用户回答' in q['text']
 assert call('sidebar_snapshot')['agents'][0]['state']=='waiting_user_answer'
 w.call('answer')
 until(lambda:any(e['type']=='native_question_resolved' and e['data']['status']=='answered' and
                    e['data']['response']['answers'].get('选择部署区域？')=='西区' for e in events()),'Native confirmed selected answer')
 until(lambda:call('workbench_snapshot','--task','T108-real','--launch',manifest['launch'])['pane']['state']=='idle','Matched Stop returns idle')
 ev=events();hooks=[json.loads(e['data']['raw_stdin']) for e in ev if e['type']=='hook_received']
 starts=[h for h in hooks if h['hook_event_name']=='UserPromptSubmit'];stops=[h for h in hooks if h['hook_event_name']=='Stop']
 assert len(starts)==len(stops)==1 and starts[0]['prompt_id']==stops[0]['prompt_id'] and stops[0]['stop_hook_active'] is False
 with sqlite3.connect('file:'+str(state/'state.sqlite3')+'?mode=ro',uri=True) as db:
  answers=[json.loads(d) for d, in db.execute('SELECT data FROM user_inputs') if json.loads(d)['form']=='answer']
 assert len(answers)==1 and answers[0]['reply_to']==q['id'] and answers[0]['target']['request']==q['id'] and answers[0]['target']['thread']==manifest['thread']
 assert w.call('duplicate',question=q['id'])['rejected']
 report['checks']=['normal_login_recorded_version','electron_question_and_wait','dom_answer_original_pty','native_answer_and_matched_stop','answer_link','duplicate_refused']
 report['status']='PASS'
except Exception as error:report['error']=str(error)
finally:
 for w in windows:
  try:w.close()
  except Exception as error:report['status']='INCOMPLETE';report['window_cleanup_error']=str(error)
 if daemon:
  try:
   if (state/'daemon.pid').exists():call('daemon_stop')
   daemon.wait(timeout=55);assert daemon.returncode==0
  except Exception as error:
   report['status']='INCOMPLETE';report['daemon_cleanup_error']=str(error)
   if owner:
    try:report['forced_daemon_cleanup']=stop_owned(owner)
    except Exception as cleanup:report['forced_cleanup_error']=str(cleanup)
 if manifest:
  try:
   facts=json.loads((state/'login-audits'/manifest['launch']/'facts.json').read_text())
   report['model_calls']=facts['counts']['model_requests'];report['vendor_calls']=facts['forwarder']['forwarded']
   report['login_facts']=facts
   assert facts['counts']['counts_match'] and facts['auth_original_reads']==1 and facts['isolated_home_removed'] and facts['credential_scan']['hits']==0
   assert facts['onboarding']['state_intact'] and not facts['onboarding']['preflight_observed']
   # T-118: the audit carries the installed CLI's own --version output; the manifest value is only the configured one.
   observed=subprocess.run([manifest['executable'],'--version'],capture_output=True,text=True,timeout=10).stdout.strip()
   assert facts['cli_version']==observed and facts['configured_cli_version']==manifest['version'] and facts['onboarding']['internal_state_version']==manifest['version']
   for role in ['F','D']:
    pid=facts['processes'][role]['pid'];until(lambda:observe(pid) is None,'Login helper exit '+role,10)
  except Exception as error:report['status']='INCOMPLETE';report['facts_or_cleanup_error']=str(error)
 if build and all(w.proc.poll() is not None for w in windows):shutil.rmtree(Path(build['out']).parent)
 a.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':report['status'],'summary':str(a.summary),'root_inputs_attempted':report['root_inputs_attempted'],'model_calls':report['model_calls'],'vendor_calls':report['vendor_calls']},ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
