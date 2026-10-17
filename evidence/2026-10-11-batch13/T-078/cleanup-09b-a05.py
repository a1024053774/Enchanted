"""Owner-bound A-05 cleanup; authenticated daemon shutdown owns controller/target exits."""
import argparse, importlib.util, json, os, shlex, shutil, signal, subprocess, time, traceback
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/t078-2-09b-run-94_wksxv');STATE=ROOT/'state';APIS=[(70730,'ideation',ROOT/'roles/ideation'),(70731,'executor',ROOT/'roles/executor')];DAEMON=70733;TARGET=[70837,70839];CLAUDE=[1227,1228]
def ps(pid):
 p=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,lstart=,command='],capture_output=True,text=True,env={**os.environ,'LC_ALL':'C','LANG':'C'})
 if p.returncode==1 and not p.stdout.strip():return None
 if p.returncode!=0 or p.stderr.strip():raise RuntimeError('process_readback_failed')
 parts=p.stdout.strip().split(maxsplit=6)
 if len(parts)!=7 or int(parts[0])!=pid:raise RuntimeError('process_identity_mismatch')
 return {'pid':pid,'lstart':' '.join(parts[1:6]),'command':parts[6]}
def wait_absent(pid,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if ps(pid) is None:return True
  time.sleep(.1)
 return ps(pid) is None
def api_command_matches(command, expected):
 parts=shlex.split(command)
 return len(parts)>=2 and parts[1:]==['-B',*expected]
def main():
 p=argparse.ArgumentParser();p.add_argument('--approval-ref',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args();out=BASE/('09b-a05-cleanup-dry-run-02' if a.dry_run else '09b-a05-cleanup');out.mkdir(exist_ok=False)
 r={'status':'BLOCKED','dry_run':a.dry_run,'root':str(ROOT),'approval_ref':a.approval_ref,'signals_sent':[],'root_removed':False,'slots_removed':[],'scope':'A-05 root only; controller/target normal daemon shutdown then owned API SIGTERM'}
 def save():(out/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 save()
 try:
  assert a.approval_ref.strip() and ROOT.is_dir() and ROOT.resolve()==ROOT
  ready=json.loads((BASE/'09b-stage-a-05/readiness.json').read_bytes());scene=json.loads((BASE/'09b-stage-a-05/result.json').read_bytes());manifest=json.loads((BASE/'09b-stage-b-ideation-p1-02/09b-stage-b1-ideation-04/process-manifest.json').read_bytes())
  assert ready['status']=='READY_FOR_APPROVAL' and scene['status']=='READY_FOR_APPROVAL' and ready['root']==str(ROOT)
  identities={pid:ps(pid) for pid in [DAEMON,*TARGET,*CLAUDE,*[x[0] for x in APIS]]};r['before']=identities;save()
  assert identities[DAEMON] and str(SOURCE/'workbench/src/daemon.ts') in identities[DAEMON]['command'] and str(STATE) in identities[DAEMON]['command']
  assert identities[70837] and '/bin/zsh' in identities[70837]['command'];assert identities[70839] and str(ROOT/'target/bin/codex-receiver') in identities[70839]['command']
  assert identities[1227] and '/bin/zsh' in identities[1227]['command'];assert identities[1228] and 'claude' in identities[1228]['command'].lower()
  for pid,role,api_root in APIS:
   ready_api=json.loads((api_root/'api-ready.json').read_bytes());identity=identities[pid];assert identity and ready_api['pid']==pid and ready_api['role']==role
   expected=[str(SOURCE/'workbench/tests/t078_09b_fake_api.py'),'--root',str(api_root),'--role',role,'--port','0'];assert api_command_matches(identity['command'],expected)
  r['identity_checks']='PASS';r['planned_actions']=['authenticated daemon_stop invokes normal panes.shutdown for Claude and target','confirm Claude/target/daemon exit without direct signal','SIGTERM each A-05 API once','archive every member and byte-readback before root delete'];save()
  if a.dry_run:r.update(status='PASS',action='dry-run only; no signal/stop/archive/delete');save();print(json.dumps({'status':'PASS','dry_run':True,'signals_sent':[]}));return 0
  node=shutil.which('node');env={**os.environ,'A2A_OPERATOR_CREDENTIAL':str(ROOT/'operator.json'),'LC_ALL':'C','LANG':'C'};q=subprocess.run([node,str(SOURCE/'workbench/src/gates/cli.ts'),'--state',str(STATE),'daemon_stop'],cwd=SOURCE,env=env,capture_output=True,text=True,timeout=30);r['controller_stop_path']='authenticated daemon_stop -> panes.shutdown (normal path; no direct controller signal)';r['daemon_stop']={'exit_code':q.returncode,'stdout':q.stdout,'stderr':q.stderr};save();assert q.returncode==0
  for pid in [1228,1227,*TARGET,DAEMON]:assert wait_absent(pid),f'owned exit unconfirmed {pid}'
  assert not (STATE/'daemon.pid').exists() and not (STATE/'control.sock').exists()
  for pid,role,api_root in APIS:
   assert ps(pid) is not None;os.kill(pid,signal.SIGTERM);r['signals_sent'].append({'pid':pid,'signal':'SIGTERM'});save();assert wait_absent(pid,2)
  if (ROOT/'operator.json').exists():(ROOT/'operator.json').unlink()
  volume=Path('/Volumes/WD-Elements');assert os.path.ismount(volume) and volume.resolve()==volume;external=volume/'a2a-evidence/2026-10-11-batch13/T-078/09b-a05-cleanup';external.parent.mkdir(parents=True,exist_ok=True);external.mkdir()
  spec=importlib.util.spec_from_file_location('archive',BASE/'cleanup-09b-stage-a-03.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);archive=external/'fixture.tar.gz';inv=helper.archive_and_verify(ROOT,archive);r.update(status='PASS',archive=str(archive),archive_bytes=archive.stat().st_size,archive_inventory=inv,byte_readback='PASS');save();assert not ROOT.is_symlink();shutil.rmtree(ROOT);assert not ROOT.exists();r['root_removed']=True;save()
 except Exception as e:r.update(status='BLOCKED',error=repr(e),traceback=traceback.format_exc(),root_retained=ROOT.exists());save()
 print(json.dumps({'status':r['status'],'dry_run':r['dry_run'],'signals_sent':r['signals_sent'],'root_removed':r['root_removed'],'error':r.get('error')}));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
