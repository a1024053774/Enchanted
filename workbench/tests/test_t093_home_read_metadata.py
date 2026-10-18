"""Policy construction and recorder checks; OS behavior requires outside runs."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'src/claudeLoginSession.py'
output=Path(sys.argv[1]);assert not output.exists()
spec=importlib.util.spec_from_file_location('metadata_runtime',SOURCE)
runtime=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text(encoding='utf-8') if len(sys.argv)>2 else SOURCE.read_text(encoding='utf-8')
exec(compile(text,str(SOURCE),'exec'),vars(runtime))
checks=[]

def record(name,action):
 try:detail=action();checks.append({'check':name,'status':'PASS','detail':detail})
 except AssertionError as error:checks.append({'check':name,'status':'FAIL','business_failure':str(error)})

def policy():
 assert hasattr(runtime,'home_read_barrier'),'Node_ancestor_metadata_rule_required'
 home='/Users/fixture-user'
 readable=[('subpath',Path(home+'/project/workbench')),('literal',Path(home+'/.local/claude/2.1.302')),('literal',Path('/opt/node'))]
 rule=runtime.home_read_barrier(home,readable)
 prefix='(allow file-read-metadata '
 assert rule.count(prefix)==1,'ancestor_allowance_must_only_grant_metadata'
 before,metadata=rule.split(prefix)
 assert before=='(deny file-read* (require-all (subpath "/Users/fixture-user")(require-not (require-any (subpath "/Users/fixture-user/project/workbench") (literal "/Users/fixture-user/.local/claude/2.1.302") (literal "/opt/node")))))'
 # Expected paths are supplied by this fixture contract, not generated from
 # the product's output or traversal algorithm.
 expected={'/','/Users','/Users/fixture-user','/Users/fixture-user/project','/Users/fixture-user/.local','/Users/fixture-user/.local/claude','/opt'}
 import re
 actual=set(re.findall(r'\(literal "([^"]+)"\)',metadata))
 assert actual==expected,'metadata_allowance_must_use_exact_ancestors'
 assert metadata==''.join('(literal '+json.dumps(path)+')'+' ' for path in sorted(expected)).rstrip()+')'
 session={'real_home':home,'private_root':'/private/tmp/private','credential_home':home,'manifest':{'executable':home+'/.local/claude/2.1.302','state':'/private/tmp/state'},'forward_port':52101,'upstream_address':'127.0.0.1','upstream_port':52102,'forwarder_directory':'/private/tmp/F','metadata_directory':'/private/tmp/D'}
 profiles=runtime.policies(session)
 for role in ('C','F'):
  assert prefix in profiles[role] and '(deny file-write* (subpath "/Users/fixture-user"))' in profiles[role]
 assert prefix not in profiles['D'],'D_inventory_permissions_must_not_change'
 return {'roles':['C','F'],'exact_metadata_paths':sorted(actual),'no_new_write_or_data_allowance':True}

def fact_entry():
 assert hasattr(runtime,'home_read_barrier'),'facts_ancestor_metadata_rule_required'
 class ExecCaptured(BaseException):pass
 captured={}
 def execve(path,args,env):captured.update(path=path,args=args);raise ExecCaptured()
 with patch.object(sys,'argv',['session','--stage','facts','--audit','/private/tmp/t093-metadata-facts']),patch.object(runtime,'validate_bootstrap'),patch.object(runtime.os,'chdir'),patch.object(runtime.os,'execve',side_effect=execve):
  try:runtime.main()
  except ExecCaptured:pass
 assert captured['path']=='/usr/bin/sandbox-exec'
 profile=captured['args'][2]
 assert '(allow file-read-metadata ' in profile,'external_facts_must_allow_exact_ancestor_metadata'
 assert '(deny file-write* (subpath ' in profile and '(deny network*)' in profile and '(deny file-read* ' in profile
 return {'stage':'external facts V','metadata_rule_present':True,'HOME_write_and_data_barriers_present':True}

def recorder():
 helper=SOURCE.parents[1]/'tests/t093_home_read_boundary.ts'
 with tempfile.TemporaryDirectory(prefix='t093-read-recorder-',dir='/private/tmp') as value:
  root=Path(value);target=root/'AGENTS.md';target.write_text('public synthetic sentinel\n')
  program='import {observeHomeReadBoundary} from '+json.dumps(helper.as_uri())+'; console.log(JSON.stringify(observeHomeReadBoundary(...process.argv.slice(1))));'
  run=subprocess.run(['/opt/homebrew/bin/node','--input-type=module','-e',program,str(root),str(target),str(helper)],text=True,capture_output=True,timeout=8)
  assert run.returncode==0,'read_boundary_recorder_must_run_on_synthetic_input'
  value=json.loads(run.stdout)
  assert value['entry_resolved'] and all(v['is_directory'] for v in value['metadata'])
  assert value['content']=={'denied':False,'code':None,'bytes_read':1} and value['ancestor_directory_entries']=={'denied':False,'code':None},'read_recorder_must_report_missing_restrictions'
  try:assert value['content']['denied'] and value['content']['bytes_read']==0,'actual_HOME_content_read_must_remain_denied'
  except AssertionError as error:business=str(error)
  else:raise AssertionError('missing_data_barrier_must_fail_business_assertion')
  return {'synthetic_unprotected_file_read':True,'synthetic_directory_enumeration':True,'business_failure':business,'actual_HOME_reads':0}

record('exact ancestor metadata only',policy)
record('external facts uses same rule',fact_entry)
record('missing restriction recorder',recorder)
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x',encoding='utf-8') as stream:json.dump({'status':status,'scope':'local construction/recorder only; no OS profile/auth/actual HOME content read','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
