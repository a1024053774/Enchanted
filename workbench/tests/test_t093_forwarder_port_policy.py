"""Revised F port contract, pure policy generation; no sandbox/network/auth calls."""
import importlib.util
import ast
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

source=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py'
spec=importlib.util.spec_from_file_location('port_policy',source)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
output=Path(sys.argv[1]);assert not output.exists();checks=[]
for address,port in [('127.0.0.1',443),('203.0.113.31',443),('127.0.0.1',18443),('203.0.113.31',52321)]:
 try:
  session={'real_home':'/private/tmp/t093-policy-home','private_root':'/private/tmp/t093-policy-private','credential_home':'/private/tmp/t093-policy-home','forward_port':54111,'upstream_port':443,'upstream_address':address,'forwarder_directory':'/private/tmp/t093-policy-state/forwarder','metadata_directory':'/private/tmp/t093-policy-state/metadata','manifest':{'state':'/private/tmp/t093-policy-state','executable':'/usr/bin/true'}}
  baseline=mod.policies(session)
  session['upstream_port']=port
  policies=mod.policies(session);f=policies['F'];c=policies['C']
  assert f'(remote tcp4 "*:{port}")' in f,'F_OS_must_use_the_supplied_port'
  assert f.replace(f'(remote tcp4 "*:{port}")','(remote tcp4 "*:443")')==baseline['F'],'same_generator_must_change_only_the_remote_port'
  assert policies['C']==baseline['C'] and policies['D']==baseline['D'],'other_profiles_must_not_change_for_test_port'
  assert '(remote tcp4 "*:*")' not in f and address not in f,'F_OS_must_not_claim_numeric_host_enforcement'
  assert '(remote tcp4 "localhost:54111")' in c and '(remote tcp4 "*:443")' not in c,'CLI_must_keep_forwarder_only_network'
  assert '(deny process-fork)' in f and '(deny file-write* (subpath "/private/tmp/t093-policy-home"))' in f,'other_F_boundaries_must_remain'
  checks.append({'case':address,'status':'PASS','OS_host_filter':False,'OS_outbound_port':port})
 except AssertionError as error:checks.append({'case':address,'port':port,'status':'FAIL','business_failure':str(error)})
for url,address in [('https://configured.fixture.invalid:444','203.0.113.31'),('http://127.0.0.1:8080','127.0.0.1'),('https://configured.fixture.invalid:0','203.0.113.31')]:
 with tempfile.TemporaryDirectory(prefix='t093-port-unit-',dir='/private/tmp') as temporary:
  root=Path(temporary);manifest={'authentication':'normal-login','version':'2.1.302','credential_source':'file','launch':'11111111-1111-4111-8111-111111111111','executable':str(Path('/usr/bin/true').resolve()),'upstream_url':url,'root':str(root),'state':str(root/'state')}
  try:
   with patch.object(mod,'read_auth',side_effect=AssertionError('auth_read_forbidden')),patch.object(mod,'collect_baseline',side_effect=AssertionError('OS_process_forbidden')):
    try:mod.prepare(manifest,root/'repo',54111,address,60,root/'source-home',on_failure=lambda *_args:None)
    except ValueError as error:assert str(error)=='upstream_port_443_required','non_443_must_fail_with_port_contract'
    else:raise AssertionError('non_443_upstream_must_be_rejected')
   checks.append({'case':url,'status':'PASS','rejected_before_auth_or_OS':True})
  except BaseException as error:checks.append({'case':url,'status':'FAIL','business_failure':'non_443_must_be_rejected_before_auth_or_OS','observed_type':type(error).__name__})
class BaselineReached(Exception):pass
for target,accepted in [(18443,True),(18444,False)]:
 with tempfile.TemporaryDirectory(prefix='t093-test-port-unit-',dir='/private/tmp') as temporary:
  root=Path(temporary);manifest={'authentication':'normal-login','version':'2.1.302','credential_source':'file','launch':'11111111-1111-4111-8111-111111111111','executable':str(Path('/usr/bin/true').resolve()),'upstream_url':f'http://127.0.0.1:{target}','root':str(root),'state':str(root/'state')}
  try:
   with patch.object(mod,'read_auth',side_effect=AssertionError('auth_read_forbidden')),patch.object(mod,'collect_baseline',side_effect=BaselineReached):
    try:mod.prepare(manifest,root/'repo',54111,'127.0.0.1',60,root/'source-home',on_failure=lambda *_args:None,upstream_port=18443)
    except BaselineReached:assert accepted,'mismatched_test_port_must_fail_before_baseline'
    except ValueError as error:assert not accepted and str(error)=='upstream_port_mismatch','configured_test_port_must_reach_baseline'
    else:raise AssertionError('expected_validation_or_baseline_boundary')
   checks.append({'case':'test_prepare_'+str(target),'status':'PASS','auth_or_OS_calls':0})
  except (AssertionError,TypeError) as error:checks.append({'case':'test_prepare_'+str(target),'status':'FAIL','business_failure':str(error)})
try:
 tree=ast.parse(source.read_text())
 entry=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='prepare']
 assert len(entry)==1 and any(arg.arg=='upstream_port' and isinstance(arg.value,ast.Constant) and arg.value.value==443 for arg in entry[0].keywords),'production_entry_must_explicitly_fix_443'
 checks.append({'case':'production_entry_fixed_443','status':'PASS'})
except AssertionError as error:checks.append({'case':'production_entry_fixed_443','status':'FAIL','business_failure':str(error)})
status='PASS' if all(row['status']=='PASS' for row in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'policy source and prepare validation only; no compiler/OS boundary proof','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
