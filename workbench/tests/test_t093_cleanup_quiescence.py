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
 assert hasattr(mod,'setup_quiescence'),'cleanup_must_collect_root_bound_setup_quiescence'
 source=str(mod.SOURCE.parents[2].resolve());root=Path('/private/tmp/t093-chain-bound-unit')
 own=f'{os.getpid()} {os.getpgrp()} S /usr/bin/python3 cleanup_t093_retained_fixture.py\n'
 cases=[('inactive',own+'440601 440601 R /bin/ps -axo pid=,pgid=,stat=,command=\n',None),
        ('relative_R',own+'440501 440500 S /usr/bin/python3 workbench/tests/run_t093_login_chain.py --output /private/tmp/output.json\n','R'),
        ('G',own+'440502 440502 S /usr/bin/git --no-optional-locks -C '+source+' grep --cached\n','G'),
        ('incomplete','', 'incomplete')]
 observed=[]
 for name,body,role in cases:
  class Child:
   pid=440601;returncode=0
   def communicate(self,timeout=None):return body,''
  with patch.object(mod.subprocess,'Popen',return_value=Child()) as popen:
   try:value=mod.setup_quiescence(root)
   except mod.ActiveSetupProcesses as error:
    assert role in ('R','G') and error.proof['root']==str(root) and error.proof['matching_processes'][0]['role']==role
   except ValueError as error:assert role=='incomplete' and str(error)=='setup_process_inventory_incomplete'
   else:assert role is None and value['root']==str(root) and value['complete'] and value['matching_processes']==[]
   assert popen.call_args.args[0]==['/bin/ps','-ww','-axo','pid=,pgid=,stat=,command='] and popen.call_args.kwargs['start_new_session'] is True
  observed.append(name)
 return {'synthetic_inventory_cases':observed,'raw_argv_saved':False,'actual_ps_commands':0}

record('initial fixture with active setup',active_initial)
record('bound scoped process inventory',inventory)
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'synthetic filesystem and ps output; no real process inventory or existing fixture deletion','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
