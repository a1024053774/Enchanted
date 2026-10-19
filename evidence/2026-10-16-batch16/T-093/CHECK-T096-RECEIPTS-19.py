"""Read-only business recount of controller-run native T096 receipts; no processes."""
import argparse
import json
from pathlib import Path
import sqlite3
import shutil
import tempfile

CANDIDATE='57c3bfb634b6908be968fcb88090293ed5d4dd65'
CASES={'tracer':(1,None,True,False),'three':(3,None,True,False),
 'no-argv':(1,'restore_argv_missing',False,False),
 'version':(1,'restore_version_mismatch',False,False),
 'no-session':(1,'restore_session_missing',False,False),
 'isolation':(3,'restore_argv_missing',False,False),'empty-reopen':(3,None,True,True)}
KEYS=[('ArrowUp','onboarding-theme'),('ArrowDown','onboarding-theme'),('Enter','onboarding-theme'),
 ('Enter','onboarding-notice'),('ArrowDown','workspace-trust'),('Enter','workspace-trust')]

def require(value,code):
 if not value:raise AssertionError(code)

def verify(repo,case,mutation=None):
 count,fault,close,empty=CASES[case];label='t093-r18b-'+case+'-01'
 summary=repo/'evidence/2026-10-16-batch16/T-096'/f'{label}.run.json'
 baseline={}
 def read_path(path):
  info=path.stat();baseline[path]=(info.st_size,info.st_mtime_ns)
  return json.loads(path.read_text(encoding='utf-8'))
 run=read_path(summary);argv=run['argv']
 option=lambda key:argv[argv.index('--'+key)+1]
 archive=Path(option('output'))
 require(archive==Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096')/label,'external_T096_output_required')
 def read(name):
  value=read_path(archive/name)
  # Counterexamples change only in-memory observations, never the originals.
  if mutation=='native_argv' and name=='ideation.resumed-argv.json':value=value[:-1]
  if mutation=='attempt' and name=='gate-after.json':value['current_attempt']={'changed':'independent-counterexample'}
  if mutation=='fault' and name=='ideation.after.json':value['pane']['restoration']['error']='unexpected_error'
  if mutation=='history' and name=='ideation.resumed-view.json':value['terminal']=''
  if mutation=='empty' and name=='empty-reopened-view.json':value['pane_keys']=['unexpected-key']
  return value
 require(run['status']=='PASS' and run['revision']==CANDIDATE and run['expectation']=='restore','frozen_success_receipt_required')
 require(option('panes')==str(count) and option('expect')=='restore' and option('claude-version')=='2.1.302' and option('startup-wait-seconds')=='600','direct_runner_arguments_must_match_contract')
 expected_fault={'no-argv':'missing-argv','version':'version-mismatch','no-session':'missing-session','isolation':'missing-argv'}.get(case)
 require(('--fault' in argv)==bool(expected_fault) and (not expected_fault or option('fault')==expected_fault),'fault_mode_must_match')
 require(('--check-close' in argv)==close and ('--check-empty-reopen' in argv)==empty,'close_modes_must_match')
 require(run['model_turns']==run['fake_posts']==0,'zero_model_and_fake_POST_budget')
 require(not any(row.get('method')=='POST' for row in read('fake-api-requests.json')),'raw_fake_POST_budget')
 require(run['cleanup_complete'] is True and run['cleanup']['cleanup_complete'] is True and run['cleanup']['writers_absent'] is True and run['cleanup']['diagnostics']==[] and not run['cleanup']['handoff'],'cleanup_must_be_complete')
 require(run['crash_observer']['exited'] is True and run['crash_observer']['diagnostics']==[],'initial_window_crash_must_be_confirmed')
 require(run['cleanup']['electron']['exited'] is True and run['cleanup']['electron']['diagnostics']==[],'final_window_exit_must_be_confirmed')
 listed={row['name']:row['status'] for row in run['checks']}
 require(len(listed)==len(run['checks']) and all(status=='PASS' for status in listed.values()),'all_unique_recorded_checks_must_pass')
 gate_before,gate_after=read('gate-before.json'),read('gate-after.json')
 require(gate_before['current_attempt']==gate_after['current_attempt'],'worker_attempt_must_not_change')
 before,after=read('before-view.json'),read('after-view.json')
 require(len(before['panes'])==len(after['panes'])==count,'pane_count_must_match')
 require([row['launch'] for row in before['panes']]==[row['launch'] for row in after['panes']],'saved_pane_order_must_match')
 commands=run['commands']
 def calls(name,thread=None):
  values=[]
  for command in commands:
   args=command['argv']
   if '--state' not in args or args[args.index('--state')+2]!=name:continue
   if thread and ('--thread' not in args or args[args.index('--thread')+1]!=thread):continue
   require(command['exit']==0,'saved_business_command_must_succeed')
   values.append(read(f'command-{command["id"]}.stdout.txt'))
  require(values,'required_saved_business_command_missing')
  return values
 events=calls('orchestration_events')[-1]['events']
 histories={row['launch']:row for row in read('synthetic-history.json')}
 role_results=[]
 for index,preset in enumerate(['ideation','executor'] if count==3 else ['ideation']):
  original=read(preset+'.before.json');record=original['record'];launch=record['id']
  observed=read(preset+'.after.json');pane=observed['pane'];view=next(row for row in after['panes'] if row['launch']==launch)
  require(record['authentication']=='isolated fake API only' and record['attempt'] is None,'native_regression_is_fake_API_controller_only')
  require(record['code_revision']==CANDIDATE and record['cli_version']=='2.1.302 (Claude Code)','controller_version_and_revision_must_match')
  require(read(preset+'.initial-argv.json')==record['argv'],'initial_native_argv_must_match')
  keys=[row for row in run['keys'] if row['launch']==launch]
  require([(row['key'],row['purpose']) for row in keys]==KEYS and len({row['screen_id'] for row in keys})==6,'six_explicit_startup_keys_required')
  successes=[event for event in events if event['launch']==launch and event['type']=='pane_restored']
  if index==0 and fault:
   require(pane['restoration']['status']=='failed' and pane['restoration']['error']==fault and pane['historical'] is True,'fault_must_refuse_exact_error_before_success')
   require(not successes and '未恢复' in view['text'] and view['input_enabled'] is False,'failed_pane_must_stay_unrestored_readonly')
   role_results.append({'role':preset,'restoration':'failed','error':fault,'success_events':0})
   continue
  require(pane['restoration']['status']=='restored' and len(successes)==1,'valid_controller_must_restore_once')
  event=successes[0]['data'];expected=[record['argv'][0],'--resume',*record['argv'][2:]]
  require(event['argv']==expected,'restore_event_argv_every_field')
  require(read(preset+'.resumed-argv.json')==expected,'native_argv_every_field')
  require(event['native_session']==pane['native_session']==record['session'],'native_session_must_match')
  require(event['version_probe']['argv']==[record['argv'][0],'--version'] and event['version_probe']['stdout'].strip()==record['cli_version'],'runtime_version_probe_must_match')
  shown=[value['launch'] for value in calls('launch_show') if value['launch']['id']==launch]
  require(shown and shown[-1]==record,'historical_launch_must_not_change')
  process=calls('pane_process_info',record['thread'])[-1]
  require(process['leader'] and not process['failed'] and process['native_session']==record['session'],'foreground_process_native_identity')
  require(process['shell_pid']==pane['shell_pid']==event['shell_pid'] and process['leader']==event['leader'] and process['leader']!=original['process']['leader'],'restored_runtime_must_have_new_observed_identity')
  require(process['observer']['method']=='macOS libproc' and process['observer']['root_pid']==process['shell_pid'],'libproc_observer_must_bind_shell')
  require(any(row['pid']==process['leader'] and row['pid']==row['pgid']==row['tpgid'] and row['command']==record['executable_path'] for row in process['processes']),'canonical_foreground_executable_must_match')
  require(view['task']==record['task'] and view['role']=='controller' and view['preset']==preset,'restored_view_binding_must_match')
  resumed_view=read(preset+'.resumed-view.json')
  require(histories[launch]['nonce'] in resumed_view['terminal'],'independent_native_history_must_be_visible')
  role_results.append({'role':preset,'restoration':'restored','argv_every_field':True,'canonical_identity':True,'history_visible':True,'historical_record_unchanged':True})
 if count==3:
  worker=next(row for row in after['panes'] if row['role']=='worker')
  require(worker['snapshot']['pane']['restoration']['error']=='restore_managed_attempt_requires_reclaim' and '未恢复' in worker['text'] and worker['input_enabled'] is False,'worker_must_stay_unrestored_readonly')
  require(not any(row['type']=='pane_restored' and row['launch']==worker['launch'] for row in events),'worker_must_have_no_restore_event')
  require(len(list((archive/'fixture/codex-home').glob('receiver-*.json')))==1,'worker_receiver_must_not_restart')
 if close:
  require(listed.get('explicit_close_persisted')=='PASS' and listed.get('close_does_not_mutate_attempt')=='PASS','explicit_close_checks_required')
 if empty:
  for name in ['empty-layout-before-reopen.json','empty-layout-after-reopen.json']:
   layout=read(name);require(layout['saved'] is True and layout['panes']==[],'saved_empty_layout_must_remain_empty')
  view=read('empty-reopened-view.json')
  require(view['panes']==[] and view['pane_keys']==[],'empty_reopen_must_have_no_panes_or_keys')
  require(listed.get('empty_reopen_does_not_open_or_authorize_worker')=='PASS' and listed.get('empty_reopen_task_unchanged')=='PASS','empty_reopen_must_not_authorize_worker_or_change_task')
  event_batches=calls('orchestration_events')
  cutoff=event_batches[-2]['events'][-1]['seq']
  require(not any(row['seq']>cutoff and row['type'] in ['pane_layout_opened','window_opened','pane_restored'] for row in event_batches[-1]['events']),'empty_reopen_raw_events_must_not_authorize_panes')
  final_task=calls('status')[-1]['task']
  if mutation=='empty_task':final_task['state']='independent-counterexample'
  require(final_task==gate_after,'empty_reopen_raw_task_must_not_change')
 require(listed.get('application_exit_preserves_panes')=='PASS','application_exit_must_preserve_saved_layout')
 database=archive/'fixture/state/state.sqlite3'
 # WAL belongs to the stopped snapshot. Keep originals read-only: one path
 # copies DB+WAL to a private disposable directory and opens only that copy.
 with tempfile.TemporaryDirectory(prefix='t093-receipt-db-',dir='/private/tmp') as temporary:
  copied=Path(temporary)/'state.sqlite3'
  for suffix in ('','-wal'):
   original=Path(str(database)+suffix)
   if original.exists():
    info=original.stat();baseline[original]=(info.st_size,info.st_mtime_ns)
    shutil.copyfile(original,Path(str(copied)+suffix))
  connection=sqlite3.connect(copied.as_uri()+'?mode=rw',uri=True)
  try:
   connection.execute('PRAGMA query_only=ON')
   layout_events=connection.execute("SELECT type,launch FROM orchestration_events WHERE task=? AND type IN ('pane_layout_opened','pane_layout_closed') ORDER BY seq",(gate_after['task_id'],)).fetchall()
  finally:connection.close()
 if mutation=='archived_layout':layout_events.append(('pane_layout_opened','independent-unexpected-reopen'))
 final_open=set()
 for kind,launch in layout_events:
  if kind=='pane_layout_opened':final_open.add(launch)
  else:final_open.discard(launch)
 expected_open=[row['launch'] for row in after['panes']]
 if close:expected_open=[] if empty else expected_open[:-1]
 require(final_open==set(expected_open),'application_exit_archived_layout_must_preserve_explicit_open_set')
 archive_meta=read_path(summary.with_suffix('').with_suffix('.archive.json'))
 require(archive_meta['archive']==str(archive/'fixture') and archive_meta['comparison'] is True and archive_meta['files']>0 and archive_meta['bytes']>0,'stopped_fixture_archive_manifest_must_match')
 require(archive_meta['excluded']=={} and 'private credential removal' in archive_meta['comparison_scope'],'archive_must_follow_private_credential_removal')
 for path,before_stat in baseline.items():
  now=path.stat();require((now.st_size,now.st_mtime_ns)==before_stat,'readonly_original_changed')
 return {'case':case,'status':'PASS','source':str(summary),'archive':str(archive),'recorded_checks':len(listed),'roles':role_results,'worker_attempt_unchanged':True,'worker_unrestored':count==3,'empty_reopen':empty,'fake_posts':0,'model_turns':0,'cleanup_complete':True,'read_only_inputs':len(baseline)}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();results=[];counterexamples=[]
 for case in CASES:
  try:results.append(verify(args.repo.resolve(),case))
  except (AssertionError,OSError,KeyError,ValueError,sqlite3.Error) as error:results.append({'case':case,'status':'INCOMPLETE','error_type':type(error).__name__,'error':str(error)})
 for case,mutation,code in [('tracer','native_argv','native_argv_every_field'),('three','attempt','worker_attempt_must_not_change'),('version','fault','fault_must_refuse_exact_error_before_success'),('tracer','history','independent_native_history_must_be_visible'),('empty-reopen','empty','empty_reopen_must_have_no_panes_or_keys'),('empty-reopen','empty_task','empty_reopen_raw_task_must_not_change'),('tracer','archived_layout','application_exit_archived_layout_must_preserve_explicit_open_set')]:
  try:verify(args.repo.resolve(),case,mutation)
  except AssertionError as error:counterexamples.append({'mutation':mutation,'case':case,'rejected':str(error)==code,'business_failure':str(error)})
  except (OSError,KeyError,ValueError,sqlite3.Error) as error:counterexamples.append({'mutation':mutation,'case':case,'rejected':False,'error_type':type(error).__name__})
  else:counterexamples.append({'mutation':mutation,'case':case,'rejected':False})
 status='PASS' if all(row['status']=='PASS' for row in results) and all(row['rejected'] for row in counterexamples) else 'INCOMPLETE'
 report={'status':status,'candidate':CANDIDATE,'source':'controller #127 direct run_restart.py invocations; wrapper not used','scope':__doc__,'cases':results,'counterexamples':counterexamples,'limitations':['Saved facts only; no new PID/CLI/OS/network/auth operations.','History is fixture-seeded, not vendor/model-generated.','Original T096 run/archive/external files are read only and remain outside this delivery.']}
 with args.output.open('x',encoding='utf-8') as file:json.dump(report,file,ensure_ascii=False,indent=2);file.write('\n')
 print(json.dumps({'status':status,'cases':len(results),'counterexamples':len(counterexamples)}));return 0 if status=='PASS' else 2

if __name__=='__main__':raise SystemExit(main())
