"""Synthetic R regressions: timeout ownership, original diagnostics, secrecy.

No OS profile or real Git child runs. Failures must preserve the primary error,
reap their owned child, identify the failed step, and never persist auth bytes.
"""
import ast
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

SOURCE=Path(__file__).with_name('run_t093_login_chain.py').resolve()
output=Path(sys.argv[1]);assert not output.exists()
text=Path(sys.argv[2]).read_text(encoding='utf-8') if len(sys.argv)>2 else SOURCE.read_text(encoding='utf-8')
spec=importlib.util.spec_from_file_location('setup_driver',SOURCE)
driver=importlib.util.module_from_spec(spec);exec(compile(text,str(SOURCE),'exec'),vars(driver))
checks=[]
def record(name,action):
 try:value=action();checks.append({'check':name,'status':'PASS','detail':value})
 except AssertionError as error:checks.append({'check':name,'status':'FAIL','business_failure':str(error)})

def timeout():
 calls=[]
 directory=tempfile.TemporaryDirectory(prefix='t093-G-checkpoint-unit-',dir='/private/tmp')
 checkpoint=Path(directory.name)/'result.json'
 class Child:
  pid=440301
  returncode=None
  def poll(self):return self.returncode
  def communicate(self,data=None,timeout=None):
   calls.append(('wait',timeout))
   if len([v for v in calls if v[0]=='wait'])==1:raise subprocess.TimeoutExpired(['git'],timeout,stderr=b'original timeout stderr')
   self.returncode=-9;return b'',b'original timeout stderr'
 child=Child()
 def kill(group,kind):
  calls.append(('signal',int(kind)))
  if kind==0:raise ProcessLookupError()
  assert group==child.pid
  assert checkpoint.is_file() and json.loads(checkpoint.read_text())['primary_failure']=='protected_chain_setup_failed','R_primary_JSON_must_exist_before_Git_termination'
 context={'setup_stage':'git_credential_scan','processes':[],'cleanup_failures':[],'output':str(checkpoint)}
 if hasattr(driver,'run_git'):
  with patch.object(driver.subprocess,'Popen',return_value=child),patch.object(driver.os,'killpg',side_effect=kill):
   try:driver.run_git(Path('/private/tmp/source'),'synthetic G',['grep'],context,timeout=90)
   except subprocess.TimeoutExpired:pass
   else:raise AssertionError('Git_timeout_must_preserve_original_exception')
 else:
  tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  function=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='git')
  namespace={'subprocess':driver.subprocess,'g':'synthetic G','processes':[],'source':Path('/private/tmp/source')}
  exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'old_nested_git','exec'),namespace)
  with patch.object(driver.subprocess,'Popen',return_value=child):
   try:namespace['git'](['grep'])
   except subprocess.TimeoutExpired:pass
 assert ('signal',int(signal.SIGKILL)) in calls and len([v for v in calls if v[0]=='wait'])==2,'timed_out_Git_child_must_be_terminated_and_reaped'
 assert context['last_git']['stderr']=='original timeout stderr','Git_timeout_stderr_must_be_preserved'
 directory.cleanup()
 return {'original_timeout_preserved':True,'owned_child_terminated_and_reaped':True,'actual_process_signals':0}

