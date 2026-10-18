"""Actual U listen/finally block with supplied servers; no sockets or auth."""
import ast
import errno
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

source=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).with_name('t093_parallel_chain_peer.py')
tree=ast.parse(source.read_text(encoding='utf-8'))
main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
start=next(index for index,node in enumerate(main.body) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='servers' for target in node.targets))
body=[node for node in main.body[start:] if not isinstance(node,ast.Return)]
assert any(isinstance(node,ast.Try) for node in body),'actual_U_lifecycle_required'
spec=importlib.util.spec_from_file_location('session',Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
checks=[]
for case,failed_at,close_error in [('never_listened',0,False),('partial_start',1,False),('normal_close',None,False),('startup_and_close_error',1,True)]:
 with tempfile.TemporaryDirectory(prefix='t093-U-startup-unit-',dir='/private/tmp') as temporary:
  root=Path(temporary);(root/'U').mkdir();(root/'U/stop').touch()
  created=[]
  class Server:
   def __init__(self,address,handler):
    if len(created)==failed_at:raise OSError(errno.EACCES if failed_at==0 else errno.EADDRINUSE,'supplied bind failure')
    self.closed=False;created.append(self)
   def server_close(self):
    if close_error:raise OSError(errno.EIO,'supplied close failure')
    self.closed=True
  namespace={'root':root,'runtime':runtime,'fixture':{'upstream_port':18443,'other_port':51931},'own':{'pid':53941,'pgrp':53940,'profile':'U'},'session':{'deadline':0},'received':[],'Handler':object,'LocalServer':Server}
  observed=None
  try:exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(source),'exec'),namespace)
  except OSError as error:observed=error.errno
  try:
   assert observed==(None if failed_at is None else errno.EACCES if failed_at==0 else errno.EADDRINUSE),'original_bind_failure_must_not_be_masked'
   assert (root/'U/closed.json').exists(),'U_must_publish_closure_even_if_never_listened'
   closed=json.loads((root/'U/closed.json').read_text())
   assert closed['startup_completed']==(failed_at is None),'receipt_must_distinguish_startup_from_close'
   assert closed['listeners_bound']==len(created) and closed['closed_listeners']==sum(server.closed for server in created),'receipt_must_count_actual_listener_closes'
   assert closed['all_closed']==(not close_error),'failed_close_must_not_be_confirmed'
   assert bool(closed['close_errors'])==close_error,'close_errors_must_remain_separate'
   assert (root/'U/ready.json').exists()==(failed_at is None)
   if failed_at is not None:assert json.loads((root/'U/startup-failed.json').read_text())['errno']==observed
   checks.append({'case':case,'status':'PASS','listeners_bound':len(created),'all_closed':closed['all_closed']})
  except (AssertionError,KeyError) as error:checks.append({'case':case,'status':'FAIL','business_failure':str(error)})
status='PASS' if all(row['status']=='PASS' for row in checks) else 'FAIL'
with Path(sys.argv[1]).open('x',encoding='utf-8') as file:json.dump({'status':status,'scope':__doc__,'checks':checks},file,indent=2);file.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
