"""Real preparation failure path, synthetic baseline/auth failure and cleanup error."""
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import tempfile
import uuid
from unittest.mock import patch

here=Path(__file__).resolve().parent
source=here.parent/'src/claudeLoginSession.py'
spec=importlib.util.spec_from_file_location('prepare_runtime',source);runtime=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text() if len(sys.argv)>2 else source.read_text();exec(compile(text,str(source),'exec'),vars(runtime))
spec=importlib.util.spec_from_file_location('driver',here/'run_t093_login_chain.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
output=Path(sys.argv[1]);assert not output.exists();checks=[]
for secondary in (False,True):
 with tempfile.TemporaryDirectory(prefix='t093-prepare-checkpoint-unit-',dir='/private/tmp') as temporary:
  root=Path(temporary);(root/'repo').mkdir();(root/'state').mkdir();target=root/'result.json'
  manifest={'authentication':'normal-login','version':'2.1.302','credential_source':'file','upstream_url':'http://127.0.0.1:52102','root':str(root),'state':str(root/'state'),'launch':str(uuid.uuid4()),'executable':'/usr/bin/true'}
  context={'output':str(target),'candidate':'a'*40,'mutation':'none','setup_stage':'prepare_session','cleanup_failures':[]}
  observed=[];private=[];original_remove=runtime.shutil.rmtree
  def publish(error,path,pending,cleanup_error):
   context['private_root']=str(path);private.append(Path(path))
   if cleanup_error:context['cleanup_failures'].append('private_preparation_cleanup_failed')
   driver.write_setup_failure(context,error,cleanup=False)
  def cleanup(path,*args,**kwargs):
   observed.append(target.is_file() and json.loads(target.read_text())['error_summary']['type']=='RuntimeError')
   private.append(Path(path))
   if secondary:raise OSError(66,'synthetic ENOTEMPTY',str(path))
   original_remove(path,*args,**kwargs)
  parameters={'on_failure':publish} if 'on_failure' in inspect.signature(runtime.prepare).parameters else {}
  with patch.object(runtime,'collect_baseline',return_value=({},{})),patch.object(runtime,'read_auth',side_effect=RuntimeError('independent_primary_probe')),patch.object(runtime.shutil,'rmtree',side_effect=cleanup):
   try:runtime.prepare(manifest,root/'repo',52101,'127.0.0.1',60,root/'synthetic-source',**parameters)
   except Exception as error:final=driver.write_setup_failure(context,error,cleanup=False)
   else:raise AssertionError('injected_preparation_error_must_fail')
  try:
   assert observed==[True],'preparation_primary_JSON_must_precede_internal_cleanup'
   assert final['error_summary']['type']=='RuntimeError' and final['error_summary']['message']=='independent_primary_probe','preparation_cleanup_must_not_replace_primary'
   assert ('private_preparation_cleanup_failed' in final['cleanup_failures'])==secondary,'preparation_cleanup_error_must_be_secondary'
   checks.append({'secondary_cleanup_error':secondary,'status':'PASS','primary_type':'RuntimeError'})
  except AssertionError as error:checks.append({'secondary_cleanup_error':secondary,'status':'FAIL','business_failure':str(error)})
  finally:
   for path in set(private):
    if path.exists():original_remove(path)
with tempfile.TemporaryDirectory(prefix='t093-production-R-unit-',dir='/private/tmp') as temporary:
 root=Path(temporary);(root/'repo').mkdir();(root/'state').mkdir()
 manifest={'authentication':'normal-login','version':'2.1.302','credential_source':'file','upstream_url':'http://127.0.0.1:52102','root':str(root),'state':str(root/'state'),'launch':str(uuid.uuid4()),'executable':'/usr/bin/true'}
 (root/'manifest.json').write_text(json.dumps(manifest));private=[]
 def cleanup(path,*args,**kwargs):
  private.append(Path(path));reports=list((root/'state').glob('login-preparation-failure-*.json'))
  assert len(reports)==1 and json.loads(reports[0].read_text())['primary_failure']=='RuntimeError','production_R_primary_must_precede_cleanup'
  raise OSError(66,'synthetic secondary cleanup failure',str(path))
 try:
  with patch.object(sys,'argv',['session','--manifest',str(root/'manifest.json'),'--repo',str(root/'repo'),'--forward-port','52101','--upstream-address','127.0.0.1']),patch.object(runtime,'validate_bootstrap'),patch.object(runtime,'collect_baseline',return_value=({},{})),patch.object(runtime,'read_auth',side_effect=RuntimeError('independent_primary_probe')),patch.object(runtime.shutil,'rmtree',side_effect=cleanup):
   try:runtime.main()
   except RuntimeError as error:assert str(error)=='independent_primary_probe'
   else:raise AssertionError('production_R_must_rethrow_original')
  reports=[json.loads(path.read_text()) for path in (root/'state').glob('login-preparation-failure-*.json')]
  assert len(reports)==2 and {value['cleanup_pending'] for value in reports}=={True,False}
  assert all(value['primary_failure']=='RuntimeError' for value in reports)
  assert any(value['cleanup_failures']==[{'type':'OSError','errno':66}] for value in reports)
  assert all('independent_primary_probe' not in json.dumps(value) for value in reports),'production_R_must_not_publish_raw_exception_text'
  checks.append({'production_R_entry':True,'status':'PASS','immutable_primary_and_separate_cleanup':True})
 except (AssertionError,TypeError) as error:checks.append({'production_R_entry':True,'status':'FAIL','business_failure':str(error)})
 finally:
  for path in set(private):
   if path.exists():original_remove(path)
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'actual prepare + R publisher; synthetic failure, no auth read/subprocess/OS profile','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