def budget():
 tree=ast.parse(text)
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 scan_calls=[n for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run_git' and any(isinstance(arg,ast.List) and arg.elts and isinstance(arg.elts[0],ast.Constant) and arg.elts[0].value=='grep' for arg in n.args)]
 assert len(scan_calls)==1,'credential_scan_must_have_one_explicit_Git_call'
 limit=next((n.value.value for n in scan_calls[0].keywords if n.arg=='timeout' and isinstance(n.value,ast.Constant)),None)
 assert isinstance(limit,(int,float)) and 19.325<limit<=90,'full_index_scan_budget_must_cover_observed_19_seconds_and_remain_bounded'
 return {'scan_budget_seconds':limit,'scan_call_count':1,'no_retry':True}

def diagnostics():
 assert hasattr(driver,'write_setup_failure'),'R_failure_must_write_original_error_summary'
 with tempfile.TemporaryDirectory(prefix='t093-R-diagnostic-unit-',dir='/private/tmp') as value:
  root=Path(value);fixture=root/'fixture';(fixture/'source-home/.claude').mkdir(parents=True)
  secret='synthetic-diagnostic/"\\-private-token'
  (fixture/'source-home/.claude/.credentials.json').write_text('synthetic only')
  import base64
  from urllib.parse import quote
  independent_variants=[secret,json.dumps(secret)[1:-1],quote(secret,safe='').lower(),base64.b64encode(secret.encode()).decode(),base64.urlsafe_b64encode(secret.encode()).decode().rstrip('=')]
  context={'setup_stage':'git_credential_scan','fixture_root':str(fixture),'output':str(root/'result.json'),'candidate':'a'*40,'mutation':'none','secrets':[secret],
           'processes':[],'cleanup_failures':[],'last_git':{'operation':'git_credential_scan','returncode':2,'stderr':'denied '+' '.join(independent_variants),'stdout':'original stdout'}}
  error=OSError(1,'original failure '+secret)
  original_remove=driver.shutil.rmtree
  def remove_after_checkpoint(path):
   assert (root/'result.json').is_file(),'R_primary_JSON_must_exist_before_source_cleanup'
   checkpoint=json.loads((root/'result.json').read_text())
   assert checkpoint['primary_failure']=='protected_chain_setup_failed' and checkpoint['error_summary']['errno']==1,'R_primary_error_must_precede_cleanup'
   original_remove(path)
  with patch.object(driver.shutil,'rmtree',side_effect=remove_after_checkpoint):
   result=driver.write_setup_failure(context,error)
  raw=(root/'result.json').read_text();saved=json.loads(raw)
  assert saved['setup_stage']=='git_credential_scan' and saved['error_summary']['type']=='PermissionError','R_failure_must_identify_stage_and_original_type'
  assert 'original failure' in saved['error_summary']['message'] and saved['error_summary']['errno']==1,'R_failure_must_preserve_sanitized_original_message'
  assert saved['last_git']['stderr'].startswith('denied ') and '<CREDENTIAL>' in raw,'Git_stderr_must_be_sanitized_and_preserved'
  assert saved['source_credentials_removed'] and not (fixture/'source-home/.claude').exists(),'setup_failure_must_remove_generated_credential_directory'
  assert saved['fixture_removed'] is False and fixture.exists(),'setup_failure_must_preserve_noncredential_fixture'
  for sample in independent_variants:assert sample not in raw,'setup_diagnostics_must_not_expose_credentials'
  assert result['primary_failure']=='protected_chain_setup_failed'
  return {'original_message_retained':True,'synthetic_credentials_removed':True,'noncredential_fixture_preserved':True,'public_secret_hits':0}

def cleanup_error():
 assert hasattr(driver,'run_git'),'Git_cleanup_must_preserve_primary_timeout'
 class Child:
  pid=440302
  def poll(self):return None
  def communicate(self,data=None,timeout=None):
   if timeout==90:raise subprocess.TimeoutExpired(['git'],90,stderr=b'partial original stderr')
   raise OSError(1,'synthetic reap failure')
 context={'setup_stage':'git_credential_scan','processes':[],'cleanup_failures':[]}
 with patch.object(driver.subprocess,'Popen',return_value=Child()),patch.object(driver.os,'killpg'):
  try:driver.run_git(Path('/private/tmp/source'),'synthetic G',['grep'],context,timeout=90)
  except Exception as error:observed=error
 assert isinstance(observed,subprocess.TimeoutExpired) and observed.timeout==90,'cleanup_error_must_not_mask_original_Git_timeout'
 assert context['cleanup_failures']==['setup_Git_reap_unconfirmed']
 assert context['last_git'].get('stderr')=='partial original stderr','cleanup_error_must_not_discard_partial_original_stderr'
 return {'original_timeout_seconds':90,'secondary_reap_failure_reported':True}

def main_context():
 assert hasattr(driver,'run_git'),'main_setup_must_keep_diagnostic_context'
 with tempfile.TemporaryDirectory(prefix='t093-R-main-unit-',dir='/private/tmp') as value:
  context={};calls=[];target=Path(value)/'result.json'
  def git(source,profile,arguments,ctx,input_text=None,timeout=15):
   calls.append((ctx['setup_stage'],timeout))
   if arguments[0]=='rev-parse':return 0,'a'*40+'\n'
   if arguments[0]=='diff':return 0,''
   assert arguments[0]=='grep' and timeout==90
   raise subprocess.TimeoutExpired(['synthetic git'],timeout)
  with patch.object(sys,'argv',['chain','--output',str(target),'--source-revision','a'*40]),patch.object(driver,'load_module',return_value=types.SimpleNamespace(validate_bootstrap=lambda:None)),patch.object(driver,'run_git',side_effect=git):
   try:driver.main(context)
   except subprocess.TimeoutExpired as error:result=driver.write_setup_failure(context,error)
   else:raise AssertionError('injected_Git_timeout_must_reach_R_failure_writer')
  try:
   assert calls==[('git_revision',15),('git_clean_sources',15),('git_credential_scan',90)]
   assert result['setup_stage']=='git_credential_scan' and result['error_summary']['timeout_seconds']==90
   assert result['source_credentials_removed'] and not (Path(context['fixture_root'])/'source-home/.claude').exists()
  finally:driver.shutil.rmtree(context['fixture_root'])
  return {'actual_main_reached_git_scan':True,'protected_services_or_auth_reads':0,'generated_credential_directory_removed':True}

record('owned Git timeout cleanup',timeout)
record('bounded scan covers observed duration',budget)
record('original R error and no credential leakage',diagnostics)
record('cleanup failure remains secondary',cleanup_error)
record('actual main stage context',main_context)
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x',encoding='utf-8') as stream:json.dump({'status':status,'scope':'synthetic exception/child fixtures; no OS profile, real Git, auth or model','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
