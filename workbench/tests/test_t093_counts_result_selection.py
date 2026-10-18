"""Single-counts result selection; supplied process queries, never an OS run."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

source=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).with_name('check_t093_chain_results.py')
spec=importlib.util.spec_from_file_location('counts_oracle',source)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
output=Path(sys.argv[1]);assert not output.exists();checks=[]
# Independent inputs: one expected mutant failure, every writer absent, original
# checkpoint before source cleanup. Permission denial and live writers are bad.
with tempfile.TemporaryDirectory(prefix='t093-counts-oracle-unit-',dir='/private/tmp') as temporary:
 directory=Path(temporary);root=Path('/private/tmp')/('t093-chain-absent-'+directory.name)
 candidate='e'*40;primary='missing_raw_request_must_be_detected';roles=('F','D','U','S','M','G0','G1','G2')
 identities={role:550910+i for i,role in enumerate(roles)}
 control={'candidate':candidate,'mutation':'counts-always-match','rehearsal':'none','status':'INCOMPLETE','primary_failure':primary,'cleanup_failures':[],'fixture_removed':True,
  **{k:0 for k in ('real_model_turns','real_cli_starts','real_upstream_requests','real_auth_reads','git_index_credential_hits')},
  'fixture_root':str(root),'checkpoint_sequence':3,
  'processes':{**{role:{'pgrp':identities[role]} for role in roles[:5]},'G':[{'pid':identities[role]} for role in roles[5:]],'C':[{'pid':550901},{'pid':550902}]},
  'writer_exit':{'all_exited':True,'daemon_closed':True,'groups':[{'role':role,'pgrp':identities[role],'exited':True} for role in roles],'children':[{'pid':550901,'exited':True}],'reporter_pid':550902},
  'source_home_cleanup':{'profile':'D test source cleanup','source_home':str(root/'source-home'),'removed':True,'credential_body_read':False,'checkpoint_sequence':2},
  'service_receipts':{'D_guards':{'source_content_read':{'denied':True,'bytes_read':0,'errno':1}}},
  'counterexamples':{'foreground_process_query':{'observer':{'method':'macOS libproc','root_pid':550900},'shell_pid':550900,'leader':550903,'processes':[{'pid':550903,'pgid':550903,'tpgid':550903,'command':str(root/'fake-claude')}]}}}
 control['port_configuration']={'generator':'claudeLoginSession.policies','production_upstream_port':443,'test_upstream_port':18443}
 control['facts']={'network_boundary':{'os_host_filter':False,'os_remote_ports':[18443],'application_host_lock':True}}
 control['processes']['U']['pid']=550930
 control['service_receipts']['U']={'pid':550930,'pgrp':identities['U'],'all_closed':True,'startup_completed':True,'listeners_bound':2,'closed_listeners':2,'close_errors':[]}
 control['counterexamples']['application_host_lock']={'status':'PASS','checks':[{'case':name,'status':'PASS','connections_started':0 if denied else 1,'recorded_error':'upstream_host_mismatch' if denied else None} for name,denied in [('configured',False),('incoming_host_ignored',False),('non_configured_target',True),('lookup_hostname_mismatch',True),('redirect_not_followed',False)]]}
 history=[{'sequence':1,'phase':'business_pending','primary_failure':None},{'sequence':2,'phase':'cleanup_pending','primary_failure':primary},{'sequence':3,'phase':'complete','primary_failure':primary,'fixture_removed':True}]
 for case in ('counts_only','cleanup_failure','permission_unknown','writer_alive','wrong_primary','wrong_case','wrong_candidate','duplicate','default_requires_all_six','rehearsal_conflict','wrong_port','U_not_closed','U_wrong_owner'):
  value=copy.deepcopy(control);target=directory/(case+'.input.json');verdict=directory/(case+'.verdict.json')
  if case=='cleanup_failure':value['cleanup_failures']=['upstream_shutdown_unconfirmed']
  if case=='wrong_primary':value['primary_failure']='unexpected_failure'
  if case=='wrong_case':value['mutation']='scanner-zero'
  if case=='wrong_candidate':value['candidate']='f'*40
  if case=='wrong_port':value['facts']['network_boundary']['os_remote_ports']=[443]
  if case=='U_not_closed':value['service_receipts']['U']['all_closed']=False
  if case=='U_wrong_owner':value['service_receipts']['U']['pid']=550999
  target.write_text(json.dumps(value));Path(str(target)+'.events.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in history))
  argv=['check','--guarded','--candidate',candidate,'--output',str(verdict)]
  if case!='default_requires_all_six':argv.append('--counts-only')
  if case=='rehearsal_conflict':argv.append('--rehearsal')
  argv.append(str(target))
  if case=='duplicate':argv.append(str(target))
  def probe(identity,signal):
   assert signal==0
   if case=='permission_unknown':raise PermissionError(1,'supplied EPERM')
   if case=='writer_alive':return
   raise ProcessLookupError()
  try:
   with patch.object(sys,'argv',argv),patch.object(mod.os,'kill',side_effect=probe),patch.object(mod.os,'killpg',side_effect=probe),patch.object(mod.os,'execve',side_effect=AssertionError('OS execution forbidden in logic test')),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    try:rc=mod.main()
    except SystemExit as error:rc=error.code
   result=json.loads(verdict.read_text()) if verdict.exists() else None
   if case=='counts_only':
    assert rc==0 and result and result['status']=='PASS','counts_only_must_accept_complete_single_case'
    assert len(result['cases'])==1 and result['cases'][0]['case']=='counts-always-match','single_case_scope_must_be_explicit'
   else:assert rc==2 and (not result or result['status']=='INCOMPLETE'),'invalid_or_unconfirmed_case_must_fail'
   checks.append({'case':case,'status':'PASS','verdict':result['status'] if result else 'argument_rejected'})
  except AssertionError as error:checks.append({'case':case,'status':'FAIL','business_failure':str(error)})
status='PASS' if all(row['status']=='PASS' for row in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'actual checker main with supplied PID queries and independent receipts; no profile/network/auth','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
