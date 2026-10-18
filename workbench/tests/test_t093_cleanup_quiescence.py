"""Initial fixture shape must not authorize deletion while its R/G can run."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

SOURCE=Path(__file__).with_name('cleanup_t093_retained_fixture.py').resolve()
spec=importlib.util.spec_from_file_location('cleanup',SOURCE);mod=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text() if len(sys.argv)>2 else SOURCE.read_text();exec(compile(text,str(SOURCE),'exec'),vars(mod))
output=Path(sys.argv[1]);assert not output.exists();checks=[]
def record(name,action):
 try:value=action();checks.append({'check':name,'status':'PASS','detail':value})
 except AssertionError as error:checks.append({'check':name,'status':'FAIL','business_failure':str(error)})

def active_initial():
 root=Path(tempfile.mkdtemp(prefix='t093-chain-active-unit-',dir='/private/tmp'))
 try:
  for name in ('U','S','M','state','repo','synthetic-home','source-home/.claude'):(root/name).mkdir(parents=True)
  for name in ('home','claude','tmp','shell','requests','hooks','user-data'):(root/'roles/ideation'/name).mkdir(parents=True)
  for name in ('roles/ideation/role.md','source-home/private-sentinel','source-home/.claude/.credentials.json'):(root/name).write_text('synthetic only')
  rejected=False
  with patch.object(mod,'setup_quiescence',side_effect=ValueError('active_setup_processes_prevent_fixture_deletion'),create=True):
   try:mod.remove(root)
   except ValueError:rejected=True
  assert rejected and (root/'source-home/.claude/.credentials.json').exists(),'initial_fixture_must_require_R_G_stoppage_before_any_deletion'
  return {'initial_shape_rejected_while_setup_active':True,'actual_process_probes':0}
 finally:
  if root.exists():shutil.rmtree(root)

def inventory():
 assert hasattr(mod,'error_details'),'unprivileged_observer_with_positive_control_required'
 root=Path('/private/tmp/t093-chain-bound-unit')
 cases=[('inactive',None),('active_R','R'),('active_G','G'),('active_C','C'),('control_missing','missing'),('query_error','error')]
 observed=[]
 for name,role in cases:
  class Control:
   pid=440701;returncode=None
   def poll(self):return self.returncode
   def kill(self):self.returncode=-9
   def communicate(self,timeout=None):return None,None
  control=Control();commands=[]
  def popen(argv,**options):
   commands.append(argv)
   assert options['start_new_session'] is True
   if argv[0]=='/usr/bin/python3':
    assert callable(options['preexec_fn']),'control_deadline_must_start_before_exec'
    return control
   assert argv[:5]==['/usr/bin/pgrep','-a','-f','-U',str(os.getuid())]
   query_role='R' if 'run_t093_login_chain' in argv[-1] else 'C' if 'test_t093_login_chain' in argv[-1] else 'G'
   values=set()
   if control.poll() is None and role!='missing':values.add(control.pid)
   if role==query_role:values.add(440501)
   class Query:
    pid=440800+len(commands);returncode=3 if role=='error' else 0 if values else 1
    def communicate(self,timeout=None):return ''.join(str(pid)+'\n' for pid in sorted(values)),'synthetic error' if role=='error' else ''
   return Query()
  def absent(*args):raise ProcessLookupError()
  with patch.object(mod.subprocess,'Popen',side_effect=popen),patch.object(mod.os,'killpg',side_effect=absent),patch.object(mod.os,'getpgid',return_value=440500):
   try:value=mod.setup_quiescence(root)
   except mod.ActiveSetupProcesses as error:
    assert role in ('R','G','C') and error.proof['root']==str(root) and error.proof['matching_processes'][0]['role']==role
   except ValueError as error:assert role in ('missing','error') and str(error)==('setup_process_positive_control_not_seen' if role=='missing' else 'setup_process_inventory_unavailable')
   else:assert role is None and value['root']==str(root) and value['complete'] and value['matching_processes']==[] and value['positive_control']['R_seen'] and value['positive_control']['G_seen'] and value['positive_control']['C_seen']
   assert control.returncode==-9,'observer_control_must_be_reaped_before_return'
   assert all(argv[0] in ('/usr/bin/python3','/usr/bin/pgrep') for argv in commands)
  observed.append(name)
 return {'synthetic_inventory_cases':observed,'raw_argv_saved':False,'actual_process_commands':0,'setuid_observer_used':False}

record('initial fixture with active setup',active_initial)
record('bound scoped process inventory',inventory)
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'synthetic filesystem and ps output; no real process inventory or existing fixture deletion','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
