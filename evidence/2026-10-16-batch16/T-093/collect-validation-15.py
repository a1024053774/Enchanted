"""只整理指定的既有 JSON；不启动链路、查询进程、读取 auth 或判定新候选。"""
import argparse
import json
from pathlib import Path

OLD='079842e8b6808fa95a7e6f2efbd5fce2c8d1e0ac'
NEW='fb39d14f14588bb2634f110b2a5a13d6187b4513'
GROUPS={
 'chain-07':(OLD,['green','home','scanner','counts','drop','empty']),
 'chain-08':(NEW,['counts']),
 'rehearsal-04':(OLD,['primary','green']),
}
def select(value,keys):return {key:value[key] for key in keys if key in value}
def summarize(value,details):
 facts=value.get('facts') or {};counter=value.get('counterexamples',{});proof=value.get('writer_exit',{})
 result=select(value,['candidate','status','mutation','rehearsal','primary_failure','failure_stage','cleanup_failures','fixture_root','fixture_removed','upstream_requests','real_model_turns','real_cli_starts','real_upstream_requests','real_auth_reads','git_index_credential_hits','checks','checkpoint_sequence'])
 result['cleanup_errors']=[select(row,['step','type','message','code','errno','path']) for row in value.get('cleanup_errors',[])]
 result['writer_exit']={'all_exited':proof.get('all_exited'),'daemon_closed':proof.get('daemon_closed'),'group_count':len(proof.get('groups',[])),'child_count':len(proof.get('children',[])),'all_group_rows_exited':all(row.get('exited') is True for row in proof.get('groups',[])),'all_child_rows_exited':all(row.get('exited') is True for row in proof.get('children',[]))}
 result['facts']={'counts':facts.get('counts'),'credential_scan':facts.get('credential_scan'),'isolated_home_removed':facts.get('isolated_home_removed'),'auth_original_reads':facts.get('auth_original_reads'),
  'inventory':select(facts.get('inventory',{}),['pass_condition','acceptance_basis','collection_complete','before_phase','after_phase','scope','excludes','before_entries','after_entries','changed','differences','attribution']),
  'onboarding':facts.get('onboarding'),'cleanup':facts.get('cleanup')}
 result['upstream_receipts']=value.get('independent_upstream_receipts',[])
 result['counterexamples']=select(counter,['home_references','credential_injection_case_count','credential_injections','missing_record'])
 if details:
  result['boundary_observations']=select(counter,['home_read_boundary_C','parent_home_write','cli','forwarder','protected_helpers','synthetic_guard','foreground_process_query'])
  result['processes']=value.get('processes');result['source_home_cleanup']=value.get('source_home_cleanup')
  result['home_probe_absence']=facts.get('processes',{}).get('D',{}).get('home_probe_paths')
  result['writer_exit']=proof
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source',type=Path,default=Path('/private/tmp'))
 parser.add_argument('--output-dir',type=Path,required=True)
 args=parser.parse_args();pending={};manifest=[]
 for group,(candidate,labels) in GROUPS.items():
  runs=[]
  for label in labels:
   path=args.source/('t093-'+group+'-'+label+'.json');data=json.loads(path.read_text(encoding='utf-8'))
   if data.get('candidate')!=candidate:raise ValueError('source_candidate_mismatch: '+path.name)
   runs.append({'source':str(path),'observed':summarize(data,group=='chain-08' or group=='chain-07' and label=='green')})
   events=Path(str(path)+'.events.jsonl');history=[json.loads(line) for line in events.read_text(encoding='utf-8').splitlines()]
   if not history or history[-1].get('sequence')!=data.get('checkpoint_sequence'):raise ValueError('checkpoint_history_mismatch: '+events.name)
   manifest.extend([{'original':str(path),'bytes':path.stat().st_size,'group':group,'kind':'run_json','candidate':candidate,'summary':group+'-summary-15.json','summary_case':label},
                    {'original':str(events),'bytes':events.stat().st_size,'group':group,'kind':'checkpoint_history','candidate':candidate,'records':len(history),'retained':events.name.replace('t093-','',1)}])
   pending[events.name.replace('t093-','',1)]=events.read_bytes()
  check_name='t093-'+group+('-counts-check.json' if group=='chain-08' else '-check.json')
  check_path=args.source/check_name;check=json.loads(check_path.read_text(encoding='utf-8'))
  if check.get('candidate')!=candidate:raise ValueError('checker_candidate_mismatch')
  stored=check_name.replace('t093-','',1)
  # Preserve identical earlier copies; a fresh output directory receives all three.
  pending[stored]=check_path.read_bytes()
  manifest.append({'original':str(check_path),'bytes':check_path.stat().st_size,'group':group,'kind':'independent_V','candidate':candidate,'retained':stored,'observed_status':check['status']})
  pending[group+'-summary-15.json']=(json.dumps({'status':check['status'],'candidate':candidate,'controller_report':'主控 #116 / #27' if group!='chain-08' else '主控 #117 / #28','scope':'Existing run facts only; no new execution or cross-revision verdict.','runs':runs,'independent_check':check},ensure_ascii=False,indent=2)+'\n').encode()
 pending['VALIDATION-MANIFEST-15.json']=(json.dumps({'status':'PASS','scope':'指定三组原始 JSON 与 checkpoint 历史的文本清单；不是新验收结论。','current_product_revision':NEW,'mixed_revisions':True,'same_revision_full_suite_rerun':False,'files':manifest,'raw_files_deleted':False,'archive_performed':False,'large_fixtures_sqlite_binaries_auth_copied':False,'replay_note':'业务重放须使用清单中 candidate 的受管工作区和新输出；EVIDENCE-RECHECK-03.sh 分别指定原 mutation，REHEARSE-CHAIN-01.sh 指定 primary/green。V 只核对同一 candidate；chain08 使用 --counts-only。清单不提供把两代结果伪装为同一代的汇总 PASS。','summary_replay':'python3 -B evidence/2026-10-16-batch16/T-093/collect-validation-15.py --source /private/tmp --output-dir /private/tmp/t093-summary-replay-NEW'},ensure_ascii=False,indent=2)+'\n').encode()
 args.output_dir.mkdir(parents=True,exist_ok=True)
 # Preserve earlier event/check copies; reject conflicting bytes without hashes.
 for name,payload in pending.items():
  target=args.output_dir/name
  if target.exists():
   if not (name.endswith('.events.jsonl') or name in ('chain-07-check.json','rehearsal-04-check.json')) or target.read_bytes()!=payload:raise FileExistsError(target)
 for name,payload in pending.items():
  target=args.output_dir/name
  if target.exists():continue
  with target.open('xb') as stream:stream.write(payload)
 print(json.dumps({'status':'PASS','groups':len(GROUPS),'source_files':len(manifest),'raw_files_deleted':False}))

if __name__=='__main__':main()
