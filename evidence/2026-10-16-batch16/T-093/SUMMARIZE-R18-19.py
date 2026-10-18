"""Summarize saved controller OS runs, preserving small logical forwarding records."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();candidate='57c3bfb634b6908be968fcb88090293ed5d4dd65'
rows=[]
expected={'none':None,'home':'home_path_injection_must_be_reported','scanner':'credential_injection_must_be_detected',
 'counts':'missing_raw_request_must_be_detected','drop':'forwarder_record_count_must_match_upstream','empty':'credential_injection_cases_must_not_be_empty'}
for label,path,primary in [('primary','/private/tmp/t093-r18-primary-01.json','rehearsal_primary_probe'),('green','/private/tmp/t093-r18-green-01.json',None),*[(name,'/private/tmp/t093-chain-11-'+name+'.json',failure) for name,failure in expected.items()]]:
 value=json.loads(Path(path).read_text(encoding='utf-8'));facts=value['facts'];counter=value['counterexamples'];closed=value['service_receipts']['U']
 assert value['candidate']==candidate and value['primary_failure']==primary
 assert value['status']==('INCOMPLETE' if primary else 'PASS') and value['cleanup_failures']==[] and value['fixture_removed'] is True
 assert all(value[key]==0 for key in ['real_model_turns','real_cli_starts','real_upstream_requests','real_auth_reads','git_index_credential_hits'])
 assert value['port_configuration']=={'generator':'claudeLoginSession.policies','production_upstream_port':443,'test_upstream_port':18443}
 assert facts['network_boundary']=={'os_host_filter':False,'os_remote_ports':[18443],'application_host_lock':True}
 assert value['upstream_requests']==2 and facts['counts']['model_requests']==(1 if label=='drop' else 2)
 assert facts['counts']['received_requests']==2 and facts['counts']['counts_match']==(label!='drop')
 assert closed['all_closed'] and closed['startup_completed'] and closed['listeners_bound']==closed['closed_listeners']==2 and closed['close_errors']==[]
 assert value['writer_exit']['all_exited'] and all(row['exited'] for row in value['writer_exit']['groups']+value['writer_exit']['children'])
 requests=[row for row in value['forwarder_raw_records'] if row['kind']=='request'];outcomes=[row for row in value['forwarder_raw_records'] if row['kind']=='outcome']
 assert facts['counts']['ledger_requests']==len(requests) and facts['counts']['model_requests']==len(requests) and facts['counts']['outcomes']==len(outcomes)
 assert len(requests)==(1 if label=='drop' else 2) and [row['status'] for row in outcomes]==[400,200]
 assert all(row['bearer_matches_copy'] and row['messages_present'] and row['prompt_matches_fixture'] for row in value['independent_upstream_receipts'])
 if label!='drop':assert all(row['recorded_before_receipt'] for row in value['independent_upstream_receipts'])
 rows.append({'case':label,'status':value['status'],'expected_primary':primary,'primary_matched':True,'source':path,
  'port_configuration':value['port_configuration'],'network_boundary':facts['network_boundary'],'counts':facts['counts'],
  'raw_requests':len(requests),'raw_outcomes':len(outcomes),'upstream_requests':value['upstream_requests'],
  'cleanup_failures':[],'fixture_removed':True,'writer_exit_confirmed':True,'U_endpoints_closed':True,
  'real_model_turns':0,'real_upstream_requests':0,'real_cli_starts':0,'real_auth_reads':0,
  'inventory':{'pass_condition':facts['inventory']['pass_condition'],'collection_complete':facts['inventory']['collection_complete'],
    'before_entries':facts['inventory']['before_entries'],'after_entries':facts['inventory']['after_entries'],'changed':facts['inventory']['changed']},
  'credential_hits':facts['credential_scan']['hits']})
 if label=='none':
  green={'logical_forwarder_records':value['forwarder_raw_records'],'independent_upstream_receipts':value['independent_upstream_receipts'],
   'home_guards':{'parent':counter['parent_home_write'],'CLI':counter['cli']['real_home_write'],'F':counter['forwarder']['real_home_write'],
     'helpers':[{'profile':item['profile'],'real_home_write':item['real_home_write'],'fork':item['fork'],'security':item['security']} for item in counter['protected_helpers']]},
   'F_unconfigured_port':counter['forwarder']['unconfigured_port'],'CLI_bypass':counter['cli']['upstream_bypass'],
   'application_host_lock':counter['application_host_lock'],'synthetic_HOME_mutant':counter['synthetic_guard'],
   'credential_injections':counter['credential_injections'],'home_references':counter['home_references'],
   'missing_record':counter['missing_record'],'raw_record_scope':'Logical records read from original journal into saved run JSON; original byte formatting is not retained.'}
compile_path=Path('/private/tmp/t093-r18-compile-01.json');compiled=json.loads(compile_path.read_text())
assert compiled['candidate']==candidate and compiled['status']=='PASS' and len(compiled['cases'])==4
compile_rows=[{key:row[key] for key in ['mode','address','compiled','OS_host_filter','OS_remote_ports','same_generator_only_port_changed']} for row in compiled['cases']]
assert all(row['compiled'] and row['same_generator_only_port_changed'] and row['OS_remote_ports']==([443] if row['mode']=='production' else [18443]) for row in compile_rows)
verdicts=[]
for name,count in [('t093-r18-rehearsal-check-01.json',2),('t093-chain-11-check.json',6)]:
 value=json.loads((Path('/private/tmp')/name).read_text());assert value['candidate']==candidate and value['status']=='PASS' and len(value['cases'])==count and all(row['pass'] for row in value['cases'])
 verdicts.append({'source':'/private/tmp/'+name,'status':value['status'],'cases':value['cases'],'scope':value['scope']})
report={'status':'PASS','scope':__doc__,'candidate':candidate,'source':'controller #127 outside runs; worker performs saved-fact recount only',
 'production_443':'Compile only; no real upstream request performed.','test_port':18443,'compile':{'source':str(compile_path),'cases':compile_rows},
 'runs':rows,'independent_V_receipts':verdicts,'green_detail':green,'worker_new_OS_CLI_auth_network_models':0,
 'limitations':['Saved ESRCH receipts and V outputs are not new live PID probes.','No real model or real upstream validation.','HOME inventory changes are informational under user decision A.']}
with args.output.open('x',encoding='utf-8') as file:json.dump(report,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps({'status':'PASS','runs':len(rows),'compile_cases':len(compile_rows),'V_cases':[2,6]}))
