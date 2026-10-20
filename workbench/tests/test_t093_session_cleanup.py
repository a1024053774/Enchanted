"""Synthetic metadata/close and preparation checks. No OS profile/network/auth."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import uuid
from unittest.mock import patch

HERE=Path(__file__).resolve().parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

probe=load('parallel',HERE/'probe_t093_parallel_profiles.py')
runtime=load('session',HERE.parent/'src/claudeLoginSession.py')
output=Path(sys.argv[1]);assert not output.exists()
checks=[]
class Server:
 def __init__(self,*args):self.timeout=1
 def server_close(self):pass

def exercise(function,fail):
 with tempfile.TemporaryDirectory(prefix='t093-U-close-unit-',dir='/private/tmp') as temporary:
  root=Path(temporary);(root/'U').mkdir();(root/'U/stop').write_text('');(root/'C-attempts.json').write_text('[]')
  home=root/'synthetic-home';home.mkdir();(home/'.claude').mkdir()
  options={'root':str(root),'real_home':str(home),'upstream_port':52101,'other_port':52102,'deadline_ms':int(time.time()*1000)+5000}
  with patch.object(probe,'LocalHTTPServer',Server):
   if fail:
    with patch.object(probe,'local_inventory',side_effect=RuntimeError('synthetic_inventory_failure')):
     try:function(options)
     except RuntimeError:pass
   else:function(options)
  return {'closed':(root/'U/closed.json').exists(),'after':(root/'U/inventory-after.json').exists()}

normal=exercise(probe.upstream_server,False);assert normal=={'closed':True,'after':True}
failed=exercise(probe.upstream_server,True);assert failed=={'closed':False,'after':False},'U_closed_must_include_post_inventory'
checks.append('same Python process collects after inventory before acknowledging close; failure does not acknowledge')
# Recreate the original early-ack failure through the actual function body.
tree=ast.parse((HERE/'probe_t093_parallel_profiles.py').read_text())
function=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='upstream_server'))
idx=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='upstream_after')
function.body[idx],function.body[idx+1]=function.body[idx+1],function.body[idx]
namespace=dict(vars(probe));exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'early-ack-mutant','exec'),namespace)
# Its global helpers are patched through the mutated function namespace.
namespace['LocalHTTPServer']=Server;namespace['local_inventory']=lambda *args:(_ for _ in ()).throw(RuntimeError('synthetic_inventory_failure'))
mutant=exercise(namespace['upstream_server'],True)
assert mutant['closed'] and not mutant['after']
try:assert not mutant['closed'],'U_closed_must_include_post_inventory'
except AssertionError as error:mutant_failure=str(error)
assert mutant_failure=='U_closed_must_include_post_inventory'
checks.append('early closed acknowledgement mutant rejected by business assertion')

with tempfile.TemporaryDirectory(prefix='t093-session-unit-',dir='/private/tmp') as temporary:
 root=Path(temporary)
 for name in ('state','repo','source-home/.claude'):(root/name).mkdir(parents=True)
 oauth={'accessToken':'synthetic-session-unit-token','expiresAt':(time.time()+600)*1000}
 (root/'source-home/.claude/.credentials.json').write_text(json.dumps({'claudeAiOauth':oauth,'unrelated':'do-not-copy'}))
 manifest={'authentication':'normal-login','version':'2.1.304','credential_source':'file','upstream_url':'https://configured.invalid/','root':str(root),'state':str(root/'state'),'launch':str(uuid.uuid4()),'executable':'/usr/bin/true'}
 order=[];original_auth=runtime.read_auth
 def baseline(value):order.append('baseline');return {},{'profile':'D simulated in unit'}
 def copied(*args):order.append('auth');return original_auth(*args)
 with patch.object(runtime,'collect_baseline',side_effect=baseline),patch.object(runtime,'read_auth',side_effect=copied) as auth,patch('socket.getaddrinfo',side_effect=AssertionError('DNS_must_not_run')):
  session=runtime.prepare(manifest,root/'repo',52101,'127.0.0.1',60,root/'source-home',on_failure=lambda *args:None)
  assert auth.call_count==1
  assert order==['baseline','auth'],'before_inventory_must_precede_original_auth_read'
 try:
  private=Path(session['private_root']);copied=runtime.read(private/'home/.claude/.credentials.json')
  assert list(copied)==['claudeAiOauth']
  assert runtime.read(private/'home/.claude/.claude.json')=={'hasCompletedOnboarding':True,'projects':{str(root/'repo'):{'hasTrustDialogAccepted':True}}}
  assert session['upstream_port']==443 and '(remote tcp4 "*:443")' in session['profiles']['F']
  assert '(deny process-fork)' in session['profiles']['F'] and '(deny process-fork)' in session['profiles']['D']
  assert '(allow network-bind network-inbound (literal '+json.dumps(str(root/'state/control.sock'))+'))' in session['profiles']['C']
  assert all(p.count('(version 1)')==1 for p in session['profiles'].values())
 finally:shutil.rmtree(private)
checks.append('one synthetic auth read; only OAuth copied; generated minimal state; F OS allows TCP 443 without host filter; no DNS or nested profile')
with tempfile.TemporaryDirectory(prefix='t093-session-paths-',dir='/private/tmp') as temporary:
 root=Path(temporary)
 for name in ('state','repo','source-home/.claude','redirect'):(root/name).mkdir(parents=True)
 (root/'source-home/.claude/.credentials.json').write_text(json.dumps({'claudeAiOauth':oauth}))
 base={**manifest,'root':str(root),'state':str(root/'state'),'launch':'../../redirect'}
 with patch.object(runtime,'read_auth',wraps=runtime.read_auth) as auth:
  try:runtime.prepare(base,root/'repo',52101,'127.0.0.1',60,root/'source-home',on_failure=lambda *args:None)
  except ValueError as error:assert str(error)=='invalid_controller_identity'
  else:raise AssertionError('invalid_launch_path_must_fail_before_auth')
  assert auth.call_count==0
 (root/'state/login-audits').symlink_to(root/'redirect',target_is_directory=True)
 base['launch']=str(uuid.uuid4())
 try:runtime.prepare(base,root/'repo',52101,'127.0.0.1',60,root/'source-home',on_failure=lambda *args:None)
 except ValueError as error:assert str(error)=='canonical_audit_path_required'
 else:raise AssertionError('audit_parent_symlink_must_be_rejected')
 assert not list((root/'redirect').iterdir())
checks.append('invalid launch path rejected before auth; audit parent symlink rejected before public writes')
cleanup_cases=[]
for cancelled,lost in ((False,False),(True,False),(False,True)):
 with tempfile.TemporaryDirectory(prefix='t093-D-cleanup-unit-',dir='/private/tmp') as temporary:
  root=Path(temporary);private=root/'private';metadata=root/'receipts';home=root/'synthetic-real-home'
  for path in (private/'metadata',private/'home',metadata,home):path.mkdir(parents=True,exist_ok=True)
  (private/'home/owned-copy').write_text('synthetic only')
  runtime.save(private/'metadata/before.json',{})
  runtime.save(private/'services.json',{'F':{'pid':440101,'pgrp':440001}})
  (private/'owned-groups.jsonl').write_text(json.dumps({'role':'F','pid':440101,'pgrp':440001})+'\n'+json.dumps({'role':'U','pid':440102,'pgrp':440002})+'\n')
  if cancelled:(metadata/'abort').write_text('')
  else:runtime.save(metadata/'stop.json',{});(metadata/'cleanup').write_text('')
  called=[]
  def fake_group(group,kind):
   if kind==0:raise ProcessLookupError()
   called.append(group)
  session={'private_root':str(private),'metadata_directory':str(metadata),'real_home':str(home),'c_root_pid':330001,'deadline':time.time()+10}
  with patch.object(runtime.os,'killpg',side_effect=fake_group),patch.object(runtime.os,'getpgid',side_effect=lambda pid:440999 if lost else {440101:440001,440102:440002}[pid]),patch.object(runtime.os,'kill'),patch.object(runtime.signal,'signal'),patch.object(runtime.signal,'setitimer'):
   code=runtime.metadata_service(session)
  receipt=runtime.read(metadata/'removed.json')
  if lost:
   assert code==2 and receipt['cleanup_failures']==['owned_group_identity_lost'] and private.exists() and not called
  else:
   assert receipt['isolated_home_removed'] and not receipt['cleanup_failures'] and not private.exists()
   assert code==(2 if cancelled else 0)
  assert 330001 not in called,'explicit_cancel_must_not_kill_reporting_C_root'
  assert set(called)==(set() if lost else {440001,440002} if cancelled else {440001})
  cleanup_cases.append({'cancelled':cancelled,'identity_lost':lost,'returncode':code,'removed':receipt['isolated_home_removed'],'groups_targeted':called})
checks.append('D removes the whole private root after normal ack or explicit cancellation; only owned groups targeted; reporting C root survives cancellation')
result={'status':'PASS','scope':'synthetic local logic only; no Security query, OS profile, true HOME write or network; D signals mocked','checks':checks,'D_cleanup_cases':cleanup_cases,'early_ack_mutant':{'observed':mutant,'business_failure':mutant_failure}}
with output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks)}))
