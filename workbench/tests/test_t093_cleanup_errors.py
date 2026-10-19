"""Cleanup failures identify their operation and target without file bodies."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

p=Path(__file__).with_name('cleanup_t093_retained_fixture.py').resolve();spec=importlib.util.spec_from_file_location('cleanup',p);mod=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text() if len(sys.argv)>2 else p.read_text();exec(compile(text,str(p),'exec'),vars(mod))
output=Path(sys.argv[1]);assert not output.exists();checks=[]
def record(name,action):
 try:value=action();checks.append({'check':name,'status':'PASS','detail':value})
 except AssertionError as error:checks.append({'check':name,'status':'FAIL','business_failure':str(error)})

def filesystem():
 assert hasattr(mod,'error_details'),'cleanup_failure_must_preserve_operation_path_errno'
 target='/private/tmp/t093-chain-fixture/state/denied.json'
 value=mod.error_details(PermissionError(13,'denied',target),{'operation':'read_process_metadata','path':target})
 assert value['operation']=='read_process_metadata' and value['path']==target and value['errno']==13
 return {'path_retained':True,'errno':13,'file_body_read':False}

def execution():
 assert hasattr(mod,'error_details'),'cleanup_exec_failure_must_identify_binary'
 value=mod.error_details(PermissionError(1,'not permitted','/bin/ps'),{'operation':'process_inventory_exec','path':'/bin/ps'})
 assert value['path']=='/bin/ps' and value['errno']==1 and value['operation']=='process_inventory_exec'
 return {'path':'/bin/ps','errno':1,'actual_ps_execution':False}

def process():
 assert hasattr(mod,'error_details'),'cleanup_process_probe_failure_must_identify_pid'
 value=mod.error_details(PermissionError(1,'not permitted'),{'operation':'process_signal_zero','path':None,'pid':440901})
 assert value['path'] is None and value['pid']==440901 and value['errno']==1
 return {'nonfilesystem_target_retained':True,'actual_signal':False}

def legacy():
 assert hasattr(mod,'legacy_ps_diagnostic'),'inspection_must_capture_original_ps_exec_failure'
 with patch.object(mod.subprocess,'Popen',side_effect=PermissionError(1,'not permitted','/bin/ps')):
  value=mod.legacy_ps_diagnostic()
 assert value['operation']=='legacy_observer_exec' and value['path']=='/bin/ps' and value['errno']==1 and value['metadata']['setuid'] is True
 return {'legacy_exec_target_retained':True,'actual_ps_execution':False}

def deletion_path():
 assert hasattr(mod,'error_details'),'rmtree_error_must_preserve_full_target_path'
 target='/private/tmp/t093-chain-fixture/nested/blocked.json'
 value=mod.error_details(PermissionError(13,'denied','blocked.json'),{'operation':'rmtree_unlink','path':target})
 assert value['path']==target and value['errno']==13 and value['os_filename']=='blocked.json'
 return {'full_path_retained':True,'actual_deletion':False}

def fifo():
 assert hasattr(mod,'error_details'),'special_file_failure_must_identify_path_and_kind'
 root=Path(tempfile.mkdtemp(prefix='t093-chain-fifo-unit-',dir='/private/tmp'))
 try:
  for name in ('U','S','M','state','repo','synthetic-home','source-home/.claude'):(root/name).mkdir(parents=True)
  for name in ('home','claude','tmp','shell','requests','hooks','user-data'):(root/'roles/ideation'/name).mkdir(parents=True)
  for name in ('roles/ideation/role.md','source-home/private-sentinel'):(root/name).write_text('synthetic only')
  target=root/'source-home/.claude/.credentials.json';os.mkfifo(target,0o600);context={}
  try:mod.inspect(root,context)
  except ValueError as error:value=mod.error_details(error,context)
  else:raise AssertionError('FIFO_must_be_refused_before_read')
  assert value['path']==str(target) and value['metadata']['kind']=='fifo' and value['operation']=='lstat'
  return {'FIFO_identified_without_opening':True,'retained_fixture_touched':False}
 finally:shutil.rmtree(root)

record('filesystem error target',filesystem);record('protected execution error target',execution);record('process probe error target',process);record('legacy protected exec diagnostic',legacy);record('rmtree full path',deletion_path);record('special file metadata',fifo)
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'synthetic exceptions only; no filesystem permissions changed or process inventory','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
